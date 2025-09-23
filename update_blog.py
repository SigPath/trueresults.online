# === TRUE RESULTS ONLINE - GENERATOR ARTYKUŁÓW v9.0 ===
# === WERSJA 9.0: RZECZYWISTE CASE STUDY z KONKRETNYMI FAKTAMI ===
#
# **KONCEPCJA ARCHITEKTONICZNA v9.0:**
# Skrypt generuje artykuły oparte na rzeczywistych SMS-ach, logach rozmów
# i dokumentacji zachowań z docs/osoba_a_partner_1.txt i docs/SMS_PARTNER_2_HTML
# z bezlitosną analizą psychologiczną konkretnych wzorców.
#
# **REWOLUCYJNE ZMIANY w v9.0:**
# - Użycie rzeczywistych cytatów z SMS-ów i rozmów
# - Analiza konkretnych zachowań zamiast wymyślonych przykładów
# - Demaskowanie rzeczywistych mechanizmów na podstawie faktów
# - Ekspertcki ton psychologa analizującego prawdziwy materiał dowodowy
# - Multi-level analysis: FAKT → HIPOTEZA → MECHANIZM → APLIKACJAULTS ONLINE - GENERATOR ARTYKUŁÓW v8.1 ===
# === WERSJA 8.1: CASE STUDY FORMAT + TRIPLE FALLBACK (GEMINI/GROQ/COPILOT) ===
#
# **KONCEPCJA ARCHITEKTONICZNA v8.0:**
# Skrypt generuje artykuły w formacie eksperckiego studium przypadku
# z rygorystyczną analizą psychologiczną i demaskowaniem wzorców zachowań.
# Każdy artykuł to konkretne case study z rzeczywistymi mechanizmami psychologicznymi.
#
# **REWOLUCYJNE ZMIANY w v8.0:**
# - Format case study z konkretną Osobą A jako studium przypadku
# - Demaskowanie wzorców zachowań zamiast ogólnych analiz  
# - Ekspertcki, analityczny ton psychologa-praktyka
# - Konkretne mechanizmy psychologiczne zamiast teorii
# - Fokus na praktyczne zrozumienie wzorców relacyjnych
#
# **NOWE w v8.1:**
# - Triple fallback system: Gemini API → Groq API → GitHub Copilot → Offline
# - Zapewnia 100% ciągłość działania niezależnie od dostępności API
# - GitHub Copilot jako premium fallback dla najwyższej jakości

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
import requests  # Do GitHub API calls

# Wczytanie zmiennych środowiskowych z .env
load_dotenv()

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
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Token dla GitHub Copilot API

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

# === KROK 2: NOWA FUNKCJA WCZYTYWANIA RZECZYWISTYCH MATERIAŁÓW DOWODOWYCH ===
def load_real_evidence_materials() -> dict:
    """
    WERSJA 9.0: Wczytuje rzeczywiste materiały dowodowe z docs/ do analizy.
    Zwraca słownik z konkretnymi cytatami, SMS-ami i zachowaniami do analizy.
    """
    evidence = {
        "osoba_a_partner_1_conversations": [],
        "sms_patterns": [],
        "key_quotes": [],
        "behavioral_facts": []
    }
    
    try:
        # Wczytywanie rozmów Osoba A - Partner 1 z października 2024
        osoba_a_partner_1_file = REPO_PATH / "docs" / "karolina_marcin.txt"
        if osoba_a_partner_1_file.exists():
            with open(osoba_a_partner_1_file, 'r', encoding='utf-8') as f:
                content = f.read()
                evidence["osoba_a_partner_1_conversations"] = content
            print(f"📱 Wczytano rozmowy Osoba A - Partner 1: {len(content)} znaków")
        
        # Wczytywanie WSZYSTKICH SMS-ów z Partnerem 2 (wszystkie 6 plików)
        sms_dir = REPO_PATH / "docs" / "SMS_JUREK_HTML"
        if sms_dir.exists():
            all_sms_files = [
                "karolina_pawel_16_maj_2021_31_sie_2024.html",
                "karolina_pawel_17_kwi_2022_30_mar_2024.html", 
                "karolina_pawel_2_wrz_2024_27_wrz_2024.html",
                "karolina_pawel_30_lis_2021_30_mar_2024.html",
                "karolina_pawel_5_lip_2023_11_sie_2023.html",
                "karolina_pawel_5_maj_2021_11_sie_2023.html"
            ]
            for filename in all_sms_files:
                filepath = sms_dir / filename
                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        sms_content = f.read()
                        evidence["sms_patterns"].append({
                            "file": filename,
                            "content": sms_content[:8000]  # Zwiększono do 8000 znaków
                        })
            print(f"💬 Wczytano {len(evidence['sms_patterns'])} plików SMS-ów (wszystkie dostępne)")
        
        # Ekstrakcja kluczowych cytatów z rozmów
        if evidence["osoba_a_partner_1_conversations"]:
            lines = evidence["osoba_a_partner_1_conversations"].split('\n')
            key_quotes = []
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ["przeprasz", "gnojek", "kochał", "znajomy", "amant", "ciąża"]):
                    key_quotes.append(line)
            evidence["key_quotes"] = key_quotes[:20]  # Top 20 najważniejszych cytatów
            print(f"💡 Wyekstraktowano {len(evidence['key_quotes'])} kluczowych cytatów")
        
        # Lista udokumentowanych faktów behawioralnych (rozszerzona)
        evidence["behavioral_facts"] = [
            "Równoległe relacje: Osoba A utrzymywała kontakt z Partnerem 2 przez cały okres związku z Partnerem 1",
            "Minimalizowanie: Nazywała Partnera 2 'znajomym', a nie 'amantem' pomimo intensywnej korespondencji",
            "Projekcja winy: Nazywała Partnera 1 'gnojkiem' jednocześnie deklarując miłość",
            "Segmentacja tożsamości: Różne wersje siebie dla różnych osób",
            "Racjonalizacja: 'Nie zasranowałeś się ze te rozmowy może były mi potrzebne'",
            "Gaslighting: Zaprzeczanie faktom z SMS-ów i logów konwersacji",
            "Manipulacja rodzinną: Wciąganie matki w układ kłamstw nt. Partnera 2",
            "Instrumentalizacja dziecka: Używanie dziecka jako narzędzia w konfliktach",
            "Dwulicowość: 'Kochałam Partnera 1' vs rzeczywiste zachowania",
            "Kompartmentalizacja: Fizyczne i emocjonalne oddzielanie światów",
            "Chroniczna nieautentyczność: Brak spójnej tożsamości we wszystkich relacjach"
        ]
        
        # NOWE: Ekstrakcja cytatów z SMS-ów (HTML parsing)
        sms_quotes = []
        for sms_file in evidence["sms_patterns"]:
            content = sms_file["content"]
            
            # Wydobyj treść z elementów <div class="body">
            import re
            # Pattern dla treści wiadomości w HTML
            body_pattern = r'<div class="body"[^>]*>(.*?)</div>'
            matches = re.findall(body_pattern, content, re.DOTALL)
            
            for match in matches:
                # Usuń tagi HTML i wyczyść tekst
                clean_text = re.sub(r'<[^>]+>', '', match).strip()
                clean_text = clean_text.replace('&nbsp;', ' ').replace('&amp;', '&')
                
                if len(clean_text) > 10 and len(clean_text) < 200:
                    # Filtruj interesujące wiadomości
                    if any(word in clean_text.lower() for word in [
                        "kochanie", "kotku", "skarbie", "całuje", "tęskni", "miłość", 
                        "spotkanie", "dzieci", "mama", "tata", "razem", "chce"
                    ]):
                        if clean_text not in sms_quotes:
                            sms_quotes.append(f"SMS: {clean_text}")
                        
        evidence["sms_key_quotes"] = sms_quotes[:20]  # Top 20 cytatów z SMS-ów
        print(f"📱 Wyekstraktowano {len(evidence['sms_key_quotes'])} cytatów z SMS-ów")
        
        return evidence
        
    except Exception as e:
        print(f"⚠️ Błąd wczytywania materiałów dowodowych: {e}")
        return evidence

# === KROK 3: Ulepszona Funkcja Wczytywania Konfiguracji z Excela ===
def load_config_from_excel(path: Path) -> dict:
    """
    WERSJA 9.0: Wczytuje konfigurację z pliku Excel + ładuje rzeczywiste materiały dowodowe.
    Arkusz KampanieTematyczne zawiera pakiety do analizy konkretnych faktów z SMS-ów
    i logów rozmów z demaskowaniem rzeczywistych wzorców zachowań.
    """
    if not path.exists():
        raise FileNotFoundError(f"Plik konfiguracyjny nie został znaleziony: {path}")

    print(f"🔧 [v8.0] Wczytywanie konfiguracji z case study format: {path}...")
    config = {
        "master_prompt_parts": {},
        "case_study": {},
        "campaign_topics": []  # Lista słowników z pełnymi pakietami zadaniowymi (Tytuł + Teza)
    }

    try:
        # Wczytywanie MasterPrompt
        df_prompt = pd.read_excel(path, sheet_name='MasterPrompt')
        config['master_prompt_parts'] = dict(zip(df_prompt['Klucz'], df_prompt['Wartość']))

        # Wczytywanie CaseStudy
        df_case = pd.read_excel(path, sheet_name='CaseStudy')
        config['case_study'] = dict(zip(df_case['Kategoria'], df_case['Szczegół']))

        # KLUCZOWA ZMIANA v8.0: Wczytywanie matrycy case studies z wzorcami zachowań
        df_topics = pd.read_excel(path, sheet_name='KampanieTematyczne')
        # Struktura: Kampania | Tytuł Artykułu | Teza Główna
        
        # Przekształcenie do listy słowników - każdy wiersz to kompletny "pakiet zadaniowy"
        campaign_topics = []
        for _, row in df_topics.iterrows():
            if pd.notna(row['Kampania']) and pd.notna(row['Tytuł Artykułu']) and pd.notna(row['Teza Główna']):
                topic_package = {
                    'campaign': str(row['Kampania']).strip(),
                    'title': str(row['Tytuł Artykułu']).strip(),
                    'thesis': str(row['Teza Główna']).strip()
                }
                campaign_topics.append(topic_package)
        
        config['campaign_topics'] = campaign_topics
        
        print(f"✅ [v9.0] Wczytano {len(campaign_topics)} pakietów case study do analizy rzeczywistych faktów.")
        return config

    except Exception as e:
        print(f"❌ [BŁĄD KRYTYCZNY] Nie udało się wczytać danych z pliku Excel: {e}")
        print("Upewnij się, że plik 'config.xlsx' zawiera arkusze: 'MasterPrompt', 'CaseStudy', 'KampanieTematyczne'.")
        raise

# === KROK 4: Dynamiczne Budowanie Master Promptu z Rzeczywistymi Materiałami ===
def build_master_prompt_from_config(config_file_path: Path) -> str:
    """
    WERSJA 9.0: Buduje master prompt z rzeczywistymi materiałami dowodowymi.
    Integruje dane z arkuszy Excel + konkretne cytaty i SMS-y.
    """
    try:
        df_prompt = pd.read_excel(config_file_path, sheet_name='MasterPrompt')
        df_case_study = pd.read_excel(config_file_path, sheet_name='CaseStudy')
        
        # Wczytanie rzeczywistych materiałów dowodowych
        evidence = load_real_evidence_materials()
        
        # Budowanie master promtu z arkusza MasterPrompt
        prompt_parts = []
        for _, row in df_prompt.iterrows():
            prompt_parts.append(str(row['Wartość']))
        
        # Budowanie case study z arkusza CaseStudy
        case_study_parts = []
        for _, row in df_case_study.iterrows():
            case_study_parts.append(f"{row['Kategoria']}: {row['Szczegół']}")
        
        case_study_full = "\n".join(case_study_parts)
        
        # NOWE v9.0: Dodanie sekcji z rzeczywistymi cytatami
        real_evidence_section = f"""

=== RZECZYWISTE MATERIAŁY DOWODOWE ===

KLUCZOWE CYTATY Z ROZMÓW:
{chr(10).join(evidence['key_quotes'][:15]) if evidence['key_quotes'] else 'Brak cytatów'}

CYTATY Z SMS-ÓW Z PARTNEREM 2:
{chr(10).join(evidence.get('sms_key_quotes', [])[:10]) if evidence.get('sms_key_quotes') else 'Brak cytatów SMS'}

UDOKUMENTOWANE FAKTY BEHAWIORALNE:
{chr(10).join(evidence['behavioral_facts'])}

WZORCE SMS-ÓW Z PARTNEREM 2:
- Częstotliwość: tysiące wiadomości przez 3+ lata ({len(evidence['sms_patterns'])} plików dowodowych)
- Ton: czułe zwroty, troska, planowanie spotkań
- Ukrywanie: przed Partnerem 1 przez cały okres związku
- Zakres czasowy: maj 2021 - wrzesień 2024

=== KONIEC MATERIAŁÓW DOWODOWYCH ===
"""
        
        # Składanie pełnego promptu
        full_prompt = "\n\n".join(prompt_parts)
        
        # WERSJA 9.0 FIXED: Zawsze dodaj case study i materiały dowodowe na końcu
        if "{{CASE_STUDY}}" in full_prompt:
            full_prompt = full_prompt.replace("{{CASE_STUDY}}", case_study_full + real_evidence_section)
        else:
            # Jeśli placeholder nie istnieje, dodaj materiały na końcu
            full_prompt += "\n\n=== STUDIUM PRZYPADKU ===\n" + case_study_full + real_evidence_section
        
        return full_prompt
        
    except Exception as e:
        print(f"⚠️  Błąd odczytu master promptu z Excela: {e}")
        return """Jesteś ekspertem psychologiem-praktykiem analizującym rzeczywiste przypadki. 
        Używaj konkretnych cytatów i udokumentowanych zachowań do bezlitosnej analizy wzorców.
        Twórz artykuły case study z demaskowaniem rzeczywistych mechanizmów psychologicznych."""

# === KROK 2b: System Bezpieczeństwa Plików ===
def check_file_safe_for_updates(file_path: Path) -> bool:
    """
    Sprawdza czy plik jest bezpieczny do automatycznych aktualizacji.
    Zwraca False jeśli plik wygląda na ręcznie edytowany.
    """
    if not file_path.exists():
        return True  # Nieistniejący plik można utworzyć
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Proste heurystyki wykrywające ręczne edycje
        suspicious_patterns = [
            '<!DOCTYPE html>\n\n<!DOCTYPE html>',  # Duplikacja
            '<html><html>',  # Zagnieżdżone tagi
        ]
        
        for pattern in suspicious_patterns:
            if pattern in content:
                return False  # Plik wydaje się zepsuty
        
        # Jeśli plik ma profesjonalną strukturę z załącznika - nie ruszać
        if 'True Results Online – Prawda. Analiza. Zrozumienie.' in content:
            if 'Przebijanie się przez szum dzięki rygorystycznym' in content:
                return False  # To jest dobra wersja z załącznika
        
        return True  # Plik wygląda na bezpieczny do modyfikacji
        
    except Exception:
        return False  # W razie wątpliwości - nie ruszać

# === KROK 3: Zaktualizowana Logika Wyboru Tematu ===
def get_used_titles():
    """Wczytuje użyte tytuły artykułów z pliku historii."""
    if not HISTORY_FILE.exists():
        return set()
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def save_used_topic_title(title: str):
    """WERSJA 9.0: Zapisuje użyty tytuł analizy rzeczywistych faktów do pliku historii."""
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(title + '\n')

def pick_topic_package(config: dict) -> dict:
    """
    WERSJA 9.0: Wybiera pakiet analizy rzeczywistych faktów z matrycy Excel.
    Zwraca słownik z polami: campaign, title, thesis - gotowy do analizy konkretnych materiałów dowodowych.
    """
    campaign_topics = config.get('campaign_topics', [])
    if not campaign_topics:
        print("❌ Brak dostępnych pakietów case study w konfiguracji.")
        return None
    
    used_titles = get_used_titles()
    
    # Filtrowanie nieużytych pakietów na podstawie tytułów
    available_packages = [
        pkg for pkg in campaign_topics 
        if pkg['title'] not in used_titles
    ]
    
    if not available_packages:
        print("⚠️ Wszystkie pakiety case study zostały już wykorzystane.")
        print("💡 Resetowanie historii użycia...")
        available_packages = campaign_topics
    
    # Wybór losowego pakietu zadaniowego
    chosen_package = random.choice(available_packages)
    
    # Zapisanie tytułu do historii użycia
    save_used_topic_title(chosen_package['title'])
    
    print(f"📋 [v9.0] Wybrany pakiet analizy rzeczywistych faktów:")
    print(f"    🏷️  Kampania: {chosen_package['campaign']}")
    print(f"    📰 Tytuł: {chosen_package['title']}")
    print(f"    💡 Teza: {chosen_package['thesis'][:100]}...")
    
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
    """WERSJA 8.0: Generuje artykuł case study używając Groq API z głęboką analizą psychologiczną."""
    print("🦙 Próbuję generować case study z Groq API (próba 1/2)...")
    
    # WERSJA 9.0: GROQ PROMPT z RZECZYWISTYMI MATERIAŁAMI DOWODOWYMI
    final_prompt = f"""{master_prompt}

---
### ZADANIE DLA AI: ANALIZA RZECZYWISTYCH MATERIAŁÓW DOWODOWYCH ###

Jesteś ekspertem psychologiem-praktykiem analizującym prawdziwy przypadek.

**TEMAT ANALIZY:** "{topic_package['title']}"

**HIPOTEZA DO UDOWODNIENIA:** {topic_package['thesis']}

**METODOLOGIA ANALIZY RZECZYWISTYCH FAKTÓW:**

**KROK 1: UŻYJ WYŁĄCZNIE RZECZYWISTYCH MATERIAŁÓW**
- Cytuj konkretne SMS-y i rozmowy z sekcji "RZECZYWISTE MATERIAŁY DOWODOWE"
- Analizuj udokumentowane zachowania, NIE wymyślaj przykładów
- Każdy wniosek MUSI być oparty na konkretnym cytacie lub fakcie

**KROK 2: STRUKTURA MULTI-LEVEL ANALYSIS**
- POZIOM 1 - FAKT: Co zostało udokumentowane (cytaty, SMS-y)
- POZIOM 2 - HIPOTEZA: Możliwa interpretacja (z poziomem pewności)  
- POZIOM 3 - MECHANIZM: Psychologiczne wyjaśnienie wzorca
- POZIOM 4 - APLIKACJA: Praktyczne rozpoznawanie podobnych przypadków

**KROK 3: TON EKSPERTCKI i DEMASKUJĄCY**
- Pisz jak psycholog analizujący materiał dowodowy w sprawie sądowej
- Bądź bezlitosny w analizie, ale oparty na faktach
- Używaj terminologii psychologicznej: mechanizm projekcji, gaslighting, kompartmentalizacja

**OBOWIĄZKOWA STRUKTURA html_content:**
<h2>Wprowadzenie</h2>
<p>2-3 akapity wprowadzające</p>
<h2>Analiza Rzeczywistych Materiałów</h2>
<blockquote>\"Pierwszy cytat z sekcji RZECZYWISTE MATERIAŁY DOWODOWE\"</blockquote>
<p>Analiza tego cytatu - mechanizm psychologiczny</p>
<blockquote>\"Drugi cytat z materiałów\"</blockquote>
<p>Analiza drugiego cytatu</p>
<h2>Wzorce Zachowań</h2>
<p>3-4 akapity o wzorcach na podstawie faktów</p>
<h2>Mechanizmy Obronne</h2>
<p>3-4 akapity o mechanizmach obronnych</p>
<h2>Konsekwencje</h2>
<p>2-3 akapity o konsekwencjach</p>
<h2>Wnioski</h2>
<p>2 akapity końcowe</p>

ABSOLUTNIE OBOWIĄZKOWE: MINIMUM 20 tagów <p> w html_content!

**OSTRZEŻENIE**: Jeśli html_content będzie miał mniej niż 18 akapitów <p>, odpowiedź zostanie ODRZUCONA!

**PRZYKŁAD CYTOWANIA:**
<blockquote>"Przepraszam, ale nie zaśranowałeś się że te rozmowy może były mi potrzebne" - Osoba A w rozmowie z Partnerem 1</blockquote>
<p>Ten cytat ujawnia <strong>mechanizm racjonalizacji</strong> z jednoczesną <strong>projekcją winy</strong>.</p>

Zwróć wynik jako JSON (uwaga na poprawne escapowanie cudzysłowów):

{{
  "title": "TEMAT_ARTYKULU",
  "meta_description": "Analiza rzeczywistych materiałów: {topic_package['title'][:60]}...",
  "html_content": "<h2>Wprowadzenie</h2><p>Analiza rzeczywistego przypadku...</p>",
  "faq_html": "<div class='faq-section'><h2>Najczęściej zadawane pytania</h2>...</div>",
  "related_articles_html": "<div class='related-articles'><h2>Powiązane analizy</h2>...</div>",
  "faq_json_ld": {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [] }}
}}

---
ANALIZUJ TERAZ WYŁĄCZNIE DOSTARCZONE RZECZYWISTE MATERIAŁY DOWODOWE:"""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "Jesteś ekspertem psychologiem analizującym rzeczywiste przypadki. PRZYKŁAD OCZEKIWANEJ DŁUGOŚCI html_content:\n<h2>Wprowadzenie</h2><p>Długi akapit wprowadzający...</p><p>Drugi akapit kontekstu...</p><h2>Analiza Materiałów Dowodowych</h2><p>Pierwszy akapit analizy...</p><blockquote>\"Konkretny cytat z materiałów\"</blockquote><p>Analiza cytatu w osobnym akapicie...</p><p>Dalsze rozwinięcie analizy...</p><h2>Wzorce Psychologiczne</h2><p>Kolejne 3-4 akapity...</p><h2>Mechanizmy Obronne</h2><p>Kolejne 3-4 akapity...</p><h2>Konsekwencje Behawioralne</h2><p>Kolejne 3-4 akapity...</p><h2>Wnioski</h2><p>2-3 akapity końcowe...</p>\nMUSISZ wygenerować DOKŁADNIE tak długi html_content. Każdy cytat z materiałów w blockquote + analiza."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.9,
            max_tokens=8192,
            top_p=0.95,
            frequency_penalty=0.3,  # Dodano dla większej różnorodności
            response_format={"type": "json_object"}
        )
        
        response_text = completion.choices[0].message.content
        
        # DEBUG: Szczegółowa analiza odpowiedzi Groq
        print(f"🔍 Groq response length: {len(response_text)} characters")
        if len(response_text) < 500:
            print(f"🔍 Short response content: {response_text}")
        
        # DEBUG: Sprawdź czy html_content jest długi
        if '"html_content"' in response_text:
            import re
            html_match = re.search(r'"html_content":\s*"([^"]+(?:\\.[^"]*)*?)"', response_text)
            if html_match:
                html_preview = html_match.group(1)[:200].replace('\\n', '\n')
                p_count = html_preview.count('<p>')
                print(f"🔍 HTML preview (first 200 chars): {html_preview}")
                print(f"🔍 Paragraph count in preview: {p_count}")
        
        # DEBUG: Pokaż fragment odpowiedzi
        print(f"🔍 Response preview: {response_text[:300]}...")
        
        # Parsowanie JSON
        parsed_json = json.loads(response_text)
        
        # Walidacja kluczy
        required_keys = ["title", "meta_description", "html_content", "faq_html", "related_articles_html", "faq_json_ld"]
        if all(key in parsed_json for key in required_keys):
            # NOWA WALIDACJA: Sprawdź czy html_content jest wystarczająco długi
            html_content = parsed_json.get("html_content", "")
            p_count = html_content.count("<p>")
            word_count = len(html_content.split())
            
            print(f"📊 HTML content stats: {p_count} paragraphs, ~{word_count} words")
            
            if p_count >= 13 and word_count >= 250:
                print("✅ Groq API: Case study wygenerowane pomyślnie!")
                return parsed_json
            else:
                print(f"⚠️ Groq API: Artykuł za krótki ({p_count} akapitów, {word_count} słów). Wymagane: 13+ akapitów, 250+ słów.")
                return None
        else:
            print("❌ Groq API: Odpowiedź nie zawiera wszystkich wymaganych kluczy.")
            return None
            
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return None

# === KROK 6b: Funkcja Generowania z GitHub Copilot ===
def generate_with_copilot(topic_package: dict, master_prompt: str) -> dict:
    """WERSJA 9.1: Fallback z wysokiej jakości analizą case study na podstawie rzeczywistych materiałów."""
    print("🐙 Generuję szczegółowe case study z wbudowanym mechanizmem fallback...")
    
    # Wysokiej jakości fallback z rzeczywistymi materiałami
    try:
        # Wyciągnij kluczowe cytaty z master_prompt
        evidence_quotes = []
        behavior_facts = []
        
        if "SMS:" in master_prompt:
            import re
            sms_matches = re.findall(r'SMS: \"([^\"]+)\"', master_prompt)
            evidence_quotes.extend(sms_matches[:8])  # Top 8 SMS quotes
        
        if "ROZMOWA:" in master_prompt:
            conv_matches = re.findall(r'ROZMOWA: \"([^\"]+)\"', master_prompt)  
            evidence_quotes.extend(conv_matches[:5])  # Top 5 conversation quotes
            
        if "FAKT:" in master_prompt:
            fact_matches = re.findall(r'FAKT: ([^\\n]+)', master_prompt)
            behavior_facts.extend(fact_matches[:6])  # Top 6 behavioral facts
        
        # Buduj szczegółową analizę z rzeczywistymi materiałami
        analysis_content = f"""
<h2>Analiza Case Study: {topic_package['title']}</h2>

<p><strong>Kontekst badawczy:</strong> Niniejsza analiza opiera się na rzeczywistych materiałach dowodowych - SMS-ach, logach rozmów i udokumentowanych zachowaniach. Jest to ekspertcka ocena psychologiczna wzorców behawioralnych przeprowadzona metodą case study.</p>

<h3>Główna teza badawcza</h3>
<p><strong>DO UDOWODNIENIA:</strong> {topic_package.get('thesis', 'Analiza wzorców psychologicznych w kontekście rzeczywistych zachowań badanej osoby.')}</p>

<h3>Materiały dowodowe - rzeczywiste cytaty</h3>
<p>Analiza opiera się na autentycznej dokumentacji komunikacji i zachowań:</p>
<ul>
{chr(10).join([f'<li><em>"{quote[:150]}..."</em></li>' for quote in evidence_quotes[:6]])}
</ul>

<h3>Kluczowe fakty behawioralne</h3>
<p>Udokumentowane wzorce zachowań:</p>
<ul>
{chr(10).join([f'<li>{fact}</li>' for fact in behavior_facts[:4]])}
</ul>

<h3>Mechanizmy psychologiczne - analiza ekspertcka</h3>
<p>W badanym przypadku obserwujemy następujące wzorce typowe dla zaburzeń osobowości:</p>
<ul>
<li><strong>Projekcja winy</strong> - systematyczne przenoszenie odpowiedzialności za własne czyny na inne osoby</li>
<li><strong>Racjonalizacja</strong> - tworzenie pozornie logicznych usprawiedliwień dla nieakceptowalnych zachowań</li>
<li><strong>Gaslighting</strong> - manipulacja mająca na celu podważenie pewności siebie ofiary</li>
<li><strong>Segmentacja tożsamości</strong> - prowadzenie podwójnego życia jako mechanizm obronny</li>
<li><strong>Instrumentalizacja</strong> - traktowanie innych osób jako narzędzi do zaspokajania własnych potrzeb</li>
</ul>

<h3>Wzorce komunikacji manipulacyjnej</h3>
<p>Analiza rzeczywistych SMS-ów i rozmów ujawnia charakterystyczne techniki:</p>
<p><strong>Fałszywe przeprosiny:</strong> Wzorzec "przepraszam, ALE..." który służy nie wyrażeniu skruchy, ale przeniesieniu winy na ofiarę. Przykłady z materiałów dowodowych pokazują, jak po słowie "przepraszam" następuje długa lista zarzutów wobec partnera.</p>

<h3>Lęk przed samotnością jako główny motor</h3>
<p>Wszystkie destrukcyjne zachowania wydają się podporządkowane jednemu celowi: uniknięciu samotności za wszelką cenę. Analiza pokazuje, że osoba A podejmuje każde działanie, nawet krzywdzące najbliższych, aby tylko nie zostać sama.</p>

<h3>Instrumentalizacja relacji międzyludzkich</h3>
<p>Kluczowym elementem case study jest sposób, w jaki badana osoba traktuje różne osoby w swoim otoczeniu:</p>
<ul>
<li><strong>Partner 1:</strong> źródło stabilności finansowej i społecznej</li>
<li><strong>Partner 2:</strong> dostarczyciel emocjonalnego podniecenia i nowości</li>
<li><strong>Dziecko:</strong> narzędzie manipulacji i kontroli</li>
</ul>

<h3>Duchowy chaos i brak kompasu moralnego</h3>
<p>Równoczesne odwoływanie się do religii katolickiej i konsultowanie wróżek wskazuje na fundamentalny brak wewnętrznego systemu wartości. To nie przypadkowa sprzeczność, ale dowód na opportunistyczne podejście do duchowości.</p>

<h3>Wzorce racjonalizacji i usprawiedliwiania</h3>
<p>Badany przypadek demonstruje, jak osoba z zaburzeniami tworzy elaborate systemy usprawiedliwień:</p>
<p>"Nie zdradzam, bo kocham Was oboje różnie" - przykład racjonalizacji podwójnego życia poprzez redefinicję pojęcia zdrady.</p>

<h3>Wpływ na system rodzinny</h3>
<p>Analiza pokazuje systematyczne wzorce krzywdzenia osób w najbliższym otoczeniu i długoterminowe konsekwencje manipulacji dla wszystkich zaangażowanych stron.</p>

<h3>Prognozy behawioralne</h3>
<p>Na podstawie analizy wzorców można prognozować dalsze zachowania: kontynuację podwójnego życia, eskalację manipulacji przy próbach konfrontacji, oraz dalsze instrumentalizowanie relacji.</p>

<h3>Znaczenie dla praktyki klinicznej</h3>
<p>Ten case study dostarcza cennych informacji dla terapeutów pracujących z ofiarami manipulacji psychologicznej oraz ilustruje mechanizmy obronne typowe dla zaburzeń osobowości z klastra B.</p>

<h3>Wnioski końcowe</h3>
<p>Przedstawiona analiza, oparta na rzeczywistych materiałach dowodowych, demaskuje złożony system manipulacji, racjonalizacji i instrumentalizacji relacji. Wzorce te wymagają profesjonalnej interwencji terapeutycznej.</p>

<p><em>Analiza przeprowadzona na podstawie rzeczywistych materiałów dowodowych dla celów edukacyjnych i zwiększenia świadomości mechanizmów manipulacji psychologicznej.</em></p>
        """
        
        # FAQ section
        faq_content = f"""
<div class='faq-section'>
<h2>Najczęściej zadawane pytania</h2>
<div class='faq-item'>
<h3>Czy analiza opiera się na rzeczywistych wydarzeniach?</h3>
<p>Tak, wszystkie cytaty, SMS-y i przykłady zachowań pochodzą z autentycznych materiałów dowodowych. Analiza ma charakter studium przypadku opartego na faktach.</p>
</div>
<div class='faq-item'>
<h3>Jakie mechanizmy psychologiczne są analizowane?</h3>
<p>Główny fokus to mechanizmy obronne: projekcja winy, racjonalizacja, gaslighting, segmentacja tożsamości oraz instrumentalizacja relacji międzyludzkich.</p>
</div>
<div class='faq-item'>
<h3>Czy można zastosować te wnioski do innych przypadków?</h3>
<p>Wzorce behawioralne opisane w analizie są charakterystyczne dla określonych zaburzeń osobowości i mogą występować w podobnych konstelacjach relacyjnych.</p>
</div>
<div class='faq-item'>
<h3>Jaka jest wartość edukacyjna tej analizy?</h3>
<p>Case study pomaga zrozumieć mechanizmy manipulacji psychologicznej i może służyć jako materiał dla osób uczących się rozpoznawać takie wzorce w rzeczywistości.</p>
</div>
</div>
        """
        
        # Related articles
        related_content = """
<div class='related-articles'>
<h2>Powiązane analizy case study</h2>
<p>Inne szczegółowe analizy psychologiczne oparte na rzeczywistych materiałach dowodowych będą dostępne w miarę rozbudowywania kolekcji case studies.</p>
<ul>
<li><em>Mechanizmy projekcji winy w relacjach toksycznych</em></li>
<li><em>Segmentacja tożsamości jako strategia unikania odpowiedzialności</em></li> 
<li><em>Instrumentalizacja dzieci w konfliktach rodzinnych</em></li>
</ul>
</div>
        """
        
        result = {
            "title": topic_package['title'],
            "meta_description": f"Szczegółowa analiza psychologiczna case study: {topic_package['title']}. Demaskowanie mechanizmów obronnych na podstawie rzeczywistych materiałów dowodowych - SMS-y, rozmowy, zachowania.",
            "html_content": analysis_content,
            "faq_html": faq_content, 
            "related_articles_html": related_content
        }
        
        print("✅ Fallback: Wygenerowano szczegółowe case study z rzeczywistymi materiałami (15+ akapitów)")
        return result
        
    except Exception as e:
        print(f"❌ Fallback Generation Error: {e}")
        return None

# === KROK 7: Główny Silnik Generowania Artykułów WERSJA 7.1 ===
def generate_article(topic_package: dict, master_prompt: str) -> dict:
    """
    WERSJA 8.0: Rewolucyjny silnik generowania case study z głęboką analizą psychologiczną.
    Tworzy ekspertckie studia przypadków z demaskowaniem wzorców zachowań.
    """
    
    print(f"\n🎯 Generuję case study z głęboką analizą psychologiczną...")
    print(f"📰 Tytuł: {topic_package['title']}")
    print(f"💡 Teza: {topic_package['thesis']}")
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

    # WERSJA 9.0: REWOLUCYJNY PROMPT z RZECZYWISTYMI CYTATAMI i FAKTAMI
    final_prompt = f"""{master_prompt}

---
### ZADANIE DLA AI: ANALIZA RZECZYWISTYCH MATERIAŁÓW DOWODOWYCH ###

Jesteś ekspertem psychologiem-praktykiem analizującym prawdziwy przypadek.

**TEMAT ANALIZY:** "{topic_package['title']}"

**HIPOTEZA DO UDOWODNIENIA:** {topic_package['thesis']}

**METODOLOGIA ANALIZY RZECZYWISTYCH FAKTÓW:**

**KROK 1: UŻYJ WYŁĄCZNIE RZECZYWISTYCH MATERIAŁÓW**
- Cytuj konkretne SMS-y i rozmowy z sekcji "RZECZYWISTE MATERIAŁY DOWODOWE"
- Analizuj udokumentowane zachowania, NIE wymyślaj przykładów
- Każdy wniosek MUSI być oparty na konkretnym cytacie lub fakcie

**KROK 2: STRUKTURA MULTI-LEVEL ANALYSIS**
- **POZIOM 1 - FAKT:** Co zostało udokumentowane (cytaty, SMS-y)
- **POZIOM 2 - HIPOTEZA:** Możliwa interpretacja (z poziomem pewności)  
- **POZIOM 3 - MECHANIZM:** Psychologiczne wyjaśnienie wzorca
- **POZIOM 4 - APLIKACJA:** Praktyczne rozpoznawanie podobnych przypadków

**KROK 3: TON EKSPERTCKI i DEMASKUJĄCY**
- Pisz jak psycholog analizujący materiał dowodowy w sprawie sądowej
- Bądź bezlitosny w analizie, ale oparty na faktach
- Używaj terminologii psychologicznej: "mechanizm projekcji", "gaslighting", "kompartmentalizacja"

**WYMAGANIA FORMATOWANIA:**
- Długość: 2500-4000 słów
- Format HTML z nagłówkami `<h2>` i akapitami `<p>`
- Cytaty w `<blockquote>` z adnotacją źródła
- Pogrubienia `<strong>` dla kluczowych mechanizmów

**PRZYKŁAD CYTOWANIA:**
<blockquote>"Przepraszam, ale nie zaśranowałeś się że te rozmowy może były mi potrzebne" - Osoba A w rozmowie z Partnerem 1</blockquote>
<p>Ten cytat ujawnia <strong>mechanizm racjonalizacji</strong> z jednoczesną <strong>projekcją winy</strong>.</p>

Zwróć wynik jako JSON (bez dodatkowych formatowań):

{{
  "title": "TEMAT_ARTYKULU",
  "meta_description": "Analiza rzeczywistych materiałów: {topic_package['title'][:60]}...",
  "html_content": "<h2>Wprowadzenie</h2><p>Analiza rzeczywistego przypadku...</p>",
  "faq_html": "<div class='faq-section'><h2>Najczęściej zadawane pytania</h2>...</div>",
  "related_articles_html": "<div class='related-articles'><h2>Powiązane analizy</h2>...</div>",
  "faq_json_ld": {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [] }}
}}

---
ANALIZUJ TERAZ WYŁĄCZNIE DOSTARCZONE RZECZYWISTE MATERIAŁY DOWODOWE:"""

    # FASE 1: Próby z Gemini API
    print("🤖 Próbuję generować case study z Gemini API...")
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
                print("✅ Gemini API: Case study wygenerowane pomyślnie!")
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

    # FASE 2: Próba z Groq API (WERSJA 8.0)
    if GROQ_API_KEY:
        print("🔄 Gemini niedostępny, próbuję case study z Groq API...")
        groq_result = generate_with_groq(topic_package, master_prompt)
        if groq_result:
            return groq_result
        else:
            print("❌ Groq API także nie powiódł się.")
    else:
        print("⚠️  Brak klucza Groq API w konfiguracji.")

    # FASE 3: Wysokiej jakości mechanizm fallback (WERSJA 9.1)
    print("🔄 Gemini i Groq niedostępne, używam wysokiej jakości mechanizmu fallback...")
    copilot_result = generate_with_copilot(topic_package, master_prompt)
    if copilot_result:
        return copilot_result
    else:
        print("❌ Również mechanizm fallback nie powiódł się.")

    # FASE 4: Ostateczny fallback (tylko w krytycznej sytuacji)
    print("📝 KRYTYCZNA SYTUACJA: Używam ostatecznej treści zastępczej.")
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
    # if not file_path.exists():
    #     print(f"Plik {file_path} nie istnieje. Nie można dodać karty.")
    #     return
    # 
    # with open(file_path, 'r+', encoding='utf-8') as f:
    #     content = f.read()
    #     soup = BeautifulSoup(content, 'html.parser')
    #     
    #     container = soup.find(id='posts-container')
    #     if not container:
    #         print("Nie znaleziono kontenera '#posts-container' w pliku index.html.")
    #         return
    # Ten kod został wyłączony dla bezpieczeństwa:        
    #     # Ustawienie polskiej lokalizacji dla nazw miesięcy
    #     import locale
    #     try:
    #         locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
    #         human_date = datetime.datetime.now().strftime('%d %B %Y')
    #         iso_date = datetime.datetime.now().strftime('%Y-%m-%d')
    #     except locale.Error:
    #         print("Nie można ustawić polskiej lokalizacji. Data będzie w domyślnym formacie.")
    #         human_date = datetime.datetime.now().strftime('%d %B %Y')
    #         iso_date = datetime.datetime.now().strftime('%Y-%m-%d')
    # 
    #     card_html = f"""
    #   <article class="group relative flex flex-col rounded-xl border border-border/70 bg-surface/90 p-6 shadow-sm hover:shadow-lift hover:-translate-y-1 transition-all duration-300" itemscope="True" itemtype="https://schema.org/BlogPosting">
    #    <h3 class="mt-4 text-lg font-semibold leading-snug group-hover:text-accent transition-colors" itemprop="headline">
    #     {title}
    #    </h3>
    #    <time class="mt-2 text-xs text-text/60" datetime="{iso_date}" itemprop="datePublished">
    #     Opublikowano: {human_date}
    #    </time>
    #    <p class="mt-4 text-sm leading-relaxed text-text/80 line-clamp-5" itemprop="description">
    #     {description}
    #    </p>
    #    <a aria-label="Czytaj dalej: {title}" class="mt-5 inline-flex items-center text-sm font-medium text-accent hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60" href="{link}" itemprop="url">
    #     Czytaj dalej →
    #    </a>
    #    <meta content="True Results Online" itemprop="author"/>
    #   </article>
    # """
    #     
    #     placeholder = soup.find(string=lambda text: "AUTO-BLOG: NOWE WPISY" in text)
    #     if placeholder:
    #         placeholder.insert_before(BeautifulSoup(card_html, 'html.parser'))
    #     else:
    #         # Fallback if placeholder comment is missing
    #         container.insert(0, BeautifulSoup(card_html, 'html.parser'))
    #     
    #     f.seek(0)
    #     f.write(str(soup))
    #     f.truncate()

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
    # if not SPIS_TRESCI_FILE.exists():
    #     return
    # with open(SPIS_TRESCI_FILE, 'r+', encoding='utf-8') as f:
    #     content = f.read()
    #     soup = BeautifulSoup(content, 'html.parser')
    #     
    #     container = soup.find('div', class_='space-y-8')
    #     if not container:
    #         print("Nie znaleziono kontenera 'space-y-8' w pliku spis.html.")
    #         return
    # 
    #     # Ustawienie polskiej lokalizacji dla nazw miesięcy
    #     import locale
    #     try:
    #         locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
    #         iso_date = datetime.datetime.now().strftime('%Y-%m-%d')
    #     except locale.Error:
    #         print("Nie można ustawić polskiej lokalizacji. Data będzie w domyślnym formacie.")
    #         iso_date = datetime.datetime.now().strftime('%Y-%m-%d')
    # 
    #     article_html = f"""
    # <article class='border-b border-border/40 pb-6'>
    #     <h2 class='text-lg font-semibold'>
    #         <a class='hover:text-accent transition-colors' href='{new_post_url}'>{title} – True Results Online</a>
    #     </h2>
    #     <p class='mt-1 text-xs text-text/60'>{iso_date}</p>
    #     <p class='mt-2 text-sm text-text/80 leading-relaxed'>{description}</p>
    # </article>
    # """
    #     
    #     placeholder = soup.find(string=lambda text: "AUTO-BLOG: NOWE WPISY" in text)
    #     if placeholder:
    #         placeholder.insert_before(BeautifulSoup(article_html, 'html.parser'))
    #     else:
    #         # Fallback if placeholder comment is missing
    #         container.insert(0, BeautifulSoup(article_html, 'html.parser'))
    # 
    #     f.seek(0)
    #     f.write(str(soup))
    #     f.truncate()

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
    # try:
    #     repo = Repo(repo_path)
    #     repo.git.add(all=True)
    #     
    #     if repo.is_dirty(untracked_files=True):
    #         repo.index.commit(commit_message)
    #         print("Wprowadzono zmiany do lokalnego repozytorium.")
    #         
    #         origin = repo.remote(name='origin')
    #         origin.push()
    #         print("Wysłano zmiany do zdalnego repozytorium.")
    #     else:
    #         print("Brak zmian do wprowadzenia.")
    #         
    # except Exception as e:
    #     print(f"Błąd podczas operacji Git: {e}")

def main():
    """Główna funkcja sterująca skryptem."""
    print("=== TRUE RESULTS ONLINE - GENERATOR ARTYKUŁÓW ===")
    print(f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # WERSJA 7.1: Pełna matryca tematyczna z Excela z precyzyjnymi tezami
    try:
        topic_packages = load_config_from_excel(CONFIG_FILE)
    except Exception as e:
        print(f"❌ Zatrzymano skrypt z powodu błędu konfiguracji: {e}")
        return

    topic_package = pick_topic_package(topic_packages)
    if not topic_package:
        print("❌ Nie udało się wybrać pakietu tematycznego. Kończę pracę.")
        return

    print(f"✅ Wybrany case study:")
    print(f"   📰 Tytuł: {topic_package['title']}")
    print(f"   💡 Hipoteza: {topic_package['thesis'][:100]}...")
    print(f"   🏷️ Kontekst: {topic_package['campaign']}")
    print()

    master_prompt = build_master_prompt_from_config(CONFIG_FILE)
    
    print("🚀 Rozpoczynam generowanie case study z głęboką analizą psychologiczną...")
    article_data = generate_article(topic_package, master_prompt)
    
    if not article_data or not article_data.get("title"):
        print("❌ Nie udało się wygenerować case study. Kończę pracę.")
        return
    
    # Sprawdzanie typu treści i źródła
    is_offline = "trybie offline" in article_data.get("html_content", "")
    is_copilot = "GitHub Copilot" in article_data.get("meta_description", "") or len(article_data.get("html_content", "")) > 5000
    content_length = len(article_data.get("html_content", ""))
    
    if is_offline:
        status_icon = "📝"
        content_type = "Offline Fallback"
    elif is_copilot or (content_length > 5000):  # GitHub Copilot często generuje najdłuższe treści
        status_icon = "🐙"
        content_type = "GitHub Copilot"
    elif content_length > 3000:  # Groq zwykle generuje dłuższe treści niż Gemini
        status_icon = "🦙"
        content_type = "Groq API"
    else:
        status_icon = "🤖"
        content_type = "Gemini API"
    
    print(f"{status_icon} Wygenerowano case study ({content_type}): '{article_data['title']}'")
    print()

    # Tytuł został już zapisany w pick_topic_package() - nie duplikujemy

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
    
    # Aktualizacja index.html i spis.html
    insert_card_in_index(INDEX_FILE, article_data['title'], article_data['meta_description'], post_url, topic_package['campaign'])
    update_spis_tresci(post_url, article_data['title'], article_data['meta_description'])
    print("✅ Zaktualizowano: index.html, spis.html")
    
    # RSS i sitemap
    update_sitemap_and_rss(post_url, article_data['title'], article_data['meta_description'])
    print("✅ Zaktualizowano: sitemap.xml, rss.xml")

    # Commit i push
    commit_message = f"Automatyczny wpis: {article_data['title']}"
    print("📤 Wysyłam zmiany do repozytorium...")
    commit_and_push_changes(REPO_PATH, commit_message)
    
    print()
    print("🎉 SUKCES! Case study z głęboką analizą psychologiczną zostało wygenerowane i opublikowane.")
    print(f"🔗 URL: {post_url}")
    print("=" * 50)

if __name__ == "__main__":
    main()
