# Projekt „Niekończące się Lustro” (True Results Online) – Wersja 2.0

System automatycznego, analitycznego bloga psychologicznego z dzienną publikacją poprzez GitHub Actions oraz DZIENNĄ rotacją Kampanii Tematycznych.

---

## 🎯 Cel Projektu
Stworzenie regularnie aktualizowanego repozytorium obserwacyjno-analitycznego dynamik relacyjnych i poznawczych. Każdy wpis stanowi modułowy artefakt: spójny język, stały format, ograniczona długość (≈250–300 słów), klarowna struktura akapitów oraz nacisk na mikro‑mechanizmy psychologiczne. Wersja 2.0 dodaje logikę rotacyjnych „kampanii” – zamiast chaotycznej losowości, tematy układają się w tygodniowe skupienia poznawcze.

---

## 🧠 Kampanie Tematyczne (Core Upgrade)
Mechanizm „Kampanii” zapewnia, że KAŻDEGO DNIA wybierana jest inna kategoria semantyczna (mapowanie: dzień roku 1–366 modulo liczba kategorii). Eliminuje to tygodniową monotonię i zwiększa percepcyjną różnorodność.

### Zalety tej architektury
- Spójność percepcyjna: czytelnik odbiera serię jako logiczny blok.
- Lepsze nasycenie słów kluczowych (SEO tematyczne).
- Umożliwia późniejsze generowanie raportów „kampania → agregat wniosków”.
- Minimalny narzut – algorytm selekcji kontroluje wyłącznie warstwę wyboru tematu.

### Jak to działa pod spodem
1. Zdefiniowany słownik `CAMPAIGN_TOPICS`: klucz = kategoria, wartość = lista tematów.
2. Funkcja `get_current_campaign()` pobiera numer dnia roku (`date.strftime('%j')`) i wykonuje modulo po liczbie kategorii.
3. Funkcja `pick_topic()` filtruje wykorzystane tematy danej kategorii (format zapisów: `KATEGORIA|TEMAT` w `used_topics.txt`).
4. Gdy wszystkie tematy w kategorii zostały zużyte – reset następuje tylko dla tej kategorii (inne kategorie zachowują historię zużycia).
5. Można wymusić kampanię: `FORCE_CAMPAIGN="Mechanizmy Obronne i Taktyki Manipulacji"`.
6. (Wyłączono) Dawny baner informacyjny kampanii na stronie głównej – usunięty na życzenie (możliwy powrót przez odkomentowanie kodu).

---

## 🗂 Struktura Repozytorium (Kluczowe Elementy)
```
index.html           # Strona główna – 21 najnowszych wpisów (paginacja włączona)
spis.html            # Generowany pełny spis treści
pages/*.html         # Wygenerowane wpisy (slug + data)
update_blog.py       # Główny skrypt automatyzacji
prompts/master_prompt.py  # (Opcjonalny) bazowy mega‑prompt
prompts/case_study.txt    # Studium przypadku wstrzykiwane do master promptu
feed.xml             # RSS 2.0 (ostatnie wpisy)
sitemap.xml          # Mapa strony dla indeksacji
logs/last_run.txt    # Logi operacyjne (tryb, kampania, temat, slug, błędy)
README_AUTOBLOG.md   # Dokumentacja operacyjno‑techniczna
README.md            # Ten plik – warstwa koncepcyjno‑architektoniczna
```

---

## 🔄 Przepływ Dzienny (Pipeline)
1. GitHub Actions uruchamia `update_blog.py`.
2. `get_current_campaign()` → wybór kategorii.
3. `pick_topic()` → losowy temat z dostępnej puli kampanii.
4. `fetch_ai_article()` / `generate_article()` (Gemini Flash 1.5) → surowa treść.
5. Sanitizacja, ograniczenie słów, zachowanie <p> i <strong>.
6. Render szablonu (`szablon_wpisu.html`) → zapis do `pages/`.
7. Aktualizacja `index.html` (prepend karty, utrzymanie limitu 21) + opcjonalny baner.
8. Regeneracja: paginacja (`page2.html`+), RSS, sitemap, spis (`spis.html`).
9. Selektywny commit (tylko nowe / zmienione rozmiarem pliki) → push.
10. Log zapisuje: DATA | KAMPANIA | TRYB | TEMAT | SLUG | TYTUL.

---

## 🧩 Kontrakt Treści (Specyfikacja Wpisu)
- Długość docelowa: 250–300 słów (twarde przycięcie > limitu).
- Struktura: 5 akapitów w tagach `<p>` (definicja / mechanizm / dynamika / interwencje / synteza).
- Styl: analityczny, bez „waty”, brak list, brak nagłówków wewnętrznych.
- Wyróżnienia: kluczowe frazy w `<strong>` (model instruowany w promptach).
- Meta: opis ≈ 155 znaków (SEO snippet), kanoniczny URL, datePublished.

---

## 🔐 Bezpieczeństwo i Sekrety
- Klucz Gemini: `GEMINI_API_KEY` w `.env` lokalnie / jako GitHub Secret w Actions.
- `.env` jest ignorowany (`.gitignore`).
- Brak zapisu sekretów w logach.
- Fallback treści jeśli brak klucza – deterministyczne akapity.

---

## ⚙️ Zmienne Środowiskowe (Wybrane)
| Zmienna | Opis |
|---------|------|
| `GEMINI_API_KEY` | Klucz do API Gemini |
| `GEMINI_MODEL` | Model podstawowy (domyślnie `gemini-1.5-flash`) |
| `USE_MASTER_PROMPT=1` | Włącza scalanie `master_prompt.py` + `case_study.txt` |
| `FORCE_CAMPAIGN` | Wymusza konkretną kampanię (nazwa klucza) |
| `SHOW_CAMPAIGN_BANNER=1` | Wyświetla baner aktualnej kampanii w `index.html` |
| `REBUILD_ALL_PAGES=1` | Rekonstrukcja listy kart z istniejących plików |
| (kod) `PAGINATION_ENABLED` | Globalne włączenie/wyłączenie paginacji (obecnie: True) |
| (kod) `MAX_CARDS` | Liczba wpisów na stronę (21) |

---

## 🧪 Testowanie Lokalnie
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
GEMINI_API_KEY=TWÓJ_KLUCZ python update_blog.py
```
Wymuszenie kampanii + banera (np. dla demo):
```
FORCE_CAMPAIGN="Mechanizmy Obronne i Taktyki Manipulacji" SHOW_CAMPAIGN_BANNER=1 python update_blog.py
```
Pełna odbudowa kart (bez tworzenia nowego wpisu):
```
REBUILD_ALL_PAGES=1 python update_blog.py
```

---

## 📁 Plik `used_topics.txt`
Format linii: `KATEGORIA|TEMAT`. Reset następuje selektywnie – tylko gdy dana kategoria wyczerpie swoją pulę.

Przykład fragmentu:
```
Psychologia Sprawcy|Lęk przed Samotnością jako Główny Motor Destrukcyjnych Działań
Psychologia Sprawcy|Rola Peruki i Fałszywych Tożsamości w Kontekście Niestabilnego Poczucia Własnej Wartości
```

---

## 📡 Generowane Artefakty
- `feed.xml` – RSS (ostatnie ~30 wpisów)
- `sitemap.xml` – sitemap (root, spis, wpisy)
- `spis.html` – kompletny indeks wpisów
- Log wejściowy (meta) – audyt przebiegu

---

## 🧱 Architektura Kodowa (Wybrane Funkcje)
| Funkcja | Rola |
|---------|------|
| `get_current_campaign()` | Wyznacza aktywną kampanię na podstawie tygodnia lub wymuszenia |
| `pick_topic()` | Losuje temat w ramach kampanii, zapisuje zużycie |
| `generate_article()` | Orkiestruje prompt + model + sanitizację |
| `insert_card_in_index()` | Wstrzyknięcie karty wpisu + opcjonalny baner |
| `generate_rss_feed()` | Budowa RSS 2.0 |
| `generate_sitemap()` | Budowa sitemap.xml |
| `generate_full_spis()` | Regeneracja pełnego spisu treści |
| `git_commit_and_push()` | Selektywny commit (nowe / zmienione rozmiarem) |

---

## 🚀 Możliwe Kierunki 3.0
- Agregaty kampanii (strony syntetyzujące tydzień).
- Metadane JSON dla analizy temporalnej.
- Eksport do wektorowego indeksu (embeddingi) dla semantycznego wyszukiwania.
- Filtry UI (kampania / zakres dat / tag logiczny).
- Wczesne alerty duplikacji semantycznej (embedding similarity > threshold).

---

## 🧾 Licencja
Otwarte do adaptacji. Atrybucja mile widziana, niewymagana.

---

## 📌 Szybki Checklist Developer’a
- [x] Kampanie rotacyjne działają
- [x] Selektywny log per wpis
- [x] Reset per kategoria (nie globalny)
- [x] Brak obrazów (świadoma decyzja UX)
- [x] Paginacja (21 / strona) aktywna
- [x] Spis i sitemap zawsze regenerowane

Jeśli potrzebujesz rozszerzyć funkcjonalność – opisz intencję (semantyka / warstwa prezentacji / analityka), a dopasuję kolejne iteracje.
