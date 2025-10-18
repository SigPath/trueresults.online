from agents.DISTRIBUTION_AGENT import DistributionAgent
from agents.SEO_AGENT import SEOAgent

import json, time
from agents.TRENDWATCHER_AGENT import TrendWatcherAgent
from agents.INNOVATION_AGENT import InnovationAgent
from agents.CEO_AGENT import CEOAgent
from agents.RESEARCH_AGENT import ResearchAgent
from agents.CONTENT_AGENT import ContentAgent
from agents.MARKETING_AGENT import MarketingAgent
from agents.EXECUTOR_AGENT import ExecutorAgent
from agents.MONETIZATION_AGENT import MonetizationAgent
from agents.FRONTEND_AGENT import FrontendAgent
from agents.VCS_AGENT import VCSAgent
from agents.ANALYTICS_AGENT import AnalyticsAgent

def load_state(path='data/state.json'):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(state, path='data/state.json'):
    with open(path, 'w') as f:
        json.dump(state, f, indent=2)


def main_loop():
    state = load_state()
    trend_watcher = TrendWatcherAgent(state)
    innovation = InnovationAgent(state)
    ceo = CEOAgent(state)
    seo = SEOAgent(state)
    research = ResearchAgent(state)
    content = ContentAgent(state)
    executor = ExecutorAgent(state)
    from agents.INSPIRATION_AGENT import InspirationAgent
    inspiration = InspirationAgent(state)
    from agents.CRITIQUE_AGENT import CritiqueAgent
    critique = CritiqueAgent(state)
    monetization = MonetizationAgent(state)
    marketing = MarketingAgent(state)
    from agents.FINANCE_AGENT import FinanceAgent
    finance = FinanceAgent(state)
    frontend = FrontendAgent(state)
    vcs = VCSAgent(state)
    distribution = DistributionAgent(state)
    analytics = AnalyticsAgent(state)

    while True:
        # CEO jako pierwszy ustawia tryb i strategię
        state = ceo.run(state)
        current_mode = state.get('current_mode', 'PRODUCTION')

        # Uruchamiamy agentów warunkowo na podstawie trybu
        if current_mode == 'CREATIVE':
            state = inspiration.run(state)
        else: # PRODUCTION
            state = trend_watcher.run(state)
            state = analytics.run(state)
            state = seo.run(state)
            state = research.run(state)

        # Ci agenci działają w obu trybach, ale adaptują swoje zachowanie
        state = innovation.run(state)
        state = content.run(state)
        state = executor.run(state)
        state = critique.run(state)
        state = monetization.run(state)

        # Marketing i reszta działają tylko, gdy treść jest gotowa do publikacji
        if state.get('content_generation_task', {}).get('status') == 'approved_for_publication':
            state = marketing.run(state)
            state = frontend.run(state)
            state = vcs.run(state)
            state = distribution.run(state)

        save_state(state)
        print("--- CYKL ZAKOŃCZONY, OCZEKIWANIE ---")
        time.sleep(5)

if __name__ == '__main__':
    main_loop()
