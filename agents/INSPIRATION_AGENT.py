import os
import requests
import json
import random
import requests
import json
import random
from datetime import datetime

class InspirationAgent:
    """
    Inspiration Agent — Muza systemu. Przegląda zbiory sztuki, korzystając
    z otwartego API Rijksmuseum, aby dostarczyć kreatywnych bodźców.
    """
    def __init__(self, state):
        self.state = state
        self.api_url = "https://data.rijksmuseum.nl/search/collection"
        self.inspirations_file = "data/inspirations.json"
        self.search_terms = ['painting', 'night', 'sea', 'portrait', 'landscape', 'love', 'war']

    def run(self, state):
        """Działa tylko w trybie kreatywnym, szukając inspiracji."""
        if state.get('current_mode') != 'CREATIVE':
            return state

        print(f"[{datetime.now().isoformat()}] INSPIRATION AGENT: Szukam inspiracji w otwartych zbiorach Rijksmuseum...")
        
        try:
            params = {
                'q': random.choice(self.search_terms),
                'format': 'json',
                'ps': 50,
                'imgonly': 'True'
            }
            response = requests.get(self.api_url, params=params, timeout=15)
            response.raise_for_status()
            artworks = response.json().get('items', [])
            if not artworks:
                print("[INSPIRATION AGENT] Nie udało się znaleźć żadnych dzieł sztuki dla danego zapytania.")
                return state
            chosen_art = random.choice(artworks)
            inspiration = {
                'source': 'Rijksmuseum LOD API',
                'type': 'visual_art',
                'title': chosen_art.get('title', 'Untitled'),
                'artist': chosen_art.get('creator', 'Unknown Artist'),
                'image_url': chosen_art.get('image_url', ''),
                'timestamp': datetime.now().isoformat()
            }
            with open(self.inspirations_file, 'w', encoding='utf-8') as f:
                json.dump(inspiration, f, indent=2)
            print(f"[INSPIRATION AGENT] Znaleziono inspirację: '{inspiration['title']}' autorstwa {inspiration['artist']}.")
        except requests.RequestException as e:
            print(f"[INSPIRATION AGENT] Błąd API podczas szukania inspiracji: {e}")
        return state
        return state
