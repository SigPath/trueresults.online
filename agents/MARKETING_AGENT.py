

import random
from datetime import datetime
import os
import re


class MarketingAgent:
    """
    Marketing Agent — publikuje treści, tworząc fizyczne pliki Markdown,
    i symuluje monitorowanie reakcji.
    """
    def __init__(self, state):
        self.state = state
        self.publish_dir = "frontend/content/posts"
        os.makedirs(self.publish_dir, exist_ok=True)
        # Symulujemy, że niektóre nisze mają większy potencjał
        self.niche_potential = {
            'ai-tools-for-business': 0.12,
            'sustainable-gadgets': 0.08,
            'home-automation-tips': 0.05,
            'biohacking-for-beginners': 0.10,
            'productivity-apps-review': 0.09,
            'default': 0.03
        }

    def _create_slug(self, title):
        """Tworzy URL-friendly slug z tytułu artykułu."""
        title = title.lower()
        title = re.sub(r'\s+', '-', title) # Zastąp spacje myślnikami
        title = re.sub(r'[^a-z0-9-]', '', title) # Usuń znaki specjalne
        return title[:60] # Ogranicz długość

    def _publish_article_to_file(self, article_data):
        """Zapisuje artykuł do pliku .md w folderze publikacji."""
        try:
            title = article_data['title']
            body = article_data['body']
            
            slug = self._create_slug(title)
            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = f"{timestamp}-{slug}.md"
            filepath = os.path.join(self.publish_dir, filename)

            # Dodajemy metadane (frontmatter) dla potencjalnych generatorów stron statycznych
            file_content = f"---\ntitle: \"{title}\"\ndate: {timestamp}\n---\n\n{body}"

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            print(f"[MARKETING AGENT] Artykuł opublikowany: {filepath}")
            return filepath
        except Exception as e:
            print(f"[MARKETING AGENT] Błąd podczas publikacji pliku: {e}")
            return None

    def run(self, state):
        """Uruchamia kampanię: czeka na treść lub publikuje jeśli gotowa."""
        print(f"[{datetime.now().isoformat()}] MARKETING AGENT: Rozpoczynam kampanię...")
        content_task = state.get('content_generation_task', {})
        # NOWA BRAMKA KONTROLI JAKOŚCI
        if not content_task or content_task.get('status') != 'approved_for_publication':
            print(f"[MARKETING AGENT] Czekam na akceptację treści przez CritiqueAgent.")
            return state
        # (Stara logika publikacji, jeśli treść jest gotowa)
        published_filepath = None
        generated_content = state.get('generated_content', {})
        if generated_content and generated_content.get('type') == 'article':
            published_filepath = self._publish_article_to_file(generated_content)

        # KROK 2: Symulacja wyników marketingowych (nadal potrzebna dla Agenta Finansowego)
        ceo_decision = state.get('ceo_decision', {})
        chosen_niche = ceo_decision.get('chosen_niche', 'default')
        base_engagement = self.niche_potential.get(chosen_niche, self.niche_potential['default'])
        random_factor = random.uniform(0.7, 1.3)
        simulated_engagement = base_engagement * random_factor
        marketing_summary = {
            'engagement_rate': round(simulated_engagement, 4),
            'views': random.randint(1000, 50000),
            'clicks': random.randint(50, 2500),
            'published_content_title': generated_content.get('title', 'N/A'),
            'published_filepath': published_filepath
        }
        print(f"[MARKETING AGENT] Wyniki kampanii: Nisza='{chosen_niche}', Zaangażowanie={marketing_summary['engagement_rate']:.2%}")
        state['marketing_summary'] = marketing_summary
        return state
