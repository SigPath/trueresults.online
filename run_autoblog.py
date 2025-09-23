#!/usr/bin/env python3
"""Jednoprzyciskowy wrapper do generowania wpisów i pushowania do GitHub.

Użycie:
  python3 run_autoblog.py              -> 1 wpis
  python3 run_autoblog.py 5            -> 5 wpisów (kolejno, każde wywołanie update_blog.main())
  MASS=10 python3 run_autoblog.py      -> alternatywnie możesz nadal użyć MASS_REGENERATE w .env

Zachowanie:
 - Ładuje zmienne z .env (jeśli istnieje)
 - Dla count>1 uruchamia pętlę i śpi 2 sekundy między wpisami (prosty throttle)
 - Obsługuje błędy pojedynczych iteracji, logując do stderr

Zmienne opcjonalne środowiska:
 - DELAY_SECONDS (domyślnie 2) opóźnienie między wpisami
 - USE_MASTER_PROMPT=1 aby wymusić master prompt (już wspierane w update_blog)

UWAGA: Jeśli chcesz pełną masową regenerację z resetem – nadal użyj MASS_REGENERATE=N w środowisku.
"""
from __future__ import annotations
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv  # type: ignore

# Ścieżka bazowa = katalog tego pliku
BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Import po załadowaniu .env aby konfiguracja była dostępna
import update_blog  # type: ignore  # noqa: E402


def run_single() -> bool:
    try:
        update_blog.main()
        return True
    except SystemExit:
        # propagate system exits, e.g. MASS_REGENERATE errors
        raise
    except Exception as e:  # pragma: no cover
        print(f"[RUN] Błąd generowania wpisu: {e}", file=sys.stderr)
        return False


def main():
    # Jeśli użytkownik ustawi MASS_REGENERATE w środowisku – delegujemy całkowicie do update_blog
    if os.getenv("MASS_REGENERATE"):
        update_blog.main()
        return

    # Liczba wpisów z argumentu CLI
    count = 1
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print("Argument musi być liczbą całkowitą (liczba wpisów).", file=sys.stderr)
            sys.exit(2)
        if count <= 0:
            print("Liczba wpisów musi być > 0", file=sys.stderr)
            sys.exit(2)

    delay = float(os.getenv("DELAY_SECONDS", "2"))
    success = 0
    for i in range(1, count + 1):
        print(f"=== Generowanie wpisu {i}/{count} ===")
        ok = run_single()
        if ok:
            success += 1
        if i != count:
            time.sleep(delay)
    print(f"Zakończono: {success}/{count} wpisów poprawnych.")
    if success != count:
        sys.exit(1)


if __name__ == "__main__":
    main()
