

import random
from datetime import datetime
import json
import os
import re

class InnovationAgent:
    """
    Innovation Agent — w trybie produkcyjnym czerpie z trendów, a w trybie
    kreatywnym przekształca surową inspirację w konkretny pomysł na projekt.
    """
    def __init__(self, state):
        self.state = state
        self.trends_input_file = "data/trends.json"
        self.inspirations_input_file = "data/inspirations.json"

    def _slugify_trend(self, trend_title):
        slug = trend_title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug[:50]

    def run(self, state):
        current_mode = state.get('current_mode', 'PRODUCTION')
        print(f"[{datetime.now().isoformat()}] INNOVATION AGENT: Rozpoczynam burzę mózgów w trybie: {current_mode}")

        if current_mode == 'CREATIVE':
            if not os.path.exists(self.inspirations_input_file):
                print("[INNOVATION AGENT] Brak pliku inspiracji. Czekam na pracę InspirationAgent.")
                return state
            with open(self.inspirations_input_file, 'r', encoding='utf-8') as f:
                inspiration = json.load(f)
            print(f"[INNOVATION AGENT] Przetwarzam inspirację: '{inspiration['title']}'")
            state['current_inspiration'] = inspiration
        else:
            if not os.path.exists(self.trends_input_file):
                print("[INNOVATION AGENT] Brak pliku trendów. Czekam na pracę TrendWatcherAgent.")
                return state
            with open(self.trends_input_file, 'r', encoding='utf-8') as f:
                idea_pool = json.load(f)
            raw_idea = random.choice(idea_pool)
            new_niche_idea = self._slugify_trend(raw_idea)
            current_niches = state.get('potential_niches', [])
            if new_niche_idea not in current_niches:
                if 'innovation_ideas' not in state: state['innovation_ideas'] = []
                state['innovation_ideas'].append({
                    'type': 'new_niche', 'value': new_niche_idea, 'source': 'trends'
                })
                print(f"[INNOVATION AGENT] Nowy pomysł z trendów: '{new_niche_idea}'")
        return state
