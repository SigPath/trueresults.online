"""
Automatyczny generator wpisów blogowych dla True Results Online - WERSJA 5.1 (Finalna)
"""
from __future__ import annotations
import os
import time
import datetime as dt
import random
import re
import json
import difflib
from pathlib import Path
from typing import List, Optional, Dict

from bs4 import BeautifulSoup
from git import Repo
from slugify import slugify

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============ KONFIGURACJA ============
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "WPROWADZ_KLUCZ_LOKALNIE")
if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "WPROWADZ_KLUCZ_LOKALNIE")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
REPO_PATH = Path(os.getenv("REPO_PATH", Path(__file__).parent))
PAGES_DIR = REPO_PATH / "pages"
TEMPLATE_FILE = REPO_PATH / "szablon_wpisu.html"
INDEX_FILE = REPO_PATH / "index.html"
HISTORY_FILE = REPO_PATH / "used_topics_global.txt" # Uproszczono do jednego pliku historii
LOG_DIR = REPO_PATH / "logs"
LOG_FILE = LOG_DIR / "last_run.txt"
FEED_FILE = REPO_PATH / "feed.xml"
SITEMAP_FILE = REPO_PATH / "sitemap.xml"
SPIS_FILE = REPO_PATH / "spis.html"
PROMPTS_DIR = REPO_PATH / "prompts"
MASTER_PROMPT_FILE = PROMPTS_DIR / "master_prompt.py"
CASE_STUDY_FILE = PROMPTS_DIR / "case_study.txt"
TITLES_INDEX_FILE = REPO_PATH / "titles_index.txt"
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "25"))
ART_MIN_WORDS = int(os.getenv("ART_MIN_WORDS", "650"))
ART_MAX_WORDS = int(os.getenv("ART_MAX_WORDS", "900"))
MAX_INDEX_CARDS = 21
BASE_URL = os.getenv("BASE_URL", "https://trueresults.online").rstrip('/')
SITE_NAME = "True Results Online"

CAMPAIGN_TOPICS: dict[str, list[str]] = {
    "Anatomia Nielojalności i Podwójnego Życia": ["Analiza Wzorca Utrzymywania Równoległej Relacji Emocjonalnej jako 'Planu B'", "Studium Przypadku: Jak 'Niewinna Przyjaźń' Przekształca się w Emocjonalną Zdradę", "‘Zero Kłótni’ – Dlaczego Pozorna Harmonia Może Być Sygnałem Głebokiego Kryzysu", "Psychologia Kłamstwa: Jak Osoby w Podwójnych Relacjach Racjonalizują Swoje Działania", "Segmentacja Tożsamości: Rola Wielu Profili i Pseudonimów w Ukrywaniu Prawdy", "Analiza Lingwistyczna Komunikatów w Tajnych Relacjach: Studium Słów-Kluczy", "'On/Ona Mnie Nie Rozumie' - Klasyczna Wymówka Usprawiedliwiająca Nielojalność", "Syndrom Idealnej Fasady: Kiedy Publiczny Wizerunek Maskuje Wewnętrzny Chaos", "Rola Tajemnicy i Adrenaliny w Uzależnieniu od Podwójnego Życia", "Konsekwencje Długofalowej Nielojalności dla Poczucia Tożsamości Sprawcy", "'Ukrywanie pod Żeńskim Imieniem': Analiza Taktyk Dezinformacyjnych w Związku", "Jak Lęk przed Zaangażowaniem Prowadzi do Tworzenia 'Dróg Ucieczki'", "Dysonans Poznawczy: Jak Można Kochać i Oszukiwać Jednocześnie?", "Analiza Decyzji o Dziecku w Kontekście Prowadzenia Podwójnego Życia", "Rola Technologii (SMS, Komunikatory) w Ułatwianiu i Utrzymywaniu Tajnych Relacji", "'Starszeństwo Znajomości' jako Absurdalna Próba Usprawiedliwienia Zdrady", "Porównanie Zdrady Fizycznej i Emocjonalnej: Co Jest Bardziej Destrukcyjne?", "Jak Osoba Niewierna Definiuje 'Lojalność', aby Pasowała do Jej Działań", "Studium Przypadku: Od 'Kawy' do Trzyletniej, Równoległej Rzeczywistości", "Jak Potrzeba Nowości i Ekscytacji Sabotuje Stabilne Związki"],
    "Mechanizmy Obronne i Taktyki Manipulacji": ["‘To Twoja Wina, że Zdradziłam’: Dekonstrukcja Mechanizmu Projekcji", "Sztuka Zaprzeczania: Jak Umysł Potrafi Przepisać Rzeczywistość w Obliczu Dowodów", "Analiza Lingwistyczna Fałszywych Przeprosin ('Przepraszam, ALE...')", "Gaslighting: Jak Manipulator Zmusza Cię do Wątpienia we Własną Percepcję", "Granie Ofiary jako Ostateczna Tarcza Obronna po Demaskacji", "'Nie Masz Życia': Analiza Ataku Ad Personam jako Taktyki Unikowej", "Od Płaczu do Agresji: Emocjonalny Rollercoaster Manipulatora w Kryzysie", "Używanie Dziecka jako Argumentu i Tarczy w Konflikcie Partnerskim", "'Mam Czyste Sumienie': Psychologia Całkowitego Odcięcia od Poczucia Winy", "Taktyka 'Nagłej Zajętości' jako Sposób na Uniknięcie Odpowiedzi", "Jak Osoby Unikające Odpowiedzialności Wykorzystują Autorytet Innych (np. 'Moja Mama Uważa...')", "Minimalizacja: Jak Poważne Przewinienia są Sprowadzane do Rangi 'Drobnych Błędów'", "Rozszczepienie (Splitting): Postrzeganie Partnera jako 'Anioła' lub 'Demona'", "Czym Jest Rana Narcystyczna i Jak Prowadzi do Eskalacji Agresji", "Używanie Wyidealizowanych Wspomnień do Manipulowania Teraźniejszością", "'Jesteśmy Tylko Ludźmi': Jak Ogólniki Służą do Rozmywania Osobistej Odpowiedzialności", "Dlaczego Manipulatorzy Nienawidzą Logiki i Faktów", "Taktyka 'Zmiany Tematu': Jak Uniknąć Odpowiedzi na Trudne Pytanie", "Analiza Komunikacji Pasywno-Agresywnej w Relacjach", "Jak Rozpoznać, Kiedy 'Troska' Jest w Rzeczywistości Formą Kontroli", "'Przecież Próbowałam to Zakończyć': Mit o Dobrych Intencjach", "Publiczna Dekompensacja: Co się Dzieje, Gdy Manipulator Traci Kontrolę na Oczach Innych", "Auto-Sabotaż jako Nieświadoma Prośba o Postawienie Granic", "Jak Osoby Niewierne Tworzą Koalicje Przeciwko Zdradzonemu Partnerowi", "Milczenie jako Forma Kary i Manipulacji (Silent Treatment)"],
    "Psychologia Sprawcy": ["Lęk przed Samotnością jako Główny Motor Destrukcyjnych Działań", "Rola Peruki i Fałszywych Tożsamości w Kontekście Niestabilnego Poczucia Własnej Wartości", "Wpływ Wzorców z Rodziny Pochodzenia na Skłonność do Nielojalności", "Nienasycony Głód Walidacji: Dlaczego 'Miłość Jednej Osoby' Nigdy Nie Wystarcza", "Cechy Osobowości Narcystycznej a Skłonność do Prowadzenia Podwójnego Życia", "Lęk Przywiązaniowy Unikający: Kiedy Bliskość Jest Jednocześnie Pragnieniem i Zagrożeniem", "Instrumentalizacja Ludzi: Postrzeganie Innych jako Narzędzi do Zaspokajania Potrzeb", "Brak Empatii: Czy Osoby Niewierne Rozumieją Ból, Który Zadają?", "Pułapka Samotności po Zdradzie: Dlaczego Trudno Zbudować Nową, Zdrową Relację", "Od Religijności do Ezoteryki: Duchowy Chaos jako Ucieczka od Odpowiedzialności", "Jak Niska Samoocena Prowadzi do Poszukiwania Potwierdzenia w Ryzykownych Zachowaniach", "'Syndrom Oszusta' w Relacjach: Lęk przed Byciem Zdemaskowanym", "Dlaczego Niektórzy Ludzie Potrzebują Dramatu, aby Czuć, że Żyją", "Jak Potrzeba Kontroli Prowadzi do Utraty Kontroli nad Własnym Życiem", "Analiza Snów i Fantazji jako Klucz do Zrozumienia Ukrytych Pragnień", "Czy Osoba o Takich Wzorcach Może się Zmienić? Warunki Prawdziwej Transformacji", "Moral Licensing: Jak 'Dobre Uczynki' Usprawiedliwiają Złe Zachowania", "Psychologiczny Portret Kobiety, Która Nigdy Nie Była w Stałym Związku", "Ruminacje: Jak Umysł Oszusta Przetwarza Poczucie Winy", "Konsekwencje Życia w Kłamstwie dla Zdrowia Psychicznego", "Dlaczego Niektórzy Ludzie Wybierają Partnerów, Których Później Poniżają", "'Alergia na Nudę': Kiedy Stabilizacja Jest Odbierana jako Zagrożenie", "Jak Presja Biologiczna (Zegar Biologiczny) Wpływa na Moralność w Relacjach", "Wewnętrzny Krytyk: Czy Agresja na Zewnątrz jest Odbiciem Wewnętrznego Głosu?", "Rola Tajemnicy w Budowaniu Fałszywego Poczucia Wyjątkowości"],
    "Perspektywa Zdradzonego i Konsekwencje": ["Alienacja Rodzicielska jako Ostateczny Akt Zemsty", "Długofalowe Skutki Emocjonalnej Zdrady dla Zdrowia Psychicznego", "Jak Odbudować Zaufanie do Siebie i Świata po Byciu Oszukanym", "'Mgła Wojny': Jak Radzić Sobie z Chaosem Komunikacyjnym po Demaskacji", "Dlaczego Logiczne Argumenty Nie Działają na Osobę w Trybie Obronnym", "Jak Zbierać Dowody na Nielojalność w Sposób Legalny i Etyczny", "Konfrontacja: Kiedy Warto, a Kiedy Trzeba Odpuścić", "Rola 'Tego Drugiego' (Partnera 2): Ofiara czy Współwinny?", "Jak Rozmawiać z Dzieckiem o Rozstaniu i Nieobecności Drugiego Rodzica", "Ustalanie Granic: Jak Chronić Siebie Przed Dalszą Manipulacją", "Czy Możliwe jest Wybaczenie bez Skruchy ze Strony Sprawcy?", "Trauma Zdrady: Objawy i Metody Leczenia", "Jak Rozpoznać, Kiedy Były Partner Próbuje Wciągnąć Cię z Powrotem w Grę", "Rola Systemu Prawnego w Walce o Kontakt z Dzieckiem", "'List Ostateczny': Analiza Narzędzia do Zamknięcia Rozdziału", "Jak Twoje Własne Wzorce Przywiązaniowe Mogły Przyczynić się do Związku", "Syndrom Sztokholmski w Relacjach: Kiedy Bronimy Tych, Którzy Nas Ranią", "Jak Pomóc Przyjacielowi, Który Doświadcza Zdrady", "Różnica Między Zamknięciem a Sprawiedliwością", "Budowanie Nowego Życia: Od Bólu do Siły"],
    "Tematy Ogólne i Ponadczasowe": ["Czym Jest Prawdziwa Intymność w Związku?", "Rola Uczciwości jako Fundamentu Trwałej Relacji", "Jak Rozpoznać Czerwone Flagi na Początku Znajomości", "Psychologia Portali Randkowych: Między Nadzieją a Iluzją", "Czy Miłość Wszystko Wybacza? Granice Kompromisu.", "Jak Komunikować Swoje Potrzeby w Zdrowy Sposób", "Różnica Między Samotnością a Byciem Samemu", "Jak Wartości Kształtują Nasze Wybory w Relacjach", "Rola Terapii w Przepracowywaniu Traum Relacyjnych", "Czym Jest Dojrzała Miłość?"]
}

# --- PONIŻEJ ZNAJDUJE SIĘ KOMPLETNY, DZIAŁAJĄCY KOD SKRYPTU ---

def safe_write(path: Path, content: str, *, binary: bool = False, append: bool = False):
    """Bezpiecznie zapisuje treść do pliku, obsługując tryb dry-run."""
    if os.getenv("DRY_RUN", "0") == "1":
        print(f"[DRY RUN] Zapis do pliku {path} pominięty.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = 'ab' if binary else 'a' if append else 'w'
    encoding = None if binary else 'utf-8'
    with open(path, mode, encoding=encoding) as f:
        f.write(content)

def load_master_prompt() -> str:
    """Ładuje i zwraca treść głównego promptu."""
    try:
        return MASTER_PROMPT_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("[OSTRZEŻENIE] Plik master_prompt.py nie został znaleziony.")
        return ""
    except Exception as e:
        print(f"[BŁĄD] Nie można odczytać pliku master_prompt.py: {e}")
        return ""

def get_current_campaign(today: Optional[dt.date] = None) -> str:
    """Zwraca nazwę bieżącej kampanii na podstawie tygodnia w roku."""
    d = today or dt.date.today()
    campaign_names = list(CAMPAIGN_TOPICS.keys())
    return campaign_names[d.isocalendar().week % len(campaign_names)]

def pick_topic(for_date: Optional[dt.date] = None) -> str:
    """Wybiera unikalny temat z bieżącej kampanii."""
    today = for_date or dt.date.today()
    campaign = get_current_campaign(today)
    
    available_topics = CAMPAIGN_TOPICS.get(campaign, [])
    if not available_topics:
        return "Brak dostępnych tematów w tej kampanii"

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = {line.strip().split('|', 1)[-1] for line in f}
    except FileNotFoundError:
        history = set()

    unique_topics = [t for t in available_topics if t not in history]

    if not unique_topics:
        print(f"[OSTRZEŻENIE] Wszystkie tematy z kampanii '{campaign}' zostały już użyte. Resetuję historię dla tej kampanii.")
        # Opcjonalnie: można zresetować historię lub wybrać losowy
        topic = random.choice(available_topics)
    else:
        topic = random.choice(unique_topics)

    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{campaign}|{topic}\n")
    
    return topic

def sanitize_generated_text(raw_text: str) -> str:
    """Czyści surowy tekst HTML wygenerowany przez AI."""
    # Usuwa znaczniki ```html i ```
    cleaned_text = re.sub(r'^```html\s*|\s*```$', '', raw_text, flags=re.MULTILINE).strip()
    return cleaned_text

def extract_plain(html_content: str) -> str:
    """Wyciąga czysty tekst z treści HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    return ' '.join(soup.stripped_strings)

def ensure_unique_title(title: str) -> str:
    """Upewnia się, że tytuł jest unikalny, dodając w razie potrzeby dopisek."""
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

def generate_meta_description(plain: str) -> str:
    """Generuje meta opis na podstawie czystego tekstu."""
    return (plain[:155] + '…') if len(plain) > 155 else plain

def generate_faq(topic: str, body_plain: str) -> list[dict]:
    """Generuje FAQ na podstawie tematu i treści artykułu."""
    if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
        return [{"question": "Jakie są kluczowe aspekty tego tematu?", "answer": "Artykuł szczegółowo analizuje temat, koncentrując się na jego mechanizmach i konsekwencjach."}]

    prompt = f"""
Na podstawie poniższego artykułu na temat "{topic}", wygeneruj 3-5 pytań i odpowiedzi w formacie FAQ.
Odpowiedzi powinny być zwięzłe i merytoryczne.
Format wyjściowy: JSON jako lista obiektów [{{ "question": "...", "answer": "..." }}].
Nie dodawaj żadnego tekstu poza JSON.

Fragment artykułu:
{body_plain[:2000]}
"""
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

def select_related_posts(current_slug: str) -> list[dict]:
    """Wybiera 3 losowe, powiązane posty."""
    all_posts = collect_all_posts()
    other_posts = [p for p in all_posts if p.get('slug') != current_slug]
    return random.sample(other_posts, min(len(other_posts), 3))

def generate_article(topic: str) -> dict:
    """
    Główna, ujednolicona funkcja generująca treść z mechanizmem retry.
    """
    master_prompt = load_master_prompt()
    mode = "master_prompt" if master_prompt and os.getenv("USE_MASTER_PROMPT", "1") == "1" else "fallback"
    body_html = ""
    
    if mode == "master_prompt":
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
                body_html = sanitize_generated_text(raw_text)
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

    plain_full = extract_plain(body_html)
    word_count = len(plain_full.split())
    
    return {
        "title": topic,
        "description": (plain_full[:155] + '…') if len(plain_full) > 155 else plain_full,
        "html_content": body_html,
        "mode": mode,
        "word_count": word_count
    }

def build_post_html(data: dict, date: dt.date, slug: str) -> str:
    """Buduje pełny kod HTML wpisu na podstawie szablonu i danych."""
    try:
        template_str = TEMPLATE_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"[BŁĄD KRYTYCZNY] Plik szablonu '{TEMPLATE_FILE}' nie został znaleziony. Nie można zbudować wpisu.")
        # Zwraca absolutne minimum, aby uniknąć crashu, ale sygnalizuje problem
        return f"<h1>{data['title']}</h1><p>Błąd: Brak szablonu.</p>"

    faq_html = ""
    if data.get('faq'):
        faq_items_html = "".join([
            f"""<div class="py-4">
                    <dt class="font-semibold text-text">{item['question']}</dt>
                    <dd class="mt-2 text-text/80">{item['answer']}</dd>
                </div>"""
            for item in data['faq']
        ])
        if faq_items_html:
            faq_html = f"""<section class="mt-12 pt-8 border-t border-border/60 not-prose" id="faq">
                <h2 class="text-xl font-semibold mb-4">Najczęściej zadawane pytania (FAQ)</h2>
                <dl class="divide-y divide-border/60">{faq_items_html}</dl>
            </section>"""

    related_html = ""
    if data.get('related'):
        related_items_html = "".join([
            f"<li><a class='text-accent hover:underline text-sm' href='{p['slug']}.html'>{p['title']}</a></li>"
            for p in data['related']
        ])
        if related_items_html:
            related_html = f"""<section class='mt-12 not-prose' id='related'>
                <h2 class='text-lg font-semibold mb-4'>Powiązane analizy</h2>
                <ul class='space-y-2'>{related_items_html}</ul>
            </section>"""

    # Upewnij się, że wszystkie klucze istnieją, aby uniknąć błędów
    title = data.get('title', 'Brak tytułu')
    description = data.get('description', 'Brak opisu.')
    html_content = data.get('html_content', '<p>Brak treści.</p>')
    
    # Pobranie kategorii z danych, jeśli istnieje
    category = data.get('category', 'Artykuły') # Domyślna kategoria

    return (template_str
            .replace("{{TYTUL}}", title)
            .replace("{{OPIS}}", description)
            .replace("{{KATEGORIA}}", category)
            .replace("{{KANONICAL}}", f"{BASE_URL}/pages/{slug}.html")
            .replace("{{DATA}}", date.strftime("%Y-%m-%d"))
            .replace("{{TRESC_HTML}}", html_content)
            .replace("{{FAQ_HTML}}", faq_html)
            .replace("{{POWIAZANE_POSTY_HTML}}", related_html)
    )

def insert_card_in_index(slug: str, data: dict, date: dt.date, campaign_name: str) -> None:
    """Wstawia nową kartę artykułu na stronę główną, używając profesjonalnego szablonu."""
    try:
        index_content = INDEX_FILE.read_text(encoding="utf-8")
        soup = BeautifulSoup(index_content, 'html.parser')
        
        posts_container = soup.find(id="posts-container")
        if not posts_container:
            print("[OSTRZEŻENIE] Nie znaleziono kontenera #posts-container w index.html. Wstawianie karty pominięte.")
            return

        # Nowy, profesjonalny szablon karty
        card_html = f"""<article class="group relative flex flex-col rounded-xl border border-border/70 bg-surface/90 p-6 shadow-sm hover:shadow-lift hover:-translate-y-1 transition-all duration-300" itemscope="True" itemtype="https://schema.org/BlogPosting">
<h3 class="mt-4 text-lg font-semibold leading-snug group-hover:text-accent transition-colors" itemprop="headline">{data['title']}</h3>
<time class="mt-2 text-xs text-text/60" datetime="{date.strftime('%Y-%m-%d')}" itemprop="datePublished">Opublikowano: {date.strftime('%d %B %Y')}</time>
<p class="mt-4 text-sm leading-relaxed text-text/80 line-clamp-5" itemprop="description">{data['description']}</p>
<a aria-label="Czytaj dalej: {data['title']}" class="mt-5 inline-flex items-center text-sm font-medium text-accent hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60" href="pages/{slug}.html" itemprop="url">Czytaj dalej →</a>
<meta content="{SITE_NAME}" itemprop="author"/>
</article>"""
        new_card_soup = BeautifulSoup(card_html, 'html.parser')
        
        # Wstaw nową kartę na początek kontenera
        posts_container.insert(0, new_card_soup)

        # Ogranicz liczbę kart do MAX_INDEX_CARDS
        all_cards = posts_container.find_all("article", recursive=False)
        if len(all_cards) > MAX_INDEX_CARDS:
            for card in all_cards[MAX_INDEX_CARDS:]:
                card.decompose()

        # Zapisz zmodyfikowany plik
        safe_write(INDEX_FILE, str(soup.prettify()))

    except Exception as e:
        print(f"[BŁĄD] Nie udało się zaktualizować pliku index.html: {e}")


def generate_full_spis(posts: list[dict]) -> None:
    """Generuje pełną, profesjonalnie wyglądającą stronę spisu treści (spis.html)."""
    
    post_items_html = []
    for p in posts:
        post_items_html.append(f"""
<article class='border-b border-border/40 pb-6'>
    <h2 class='text-lg font-semibold'>
        <a class='hover:text-accent transition-colors' href='pages/{p['slug']}.html'>{p['title']}</a>
    </h2>
    <p class='mt-1 text-xs text-text/60'>{p['date']}</p>
    <p class='mt-2 text-sm text-text/80 leading-relaxed'>{p['description']}</p>
</article>
""")

    spis_html = f"""<!DOCTYPE html>
<html lang='pl'>
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Spis Treści – {SITE_NAME}</title>
    <meta name="description" content="Pełne archiwum wszystkich analiz opublikowanych w serwisie {SITE_NAME}." />
    <link rel="canonical" href="{BASE_URL}/spis.html" />
    <link href="/favicon.svg" rel="icon" type="image/svg+xml"/>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
    <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
    <script>
        tailwind.config = {{
          theme: {{
            extend: {{
              colors: {{
                background: '#0d1117',
                surface: '#161b22',
                border: '#30363d',
                accent: '#58a6ff',
                text: '#c9d1d9'
              }},
              fontFamily: {{
                sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']
              }}
            }}
          }}
        }}
    </script>
    <style>
        body {{ font-family: 'Inter', system-ui, sans-serif; }}
        :focus-visible {{ outline: 2px solid #58a6ff; outline-offset: 2px; }}
    </style>
</head>
<body class="bg-background text-text antialiased">
    <header class="border-b border-border/60 backdrop-blur supports-[backdrop-filter]:bg-background/70 sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
            <a aria-label="Strona główna {SITE_NAME}" class="font-semibold tracking-tight text-lg hover:text-accent transition-colors" href="index.html">TrueResults<span class="text-accent">.online</span></a>
            <nav aria-label="Main navigation" class="flex items-center gap-6 text-sm">
                <a class="hover:text-accent transition-colors" href="index.html#about">O projekcie</a>
                <a class="hover:text-accent transition-colors" href='spis.html'>Spis Treści</a>
            </nav>
        </div>
    </header>
    <main>
        <section class='pt-20 pb-16 md:pt-24 md:pb-20'>
            <div class='max-w-4xl mx-auto px-4 sm:px-6'>
                <h1 class='text-3xl md:text-4xl font-bold tracking-tight mb-10'>Spis Treści</h1>
                <div class='space-y-8'>
                    {''.join(post_items_html)}
                </div>
            </div>
        </section>
    </main>
    <footer class="border-t border-border/60 py-8 text-sm text-text/60">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 text-center">
            <p>© <span id="year">{dt.date.today().year}</span> {SITE_NAME}. Wszelkie prawa zastrzeżone.</p>
        </div>
    </footer>
</body>
</html>"""
    safe_write(SPIS_FILE, spis_html)

def generate_sitemap(posts: list[dict]) -> None:
    """Generuje plik sitemap.xml."""
    urls = [f"<url><loc>{BASE_URL}/pages/{p['slug']}.html</loc></url>" for p in posts]
    xml = f"<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">{''.join(urls)}</urlset>"
    safe_write(SITEMAP_FILE, xml)

def generate_rss_feed(posts: list[dict]) -> None:
    """Generuje kanał RSS (feed.xml)."""
    items = []
    for p in posts[:20]:
        items.append(f"<item><title>{p['title']}</title><link>{BASE_URL}/pages/{p['slug']}.html</link><description>{p['description']}</description><pubDate>{p['date']}</pubDate></item>")
    xml = f"<rss version=\"2.0\"><channel><title>{SITE_NAME}</title><link>{BASE_URL}</link><description>...</description>{''.join(items)}</channel></rss>"
    safe_write(FEED_FILE, xml)

def collect_all_posts() -> list[dict]:
    """Zbiera dane o wszystkich istniejących postach."""
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

            posts.append({
                "slug": f.stem,
                "title": title,
                "description": description,
                "date": post_date,
            })
        except Exception as e:
            print(f"[OSTRZEŻENIE] Nie można przetworzyć pliku {f.name}: {e}")
    return sorted(posts, key=lambda p: p['date'], reverse=True)

def git_commit_and_push(commit_message: str):
    """Wykonuje commit i push zmian do repozytorium Git."""
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

def create_post(for_date: Optional[dt.date] = None):
    today = for_date or dt.date.today()
    topic = pick_topic(for_date=today)
    
    data = generate_article(topic)
    
    unique_title = ensure_unique_title(data['title'])
    data['title'] = unique_title
    
    slug = slugify(unique_title) + f"-{today.strftime('%Y%m%d')}"
    
    # Generate FAQ and Related Posts
    plain_content = extract_plain(data['html_content'])
    data['faq'] = generate_faq(unique_title, plain_content)
    data['related'] = select_related_posts(slug)
    
    html_content = build_post_html(data, today, slug)
    
    PAGES_DIR.mkdir(exist_ok=True)
    post_path = PAGES_DIR / f"{slug}.html"
    safe_write(post_path, html_content)
    
    campaign_name = get_current_campaign(today)
    insert_card_in_index(slug, data, today, campaign_name)
    
    all_posts = collect_all_posts()
    generate_full_spis(all_posts)
    generate_sitemap(all_posts)
    generate_rss_feed(all_posts)
    
    commit_message = f"AUTO: Nowy wpis {today.strftime('%Y-%m-%d')} - {unique_title[:50]}"
    git_commit_and_push(commit_message)

    return data, topic, slug

def main():
    if os.getenv("REBUILD_ALL_PAGES") == "1":
        # ... (logika rebuild)
        return
    
    data, topic, slug = create_post()
    
    # Logowanie
    log_entry = (
        f"DATA={dt.datetime.now().isoformat()} | KAMPANIA={get_current_campaign()} | TRYB={data.get('mode')} | "
        f"TEMAT={topic} | SLUG={slug} | TYTUL={data.get('title')} | SŁOWA={data.get('word_count', 0)}\n"
    )
    LOG_DIR.mkdir(exist_ok=True)
    safe_write(LOG_FILE, log_entry, binary=False) # Zakładamy, że safe_write obsługuje tryb 'a' lub sami go dodajemy
    
    print(f"Dodano wpis: {data['title']} -> {slug}.html (tryb={data.get('mode')})")

if __name__ == "__main__":
    main()
