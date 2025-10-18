import subprocess
from datetime import datetime

class VCSAgent:
    """
    VCS Agent (Version Control System) — automatyzuje proces kontroli wersji.
    Wykrywa zmiany w repozytorium, tworzy commity i wysyła je na serwer zdalny.
    """
    def __init__(self, state):
        self.state = state

    def _run_command(self, command):
        """Uruchamia komendę w powłoce i zwraca jej wynik."""
        try:
            result = subprocess.run(command, check=True, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.now().isoformat()}] VCS AGENT: Błąd wykonania komendy '{command}': {e.stderr}")
            return None

    def run(self, state):
        """Główna logika agenta: add, commit, push."""
        print(f"[{datetime.now().isoformat()}] VCS AGENT: Sprawdzam status repozytorium...")
        
        # Sprawdź, czy są jakiekolwiek zmiany do zatwierdzenia
        status_output = self._run_command("git status --porcelain")
        if status_output is None:
            print(f"[{datetime.now().isoformat()}] VCS AGENT: Nie udało się sprawdzić statusu. Pomijam cykl.")
            return state
            
        if not status_output:
            print(f"[{datetime.now().isoformat()}] VCS AGENT: Brak zmian do zsynchronizowania.")
            return state

        print(f"[{datetime.now().isoformat()}] VCS AGENT: Wykryto zmiany. Rozpoczynam synchronizację...")

        # Krok 1: Dodaj wszystkie zmiany
        self._run_command("git add .")

        # Krok 2: Stwórz commit z dynamiczną wiadomością
        commit_title = state.get('marketing_summary', {}).get('published_content_title', 'Aktualizacja systemowa')
        commit_message = f'Auto-publish: {commit_title} @ {datetime.now().isoformat()}'
        self._run_command(f'git commit -m "{commit_message}"')

        # Krok 3: Wypchnij zmiany do zdalnego repozytorium
        print(f"[{datetime.now().isoformat()}] VCS AGENT: Wypycham zmiany na serwer zdalny...")
        push_result = self._run_command("git push")
        
        if push_result is not None:
            print(f"[{datetime.now().isoformat()}] VCS AGENT: Synchronizacja zakończona pomyślnie.")
        else:
            print(f"[{datetime.now().isoformat()}] VCS AGENT: Błąd podczas wypychania zmian.")
            # TODO: Zaimplementuj logikę ponawiania lub powiadamiania w przypadku błędu.

        return state
