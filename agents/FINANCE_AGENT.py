
import csv
from datetime import datetime
import os
import random

class FinanceAgent:
    """
    Finance Agent — analityk biznesowy systemu. Śledzi historyczną wydajność
    każdej strategii, oblicza ROI i dostarcza dane dla strategicznych decyzji CEO.
    """
    def __init__(self, state):
        self.state = state
        # Każda wyprodukowana treść to "inwestycja" o stałym koszcie
        self.COST_PER_CONTENT_PIECE = 10.0

    def run(self, state):
        """Aktualizuje metryki wydajności i oblicza ROI dla bieżącej strategii."""
        print(f"[{datetime.now().isoformat()}] FINANCE AGENT: Analizuję zwrot z inwestycji...")

        # Inicjalizuj słownik wydajności, jeśli nie istnieje
        if 'performance_metrics' not in state:
            state['performance_metrics'] = {}

        # Pobierz RZECZYWISTE dane od Agenta Analitycznego
        analytics_summary = state.get('analytics_summary', {})
        unique_viewers = analytics_summary.get('unique_viewers', 0)
        
        # Prosty model monetyzacji oparty na realnym ruchu
        revenue = unique_viewers * 0.1
        profit = round(max(0, revenue - self.COST_PER_CONTENT_PIECE), 2)

        # Zidentyfikuj, której niszy dotyczy ten cykl
        current_niche = state.get('ceo_decision', {}).get('chosen_niche')
        if not current_niche:
            print("[FINANCE AGENT] Ostrzeżenie: Brak aktywnej niszy. Nie można przypisać wyników.")
            return state

        # Zaktualizuj dane historyczne dla tej niszy
        metrics = state['performance_metrics'].setdefault(current_niche, {
            'total_revenue': 0.0,
            'total_cost': 0.0,
            'content_pieces': 0,
            'roi': 0.0
        })
        
        metrics['total_revenue'] += revenue
        metrics['total_cost'] += self.COST_PER_CONTENT_PIECE
        metrics['content_pieces'] += 1
        
        # Oblicz ROI: (Zysk / Koszt) * 100%
        if metrics['total_cost'] > 0:
            total_profit = metrics['total_revenue'] - metrics['total_cost']
            metrics['roi'] = round((total_profit / metrics['total_cost']), 2)

        print(f"[FINANCE AGENT] Wyniki dla niszy '{current_niche}': Przychód={revenue:.2f}, Zysk={profit:.2f}, ROI={metrics['roi']:.2%}")
        
        # Zapisz bieżący zysk do pliku CSV (nadal użyteczne dla ogólnych trendów)
        finance_file = 'data/finance.csv'
        today = datetime.now().date().isoformat()
        file_exists = os.path.exists(finance_file)
        with open(finance_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists or os.path.getsize(finance_file) == 0:
                writer.writerow(['date', 'profit', 'niche'])
            writer.writerow([today, profit, current_niche])

        state['finance_summary'] = {'today_profit': profit, 'current_niche': current_niche}
        return state
