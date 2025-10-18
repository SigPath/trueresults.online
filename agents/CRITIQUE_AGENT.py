import os
import subprocess
from datetime import datetime

class CritiqueAgent:
    """
    Critique Agent — wewnętrzny redaktor i strażnik jakości. Ocenia wygenerowaną
    treść pod kątem oryginalności, wartości i "duszy", blokując publikację słabych materiałów.
    """
    def __init__(self, state):
        self.state = state
        self.drafts_dir = "data/drafts_for_review"
        os.makedirs(self.drafts_dir, exist_ok=True)
        self.quality_threshold = 7 # Minimalna ocena, aby treść przeszła dalej

    def _run_critique_prompt(self, content_text, content_mode):
        """Używa LLM (Copilot CLI) do oceny jakościowej treści."""
        if content_mode == 'CREATIVE':
            prompt = f"""
Jesteś surowym, ale sprawiedliwym krytykiem literackim. Oceń poniższy tekst w skali od 1 do 10 pod kątem oryginalności, głębi refleksji i tego, czy "ma duszę". 
Odpowiedź zwróć w formacie JSON: {{"ocena": X, "uzasadnienie": "Krótkie uzasadnienie."}}

Tekst do oceny:
---
{content_text}
"""
        else: # PRODUCTION mode
            prompt = f"""
Jesteś redaktorem SEO. Oceń poniższy artykuł w skali od 1 do 10 pod kątem wartości dla czytelnika, klarowności i zgodności z dobrymi praktykami SEO (bez analizy technicznej, skup się na treści). 
Odpowiedź zwróć w formacie JSON: {{"ocena": X, "uzasadnienie": "Krótkie uzasadnienie."}}

Tekst do oceny:
---
{content_text}
"""
        try:
            # Używamy `gh copilot suggest` do wykonania oceny
            command = f'gh copilot suggest "{prompt}"'
            result = subprocess.run(command, check=True, shell=True, capture_output=True, text=True, encoding='utf-8')
            # Spróbuj sparsować odpowiedź jako JSON
            import json
            critique_json = json.loads(result.stdout.strip())
            return critique_json.get('ocena'), critique_json.get('uzasadnienie')
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[{datetime.now().isoformat()}] CRITIQUE AGENT: Błąd podczas krytyki przez LLM: {e}. Daję ocenę domyślną 5.")
            return 5, "Błąd automatycznej oceny."

    def run(self, state):
        """Ocenia gotową treść i decyduje o jej dalszym losie."""
        content_task = state.get('content_generation_task', {})
        
        if not content_task or content_task.get('status') != 'completed':
            return state # Działa tylko na treści, która została już wygenerowana

        print(f"[{datetime.now().isoformat()}] CRITIQUE AGENT: Rozpoczynam ocenę jakościową treści...")
        filepath = content_task['output_file']
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Pomijamy frontmatter w ocenie
                content_lines = f.readlines()
                content_to_critique = "".join(content_lines[4:]) # Zakładając 4 linie frontmatter

            score, justification = self._run_critique_prompt(content_to_critique, content_task['mode'])
            
            if score >= self.quality_threshold:
                print(f"[CRITIQUE AGENT] Ocena: {score}/10. Treść zaakceptowana. Uzasadnienie: '{justification}'")
                state['content_generation_task']['status'] = 'approved_for_publication'
            else:
                print(f"[CRITIQUE AGENT] Ocena: {score}/10. Treść ODRZUCONA. Wymaga poprawy. Uzasadnienie: '{justification}'")
                state['content_generation_task']['status'] = 'rejected'
                
                # Przenieś plik do draftów i dodaj notatkę od redaktora
                draft_path = os.path.join(self.drafts_dir, os.path.basename(filepath))
                os.rename(filepath, draft_path)
                
                with open(draft_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n---\n**Notatka od CritiqueAgent ({datetime.now().isoformat()})**\n")
                    f.write(f"**Ocena:** {score}/10\n**Uzasadnienie:** {justification}\n")
                
                print(f"[CRITIQUE AGENT] Plik przeniesiony do: {draft_path}")
        
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] CRITIQUE AGENT: Krytyczny błąd podczas oceny pliku {filepath}: {e}")
            state['content_generation_task']['status'] = 'critique_failed'

        return state
