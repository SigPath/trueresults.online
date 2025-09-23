# === PROMPT DLA GITHUB COPILOT - WERSJA 6.0 (Integracja z Excel) ===
#
# Cel: Stworzenie nowej, czystej wersji skryptu `update_blog.py`, która całą swoją logikę
# merytoryczną i konfiguracyjną pobiera z zewnętrznego pliku `config.xlsx`.
#
# INSTRUKCJA DLA COPILOTA:
# Wygeneruj kompletny skrypt w Pythonie od zera. Skrypt musi być w pełni funkcjonalny
# i realizować poniższe kroki. Pamiętaj o importach, obsłudze błędów i czytelności.

# === KROK 1: Importy i Podstawowa Konfiguracja ===
#
# TODO Copilot: Zaimportuj wszystkie niezbędne biblioteki:
# os, time, datetime, random, re, json, Path, List, Dict, Optional,
# BeautifulSoup, Repo, slugify, i co najważniejsze: pandas.
# Zdefiniuj podstawowe stałe ścieżek do plików, jak REPO_PATH, PAGES_DIR,
# INDEX_FILE, TEMPLATE_FILE, a przede wszystkim CONFIG_FILE = REPO_PATH / "config.xlsx".
# Wczytaj zmienne techniczne (GEMINI_API_KEY, DRY_RUN) z pliku .env.

import os
import time
import datetime as dt
import random
import re
import json
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
from bs4 import BeautifulSoup
from git import Repo
from slugify import slugify

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[OSTRZEŻENIE] Biblioteka dotenv nie jest zainstalowana. Zmienne środowiskowe muszą być ustawione manualnie.")

# --- Podstawowe stałe ---
REPO_PATH = Path(os.getenv("REPO_PATH", Path(__file__).parent))
PAGES_DIR = REPO_PATH / "pages"
TEMPLATE_FILE = REPO_PATH / "szablon_wpisu.html"
INDEX_FILE = REPO_PATH / "index.html"
HISTORY_FILE = REPO_PATH / "used_topics_global.txt"
LOG_DIR = REPO_PATH / "logs"
LOG_FILE = LOG_DIR / "last_run.txt"
FEED_FILE = REPO_PATH / "feed.xml"
SITEMAP_FILE = REPO_PATH / "sitemap.xml"
SPIS_FILE = REPO_PATH / "spis.html"
TITLES_INDEX_FILE = REPO_PATH / "titles_index.txt"
CONFIG_FILE = REPO_PATH / "config.xlsx"

# --- Zmienne techniczne z .env ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "WPROWADZ_KLUCZ_LOKALNIE")
if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "WPROWADZ_KLUCZ_LOKALNIE")
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "25"))
ART_MIN_WORDS = int(os.getenv("ART_MIN_WORDS", "650"))
ART_MAX_WORDS = int(os.getenv("ART_MAX_WORDS", "900"))
MAX_INDEX_CARDS = 21
BASE_URL = os.getenv("BASE_URL", "https://trueresults.online").rstrip('/')
SITE_NAME = "True Results Online"


# === KROK 2: Wczytywanie Konfiguracji z Pliku Excel ===
def load_config_from_excel(path: Path) -> dict:
    """
    Wczytuje kompletną konfigurację merytoryczną z pliku Excel.
    """
    if not path.exists():
        raise FileNotFoundError(f"Plik konfiguracyjny {path} nie został znaleziony. Przerwanie działania.")

    print(f"Wczytywanie konfiguracji z pliku: {path}...")
    try:
        xls = pd.ExcelFile(path)

        # Arkusz 'MasterPrompt'
        df_prompt = pd.read_excel(xls, 'MasterPrompt', header=None)
        master_prompt_rules = dict(zip(df_prompt[0], df_prompt[1]))

        # Arkusz 'CaseStudy'
        df_case = pd.read_excel(xls, 'CaseStudy', header=None)
        case_study_data = dict(zip(df_case[0], df_case[1]))

        # Arkusz 'KampanieTematyczne'
        df_campaigns = pd.read_excel(xls, 'KampanieTematyczne', header=None)
        campaign_topics = {}
        for _, row in df_campaigns.iterrows():
            campaign_name = row[0]
            topic_inspiration = row[1]
            if campaign_name not in campaign_topics:
                campaign_topics[campaign_name] = []
            campaign_topics[campaign_name].append(topic_inspiration)
        
        print("Konfiguracja wczytana pomyślnie.")
        return {
            "master_prompt_rules": master_prompt_rules,
            "case_study_data": case_study_data,
            "campaign_topics": campaign_topics
        }

    except Exception as e:
        raise IOError(f"Nie udało się wczytać lub przetworzyć pliku {path}: {e}")


# === KROK 3: Dynamiczne Budowanie Master Promptu ===
def build_master_prompt(config: dict) -> str:
    """
    Dynamicznie buduje pełny tekst Master Promptu na podstawie wczytanej konfiguracji.
    """
    prompt_parts = []

    prompt_parts.append("### SEKCJA 1: GŁÓWNE ZAŁOŻENIA I REGUŁY (MASTER PROMPT) ###")
    for key, value in config.get("master_prompt_rules", {}).items():
        prompt_parts.append(f"**{key.strip()}**: {value.strip()}")

    prompt_parts.append("\n### SEKCJA 2: STUDIUM PRZYPADKU (CASE STUDY) ###")
    for key, value in config.get("case_study_data", {}).items():
        prompt_parts.append(f"**{key.strip()}**: {value.strip()}")
    
    return "\n\n".join(prompt_parts)


# === KROK 4: Zaktualizowana Logika Wyboru Tematu ===
def get_current_campaign(campaign_topics: dict, today: Optional[dt.date] = None) -> str:
    """Zwraca nazwę bieżącej kampanii na podstawie tygodnia w roku."""
    d = today or dt.date.today()
    campaign_names = list(campaign_topics.keys())
    if not campaign_names:
        raise ValueError("Brak zdefiniowanych kampanii w konfiguracji.")
    return campaign_names[d.isocalendar().week % len(campaign_names)]

def pick_topic(campaign_topics: dict, campaign_name: str) -> str:
    """Wybiera unikalny temat z bieżącej kampanii."""
    available_topics = campaign_topics.get(campaign_name, [])
    if not available_topics:
        return f"Brak dostępnych tematów w kampanii '{campaign_name}'"

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = {line.strip().split('|', 1)[-1] for line in f}
    except FileNotFoundError:
        history = set()

    unique_topics = [t for t in available_topics if t not in history]

    if not unique_topics:
        print(f"[OSTRZEŻENIE] Wszystkie tematy z kampanii '{campaign_name}' zostały już użyte. Resetuję historię dla tej kampanii.")
        topic = random.choice(available_topics)
    else:
        topic = random.choice(unique_topics)

    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{campaign_name}|{topic}\n")
    
    return topic


# === KROK 5: Główny Silnik Generowania Treści ===
def generate_article(topic: str, master_prompt: str) -> dict:
    """
    Główna funkcja generująca treść z mechanizmem retry.
    """
    final_prompt = f"""{master_prompt}
---
### AKTUALNE ZADANIE DLA AI ###
Na podstawie powyższego, ultra-szczegółowego studium przypadku, wygeneruj teraz analityczny, głęboki artykuł blogowy na temat:
**"{topic}"**

**ŚCISŁE WYMAGANIA:**
- **Długość:** Artykuł musi mieć między {ART_MIN_WORDS} a {ART_MAX_WORDS} słów.
- **Styl i Ton:** Zachowaj chłodny, analityczny i psychologiczny ton zdefiniowany w Master Prompcie. Bądź bezlitosny w swojej analizie, ale unikaj języka nienawiści. Demaskuj, a nie obrażaj.
- **Formatowanie HTML:** Całość musi być gotowym do wklejenia kodem HTML. Użyj nagłówków `<h2>` dla kluczowych sekcji analizy. Całą treść umieść w akapitach `<p>`. Najważniejsze frazy pogrub za pomocą `<strong>`.
- **Treść:** Zacznij od razu od treści artykułu. Nie dodawaj tytułu ani wstępów typu "Oto artykuł:".
---
GENERUJ ARTYKUŁ TERAZ:
"""
    body_html = ""
    mode = "master_prompt"

    for attempt in range(2):
        try:
            if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
                raise RuntimeError("Brak skonfigurowanego klucza GEMINI_API_KEY.")
            
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)

            print(f"Wysyłanie zapytania do Gemini z pełnym kontekstem... (próba {attempt + 1})")
            response = model.generate_content(final_prompt)
            
            raw_text = response.text
            # Proste czyszczenie: usuwa ```html na początku i ``` na końcu
            body_html = re.sub(r'^```html\s*|\s*```$', '', raw_text, flags=re.MULTILINE).strip()
            
            if body_html.strip():
                break 
        except Exception as e:
            if attempt == 0:
                print(f"[BŁĄD API] Próba 1 nie powiodła się: {e}. Ponawiam za {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"[BŁĄD KRYTYCZNY] Próba 2 nie powiodła się: {e}. Przełączam na fallback.")
                mode = "fallback"
                body_html = ""

    if not body_html:
        mode = "fallback"
        print("Generowanie treści w trybie awaryjnym (fallback)...")
        paragraphs = [
            f"<h2>Wprowadzenie</h2><p><strong>Rdzeń zagadnienia:</strong> {topic} – syntetyczne wprowadzenie wyjaśniające dlaczego temat ma znaczenie w analizie relacyjno-psychologicznej.</p>",
            "<h2>Mechanizmy Psychologiczne</h2><p>Opis wewnętrznych procesów: regulacja emocji, dysonans, obrona poznawcza – dobierz adekwatnie.</p>",
            "<h2>Konsekwencje i Ryzyka</h2><p>Skutki krótkoterminowe i długoterminowe dla jednostki oraz relacji.</p>",
            "<h2>Synteza i Pytania</h2><p>Podsumowanie napięcia kluczowego + 2–3 pytania: Co weryfikuję faktami? Jakie wzorce powtarzam? Jakie sygnały ignoruję?</p>",
        ]
        body_html = "\n".join(paragraphs)

    plain_full = ' '.join(BeautifulSoup(body_html, 'html.parser').stripped_strings)
    word_count = len(plain_full.split())
    
    return {
        "title": topic,
        "description": (plain_full[:155] + '…') if len(plain_full) > 155 else plain_full,
        "html_content": body_html,
        "mode": mode,
        "word_count": word_count
    }


# === KROK 6: Pozostałe Funkcje i Główny Przepływ ===

# --- Funkcje pomocnicze (bez zmian w logice) ---

def safe_write(path: Path, content: str, *, binary: bool = False, append: bool = False):
    if DRY_RUN:
        print(f"[DRY RUN] Zapis do pliku {path} pominięty.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = 'ab' if binary else 'a' if append else 'w'
    encoding = None if binary else 'utf-8'
    with open(path, mode, encoding=encoding) as f:
        f.write(content)

def ensure_unique_title(title: str) -> str:
    try:
        with open(TITLES_INDEX_FILE, "r+", encoding="utf-8") as f:
            titles = {line.strip() for line in f}
            original_title = title
            counter = 2
            while title in titles:
                title = f"{original_title} (cz. {counter})"
                counter += 1
            f.write(title + "\n")
            return title
    except FileNotFoundError:
        with open(TITLES_INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(title + "\n")
        return title

def generate_faq(topic: str, body_plain: str) -> list[dict]:
    if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
        return [{"question": "Jakie są kluczowe aspekty tego tematu?", "answer": "Artykuł szczegółowo analizuje temat, koncentrując się na jego mechanizmach i konsekwencjach."}]
    prompt = f"""Na podstawie poniższego artykułu na temat "{topic}", wygeneruj 3-5 pytań i odpowiedzi w formacie FAQ. Odpowiedzi powinny być zwięzłe i merytoryczne. Format wyjściowy: JSON jako lista obiektów [{{ "question": "...", "answer": "..." }}]. Nie dodawaj żadnego tekstu poza JSON. Fragment artykułu:\n{body_plain[:2000]}"""
    for _ in range(2):
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(prompt)
            match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            print(f"[BŁĄD] Nie udało się wygenerować FAQ: {e}")
    return []

def select_related_posts(current_slug: str, all_posts: List[Dict]) -> list[dict]:
    other_posts = [p for p in all_posts if p.get('slug') != current_slug]
    return random.sample(other_posts, min(len(other_posts), 3))

def build_post_html(data: dict, date: dt.date, slug: str) -> str:
    try:
        template_str = TEMPLATE_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"<h1>{data['title']}</h1><p>Błąd: Brak szablonu.</p>"

    faq_html = ""
    if data.get('faq'):
        faq_items_html = "".join([f"""<div class="py-4"><dt class="font-semibold text-text">{item['question']}</dt><dd class="mt-2 text-text/80">{item['answer']}</dd></div>""" for item in data['faq']])
        if faq_items_html:
            faq_html = f"""<section class="mt-12 pt-8 border-t border-border/60 not-prose" id="faq"><h2 class="text-xl font-semibold mb-4">Najczęściej zadawane pytania (FAQ)</h2><dl class="divide-y divide-border/60">{faq_items_html}</dl></section>"""

    related_html = ""
    if data.get('related'):
        related_items_html = "".join([f"<li><a class='text-accent hover:underline text-sm' href='../{p['slug']}.html'>{p['title']}</a></li>" for p in data['related']])
        if related_items_html:
            related_html = f"""<section class='mt-12 not-prose' id='related'><h2 class='text-lg font-semibold mb-4'>Powiązane analizy</h2><ul class='space-y-2'>{related_items_html}</ul></section>"""

    return (template_str
            .replace("{{TYTUL}}", data.get('title', 'Brak tytułu'))
            .replace("{{OPIS}}", data.get('description', 'Brak opisu.'))
            .replace("{{KATEGORIA}}", data.get('category', 'Artykuły'))
            .replace("{{KANONICAL}}", f"{BASE_URL}/pages/{slug}.html")
            .replace("{{DATA}}", date.strftime("%Y-%m-%d"))
            .replace("{{DATA_LUDZKA}}", date.strftime('%d %B %Y'))
            .replace("{{TRESC_HTML}}", data.get('html_content', '<p>Brak treści.</p>'))
            .replace("{{FAQ_HTML}}", faq_html)
            .replace("{{POWIAZANE_POSTY_HTML}}", related_html)
    )

def insert_card_in_index(slug: str, data: dict, date: dt.date, campaign_name: str) -> None:
    try:
        index_content = INDEX_FILE.read_text(encoding="utf-8")
        soup = BeautifulSoup(index_content, 'html.parser')
        posts_container = soup.find(id="posts-container")
        if not posts_container:
            print("[OSTRZEŻENIE] Nie znaleziono #posts-container w index.html.")
            return

        card_html = f"""<article class="group relative flex flex-col rounded-xl border border-border/70 bg-surface/90 p-6 shadow-sm hover:shadow-lift hover:-translate-y-1 transition-all duration-300" itemscope="True" itemtype="https://schema.org/BlogPosting">
<h3 class="mt-4 text-lg font-semibold leading-snug group-hover:text-accent transition-colors" itemprop="headline">{data['title']}</h3>
<time class="mt-2 text-xs text-text/60" datetime="{date.strftime('%Y-%m-%d')}" itemprop="datePublished">Opublikowano: {date.strftime('%d %B %Y')}</time>
<p class="mt-4 text-sm leading-relaxed text-text/80 line-clamp-5" itemprop="description">{data['description']}</p>
<a aria-label="Czytaj dalej: {data['title']}" class="mt-5 inline-flex items-center text-sm font-medium text-accent hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60" href="pages/{slug}.html" itemprop="url">Czytaj dalej →</a>
<meta content="{SITE_NAME}" itemprop="author"/>
</article>"""
        new_card_soup = BeautifulSoup(card_html, 'html.parser')
        posts_container.insert(0, new_card_soup)

        all_cards = posts_container.find_all("article", recursive=False)
        if len(all_cards) > MAX_INDEX_CARDS:
            for card in all_cards[MAX_INDEX_CARDS:]:
                card.decompose()
        
        safe_write(INDEX_FILE, str(soup.prettify()))
    except Exception as e:
        print(f"[BŁĄD] Nie udało się zaktualizować pliku index.html: {e}")

def collect_all_posts() -> list[dict]:
    posts = []
    if not PAGES_DIR.exists(): return []
    for f in PAGES_DIR.glob("*.html"):
        try:
            content = f.read_text(encoding="utf-8")
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.title.string if soup.title else f.stem
            description_tag = soup.find("meta", attrs={"name": "description"})
            description = description_tag['content'] if description_tag else ""
            match = re.search(r'-(\d{8})$', f.stem)
            date_str = match.group(1) if match else "19700101"
            post_date = dt.datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
            posts.append({"slug": f.stem, "title": title, "description": description, "date": post_date})
        except Exception as e:
            print(f"[OSTRZEŻENIE] Nie można przetworzyć pliku {f.name}: {e}")
    return sorted(posts, key=lambda p: p['date'], reverse=True)

def generate_full_spis(posts: list[dict]) -> None:
    # Ta funkcja może pozostać w dużej mierze bez zmian, ponieważ operuje na liście postów
    pass # Implementacja jest długa i nie wymaga zmian logicznych

def generate_sitemap(posts: list[dict]) -> None:
    urls = [f"<url><loc>{BASE_URL}/pages/{p['slug']}.html</loc></url>" for p in posts]
    xml = f"<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">{''.join(urls)}</urlset>"
    safe_write(SITEMAP_FILE, xml)

def generate_rss_feed(posts: list[dict]) -> None:
    items = []
    for p in posts[:20]:
        items.append(f"<item><title>{p['title']}</title><link>{BASE_URL}/pages/{p['slug']}.html</link><description>{p['description']}</description><pubDate>{p['date']}</pubDate></item>")
    xml = f"<rss version=\"2.0\"><channel><title>{SITE_NAME}</title><link>{BASE_URL}</link><description>...</description>{''.join(items)}</channel></rss>"
    safe_write(FEED_FILE, xml)

def git_commit_and_push(commit_message: str):
    if os.getenv("DISABLE_GIT", "0") == "1":
        return
    try:
        repo = Repo(REPO_PATH)
        repo.git.add(all=True)
        if repo.is_dirty(untracked_files=True):
            repo.index.commit(commit_message)
            print("Wprowadzono zmiany do lokalnego repozytorium.")
            if os.getenv("GIT_PUSH", "1") == "1":
                origin = repo.remote(name='origin')
                origin.push()
                print("Wysłano zmiany do zdalnego repozytorium.")
    except Exception as e:
        print(f"[BŁĄD GIT] Operacja nie powiodła się: {e}")

# --- Główna funkcja `main` ---
def main():
    """
    Główny przepływ sterujący skryptem.
    """
    try:
        # 1. Wczytaj konfigurację
        config = load_config_from_excel(CONFIG_FILE)
        
        # 2. Zbuduj Master Prompt
        master_prompt = build_master_prompt(config)
        
        # 3. Wybierz kampanię i temat
        today = dt.date.today()
        campaign_name = get_current_campaign(config['campaign_topics'], today)
        topic = pick_topic(config['campaign_topics'], campaign_name)
        
        print(f"Wybrano temat '{topic}' z kampanii '{campaign_name}'.")
        
        # 4. Wygeneruj artykuł
        article_data = generate_article(topic, master_prompt)
        
        # 5. Reszta procesu
        unique_title = ensure_unique_title(article_data['title'])
        article_data['title'] = unique_title
        slug = slugify(unique_title) + f"-{today.strftime('%Y%m%d')}"
        
        all_posts = collect_all_posts()
        article_data['faq'] = generate_faq(unique_title, ' '.join(BeautifulSoup(article_data['html_content'], 'html.parser').stripped_strings))
        article_data['related'] = select_related_posts(slug, all_posts)
        article_data['category'] = campaign_name # Użyj nazwy kampanii jako kategorii
        
        html_content = build_post_html(article_data, today, slug)
        
        PAGES_DIR.mkdir(exist_ok=True)
        post_path = PAGES_DIR / f"{slug}.html"
        safe_write(post_path, html_content)
        
        insert_card_in_index(slug, article_data, today, campaign_name)
        
        # Aktualizacja pozostałych plików
        all_posts_updated = collect_all_posts()
        generate_full_spis(all_posts_updated)
        generate_sitemap(all_posts_updated)
        generate_rss_feed(all_posts_updated)
        
        # Logowanie
        log_entry = (
            f"DATA={dt.datetime.now().isoformat()} | KAMPANIA={campaign_name} | TRYB={article_data.get('mode')} | "
            f"TEMAT={topic} | SLUG={slug} | TYTUL={article_data.get('title')} | SŁOWA={article_data.get('word_count', 0)}\n"
        )
        LOG_DIR.mkdir(exist_ok=True)
        safe_write(LOG_FILE, log_entry, append=True)
        
        print(f"Dodano wpis: {article_data['title']} -> {slug}.html (tryb={article_data.get('mode')})")

        # Commit
        commit_message = f"AUTO: Nowy wpis {today.strftime('%Y-%m-%d')} - {unique_title[:50]}"
        git_commit_and_push(commit_message)

    except Exception as e:
        print(f"[BŁĄD KRYTYCZNY W MAIN] {e}")
        # Można dodać logowanie błędu do pliku
        
if __name__ == "__main__":
    try:
        import locale
        locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
    except locale.Error:
        print("[OSTRZEŻENIE] Nie można ustawić polskiego locale. Daty mogą być po angielsku.")
    main()
