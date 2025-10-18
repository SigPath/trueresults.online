import os
import re
from datetime import datetime

class FrontendAgent:
    """
    Frontend Agent — generuje plik index.html, który listuje wszystkie
    opublikowane artykuły, tworząc dynamiczny dashboard.
    """
    def __init__(self, state):
        self.state = state
        self.posts_dir = "frontend/content/posts"
        self.output_path = "frontend/index.html"

    def _parse_article_title(self, filepath):
        """Wyciąga tytuł z metadanych (frontmatter) pliku Markdown."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('title:'):
                        # Wyciągnij wartość po "title:", usuń cudzysłowy i białe znaki
                        return line.split(':', 1)[1].strip().strip('"')
            return "Beztytułowy Artykuł"
        except Exception:
            return "Błąd Odczytu Tytułu"

    def run(self, state):
        """Skanuje posty i generuje na ich podstawie plik index.html."""
        print(f"[{datetime.now().isoformat()}] FRONTEND AGENT: Generuję index.html...")
        
        try:
            # Znajdź wszystkie pliki .md w folderze
            all_posts = [f for f in os.listdir(self.posts_dir) if f.endswith('.md')]
            # Sortuj od najnowszych do najstarszych na podstawie nazwy pliku (YYYY-MM-DD)
            all_posts.sort(reverse=True)

            # Buduj listę artykułów w HTML
            article_links_html = ""
            if not all_posts:
                article_links_html = "<p>Brak opublikowanych artykułów.</p>"
            else:
                for post_filename in all_posts:
                    filepath = os.path.join(self.posts_dir, post_filename)
                    title = self._parse_article_title(filepath)
                    # Link prowadzi bezpośrednio do pliku .md, GitHub Pages go wyświetli
                    relative_path = f"content/posts/{post_filename}"
                    article_links_html += f'<li><a href="{relative_path}">{title}</a></li>\n'
            
            # Stwórz pełną stronę HTML
            html_template = f"""
<!DOCTYPE html>
<html lang=\"pl\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>TrueResults.online - Autonomiczny System AI</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 20px auto; padding: 0 15px; background-color: #fdfdfd; }}
        header {{ text-align: center; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
        h1 {{ color: #111; }}
        h2 {{ color: #333; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
        ul {{ list-style-type: none; padding: 0; }}
        li a {{ text-decoration: none; color: #007bff; font-size: 1.1em; }}
        li a:hover {{ text-decoration: underline; }}
        footer {{ text-align: center; margin-top: 40px; font-size: 0.9em; color: #777; }}
    </style>
</head>
<body>
    <header>
        <h1>TrueResults AI Network</h1>
        <p>Automatycznie generowane i publikowane treści przez sieć agentów AI.</p>
    </header>
    <main>
        <h2>Ostatnie Artykuły</h2>
        <ul>
            {article_links_html}
        </ul>
    </main>
    <footer>
        <p>Strona wygenerowana automatycznie o {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.</p>
    </footer>
</body>
</html>
"""
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(html_template)

            print(f"[FRONTEND AGENT] Plik index.html został pomyślnie zaktualizowany.")
        except Exception as e:
            print(f"[FRONTEND AGENT] Krytyczny błąd podczas generowania frontendu: {e}")
            
        return state
