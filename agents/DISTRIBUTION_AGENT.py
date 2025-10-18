import os
import tweepy
from datetime import datetime

class DistributionAgent:
    """
    Distribution Agent — specjalista od mediów społecznościowych. Automatycznie
    promuje nowe treści na platformach takich jak X (Twitter), zwiększając zasięg.
    """
    def __init__(self, state):
        self.state = state
        # Wczytaj klucze API z zmiennych środowiskowych - NIGDY NIE ZAPISUJ ICH W KODZIE
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret_key = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.repo_name = os.getenv('GITHUB_REPO') # np. "twoja-nazwa/TrueResults-AI"

        self.client = self._get_twitter_client()

    def _get_twitter_client(self):
        """Inicjalizuje i zwraca klienta API v2 dla Twittera."""
        if not all([self.api_key, self.api_secret_key, self.access_token, self.access_token_secret]):
            print("[DISTRIBUTION AGENT] OSTRZEŻENIE: Brak kluczy API Twittera. Agent będzie nieaktywny.")
            return None
        try:
            client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret_key,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            return client
        except Exception as e:
            print(f"[DISTRIBUTION AGENT] Błąd inicjalizacji klienta Twittera: {e}")
            return None

    def _construct_public_url(self, local_filepath):
        """Konstruuje publiczny URL na podstawie ścieżki pliku i nazwy repo."""
        if not self.repo_name:
            return None
        user_name = self.repo_name.split('/')[0]
        public_path = local_filepath.replace('frontend/', '')
        return f"https://{user_name}.github.io/{self.repo_name.split('/')[1]}/{public_path}"

    def run(self, state):
        """Publikuje post o nowym artykule na Twitterze."""
        if not self.client:
            return state

        filepath = state.get('marketing_summary', {}).get('published_filepath')
        title = state.get('marketing_summary', {}).get('published_content_title')

        if not filepath or not title:
            print("[DISTRIBUTION AGENT] Brak nowego artykułu do promocji w tym cyklu.")
            return state

        public_url = self._construct_public_url(filepath)
        if not public_url:
            print("[DISTRIBUTION AGENT] Błąd: Brak GITHUB_REPO. Nie można stworzyć publicznego URL.")
            return state

        hashtags = "#AI #Biznes #Automatyzacja #" + state.get('ceo_decision', {}).get('chosen_niche', '').replace('-', '')
        post_text = f"🚀 Nowy artykuł na blogu: \"{title}\"\n\nDowiedz się więcej i zoptymalizuj swoje działania!\n\n{public_url}\n\n{hashtags}"

        try:
            print(f"[{datetime.now().isoformat()}] DISTRIBUTION AGENT: Publikuję na Twitterze: {post_text}")
            self.client.create_tweet(text=post_text)
            print("[DISTRIBUTION AGENT] Pomyślnie opublikowano post na Twitterze.")
        except tweepy.errors.TweepyException as e:
            print(f"[DISTRIBUTION AGENT] Błąd podczas publikacji na Twitterze: {e}")

        state['marketing_summary']['published_filepath'] = None

        return state
