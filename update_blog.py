# === PROMPT DLA GITHUB COPILOT - WERSJA 7.0 (Integracja z Matrycą Excel) ===
#
# **TWOJA ROLA:** Jesteś starszym inżynierem oprogramowania. Twoim zadaniem jest
# refaktoryzacja istniejącego skryptu `update_blog.py`, aby w pełni wykorzystywał
# rozbudowaną, czterokolumnową strukturę danych z pliku `config.xlsx`.
#
# **KONCEPCJA ARCHITEKTONICZNA:**
# Skrypt musi teraz działać jak precyzyjny wykonawca poleceń z Excela.
# Zamiast losować ogólną "inspirację", będzie losował cały "pakiet zadaniowy"
# (Tytuł, Teza, Słowa Kluczowe) i przekazywał go do AI.

# === KROK 1: Importy i Konfiguracja Podstawowa ===
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
HISTORY_FILE = REPO_PATH / "used_topics_global.txt"
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
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

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

# === KROK 2: Ulepszona Funkcja Wczytywania Konfiguracji z Excela ===
def load_config_from_excel(path: Path) -> dict:
    """
    Wczytuje konfigurację z pliku Excel, w tym pełną matrycę tematyczną.
    NOWOŚĆ WERSJI 7.0: Arkusz KampanieTematyczne wczytywany jako lista słowników
    z czterema kolumnami: campaign, title, thesis, keywords.
    """
    if not path.exists():
        raise FileNotFoundError(f"Plik konfiguracyjny nie został znaleziony: {path}")

    print(f"🔧 [v7.0] Wczytywanie konfiguracji z pliku: {path}...")
    config = {
        "master_prompt_parts": {},
        "case_study": {},
        "campaign_topics": []  # NOWOŚĆ: Lista słowników z pełnymi pakietami zadaniowymi
    }

    try:
        # Wczytywanie MasterPrompt z właściwymi nagłówkami
        df_prompt = pd.read_excel(path, sheet_name='MasterPrompt')
        # Arkusz ma kolumny: Klucz, Wartość
        config['master_prompt_parts'] = dict(zip(df_prompt['Klucz'], df_prompt['Wartość']))

        # Wczytywanie CaseStudy z właściwymi nagłówkami
        df_case = pd.read_excel(path, sheet_name='CaseStudy')
        # Arkusz ma kolumny: Kategoria, Szczegół
        config['case_study'] = dict(zip(df_case['Kategoria'], df_case['Szczegół']))

        # KLUCZOWA ZMIANA: Wczytywanie pełnej matrycy tematycznej
        df_topics = pd.read_excel(path, sheet_name='KampanieTematyczne')
        # Arkusz ma nagłówki: Kampania, Tytuł Artykułu, Teza Główna, Słowa Kluczowe - używamy oryginalnych nazw
        
        # Przekształcenie do listy słowników - każdy wiersz to kompletny "pakiet zadaniowy"
        campaign_topics = []
        for _, row in df_topics.iterrows():
            # Używamy prawdziwych nazw kolumn z arkusza
            if pd.notna(row['Kampania']) and pd.notna(row['Tytuł Artykułu']):
                topic_package = {
                    'campaign': str(row['Kampania']).strip(),
                    'title': str(row['Tytuł Artykułu']).strip(),
                    'thesis': str(row['Teza Główna']).strip() if pd.notna(row['Teza Główna']) else '',
                    'keywords': str(row['Słowa Kluczowe']).strip() if pd.notna(row['Słowa Kluczowe']) else ''
                }
                campaign_topics.append(topic_package)
        
        config['campaign_topics'] = campaign_topics
        
        print(f"✅ [v7.0] Wczytano {len(campaign_topics)} kompletnych pakietów zadaniowych.")
        return config

    except Exception as e:
        print(f"❌ [BŁĄD KRYTYCZNY] Nie udało się wczytać danych z pliku Excel: {e}")
        print("Upewnij się, że plik 'config.xlsx' zawiera arkusze: 'MasterPrompt', 'CaseStudy', 'KampanieTematyczne'.")
        raise

# === KROK 3: Dynamiczne Budowanie Master Promptu ===
def build_master_prompt_from_config(config_file_path: Path) -> str:
    """
    WERSJA 7.0: Buduje master prompt bezpośrednio z arkuszy Excela.
    Pobiera dane z arkuszy MasterPrompt i CaseStudy.
    """
    try:
        df_prompt = pd.read_excel(config_file_path, sheet_name='MasterPrompt')
        df_case_study = pd.read_excel(config_file_path, sheet_name='CaseStudy')
        
        # Budowanie master promtu z arkusza MasterPrompt (kolumny: Klucz, Wartość)
        prompt_parts = []
        for _, row in df_prompt.iterrows():
            prompt_parts.append(str(row['Wartość']))
        
        # Budowanie case study z arkusza CaseStudy (kolumny: Kategoria, Szczegół)
        case_study_parts = []
        for _, row in df_case_study.iterrows():
            case_study_parts.append(f"{row['Kategoria']}: {row['Szczegół']}")
        
        case_study_full = "\n".join(case_study_parts)
        
        # Składanie pełnego promptu
        full_prompt = "\n\n".join(prompt_parts)
        full_prompt = full_prompt.replace("{{CASE_STUDY}}", case_study_full)
        
        return full_prompt
        
    except Exception as e:
        print(f"⚠️  Błąd odczytu master promptu z Excela: {e}")
        return "Jesteś ekspertem psychologiem i analitykiem. Twórz głębokie, analityczne artykuły w języku polskim."

# === KROK 3: Zaktualizowana Logika Wyboru Tematu ===
def get_used_titles():
    """Wczytuje użyte tytuły artykułów z pliku historii."""
    if not HISTORY_FILE.exists():
        return set()
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def save_used_topic_title(title: str):
    """WERSJA 7.0: Zapisuje użyty tytuł do pliku historii."""
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(title + '\n')

def pick_topic_package(config: dict) -> dict:
    """
    NOWOŚĆ WERSJI 7.0: Wybiera kompletny pakiet zadaniowy z matrycy Excel.
    Zwraca słownik z polami: campaign, title, thesis, keywords.
    """
    campaign_topics = config.get('campaign_topics', [])
    if not campaign_topics:
        print("❌ Brak dostępnych pakietów zadaniowych w konfiguracji.")
        return None
    
    used_titles = get_used_titles()
    
    # Filtrowanie nieużytych pakietów
    available_packages = [
        pkg for pkg in campaign_topics 
        if pkg['title'] not in used_titles
    ]
    
    if not available_packages:
        print("⚠️ Wszystkie pakiety zadaniowe zostały już wykorzystane.")
        print("💡 Resetowanie historii użycia...")
        # Opcjonalnie: zresetuj historię i wybierz losowo
        available_packages = campaign_topics
    
    # Wybór losowego pakietu
    chosen_package = random.choice(available_packages)
    
    # Zapisanie tytułu do historii
    save_used_topic_title(chosen_package['title'])
    
    print(f"📋 [v7.0] Wybrany pakiet zadaniowy:")
    print(f"    🏷️  Kampania: {chosen_package['campaign']}")
    print(f"    📰 Tytuł: {chosen_package['title']}")
    print(f"    💡 Teza: {chosen_package['thesis'][:100]}...")
    print(f"    🔑 Słowa kluczowe: {chosen_package['keywords']}")
    
    return chosen_package

# Usunięto stare funkcje - zastąpione przez pick_topic_package() w wersji 7.0

# === KROK 5: System Generowania Treści Offline ===
def generate_offline_content(topic_package: dict) -> str:
    """Generuje przyzwoitą treść offline gdy API nie działa."""
    title = topic_package.get('title', 'Analiza Tematyczna')
    thesis = topic_package.get('thesis', 'tematyka wymagająca głębszej analizy')
    keywords = topic_package.get('keywords', 'psychologia, analiza, studium przypadku')
    
    sections = [
        f"<h1>{title}</h1>",
        f"<p>Tematyka <strong>{title.lower()}</strong> stanowi fascynujące pole badawcze w kontekście współczesnych wyzwań psychologicznych i społecznych.</p>",
        f"<h2>Teza Główna</h2>",
        f"<p>{thesis}</p>",
        f"<h2>Kontekst Problemu</h2>",
        f"<p>W kontekście analizowanego studium przypadku, omawiane zagadnienie ujawnia się jako kluczowy element wpływający na dynamikę relacyjną i rozwój osobisty.</p>",
        f"<h2>Analiza Psychologiczna</h2>",
        f"<p>Psychologiczne mechanizmy leżące u podstaw tego zjawiska wskazują na głębokie wzorce behawioralne, które wymagają starannej analizy i zrozumienia.</p>",
        f"<p>Kluczowe aspekty związane z: {keywords}.</p>",
        f"<h2>Wnioski</h2>",
        f"<p>Analiza podkreśla wagę holistycznego podejścia do zdrowia psychicznego i jakości relacji. Wymaga to nie tylko zrozumienia teorii, ale także praktycznego zastosowania wiedzy w codziennym życiu.</p>",
        f"<p><em>Ten artykuł został wygenerowany w trybie offline. Pełna analiza z wykorzystaniem sztucznej inteligencji będzie dostępna po przywróceniu połączenia z API.</em></p>"
    ]
    return "\n".join(sections)

# === KROK 6: Funkcja Generowania z Groq API ===
def generate_with_groq(topic_package: dict, master_prompt: str) -> dict:
    """Generuje artykuł używając Groq API jako alternatywy dla Gemini."""
    print("🦙 Próbuję generować treść z Groq API...")
    
    # NOWOŚĆ WERSJI 7.0: Ultra-precyzyjny prompt z gotowymi danymi z Excela
    final_prompt = f"""{master_prompt}

🎯 **ULTRA-PRECYZYJNE ZADANIE WERSJI 7.0:**

Musisz napisać artykuł, który realizuje DOKŁADNIE poniższe specyfikacje z matrycy Excel:

📰 **OBOWIĄZKOWY TYTUŁ (nie zmieniaj!):** 
"{topic_package['title']}"

💡 **TEZA DO UDOWODNIENIA:** 
{topic_package['thesis']}

🔑 **WYMAGANE SŁOWA KLUCZOWE (użyj w tekście):** 
{topic_package['keywords']}

🏷️ **KAMPANIA:** {topic_package['campaign']}

**TWOJE ZADANIA:**
1. **Użyj DOKŁADNIE podanego tytułu** - bez żadnych zmian!
2. **Udowodnij podaną tezę** - artykuł musi logicznie prowadzić do jej potwierdzenia
3. **Wpleć słowa kluczowe** naturalnie w treść artykułu
4. **Napisz artykuł w formacie HTML** z nagłówkami, akapitami, listami
5. **Stwórz meta opis** (150-160 znaków) 
6. **Przygotuj sekcję FAQ** w HTML
7. **Dodaj powiązane artykuły** w HTML

Zwróć wynik jako JSON:

{{
  "title": "{topic_package['title']}",
  "meta_description": "Meta opis 150-160 znaków...",
  "html_content": "<h1>{topic_package['title']}</h1><p>Treść artykułu w HTML...</p>",
  "faq_html": "<div class='faq-section'><h2>Najczęściej zadawane pytania</h2>...</div>",
  "related_articles_html": "<div class='related-articles'><h2>Artykuły powiązane</h2>...</div>",
  "faq_json_ld": {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [] }}
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
        required_keys = ["title", "meta_description", "html_content", "faq_html", "related_articles_html", "faq_json_ld"]
        if all(key in parsed_json for key in required_keys):
            print("✅ Groq API: Artykuł wygenerowany pomyślnie!")
            return parsed_json
        else:
            print("❌ Groq API: Odpowiedź nie zawiera wszystkich wymaganych kluczy.")
            return None
            
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return None

# === KROK 7: Główny Silnik Generowania Artykułów WERSJA 7.0 ===
def generate_article(topic_package: dict, master_prompt: str) -> dict:
    """
    WERSJA 7.0: Generuje artykuł na podstawie precyzyjnego pakietu tematycznego z Excela.
    Wykorzystuje deterministyczne dane: tytuł, tezę, słowa kluczowe i kampanię.
    """
    
    # NOWOŚĆ WERSJI 7.0: Wszystkie dane z topic_package
    print(f"\n🎯 Generuję artykuł z matrycy Excel...")
    print(f"📰 Tytuł: {topic_package['title']}")
    print(f"💡 Teza: {topic_package['thesis']}")
    print(f"🔑 Słowa kluczowe: {topic_package['keywords']}")
    print(f"🏷️ Kampania: {topic_package['campaign']}")

    
    # Przygotowanie fallback na wypadek awarii API
    fallback_content = {
        "title": topic_package['title'],
        "meta_description": f"Analiza tematu: {topic_package['title'][:130]}...",
        "html_content": generate_offline_content(topic_package),
        "faq_html": "<div class='faq-section'><h2>Najczęściej zadawane pytania</h2><div class='faq-item'><h3>Czym charakteryzuje się to zagadnienie?</h3><p>Jest to złożone zjawisko wymagające dogłębnej analizy psychologicznej.</p></div></div>",
        "related_articles_html": "<div class='related-articles'><h2>Artykuły powiązane</h2><p><em>Artykuły powiązane będą dostępne po wygenerowaniu większej ilości treści.</em></p></div>",
        "faq_json_ld": {}
    }

    # WERSJA 7.0: Budowanie ultra-precyzyjnego promptu
    final_prompt = f"""{master_prompt}

🎯 **ULTRA-PRECYZYJNE ZADANIE WERSJI 7.0:**

Musisz napisać artykuł, który realizuje DOKŁADNIE poniższe specyfikacje z matrycy Excel:

📰 **OBOWIĄZKOWY TYTUŁ (nie zmieniaj!):** 
"{topic_package['title']}"

💡 **TEZA DO UDOWODNIENIA:** 
{topic_package['thesis']}

🔑 **WYMAGANE SŁOWA KLUCZOWE (użyj w tekście):** 
{topic_package['keywords']}

🏷️ **KAMPANIA:** {topic_package['campaign']}

**TWOJE ZADANIA:**
1. **Użyj DOKŁADNIE podanego tytułu** - bez żadnych zmian!
2. **Udowodnij podaną tezę** - artykuł musi logicznie prowadzić do jej potwierdzenia
3. **Wpleć słowa kluczowe** naturalnie w treść artykułu
4. **Napisz artykuł w formacie HTML** z nagłówkami, akapitami, listami
5. **Stwórz meta opis** (150-160 znaków) 
6. **Przygotuj sekcję FAQ** w HTML
7. **Dodaj powiązane artykuły** w HTML

Zwróć wynik jako JSON:
{{
  "title": "{topic_package['title']}",
  "meta_description": "Meta opis 150-160 znaków...",
  "html_content": "<h1>{topic_package['title']}</h1><p>Treść artykułu w HTML...</p>",
  "faq_html": "<div class='faq-section'><h2>Najczęściej zadawane pytania</h2>...</div>",
  "related_articles_html": "<div class='related-articles'><h2>Artykuły powiązane</h2>...</div>",
  "faq_json_ld": {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [] }}
}}"""

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
            required_keys = ["title", "meta_description", "html_content", "faq_html", "related_articles_html", "faq_json_ld"]
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

    # FASE 2: Próba z Groq API (WERSJA 7.0)
    if GROQ_API_KEY:
        print("🔄 Gemini niedostępny, próbuję z Groq API...")
        groq_result = generate_with_groq(topic_package, master_prompt)
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
    
    # Wstawianie sekcji FAQ i powiązanych artykułów
    html = html.replace("{{FAQ_JSON_LD}}", faq_script)
    html = html.replace("{{FAQ_HTML}}", data.get('faq_html', ''))
    html = html.replace("{{POWIAZANE_POSTY_HTML}}", data.get('related_articles_html', ''))
    
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
    
    # WERSJA 7.0: Pełna matryca tematyczna z Excela
    try:
        topic_packages = load_config_from_excel(CONFIG_FILE)
    except Exception as e:
        print(f"❌ Zatrzymano skrypt z powodu błędu konfiguracji: {e}")
        return

    topic_package = pick_topic_package(topic_packages)
    if not topic_package:
        print("❌ Nie udało się wybrać pakietu tematycznego. Kończę pracę.")
        return

    print(f"✅ Wybrany pakiet tematyczny:")
    print(f"   📰 Tytuł: {topic_package['title']}")
    print(f"   💡 Teza: {topic_package['thesis']}")
    print(f"   🔑 Słowa kluczowe: {topic_package['keywords']}")
    print(f"   🏷️ Kampania: {topic_package['campaign']}")
    print()

    master_prompt = build_master_prompt_from_config(CONFIG_FILE)
    
    print("🚀 Rozpoczynam generowanie artykułu z matrycą Excel...")
    article_data = generate_article(topic_package, master_prompt)
    
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

    # WERSJA 7.0: Zapisanie użytego tytułu
    save_used_topic_title(topic_package['title'])

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
        
        post_html = build_post_html(template_content, article_data, topic_package['campaign'], post_url)
        
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
    insert_card_in_index(INDEX_FILE, article_data['title'], article_data['meta_description'], f"pages/{filename}", topic_package['campaign'])
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
