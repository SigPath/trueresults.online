

import random
from datetime import datetime

class CEOAgent:
    """
    CEO Agent — Lider Kreatywnego Studia. Balansuje między trybem produkcyjnym (ROI-driven)
    a trybem kreatywnym (inwestycja w innowacje i "duszę" projektu).
    """
    def __init__(self, state):
        self.state = state
        self.potential_niches = state.get('potential_niches', [
            'ai-tools-for-business', 'sustainable-gadgets', 'home-automation-tips'
        ])
        self.creative_cycle_frequency = 5 # Co 5 cykli jest cyklem kreatywnym

    def run(self, state):
        run_count = state.get('run_count', 0) + 1
        state['run_count'] = run_count

        print(f"[{datetime.now().isoformat()}] CEO AGENT: Rozpoczynam cykl decyzyjny #{run_count}.")

        if run_count % self.creative_cycle_frequency == 0:
            print("[CEO AGENT] >>> Wchodzę w TRYB KREATYWNY. Czas na innowacje! <<<")
            state['current_mode'] = 'CREATIVE'
            new_strategy = {
                'chosen_niche': 'creative-experiment',
                'content_focus': 'experimental',
                'source': 'inspiration_driven',
                'last_update': datetime.now().isoformat()
            }
            state['ceo_decision'] = new_strategy
            print("[CEO AGENT] Decyzja: Zlecam projekt eksperymentalny oparty na inspiracji.")
        else:
            print("[CEO AGENT] Wchodzę w TRYB PRODUKCYJNY. Optymalizuję pod kątem wyników.")
            state['current_mode'] = 'PRODUCTION'
            performance_metrics = state.get('performance_metrics', {})
            best_niche, highest_roi = self._find_best_performer(performance_metrics)
            if best_niche and highest_roi > 0.1:
                print(f"[CEO AGENT] Decyzja (EKSPLOATACJA): Nisza '{best_niche}' ma najwyższe ROI ({highest_roi:.2%}).")
                new_niche = best_niche
            else:
                print(f"[CEO AGENT] Decyzja (EKSPLORACJA): Brak lidera ROI. Testuję nową lub mało zbadaną niszę.")
                new_niche = self._find_least_tested_niche(performance_metrics)
            new_strategy = {
                'chosen_niche': new_niche,
                'content_focus': 'articles',
                'last_update': datetime.now().isoformat()
            }
            state['ceo_decision'] = new_strategy
            print(f"[CEO AGENT] Strategia produkcyjna: Nisza='{new_strategy['chosen_niche']}'")
        state['potential_niches'] = self.potential_niches
        return state

    def _find_best_performer(self, metrics):
        best_niche, highest_roi = None, -float('inf')
        if not metrics: return None, None
        for niche, data in metrics.items():
            if data['roi'] > highest_roi:
                highest_roi = data['roi']
                best_niche = niche
        return best_niche, highest_roi

    def _find_least_tested_niche(self, metrics):
        if not self.potential_niches: return "default-niche"
        tested_counts = {niche: metrics.get(niche, {}).get('content_pieces', 0) for niche in self.potential_niches}
        return min(tested_counts, key=tested_counts.get)
