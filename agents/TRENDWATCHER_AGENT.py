import requests
from datetime import datetime
import json

class TrendWatcherAgent:
    """
    TrendWatcher Agent — skanuje zewnętrzne źródła (np. Hacker News)
    w poszukiwaniu gorących tematów i trendów, które mogą stać się nowymi niszami.
    """
    def __init__(self, state):
        self.state = state
        self.hn_api_top_stories = "https://hacker-news.firebaseio.com/v0/topstories.json"
        self.hn_api_item = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
        self.trends_output_file = "data/trends.json"
        self.min_score = 50  # Ignoruj historie z mniejszą liczbą punktów

    def run(self, state):
        """Pobiera i analizuje najpopularniejsze historie z Hacker News."""
        print(f"[{datetime.now().isoformat()}] TRENDWATCHER AGENT: Skanuję Hacker News w poszukiwaniu trendów...")
        
        try:
            # Pobierz ID najpopularniejszych historii
            response = requests.get(self.hn_api_top_stories, timeout=10)
            response.raise_for_status()
            top_ids = response.json()

            hot_trends = []
            # Przeanalizuj pierwsze 20 historii
            for story_id in top_ids[:20]:
                item_response = requests.get(self.hn_api_item.format(id=story_id), timeout=5)
                story_data = item_response.json()
                
                if story_data and story_data.get('score', 0) > self.min_score:
                    title = story_data.get('title')
                    if title:
                        hot_trends.append(title)
            
            if not hot_trends:
                print("[TRENDWATCHER AGENT] Nie znaleziono żadnych istotnych trendów w tym cyklu.")
                return state

            # Zapisz znalezione trendy do pliku
            with open(self.trends_output_file, 'w', encoding='utf-8') as f:
                json.dump(hot_trends, f, indent=2)

            print(f"[TRENDWATCHER AGENT] Zidentyfikowano i zapisano {len(hot_trends)} gorących trendów.")

        except requests.RequestException as e:
            print(f"[TRENDWATCHER AGENT] Błąd podczas łączenia z API Hacker News: {e}")
            
        return state
