#!/bin/bash
# Prosty wrapper shell – wywołuje skrypt Pythona
# Użycie: ./run_autoblog.sh [liczba]
set -euo pipefail
COUNT=${1:-1}
python3 run_autoblog.py "$COUNT"
