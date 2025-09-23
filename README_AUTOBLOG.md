# Automatyczny Blog (True Results Online)

Ten moduł dodaje codzienną automatyczną publikację wpisów analitycznych na GitHub Pages.

## Jak to działa
1. Workflow GitHub Actions (`.github/workflows/autoblog.yml`) uruchamia się codziennie (cron) lub ręcznie.
2. Uruchamiany jest skrypt `update_blog.py`.
3. Skrypt:
   - wybiera temat z aktywnej kampanii tematycznej (ROTACJA DZIENNA po dniu roku),
   - generuje treść korzystając z API Gemini (model domyślny: `gemini-1.5-flash`, fallback jeśli brak klucza),
   - tworzy plik w `pages/SLUG.html` na podstawie `szablon_wpisu.html`,
   - wstawia kartę wpisu do `index.html` (na górę listy),
   - utrzymuje na stronie głównej WYŁĄCZNIE 21 najnowszych wpisów (paginacja aktywna),
   - generuje/aktualizuje `feed.xml` (RSS),
   - generuje/aktualizuje `sitemap.xml`,
   - commit + push.

## Konfiguracja lokalna
1. Utwórz środowisko:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```
2. Skopiuj plik `.env.example` jako `.env` i uzupełnij klucz:
```
cp .env.example .env
```
Edytuj `.env`:
```
GEMINI_API_KEY=TWÓJ_PRAWIDŁOWY_KLUCZ
GEMINI_MODEL=gemini-1.5-flash
```
3. Uruchom skrypt:
```bash
python update_blog.py
```
Jeśli nie ustawisz klucza albo jest błędny – zostanie użyty tryb fallback (statyczny tekst). Informacja pojawi się w konsoli i w logu.

## System Kampanii Tematycznych (Aktualny – dzienna rotacja)
Zamiast jednej płaskiej listy tematów działa mechanizm kampanii – KAŻDEGO DNIA inna kategoria (dzienna rotacja po dniu roku):

1. Kategorie i ich tematy są zdefiniowane w słowniku `CAMPAIGN_TOPICS`.
2. Numer dnia roku (1–366) modulo liczba kategorii wybiera bieżącą kampanię.
3. Plik `used_topics.txt` przechowuje wpisy w formacie `KATEGORIA|TEMAT`, dzięki czemu reset następuje niezależnie per kategoria.
4. Zmienne środowiskowe:
   - `FORCE_CAMPAIGN` – jeśli ustawiona i pasuje do klucza w `CAMPAIGN_TOPICS`, wymusza kampanię niezależnie od tygodnia.
   - (Wyłączone) Dawny `SHOW_CAMPAIGN_BANNER` – baner kampanii został usunięty na życzenie (można przywrócić modyfikując kod).

Dodawanie nowych tematów: edytuj odpowiednią listę w `CAMPAIGN_TOPICS` zamiast starej płaskiej listy.

## Bezpieczeństwo
- Nigdy nie commituj pliku `.env` (jest w `.gitignore`).
- Przykładowe zmienne znajdziesz w `.env.example` – ten plik może być wersjonowany.
- W GitHub Actions dodaj sekret `GEMINI_API_KEY` w ustawieniach repozytorium (Settings → Secrets → Actions).
- Opcjonalnie możesz nadpisać `GEMINI_MODEL` jeśli chcesz użyć innego wariantu.
- Logi (`logs/last_run.txt`) nie zawierają sekretów – tylko meta: data, tryb, temat, slug.

### Dodatkowe zmienne długości artykułu

| Zmienna | Opis | Domyślna |
|---------|------|----------|
| `ART_MIN_WORDS` | Minimalna docelowa liczba słów generowanego artykułu (dotyczy tylko trybu z API – model może nieznacznie odbiegać). | 650 |
| `ART_MAX_WORDS` | Maksymalna docelowa liczba słów generowanego artykułu (jeśli mniejsza niż MIN zostanie automatycznie podniesiona). | 900 |

Przykład w `.env`:
```
ART_MIN_WORDS=800
ART_MAX_WORDS=1100
```
Fallback (gdy brak klucza lub błąd API) generuje skróconą, kontrolną wersję – wartości te nie mają wtedy wpływu.

## Rozszerzenia (pomysły)
- Rozbudowa banera kampanii o opis / CTA.
- Eksport statystyk: które kampanie wygenerowały najwięcej ruchu.
- JSON-LD wzbogacony o `articleSection` = kategoria kampanii.
- Plik `campaign_history.json` do audytu rotacji.
- Hashowa detekcja zmian zamiast porównania rozmiaru.

## Ręczne uruchomienie workflow
W zakładce Actions wybierz `Automatyczny Blog` → Run workflow.

## Tagi wsteczne
Jeśli chcesz wygenerować kilka wpisów wstecz (historycznych):
- Zmień tymczasowo datę w funkcji `create_post()` lub dodaj pętlę po dniach (UWAGA: unikaj zbyt wielu requestów naraz do API Gemini – rate limits).

## Struktura generowanego wpisu
Oparta na `szablon_wpisu.html` – placeholdery w klamrach są podmieniane.

## Debugowanie
- Brak karty na stronie? Sprawdź marker `AUTO-BLOG` w `index.html`.
- Brak commita? Sprawdź log w Actions (czy były zmiany po generowaniu). 
- Pusty wpis? Możliwy błąd z odpowiedzią modelu – zobacz sekcję fallback (log w Actions).
- Konflikty? Unikaj równoległych uruchomień (limituj manualne runy).

## Pełna odbudowa strony głównej (REBUILD_ALL_PAGES)
Jeśli np. ręcznie edytowałeś `index.html`, usunąłeś istniejące karty albo chcesz ponownie zbudować listę wpisów ze wszystkich plików w `pages/`, możesz użyć trybu odbudowy.

### Jak użyć lokalnie
```
REBUILD_ALL_PAGES=1 python update_blog.py
```
Skrypt:
- usuwa wszystkie istniejące `<article>` w kontenerze `#posts-container`,
- skanuje katalog `pages/*.html`,
- wyciąga `h1` (tytuł) i meta description,
- sortuje wpisy po dacie z sufiksu `-YYYYMMDD` (malejąco),
- odtwarza karty (maksymalnie tyle, ile `MAX_CARDS` w kodzie),
- zachowuje komentarz `AUTO-BLOG` jako punkt wstawiania,
- gwarantuje obecność linku do `feed.xml`.

### GitHub Actions
Możesz tymczasowo dodać w workflow przy kroku uruchomienia:
```
env:
   REBUILD_ALL_PAGES: '1'
```
lub dopisać do polecenia: `REBUILD_ALL_PAGES=1 python update_blog.py`.

Po udanej odbudowie nic nowego nie jest generowane – tylko przebudowana lista.

### Kiedy stosować
- Po ręcznym usunięciu kart.
- Po imporcie starszych plików HTML do `pages/`.
- Po większym refaktoringu struktury HTML.

### Ograniczenia
- Dla opisu używany jest meta description – jeśli brak, pojawi się "Bez opisu.".
- Jeśli plik nie ma poprawnego sufiksu daty `-YYYYMMDD`, używana jest dzisiejsza data (może to zmienić kolejność).

## Archiwum, paginacja i spis treści
Aktualny model: PAGINACJA WŁĄCZONA.

1. Strona główna (`index.html`) pokazuje maksymalnie 21 najnowszych wpisów.
2. Starsze wpisy trafiają na kolejne strony: `page2.html`, `page3.html`, ... generowane dynamicznie.
3. Liczba stron jest rzeczywista (brak sztucznego dopełniania do stałej liczby).
4. Każda strona paginacyjna zawiera własną nawigację (poprzednia / numery / następna) – ukrywana jeśli tylko 1 strona.
5. Dodanie nowego wpisu automatycznie:
   - przycina listę kart na stronie głównej do 21,
   - przesuwa najstarszy nadmiarowy wpis na początek `page2.html` itd.
6. Pliki paginacyjne wykraczające poza nowy zakres (jeśli liczba stron się zmniejszyła) są usuwane.

Strona `spis.html` nadal zawiera kompletny spis treści (wszystkie artykuły). Regenerowana przy każdej publikacji.

Parametry sterujące:
| Zmienna | Znaczenie |
|---------|-----------|
| `MAX_CARDS` | Liczba wpisów na stronę (ustawiono na 21) |
| `PAGINATION_ENABLED` | Flaga włączenia paginacji (True) |

Wyłączanie paginacji (gdyby było potrzebne): ustaw `PAGINATION_ENABLED = False` – wtedy index znów pokazuje pełną listę, a `page*.html` zostaną usunięte przy kolejnym przebiegu.

## Sitemap (`sitemap.xml`)
Sitemap jest automatycznie regenerowany przy każdym dodaniu wpisu oraz podczas pełnej odbudowy (`REBUILD_ALL_PAGES=1`). Zawiera:

1. Stronę główną (`/`) – priority 1.00
2. `spis.html` (jeśli istnieje) – priority 0.80
3. Wszystkie wpisy z `pages/*.html` – priority 0.55

Źródło daty (`<lastmod>`):
1. `datePublished` w treści wpisu (JSON-LD / meta / znacznik `<time>`)
2. Sufiks w nazwie pliku `-YYYYMMDD`
3. Mtime pliku (ostatnia modyfikacja) – fallback

Sitemap jest minimalna (bez `<changefreq>` i `<image:image>`). Rozszerzenia możliwe w przyszłości.



## Krok 8: Selektywna obsługa Git (nowe + zmienione rozmiarem pliki)
Od tej wersji skrypt nie wykonuje już `git add --all`. Zamiast tego:

1. Pobiera snapshot bieżących plików (ścieżka względna → rozmiar w bajtach).
2. Pobiera z HEAD listę blobów i ich rozmiary.
3. Porównuje – do indeksu trafiają wyłącznie:
   - nowe pliki (nieistniejące wcześniej w commitcie HEAD),
   - pliki, których rozmiar uległ zmianie.
4. Jeżeli nic nie spełnia kryteriów – commit jest pomijany.

Zalety:
- Minimalne commity (mniejszy “szum” historii).
- Unikanie przypadkowego dodania dużych niepotrzebnych artefaktów tymczasowych jeśli nie zmieniły rozmiaru.

Uwagi / ograniczenia:
- Zmiana tylko zawartości o identycznej długości bajtowej nie zostanie wykryta (edge case – rzadki przy HTML). Jeśli potrzebujesz pełnej detekcji treści: można przełączyć się na porównanie hashów (np. SHA-1) – do wdrożenia opcjonalnie.
- Pliki usunięte nie są automatycznie zdejmowane z repo (można dodać krok czyszczący – jeśli potrzebujesz, zgłoś).
- Nie ma obecnie zmiennej środowiskowej do wymuszenia "pełnego" dodania – można łatwo dodać (np. `FULL_GIT_ADD=1`).

Jak przywrócić pełne dodawanie (manualnie):
1. Otwórz `update_blog.py`.
2. W funkcji `git_commit_and_push` zamień pętlę selektywnego dodawania na `repo.git.add(all=True)`.

Przykład komunikatu w logach:
```
[GIT] Wypchnięto 3 plik(ów).
```
Jeśli brak zmian:
```
[GIT] Brak plików spełniających kryterium (nowe lub zmiana rozmiaru).
```

Repo docelowe: `https://github.com/SigPath/trueresults.online` – workflow pushuje tam jak dotychczas (zakładając poprawnie skonfigurowany remote `origin`).

Potencjalne rozszerzenia:
- Dodanie filtra rozszerzeń (np. tylko `.html`, `.xml`, `.txt`).
- Detekcja usuniętych plików (porównanie HEAD vs FS i `git rm`).
- Hashowanie zawartości (dokładniejsze niż porównanie rozmiaru).
- Flaga środowiskowa wymuszająca pełny commit.

## Licencja
Możesz adaptować wedle potrzeb.

---

## Wersja 3.0 – Pełna Integracja Master Promptu

Od wersji 3.0 cała generacja treści przechodzi przez funkcję `generate_full_article_from_master_prompt(topic)`, która:

1. Wewnątrz ładuje `MASTER_PROMPT` + (opcjonalne) `case_study.txt` poprzez `load_master_prompt()`.
2. Buduje złożony prompt: kontekst + AKTUALNY TEMAT + instrukcje struktury (9 sekcji h2, akapity p).
3. Wysyła zapytanie do Gemini (model z `GEMINI_MODEL_ARTICLE`).
4. Wypisuje w konsoli znacznik: `Wysyłanie zapytania do Gemini z pełnym kontekstem...`.
5. W razie limitu / błędu API – fallback do skróconej wersji sekcyjnej.

Konfiguracja:
| Zmienna | Znaczenie |
|---------|-----------|
| `USE_MASTER_PROMPT=1` | Aktywuje pełny prompt kontekstowy |
| `ART_MIN_WORDS` / `ART_MAX_WORDS` | Deklarowany zakres długości artykułu |
| `GEMINI_MODEL_ARTICLE` | Model do artykułów (domyśl.: gemini-1.5-flash-latest) |

Pliki:
- `prompts/master_prompt.py` – definicja `MASTER_PROMPT`.
- `prompts/case_study.txt` – wstrzykiwany tekst studium (opcjonalny, placeholder gdy pusty).

Tryb fallback oznaczony jest w logu i w polu `mode` (wartość `fallback`).

Jeśli chcesz wymusić tylko fallback (bez kontekstu) tymczasowo:
```bash
export USE_MASTER_PROMPT=0
python3 update_blog.py
```

Powrót:
```bash
export USE_MASTER_PROMPT=1
```


## Jednoprzyciskowy wrapper uruchomieniowy

Dodano skrypt `run_autoblog.py` oraz prosty wrapper Bash `run_autoblog.sh` aby uprościć lokalne wielokrotne generowanie:

Przykłady:
```bash
python3 run_autoblog.py        # 1 wpis
python3 run_autoblog.py 5      # 5 wpisów (kolejno)
./run_autoblog.sh 3            # wrapper shell (macOS/Linux)
```

Zmienne opcjonalne:
| Zmienna | Opis | Domyślna |
|---------|------|----------|
| `DELAY_SECONDS` | Odstęp (sekundy) między wpisami przy count>1 | 2 |
| `GIT_PUSH` | Ustaw 0 aby nie pushować (tylko lokalny commit) | 1 |
| `GIT_COMMIT_PREFIX` | Prefiks wiadomości commita | `[auto]` |
| `MASS_REGENERATE` | Jeśli ustawiona -> wrapper deleguje do trybu masowego w `update_blog.py` | — |

Jeśli chcesz uniknąć limitów API – zwiększ `DELAY_SECONDS`.

Przykład z opóźnieniem i bez push:
```bash
export DELAY_SECONDS=5
export GIT_PUSH=0
python3 run_autoblog.py 3
```

Powrót do normalnego działania:
```bash
unset GIT_PUSH DELAY_SECONDS
python3 run_autoblog.py
```
