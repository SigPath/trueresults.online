"""Automatyczny generator wpisów blogowych dla True Results Online.

Funkcjonalności:
1. Losowy wybór tematu z listy (bez powtórzeń w danym roku).
2. Wywołanie API Gemini (model domyślnie gemini-1.5-flash) lub fallback statyczny przy braku klucza.
3. Generowanie pliku HTML wpisu na podstawie szablonu.
4. Aktualizacja sekcji z najnowszymi wpisami w index.html (dodanie karty na górze listy).
5. (Opcjonalnie do rozbudowy) Aktualizacja struktur JSON-LD / sitemap.
6. Commit + push do repozytorium.

KROK 5 (SEO) – rozszerzenia:
• Anty-duplikaty tytułów (fuzzy similarity + mutacje suffixów).
• Ujednolicone meta description (150–160 znaków).
• FAQ sekcja (heurystyka) + miejsce na schema FAQPage.
• Powiązane wpisy (MVP losowe, docelowo semantyczne).
• Hub kampanii (kampania-<slug>.html) – topical authority.
• Aktualizacja JSON-LD (blogPost[]) na stronie głównej (ostatnie ≤50).
• Retrofit istniejących plików (SEO_RETROFIT=1). Dodaje canonical / FAQ / placeholder related.
• Plik indeksu tytułów titles_index.txt.
Struktura wymagana w repozytorium:
- index.html
- szablon_wpisu.html
- katalog pages/

Bezpieczeństwo:
- Użyj pliku .env (lokalnie) – przykład w .env.example.
- Plik .env jest ignorowany przez .gitignore i NIE może trafić do repo.
- W GitHub Actions ustaw sekret GEMINI_API_KEY w ustawieniach repozytorium.
"""
from __future__ import annotations

import os
import datetime as dt
import random
import re
import json
import difflib
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup  # type: ignore
from git import Repo  # type: ignore
from slugify import slugify  # type: ignore

# Wczytanie zmiennych z pliku .env (jeśli istnieje)
try:  # noqa: SIM105
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()  # szuka .env w bieżącym katalogu
except Exception:  # pragma: no cover - brak krytyczności, tylko informacyjnie
    # Jeśli ktoś uruchamia bez zainstalowanego python-dotenv – skrypt dalej zadziała
    pass

# ============ KONFIGURACJA ============
# Klucz API – lokalnie można ustawić przez zmienną środowiskową GEMINI_API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "WPROWADZ_KLUCZ_LOKALNIE")
# Alias: pozwól użyć GOOGLE_API_KEY jeśli ktoś ustawił tylko tę zmienną
if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
    _google_alias = os.getenv("GOOGLE_API_KEY")
    if _google_alias:
        GEMINI_API_KEY = _google_alias
# Nazwa modelu Gemini (Flash 1.5)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Ścieżka repo – przy uruchomieniu w GitHub Actions będzie to katalog roboczy.
REPO_PATH = Path(os.getenv("REPO_PATH", Path(__file__).parent))
PAGES_DIR = REPO_PATH / "pages"
TEMPLATE_FILE = REPO_PATH / "szablon_wpisu.html"
INDEX_FILE = REPO_PATH / "index.html"
HISTORY_FILE = REPO_PATH / "used_topics.txt"
GLOBAL_TOPICS_FILE = REPO_PATH / "used_topics_global.txt"  # przechowuje surowe tematy niezależnie od kampanii dla absolutnej unikalności
LOG_DIR = REPO_PATH / "logs"
LOG_FILE = LOG_DIR / "last_run.txt"
FEED_FILE = REPO_PATH / "feed.xml"
SITEMAP_FILE = REPO_PATH / "sitemap.xml"
MAX_CARDS = 21  # liczba widocznych kart na stronie głównej (wymaganie: 21 najnowszych)
BASE_URL = os.getenv("BASE_URL", "https://trueresults.online")
PAGINATION_PREFIX = "page"  # nazwa prefiksu plików paginacyjnych: page2.html, page3.html
PAGINATION_PAGE_COUNT = 0  # (DEPRECATED) stała liczba stron – 0 oznacza: użyj rzeczywistej liczby stron
SPIS_FILE = REPO_PATH / "spis.html"
PAGINATION_ENABLED = False  # Paginacja WYŁĄCZONA: index zawsze zawiera tylko MAX_CARDS najnowszych (21), reszta wyłącznie w spis.html
CAMPAIGN_HUB_ENABLED = False  # Wyłączone generowanie stron hubów kampanii (kampania-*.html)

# === KONFIG SEO (KROK 5) ===
SEO_MIN_DESC = 150
SEO_MAX_DESC = 160
ANTI_DUP_THRESHOLD = 0.82  # próg podobieństwa tytułów (SequenceMatcher + token Jaccard uśrednione)
TITLES_INDEX_FILE = REPO_PATH / "titles_index.txt"  # przechowuje unikalne (bez daty) tytuły
FAQ_COUNT = 3
RELATED_COUNT = 3
CAMPAIGN_HUB_PREFIX = "kampania-"  # nazwa pliku hubu kampanii: kampania-<slug>.html
SEO_RETROFIT_ENV = "SEO_RETROFIT"  # jeśli == "1" uruchamiamy tylko retrofit istniejących stron


# === DODATKOWA KONFIGURACJA DLA OBRAZÓW ===
# (KROK 1 – rozszerzenie) Docelowo katalog na ewentualne obrazy generowane lub pobierane.
# Aktualnie nie generujemy grafik (feature wyłączony), ale rezerwujemy stałą aby
# późniejsza integracja (np. z Google Imagen / Gemini multimodal) była minimalną zmianą.
IMAGES_DIR = REPO_PATH / "images"


# === KROK 1: Zmiana struktury danych z listy na słownik kampanii tematycznych ===
# TODO Copilot: Przekształć poniższą, dawną płaską listę TOPICS w słownik o nazwie CAMPAIGN_TOPICS.
# Kluczami słownika są nazwy kategorii (bez prefiksu "Kategoria X:"), wartościami listy tematów.
# Struktura będzie używana przez system Kampanii Tematycznych (tygodniowe rotacje kategorii).

CAMPAIGN_TOPICS: dict[str, list[str]] = {
    "Anatomia Nielojalności i Podwójnego Życia": [
        "Analiza Wzorca Utrzymywania Równoległej Relacji Emocjonalnej jako 'Planu B'",
        "Studium Przypadku: Jak 'Niewinna Przyjaźń' Przekształca się w Emocjonalną Zdradę",
        "‘Zero Kłótni’ – Dlaczego Pozorna Harmonia Może Być Sygnałem Głebokiego Kryzysu",
        "Psychologia Kłamstwa: Jak Osoby w Podwójnych Relacjach Racjonalizują Swoje Działania",
        "Segmentacja Tożsamości: Rola Wielu Profili i Pseudonimów w Ukrywaniu Prawdy",
        "Analiza Lingwistyczna Komunikatów w Tajnych Relacjach: Studium Słów-Kluczy",
        "'On/Ona Mnie Nie Rozumie' - Klasyczna Wymówka Usprawiedliwiająca Nielojalność",
        "Syndrom Idealnej Fasady: Kiedy Publiczny Wizerunek Maskuje Wewnętrzny Chaos",
        "Rola Tajemnicy i Adrenaliny w Uzależnieniu od Podwójnego Życia",
        "Konsekwencje Długofalowej Nielojalności dla Poczucia Tożsamości Sprawcy",
        "'Ukrywanie pod Żeńskim Imieniem': Analiza Taktyk Dezinformacyjnych w Związku",
        "Jak Lęk przed Zaangażowaniem Prowadzi do Tworzenia 'Dróg Ucieczki'",
        "Dysonans Poznawczy: Jak Można Kochać i Oszukiwać Jednocześnie?",
        "Analiza Decyzji o Dziecku w Kontekście Prowadzenia Podwójnego Życia",
        "Rola Technologii (SMS, Komunikatory) w Ułatwianiu i Utrzymywaniu Tajnych Relacji",
        "'Starszeństwo Znajomości' jako Absurdalna Próba Usprawiedliwienia Zdrady",
        "Porównanie Zdrady Fizycznej i Emocjonalnej: Co Jest Bardziej Destrukcyjne?",
        "Jak Osoba Niewierna Definiuje 'Lojalność', aby Pasowała do Jej Działań",
        "Studium Przypadku: Od 'Kawy' do Trzyletniej, Równoległej Rzeczywistości",
        "Jak Potrzeba Nowości i Ekscytacji Sabotuje Stabilne Związki",
    ],
    "Mechanizmy Obronne i Taktyki Manipulacji": [
        "‘To Twoja Wina, że Zdradziłam’: Dekonstrukcja Mechanizmu Projekcji",
        "Sztuka Zaprzeczania: Jak Umysł Potrafi Przepisać Rzeczywistość w Obliczu Dowodów",
        "Analiza Lingwistyczna Fałszywych Przeprosin ('Przepraszam, ALE...')",
        "Gaslighting: Jak Manipulator Zmusza Cię do Wątpienia we Własną Percepcję",
        "Granie Ofiary jako Ostateczna Tarcza Obronna po Demaskacji",
        "'Nie Masz Życia': Analiza Ataku Ad Personam jako Taktyki Unikowej",
        "Od Płaczu do Agresji: Emocjonalny Rollercoaster Manipulatora w Kryzysie",
        "Używanie Dziecka jako Argumentu i Tarczy w Konflikcie Partnerskim",
        "'Mam Czyste Sumienie': Psychologia Całkowitego Odcięcia od Poczucia Winy",
        "Taktyka 'Nagłej Zajętości' jako Sposób na Uniknięcie Odpowiedzi",
        "Jak Osoby Unikające Odpowiedzialności Wykorzystują Autorytet Innych (np. 'Moja Mama Uważa...')",
        "Minimalizacja: Jak Poważne Przewinienia są Sprowadzane do Rangi 'Drobnych Błędów'",
        "Rozszczepienie (Splitting): Postrzeganie Partnera jako 'Anioła' lub 'Demona'",
        "Czym Jest Rana Narcystyczna i Jak Prowadzi do Eskalacji Agresji",
        "Używanie Wyidealizowanych Wspomnień do Manipulowania Teraźniejszością",
        "'Jesteśmy Tylko Ludźmi': Jak Ogólniki Służą do Rozmywania Osobistej Odpowiedzialności",
        "Dlaczego Manipulatorzy Nienawidzą Logiki i Faktów",
        "Taktyka 'Zmiany Tematu': Jak Uniknąć Odpowiedzi na Trudne Pytanie",
        "Analiza Komunikacji Pasywno-Agresywnej w Relacjach",
        "Jak Rozpoznać, Kiedy 'Troska' Jest w Rzeczywistości Formą Kontroli",
        "'Przecież Próbowałam to Zakończyć': Mit o Dobrych Intencjach",
        "Publiczna Dekompensacja: Co się Dzieje, Gdy Manipulator Traci Kontrolę na Oczach Innych",
        "Auto-Sabotaż jako Nieświadoma Prośba o Postawienie Granic",
        "Jak Osoby Niewierne Tworzą Koalicje Przeciwko Zdradzonemu Partnerowi",
        "Milczenie jako Forma Kary i Manipulacji (Silent Treatment)",
    ],
    "Psychologia Sprawcy": [
        "Lęk przed Samotnością jako Główny Motor Destrukcyjnych Działań",
        "Rola Peruki i Fałszywych Tożsamości w Kontekście Niestabilnego Poczucia Własnej Wartości",
        "Wpływ Wzorców z Rodziny Pochodzenia na Skłonność do Nielojalności",
        "Nienasycony Głód Walidacji: Dlaczego 'Miłość Jednej Osoby' Nigdy Nie Wystarcza",
        "Cechy Osobowości Narcystycznej a Skłonność do Prowadzenia Podwójnego Życia",
        "Lęk Przywiązaniowy Unikający: Kiedy Bliskość Jest Jednocześnie Pragnieniem i Zagrożeniem",
        "Instrumentalizacja Ludzi: Postrzeganie Innych jako Narzędzi do Zaspokajania Potrzeb",
        "Brak Empatii: Czy Osoby Niewierne Rozumieją Ból, Który Zadają?",
        "Pułapka Samotności po Zdradzie: Dlaczego Trudno Zbudować Nową, Zdrową Relację",
        "Od Religijności do Ezoteryki: Duchowy Chaos jako Ucieczka od Odpowiedzialności",
        "Jak Niska Samoocena Prowadzi do Poszukiwania Potwierdzenia w Ryzykownych Zachowaniach",
        "'Syndrom Oszusta' w Relacjach: Lęk przed Byciem Zdemaskowanym",
        "Dlaczego Niektórzy Ludzie Potrzebują Dramatu, aby Czuć, że Żyją",
        "Jak Potrzeba Kontroli Prowadzi do Utraty Kontroli nad Własnym Życiem",
        "Analiza Snów i Fantazji jako Klucz do Zrozumienia Ukrytych Pragnień",
        "Czy Osoba o Takich Wzorcach Może się Zmienić? Warunki Prawdziwej Transformacji",
        "Moral Licensing: Jak 'Dobre Uczynki' Usprawiedliwiają Złe Zachowania",
        "Psychologiczny Portret Kobiety, Która Nigdy Nie Była w Stałym Związku",
        "Ruminacje: Jak Umysł Oszusta Przetwarza Poczucie Winy",
        "Konsekwencje Życia w Kłamstwie dla Zdrowia Psychicznego",
        "Dlaczego Niektórzy Ludzie Wybierają Partnerów, Których Później Poniżają",
        "'Alergia na Nudę': Kiedy Stabilizacja Jest Odbierana jako Zagrożenie",
        "Jak Presja Biologiczna (Zegar Biologiczny) Wpływa na Moralność w Relacjach",
        "Wewnętrzny Krytyk: Czy Agresja na Zewnątrz jest Odbiciem Wewnętrznego Głosu?",
        "Rola Tajemnicy w Budowaniu Fałszywego Poczucia Wyjątkowości",
    ],
    "Perspektywa Zdradzonego i Konsekwencje": [
        "Alienacja Rodzicielska jako Ostateczny Akt Zemsty",
        "Długofalowe Skutki Emocjonalnej Zdrady dla Zdrowia Psychicznego",
        "Jak Odbudować Zaufanie do Siebie i Świata po Byciu Oszukanym",
        "'Mgła Wojny': Jak Radzić Sobie z Chaosem Komunikacyjnym po Demaskacji",
        "Dlaczego Logiczne Argumenty Nie Działają na Osobę w Trybie Obronnym",
        "Jak Zbierać Dowody na Nielojalność w Sposób Legalny i Etyczny",
        "Konfrontacja: Kiedy Warto, a Kiedy Trzeba Odpuścić",
        "Rola 'Tego Drugiego' (Partnera 2): Ofiara czy Współwinny?",
        "Jak Rozmawiać z Dzieckiem o Rozstaniu i Nieobecności Drugiego Rodzica",
        "Ustalanie Granic: Jak Chronić Siebie Przed Dalszą Manipulacją",
        "Czy Możliwe jest Wybaczenie bez Skruchy ze Strony Sprawcy?",
        "Trauma Zdrady: Objawy i Metody Leczenia",
        "Jak Rozpoznać, Kiedy Były Partner Próbuje Wciągnąć Cię z Powrotem w Grę",
        "Rola Systemu Prawnego w Walce o Kontakt z Dzieckiem",
        "'List Ostateczny': Analiza Narzędzia do Zamknięcia Rozdziału",
        "Jak Twoje Własne Wzorce Przywiązaniowe Mogły Przyczynić się do Związku",
        "Syndrom Sztokholmski w Relacjach: Kiedy Bronimy Tych, Którzy Nas Ranią",
        "Jak Pomóc Przyjacielowi, Który Doświadcza Zdrady",
        "Różnica Między Zamknięciem a Sprawiedliwością",
        "Budowanie Nowego Życia: Od Bólu do Siły",
    ],
    "Tematy Ogólne i Ponadczasowe": [
        "Czym Jest Prawdziwa Intymność w Związku?",
        "Rola Uczciwości jako Fundamentu Trwałej Relacji",
        "Jak Rozpoznać Czerwone Flagi na Początku Znajomości",
        "Psychologia Portali Randkowych: Między Nadzieją a Iluzją",
        "Czy Miłość Wszystko Wybacza? Granice Kompromisu.",
        "Jak Komunikować Swoje Potrzeby w Zdrowy Sposób",
        "Różnica Między Samotnością a Byciem Samemu",
        "Jak Wartości Kształtują Nasze Wybory w Relacjach",
        "Rola Terapii w Przepracowywaniu Traum Relacyjnych",
        "Czym Jest Dojrzała Miłość?",
    ],
}

# ============ MASTER PROMPT (opcjonalny) ============
PROMPTS_DIR = REPO_PATH / "prompts"
MASTER_PROMPT_FILE = PROMPTS_DIR / "master_prompt.py"
CASE_STUDY_FILE = PROMPTS_DIR / "case_study.txt"


def load_master_prompt() -> Optional[str]:
    """Ładuje MASTER_PROMPT oraz studium przypadku jeśli USE_MASTER_PROMPT=1.

    Zwraca połączony tekst lub None jeśli nie używać.
    """
    use = os.getenv("USE_MASTER_PROMPT", "0") == "1"
    if not use:
        return None
    if not MASTER_PROMPT_FILE.exists():
        print("[MASTER_PROMPT] Brak pliku master_prompt.py – pomijam.")
        return None
    try:
        # Wykonujemy plik w odseparowanym namespace aby uzyskać zmienną MASTER_PROMPT
        namespace: dict = {}
        exec(MASTER_PROMPT_FILE.read_text(encoding="utf-8"), namespace)  # nosec B102
        base = namespace.get("MASTER_PROMPT")
        if not base:
            print("[MASTER_PROMPT] Nie znaleziono MASTER_PROMPT w pliku – pomijam.")
            return None
        case_text = ""
        if CASE_STUDY_FILE.exists():
            case_text = CASE_STUDY_FILE.read_text(encoding="utf-8").strip()
        combined = base.replace("(Tutaj wklej całą, szczegółową treść z poprzedniej odpowiedzi, od SEKCJI 1 do SEKCJI 4)", case_text or "[BRAK STUDIUM – UZUPEŁNIJ case_study.txt]")
        return combined
    except Exception as e:  # pragma: no cover
        print(f"[MASTER_PROMPT] Błąd ładowania: {e}")
        return None

# ============ FUNKCJE POMOCNICZE ============

def get_current_campaign(today: Optional[dt.date] = None) -> str:
    """Zwraca nazwę kampanii rotującą CODZIENNIE zamiast tygodniowo.

    Nowa strategia: każdy dzień roku (1..366) mapowany modulo na listę kategorii.
    Dzięki temu codziennie inna tematyka – brak monotonii.
    Możliwość nadpisania poprzez FORCE_CAMPAIGN (jak wcześniej).
    """
    if today is None:
        today = dt.date.today()
    force = os.getenv("FORCE_CAMPAIGN")
    if force and force in CAMPAIGN_TOPICS:
        return force
    day_of_year = int(today.strftime("%j"))  # 1..366
    categories = list(CAMPAIGN_TOPICS.keys())
    if not categories:
        raise RuntimeError("Brak kategorii w CAMPAIGN_TOPICS")
    idx = (day_of_year - 1) % len(categories)
    return categories[idx]


# === KROK 2: Stworzenie funkcji do wyboru bieżącej kampanii ===
# TODO Copilot: Napisz funkcję `get_current_campaign(campaign_data)`, która przyjmuje słownik z tematami.
# Funkcja ma determinować, która kampania jest aktywna w bieżącym tygodniu.
# Użyj numeru tygodnia w roku (od 1 do 52) do cyklicznego wyboru kampanii.
# Na przykład: tydzień 1 -> pierwsza kampania, tydzień 2 -> druga kampania, itd.
# Gdy dojdziemy do końca listy kampanii, cykl powinien zacząć się od początku.
# Funkcja powinna zwracać krotkę: (nazwa_bieżącej_kampanii, lista_tematów_dla_tej_kampanii).
# Wykorzystaj moduł datetime do pobrania numeru tygodnia.

def pick_topic(for_date: dt.date | None = None) -> str:
    """Wybiera unikalny (globalnie) temat z bieżącej kampanii.

    Zmiany względem poprzedniej wersji:
    - Wymusza całkowitą unikalność tematu w skali całego bloga (nie tylko w obrębie kampanii) – brak powtórzeń tytułu/tematu.
    - Używa pliku GLOBAL_TOPICS_FILE do śledzenia wszystkich zużytych tematów (surowy tekst).
    - Zachowuje plik HISTORY_FILE (kampania|temat) do analityki / rotacji, ale NIE resetuje już kampanii automatycznie
      chyba że wyczerpano wszystkie jej tematy i jednocześnie ustawiono ALLOW_TOPIC_REUSE=1.
    - Parametr for_date pozwala deterministycznie przypisać kampanię historyczną (np. przy masowej regeneracji wstecz).

    Strategia wyboru:
    1. Pobierz aktywną kampanię (dla for_date jeśli podano, inaczej dziś).
    2. Wczytaj zbiór *globalnie* użytych tematów.
    3. Odfiltruj z puli kampanii wszystkie już użyte globalnie.
    4. Jeśli pula jest pusta:
         a) jeśli ALLOW_TOPIC_REUSE != '1' -> błąd (świadome zatrzymanie aby nie tworzyć duplikatów),
         b) jeśli ALLOW_TOPIC_REUSE == '1' -> pozwól na ponowne użycie (fallback losowy), *ale* dopisz sufiks roku aby wymusić odróżnienie.
    5. Zapisz wybór do obu plików śledzących.
    """
    # 1. Kampania zależna od daty
    if for_date is None:
        campaign_name = get_current_campaign()
    else:
        campaign_name = get_current_campaign(for_date)
    topics_pool = CAMPAIGN_TOPICS.get(campaign_name, [])
    if not topics_pool:
        raise RuntimeError(f"Brak tematów w kampanii: {campaign_name}")

    # 2. Globalnie zużyte tematy
    global_used: set[str] = set()
    if GLOBAL_TOPICS_FILE.exists():
        for line in GLOBAL_TOPICS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                global_used.add(line)

    # 3. Filtr lokalny puli
    available = [t for t in topics_pool if t not in global_used]

    # 4. Obsługa wyczerpania
    if not available:
        if os.getenv("ALLOW_TOPIC_REUSE", "0") != "1":
            raise RuntimeError(
                "Wyczerpano unikalne tematy w kampanii i globalnie – ustaw ALLOW_TOPIC_REUSE=1 jeśli chcesz dopuścić powtórki."
            )
        # Fallback – pozwól użyć puli, ale zmodyfikuj aby zachować unikalność (dodanie sufiksu roku)
        base_choice = random.choice(topics_pool)
        year_suffix = (for_date or dt.date.today()).year
        mutated = f"{base_choice} ({year_suffix})"
        # Unikaj konfliktu jeśli również istnieje już taka forma
        attempt = 1
        final_choice = mutated
        while final_choice in global_used and attempt < 10:
            attempt += 1
            final_choice = f"{base_choice} ({year_suffix}-{attempt})"
        chosen = final_choice
    else:
        chosen = random.choice(available)

    # 5. Zapis historii
    with HISTORY_FILE.open("a", encoding="utf-8") as hf:
        hf.write(f"{campaign_name}|{chosen}\n")
    with GLOBAL_TOPICS_FILE.open("a", encoding="utf-8") as gf:
        gf.write(chosen + "\n")
    return chosen

# ===== KROK 5 SEO: Funkcje anty-duplikatów i meta =====

def _load_titles_index() -> set[str]:
    s: set[str] = set()
    if TITLES_INDEX_FILE.exists():
        for line in TITLES_INDEX_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                s.add(line)
    return s

def _save_titles_index(titles: set[str]) -> None:
    TITLES_INDEX_FILE.write_text("\n".join(sorted(titles)) + "\n", encoding="utf-8")

def _tokenize(txt: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[\wąćęłńóśźż]+", txt.lower())]

def _jaccard(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    inter = sa & sb
    union = sa | sb
    if not union:
        return 0.0
    return len(inter) / len(union)

def title_similarity(a: str, b: str) -> float:
    seq = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
    jac = _jaccard(_tokenize(a), _tokenize(b))
    return (seq + jac) / 2

def mutate_title_for_uniqueness(base: str, attempt: int) -> str:
    suffixes = [
        " – ujęcie strategiczne",
        " – perspektywa praktyczna",
        " – analiza pogłębiona",
        " – kluczowe mechanizmy",
        " – przewodnik świadomy",
    ]
    idx = attempt % len(suffixes)
    # unikaj wielokrotnego dodawania – jeśli już zawiera sufiks spróbuj inny
    if any(suf in base for suf in suffixes):
        base_core = re.sub(r" – .*", "", base)
    else:
        base_core = base
    return base_core + suffixes[idx]

def ensure_unique_title(title: str) -> str:
    titles = _load_titles_index()
    if not titles:
        titles.add(title)
        _save_titles_index(titles)
        return title
    if title not in titles:
        # sprawdź podobieństwo
        for t in titles:
            if title_similarity(title, t) >= ANTI_DUP_THRESHOLD:
                # próbuj mutować
                mutated = title
                for attempt in range(1, 8):
                    mutated = mutate_title_for_uniqueness(mutated, attempt)
                    # sprawdź kontra wszystkie
                    if all(title_similarity(mutated, existing) < ANTI_DUP_THRESHOLD for existing in titles):
                        titles.add(mutated)
                        _save_titles_index(titles)
                        return mutated
                # jeśli się nie udało – dodaj timestamp suffix
                force = title + f" ({dt.date.today().year})"
                titles.add(force)
                _save_titles_index(titles)
                return force
        # brak kolizji
        titles.add(title)
        _save_titles_index(titles)
        return title
    # tytuł dokładnie istnieje – modyfikuj
    for attempt in range(1, 8):
        mutated = mutate_title_for_uniqueness(title, attempt)
        if mutated not in titles and all(title_similarity(mutated, t) < ANTI_DUP_THRESHOLD for t in titles):
            titles.add(mutated)
            _save_titles_index(titles)
            return mutated
    fallback = title + f" ({dt.date.today().year})"
    titles.add(fallback)
    _save_titles_index(titles)
    return fallback

def generate_meta_description(plain: str, min_len: int = SEO_MIN_DESC, max_len: int = SEO_MAX_DESC) -> str:
    txt = re.sub(r"\s+", " ", plain.strip())
    if len(txt) > max_len:
        cut = txt[:max_len]
        # nie urywaj w połowie słowa
        cut = re.sub(r"\s+\S*$", "", cut)
        if len(cut) < min_len:
            cut = txt[:max_len]
        if not cut.endswith("…"):
            cut += "…"
        return cut
    # jeśli za krótkie – nie dopychamy watą, zostawiamy
    return txt

def extract_plain(html_content: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", html_content)
    return re.sub(r"\s+", " ", txt).strip()

def generate_faq(topic: str, body_plain: str, count: int = FAQ_COUNT) -> list[dict]:
    # Prosty heurystyczny generator Q/A – bez dodatkowego API call.
    base_kw = topic.split(" ")[:4]
    root = " ".join(base_kw)
    questions = [
        f"Jak zrozumieć {root.lower()} w praktyce?",
        f"Jakie są najczęstsze błędy przy ocenie {root.lower()}?",
        f"Jak wdrożyć zmianę w obszarze {root.lower()}?",
        f"Jakie sygnały ostrzegawcze warto monitorować?",
        f"Jak odróżnić trwały wzorzec od reakcji sytuacyjnej?",
    ]
    out = []
    for q in questions[:count]:
        # odpowiedź: wybierz fragment treści do ~200 znaków
        snippet = body_plain[:400]
        out.append({"question": q, "answer": snippet})
    return out

def select_related_posts(current_slug: str, campaign_name: str, limit: int = RELATED_COUNT) -> list[dict]:
    # Wybór na podstawie shared campaign: przejrzyj HISTORY_FILE i zbierz inne tematy tej kampanii
    related = []
    if not PAGES_DIR.exists():
        return related
    # Parsuj istniejące strony
    for f in sorted(PAGES_DIR.glob("*.html")):
        slug = f.name[:-5]
        if slug == current_slug:
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Wydobądź tytuł
        m = re.search(r"<h1 class=\"mb-2\">(.*?)</h1>", txt)
        title = m.group(1).strip() if m else slug
        # sprawdz campaign mention? (nie mamy zapisanej kampanii w pliku – heurystyka: tytuł lub brak)
        # Na potrzeby MVP nie filtrujemy po kampanii – losowy wybór ostatnich
        related.append({"slug": slug, "title": title})
    random.shuffle(related)
    return related[:limit]



# === KROK 4: Aktualizacja strony głównej o nazwę bieżącej kampanii ===
# Cel edukacyjny: Poniżej dodajemy funkcję, która w pliku index.html umieszcza (lub aktualizuje)
# element nagłówkowy z nazwą aktualnej kampanii tematycznej. Dzięki temu odwiedzający widzi,
# jaki blok tematyczny jest obecnie eksplorowany przez automatyczny silnik publikacji.
#
# Wymagania funkcjonalne:
# 1. Szukamy w index.html sekcji z nagłówkiem "Najnowsze Analizy" (id="latest-heading").
# 2. Pod nim (logicznie obok) chcemy mieć <h4 id="campaign-title" ...>Aktualna kampania: XYZ</h4>
# 3. Jeśli element już istnieje – tylko aktualizujemy jego treść (inner text) zachowując klasę.
# 4. Jeśli nie istnieje – wstrzykujemy go za nagłówkiem h2 (zachowując strukturę, minimalną ingerencję w HTML).
# 5. Nazwa kampanii nie powinna być HTML‑escape'owana przez BeautifulSoup (plain text wystarczy).
# 6. Funkcja ma być idempotentna: wielokrotne wywołanie dla tej samej kampanii nie duplikuje elementu.
# 7. Wywołanie funkcji kontrolujemy zmienną środowiskową SHOW_CAMPAIGN_TITLE ("1" => aktywne).
#
# Techniczne kroki implementacji:
# A. Parsujemy index.html przez BeautifulSoup.
# B. Lokalizujemy h2#latest-heading. Jeśli brak – przerywamy bez błędu.
# C. Sprawdzamy, czy istnieje już tag #campaign-title.
# D. Jeśli istnieje – aktualizujemy .string na nowy tekst.
# E. Jeśli nie – tworzymy nowy tag <h4 id="campaign-title" class="...">Aktualna kampania: ...</h4>
#    i wstawiamy go TUŻ PO h2 (insert_after).
# F. Zapisujemy plik tylko jeśli nastąpiła zmiana (dla ograniczenia diffów w repo i minimalizacji commitów).
#
# Uwaga: dobór klas Tailwind zachowujemy spójny z semantyką podtytułów (rozmiar mniejszy od h2, lekka
# semantyczna hierarchia). Używamy klas: text-sm md:text-base font-medium text-accent/80 mt-1.
#
# Zwraca True jeśli wprowadzono zmianę w pliku, False jeśli nic nie zmieniono.
def update_campaign_title_on_index(campaign_name: str) -> bool:
    if not INDEX_FILE.exists():  # brak pliku – nie przerywamy wyjątkiem
        return False
    try:
        html = INDEX_FILE.read_text(encoding="utf-8")
    except Exception:
        return False
    soup = BeautifulSoup(html, "html.parser")

    latest_h2 = soup.find("h2", {"id": "latest-heading"})
    if not latest_h2:
        return False  # brak sekcji – nic nie robimy

    existing = soup.find(id="campaign-title")
    target_text = f"Aktualna kampania: {campaign_name}"
    changed = False
    if existing:
        current_text = existing.get_text(strip=True)
        if current_text != target_text:
            existing.string = target_text
            changed = True
    else:
        # Tworzymy nowy element
        new_tag = soup.new_tag(
            "h4",
            id="campaign-title",
            **{"class": "text-sm md:text-base font-medium text-accent/80 mt-1"},
        )
        new_tag.string = target_text
        latest_h2.insert_after(new_tag)
        changed = True

    if changed:
        # Pretty-print nie jest wymagany – zachowujemy minimalną modyfikację.
        INDEX_FILE.write_text(str(soup), encoding="utf-8")
    return changed


def sanitize_generated_text(raw_text: str) -> str:
    """Usuwa code fences, nadmiarowe znaczniki ```html oraz backticki.

    Nie narusza istniejących tagów <p> jeśli są obecne.
    """
    # Usuń trójbacktickowe bloki
    raw = re.sub(r"```[a-zA-Z]*", "", raw_text)
    raw = raw.replace("```", "")
    # Usuń leading "html" które czasem zostaje po ```html
    raw = re.sub(r"^\s*html\s*", "", raw, flags=re.IGNORECASE)
    return raw.strip()


def ensure_paragraphs(text: str) -> str:
    if "<p" in text:
        return text
    parts = [p.strip() for p in text.split("\n") if p.strip()]
    # Ogranicz do 5 akapitów jak wcześniej
    parts = parts[:5]
    return "\n".join(f"<p>{p}</p>" for p in parts)


def enforce_word_limit(html_content: str, max_words: int = 300) -> str:
    """Przycina treść do maksymalnej liczby słów, zachowując strukturę <p>.

    Nie dodaje sztucznie słów jeśli jest mniej. Przycięcie następuje na końcu zdania,
    jeśli to możliwe – w prostym wariancie po osiągnięciu limitu obcina resztę.
    """
    # Proste parsowanie paragrafów
    paragraphs = re.findall(r"<p>(.*?)</p>", html_content, flags=re.DOTALL)
    out_paragraphs = []
    word_total = 0
    for para in paragraphs:
        # Usuń zagnieżdżone tagi tylko na potrzeby liczenia słów (ale zachowaj oryginalny tekst z tagami <strong>)
        plain = re.sub(r"<[^>]+>", "", para)
        words = plain.split()
        if not words:
            continue
        remaining = max_words - word_total
        if remaining <= 0:
            break
        if len(words) <= remaining:
            out_paragraphs.append(para.strip())
            word_total += len(words)
        else:
            # Przytnij
            clipped_plain_words = words[:remaining]
            clipped_plain = " ".join(clipped_plain_words)
            # Nie próbujemy odwzorowywać <strong> w przyciętym fragmencie – uproszczenie
            out_paragraphs.append(clipped_plain.strip())
            word_total += remaining
            break
    # Jeśli nic nie znaleziono (brak <p>), zwróć oryginał
    if not out_paragraphs:
        return html_content
    return "\n".join(f"<p>{p}</p>" for p in out_paragraphs)


def generate_full_article_from_master_prompt(topic: str) -> dict:
    """NOWA FUNKCJA GŁÓWNA: Generuje pełny artykuł ZAWSZE używając MASTER PROMPT jeśli dostępny.

    Zwraca dict(title, description, html_content, mode, faq) w formacie zgodnym z poprzednim fetch_ai_article.

    Zasady:
    - Jeśli master_prompt jest None lub USE_MASTER_PROMPT!=1 -> fallback do logicznie skróconego wariantu dawnego fetch_ai_article.
    - Jeśli jest master_prompt: doklej instrukcję formatu rozszerzonego (9 sekcji), długości (ART_MIN/MAX) i temat.
    - ZACHOWUJEMY unifikację: build_post_html spodziewa się dict o identycznych kluczach.
    - Minimalne ryzyko: nie usuwamy jeszcze fetch_ai_article (oznaczamy jako deprecated) do czasu pełnej migracji create_post.
    """
    description_limit = 155
    # Ładuj master prompt wewnątrz (centralizacja)
    master_prompt = load_master_prompt()
    # Konfiguracja długości
    try:
        target_min = int(os.getenv("ART_MIN_WORDS", "650"))
    except ValueError:
        target_min = 650
    try:
        target_max = int(os.getenv("ART_MAX_WORDS", "900"))
    except ValueError:
        target_max = 900
    if target_max < target_min:
        target_max = target_min + 100

    extended_structure_instr = f"""
STRUKTURA (HTML):
<h2>Wprowadzenie</h2> 1–3 akapity <p>
<h2>Definicja i Kontekst</h2>
<h2>Mechanizmy Psychologiczne</h2>
<h2>Mikrodynamika / Wzorce Zachowań</h2>
<h2>Studium Przypadku (syntetyczne)</h2>
<h2>Konsekwencje i Ryzyka</h2>
<h2>Interwencje / Strategie</h2>
<h2>Perspektywa Długoterminowa</h2>
<h2>Synteza + Pytania Refleksyjne</h2>
Każda sekcja zawiera 1–4 akapity <p>. Bez list, tabel, obrazów. Zero wstępów typu "Oto artykuł".
Docelowa długość: {target_min}–{target_max} słów (twarde maksimum {int(target_max*1.05)}). Unikaj powtórzeń tytułu i lania wody.
""".strip()

    use_master = master_prompt is not None and os.getenv("USE_MASTER_PROMPT", "0") == "1"
    mode = "master" if use_master else "fallback"
    body_html = ""
    if use_master and GEMINI_API_KEY != "WPROWADZ_KLUCZ_LOKALNIE":
        try:
            import google.generativeai as gen  # type: ignore
            gen.configure(api_key=GEMINI_API_KEY)
            model_name = os.getenv("GEMINI_MODEL_ARTICLE", "gemini-1.5-flash-latest")
            model = gen.GenerativeModel(model_name)
            print("Wysyłanie zapytania do Gemini z pełnym kontekstem...")
            prompt = (
                master_prompt
                + "\n---\nAKTUALNY TEMAT: " + topic
                + "\nInstrukcja dodatkowa: Napisz rozbudowany, głęboki artykuł analityczny w języku polskim, styl: precyzyjny, oparty na procesach psychologicznych i dynamice relacyjnej."
                + "\n" + extended_structure_instr
                + "\nZwróć WYŁĄCZNIE czysty HTML sekcji (h2 + p). Bez nagłówka tytułowego h1. Bez meta komentarzy.\n---\nGENERUJ:" 
            )
            response = model.generate_content(prompt)
            raw_text = response.text if hasattr(response, "text") else "".join(p.text for p in response.parts)  # type: ignore
            raw_text = sanitize_generated_text(raw_text)
            body_html = ensure_paragraphs(raw_text)
        except Exception as e:  # pragma: no cover
            print(f"[MASTER_GEN] Błąd generowania przez master prompt: {e}")
            use_master = False
            mode = "fallback"
    if not body_html:
        # Fallback – wykorzystujemy krótszy wariant oparty na dawnym fetch_ai_article (sekcje skrócone)
        paragraphs = [
            f"<h2>Wprowadzenie</h2><p><strong>Rdzeń zagadnienia:</strong> {topic} – syntetyczne wprowadzenie wyjaśniające dlaczego temat ma znaczenie w analizie relacyjno-psychologicznej.</p>",
            "<h2>Definicja i Kontekst</h2><p>Operacyjne zdefiniowanie zjawiska oraz wskazanie ram teoretycznych relewantnych do zagadnienia.</p>",
            "<h2>Mechanizmy Psychologiczne</h2><p>Opis wewnętrznych procesów: regulacja emocji, dysonans, obrona poznawcza – dobierz adekwatnie.</p>",
            "<h2>Mikrodynamika / Wzorce</h2><p>Obserwowalne sygnały behawioralne i komunikacyjne, które wzmacniają zjawisko.</p>",
            "<h2>Studium Przypadku</h2><p>Zsyntetyzowany modelowy scenariusz ilustrujący dynamikę – anonimizowany.</p>",
            "<h2>Konsekwencje i Ryzyka</h2><p>Skutki krótkoterminowe i długoterminowe dla jednostki oraz relacji.</p>",
            "<h2>Interwencje / Strategie</h2><p>Realistyczne kierunki pracy, autorefleksji i stabilizacji – bez banałów.</p>",
            "<h2>Perspektywa Długoterminowa</h2><p>Potencjalne trajektorie adaptacji lub eskalacji.</p>",
            "<h2>Synteza i Pytania</h2><p>Podsumowanie napięcia kluczowego + 2–3 pytania: Co weryfikuję faktami? Jakie wzorce powtarzam? Jakie sygnały ignoruję?</p>",
        ]
        body_html = "\n".join(paragraphs)

    # Meta description (pierwsze zdania)
    import re as _re
    plain = _re.sub(r"<[^>]+>", " ", body_html)
    plain = plain.replace("`", "")
    description = (plain.strip()[:description_limit]).rstrip()
    if len(plain) > description_limit:
        description += "…"
    unique_title = ensure_unique_title(topic)
    description = generate_meta_description(description)
    plain_full = extract_plain(body_html)
    faq = generate_faq(unique_title, plain_full)
    return {
        "title": unique_title,
        "description": description,
        "html_content": body_html,
        "mode": mode,
        "faq": faq,
    }


# === KROK 2: Funkcje do generowania obrazów za pomocą Google AI ===
# Uwaga: W tym etapie dodajemy funkcje pomocnicze potrzebne do przyszłej integracji z Imagen / Vertex AI.
# Obecnie ich wywołanie NIE jest zintegrowane z głównym przepływem (create_post) – to świadoma decyzja,
# aby etapowo rozwijać feature i móc łatwo wycofać zmiany bez wpływu na generację artykułów.

try:  # Import opcjonalny – jeśli brak requests, funkcje po prostu nie zadziałają.
    import requests  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    requests = None  # type: ignore


def generate_image_prompt_for_imagen(article_content: str, topic: str) -> str:
    """Generuje krótki (≤25 słów) angielski prompt wizualny dla modelu obrazowego.

    Mechanizm:
    1. Używa modelu Gemini (tekstowego) do kondensacji semantyki artykułu w opis obrazu.
    2. Styl: minimalistyczna, metaforyczna, konceptualna kompozycja; ciemna paleta + jeden akcent.
    3. Brak ludzkich twarzy, brak dosłownego streszczenia – raczej symbol.

    Zwraca: prompt (string). W przypadku błędów – fallback prosty prompt bazujący na topic.
    """
    if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
        return f"Minimalist symbolic dark composition representing: {topic}. One vivid accent color. No human faces."
    try:
        import google.generativeai as gen  # type: ignore
        gen.configure(api_key=GEMINI_API_KEY)
        model_name = os.getenv("GEMINI_MODEL_IMAGE_PROMPT", "gemini-1.5-flash-latest")
        model = gen.GenerativeModel(model_name)
        system_instruction = (
            "You are an assistant that creates concise (max 25 words) English prompts for an AI image generation system (e.g., Imagen). "
            "Focus on symbolic, conceptual, minimalist digital art; dark background + single strong accent color; no human faces; no copyrighted characters."
        )
        user_prompt = (
            f"Based on the following Polish analytical article about '{topic}', create ONE short English image generation prompt. "
            f"Avoid literal narration; use abstract symbolism. Article excerpt (HTML allowed, ignore tags):\n{article_content[:2000]}"
        )
        response = model.generate_content(system_instruction + "\n---\n" + user_prompt)
        text = response.text if hasattr(response, "text") else "".join(p.text for p in response.parts)  # type: ignore
        if not text:
            raise RuntimeError("Empty response from Gemini")
        # Post‑processing: usuń nowe linie i potencjalne cudzysłowy
        cleaned = text.strip().replace("\n", " ")
        if len(cleaned.split()) > 27:  # prosta korekta długości
            cleaned = " ".join(cleaned.split()[:27])
        return cleaned
    except Exception as e:  # pragma: no cover
        print(f"[IMAGEN_PROMPT] Fallback z powodu błędu: {e}")
        return f"Dark minimalist symbolic composition about: {topic}. Single neon accent. No faces."


def generate_and_save_image_with_imagen(image_prompt: str, slug: str) -> str | None:
    """Generuje obraz za pomocą Imagen (Vertex AI) i zapisuje go do pliku.

    Realistyczny szkic integracji – wymaga skonfigurowanego Google Cloud:
    - Zmienna środowiskowa GOOGLE_APPLICATION_CREDENTIALS lub ADC (gcloud auth application-default login)
    - Zainstalowany pakiet google-cloud-aiplatform
    - Poprawne ID projektu i endpoint modelu
    """
    try:
        from google.cloud import aiplatform  # type: ignore
        from google.cloud.aiplatform.gapic.v1 import PredictionServiceClient  # type: ignore
        from google.protobuf import struct_pb2  # type: ignore
    except ImportError:
        print("Błąd: Aby generować obrazy, zainstaluj 'google-cloud-aiplatform'. (pomijam)")
        return None

    IMAGES_DIR.mkdir(exist_ok=True)

    project_id = os.getenv("VERTEX_PROJECT_ID", "TWOJ_PROJECT_ID_W_GOOGLE_CLOUD")
    location = os.getenv("VERTEX_LOCATION", "us-central1")
    endpoint_id = os.getenv("VERTEX_IMAGEN_ENDPOINT", "imagegeneration@006")

    try:
        aiplatform.init(project=project_id, location=location)
        client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        client = PredictionServiceClient(client_options=client_options)

        instance = struct_pb2.Struct()
        instance.fields["prompt"].string_value = image_prompt

        parameters = struct_pb2.Struct()
        parameters.fields["sampleCount"].number_value = 1

        endpoint = client.endpoint_path(project=project_id, location=location, endpoint=endpoint_id)
        response = client.predict(endpoint=endpoint, instances=[instance], parameters=parameters)

        # Odbierz dane obrazu – w przykładowej odpowiedzi klucz może się różnić, zależnie od wersji API.
        try:
            image_bytes = response.predictions[0]["bytesBase64Decoded"]  # type: ignore[index]
        except Exception:
            print("[IMAGEN] Nie znaleziono klucza 'bytesBase64Decoded' w odpowiedzi – struktura mogła się zmienić.")
            return None

        image_filename = f"{slug}.png"
        image_path = IMAGES_DIR / image_filename
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        print(f"Obraz zapisany: {image_path}")
        return image_filename
    except Exception as e:  # pragma: no cover
        print(f"[IMAGEN] Błąd generowania obrazu: {e}")
        return None


def fetch_ai_article(topic: str) -> dict:
    """[DEPRECATED] Stara funkcja generowania artykułu – pozostawiona tymczasowo dla kompatybilności.

    UWAGA: Docelowo zostanie usunięta po pełnej migracji do generate_full_article_from_master_prompt.
    Wywołania nowych wpisów powinny korzystać z generate_full_article_from_master_prompt().

    Generuje treść artykułu (rozszerzona wersja) poprzez API Gemini lub fallback.

    Nowości (wersja rozszerzona):
    - Konfigurowalna docelowa długość (ART_MIN_WORDS / ART_MAX_WORDS – domyślnie 650–900 słów)
    - Struktura wielosekcyjna z wyraźnymi nagłówkami śródtytułów (h2) + akapity <p>
    - Sekcje: Wprowadzenie, Definicja/Kontekst, Mechanizmy, Mikrodynamika / Wzorce, Studium Przypadku (syntetyczne), Konsekwencje / Ryzyka, Interwencje / Strategie, Perspektywa Długoterminowa, Synteza + Pytania Refleksyjne.
    - Każda sekcja generowana jako czysty HTML (bez list ul/ol – unikamy zbyt dużej wariancji, można dodać później)
    - Fallback nadal daje krótszą wersję (aby nie wstrzymywać procesu bez API) – ale lekko wydłużoną (8 akapitów).

    Zwraca: dict(title, description, html_content, mode, faq?)
    """
    description_limit = 155
    # Konfiguracja długości przez zmienne środowiskowe
    try:
        target_min = int(os.getenv("ART_MIN_WORDS", "650"))
    except ValueError:
        target_min = 650
    try:
        target_max = int(os.getenv("ART_MAX_WORDS", "900"))
    except ValueError:
        target_max = 900
    if target_max < target_min:
        target_max = target_min + 100

    # Główny prompt – staramy się wymusić długość i strukturę
    base_prompt = f"""
Napisz analityczny, głęboki artykuł po polsku na temat: "{topic}".
WYMAGANIA:
- Długość docelowa: {target_min}–{target_max} słów (nie mniej niż {int(target_min*0.9)} i nie więcej niż {int(target_max*1.05)}).
- Styl: precyzyjny, oparty na psychologii / analizie systemowej, unikaj lania wody i ogólników.
- NIE twórz treści porad prawnych ani medycznych – zachowaj charakter edukacyjno-analityczny.
- Unikaj sztucznego powtarzania tytułu i clickbaitowych sformułowań.
STRUKTURA (każdy nagłówek jako <h2>, treść sekcji w akapitach <p>):
1. Wprowadzenie – problem i dlaczego jest istotny.
2. Definicja i Kontekst – osadzenie pojęć, ramy psychologiczne.
3. Mechanizmy Psychologiczne – kluczowe procesy, wewnętrzne dynamiki.
4. Mikrodynamika / Wzorce Zachowań – obserwowalne sygnały, mikrointerakcje.
5. Studium Przypadku (syntetyczne) – krótka, modelowa ilustracja mechanizmu (anonimowa, neutralna).
6. Konsekwencje i Ryzyka – skutki dla jednostki i relacji.
7. Interwencje / Strategie – realistyczne kierunki pracy / autorefleksji (bez tanich porad typu "po prostu bądź szczery").
8. Perspektywa Długoterminowa – trajektorie rozwoju / regresu.
9. Synteza + 2–3 pytania refleksyjne – bez powtarzania całych zdań z wcześniejszych sekcji.
FORMAT:
- Zwróć wyłącznie czyste HTML: sekwencja <h2> + 1..4 akapitów <p> pod każdym nagłówkiem.
- Nie używaj list, tabel ani obrazków.
- Bez wstępu typu "Oto artykuł" – od razu treść.
""".strip()

    mode = "gemini"
    try:
        if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
            raise RuntimeError("Brak prawidłowego klucza – fallback.")
        import google.generativeai as gen  # type: ignore
        gen.configure(api_key=GEMINI_API_KEY)
        model = gen.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(base_prompt)
        raw_text = response.text if hasattr(response, 'text') else "".join(p.text for p in response.parts)  # type: ignore
        raw_text = sanitize_generated_text(raw_text)
        # Upewnij się, że mamy <p> – jeśli model zwrócił plaintext z nagłówkami
        body_html = ensure_paragraphs(raw_text)
    except Exception:
        # Fallback – dłuższa wersja niż poprzednio, ale nadal deterministyczna
        mode = "fallback"
        paragraphs = [
            f"<h2>Wprowadzenie</h2><p><strong>Rdzeń zagadnienia:</strong> {topic} – syntetyczne wprowadzenie wyjaśniające dlaczego temat ma znaczenie w analizie relacyjno-psychologicznej.</p>",
            "<h2>Definicja i Kontekst</h2><p>Operacyjne zdefiniowanie zjawiska oraz wskazanie ram teoretycznych (psychologia poznawcza, systemowa, teorii przywiązania – zależnie od relewancji).</p>",
            "<h2>Mechanizmy Psychologiczne</h2><p>Opis wewnętrznych sprzężeń: regulacja emocji, dysonans poznawczy, racjonalizacja, projekcja, segmentacja tożsamości – przykłady mechanizmów zależnych od tematu.</p>",
            "<h2>Mikrodynamika / Wzorce</h2><p>Konkrety: powtarzalne frazy, zmiany rytmu odpowiedzi, eskalacja/wycofanie, taktyczne użycie ciszy, przerzucanie ciężaru dowodu.</p>",
            "<h2>Studium Przypadku</h2><p>Zsyntetyzowany modelowy scenariusz ilustrujący dynamikę – pozbawiony danych osobowych, służący wyłącznie ilustracji funkcji mechanizmu.</p>",
            "<h2>Konsekwencje i Ryzyka</h2><p>Skutki krótkoterminowe (dezorientacja, fragmentacja narracji) oraz długoterminowe (erozja zaufania, przebudowa modelu relacyjnego, osłabienie wglądu).</p>",
            "<h2>Interwencje / Strategie</h2><p>Priorytety: rekonstrukcja faktów, identyfikacja wzorców, wzmacnianie granic, higiena informacyjna, praca nad tolerancją dysonansu.</p>",
            "<h2>Perspektywa Długoterminowa</h2><p>Potencjalne trajektorie: adaptacyjne integrowanie doświadczenia vs. utrwalanie defensywnych narracji i dalsza dysocjacja odpowiedzialności.</p>",
            "<h2>Synteza i Pytania</h2><p>Podsumowanie kluczowego wektora napięcia + pytania: Co faktycznie wiem a co zakładam? Jakie sygnały ignorowałem? Które interpretacje opierają się na danych, a które na potrzebie domknięcia?</p>",
        ]
        body_html = "\n".join(paragraphs)

    # Meta description – pierwsze zdania z treści (strip tagów)
    import re as _re
    plain = _re.sub(r"<[^>]+>", " ", body_html)
    plain = plain.replace("`", "")
    description = (plain.strip()[:description_limit]).rstrip()
    if len(plain) > description_limit:
        description += "…"

    unique_title = ensure_unique_title(topic)
    description = generate_meta_description(description)
    plain_full = extract_plain(body_html)
    faq = generate_faq(unique_title, plain_full)
    return {
        "title": unique_title,
        "description": description,
        "html_content": body_html,
        "mode": mode,
        "faq": faq,
    }


def build_post_html(data: dict, date: dt.date, slug: str) -> str:
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    human_date = date.strftime("%Y-%m-%d")
    # Dodaj meta kategorii (kampanii) – uzyskaj nazwę bieżącej kampanii
    try:
        category_name = get_current_campaign(date)
    except Exception:
        category_name = "Analiza"
    # Stały obraz og:image – szablon ma wpisane /og-image.png; nie modyfikujemy dynamicznie.
    replacements = {
        "{{TYTUL}}": data["title"],
        "{{OPIS}}": data["description"],
        "{{DATA}}": human_date,
        "{{DATA_LUDZKA}}": human_date,
        "{{TRESC_HTML}}": data["html_content"],
        "{{KANONICAL}}": f"https://trueresults.online/pages/{slug}.html",
    }
    for k, v in replacements.items():
        template = template.replace(k, v)
    # Wstrzyknij <meta name="article:category" ...> jeśli brak
    if 'name="article:category"' not in template:
        template = template.replace('</head>', f'    <meta name="article:category" content="{category_name}"/>\n</head>')
    # Dodaj articleSection do JSON-LD jeśli brak
    try:
        m_ld = re.search(r'<script id="structured-data"[^>]*>([\s\S]*?)</script>', template)
        if m_ld:
            jd = json.loads(m_ld.group(1))
            if isinstance(jd, dict) and 'articleSection' not in jd:
                jd['articleSection'] = category_name
                new_ld = json.dumps(jd, ensure_ascii=False, indent=2)
                template = template.replace(m_ld.group(1), new_ld)
    except Exception:
        pass
    # Dodanie FAQ (jeśli obecne) i powiązanych wpisów placeholder – wstrzyknięcie przed </article>
    faq_list = data.get("faq") or []
    if faq_list:
        faq_html_parts = ["<section class='mt-10 not-prose' id='faq'><h2 class='text-lg font-semibold mb-4'>FAQ</h2><dl class='space-y-4'>"]
        for item in faq_list:
            q = item['question']
            a = item['answer']
            faq_html_parts.append(f"<div class='border border-border/40 rounded-lg p-4 bg-surface/60'><dt class='font-medium'>{q}</dt><dd class='mt-2 text-sm text-text/80 leading-relaxed'>{a}</dd></div>")
        faq_html_parts.append("</dl></section>")
        faq_block = "\n".join(faq_html_parts)
        template = template.replace("{{TRESC_HTML}}", "{{TRESC_HTML}}" + faq_block)
    # Related posts – dynamicznie dołożone w retrofit / create_post po wygenerowaniu (placeholder)
    template = template.replace("</article>", "<div id='related-placeholder'></div></article>")
    return template

# Retrofit: dodaj meta kategorii do istniejących artykułów jeśli brak
def retrofit_article_categories() -> None:
    if not PAGES_DIR.exists():
        return
    for f in PAGES_DIR.glob('*.html'):
        try:
            txt = f.read_text(encoding='utf-8')
        except Exception:
            continue
        if 'name="article:category"' in txt:
            continue
        # Odtwórz datę z nazwy pliku
        m = re.search(r'-(\d{8})\.html$', f.name)
        if m:
            try:
                d = dt.datetime.strptime(m.group(1), '%Y%m%d').date()
            except Exception:
                d = dt.date.today()
        else:
            d = dt.date.today()
        try:
            cat = get_current_campaign(d)
        except Exception:
            cat = 'Analiza'
        new_txt = re.sub(r'</head>', f'    <meta name="article:category" content="{cat}"/>\n</head>', txt, count=1, flags=re.IGNORECASE)
        # Jeśli JSON-LD istnieje i nie ma articleSection – wstrzyknij
        try:
            m_ld = re.search(r'<script id="structured-data"[^>]*>([\s\S]*?)</script>', new_txt)
            if m_ld:
                jd = json.loads(m_ld.group(1))
                changed = False
                if isinstance(jd, dict) and 'articleSection' not in jd:
                    jd['articleSection'] = cat
                    changed = True
                if changed:
                    new_txt = new_txt.replace(m_ld.group(1), json.dumps(jd, ensure_ascii=False, indent=2))
        except Exception:
            pass
        try:
            f.write_text(new_txt, encoding='utf-8')
        except Exception:
            pass

# ============ GENEROWANIE OBRAZÓW (umieszczone przed użyciem) ============


def insert_card_in_index(slug: str, data: dict, date: dt.date, campaign_name: str | None = None) -> None:
    html = INDEX_FILE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find(id="posts-container")
    if not container:
        raise RuntimeError("Nie znaleziono #posts-container w index.html")

    # (Opcjonalnie) wstaw baner kampanii na górze sekcji – tylko raz
    if os.getenv("SHOW_CAMPAIGN_BANNER", "0") == "1":
        campaign_name = get_current_campaign(date)
        if not soup.find(id="current-campaign-banner"):
            banner = soup.new_tag("div")
            banner["id"] = "current-campaign-banner"
            banner["class"] = [
                "col-span-full","mb-6","rounded-xl","border","border-accent/40","bg-accent/10","p-5","backdrop-blur",
                "shadow-sm","transition","animate-fade-in"
            ]
            h_banner = soup.new_tag("h2")
            h_banner["class"] = ["text-sm","font-semibold","tracking-wide","text-accent","uppercase","mb-1"]
            h_banner.string = "Aktualna Kampania"  # label
            p_banner = soup.new_tag("p")
            p_banner["class"] = ["text-sm","text-text/80","leading-relaxed"]
            p_banner.string = f"W tym tygodniu analizujemy: {campaign_name}"  # content
            banner.append(h_banner)
            banner.append(p_banner)
            # Wstaw banner na początek kontenera
            container.insert(0, banner)

    # Utwórz nowy element (karta)
    article = soup.new_tag("article")
    article["class"] = [
        "group","relative","flex","flex-col","rounded-xl","border","border-border/70","bg-surface/90","p-6","shadow-sm","hover:shadow-lift","hover:-translate-y-1","transition-all","duration-300"
    ]
    article["itemscope"] = True
    article["itemtype"] = "https://schema.org/BlogPosting"

    category_span = soup.new_tag("div")
    category_span["class"] = ["flex","items-center","gap-2","text-[11px]","font-medium","tracking-wide","uppercase","text-accent/90"]
    inner_span = soup.new_tag("span")  # etykieta kategorii / kampanii
    inner_span["itemprop"] = "articleSection"
    if campaign_name is None:
        # Jeśli nie przekazano kampanii (legacy wywołanie) – ustal na podstawie bieżącej daty.
        try:
            campaign_name = get_current_campaign(date)
        except Exception:
            campaign_name = "Analiza"
    inner_span.string = campaign_name
    category_span.append(inner_span)

    # Obraz miniatury (jeśli istnieje) – umieszczamy nad tytułem
    thumb_wrapper = None
    if data.get("image_filename"):
        thumb_wrapper = soup.new_tag("div")
        thumb_wrapper["class"] = ["mb-4","overflow-hidden","rounded-lg","border","border-border/50","aspect-[16/9]","bg-background/40"]
        img_tag = soup.new_tag("img")
        img_tag["src"] = f"images/{data['image_filename']}"
        img_tag["alt"] = f"Ilustracja: {data['title']}"
        img_tag["class"] = ["w-full","h-full","object-cover","transition-transform","duration-500","group-hover:scale-[1.03]"]
        img_tag["loading"] = "lazy"
        thumb_wrapper.append(img_tag)

    h3 = soup.new_tag("h3")
    h3["class"] = ["mt-4","text-lg","font-semibold","leading-snug","group-hover:text-accent","transition-colors"]
    h3["itemprop"] = "headline"
    h3.string = data["title"]

    time_tag = soup.new_tag("time")
    time_tag["class"] = ["mt-2","text-xs","text-text/60"]
    time_tag["datetime"] = date.strftime("%Y-%m-%d")
    time_tag["itemprop"] = "datePublished"
    time_tag.string = f"Opublikowano: {date.strftime('%Y-%m-%d')}"

    p = soup.new_tag("p")
    p["class"] = ["mt-4","text-sm","leading-relaxed","text-text/80","line-clamp-5"]
    p["itemprop"] = "description"
    p.string = data["description"]

    a = soup.new_tag("a")
    # Używamy ścieżki względnej (bez wiodącego '/') aby linki działały także przy lokalnym otwieraniu pliku (file://) lub hostowaniu w podkatalogu.
    a["href"] = f"pages/{slug}.html"
    a["class"] = ["mt-5","inline-flex","items-center","text-sm","font-medium","text-accent","hover:underline","focus:outline-none","focus-visible:ring-2","focus-visible:ring-accent/60"]
    a["itemprop"] = "url"
    a["aria-label"] = f"Czytaj dalej: {data['title']}"
    a.string = "Czytaj dalej →"

    meta_author = soup.new_tag("meta")
    meta_author["itemprop"] = "author"
    meta_author["content"] = "True Results Online"

    # Wstaw na początek po komentarzu markera
    marker = None
    for c in container.children:
        if isinstance(c, type(soup.new_string(""))) and "AUTO-BLOG" in str(c):
            marker = c
            break
    if marker:
        marker.insert_after(article)
    else:
        container.insert(0, article)

    # Dodaj dzieci do artykułu
    if thumb_wrapper:
        article.append(thumb_wrapper)
    article.append(category_span)
    article.append(h3)
    article.append(time_tag)
    article.append(p)
    article.append(a)
    article.append(meta_author)

    # Retrofit: normalizujemy istniejące linki (usuwamy wiodący '/') jeśli występuje
    for link in container.find_all("a", href=True):
        if link["href"].startswith("/pages/"):
            link["href"] = link["href"].lstrip("/")

    # Cleanup: usuń luźne tekstowe węzły / meta / a, które nie są opakowane w <article>
    from bs4 import NavigableString, Tag  # type: ignore
    stray = []
    for child in list(container.children):
        if isinstance(child, NavigableString):
            if not str(child).strip():
                continue
            # jeśli to komentarz marker – zachowaj
            if "AUTO-BLOG" in str(child):
                continue
            stray.append(child)
        elif isinstance(child, Tag) and child.name not in {"article"}:
            # Nie usuwamy komentarzy (komentarze nie są Tag)
            stray.append(child)
    for s in stray:
        try:
            s.extract()
        except Exception:
            pass

    # Zawsze przytnij do MAX_CARDS (21 najnowszych) – reszta dostępna tylko w spis.html
    if MAX_CARDS:
        cards = container.find_all("article", recursive=False)
        if len(cards) > MAX_CARDS:
            for extra in cards[MAX_CARDS:]:
                extra.decompose()

    INDEX_FILE.write_text(str(soup), encoding="utf-8")


def rebuild_index_from_pages(limit: Optional[int] = None) -> None:
    """Odbudowuje listę kart w index.html bazując na plikach w pages/.

    Sortuje według daty w nazwie (YYYYMMDD na końcu slug-a) malejąco.
    Tworzy nowe <article> tak jak insert_card_in_index (bez statycznej karty demo).
    """
    if not INDEX_FILE.exists():
        raise RuntimeError("Brak index.html – nie mogę odbudować.")
    if not PAGES_DIR.exists():
        return
    html = INDEX_FILE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find(id="posts-container")
    if not container:
        raise RuntimeError("Nie znaleziono #posts-container w index.html")
    # Usuń wszystkie istniejące artykuły (zostaw komentarz markera jeśli jest)
    for art in container.find_all("article", recursive=False):
        art.decompose()
    # Zbierz wpisy z pełną logiką (łącznie z kategorią) – reuse collect_all_posts()
    entries = collect_all_posts()  # zawiera: slug,title,description,date,category
    # Wymaganie: index.html ma pokazywać TYLKO 21 najnowszych wpisów.
    # Ignorujemy parametr limit dla zachowania spójności – zawsze bierzemy MAX_CARDS.
    full_entries = entries[:]  # do generowania pełnego spisu
    entries = entries[:MAX_CARDS]

    for e in entries:
        article = soup.new_tag("article")
        article["class"] = [
            "group","relative","flex","flex-col","rounded-xl","border","border-border/70","bg-surface/90","p-6","shadow-sm","hover:shadow-lift","hover:-translate-y-1","transition-all","duration-300"
        ]
        article["itemscope"] = True
        article["itemtype"] = "https://schema.org/BlogPosting"
        cat_div = soup.new_tag("div")
        cat_div["class"] = ["flex","items-center","gap-2","text-[11px]","font-medium","tracking-wide","uppercase","text-accent/90"]
        span = soup.new_tag("span")
        span["itemprop"] = "articleSection"
        # Kategoria jeśli dostępna – w przeciwnym razie fallback
        span.string = e.get("category") if e.get("category") else "Analiza Relacyjna"
        cat_div.append(span)
        h3 = soup.new_tag("h3")
        h3["class"] = ["mt-4","text-lg","font-semibold","leading-snug","group-hover:text-accent","transition-colors"]
        h3["itemprop"] = "headline"
        h3.string = e["title"]
        time_tag = soup.new_tag("time")
        time_tag["class"] = ["mt-2","text-xs","text-text/60"]
        time_tag["datetime"] = e["date"].strftime("%Y-%m-%d")
        time_tag["itemprop"] = "datePublished"
        time_tag.string = f"Opublikowano: {e['date'].strftime('%Y-%m-%d')}"
        p = soup.new_tag("p")
        p["class"] = ["mt-4","text-sm","leading-relaxed","text-text/80","line-clamp-5"]
        p["itemprop"] = "description"
        p.string = e["description"]
        a = soup.new_tag("a")
        a["href"] = f"pages/{e['slug']}.html"
        a["class"] = ["mt-5","inline-flex","items-center","text-sm","font-medium","text-accent","hover:underline","focus:outline-none","focus-visible:ring-2","focus-visible:ring-accent/60"]
        a["itemprop"] = "url"
        a["aria-label"] = f"Czytaj dalej: {e['title']}"
        a.string = "Czytaj dalej →"
        meta_author = soup.new_tag("meta")
        meta_author["itemprop"] = "author"
        meta_author["content"] = "True Results Online"
        article.extend([cat_div,h3,time_tag,p,a,meta_author])
        # wstaw po markerze jeśli jest
        marker = None
        for c in container.children:
            if isinstance(c, type(soup.new_string(""))) and "AUTO-BLOG" in str(c):
                marker = c
                break
        if marker:
            marker.insert_after(article)
        else:
            container.append(article)
    INDEX_FILE.write_text(str(soup), encoding="utf-8")
    # Pełny spis generujemy z pełnej listy (full_entries), aby zawierał wszystkie wpisy.
    try:
        generate_full_spis(full_entries)
    except Exception as e:  # pragma: no cover
        print(f"[SPIS] Błąd generowania spisu: {e}")

def collect_all_posts() -> list[dict]:
    """Zwraca listę wszystkich wpisów (parsując pliki HTML)."""
    posts = []
    for f in PAGES_DIR.glob("*.html"):
        name = f.name[:-5]
        m = re.search(r"-(\d{8})$", name)
        if m:
            try:
                date_obj = dt.datetime.strptime(m.group(1), "%Y%m%d").date()
            except ValueError:
                date_obj = dt.date.today()
        else:
            date_obj = dt.date.today()
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        mt = re.search(r"<h1 class=\"mb-2\">(.*?)</h1>", txt)
        title = mt.group(1).strip() if mt else name
        md = re.search(r'<meta name="description" content="(.*?)"', txt)
        desc = md.group(1).strip() if md else "Bez opisu."
        # Wykryj kategorię: meta article:category -> JSON-LD articleSection -> fallback kampania z daty
        category = None
        mc = re.search(r'<meta name="article:category" content="(.*?)"', txt)
        if mc:
            category = mc.group(1).strip()
        else:
            try:
                ld_match = re.search(r'<script id="structured-data"[^>]*>([\s\S]*?)</script>', txt)
                if ld_match:
                    data_ld = json.loads(ld_match.group(1))
                    if isinstance(data_ld, dict):
                        category = data_ld.get("articleSection")
            except Exception:
                pass
        if not category:
            try:
                category = get_current_campaign(date_obj)
            except Exception:
                category = "Analiza"
        posts.append({
            "slug": name,
            "title": title,
            "description": desc,
            "date": date_obj,
            "category": category,
        })
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts

def build_card_html(soup: BeautifulSoup, post: dict) -> 'BeautifulSoup':  # type: ignore
    article = soup.new_tag("article")
    article["class"] = [
        "group","relative","flex","flex-col","rounded-xl","border","border-border/70","bg-surface/90","p-6","shadow-sm","hover:shadow-lift","hover:-translate-y-1","transition-all","duration-300"
    ]
    article["itemscope"] = True
    article["itemtype"] = "https://schema.org/BlogPosting"
    cat_div = soup.new_tag("div")
    cat_div["class"] = ["flex","items-center","gap-2","text-[11px]","font-medium","tracking-wide","uppercase","text-accent/90"]
    span = soup.new_tag("span")
    span["itemprop"] = "articleSection"
    span.string = post.get("category", "Analiza Relacyjna")
    cat_div.append(span)
    h3 = soup.new_tag("h3")
    h3["class"] = ["mt-4","text-lg","font-semibold","leading-snug","group-hover:text-accent","transition-colors"]
    h3["itemprop"] = "headline"
    h3.string = post["title"]
    time_tag = soup.new_tag("time")
    time_tag["class"] = ["mt-2","text-xs","text-text/60"]
    time_tag["datetime"] = post["date"].strftime("%Y-%m-%d")
    time_tag["itemprop"] = "datePublished"
    time_tag.string = f"Opublikowano: {post['date'].strftime('%Y-%m-%d')}"
    p = soup.new_tag("p")
    p["class"] = ["mt-4","text-sm","leading-relaxed","text-text/80","line-clamp-5"]
    p["itemprop"] = "description"
    p.string = post["description"]
    a = soup.new_tag("a")
    a["href"] = f"pages/{post['slug']}.html"
    a["class"] = ["mt-5","inline-flex","items-center","text-sm","font-medium","text-accent","hover:underline","focus:outline-none","focus-visible:ring-2","focus-visible:ring-accent/60"]
    a["itemprop"] = "url"
    a["aria-label"] = f"Czytaj dalej: {post['title']}"
    a.string = "Czytaj dalej →"
    meta_author = soup.new_tag("meta")
    meta_author["itemprop"] = "author"
    meta_author["content"] = "True Results Online"
    article.extend([cat_div,h3,time_tag,p,a,meta_author])
    return article

def build_pagination_nav(soup: BeautifulSoup, current: int, total: int) -> 'BeautifulSoup':  # type: ignore
    """Buduje element nawigacji paginacyjnej.

    Zmiana (paginacja 2024-09):
    - Rezygnujemy z wymuszonej stałej liczby stron (PAGINATION_PAGE_COUNT).
    - Wyświetlamy tylko rzeczywistą liczbę stron (total).
    - Jeśli total == 1 – zwracamy pusty kontener (bez nawigacji).
    """
    if total <= 1:
        return soup.new_tag("nav")  # brak realnej paginacji – pusty element (opcjonalnie można zwrócić fragment)
    visible_total = total
    nav = soup.new_tag("nav")
    nav["class"] = ["mt-12","flex","items-center","justify-center","gap-2","flex-wrap","text-sm","pagination-nav"]
    # Wstecz
    if current > 1:
        prev_link = soup.new_tag("a", href="index.html" if current-1 == 1 else f"{PAGINATION_PREFIX}{current-1}.html")
        prev_link["class"] = ["px-3","py-1.5","rounded","border","border-border/60","hover:bg-surface/60","transition"]
        prev_link.string = "Wstecz"
        nav.append(prev_link)
    else:
        span_prev = soup.new_tag("span")
        span_prev["class"] = ["px-3","py-1.5","rounded","border","border-border/40","opacity-40","cursor-not-allowed"]
        span_prev.string = "Wstecz"
        nav.append(span_prev)
    # Numery stron (1..visible_total)
    for i in range(1, visible_total+1):
        if i == current:
            s = soup.new_tag("span")
            s["class"] = ["px-3","py-1.5","rounded","bg-accent","text-background","font-medium","shadow"]
            s.string = str(i)
            nav.append(s)
        else:
            a = soup.new_tag("a")
            a["href"] = "index.html" if i == 1 else f"{PAGINATION_PREFIX}{i}.html"
            a["class"] = ["px-3","py-1.5","rounded","border","border-border/60","hover:bg-surface/60","transition"]
            a.string = str(i)
            nav.append(a)
    # Dalej (aktywny tylko jeśli istnieje kolejna strona z treścią lub jeśli current < visible_total)
    if current < visible_total:
        next_link = soup.new_tag("a", href=f"{PAGINATION_PREFIX}{current+1}.html")
        next_link["class"] = ["px-3","py-1.5","rounded","border","border-border/60","hover:bg-surface/60","transition"]
        next_link.string = "Dalej"
        nav.append(next_link)
    else:
        span_next = soup.new_tag("span")
        span_next["class"] = ["px-3","py-1.5","rounded","border","border-border/40","opacity-40","cursor-not-allowed"]
        span_next.string = "Dalej"
        nav.append(span_next)
    return nav

def generate_all_paginated_pages() -> None:
    """Generuje strony paginacji oraz aktualizuje index.html.

    Nowa logika:
    - Tylko realna liczba stron (total_pages); brak sztucznego dopełniania.
    - Strona 1 = index.html (hero, sekcje). Strony 2..N = uproszczony layout.
    - Usuwa nadmiarowe pliki jeśli liczba stron się zmniejszyła.
    - Każda strona zawiera nawigację (pojawia się tylko jeśli total_pages>1).
    - Per-page = MAX_CARDS.
    """
    if not PAGINATION_ENABLED:
        return
    posts = collect_all_posts()
    per_page = MAX_CARDS
    total_pages = (len(posts) + per_page - 1) // per_page if posts else 1
    base_html = INDEX_FILE.read_text(encoding="utf-8") if INDEX_FILE.exists() else ""
    for page in range(1, total_pages + 1):
        start = (page - 1) * per_page
        end = start + per_page
        subset = posts[start:end]
        if page == 1:
            soup = BeautifulSoup(base_html, "html.parser")
            container = soup.find(id="posts-container")
            if not container:
                continue
            # Wyczyść istniejące artykuły
            for art in container.find_all("article", recursive=False):
                art.decompose()
            # Usuń stare nav-y
            parent = container.parent
            if parent:
                for old_nav in list(parent.find_all("nav", class_=re.compile("pagination-nav"))):
                    old_nav.decompose()
            marker = None
            for c in container.children:
                if isinstance(c, type(soup.new_string(""))) and "AUTO-BLOG" in str(c):
                    marker = c
                    break
            if subset:
                for post in subset:
                    card = build_card_html(soup, post)
                    if marker:
                        marker.insert_after(card)
                        marker = card
                    else:
                        container.append(card)
            else:
                empty_info = soup.new_tag("p")
                empty_info["class"] = ["col-span-full","text-center","text-text/60","text-sm"]
                empty_info.string = "Brak wpisów – wkrótce pojawią się nowe."
                container.append(empty_info)
            nav = build_pagination_nav(soup, page, total_pages)
            if total_pages > 1:
                container_parent = container.parent
                container_parent.append(nav)
            INDEX_FILE.write_text(str(soup), encoding="utf-8")
        else:
            soup = BeautifulSoup(
                "<!DOCTYPE html><html lang=\"pl\"><head><meta charset='utf-8'/><title>Archiwum – Strona "
                + str(page)
                + " – True Results Online</title><meta name=\"description\" content=\"Archiwum analiz – strona "
                + str(page)
                + "\"/><meta name='viewport' content='width=device-width, initial-scale=1.0'/><link rel='icon' type='image/svg+xml' href='/favicon.svg'/><script src='https://cdn.tailwindcss.com?plugins=typography'></script></head><body class='bg-background text-text antialiased' style='font-family:Inter,system-ui,sans-serif'>",
                "html.parser",
            )
            body = soup.body
            header = soup.new_tag("header")
            header["class"] = "border-b border-border/60 backdrop-blur supports-[backdrop-filter]:bg-background/70 sticky top-0 z-50"
            header_inner = soup.new_tag("div")
            header_inner["class"] = "max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16"
            a_home = soup.new_tag("a", href="index.html")
            a_home["class"] = "font-semibold tracking-tight text-lg hover:text-accent transition-colors"
            a_home.string = "TrueResults"
            span_dot = soup.new_tag("span")
            span_dot["class"] = "text-accent"
            span_dot.string = ".online"
            a_home.append(span_dot)
            header_inner.append(a_home)
            header.append(header_inner)
            body.append(header)
            main = soup.new_tag("main")
            section = soup.new_tag("section")
            section["class"] = "py-14"
            wrap = soup.new_tag("div")
            wrap["class"] = "max-w-6xl mx-auto px-4 sm:px-6"
            h1 = soup.new_tag("h1")
            h1["class"] = "text-2xl md:text-3xl font-semibold mb-8"
            h1.string = f"Archiwum – Strona {page}"
            grid = soup.new_tag("div")
            grid["class"] = "grid gap-8 sm:grid-cols-2 lg:grid-cols-3"
            if subset:
                for post in subset:
                    grid.append(build_card_html(soup, post))
            else:
                empty_info = soup.new_tag("p")
                empty_info["class"] = "col-span-full text-center text-text/60 text-sm"
                empty_info.string = "Brak starszych wpisów do wyświetlenia."
                grid.append(empty_info)
            wrap.append(h1)
            wrap.append(grid)
            nav = build_pagination_nav(soup, page, total_pages)
            if total_pages > 1:
                wrap.append(nav)
            section.append(wrap)
            main.append(section)
            body.append(main)
            footer = soup.new_tag("footer")
            footer["class"] = "border-t border-border/60 py-8 text-sm text-text/60"
            fwrap = soup.new_tag("div")
            fwrap["class"] = "max-w-6xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-4"
            pcopy = soup.new_tag("p")
            pcopy.string = "© True Results Online"
            fwrap.append(pcopy)
            footer.append(fwrap)
            body.append(footer)
            out_file = REPO_PATH / f"{PAGINATION_PREFIX}{page}.html"
            out_file.write_text(str(soup), encoding="utf-8")
    # Usuń pliki wybiegające poza nowy zakres
    existing = list(REPO_PATH.glob(f"{PAGINATION_PREFIX}[0-9]*.html"))
    for f in existing:
        m = re.search(rf"{PAGINATION_PREFIX}(\d+)\.html", f.name)
        if m:
            num = int(m.group(1))
            if num > total_pages:
                try:
                    f.unlink()
                except Exception:
                    pass
    try:
        generate_full_spis(posts)
    except Exception as e:  # pragma: no cover
        print(f"[SPIS] Błąd generowania spisu: {e}")

def generate_full_spis(posts: list[dict]) -> None:
    """Generuje stronę spis.html wiernie odwzorowując styl (kolorystykę, klasy) index.html.

    Założenia:
    - Reużywamy <head>, <header> i <footer> z index.html (z modyfikacjami tytułu/opisu/kanonicznego linku).
    - Link "O projekcie" prowadzi do index.html#about.
    - Link "Spis Treści" wskazuje bieżącą stronę i jest gwarantowany.
    - Zachowujemy klasy body jak w index.html (m.in. selection:bg-accent/30).
    """
    if not posts:
        posts = collect_all_posts()
    if not INDEX_FILE.exists():  # fallback stary minimalny wariant
        # (Teoretycznie index zawsze istnieje, ale zachowujemy defensywnie)
        simple = ["<!DOCTYPE html>", "<html lang='pl'>", "<head><meta charset='utf-8'/>",
                  "<title>Spis Treści – True Results Online</title>",
                  "<meta name='description' content='Pełny spis treści wszystkich analiz True Results Online'/>",
                  "<script src='https://cdn.tailwindcss.com?plugins=typography'></script>",
                  "</head><body class='bg-background text-text antialiased'>"]
        simple.append("<main class='pt-20 pb-16 md:pt-24 md:pb-10 max-w-6xl mx-auto px-4 sm:px-6'>")
        simple.append("<h1 class='text-3xl md:text-4xl font-bold tracking-tight mb-10'>Spis Treści</h1>")
        for p in posts:
            simple.append(
                "<article class='border-b border-border/40 pb-6'>"
                f"<h2 class='text-lg font-semibold'><a class='hover:text-accent transition-colors' href='pages/{p['slug']}.html'>{p['title']}</a></h2>"
                f"<p class='mt-1 text-xs text-text/60'>{p['date'].strftime('%Y-%m-%d')}</p>"
                f"<p class='mt-2 text-sm text-text/80 leading-relaxed'>{p['description']}</p>"
                "</article>"
            )
        simple.append("</main></body></html>")
        SPIS_FILE.write_text("\n".join(simple), encoding="utf-8")
        return

    index_html = INDEX_FILE.read_text(encoding="utf-8")
    # HEAD – kopiujemy i modyfikujemy tytuł / meta description / canonical
    m_head = re.search(r"<head[\s\S]*?</head>", index_html, re.IGNORECASE)
    head_html = m_head.group(0) if m_head else "<head></head>"
    # title
    head_html = re.sub(r"<title>.*?</title>", "<title>Spis Treści – True Results Online</title>", head_html, count=1, flags=re.DOTALL|re.IGNORECASE)
    # meta description – zamień lub dodaj
    if re.search(r'<meta[^>]+name=["\']description["\']', head_html, re.IGNORECASE):
        head_html = re.sub(r'(<meta[^>]+name=["\']description["\'][^>]*content=")[^"]*("[^>]*>)',
                           r'\1Pełny spis treści wszystkich analiz True Results Online\2', head_html, count=1, flags=re.IGNORECASE)
    else:
        head_html = head_html.replace("</head>", "<meta name=\"description\" content=\"Pełny spis treści wszystkich analiz True Results Online\"/>\n</head>")
    # canonical
    if "spis.html" not in head_html:
        head_html = head_html.replace("</head>", "<link rel=\"canonical\" href=\"https://trueresults.online/spis.html\"/>\n</head>")

    # HEADER
    m_header = re.search(r"<header[\s\S]*?</header>", index_html, re.IGNORECASE)
    header_html = m_header.group(0) if m_header else ""
    if header_html:
        # brand link -> index.html
        header_html = re.sub(r'href=["\']#["\']', 'href="index.html"', header_html, count=1)
        # O projekcie -> index.html#about
        header_html = re.sub(r'href=["\']#about["\']', 'href="index.html#about"', header_html)
        # Dodaj (lub upewnij się) link Spis Treści
        if 'Spis Treści' not in header_html:
            header_html = re.sub(r"</nav>", "<a class='hover:text-accent transition-colors' href='spis.html'>Spis Treści</a></nav>", header_html, count=1)
        else:
            # Upewnij się, że href do spisu jest poprawny
            header_html = re.sub(r"href=[\"']spis\.html[\"']", "href='spis.html'", header_html)

    # FOOTER
    m_footer = re.search(r"<footer[\s\S]*?</footer>", index_html, re.IGNORECASE)
    footer_html = m_footer.group(0) if m_footer else ""
    if footer_html:
        footer_html = re.sub(r'href=["\']#about["\']', 'href="index.html#about"', footer_html)
        # Usuń linki 'O projekcie' i 'Kontakt' ze stopki całkowicie
        footer_html = re.sub(r"<a[^>]+href=\"[^\"]*#about\"[^>]*>.*?</a>", "", footer_html, flags=re.IGNORECASE)
        footer_html = re.sub(r"<a[^>]+href=\"[^\"]*#\"[^>]*>.*?</a>", "", footer_html, flags=re.IGNORECASE)  # potencjalny 'Kontakt' z href="#"
        footer_html = re.sub(r"<a[^>]+href=\"[^\"]*kontakt[^\"]*\"[^>]*>.*?</a>", "", footer_html, flags=re.IGNORECASE)
        # Upewnij się, że jest link do Spisu (jeśli chcesz go zatrzymać w stopce) – lub usuń cały nav jeśli pusty
        if 'spis.html' not in footer_html:
            footer_html = footer_html.replace("</nav>", "<a class='hover:text-accent transition-colors' href='spis.html'>Spis Treści</a></nav>")
        # Jeśli nav stał się pusty (np. tylko białe znaki i </nav>) usuń go
        footer_html = re.sub(r"<nav[^>]*>\s*</nav>", "", footer_html)

    # BODY classes
    m_body = re.search(r"<body[^>]*class=\"([^\"]*)\"", index_html)
    body_classes = m_body.group(1) if m_body else "bg-background text-text antialiased selection:bg-accent/30"

    # Sekcja główna spisu – zachowujemy spacing jak w sekcji bloga/hero
    lines = ["<!DOCTYPE html>", "<html lang='pl'>", head_html,
             f"<body class=\"{body_classes}\">"]
    if header_html:
        lines.append(header_html)
    lines.append("<main><section class='pt-20 pb-16 md:pt-24 md:pb-10 animate-fade-in'><div class='max-w-6xl mx-auto px-4 sm:px-6'>")
    lines.append("<h1 class='text-3xl md:text-4xl font-bold tracking-tight mb-10'>Spis Treści</h1>")
    lines.append("<div class='space-y-8'>")
    for p in posts:
        lines.append(
            "<article class='border-b border-border/40 pb-6'>"
            f"<h2 class='text-lg font-semibold'><a class='hover:text-accent transition-colors' href='pages/{p['slug']}.html'>{p['title']}</a></h2>"
            f"<p class='mt-1 text-xs text-text/60'>{p['date'].strftime('%Y-%m-%d')}</p>"
            f"<p class='mt-2 text-sm text-text/80 leading-relaxed'>{p['description']}</p>"
            "</article>"
        )
    lines.append("</div></div></section></main>")
    if footer_html:
        lines.append(footer_html)
    lines.append("</body></html>")
    SPIS_FILE.write_text("\n".join(lines), encoding="utf-8")
    # Po wygenerowaniu spisu – zaktualizuj listę blogPost w index.json-ld jeśli możliwe
    try:
        update_index_jsonld(posts[:50])
    except Exception as e:  # pragma: no cover
        print(f"[JSON-LD] Błąd aktualizacji blogPost: {e}")

def update_index_jsonld(latest_posts: list[dict]) -> None:
    if not INDEX_FILE.exists():
        return
    html = INDEX_FILE.read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    script_tag = soup.find('script', {'id': 'structured-data'})
    if not script_tag or not script_tag.string:
        return
    try:
        data = json.loads(script_tag.string)
    except Exception:
        return
    posts_ld = []
    for p in latest_posts:
        posts_ld.append({
            '@type': 'BlogPosting',
            'headline': p['title'],
            'datePublished': p['date'].strftime('%Y-%m-%d'),
            'url': f"{BASE_URL}/pages/{p['slug']}.html",
            'description': p['description'],
        })
    data['blogPost'] = posts_ld
    script_tag.string.replace_with(json.dumps(data, ensure_ascii=False, indent=2))
    INDEX_FILE.write_text(str(soup), encoding='utf-8')

def generate_campaign_hub(campaign_name: str) -> None:
    if not CAMPAIGN_HUB_ENABLED:
        return  # feature wyłączony
    slug = slugify(campaign_name)
    hub_file = REPO_PATH / f"{CAMPAIGN_HUB_PREFIX}{slug}.html"
    # Zbierz wpisy (heurystyka – po tytułach w historii kampanii)
    posts = collect_all_posts()
    # Na razie nie mamy zapisanego powiązania kampania->slug w plikach; pokazujemy ostatnie z listy
    body_parts = [f"<h1 class='text-3xl md:text-4xl font-bold tracking-tight mb-10'>Kampania: {campaign_name}</h1>"]
    body_parts.append("<div class='space-y-8'>")
    for p in posts[:60]:
        body_parts.append(
            "<article class='border-b border-border/40 pb-6'>"
            f"<h2 class='text-lg font-semibold'><a class='hover:text-accent transition-colors' href='pages/{p['slug']}.html'>{p['title']}</a></h2>"
            f"<p class='mt-1 text-xs text-text/60'>{p['date'].strftime('%Y-%m-%d')}</p>"
            f"<p class='mt-2 text-sm text-text/80 leading-relaxed'>{p['description']}</p>"
            "</article>"
        )
    body_parts.append("</div>")
    # Minimalny HTML (bez hero) – reużyj stylu
    html = ["<!DOCTYPE html><html lang='pl'><head><meta charset='utf-8'/>",
            f"<title>{campaign_name} – Kampania – True Results Online</title>",
            f"<meta name='description' content='Wpisy w ramach kampanii: {campaign_name}'/>",
            f"<link rel='canonical' href='{BASE_URL}/{CAMPAIGN_HUB_PREFIX}{slug}.html' />",
            "<script src='https://cdn.tailwindcss.com?plugins=typography'></script>",
            "</head>",
            "<body class='bg-background text-text antialiased selection:bg-accent/30'>",
            "<main class='pt-20 pb-16 md:pt-24 md:pb-10 max-w-6xl mx-auto px-4 sm:px-6 prose prose-invert prose-sm md:prose-base'>",
            *body_parts,
            "</main>",
            "</body></html>"]
    hub_file.write_text("\n".join(html), encoding='utf-8')

def retrofit_article_file(path: Path) -> None:
    try:
        html = path.read_text(encoding='utf-8')
    except Exception:
        return
    # Canonical – jeśli brak
    if 'rel="canonical"' not in html:
        # heurystyka slug
        slug = path.name
        html = re.sub(r"</head>", f"<link rel=\"canonical\" href=\"{BASE_URL}/pages/{slug}\" />\n</head>", html, count=1)
    # FAQ – jeśli brak FAQ sekcji a posiadamy treść artykułu
    if 'id="faq"' not in html:
        m_body = re.search(r"(<article[\s\S]*?</article>)", html)
        if m_body:
            article_block = m_body.group(1)
            # wyłuskaj tytuł
            m_title = re.search(r"<h1 class=\"mb-2\">(.*?)</h1>", article_block)
            title = m_title.group(1).strip() if m_title else path.stem
            # plain
            plain = extract_plain(article_block)
            faq_list = generate_faq(title, plain)
            faq_html_parts = ["<section class='mt-10 not-prose' id='faq'><h2 class='text-lg font-semibold mb-4'>FAQ</h2><dl class='space-y-4'>"]
            for item in faq_list:
                faq_html_parts.append(f"<div class='border border-border/40 rounded-lg p-4 bg-surface/60'><dt class='font-medium'>{item['question']}</dt><dd class='mt-2 text-sm text-text/80 leading-relaxed'>{item['answer']}</dd></div>")
            faq_html_parts.append("</dl></section>")
            faq_block = "\n".join(faq_html_parts)
            article_block_new = article_block.replace("</article>", faq_block + "</article>")
            html = html.replace(article_block, article_block_new, 1)
    # Related placeholder – jeśli brak
    if 'related-placeholder' not in html:
        html = html.replace("</article>", "<div id='related-placeholder'></div></article>")
    path.write_text(html, encoding='utf-8')

def cleanup_campaign_hub_files() -> None:
    """Usuwa istniejące pliki hubów kampanii (kampania-*.html) gdy feature jest wyłączony.

    Zostawiamy inne pliki w spokoju. Idempotentne – wielokrotne wywołanie bez skutków ubocznych.
    """
    if CAMPAIGN_HUB_ENABLED:
        return
    pattern = f"{CAMPAIGN_HUB_PREFIX}*.html"
    for f in REPO_PATH.glob(pattern):
        try:
            f.unlink()
            print(f"[HUB-CLEANUP] Usunięto {f.name}")
        except Exception as e:  # pragma: no cover
            print(f"[HUB-CLEANUP] Nie można usunąć {f.name}: {e}")

def retrofit_all_articles() -> None:
    if not PAGES_DIR.exists():
        return
    for f in PAGES_DIR.glob('*.html'):
        retrofit_article_file(f)


def retrofit_home_links() -> None:
    """Naprawia link 'Strona główna' w istniejących wpisach.

    Poprzednio w szablonie użyto href="/" co przy hostingu w podkatalogu lub przy lokalnym
    otwieraniu plików (file://) powoduje przeniesienie do root systemu / domeny zamiast do index.html.

    Nowa konwencja (patrz aktualny szablon): href="../index.html"

    Działanie:
    - W każdym pliku pages/*.html znajdujemy nagłówek <header> z linkiem zawierającym tekst
      'Strona główna'. Jeśli href to "/" lub pusty lub samo "#" – zmieniamy na "../index.html".
    - Idempotentne: wielokrotne uruchomienie nie wprowadza dalszych zmian.
    """
    if not PAGES_DIR.exists():
        return
    pattern = re.compile(r'(>←?\s*Strona główna<)', re.IGNORECASE)
    for f in PAGES_DIR.glob('*.html'):
        try:
            txt = f.read_text(encoding='utf-8')
        except Exception:
            continue
        # Szybka detekcja – jeśli nie ma frazy, pomiń aby przyspieszyć.
        if 'Strona główna' not in txt:
            continue
        # Szukamy anchorów z potencjalnie błędnym href.
        # Przykład starego fragmentu: <a href="/" class="...">← Strona główna</a>
        new_txt = re.sub(
            r'<a\s+([^>]*?)href=["\'](?:/|#|)["\']([^>]*)>(?:←\s*)?Strona główna</a>',
            r'<a \1href="../index.html"\2>← Strona główna</a>',
            txt,
            flags=re.IGNORECASE
        )
        if new_txt != txt:
            try:
                f.write_text(new_txt, encoding='utf-8')
            except Exception:
                pass


def retrofit_article_headers() -> None:
    """Aktualizuje nagłówek w istniejących artykułach do pełnej wersji (logo + nawigacja).

    Wcześniejsze wersje miały prosty <header> z linkiem '← Strona główna'. Teraz chcemy spójność
    wizualną: taki sam pasek jak na stronie głównej (bez sekcji hero).

    Kryterium wykrycia do podmiany:
    - Jeśli w pliku w sekcji <body> znajduje się fragment '← Strona główna' LUB
      <header class="border-b border-border/60 h-16 ...> itp.
    - Jeśli już istnieje 'aria-label="Strona główna True Results Online"' – pomijamy (już zaktualizowane).

    Implementacja: regex zamienia CAŁY pierwszy <header>...</header> po <body na nowy blok.
    Idempotentne: ponowne uruchomienie nie zmieni nic jeśli nagłówek jest już zgodny.
    """
    if not PAGES_DIR.exists():
        return
    new_header = (
        '<header class="border-b border-border/60 backdrop-blur supports-[backdrop-filter]:bg-background/70 sticky top-0 z-50">'
        '<div class="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">'
        '<a href="../index.html" aria-label="Strona główna True Results Online" '
        'class="font-semibold tracking-tight text-lg hover:text-accent transition-colors">'
        'TrueResults<span class="text-accent">.online</span></a>'
        '<nav class="flex items-center gap-6 text-sm" aria-label="Main navigation">'
        '<a href="../index.html#about" class="hover:text-accent transition-colors">O projekcie</a>'
        '<a href="../spis.html" class="hover:text-accent transition-colors">Spis Treści</a>'
        '</nav></div></header>'
    )
    # Ucieczka znaków dla regexu
    for f in PAGES_DIR.glob('*.html'):
        try:
            txt = f.read_text(encoding='utf-8')
        except Exception:
            continue
        if 'aria-label="Strona główna True Results Online"' in txt:
            continue  # już nowy
        if 'Strona główna' not in txt:
            continue
        # Znajdź pierwszy <header ...</header>
        new_txt = re.sub(r"<header[\s\S]*?</header>", new_header, txt, count=1, flags=re.IGNORECASE)
        if new_txt != txt:
            try:
                f.write_text(new_txt, encoding='utf-8')
            except Exception:
                pass


def ensure_spis_link_in_index() -> None:
    if not INDEX_FILE.exists():
        return
    html = INDEX_FILE.read_text(encoding="utf-8")
    if 'Spis Treści' in html:
        return
    # W prosty sposób: znajdź pierwszy link 'O projekcie' i wstaw po nim
    new_html = html.replace("O projekcie</a>", "O projekcie</a><a class=\"hover:text-accent transition-colors\" href=\"spis.html\">Spis Treści</a>", 1)
    INDEX_FILE.write_text(new_html, encoding="utf-8")

def cleanup_duplicate_paginations() -> None:
    if not INDEX_FILE.exists():
        return
    html = INDEX_FILE.read_text(encoding="utf-8")
    if not PAGINATION_ENABLED:
        # Usuń WSZYSTKIE nawigacje paginacyjne i linki do pageX.html
        new_html = re.sub(r"<nav[^>]+pagination-nav[^>]*>.*?</nav>", "", html, flags=re.DOTALL)
        # Usuń ewentualne odnośniki do pageX.html pozostawione w innych miejscach
        new_html = re.sub(r"<a[^>]+href=\"page\d+\.html\"[^>]*>.*?</a>", "", new_html)
        INDEX_FILE.write_text(new_html, encoding="utf-8")
        return
    # (Gdyby paginacja została ponownie włączona – stary mechanizm można tu odtworzyć.)

def remove_paginated_files() -> None:
    if PAGINATION_ENABLED:
        return
    for f in REPO_PATH.glob(f"{PAGINATION_PREFIX}[0-9]*.html"):
        try:
            f.unlink()
        except Exception:
            pass


def generate_rss_feed(max_items: int = 30) -> None:
    """Generuje prosty RSS 2.0 feed (feed.xml) na podstawie plików w pages/.

    Uwagi:
    - Parsuje tytuł, opis (meta description), datę i pierwszy akapit treści.
    - Sortuje według daty (desc) wykorzystując datePublished lub datę z nazwy pliku.
    - Generuje kanał z ostatnimi N pozycjami.
    - Działa w trybie "best effort" – brakujące pola pomija.
    """
    import html as _html
    import email.utils as _eutils
    items = []
    for file in PAGES_DIR.glob("*.html"):
        try:
            txt = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Tytuł
        m_title = re.search(r"<title>(.*?)</title>", txt, re.IGNORECASE | re.DOTALL)
        if not m_title:
            continue
        title = m_title.group(1).strip()
        # Skróć tytuł (usuń sufiks po '– True Results Online') jeśli występuje
        if " – " in title:
            title = title.split(" – ")[0].strip()
        # Meta description
        m_desc = re.search(r'<meta\s+name="description"\s+content="(.*?)"', txt, re.IGNORECASE)
        description = m_desc.group(1).strip() if m_desc else ""
        # Data – próbuj datePublished z JSON-LD / meta
        m_date = re.search(r'datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"', txt)
        if not m_date:
            # fallback: znajdź w znaczniku <time datetime="...">
            m_date = re.search(r'<time[^>]+datetime="(\d{4}-\d{2}-\d{2})"', txt)
        if m_date:
            date_str = m_date.group(1)
        else:
            # fallback z nazwy pliku
            # slug-date pattern: ...-YYYYMMDD.html
            m_fn = re.search(r'(\d{8})\.html$', file.name)
            if m_fn:
                d_raw = m_fn.group(1)
                date_str = f"{d_raw[0:4]}-{d_raw[4:6]}-{d_raw[6:8]}"
            else:
                date_str = dt.date.today().strftime("%Y-%m-%d")
        try:
            pub_date = dt.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pub_date = dt.datetime.now()
        # Pierwszy akapit (opcjonalnie)
        m_para = re.search(r"<p>(.*?)</p>", txt, re.DOTALL)
        content_snippet = m_para.group(1).strip() if m_para else description
        # Kanoniczny URL
        m_canon = re.search(r'<link\s+rel="canonical"\s+href="(.*?)"', txt)
        if m_canon:
            url = m_canon.group(1)
        else:
            # zbuduj z BASE_URL + pages/filename
            url = f"{BASE_URL}/pages/{file.name}"
        items.append({
            "title": title,
            "description": description,
            "content": content_snippet,
            "url": url,
            "pub_date": pub_date,
            "guid": url,
        })
    # Sort
    items.sort(key=lambda x: x["pub_date"], reverse=True)
    items = items[:max_items]
    # Budowa RSS
    last_build = _eutils.format_datetime(dt.datetime.utcnow())
    channel_title = "True Results Online"
    channel_link = BASE_URL
    channel_desc = "Psychologicznie ugruntowane analizy relacyjne i poznawcze."
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        "<channel>",
        f"<title>{_html.escape(channel_title)}</title>",
        f"<link>{_html.escape(channel_link)}</link>",
        f"<description>{_html.escape(channel_desc)}</description>",
        f"<language>pl</language>",
        f"<lastBuildDate>{last_build}</lastBuildDate>",
    ]
    for it in items:
        pub_str = _eutils.format_datetime(it["pub_date"])
        description_escaped = _html.escape(it["description"]) if it["description"] else _html.escape(it["content"])[:300]
        parts.extend([
            "<item>",
            f"<title>{_html.escape(it['title'])}</title>",
            f"<link>{_html.escape(it['url'])}</link>",
            f"<guid>{_html.escape(it['guid'])}</guid>",
            f"<pubDate>{pub_str}</pubDate>",
            f"<description>{description_escaped}</description>",
            "</item>",
        ])
    parts.append("</channel></rss>")
    FEED_FILE.write_text("\n".join(parts), encoding="utf-8")


def generate_sitemap() -> None:
    """Generuje / aktualizuje sitemap.xml na podstawie plików HTML w repo.

    Zasady:
    - Zawsze uwzględnia stronę główną / (index.html) – priority 1.0
    - Uwzględnia spis treści (spis.html) jeśli istnieje – priority 0.8
    - Każdy wpis w pages/ jako osobny <url> – priority 0.55
    - lastmod czerpany z datePublished / nazwy pliku / daty mtime jako ostateczny fallback
    - URL-e budowane na bazie BASE_URL
    - Kolejność: root, spis, wpisy (najnowsze pierwsze)
    """
    import html as _html  # noqa: F401  (zgodnie ze stylem gener_rss)

    urls: list[dict] = []

    today = dt.date.today().strftime("%Y-%m-%d")

    # Strona główna
    urls.append({
        "loc": f"{BASE_URL}/",
        "lastmod": today,
        "priority": "1.00",
    })

    # Spis treści
    if SPIS_FILE.exists():
        # Fallback lastmod = dzisiaj (regenerowany przy każdym wpisie)
        urls.append({
            "loc": f"{BASE_URL}/spis.html",
            "lastmod": today,
            "priority": "0.80",
        })

    # Wpisy
    posts: list[dict] = []
    for file in PAGES_DIR.glob("*.html"):
        try:
            txt = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Data publikacji
        m_date = re.search(r'datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"', txt)
        if not m_date:
            m_date = re.search(r'<time[^>]+datetime="(\d{4}-\d{2}-\d{2})"', txt)
        if m_date:
            date_str = m_date.group(1)
        else:
            m_fn = re.search(r'(\d{8})\.html$', file.name)
            if m_fn:
                d_raw = m_fn.group(1)
                date_str = f"{d_raw[0:4]}-{d_raw[4:6]}-{d_raw[6:8]}"
            else:
                # Fallback: mtime pliku
                try:
                    date_str = dt.date.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d")
                except Exception:
                    date_str = today
        # URL – canonical jeśli istnieje
        m_canon = re.search(r'<link\s+rel="canonical"\s+href="(.*?)"', txt)
        if m_canon:
            loc = m_canon.group(1)
        else:
            loc = f"{BASE_URL}/pages/{file.name}"
        posts.append({
            "loc": loc,
            "lastmod": date_str,
            "priority": "0.55",
            "date": date_str,
        })

    # Sortuj wpisy malejąco po dacie
    def _parse(d: str) -> dt.datetime:
        try:
            return dt.datetime.strptime(d, "%Y-%m-%d")
        except Exception:
            return dt.datetime.min

    posts.sort(key=lambda x: _parse(x["date"]), reverse=True)
    urls.extend(posts)

    # Budowa XML
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{u['loc']}</loc>")
        lines.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        lines.append(f"    <priority>{u['priority']}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>\n")
    SITEMAP_FILE.write_text("\n".join(lines), encoding="utf-8")


def ensure_rss_link_in_index() -> None:
    """Dodaje <link rel="alternate" ...> do index.html jeśli brak."""
    if not INDEX_FILE.exists():
        return
    html = INDEX_FILE.read_text(encoding="utf-8")
    if "application/rss+xml" in html:
        return
    # Wstrzykuj przed zamknięciem </head>
    insertion = '\n<link rel="alternate" type="application/rss+xml" title="True Results Online RSS" href="feed.xml" />'
    new_html = re.sub(r"</head>", insertion + "\n</head>", html, count=1, flags=re.IGNORECASE)
    INDEX_FILE.write_text(new_html, encoding="utf-8")


def create_post(for_date: dt.date | None = None, skip_index: bool = False):
    """Tworzy pojedynczy wpis.

    Parametry:
    - for_date: jeśli podano, użyj tej daty (np. przy masowej rekonstrukcji wstecz);
    - skip_index: jeśli True, nie wstawiaj karty do index.html (użyteczne gdy po serii wpisów i tak wywołamy rebuild_index_from_pages).
    """
    today = for_date or dt.date.today()
    topic = pick_topic(for_date=for_date)
    current_campaign = get_current_campaign(today)
    # NOWY PRZEPŁYW: zawsze próbuj użyć MASTER PROMPT (jeśli aktywny)
    # Funkcja generatora sama załaduje master prompt
    data = generate_full_article_from_master_prompt(topic)
    slug = slugify(data["title"]) + f"-{today.strftime('%Y%m%d')}"
    post_path = PAGES_DIR / f"{slug}.html"
    html = build_post_html(data, today, slug)
    post_path.write_text(html, encoding="utf-8")
    # Powiązane wpisy – dołącz po zapisaniu
    try:
        related = select_related_posts(slug, current_campaign)
        if related:
            html_now = post_path.read_text(encoding='utf-8')
            rel_parts = ["<section class='mt-12 not-prose' id='related'><h2 class='text-lg font-semibold mb-4'>Powiązane analizy</h2><ul class='space-y-2'>"]
            for r in related:
                rel_parts.append(f"<li><a class='text-accent hover:underline text-sm' href='{r['slug']}.html'>{r['title']}</a></li>")
            rel_parts.append("</ul></section>")
            block = "\n".join(rel_parts)
            html_now = html_now.replace("<div id='related-placeholder'></div>", block)
            post_path.write_text(html_now, encoding='utf-8')
    except Exception as e:  # pragma: no cover
        print(f"[RELATED] Błąd: {e}")
    if not skip_index:
        insert_card_in_index(slug, data, today, current_campaign)
    # Paginacja: po dodaniu nowego wpisu odśwież wszystkie strony (index + page2+)
    try:
        generate_all_paginated_pages()
    except Exception as e:  # pragma: no cover
        print(f"[PAGINATION] Błąd generowania stron: {e}")
    # Retrofit kategorii (meta + JSON-LD) – na wypadek starszych wpisów
    try:
        retrofit_article_categories()
    except Exception as e:  # pragma: no cover
        print(f"[KAT] Błąd retrofit kategorii: {e}")
    # Aktualizacja feedu RSS
    try:
        generate_rss_feed()
        ensure_rss_link_in_index()
    except Exception as e:  # pragma: no cover
        print(f"[RSS] Nie udało się wygenerować feedu: {e}")
    # Sitemap.xml
    try:
        generate_sitemap()
    except Exception as e:  # pragma: no cover
        print(f"[SITEMAP] Nie udało się zaktualizować sitemap.xml: {e}")
    try:
        ensure_spis_link_in_index()
        cleanup_duplicate_paginations()
        # Zawsze aktualizuj spis pełny
        generate_full_spis(collect_all_posts())
        # Retrofit linków do strony głównej (na wszelki wypadek gdyby stare wpisy były jeszcze niepoprawione)
        retrofit_home_links()
        # Retrofit pełnego nagłówka (logo + nawigacja) w istniejących artykułach
        retrofit_article_headers()
    except Exception as e:  # pragma: no cover
        print(f"[SPIS/NAV] Błąd: {e}")
    # KROK 4: Aktualizacja tytułu kampanii na stronie głównej (warunkowo)
    # Nagłówek kampanii na stronie głównej WYŁĄCZONY na życzenie użytkownika.
    # Zachowujemy blok jako dokumentację – aby przywrócić ustaw SHOW_CAMPAIGN_TITLE=1 i odkomentuj poniższe.
    # try:
    #     if os.getenv("SHOW_CAMPAIGN_TITLE", "0") == "1":
    #         updated = update_campaign_title_on_index(current_campaign)
    #         if updated:
    #             print(f"[KAMPANIA] Zaktualizowano nagłówek kampanii: {current_campaign}")
    # except Exception as e:  # pragma: no cover
    #     print(f"[KAMPANIA] Błąd aktualizacji nagłówka: {e}")
    return slug, data, topic, current_campaign


def git_commit_and_push(slug: str, data: dict):
    """Prostsza, deterministyczna wersja: dodaje WSZYSTKIE zmiany i wypycha jeśli cokolwiek się zmieniło.

    Zachowanie sterowane zmiennymi środowiskowymi:
    - GIT_ADD_ALL=1 (domyślnie): używa `git add -A`.
    - GIT_COMMIT_PREFIX: prefiks wiadomości commita (np. "[auto]").
    - GIT_PUSH=0 -> tylko commit lokalny bez push.
    """
    try:
        repo = Repo(REPO_PATH)
    except Exception as e:  # brak repo – nie przerywamy
        print(f"[GIT] Pomijam operacje git (brak repo): {e}")
        return

    try:
        add_all = os.getenv("GIT_ADD_ALL", "1") == "1"
        if add_all:
            repo.git.add(all=True)  # równoważne -A
        else:
            # Minimalny zestaw – strony + indeks + feed/sitemap
            patterns = ["pages/*.html", "index.html", "feed.xml", "sitemap.xml", "spis.html"]
            for pat in patterns:
                try:
                    repo.git.add(pat)
                except Exception:
                    pass

        is_initial = False
        try:
            repo.head.commit  # noqa: B018 (sprawdzenie istnienia commita)
        except Exception:
            is_initial = True

        dirty = repo.is_dirty(untracked_files=True)
        if not dirty and not is_initial:
            print("[GIT] Brak zmian do commitowania.")
            return

        prefix = os.getenv("GIT_COMMIT_PREFIX", "[auto]")
        message = f"{prefix} wpis: {data.get('title','(brak tytułu)')} ({slug})"
        repo.index.commit(message)
        if os.getenv("GIT_PUSH", "1") == "1":
            try:
                origin = repo.remote(name="origin")
                origin.push()
                print("[GIT] Commit + push OK.")
            except Exception as e:  # pragma: no cover
                print(f"[GIT] Commit ok, push nieudany: {e}")
        else:
            print("[GIT] Commit lokalny (GIT_PUSH=0).")
    except Exception as e:  # pragma: no cover
        print(f"[GIT] Błąd operacji git: {e}")


def main():
    # Tryb masowej regeneracji: usuń wszystkie istniejące wpisy i wygeneruj N (MASS_REGENERATE) cofając datę dzień po dniu.
    mass = os.getenv("MASS_REGENERATE")
    if mass:
        try:
            count = int(mass)
        except ValueError:
            raise SystemExit("MASS_REGENERATE musi być liczbą całkowitą")
        if count <= 0:
            raise SystemExit("MASS_REGENERATE > 0")
        # 1. Usuń istniejące strony
        if PAGES_DIR.exists():
            for p in PAGES_DIR.glob("*.html"):
                try:
                    p.unlink()
                except Exception as e:
                    print(f"[MASS] Nie usunięto {p.name}: {e}")
        # 2. Wyczyść historię tematów (opcjonalnie aby zwiększyć różnorodność)
        try:
            if HISTORY_FILE.exists():
                HISTORY_FILE.unlink()
        except Exception:
            pass
        # 3. Generuj wpisy od najstarszego do najnowszego aby finalnie najnowszy był na górze po rebuildzie.
        today = dt.date.today()
        generated: list[tuple[str, dict]] = []
        for offset in range(count - 1, -1, -1):
            d = today - dt.timedelta(days=offset)
            try:
                slug, data, topic, campaign_name = create_post(for_date=d, skip_index=True)
                generated.append((slug, data))
                print(f"[MASS] Wygenerowano: {slug} ({d})")
            except Exception as e:
                print(f"[MASS] Błąd przy dacie {d}: {e}")
        # 4. Po serii wpisów – przebuduj index od zera.
        try:
            rebuild_index_from_pages(limit=None)
            ensure_rss_link_in_index()
            ensure_spis_link_in_index()
            cleanup_duplicate_paginations()
            remove_paginated_files()
            generate_sitemap()
            # Nowa paginacja po pełnej odbudowie
            generate_all_paginated_pages()
            # Header retrofit po masowej regeneracji
            retrofit_article_headers()
            retrofit_article_categories()
            cleanup_campaign_hub_files()
        except Exception as e:
            print(f"[MASS] Problem przy finalizacji: {e}")
        print(f"[MASS] Zakończono masową regenerację ({len(generated)} wpisów).")
        return
    # Tryb retrofit SEO bez tworzenia nowych postów
    if os.getenv(SEO_RETROFIT_ENV) == '1':
        print("[SEO] Retrofit istniejących wpisów...")
        retrofit_all_articles()
        retrofit_home_links()
        retrofit_article_headers()
        retrofit_article_categories()
        rebuild_index_from_pages(limit=None)
        posts = collect_all_posts()
        try:
            update_index_jsonld(posts[:50])
        except Exception as e:
            print(f"[SEO] JSON-LD update fail: {e}")
        try:
            generate_sitemap()
        except Exception as e:
            print(f"[SEO] Sitemap fail: {e}")
        return
    # Tryb pełnej odbudowy kart z istniejących plików
    if os.getenv("REBUILD_ALL_PAGES") == "1":
        rebuild_index_from_pages(limit=None)  # wewnętrznie ograniczy index do 21, spis pełny
        ensure_rss_link_in_index()
        ensure_spis_link_in_index()
        cleanup_duplicate_paginations()
        remove_paginated_files()
        retrofit_home_links()
        retrofit_article_headers()
        retrofit_article_categories()
        cleanup_campaign_hub_files()
        try:
            generate_sitemap()
        except Exception as e:  # pragma: no cover
            print(f"[SITEMAP] Błąd generowania sitemap przy REBUILD: {e}")
        try:
            generate_all_paginated_pages()
        except Exception as e:
            print(f"[PAGINATION] Błąd przy REBUILD: {e}")
        print("Zakończono pełną odbudowę index.html z katalogu pages/.")
        return
    if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
        print("OSTRZEŻENIE: Brak prawidłowego klucza GEMINI_API_KEY – używany fallback statyczny.")
    PAGES_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    slug = "?"
    data: dict = {"title": "?", "mode": "error"}
    topic = "?"
    error: Optional[str] = None
    try:
        slug, data, topic, campaign_name = create_post()
        # Hub kampanii wyłączony – brak generowania
        # Aktualizacja index JSON-LD (ostatnie wpisy)
        try:
            update_index_jsonld(collect_all_posts()[:50])
        except Exception as e:
            print(f"[JSON-LD] Błąd: {e}")
        remove_paginated_files()
        cleanup_campaign_hub_files()
        # Paginate (ensure after any potential cleanup)
        try:
            generate_all_paginated_pages()
        except Exception as e:
            print(f"[PAGINATION] Błąd: {e}")
        git_commit_and_push(slug, data)
    except Exception as e:  # logujemy ale nie blokujemy zapisu logu
        error = str(e)
        print(f"[ERROR] Generacja nie w pełni się powiodła: {e}")
    finally:
        # Uwaga: campaign_name może nie istnieć jeśli błąd nastąpił przed create_post
        campaign_for_log = locals().get("campaign_name", "?")
        log_entry = (
            f"DATA={dt.datetime.now().isoformat()} | KAMPANIA={campaign_for_log} | TRYB={data.get('mode')} | TEMAT={topic} | SLUG={slug} | TYTUL={data.get('title')}"
        )
        if error:
            log_entry += f" | ERROR={error}"
        log_entry += "\n"
        with LOG_FILE.open("a", encoding="utf-8") as lf:
            lf.write(log_entry)
    if not error:
        print(f"Dodano wpis: {data['title']} -> {slug}.html (mode={data.get('mode')})")
    else:
        print("Zakończono z błędami – sprawdź log.")


if __name__ == "__main__":
    main()
