import os
import subprocess
from datetime import datetime

class ExecutorAgent:
    """
    Executor Agent — zamyka pętlę autonomii. Odczytuje prompty
    i używa narzędzi CLI (np. GitHub Copilot CLI) do samodzielnego
    wygenerowania finalnej treści.
    """
    def __init__(self, state):
        self.state = state
        self.publish_dir = "frontend/content/posts"
        os.makedirs(self.publish_dir, exist_ok=True)

    def _run_copilot_cli(self, prompt_text):
        """Uruchamia GitHub Copilot CLI z podanym promptem."""
        try:
            # Używamy `gh copilot suggest` do generowania sugestii.
            # To jest serce autonomicznej kreacji.
            command = f'gh copilot suggest "{prompt_text}" --shell'
            result = subprocess.run(command, check=True, shell=True, capture_output=True, text=True, encoding='utf-8')
            return result.stdout.strip()
        except FileNotFoundError:
            print(f"[{datetime.now().isoformat()}] EXECUTOR AGENT: KRYTYCZNY BŁĄD - Komenda 'gh' nie znaleziona. Upewnij się, że GitHub CLI jest zainstalowane i w PATH.")
            return None
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.now().isoformat()}] EXECUTOR AGENT: Błąd wykonania komendy Copilota: {e.stderr}")
            return None

    def run(self, state):
        """Sprawdza zadania i wykonuje je za pomocą LLM CLI."""
        content_task = state.get('content_generation_task')
        
        if not content_task or content_task.get('status') != 'pending_creation':
            print(f"[{datetime.now().isoformat()}] EXECUTOR AGENT: Brak zadań do wykonania.")
            return state

        print(f"[{datetime.now().isoformat()}] EXECUTOR AGENT: Podjęto zadanie: {content_task['expected_title']}")
        prompt_filepath = content_task['prompt_file']

        try:
            with open(prompt_filepath, 'r', encoding='utf-8') as f:
                prompt = f.read()

            print(f"[{datetime.now().isoformat()}] EXECUTOR AGENT: Wysyłam prompt do GitHub Copilot CLI...")
            generated_content = self._run_copilot_cli(prompt)

            if not generated_content:
                print(f"[{datetime.now().isoformat()}] EXECUTOR AGENT: Nie udało się wygenerować treści. Oznaczam zadanie jako nieudane.")
                state['content_generation_task']['status'] = 'execution_failed'
                try:
                    os.remove(prompt_filepath)
                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] EXECUTOR AGENT: Nie udało się usunąć pliku promptu: {e}")
                return state

            # Zapisz gotowy artykuł
            from agents.MARKETING_AGENT import MarketingAgent # Importujemy, by użyć _create_slug
            slug = MarketingAgent(state)._create_slug(content_task['expected_title'])
            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = f"{timestamp}-{slug}.md"
            filepath = os.path.join(self.publish_dir, filename)

            file_content = f"---\ntitle: \"{content_task['expected_title']}\"\ndate: {timestamp}\n---\n\n{generated_content}"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)

            print(f"[{datetime.now().isoformat()}] EXECUTOR AGENT: Treść wygenerowana i zapisana w: {filepath}")

            # Zaktualizuj status zadania
            state['content_generation_task']['status'] = 'completed'
            state['content_generation_task']['output_file'] = filepath
            # Usuwamy plik promptu, bo zadanie zostało wykonane
            os.remove(prompt_filepath)

        except Exception as e:
            print(f"[{datetime.now().isoformat()}] EXECUTOR AGENT: Błąd podczas przetwarzania zadania: {e}")
            state['content_generation_task']['status'] = 'failed'

        return state
