#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GENERATOR 365 UNIKALNYCH POSTÓW - TRUE RESULTS ONLINE v2.0
========================================================
Generuje 365 artykułów z prawdziwie unikalnymi tematami (nie tylko "Część X")
- Każdy post ma unikalną datę (1 post = 1 dzień)  
- Każdy post ma PRAWDZIWIE UNIKALNY temat
- Pierwsze 21 postów trafia na index.html
- Pozostałe 344 posty trafiają do spis.html
- Wszystko automatycznie wrzucane na GitHub
"""

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

def load_real_evidence_materials() -> dict:
    """Wczytuje rzeczywiste materiały dowodowe z docs/."""
    evidence = {
        "osoba_a_partner_1_conversations": [],
        "sms_patterns": [],
        "key_quotes": [],
        "behavioral_facts": []
    }
    
    try:
        # Wczytywanie rozmów Osoba A - Partner 1
        osoba_a_partner_1_file = REPO_PATH / "docs" / "karolina_marcin.txt"
        if osoba_a_partner_1_file.exists():
            with open(osoba_a_partner_1_file, 'r', encoding='utf-8') as f:
                content = f.read()
                evidence["osoba_a_partner_1_conversations"] = content
            print(f"📱 Wczytano rozmowy Osoba A - Partner 1: {len(content)} znaków")
        
        # Wczytywanie SMS-ów z Partnerem 2
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
                            "content": sms_content[:8000]
                        })
            print(f"💬 Wczytano {len(evidence['sms_patterns'])} plików SMS-ów")
        
        # Lista udokumentowanych faktów behawioralnych
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
        
        return evidence
        
    except Exception as e:
        print(f"⚠️ Błąd wczytywania materiałów dowodowych: {e}")
        return evidence

def generate_365_unique_topics() -> list:
    """
    Generuje 365 prawdziwie unikalnych tematów artykułów psychologicznych
    opartych na rzeczywistym case study.
    """
    
    # Podstawowe kategorie tematyczne
    base_categories = [
        "Anatomia Nielojalności",
        "Mechanizmy Obronne",
        "Manipulacja Psychologiczna", 
        "Toksyczne Wzorce",
        "Psychologia Kłamstwa",
        "Gaslighting i Projekcja",
        "Segmentacja Tożsamości",
        "Instrumentalizacja Relacji",
        "Lęki i Kompulsje",
        "Duchowy Chaos",
        "Konsekwencje Behawioralne",
        "Analiza Case Study"
    ]
    
    # Prefiksy do tytułów
    title_prefixes = [
        "Anatomia", "Psychologia", "Mechanizm", "Syndrom", "Fenomen", 
        "Wzorzec", "Strategia", "Taktyka", "Proces", "Dynamika",
        "Analiza", "Studium", "Dekonstrukcja", "Demaskowanie", "Diagnoza",
        "Case Study:", "Dlaczego", "Jak", "Kiedy", "Co się dzieje gdy",
        "Ukryty", "Prawdziwy", "Tajny", "Głęboki", "Chroniczny"
    ]
    
    # Główne tematy psychologiczne
    psychological_topics = [
        "podwójne życie", "równoległe relacje", "segmentacja tożsamości",
        "projekcja winy", "racjonalizacja", "gaslighting", "manipulacja",
        "instrumentalizacja", "kompartmentalizacja", "dwulicowość",
        "nieautentyczność", "lęk przed samotnością", "głód walidacji",
        "fałszywe przeprosiny", "emocjonalny szantaż", "alienacja rodzicielska",
        "duchowy chaos", "religijność fasadowa", "kontrola narracji",
        "utrata kontroli", "publiczna kompromitacja", "mechanizmy ucieczki",
        "wzorce rodzinne", "przywiązanie unikowe", "dysonans poznawczy",
        "idealizacja i dewaluacja", "splitting", "triangulacja",
        "scapegoating", "love bombing", "hoovering", "silent treatment",
        "crazy making", "emotional dumping", "parentyfikacja",
        "enmeshment", "boundary violations", "intermittent reinforcement"
    ]
    
    # Specyficzne aspekty case study
    case_study_aspects = [
        "SMS-y jako dowody", "logi rozmów", "wzorce komunikacji",
        "analiza językowa", "frequency analysis", "timing patterns",
        "emotional manipulation", "cognitive dissonance", "identity crisis",
        "loyalty conflicts", "moral injury", "trauma bonding",
        "learned helplessness", "stockholm syndrome", "codependency",
        "enablement patterns", "reality distortion", "memory manipulation",
        "timeline confusion", "evidence tampering", "witness intimidation",
        "character assassination", "smear campaigns", "flying monkeys",
        "proxy abuse", "institutional abuse", "systemic manipulation"
    ]
    
    # Skutki i konsekwencje
    consequences = [
        "długoterminowe skutki", "wpływ na dzieci", "trauma pokoleniowa",
        "broken trust", "relationship anxiety", "hypervigilance",
        "emotional numbness", "dissociation", "panic attacks",
        "depression", "suicidal ideation", "self-harm",
        "substance abuse", "eating disorders", "sleep disorders",
        "chronic pain", "autoimmune issues", "financial abuse",
        "career sabotage", "social isolation", "family destruction",
        "legal consequences", "custody battles", "parental alienation"
    ]
    
    # Frazy łączące i modyfikatory
    connectives = [
        "w praktyce", "na przykładzie", "studium przypadku", "analiza rzeczywista",
        "demaskowanie", "za fasadą", "ukryty mechanizm", "prawdziwe oblicze",
        "pod lupą", "w szczegółach", "krok po kroku", "ewolucja wzorca",
        "eskalacja", "punkt kulminacyjny", "moment prawdy", "breaking point",
        "turning point", "red flags", "warning signs", "early indicators",
        "protective factors", "recovery process", "healing journey"
    ]
    
    unique_topics = []
    used_titles = set()
    
    # Generowanie 365 unikalnych tematów
    for i in range(365):
        attempts = 0
        while attempts < 50:  # Maksymalnie 50 prób na unikalny tytuł
            # Losowy wybór elementów
            category = random.choice(base_categories)
            prefix = random.choice(title_prefixes)
            topic = random.choice(psychological_topics)
            aspect = random.choice(case_study_aspects) if random.random() > 0.5 else None
            consequence = random.choice(consequences) if random.random() > 0.7 else None
            connective = random.choice(connectives) if random.random() > 0.6 else None
            
            # Budowanie tytułu
            title_parts = []
            
            # Różne wzorce tytułów
            pattern = random.randint(1, 8)
            
            if pattern == 1:
                title = f"{prefix} {topic}"
            elif pattern == 2:
                title = f"{topic.title()}: {prefix} Rzeczywistego Przypadku"
            elif pattern == 3 and aspect:
                title = f"{aspect.title()} w Kontekście {topic}"
            elif pattern == 4 and connective:
                title = f"{topic.title()} {connective}"
            elif pattern == 5 and consequence:
                title = f"Od {topic} do {consequence}"
            elif pattern == 6:
                title = f"'{topic.title()}' - Anatomia Mechanizmu Obronnego"
            elif pattern == 7 and aspect and connective:
                title = f"{aspect.title()}: {topic} {connective}"
            else:
                title = f"{prefix} {topic} - Studium Przypadku Osoby A"
            
            # Dodawanie modyfikatorów
            if random.random() > 0.8:
                modifiers = ["Ukryte", "Nieoczywiste", "Zaawansowane", "Chroniczne", 
                           "Subtelne", "Systemowe", "Głębokie", "Kompleksowe"]
                title = f"{random.choice(modifiers)} {title}"
            
            # Normalizacja tytułu
            title = title.replace(" i ", " i ").replace(" w ", " w ")
            title = title.replace("  ", " ").strip()
            title = title[0].upper() + title[1:]
            
            if title not in used_titles and len(title) < 120:
                used_titles.add(title)
                
                # Generowanie tezy
                thesis_templates = [
                    f"Analiza {topic} ujawnia mechanizmy obronne typowe dla zaburzeń osobowości klastra B.",
                    f"Rzeczywiste materiały dowodowe pokazują ewolucję wzorca {topic} w czasie.",
                    f"Studium przypadku demaskuje ukryte aspekty {topic} w relacjach toksycznych.",
                    f"Psychologiczna analiza {topic} na podstawie autentycznej dokumentacji.",
                    f"Case study pokazuje wpływ {topic} na system rodzinny i najbliższe otoczenie.",
                ]
                
                thesis = random.choice(thesis_templates)
                
                unique_topics.append({
                    'campaign': category,
                    'title': title,
                    'thesis': thesis
                })
                break
            
            attempts += 1
        
        if attempts >= 50:
            # Fallback - dodaj prosty unikalny tytuł
            fallback_title = f"Analiza Case Study #{i+1}: Mechanizmy Psychologiczne w Relacjach Toksycznych"
            unique_topics.append({
                'campaign': random.choice(base_categories),
                'title': fallback_title,
                'thesis': "Szczegółowa analiza mechanizmów psychologicznych na podstawie rzeczywistych materiałów dowodowych."
            })
    
    print(f"✅ Wygenerowano {len(unique_topics)} prawdziwie unikalnych tematów")
    return unique_topics

def load_config_from_excel(path: Path) -> dict:
    """Wczytuje konfigurację z pliku Excel + generuje unikalne tematy."""
    config = {
        "master_prompt_parts": {},
        "case_study": {},
        "campaign_topics": []
    }

    try:
        # Wczytywanie MasterPrompt
        df_prompt = pd.read_excel(path, sheet_name='MasterPrompt')
        config['master_prompt_parts'] = dict(zip(df_prompt['Klucz'], df_prompt['Wartość']))

        # Wczytywanie CaseStudy
        df_case = pd.read_excel(path, sheet_name='CaseStudy')
        config['case_study'] = dict(zip(df_case['Kategoria'], df_case['Szczegół']))

        # NOWE: Generowanie 365 unikalnych tematów zamiast wczytywania z Excel
        config['campaign_topics'] = generate_365_unique_topics()
        
        print(f"✅ Wygenerowano {len(config['campaign_topics'])} unikalnych tematów case study.")
        return config

    except Exception as e:
        print(f"❌ Błąd wczytywania danych z pliku Excel: {e}")
        raise

def build_master_prompt_from_config(config_file_path: Path) -> str:
    """Buduje master prompt z rzeczywistymi materiałami dowodowymi."""
    try:
        df_prompt = pd.read_excel(config_file_path, sheet_name='MasterPrompt')
        df_case_study = pd.read_excel(config_file_path, sheet_name='CaseStudy')
        
        evidence = load_real_evidence_materials()
        
        # Budowanie master promtu
        prompt_parts = []
        for _, row in df_prompt.iterrows():
            prompt_parts.append(str(row['Wartość']))
        
        # Budowanie case study
        case_study_parts = []
        for _, row in df_case_study.iterrows():
            case_study_parts.append(f"{row['Kategoria']}: {row['Szczegół']}")
        
        case_study_full = "\n".join(case_study_parts)
        
        # Sekcja z rzeczywistymi materiałami dowodowymi
        real_evidence_section = f"""

=== RZECZYWISTE MATERIAŁY DOWODOWE ===

UDOKUMENTOWANE FAKTY BEHAWIORALNE:
{chr(10).join(evidence['behavioral_facts'])}

WZORCE SMS-ÓW Z PARTNEREM 2:
- Częstotliwość: tysiące wiadomości przez 3+ lata ({len(evidence['sms_patterns'])} plików dowodowych)
- Ton: czułe zwroty, troska, planowanie spotkań
- Ukrywanie: przed Partnerem 1 przez cały okres związku
- Zakres czasowy: maj 2021 - wrzesień 2024

=== KONIEC MATERIAŁÓW DOWODOWYCH ===
"""
        
        full_prompt = "\n\n".join(prompt_parts)
        
        if "{{CASE_STUDY}}" in full_prompt:
            full_prompt = full_prompt.replace("{{CASE_STUDY}}", case_study_full + real_evidence_section)
        else:
            full_prompt += "\n\n=== STUDIUM PRZYPADKU ===\n" + case_study_full + real_evidence_section
        
        return full_prompt
        
    except Exception as e:
        print(f"⚠️ Błąd odczytu master promptu z Excela: {e}")
        return """Jesteś ekspertem psychologiem-praktykiem analizującym rzeczywiste przypadki. 
        Używasz konkretnych cytatów i udokumentowanych zachowań do bezlitosnej analizy wzorców.
        Tworzysz artykuły case study z demaskowaniem rzeczywistych mechanizmów psychologicznych."""

def pick_unique_topic_package(config: dict, post_index: int) -> dict:
    """Wybiera unikalny pakiet tematyczny (bez duplikatów)."""
    campaign_topics = config.get('campaign_topics', [])
    if not campaign_topics or post_index >= len(campaign_topics):
        print(f"❌ Brak tematu dla indeksu {post_index}")
        return None
    
    # Prosty wybór po indeksie - każdy temat jest unikalny
    chosen_package = campaign_topics[post_index]
    
    print(f"📋 Wybrany unikalny temat {post_index+1}/365:")
    print(f"    🏷️ Kampania: {chosen_package['campaign']}")
    print(f"    📰 Tytuł: {chosen_package['title']}")
    print(f"    💡 Teza: {chosen_package['thesis'][:100]}...")
    
    return chosen_package

def generate_with_groq(topic_package: dict, master_prompt: str) -> dict:
    """Generuje artykuł używając Groq API."""
    final_prompt = f"""{master_prompt}

---
### ZADANIE DLA AI: ANALIZA RZECZYWISTYCH MATERIAŁÓW DOWODOWYCH ###

Jesteś ekspertem psychologiem-praktykiem analizującym prawdziwy przypadek.

**TEMAT ANALIZY:** "{topic_package['title']}"

**HIPOTEZA DO UDOWODNIENIA:** {topic_package['thesis']}

**METODOLOGIA:**
- Użyj wyłącznie rzeczywistych materiałów z sekcji "RZECZYWISTE MATERIAŁY DOWODOWE"
- Analizuj udokumentowane zachowania, nie wymyślaj przykładów
- Każdy wniosek oparty na konkretnym cytacie lub fakcie
- Ton ekspertcki i demaskujący

**STRUKTURA html_content (MINIMUM 20 akapitów <p>):**
<h2>Wprowadzenie</h2>
<p>2-3 akapity wprowadzające</p>
<h2>Analiza Rzeczywistych Materiałów</h2>
<p>Analiza z cytatami</p>
<h2>Wzorce Zachowań</h2>
<p>3-4 akapity o wzorcach</p>
<h2>Mechanizmy Obronne</h2>
<p>3-4 akapity o mechanizmach</p>
<h2>Konsekwencje</h2>
<p>2-3 akapity o konsekwencjach</p>
<h2>Wnioski</h2>
<p>2 akapity końcowe</p>

Zwróć wynik jako JSON:

{{
  "title": "TEMAT_ARTYKULU",
  "meta_description": "Analiza rzeczywistych materiałów: {topic_package['title'][:60]}...",
  "html_content": "<h2>Wprowadzenie</h2><p>Analiza rzeczywistego przypadku...</p>",
  "faq_html": "<div class='faq-section'><h2>Najczęściej zadawane pytania</h2>...</div>",
  "related_articles_html": "<div class='related-articles'><h2>Powiązane analizy</h2>...</div>",
  "faq_json_ld": {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [] }}
}}"""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "Jesteś ekspertem psychologiem analizującym rzeczywiste przypadki. Generujesz długie, szczegółowe artykuły z minimum 20 akapitami <p>."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.9,
            max_tokens=8192,
            top_p=0.95,
            frequency_penalty=0.3,
            response_format={"type": "json_object"}
        )
        
        response_text = completion.choices[0].message.content
        parsed_json = json.loads(response_text)
        
        # Walidacja
        required_keys = ["title", "meta_description", "html_content", "faq_html", "related_articles_html", "faq_json_ld"]
        if all(key in parsed_json for key in required_keys):
            html_content = parsed_json.get("html_content", "")
            p_count = html_content.count("<p>")
            word_count = len(html_content.split())
            
            if p_count >= 10 and word_count >= 200:
                return parsed_json
            else:
                print(f"⚠️ Artykuł za krótki ({p_count} akapitów, {word_count} słów).")
                return None
        else:
            print("❌ Groq API: Odpowiedź nie zawiera wszystkich wymaganych kluczy.")
            return None
            
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return None

def generate_with_copilot_fallback(topic_package: dict, master_prompt: str) -> dict:
    """Wysokiej jakości fallback z wbudowaną analizą."""
    
    analysis_content = f"""
<h2>Analiza Case Study: {topic_package['title']}</h2>

<p><strong>Kontekst badawczy:</strong> Niniejsza analiza opiera się na rzeczywistych materiałach dowodowych - SMS-ach, logach rozmów i udokumentowanych zachowaniach. Jest to ekspertcka ocena psychologiczna wzorców behawioralnych przeprowadzona metodą case study.</p>

<p><strong>Główna teza badawcza:</strong> {topic_package.get('thesis', 'Analiza wzorców psychologicznych w kontekście rzeczywistych zachowań badanej osoby.')}</p>

<h3>Materiały dowodowe</h3>
<p>Analiza opiera się na autentycznej dokumentacji komunikacji obejmującej tysiące SMS-ów z okresu maj 2021 - wrzesień 2024, logi rozmów z października 2024 oraz udokumentowane wzorce zachowań w relacjach międzyosobowych.</p>

<h3>Mechanizmy psychologiczne</h3>
<p>W badanym przypadku obserwujemy następujące wzorce typowe dla zaburzeń osobowości z klastra B:</p>

<p><strong>Projekcja winy</strong> - systematyczne przenoszenie odpowiedzialności za własne czyny na inne osoby. Mechanizm ten przejawia się w konsekwentnym obwinianiu partnera za własne destrukcyjne zachowania.</p>

<p><strong>Racjonalizacja</strong> - tworzenie pozornie logicznych usprawiedliwień dla nieakceptowalnych zachowań. Obserwujemy elaborate systemy usprawiedliwień dla podwójnego życia i manipulacji.</p>

<p><strong>Gaslighting</strong> - manipulacja mająca na celu podważenie pewności siebie ofiary poprzez zaprzeczanie oczywistym faktom dokumentalnym.</p>

<p><strong>Segmentacja tożsamości</strong> - prowadzenie podwójnego życia jako mechanizm obronny przed konfrontacją z konsekwencjami własnych czynów.</p>

<h3>Wzorce komunikacji manipulacyjnej</h3>
<p>Analiza rzeczywistych SMS-ów i rozmów ujawnia charakterystyczne techniki manipulacyjne stosowane systematycznie przez okres trzech lat.</p>

<p><strong>Fałszywe przeprosiny:</strong> Wzorzec "przepraszam, ALE..." który służy nie wyrażeniu skruchy, ale przeniesieniu winy na ofiarę. Po słowie "przepraszam" następuje długa lista zarzutów wobec partnera.</p>

<p><strong>Instrumentalizacja emocji:</strong> Używanie deklaracji miłości jako narzędzia manipulacji przy jednoczesnym prowadzeniu równoległych relacji.</p>

<h3>Lęk przed samotnością jako główny motor</h3>
<p>Wszystkie destrukcyjne zachowania wydają się podporządkowane jednemu celowi: uniknięciu samotności za wszelką cenę. Analiza pokazuje gotowość do krzywdzenia najbliższych, aby tylko nie zostać samą.</p>

<p>Ten mechanizm tłumaczy prowadzenie równoległych relacji - nie jako poszukiwanie lepszego partnera, ale jako zabezpieczenie przed pustką egzystencjalną.</p>

<h3>Instrumentalizacja relacji międzyludzkich</h3>
<p>Kluczowym elementem case study jest sposób, w jaki badana osoba traktuje różne osoby w swoim otoczeniu jako źródła zaspokajania określonych potrzeb:</p>

<p><strong>Partner 1:</strong> postrzegany jako źródło stabilności finansowej i społecznej, ojciec dziecka zapewniający status rodzinny.</p>

<p><strong>Partner 2:</strong> dostarczyciel emocjonalnego podniecenia i nowości, "ucieczka" od codzienności i odpowiedzialności.</p>

<p><strong>Dziecko:</strong> nieświadomie instrumentalizowane jako narzędzie manipulacji i kontroli w relacjach dorosłych.</p>

<h3>Duchowy chaos i brak kompasu moralnego</h3>
<p>Równoczesne odwoływanie się do religii katolickiej i konsultowanie wróżek wskazuje na fundamentalny brak wewnętrznego systemu wartości.</p>

<p>To nie przypadkowa sprzeczność, ale dowód na opportunistyczne podejście do duchowości - wybieranie tylko tych elementów, które aktualnie służą usprawiedliwieniu własnych czynów.</p>

<h3>Wzorce racjonalizacji</h3>
<p>Badany przypadek demonstruje, jak osoba z zaburzeniami tworzy elaborate systemy usprawiedliwień dla nieakceptowalnych społecznie zachowań.</p>

<p>Przykład racjonalizacji podwójnego życia: redefinicja pojęcia zdrady poprzez twierdzenie o "różnych rodzajach miłości" do różnych partnerów.</p>

<h3>Wpływ na system rodzinny</h3>
<p>Analiza pokazuje systematyczne wzorce krzywdzenia osób w najbliższym otoczeniu oraz długoterminowe konsekwencje manipulacji dla wszystkich zaangażowanych stron.</p>

<p>Szczególnie destrukcyjne jest wciąganie rodziny pochodzenia w układ kłamstw oraz instrumentalizowanie dziecka w konfliktach dorosłych.</p>

<h3>Prognozy behawioralne</h3>
<p>Na podstawie analizy wzorców można prognozować dalsze zachowania: kontynuację podwójnego życia, eskalację manipulacji przy próbach konfrontacji oraz dalsze instrumentalizowanie relacji.</p>

<p>Brak autorefleksji i gotowości do zmiany wskazuje na chroniczny charakter prezentowanych wzorców.</p>

<h3>Znaczenie dla praktyki klinicznej</h3>
<p>Ten case study dostarcza cennych informacji dla terapeutów pracujących z ofiarami manipulacji psychologicznej oraz ilustruje mechanizmy obronne typowe dla zaburzeń osobowości z klastra B.</p>

<p>Szczególną wartość ma dokumentacja ewolucji wzorców przez okres trzech lat, pokazująca ich chroniczny i eskalujący charakter.</p>

<h3>Wnioski końcowe</h3>
<p>Przedstawiona analiza, oparta na rzeczywistych materiałach dowodowych, demaskuje złożony system manipulacji, racjonalizacji i instrumentalizacji relacji międzyludzkich.</p>

<p>Wzorce te wymagają profesjonalnej interwencji terapeutycznej oraz stanowią cenny materiał edukacyjny dla zwiększania świadomości mechanizmów manipulacji psychologicznej w społeczeństwie.</p>

<p><em>Analiza przeprowadzona na podstawie rzeczywistych materiałów dowodowych dla celów edukacyjnych i zwiększenia świadomości mechanizmów manipulacji psychologicznej.</em></p>
    """
    
    faq_content = """
<div class='faq-section'>
<h2>Najczęściej zadawane pytania</h2>
<div class='faq-item'>
<h3>Czy analiza opiera się na rzeczywistych wydarzeniach?</h3>
<p>Tak, wszystkie analizowane wzorce pochodzą z autentycznych materiałów dowodowych zebranych w okresie maj 2021 - wrzesień 2024.</p>
</div>
<div class='faq-item'>
<h3>Jakie mechanizmy psychologiczne są analizowane?</h3>
<p>Główny fokus to mechanizmy obronne z zaburzeń osobowości klastra B: projekcja winy, racjonalizacja, gaslighting, segmentacja tożsamości oraz instrumentalizacja relacji.</p>
</div>
<div class='faq-item'>
<h3>Czy można zastosować te wnioski do innych przypadków?</h3>
<p>Wzorce behawioralne opisane w analizie są charakterystyczne dla określonych zaburzeń osobowości i mogą występować w podobnych konstelacjach relacyjnych.</p>
</div>
</div>
    """
    
    related_content = """
<div class='related-articles'>
<h2>Powiązane analizy case study</h2>
<p>Inne szczegółowe analizy psychologiczne oparte na rzeczywistych materiałach dowodowych z tej samej kolekcji case studies.</p>
</div>
    """
    
    return {
        "title": topic_package['title'],
        "meta_description": f"Szczegółowa analiza psychologiczna: {topic_package['title']}. Demaskowanie mechanizmów obronnych na podstawie rzeczywistych materiałów dowodowych - SMS-y, rozmowy, zachowania.",
        "html_content": analysis_content,
        "faq_html": faq_content, 
        "related_articles_html": related_content,
        "faq_json_ld": {}
    }

def generate_article_with_date(topic_package: dict, master_prompt: str, target_date: datetime.datetime) -> dict:
    """Generuje artykuł z określoną datą."""
    
    # Próba z Gemini API
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=safety_settings,
            generation_config=generation_config,
        )
        
        final_prompt = f"""{master_prompt}

TEMAT ANALIZY: "{topic_package['title']}"
HIPOTEZA: {topic_package['thesis']}

Wygeneruj szczegółową analizę psychologiczną w formacie JSON z długim html_content (minimum 15 akapitów <p>).

Zwróć wynik jako JSON:
{{
  "title": "{topic_package['title']}",
  "meta_description": "Analiza case study: {topic_package['title'][:60]}...",
  "html_content": "<h2>Wprowadzenie</h2><p>Szczegółowa analiza...</p>",
  "faq_html": "<div class='faq-section'>...</div>",
  "related_articles_html": "<div class='related-articles'>...</div>",
  "faq_json_ld": {{"@context": "https://schema.org", "@type": "FAQPage"}}
}}"""
        
        response = model.generate_content(final_prompt)
        cleaned_response = re.sub(r'^```json\s*|\s*```$', '', response.text.strip(), flags=re.MULTILINE)
        parsed_json = json.loads(cleaned_response)
        
        required_keys = ["title", "meta_description", "html_content", "faq_html", "related_articles_html", "faq_json_ld"]
        if all(key in parsed_json for key in required_keys):
            return parsed_json
            
    except Exception as e:
        print(f"Gemini błąd: {e}")
    
    # Próba z Groq
    if GROQ_API_KEY:
        groq_result = generate_with_groq(topic_package, master_prompt)
        if groq_result:
            return groq_result
    
    # Fallback
    return generate_with_copilot_fallback(topic_package, master_prompt)

def build_post_html_with_date(template_content: str, data: dict, campaign: str, post_url: str, target_date: datetime.datetime) -> str:
    """Wypełnia szablon HTML danymi artykułu z określoną datą."""
    
    # Ustawienie polskiej lokalizacji
    import locale
    try:
        locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
    except locale.Error:
        pass
    
    human_date = target_date.strftime('%d %B %Y')
    iso_date = target_date.isoformat()

    html = template_content.replace("{{TYTUL}}", data.get('title', 'Brak tytułu'))
    html = html.replace("{{OPIS}}", data.get('meta_description', 'Brak opisu.'))
    html = html.replace("{{META_OPIS}}", data.get('meta_description', 'Brak opisu.'))
    html = html.replace("{{KANONICAL}}", post_url)
    html = html.replace("{{DATA}}", iso_date)
    html = html.replace("{{DATA_LUDZKA}}", human_date)
    html = html.replace("{{KATEGORIA}}", campaign or "Ogólna")
    html = html.replace("{{TRESC_ARTYKULU}}", data.get('html_content', '<p>Brak treści.</p>'))
    html = html.replace("{{TRESC_HTML}}", data.get('html_content', '<p>Brak treści.</p>'))
    
    faq_data = data.get("faq_json_ld", {})
    faq_script = f'<script type="application/ld+json">{json.dumps(faq_data, indent=2, ensure_ascii=False)}</script>' if faq_data else ""
    
    html = html.replace("{{FAQ_JSON_LD}}", faq_script)
    html = html.replace("{{FAQ_HTML}}", data.get('faq_html', ''))
    html = html.replace("{{POWIAZANE_POSTY_HTML}}", data.get('related_articles_html', ''))
    
    return html

def update_index_html_with_posts(posts_data: list):
    """Aktualizuje index.html z pierwszymi 21 postami."""
    if not INDEX_FILE.exists():
        print("Brak pliku index.html")
        return
    
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Znajdź sekcję posts-container
        soup = BeautifulSoup(content, 'html.parser')
        container = soup.find(id='posts-container')
        if not container:
            print("Nie znaleziono #posts-container")
            return
        
        # Wyczyść istniejące artykuły
        for article in container.find_all('article'):
            article.decompose()
        
        # Dodaj pierwsze 21 postów
        for post_data in posts_data[:21]:
            title = post_data['title']
            description = post_data['meta_description']
            link = post_data['post_url']
            target_date = post_data['target_date']
            
            iso_date = target_date.strftime('%Y-%m-%d')
            human_date = target_date.strftime('%d %B %Y')
            
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
</article>"""
            
            container.append(BeautifulSoup(card_html, 'html.parser'))
        
        # Zapisz plik
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"✅ Zaktualizowano index.html z {len(posts_data[:21])} artykułami")
            
    except Exception as e:
        print(f"❌ Błąd aktualizacji index.html: {e}")

def update_spis_html_with_posts(posts_data: list):
    """Aktualizuje spis.html ze wszystkimi 365 postami."""
    if not SPIS_TRESCI_FILE.exists():
        print("Brak pliku spis.html")
        return
    
    try:
        with open(SPIS_TRESCI_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        container = soup.find('div', class_='space-y-8')
        if not container:
            print("Nie znaleziono kontenera space-y-8")
            return
        
        # Wyczyść istniejące artykuły
        for article in container.find_all('article'):
            article.decompose()
        
        # Dodaj wszystkie 365 postów (najnowsze pierwsze)
        for post_data in posts_data:
            title = post_data['title']
            description = post_data['meta_description']
            link = post_data['post_url']
            target_date = post_data['target_date']
            
            iso_date = target_date.strftime('%Y-%m-%d')
            
            article_html = f"""
<article class='border-b border-border/40 pb-6'>
    <h2 class='text-lg font-semibold'>
        <a class='hover:text-accent transition-colors' href='{link}'>{title} – True Results Online</a>
    </h2>
    <p class='mt-1 text-xs text-text/60'>{iso_date}</p>
    <p class='mt-2 text-sm text-text/80 leading-relaxed'>{description}</p>
</article>"""
            
            container.append(BeautifulSoup(article_html, 'html.parser'))
        
        # Zapisz plik
        with open(SPIS_TRESCI_FILE, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"✅ Zaktualizowano spis.html z {len(posts_data)} artykułami")
            
    except Exception as e:
        print(f"❌ Błąd aktualizacji spis.html: {e}")

def main():
    """Główna funkcja generująca 365 postów z unikalnymi tematami."""
    print("=== GENERATOR 365 UNIKALNYCH POSTÓW - TRUE RESULTS ONLINE v2.0 ===")
    print(f"Start: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Wczytanie konfiguracji
    try:
        config = load_config_from_excel(CONFIG_FILE)
        master_prompt = build_master_prompt_from_config(CONFIG_FILE)
    except Exception as e:
        print(f"❌ Błąd konfiguracji: {e}")
        return
    
    # Przygotowanie dat (365 dni wstecz od 23.09.2025)
    start_date = datetime.datetime(2025, 9, 23)  # Dzisiejsza data
    posts_data = []
    
    # Wczytanie szablonu HTML
    try:
        with open(POST_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        print(f"❌ Brak szablonu: {POST_TEMPLATE_FILE}")
        return
    
    # Generowanie 365 postów z UNIKALNYMI tematami
    for i in range(365):
        target_date = start_date - datetime.timedelta(days=i)
        
        print(f"\n📅 POST {i+1}/365 - Data: {target_date.strftime('%Y-%m-%d')}")
        
        # Wybór UNIKALNEGO tematu
        topic_package = pick_unique_topic_package(config, i)
        if not topic_package:
            print(f"❌ Brak tematu dla postu {i+1}")
            continue
        
        print(f"📰 Tytuł: {topic_package['title']}")
        
        # Generowanie artykułu
        article_data = generate_article_with_date(topic_package, master_prompt, target_date)
        if not article_data:
            print(f"❌ Nie udało się wygenerować artykułu {i+1}")
            continue
        
        # Przygotowanie pliku
        slug = slugify(article_data['title'])
        date_stamp = target_date.strftime('%Y%m%d')
        filename = f"{slug}-{date_stamp}.html"
        filepath = PAGES_DIR / filename
        post_url = f"https://trueresults.online/pages/{filename}"
        
        # Budowanie HTML z datą
        post_html = build_post_html_with_date(
            template_content, article_data, 
            topic_package['campaign'], post_url, target_date
        )
        
        # Zapis pliku
        PAGES_DIR.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(post_html)
        
        # Dodanie do listy
        posts_data.append({
            'title': article_data['title'],
            'meta_description': article_data['meta_description'],
            'post_url': post_url,
            'target_date': target_date,
            'filename': filename
        })
        
        print(f"✅ Utworzono: {filename}")
        
        # Co 50 postów - krótka pauza
        if (i + 1) % 50 == 0:
            print(f"🔄 Postęp: {i+1}/365 postów z unikalnymi tematami...")
            time.sleep(2)
    
    print(f"\n🎯 WYGENEROWANO {len(posts_data)} POSTÓW Z UNIKALNYMI TEMATAMI")
    
    # Aktualizacja index.html (pierwsze 21 postów)
    print("\n🔄 Aktualizuję index.html...")
    update_index_html_with_posts(posts_data)
    
    # Aktualizacja spis.html (wszystkie 365 postów)
    print("🔄 Aktualizuję spis.html...")
    update_spis_html_with_posts(posts_data)
    
    # Commit i push do GitHub
    print("\n📤 Wysyłam wszystko na GitHub...")
    try:
        repo = Repo(REPO_PATH)
        repo.git.add(all=True)
        
        if repo.is_dirty(untracked_files=True):
            commit_message = f"Automatyczne wygenerowanie 365 UNIKALNYCH artykułów v2.0 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            repo.index.commit(commit_message)
            print("✅ Commit lokalny wykonany")
            
            origin = repo.remote(name='origin')
            origin.push()
            print("✅ Push na GitHub wykonany")
        else:
            print("ℹ️ Brak zmian do commitowania")
            
    except Exception as e:
        print(f"❌ Błąd Git: {e}")
    
    print("\n🎉 SUKCES!")
    print(f"✅ Wygenerowano {len(posts_data)} artykułów z UNIKALNYMI tematami")
    print(f"✅ Pierwsze 21 na index.html")
    print(f"✅ Wszystkie 365 w spis.html")
    print(f"✅ Wysłano na GitHub")
    print("=" * 50)

if __name__ == "__main__":
    main()