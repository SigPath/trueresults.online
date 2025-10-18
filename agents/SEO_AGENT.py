from googlesearch import search
from datetime import datetime
import time

class SEOAgent:
    """
    SEO Agent — przeprowadza analizę słów kluczowych i konkurencji,
    tworząc brief SEO dla Content Agenta w celu maksymalizacji ruchu organicznego.
    """
    def __init__(self, state):
        self.state = state

    def _get_competitor_titles(self, query, num_results=5):
        """Pobiera tytuły top 5 wyników z wyszukiwarki Google."""
        print(f"[SEO AGENT] Analizuję konkurencję dla zapytania: '{query}'")
        try:
            results = list(search(query, num_results=num_results, lang="pl", sleep_interval=2))
            return results
        except Exception as e:
            print(f"[SEO AGENT] Błąd podczas wyszukiwania w Google: {e}. Używam pustej listy.")
            return []
            
    def _generate_lsi_keywords(self, niche):
        base = niche.replace('-', ' ')
        return [
            f"{base} poradnik",
            f"najlepsze {base}",
            f"{base} 2024",
            f"jak zacząć z {base}",
            f"{base} dla początkujących"
        ]

    def _get_user_questions(self, niche):
        base = niche.replace('-', ' ')
        return [
            f"Czym jest {base}?",
            f"Ile można zarobić na {base}?",
            f"Czy {base} jest trudne?",
            f"Jakie są najlepsze narzędzia do {base}?"
        ]

    def run(self, state):
        niche = state.get('ceo_decision', {}).get('chosen_niche')
        if not niche:
            print("[SEO AGENT] Brak wybranej niszy. Pomijam analizę SEO.")
            return state

        print(f"[{datetime.now().isoformat()}] SEO AGENT: Tworzę brief SEO dla niszy: '{niche}'")
        
        competitor_urls = self._get_competitor_titles(niche.replace('-', ' '))
        keywords = self._generate_lsi_keywords(niche)
        questions = self._get_user_questions(niche)

        seo_brief = {
            'target_niche': niche,
            'lsi_keywords': keywords,
            'user_questions': questions,
            'competitor_urls': competitor_urls
        }
        
        state['seo_brief'] = seo_brief
        print(f"[SEO AGENT] Brief SEO został wygenerowany. Znaleziono {len(competitor_urls)} konkurentów.")
        
        return state
