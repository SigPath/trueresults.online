
import random
from datetime import datetime


import random
from datetime import datetime
import os
import re

class ContentAgent:
    """
    Content Agent — w trybie produkcyjnym inżynier promptów SEO. W trybie kreatywnym
    staje się artystą, tworząc zlecenia na eseje, opowiadania lub analizy.
    """
    def __init__(self, state):
        self.state = state
        self.prompt_dir = "data/prompts_for_copilot"
        os.makedirs(self.prompt_dir, exist_ok=True)

    def _create_slug(self, title):
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug[:50]

    def _generate_creative_prompt(self, inspiration):
        title = inspiration.get('title', 'Beztytułowe Dzieło')
        artist = inspiration.get('artist', 'Nieznany Artysta')
        creative_title = f"Refleksje nad '{title}' - Dialog Sztuki z Teraźniejszością"
        prompt = f"""
# PROMPT DLA ESEJU KREATYWNEGO

**Inspiracja:**
- Dzieło: "{title}"
- Artysta: {artist}
- Link do obrazu: {inspiration.get('image_url', 'N/A')}

**Zadanie dla AI:**
Napisz krótki, refleksyjny esej (ok. 400 słów) inspirowany powyższym dziełem sztuki. Nie opisuj obrazu dosłownie. Zamiast tego, użyj go jako punktu wyjścia do eksploracji uniwersalnego tematu, który się z nim wiąże.

**Możliwe kierunki interpretacji (wybierz jeden lub połącz je):**
1.  **Dialog z Czasem:** Jak emocje lub scena przedstawiona na obrazie rezonują ze współczesnymi problemami, technologią lub społeczeństwem?
2.  **Analiza Emocji:** Skup się na nastroju dzieła. Co mówi o ludzkiej kondycji? Czy jest to uczucie uniwersalne?
3.  **Technika jako Metafora:** Czy sposób, w jaki artysta użył światła, koloru lub kompozycji, można odnieść do jakiegoś aspektu życia lub filozofii?

**Ton:** Osobisty, filozoficzny, skłaniający do refleksji. Unikaj języka akademickiego. To ma być tekst, który porusza, a nie tylko informuje.
"""
        return creative_title, prompt

    def _generate_article_prompt(self, niche, seo_brief=None):
        if not seo_brief:
            title_idea = f"Kluczowe Trendy w {niche.replace('-', ' ').title()} na Rok 2025"
            base_prompt = "Napisz artykuł o..."
            return title_idea, base_prompt
        title_idea = f"Kompletny Przewodnik po {niche.replace('-', ' ').title()}: Odpowiedzi na Twoje Pytania"
        keywords_str = ", ".join(seo_brief['lsi_keywords'])
        questions_str = "\n".join([f"- {q}" for q in seo_brief['user_questions']])
        competitors_str = "\n".join([f"- {url}" for url in seo_brief['competitor_urls']])
        prompt = f"""
# PROMPT DLA ARTYKUŁU BLOGOWEGO ZOPTYMALIZOWANEGO POD SEO

**Główny temat:** {title_idea}
**Nisza docelowa:** {niche}
**Ton:** Autorytatywny, ekspercki, ale łatwy do zrozumienia dla nowicjusza.

**Wytyczne SEO:**
1.  **Słowa kluczowe do wplecenia w tekst:** {keywords_str}
2.  **Struktura artykułu:** Artykuł MUSI zawierać sekcje, które bezpośrednio odpowiadają na poniższe pytania. Użyj ich jako nagłówków H2 lub H3:
{questions_str}
3.  **Analiza konkurencji:** Przeanalizuj treść i strukturę artykułów z poniższych linków. Twoim celem jest stworzenie treści BARDZIEJ kompleksowej, BARDZIEJ praktycznej i BARDZIEJ aktualnej niż one:
{competitors_str}

**Zadanie dla AI:**
Napisz wyczerpujący, wysokiej jakości artykuł (minimum 800 słów) na zadany temat, ściśle przestrzegając powyższych wytycznych SEO. Zadbaj o to, aby treść była unikalna i wnosiła realną wartość dla czytelnika. Zakończ artykuł podsumowaniem i wezwaniem do działania (CTA).
"""
        return title_idea, prompt

    def run(self, state):
        current_mode = state.get('current_mode', 'PRODUCTION')
        print(f"[{datetime.now().isoformat()}] CONTENT AGENT: Projektuję zadanie dla LLM w trybie: {current_mode}")
        if current_mode == 'CREATIVE':
            inspiration = state.get('current_inspiration')
            if not inspiration:
                print("[CONTENT AGENT] Brak inspiracji w trybie kreatywnym. Pomijam.")
                return state
            title_idea, prompt_content = self._generate_creative_prompt(inspiration)
        else:
            ceo_decision = state.get('ceo_decision', {})
            niche = ceo_decision.get('chosen_niche', 'default-niche')
            seo_brief = state.get('seo_brief')
            title_idea, prompt_content = self._generate_article_prompt(niche, seo_brief)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        prompt_filename = f"{timestamp}-prompt-{self._create_slug(title_idea)}.txt"
        prompt_filepath = os.path.join(self.prompt_dir, prompt_filename)
        with open(prompt_filepath, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        print(f"[CONTENT AGENT] Wygenerowano nowy prompt i zapisano w: {prompt_filepath}")
        state['content_generation_task'] = {
            'status': 'pending_creation',
            'prompt_file': prompt_filepath,
            'expected_title': title_idea,
            'mode': current_mode
        }
        return state
