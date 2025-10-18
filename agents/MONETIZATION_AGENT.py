import random
from datetime import datetime

class MonetizationAgent:
    """
    Monetization Agent — przekształca ruch w przychód.
    Dynamicznie dodaje linki afiliacyjne i CTA do wygenerowanych treści.
    """
    def __init__(self, state):
        self.state = state
        # TODO: Ta baza danych powinna być dynamicznie budowana przez Research Agenta
        self.affiliate_products = {
            'ai-tools-for-business': {
                'name': 'SuperAI Writer',
                'link': 'https://superai.example.com/aff/trueresults',
                'cta': 'Chcesz zautomatyzować swój marketing? Sprawdź SuperAI Writer - narzędzie, które pisze teksty za Ciebie!'
            },
            'sustainable-gadgets': {
                'name': 'EcoCharge Pro',
                'link': 'https://ecocharge.example.com/partner/trueresults',
                'cta': 'Szukasz ładowarki słonecznej, która naprawdę działa? Polecamy EcoCharge Pro!'
            }
        }

    def run(self, state):
        """Wzbogaca treść o elementy monetyzacyjne."""
        content_task = state.get('content_generation_task', {})
        # NOWA BRAMKA KONTROLI JAKOŚCI
        if not content_task or content_task.get('status') != 'approved_for_publication':
            return state
        # Dodatkowy warunek: nie monetyzuj treści kreatywnych
        if content_task.get('mode') == 'CREATIVE':
            print("[MONETIZATION AGENT] Pomijam monetyzację dla treści kreatywnej.")
            return state

        print(f"[{datetime.now().isoformat()}] MONETIZATION AGENT: Rozpoczynam monetyzację treści...")
        niche = state.get('ceo_decision', {}).get('chosen_niche')
        product = self.affiliate_products.get(niche)

        if not product:
            print(f"[MONETIZATION AGENT] Brak produktu afiliacyjnego dla niszy '{niche}'. Pomijam.")
            return state

        try:
            filepath = content_task['output_file']
            with open(filepath, 'r+', encoding='utf-8') as f:
                content = f.read()
                # Dodaj sekcję z poleceniem na końcu artykułu
                monetization_block = f"""
---

### Polecany Produkt: {product['name']}

{product['cta']}

**[Kliknij tutaj, aby dowiedzieć się więcej!]({product['link']})**
"""
                f.seek(0, 2) # Przejdź na koniec pliku
                f.write(monetization_block)
            
            print(f"[MONETIZATION AGENT] Pomyślnie dodano link afiliacyjny do '{product['name']}' w pliku {filepath}")

        except Exception as e:
            print(f"[MONETIZATION AGENT] Błąd podczas dodawania linku afiliacyjnego: {e}")
            
        return state
