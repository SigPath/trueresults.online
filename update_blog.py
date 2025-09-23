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

# === KROK 2: Wczytywanie Konfiguracji z Pliku Excel ===
def load_config_from_excel(path: Path) -> dict:
    """Wczytuje konfigurację z pliku Excel."""
    try:
        xls = pd.ExcelFile(path)
        master_prompt_df = xls.parse('MasterPrompt', header=None)
        case_study_df = xls.parse('CaseStudy', header=None)
        kampanie_df = xls.parse('KampanieTematyczne', header=None)

        config = {
            "master_prompt_parts": master_prompt_df.rename(columns={0: 'Klucz', 1: 'Treść'}).to_dict('records'),
            "case_study": case_study_df.rename(columns={0: 'Element', 1: 'Opis'}).to_dict('records'),
            "campaigns": kampanie_df.groupby(0)[1].apply(list).to_dict()
        }
        print(f"Wczytywanie konfiguracji z pliku: {path}...")
        print("Konfiguracja wczytana pomyślnie.")
        return config
    except FileNotFoundError:
        print(f"Błąd: Plik konfiguracyjny {path} nie został znaleziony.")
        return {}
    except Exception as e:
        print(f"Błąd podczas wczytywania konfiguracji z Excela: {e}")
        return {}

# === KROK 3: Dynamiczne Budowanie Master Promptu ===
def build_master_prompt(config: dict) -> str:
    """Dynamicznie buduje pełny tekst Master Promptu."""
    prompt_parts = [part['Treść'] for part in config.get("master_prompt_parts", [])]
    case_study_parts = [f"{row['Element']}: {row['Opis']}" for row in config.get("case_study", [])]
    
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

# === KROK 5: Główny, Kreatywny Silnik Generowania Treści ===
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
        "html_content": f"<h1>Analiza tematu: {inspiration}</h1><p>Niestety, automatyczne generowanie treści nie powiodło się. Prosimy spróbować ponownie później. Ten artykuł jest jedynie szablonem zastępczym.</p>",
        "faq_json_ld": {}
    }

    for attempt in range(2):
        try:
            print(f"Wysyłanie zapytania do Gemini z pełnym kontekstem... (próba {attempt + 1})")
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
                return parsed_json
            else:
                print("Odpowiedź JSON nie zawiera wszystkich wymaganych kluczy.")
                
        except Exception as e:
            print(f"Błąd podczas generowania treści (próba {attempt + 1}): {e}")
            if attempt < 1:
                print("Ponawiam próbę za 15 sekund...")
                time.sleep(15)

    print("Nie udało się wygenerować treści po 2 próbach. Używam treści zastępczej.")
    return fallback_content

# === KROK 6: Reszta Skryptu ===

def build_post_html(template_content: str, data: dict, campaign: str) -> str:
    """Wypełnia szablon HTML danymi artykułu."""
    now = datetime.datetime.now()
    
    # Ustawienie polskiej lokalizacji dla nazw miesięcy
    import locale
    try:
        locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
        human_date = now.strftime('%d %B %Y')
    except locale.Error:
        print("Nie można ustawić polskiej lokalizacji. Data będzie w domyślnym formacie.")
        human_date = now.strftime('%d %B %Y')

    html = template_content.replace("{{TYTUL}}", data['title'])
    html = html.replace("{{DATA_LUDZKA}}", human_date)
    html = html.replace("{{KATEGORIA}}", campaign)
    html = html.replace("{{TRESC_ARTYKULU}}", data['html_content'])
    html = html.replace("{{META_OPIS}}", data['meta_description'])
    
    faq_script = f'<script type="application/ld+json">{json.dumps(data["faq_json_ld"], indent=2, ensure_ascii=False)}</script>'
    html = html.replace("{{FAQ_JSON_LD}}", faq_script)
    
    return html

def insert_card_in_index(file_path: Path, title: str, description: str, link: str, campaign: str):
    """Dodaje nową kartę artykułu do pliku index.html."""
    if not file_path.exists():
        print(f"Plik {file_path} nie istnieje. Nie można dodać karty.")
        return

    with open(file_path, 'r+', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
        grid = soup.find('div', class_='grid')
        if not grid:
            print("Nie znaleziono siatki 'grid' w pliku index.html.")
            return
            
        # Tworzenie nowej karty
        new_card = soup.new_tag('div', **{'class': 'card'})
        
        # Ustawienie polskiej lokalizacji dla nazw miesięcy
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
            human_date = datetime.datetime.now().strftime('%d %B %Y')
        except locale.Error:
            print("Nie można ustawić polskiej lokalizacji. Data będzie w domyślnym formacie.")
            human_date = datetime.datetime.now().strftime('%d %B %Y')

        card_content = f"""
            <div class="card-category">{campaign}</div>
            <h2><a href="{link}">{title}</a></h2>
            <p>{description}</p>
            <div class="card-footer">
                <a href="{link}" class="read-more">Czytaj dalej...</a>
                <span>{human_date}</span>
            </div>
        """
        new_card.append(BeautifulSoup(card_content, 'html.parser'))
        
        # Wstawienie nowej karty na początku siatki
        grid.insert(0, new_card)
        
        f.seek(0)
        f.write(str(soup.prettify()))
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

def update_spis_tresci(new_post_url: str, title: str):
    """Aktualizuje plik spisu treści."""
    if not SPIS_TRESCI_FILE.exists():
        return
    with open(SPIS_TRESCI_FILE, 'r+', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
        main_list = soup.find('ul')
        if main_list:
            new_li = soup.new_tag('li')
            new_a = soup.new_tag('a', href=new_post_url.replace(str(REPO_PATH), '..'))
            new_a.string = title
            new_li.append(new_a)
            main_list.insert(0, new_li)
            
            f.seek(0)
            f.write(str(soup.prettify()))
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
    config = load_config_from_excel(CONFIG_FILE)
    if not config:
        return

    inspiration, campaign = pick_inspiration(config)
    if not inspiration:
        print("Nie udało się wybrać inspiracji na dziś. Kończę pracę.")
        return

    master_prompt = build_master_prompt(config)
    
    article_data = generate_creative_article(inspiration, master_prompt)
    
    if not article_data or not article_data.get("title"):
        print("Nie udało się wygenerować danych artykułu. Kończę pracę.")
        return

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
        
        post_html = build_post_html(template_content, article_data, campaign)
        
        PAGES_DIR.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(post_html)
        print(f"Dodano wpis: {article_data['title']} -> {filename}")

    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku szablonu {POST_TEMPLATE_FILE}")
        return
    except Exception as e:
        print(f"Błąd podczas tworzenia pliku HTML: {e}")
        return

    # Aktualizacja plików głównych
    insert_card_in_index(INDEX_FILE, article_data['title'], article_data['meta_description'], f"pages/{filename}", campaign)
    update_sitemap_and_rss(post_url, article_data['title'], article_data['meta_description'])
    update_spis_tresci(f"pages/{filename}", article_data['title'])

    # Commit i push
    commit_message = f"Automatyczny wpis: {article_data['title']}"
    commit_and_push_changes(REPO_PATH, commit_message)

if __name__ == "__main__":
    main()
