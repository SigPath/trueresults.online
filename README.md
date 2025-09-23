# Projekt "Niekończące się Lustro" – Wersja 4.0 (Niezawodność + Czystość Kodu)

> Wersja 3.0 wprowadziła pełną integrację Master Promptu. Wersja 4.0 koncentruje się na odporności (retry przy błędach API), redukcji długu technicznego (usunięcie legacy funkcji) oraz lepszej obserwowalności (metryka liczby słów w logu).

---

## 🧭 Roadmap / Historia Ewolucji
| Wersja | Zakres | Kluczowe Zmiany |
|--------|--------|-----------------|
| 1.x | Inicjalna automatyzacja | Prosty generator + zapis HTML + push |
| 2.x | Kampanie tematyczne | Rotacja kategorii (dzień roku), unikalność tematów, limit kart 21 |
| 3.x | Master Prompt | Centralizacja generacji (1 funkcja), struktura 9 sekcji, fallback kontrolowany, log trybu (master/fallback) |
| 4.0 | Niezawodność + Cleanup | Retry (1 powtórka po błędzie), usunięcie `fetch_ai_article`, metryka SŁOWA=, klarowny README + instrukcje dla Copilota |

---

## 🎯 Cel Wersji 4.0
1. Zminimalizować ryzyko utraty publikacji przez chwilowe błędy API (limit 429 lub przejściowa niestabilność).
2. Usunąć martwy kod (`fetch_ai_article`) aby uprościć mentalny model i uniknąć divergence.
3. Dodać metrykę liczby słów do logu aby monitorować potencjalne skrócenia odpowiedzi modelu.
4. Zachować w 100% zgodność istniejących struktur wyjściowych (brak zmian w HTML pliku wpisu, brak zmian w strukturze dict zwracanej przez generator).

---

## ✅ Ostateczna Lista Zadań (TODO – Wdrożenie 4.0)
- [ ] 1. Retry w `generate_full_article_from_master_prompt` (maks. 2 próby: pierwsza + jedna powtórka po 20 s)
- [ ] 2. Usunięcie definicji `fetch_ai_article` (legacy, deprecated)
- [ ] 3. Dodanie metryki liczby słów (`SŁOWA=<int>`) do `logs/last_run.txt`
- [ ] 4. Test lokalny (scenariusz sukces + ewentualna symulacja wyjątku)
- [ ] 5. Commit + push (wiadomość prefiks: `[auto] v4.0` lub zgodny z istniejącym wzorcem)

Opcjonalne dalsze rozszerzenia (nie w scope 4.0, ale możliwe bez kolizji):
- (A) Automatyczny backoff wykładniczy dla >1 powtórki (obecnie trzymamy prostotę)
- (B) Flaga środowiskowa `RETRY_DELAY_SECONDS` (domyślnie 20)
- (C) Oznaczanie trybu i word_count w JSON-LD (pole niestandardowe `articleBodyWordCount`)
- (D) Telemetria do osobnego pliku CSV (`logs/metrics.csv`)

---

## � Instrukcje dla GitHub Copilot / Wstawiane Komentarze w `update_blog.py`
Poniższe bloki komentarzy (KROK 1–3) służą jako sterujące instrukcje dla Copilota – po wklejeniu nadpisują istniejący kod lub sekcje.

### (KROK 1) – Retry (ZASTĄP treść funkcji `generate_full_article_from_master_prompt`)
```python
# === KROK 1: Implementacja mechanizmu RETRY w głównej funkcji generującej ===
# TODO Copilot: Przepisz poniższą funkcję `generate_full_article_from_master_prompt`, dodając do niej mechanizm ponawiania.
# Wymagania:
# 1. Maksymalnie 2 próby (pierwsza + jedna powtórka) – pętla for lub while.
# 2. Retry tylko jeśli poprzednia próba zakończyła się wyjątkiem.
# 3. Obsłuż wyjątek ogólny `Exception as e` – jeśli to nie ostatnia próba: print("Błąd API, ponawiam próbę za 20 sekund...", e)
# 4. time.sleep(20) przed drugą próbą (dodaj `import time` na górze pliku jeśli brak).
# 5. Log zachowujemy: "Wysyłanie zapytania do Gemini z pełnym kontekstem..." TYLKO przed realnym requestem.
# 6. Przy sukcesie: przerwij pętlę i kontynuuj dalszą część funkcji bez zmian logicznych.
# 7. Jeśli obie próby zawiodą: przełącz na fallback (tak jak obecnie) – NIE przerywaj całego procesu.
# 8. Reszta pipeline (meta description, ensure_unique_title, FAQ) – bez zmian.
# 9. Nie duplikuj kodu fallback – wykorzystaj istniejącą gałąź.
def generate_full_article_from_master_prompt(topic: str) -> dict:
	# ... (aktualna treść funkcji do refaktoryzacji z dodanym mechanizmem retry) ...
```

### (KROK 2) – Usunięcie funkcji legacy (ZASTĄP definicję `fetch_ai_article` komentarzem)
```python
# === KROK 2: Usunięcie zbędnego kodu (Code Cleanup) ===
# TODO Copilot: Usuń całkowicie funkcję `fetch_ai_article` (deprecated). Nie pozostawiaj pustego bloku.
# Upewnij się, że w kodzie nie ma żadnych wywołań do niej – w wersji 3.x create_post używa tylko generate_full_article_from_master_prompt.
```

### (KROK 3) – Metryka liczby słów (MODYFIKUJ blok finally w main())
```python
# === KROK 3: Rozszerzenie logowania o liczbę słów ===
# TODO Copilot: W bloku `finally` funkcji main():
# 1. Pobierz HTML z data.get('html_content','').
# 2. Użyj istniejącej funkcji extract_plain(html) lub prostego regexu – preferuj extract_plain.
# 3. word_count = len(plain.split()) jeśli plain != ''.
# 4. Dodaj na końcu log_entry: ` | SŁOWA={word_count}`.
# 5. Zachowaj dotychczasowe pola i strukturę.
```

---

## 🔍 Kryteria Akceptacji (Definition of Done)
| ID | Kryterium | Spełnienie |
|----|-----------|------------|
| 1 | Dwukrotna próba requestu (1 retry) | Request ponawiany po 20 s tylko po błędzie | 
| 2 | Usunięcie `fetch_ai_article` | Brak definicji i brak referencji | 
| 3 | Log ma suffix `| SŁOWA=NNN` | Widoczny w `logs/last_run.txt` | 
| 4 | Brak regresji publikacji | Nowy wpis generuje się poprawnie (fallback lub master) | 
| 5 | Brak nowych ostrzeżeń błędów lintera/importów | Pylance / runtime OK | 

---

## 🧪 Test Plan (Manualny Minimalny)
1. Normalny bieg (z poprawnym kluczem) – sprawdź log trybu = master, obecność SŁOWA.
2. Symulacja błędu: tymczasowo wymuś wyjątek (np. ustaw GEMINI_API_KEY na nieprawidłowy) → powinna zajść ścieżka fallback + SŁOWA.
3. Sprawdź czy brak definicji `fetch_ai_article` nie powoduje NameError (brak wywołań).
4. Powtórne uruchomienie – log dokleja nową linię (idempotencja struktury).

---

## 🗂 Struktura Repo (skrót)
```
index.html
spis.html
pages/*.html
update_blog.py
prompts/master_prompt.py
prompts/case_study.txt
run_autoblog.py / run_autoblog.sh
logs/last_run.txt
```

---

## 🔐 Bezpieczeństwo (unchanged)
- `.env` ignorowany – klucz w `GEMINI_API_KEY`.
- Brak logowania surowych odpowiedzi modelu.
- Fallback deterministyczny zapewnia ciągłość publikacji.

---

## ⚙️ Najważniejsze Zmienne Środowiskowe (Aktualne)
| Zmienna | Opis | Domyślna |
|---------|------|----------|
| GEMINI_API_KEY | Klucz do API Gemini | (brak) |
| USE_MASTER_PROMPT | Włącza master prompt | 1 / 0 |
| ART_MIN_WORDS / ART_MAX_WORDS | Docelowy zakres długości | 650 / 900 |
| GIT_COMMIT_PREFIX | Prefiks commitów | [auto] |
| GIT_PUSH | Czy wypychać na origin | 1 |

---

## 🧱 Kluczowe Funkcje (po 4.0)
| Funkcja | Rola |
|---------|------|
| load_master_prompt | Ładuje złożony kontekst master promptu |
| generate_full_article_from_master_prompt | Jedyna ścieżka generacji treści (retry + fallback) |
| pick_topic | Globalnie unikatowy wybór tematu w ramach kampanii |
| build_post_html | Budowa finalnego HTML wpisu ze szablonu |
| insert_card_in_index | Wstawienie karty + przycinanie do 21 wpisów |
| generate_rss_feed / generate_sitemap | Indeksacja / syndykacja |
| git_commit_and_push | Commit + push (deterministyczny) |

---

## � Obserwowalność
Log `logs/last_run.txt` po wdrożeniu 4.0 (przykład):
```
DATA=2025-09-23T12:34:56.123456 | KAMPANIA=Psychologia Sprawcy | TRYB=master | TEMAT=... | SLUG=... | TYTUL=... | SŁOWA=842
```

---

## ▶️ Następny Krok
1. Zastosować trzy bloki KROK 1–3 w `update_blog.py`.
2. Uruchomić lokalnie: `python update_blog.py`.
3. Zweryfikować log + push.
4. Oznaczyć release (tag v4.0) – opcjonalnie.

---

## 🧾 Licencja
Otwarty do adaptacji. Atrybucja mile widziana – nie wymagana.

---

## ✔️ Checklist po Merge (Developer)
- [ ] Retry działa (przetestowano sztucznie wymuszoną awarię)
- [ ] Fallback nienaruszony
- [ ] `fetch_ai_article` usunięty
- [ ] Log zawiera SŁOWA
- [ ] Brak regresji w generacji RSS / sitemap / spis
- [ ] Commit oznaczony prefiksem

---

Jeśli potrzebujesz kolejnych funkcji (embeddings, analityka semantyczna, warstwa API) – opisz cel biznesowy; zaproponuję iterację 5.0.
