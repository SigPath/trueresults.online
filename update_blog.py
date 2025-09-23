# === PROMPT DLA GITHUB COPILOT - WERSJA 6.1 (Autonomiczny Analityk AI) ===
#
# Cel: Stworzenie ostatecznej, kreatywnej wersji skryptu `update_blog.py`.
# System ma wczytywać konfigurację z pliku `config.xlsx`, a następnie, na podstawie
# krótkiej "inspiracji" z arkusza KampanieTematyczne, zlecać AI samodzielne
# wymyślenie tytułu i napisanie unikalnego, głębokiego artykułu.
#
# INSTRUKCJA DLA COPILOTA:
# Wygeneruj kompletny, czysty skrypt w Pythonie, który realizuje poniższą logikę.

# === KROK 1: Importy i Konfiguracja ===
import os
import time
import datetime
import random
import re
import json
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from git import Repo
from slugify import slugify
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv

# Konfiguracja ścieżek
REPO_PATH = Path(__file__).parent.resolve()
CONFIG_FILE = REPO_PATH / "config.xlsx"
USED_TOPICS_FILE = REPO_PATH / "used_topics_global.txt"
TEMPLATES_PATH = REPO_PATH
POST_TEMPLATE_FILE = TEMPLATES_PATH / "szablon_wpisu.html"
INDEX_FILE = REPO_PATH / "index.html"
PAGES_DIR = REPO_PATH / "pages"
RSS_FILE = REPO_PATH / "rss.xml"
SITEMAP_FILE = REPO_PATH / "sitemap.xml"
SPIS_TRESCI_FILE = REPO_PATH / "spis.html"

# Wczytanie zmiennych środowiskowych
load_dotenv(REPO_PATH / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

# Konfiguracja Gemini
genai.configure(api_key=GEMINI_API_KEY)
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# === KROK 2: Wczytywanie Konfiguracji z Pliku Excel (Wersja Odporna na Błędy) ===
def load_config_from_excel(path: Path) -> dict:
    """
    Wczytuje konfigurację z pliku Excel, ignorując nagłówki i bazując na pozycji kolumn.
    Kolumna A -> 'key', Kolumna B -> 'value'.
    """
    if not path.exists():
        raise FileNotFoundError(f"Plik konfiguracyjny nie został znaleziony: {path}")

    print(f"Wczytywanie konfiguracji z pliku: {path}...")
    config = {
        "master_prompt_parts": {},
        "case_study": {},
        "campaigns": {}
    }

    try:
        # Wczytywanie MasterPrompt
        df_prompt = pd.read_excel(path, sheet_name='MasterPrompt', header=None)
        df_prompt.columns = ['key', 'value']
        config['master_prompt_parts'] = dict(zip(df_prompt['key'], df_prompt['value']))

        # Wczytywanie CaseStudy
        df_case = pd.read_excel(path, sheet_name='CaseStudy', header=None)
        df_case.columns = ['key', 'value']
        config['case_study'] = dict(zip(df_case['key'], df_case['value']))

        # Wczytywanie Kampanii Tematycznych
        df_campaigns = pd.read_excel(path, sheet_name='KampanieTematyczne', header=None)
        df_campaigns.columns = ['campaign', 'inspiration']
        
        campaign_dict = {}
        for _, row in df_campaigns.iterrows():
            campaign_name = row['campaign']
            inspiration = row['inspiration']
            if pd.notna(campaign_name) and pd.notna(inspiration):
                if campaign_name not in campaign_dict:
                    campaign_dict[campaign_name] = []
                campaign_dict[campaign_name].append(inspiration)
        config['campaigns'] = campaign_dict
        
        print("Konfiguracja wczytana pomyślnie.")
        return config

    except Exception as e:
        print(f"[BŁĄD KRYTYCZNY] Nie udało się wczytać danych z pliku Excel: {e}")
        print("Upewnij się, że plik 'config.xlsx' istnieje i zawiera arkusze: 'MasterPrompt', 'CaseStudy', 'KampanieTematyczne'.")
        raise

# === KROK 3: Dynamiczne Budowanie Master Promptu ===
def build_master_prompt(config: dict) -> str:
    """Dynamicznie buduje pełny tekst Master Promptu."""
    prompt_parts = [str(value) for value in config.get("master_prompt_parts", {}).values()]
    case_study_parts = [f"{key}: {value}" for key, value in config.get("case_study", {}).items()]
    
    case_study_full = "\n".join(case_study_parts)
    
    # Wstrzyknięcie Case Study do promptu
    full_prompt = "\n\n".join(prompt_parts)
    full_prompt = full_prompt.replace("{{CASE_STUDY}}", case_study_full)
    
    return full_prompt

# === KROK 4: Logika Wyboru Inspiracji ===
def get_used_topics():
    """Wczytuje użyte tematy z pliku."""
    if not USED_TOPICS_FILE.exists():
        return set()
    with open(USED_TOPICS_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def save_used_topic(topic: str):
    """Zapisuje użyty temat do pliku."""
    with open(USED_TOPICS_FILE, 'a', encoding='utf-8') as f:
        f.write(topic + '\n')

def get_current_campaign(config: dict) -> str:
    """Określa bieżącą kampanię na podstawie daty."""
    today = datetime.date.today()
    campaign_names = list(config.get("campaigns", {}).keys())
    if not campaign_names:
        return None
    # Prosta logika rotacji kampanii co tydzień
    week_number = today.isocalendar()[1]
    campaign_index = week_number % len(campaign_names)
    return campaign_names[campaign_index]

def pick_inspiration(config: dict) -> tuple[str, str] | tuple[None, None]:
    """Wybiera nową, nieużytą inspirację z bieżącej kampanii."""
    campaign_name = get_current_campaign(config)
    if not campaign_name:
        print("Brak zdefiniowanych kampanii w konfiguracji.")
        return None, None

    inspirations = config["campaigns"].get(campaign_name, [])
    used_topics = get_used_topics()
    
    available_inspirations = [insp for insp in inspirations if insp not in used_topics]
    
    if not available_inspirations:
        print(f"Wszystkie inspiracje z kampanii '{campaign_name}' zostały już wykorzystane.")
        # Opcjonalnie: zresetuj listę użytych tematów dla tej kampanii
        return None, None
        
    chosen_inspiration = random.choice(available_inspirations)
    print(f"Wybrano temat '{chosen_inspiration}' z kampanii '{campaign_name}'.")
    return chosen_inspiration, campaign_name

# === KROK 5: System Generowania Treści Offline ===
def generate_offline_content(inspiration: str) -> str:
    """Generuje przyzwoitą treść offline gdy API nie działa."""
    sections = [
        f"<h1>{inspiration}</h1>",
        f"<p>Temat <strong>{inspiration.lower()}</strong> stanowi fascynujące pole badawcze w kontekście współczesnych wyzwań psychologicznych i społecznych.</p>",
        f"<h2>Kontekst Problemu</h2>",
        f"<p>W kontekście analizowanego studium przypadku, {inspiration.lower()} ujawnia się jako kluczowy element wpływający na dynamikę relacyjną i rozwój osobisty.</p>",
        f"<h2>Analiza Psychologiczna</h2>",
        f"<p>Psychologiczne mechanizmy leżące u podstaw tego zjawiska wskazują na głębokie wzorce behawioralne, które wymagają starannej analizy i zrozumienia.</p>",
        f"<p>Badania wskazują, że {inspiration.lower()} może mieć długotrwałe konsekwencje dla:</p>",
        f"<ul><li>Zdrowia psychicznego jednostki</li><li>Jakości relacji interpersonalnych</li><li>Rozwoju osobistego i samopoznania</li><li>Zdolności do budowania zaufania</li></ul>",
        f"<h2>Implikacje Praktyczne</h2>",
        f"<p>Zrozumienie mechanizmów związanych z {inspiration.lower()} może pomóc w:</p>",
        f"<ul><li>Rozpoznawaniu wczesnych sygnałów ostrzegawczych</li><li>Opracowywaniu skutecznych strategii interwencyjnych</li><li>Budowaniu odporności psychicznej</li></ul>",
        f"<h2>Wnioski</h2>",
        f"<p>Analiza {inspiration.lower()} podkreśla wagę holistycznego podejścia do zdrowia psychicznego i jakości relacji. Wymaga to nie tylko zrozumienia teorii, ale także praktycznego zastosowania wiedzy w codziennym życiu.</p>",
        f"<p><em>Ten artykuł został wygenerowany w trybie offline. Pełna analiza z wykorzystaniem sztucznej inteligencji będzie dostępna po przywróceniu połączenia z API.</em></p>"
    ]
    return "\n".join(sections)

# === KROK 6: Funkcja Generowania z Groq API ===
def generate_with_groq(inspiration: str, master_prompt: str) -> dict:
    """Generuje artykuł używając Groq API jako alternatywy dla Gemini."""
    print("🦙 Próbuję generować treść z Groq API...")
    
    final_prompt = f"""{master_prompt}

Twoim dzisiejszym zadaniem jest napisanie artykułu inspirowanego poniższą frazą.

INSPIRACJA: "{inspiration}"

Twoje zadania:
1.  **Wymyśl Tytuł:** Stwórz kreatywny, intrygujący i unikalny tytuł dla artykułu, który nawiązuje do inspiracji i studium przypadku.
2.  **Napisz Artykuł:** Napisz głęboki, analityczny artykuł. Masz pełną swobodę co do jego struktury. Możesz używać nagłówków, list, cytatów. Artykuł musi być napisany w formacie HTML.
3.  **Wygeneruj Meta Opis:** Stwórz krótki (150-160 znaków) meta opis, który jest esencją artykułu i zachęca do kliknięcia.
4.  **Stwórz Sekcję FAQ:** Przygotuj 3-4 pytania i odpowiedzi w formacie JSON-LD, które rozwijają kluczowe aspekty artykułu.

Całość zwróć jako pojedynczy obiekt JSON, bez żadnych dodatkowych znaków czy formatowania markdown.

Struktura JSON-a:
{{
  "title": "Twój wymyślony, kreatywny tytuł",
  "meta_description": "Twój wygenerowany meta opis (150-160 znaków).",
  "html_content": "<h1>Twój Tytuł</h1><p>Cała treść artykułu w formacie <b>HTML</b>...",
  "faq_json_ld": {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {{
        "@type": "Question",
        "name": "Pierwsze pytanie?",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "Odpowiedź na pierwsze pytanie."
        }}
      }}
    ]
  }}
}}
"""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "Jesteś ekspertem w dziedzinie psychologii i analizy społecznej. Generujesz tylko poprawne JSON-y bez dodatkowych formatowań."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
            response_format={"type": "json_object"}
        )
        
        response_text = completion.choices[0].message.content
        
        # Parsowanie JSON
        parsed_json = json.loads(response_text)
        
        # Walidacja kluczy
        required_keys = ["title", "meta_description", "html_content", "faq_json_ld"]
        if all(key in parsed_json for key in required_keys):
            print("✅ Groq API: Artykuł wygenerowany pomyślnie!")
            return parsed_json
        else:
            print("❌ Groq API: Odpowiedź nie zawiera wszystkich wymaganych kluczy.")
            return None
            
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return None

# === KROK 7: Główny, Kreatywny Silnik Generowania Treści ===
def generate_creative_article(inspiration: str, master_prompt: str) -> dict:
    """Generuje kreatywny artykuł na podstawie inspiracji, zwracając JSON."""
    
    final_prompt = f"""{master_prompt}

Twoim dzisiejszym zadaniem jest napisanie artykułu inspirowanego poniższą frazą.

INSPIRACJA: "{inspiration}"

Twoje zadania:
1.  **Wymyśl Tytuł:** Stwórz kreatywny, intrygujący i unikalny tytuł dla artykułu, który nawiązuje do inspiracji i studium przypadku.
2.  **Napisz Artykuł:** Napisz głęboki, analityczny artykuł. Masz pełną swobodę co do jego struktury. Możesz używać nagłówków, list, cytatów. Artykuł musi być napisany w formacie HTML.
3.  **Wygeneruj Meta Opis:** Stwórz krótki (150-160 znaków) meta opis, który jest esencją artykułu i zachęca do kliknięcia.
4.  **Stwórz Sekcję FAQ:** Przygotuj 3-4 pytania i odpowiedzi w formacie JSON-LD, które rozwijają kluczowe aspekty artykułu.

Całość zwróć jako pojedynczy obiekt JSON, bez żadnych dodatkowych znaków czy formatowania markdown.

Struktura JSON-a:
{{
  "title": "Twój wymyślony, kreatywny tytuł",
  "meta_description": "Twój wygenerowany meta opis (150-160 znaków).",
  "html_content": "<h1>Twój Tytuł</h1><p>Cała treść artykułu w formacie <b>HTML</b>...",
  "faq_json_ld": {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {{
        "@type": "Question",
        "name": "Pierwsze pytanie?",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "Odpowiedź na pierwsze pytanie."
        }}
      }},
      {{
        "@type": "Question",
        "name": "Drugie pytanie?",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "Odpowiedź na drugie pytanie."
        }}
      }}
    ]
  }}
}}
"""
    
    fallback_content = {
        "title": f"Analiza tematu: {inspiration}",
        "meta_description": "W tym artykule przyglądamy się bliżej zagadnieniu, analizując jego różne aspekty w kontekście studium przypadku.",
        "html_content": generate_offline_content(inspiration),
        "faq_json_ld": {}
    }

    # FASE 1: Próby z Gemini API
    print("🤖 Próbuję generować treść z Gemini API...")
    for attempt in range(2):  # Zmniejszam liczbę prób Gemini, żeby szybciej przejść do Groq
        try:
            print(f"   Wysyłanie zapytania do Gemini... (próba {attempt + 1}/2)")
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                safety_settings=safety_settings,
                generation_config=generation_config,
            )
            response = model.generate_content(final_prompt)
            
            # Czasem Gemini zwraca JSON wewnątrz bloku markdown, trzeba to wyczyścić
            cleaned_response_text = re.sub(r'^```json\s*|\s*```$', '', response.text.strip(), flags=re.MULTILINE)
            
            parsed_json = json.loads(cleaned_response_text)
            
            # Walidacja kluczy
            required_keys = ["title", "meta_description", "html_content", "faq_json_ld"]
            if all(key in parsed_json for key in required_keys):
                print("✅ Gemini API: Artykuł wygenerowany pomyślnie!")
                return parsed_json
            else:
                print("❌ Gemini API: Odpowiedź nie zawiera wszystkich wymaganych kluczy.")
                
        except Exception as e:
            print(f"❌ Gemini API Error (próba {attempt + 1}): {e}")
            if "429" in str(e) and "quota" in str(e).lower():
                print("   🚫 Gemini API osiągnął limit quota. Przechodzę do Groq...")
                break  # Natychmiast przejdź do Groq jeśli to błąd quota
            elif attempt < 1:
                print("   ⏳ Ponawiam próbę za 15 sekund...")
                time.sleep(15)

    # FASE 2: Próba z Groq API
    if GROQ_API_KEY:
        print("🔄 Gemini niedostępny, próbuję z Groq API...")
        groq_result = generate_with_groq(inspiration, master_prompt)
        if groq_result:
            return groq_result
        else:
            print("❌ Groq API także nie powiódł się.")
    else:
        print("⚠️  Brak klucza Groq API w konfiguracji.")

    # FASE 3: Fallback do treści offline
    print("📝 Oba API niedostępne. Używam treści zastępczej.")
    return fallback_content

# === KROK 6: Reszta Skryptu ===

def build_post_html(template_content: str, data: dict, campaign: str, post_url: str) -> str:
    """Wypełnia szablon HTML danymi artykułu."""
    now = datetime.datetime.now()
    
    # Ustawienie polskiej lokalizacji dla nazw miesięcy
    import locale
    try:
        locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
    except locale.Error:
        print("Nie można ustawić polskiej lokalizacji. Data będzie w domyślnym formacie.")
    
    human_date = now.strftime('%d %B %Y')
    iso_date = now.isoformat()

    html = template_content.replace("{{TYTUL}}", data.get('title', 'Brak tytułu'))
    html = html.replace("{{OPIS}}", data.get('meta_description', 'Brak opisu.'))
    html = html.replace("{{META_OPIS}}", data.get('meta_description', 'Brak opisu.')) # Podwójne dla pewności
    html = html.replace("{{KANONICAL}}", post_url)
    html = html.replace("{{DATA}}", iso_date)
    html = html.replace("{{DATA_LUDZKA}}", human_date)
    html = html.replace("{{KATEGORIA}}", campaign or "Ogólna")
    html = html.replace("{{TRESC_ARTYKULU}}", data.get('html_content', '<p>Brak treści.</p>'))
    html = html.replace("{{TRESC_HTML}}", data.get('html_content', '<p>Brak treści.</p>')) # Podwójne dla pewności
    
    faq_data = data.get("faq_json_ld", {})
    if faq_data:
        faq_script = f'<script type="application/ld+json">{json.dumps(faq_data, indent=2, ensure_ascii=False)}</script>'
    else:
        faq_script = ""
    
    # W szablonie nie ma {{FAQ_JSON_LD}}, ale zostawiam na przyszłość.
    # Zamiast tego, FAQ jest częścią {{FAQ_HTML}} - na razie puste.
    html = html.replace("{{FAQ_JSON_LD}}", faq_script)
    html = html.replace("{{FAQ_HTML}}", "") # Na razie puste
    html = html.replace("{{POWIAZANE_POSTY_HTML}}", "") # Na razie puste
    
    return html

def insert_card_in_index(file_path: Path, title: str, description: str, link: str, campaign: str):
    """Dodaje nową kartę artykułu do pliku index.html."""
    if not file_path.exists():
        print(f"Plik {file_path} nie istnieje. Nie można dodać karty.")
        return

    with open(file_path, 'r+', encoding='utf-8') as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        
        container = soup.find(id='posts-container')
        if not container:
            print("Nie znaleziono kontenera '#posts-container' w pliku index.html.")
            return
            
        # Ustawienie polskiej lokalizacji dla nazw miesięcy
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
            human_date = datetime.datetime.now().strftime('%d %B %Y')
            iso_date = datetime.datetime.now().strftime('%Y-%m-%d')
        except locale.Error:
            print("Nie można ustawić polskiej lokalizacji. Data będzie w domyślnym formacie.")
            human_date = datetime.datetime.now().strftime('%d %B %Y')
            iso_date = datetime.datetime.now().strftime('%Y-%m-%d')

        card_html = f"""
      <article class="group relative flex flex-col rounded-xl border border-border/70 bg-surface/90 p-6 shadow-sm hover:shadow-lift hover:-translate-y-1 transition-all duration-300" itemscope="True" itemtype="https://schema.org/BlogPosting">
       <h3 class="mt-4 text-lg font-semibold leading-snug group-hover:text-accent transition-colors" itemprop="headline">
        {title}
       </h3>
       <time class="mt-2 text-xs text-text/60" datetime="{iso_date}" itemprop="datePublished">
        Opublikowano: {human_date}
       </time>
       <p class="mt-4 text-sm leading-relaxed text-text/80 line-clamp-5" itemprop="description">
        {description}
       </p>
       <a aria-label="Czytaj dalej: {title}" class="mt-5 inline-flex items-center text-sm font-medium text-accent hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60" href="{link}" itemprop="url">
        Czytaj dalej →
       </a>
       <meta content="True Results Online" itemprop="author"/>
      </article>
"""
        
        placeholder = soup.find(string=lambda text: "AUTO-BLOG: NOWE WPISY" in text)
        if placeholder:
            placeholder.insert_before(BeautifulSoup(card_html, 'html.parser'))
        else:
            # Fallback if placeholder comment is missing
            container.insert(0, BeautifulSoup(card_html, 'html.parser'))
        
        f.seek(0)
        f.write(str(soup))
        f.truncate()

def update_sitemap_and_rss(new_post_url: str, title: str, description: str):
    """Aktualizuje sitemap.xml i rss.xml."""
    now_iso = datetime.datetime.now().isoformat()
    
    # Sitemap
    if SITEMAP_FILE.exists():
        with open(SITEMAP_FILE, 'r+', encoding='utf-8') as f:
            content = f.read()
            if new_post_url not in content:
                new_entry = f"""
<url>
  <loc>{new_post_url}</loc>
  <lastmod>{now_iso}</lastmod>
  <priority>0.80</priority>
</url>
"""
                content = content.replace('</urlset>', f'{new_entry}</urlset>')
                f.seek(0)
                f.write(content)
                f.truncate()

    # RSS
    if RSS_FILE.exists():
        with open(RSS_FILE, 'r+', encoding='utf-8') as f:
            content = f.read()
            if f'<link>{new_post_url}</link>' not in content:
                new_item = f"""
    <item>
      <title>{title}</title>
      <link>{new_post_url}</link>
      <description>{description}</description>
      <pubDate>{now_iso}</pubDate>
    </item>
"""
                content = content.replace('</channel>', f'{new_item}\n  </channel>')
                f.seek(0)
                f.write(content)
                f.truncate()

def update_spis_tresci(new_post_url: str, title: str, description: str):
    """Aktualizuje plik spisu treści."""
    if not SPIS_TRESCI_FILE.exists():
        return
    with open(SPIS_TRESCI_FILE, 'r+', encoding='utf-8') as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        
        container = soup.find('div', class_='space-y-8')
        if not container:
            print("Nie znaleziono kontenera 'space-y-8' w pliku spis.html.")
            return

        # Ustawienie polskiej lokalizacji dla nazw miesięcy
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
            iso_date = datetime.datetime.now().strftime('%Y-%m-%d')
        except locale.Error:
            print("Nie można ustawić polskiej lokalizacji. Data będzie w domyślnym formacie.")
            iso_date = datetime.datetime.now().strftime('%Y-%m-%d')

        article_html = f"""
<article class='border-b border-border/40 pb-6'>
    <h2 class='text-lg font-semibold'>
        <a class='hover:text-accent transition-colors' href='{new_post_url}'>{title} – True Results Online</a>
    </h2>
    <p class='mt-1 text-xs text-text/60'>{iso_date}</p>
    <p class='mt-2 text-sm text-text/80 leading-relaxed'>{description}</p>
</article>
"""
        
        placeholder = soup.find(string=lambda text: "AUTO-BLOG: NOWE WPISY" in text)
        if placeholder:
            placeholder.insert_before(BeautifulSoup(article_html, 'html.parser'))
        else:
            # Fallback if placeholder comment is missing
            container.insert(0, BeautifulSoup(article_html, 'html.parser'))

        f.seek(0)
        f.write(str(soup))
        f.truncate()

def commit_and_push_changes(repo_path: Path, commit_message: str):
    """Wprowadza zmiany do repozytorium Git i wysyła je na serwer."""
    try:
        repo = Repo(repo_path)
        repo.git.add(all=True)
        
        if repo.is_dirty(untracked_files=True):
            repo.index.commit(commit_message)
            print("Wprowadzono zmiany do lokalnego repozytorium.")
            
            origin = repo.remote(name='origin')
            origin.push()
            print("Wysłano zmiany do zdalnego repozytorium.")
        else:
            print("Brak zmian do wprowadzenia.")
            
    except Exception as e:
        print(f"Błąd podczas operacji Git: {e}")

def main():
    """Główna funkcja sterująca skryptem."""
    print("=== TRUE RESULTS ONLINE - GENERATOR ARTYKUŁÓW ===")
    print(f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        config = load_config_from_excel(CONFIG_FILE)
    except Exception as e:
        print(f"❌ Zatrzymano skrypt z powodu błędu konfiguracji: {e}")
        return

    inspiration, campaign = pick_inspiration(config)
    if not inspiration:
        print("❌ Nie udało się wybrać inspiracji na dziś. Kończę pracę.")
        return

    print(f"✅ Wybrana inspiracja: '{inspiration}'")
    print(f"✅ Kampania: '{campaign}'")
    print()

    master_prompt = build_master_prompt(config)
    
    print("🚀 Rozpoczynam generowanie artykułu...")
    article_data = generate_creative_article(inspiration, master_prompt)
    
    if not article_data or not article_data.get("title"):
        print("❌ Nie udało się wygenerować danych artykułu. Kończę pracę.")
        return
    
    # Sprawdzanie typu treści i źródła
    is_offline = "trybie offline" in article_data.get("html_content", "")
    content_length = len(article_data.get("html_content", ""))
    
    if is_offline:
        status_icon = "📝"
        content_type = "Offline Fallback"
    elif content_length > 3000:  # Groq zwykle generuje dłuższe treści
        status_icon = "🦙"
        content_type = "Groq API"
    else:
        status_icon = "🤖"
        content_type = "Gemini API"
    
    print(f"{status_icon} Wygenerowano artykuł ({content_type}): '{article_data['title']}'")
    print()

    # Zapisanie użytej inspiracji
    save_used_topic(inspiration)

    # Przygotowanie nazwy pliku i URL
    slug = slugify(article_data['title'])
    date_stamp = datetime.datetime.now().strftime('%Y%m%d')
    filename = f"{slug}-{date_stamp}.html"
    filepath = PAGES_DIR / filename
    post_url = f"https://trueresults.online/pages/{filename}"

    # Budowanie i zapis pliku HTML
    try:
        with open(POST_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        post_html = build_post_html(template_content, article_data, campaign, post_url)
        
        PAGES_DIR.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(post_html)
        print(f"✅ Utworzono plik HTML: {filename}")
        print(f"📄 Długość treści: {len(article_data.get('html_content', ''))} znaków")

    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku szablonu {POST_TEMPLATE_FILE}")
        return
    except Exception as e:
        print(f"Błąd podczas tworzenia pliku HTML: {e}")
        return

    # Aktualizacja plików głównych
    print("🔄 Aktualizuję pliki główne...")
    insert_card_in_index(INDEX_FILE, article_data['title'], article_data['meta_description'], f"pages/{filename}", campaign)
    update_sitemap_and_rss(post_url, article_data['title'], article_data['meta_description'])
    update_spis_tresci(f"pages/{filename}", article_data['title'], article_data['meta_description'])
    print("✅ Zaktualizowano: index.html, sitemap.xml, rss.xml, spis.html")

    # Commit i push
    commit_message = f"Automatyczny wpis: {article_data['title']}"
    print("📤 Wysyłam zmiany do repozytorium...")
    commit_and_push_changes(REPO_PATH, commit_message)
    
    print()
    print("🎉 SUKCES! Artykuł został wygenerowany i opublikowany.")
    print(f"🔗 URL: {post_url}")
    print("=" * 50)

if __name__ == "__main__":
    main()
