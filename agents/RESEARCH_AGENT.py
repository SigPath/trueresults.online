from googlesearch import search
from datetime import datetime
import json
import os

class ResearchAgent:
    """Research Agent — analizuje trendy i produkty"""
    def __init__(self, state):
        self.state = state
        self.opportunities_file = "data/opportunities.json"

    def _find_affiliate_programs(self, niche, num_results=10):
        query = f'"{niche.replace("-", " ")}" affiliate program'
        print(f"[RESEARCH AGENT] Wyszukuję programy partnerskie dla zapytania: '{query}'")
        try:
            urls = list(search(query, num_results=num_results, lang="pl", sleep_interval=2))
            affiliate_urls = [url for url in urls if 'affiliate' in url or 'partner' in url or 'referral' in url]
            return affiliate_urls
        except Exception as e:
            print(f"[RESEARCH AGENT] Błąd podczas wyszukiwania programów partnerskich: {e}")
            return []

    def run(self, state):
        niche = state.get('ceo_decision', {}).get('chosen_niche')
        if not niche:
            print("[RESEARCH AGENT] Brak wybranej niszy. Pomijam poszukiwania.")
            return state

        print(f"[{datetime.now().isoformat()}] RESEARCH AGENT: Badam potencjał monetyzacyjny niszy: '{niche}'")
        found_programs = self._find_affiliate_programs(niche)

        if not found_programs:
            print(f"[RESEARCH AGENT] Nie znaleziono żadnych programów partnerskich dla niszy '{niche}'.")
            return state

        if os.path.exists(self.opportunities_file):
            with open(self.opportunities_file, 'r', encoding='utf-8') as f:
                opportunities = json.load(f)
        else:
            opportunities = {}

        opportunities[niche] = found_programs

        with open(self.opportunities_file, 'w', encoding='utf-8') as f:
            json.dump(opportunities, f, indent=2)

        print(f"[RESEARCH AGENT] Znaleziono i zapisano {len(found_programs)} potencjalnych programów partnerskich dla niszy '{niche}'.")
        return state

    def run(self, state):
        # TODO: analiza trendów, produktów
        state['research'] = {'niche': 'ai-passive-income'}
        return state
