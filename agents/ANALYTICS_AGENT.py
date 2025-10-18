import os
import requests
from datetime import datetime

class AnalyticsAgent:
    """
    Analytics Agent — pobiera rzeczywiste dane analityczne z zewnętrznych źródeł,
    zastępując symulację twardymi danymi.
    """
    def __init__(self, state):
        self.state = state
        # Wczytaj zmienne środowiskowe - kluczowe dla bezpieczeństwa i konfiguracji
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_name = os.getenv('GITHUB_REPO') # np. "twoja-nazwa/TrueResults-AI"

    def run(self, state):
        """Pobiera dane o ruchu z GitHub API."""
        print(f"[{datetime.now().isoformat()}] ANALYTICS AGENT: Pobieram rzeczywiste dane o ruchu...")
        
        if not self.github_token or not self.repo_name:
            print("[ANALYTICS AGENT] OSTRZEŻENIE: Brak GITHUB_TOKEN lub GITHUB_REPO. Pomijam pobieranie analityk.")
            # Zwracamy zerowe metryki, aby system mógł kontynuować, ale CEO podejmie decyzję o zmianie strategii
            state['analytics_summary'] = {'total_views': 0, 'unique_viewers': 0, 'source': 'fallback'}
            return state

        api_url = f"https://api.github.com/repos/{self.repo_name}/traffic/views"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()  # Rzuć wyjątek dla błędów HTTP (4xx lub 5xx)
            data = response.json()
            
            total_views = data.get('count', 0)
            unique_viewers = data.get('uniques', 0)

            analytics_summary = {
                'total_views': total_views,
                'unique_viewers': unique_viewers,
                'source': 'github_api',
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"[ANALYTICS AGENT] Sukces. Unikalni użytkownicy (ostatnie 14 dni): {unique_viewers}, Wyświetlenia: {total_views}")
            state['analytics_summary'] = analytics_summary

        except requests.exceptions.RequestException as e:
            print(f"[ANALYTICS AGENT] Błąd API: Nie udało się pobrać danych z GitHuba: {e}")
            state['analytics_summary'] = {'total_views': 0, 'unique_viewers': 0, 'source': 'api_error'}

        return state
