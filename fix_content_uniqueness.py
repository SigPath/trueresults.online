#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generator naprawek dla unikalnej treści artykułów - każdy artykuł będzie miał
unikalną treść dopasowaną do swojego tematu, nie tylko unikalny tytuł.
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from slugify import slugify
import pandas as pd
import re

def load_evidence_data():
    """Ładuje materiały dowodowe."""
    evidence_data = {}
    
    # Karolina-Marcin materiały
    karolina_marcin_file = Path("docs/karolina_marcin.txt")
    if karolina_marcin_file.exists():
        with open(karolina_marcin_file, 'r', encoding='utf-8') as f:
            evidence_data['karolina_marcin'] = f.read()
    
    return evidence_data

def generate_unique_content_for_topic(title: str, thesis: str, campaign: str) -> dict:
    """Generuje unikalną treść dla każdego tematu."""
    
    # Różne wzorce treści w zależności od tematu
    topic_lower = title.lower()
    
    # Specyficzne sekcje dla różnych tematów
    specific_sections = []
    
    # Gaslighting
    if "gaslighting" in topic_lower:
        specific_sections = [
            {
                "title": "Techniki gaslightingu w komunikacji",
                "content": "Analiza rzeczywistych SMS-ów ujawnia systematyczne wykorzystywanie technik podważania pewności siebie partnera. Obserwujemy wzorce zaprzeczania faktom dokumentalnym oraz redefiniowania rzeczywistości."
            },
            {
                "title": "Etapy procesu gaslightingu",
                "content": "Dokumentacja pokazuje ewolucję od subtelnych sugestii po otwarcie podważanie zdolności poznawczych ofiary. Proces przebiega stopniowo, co utrudnia rozpoznanie manipulacji."
            },
            {
                "title": "Wpływ na pamięć i percepcję",
                "content": "Długotrwałe narażenie na gaslighting prowadzi do problemów z zaufaniem do własnej pamięci i osądu sytuacji. Ofiara zaczyna wątpić w swoje spostrzeżenia."
            }
        ]
    
    # Manipulacja psychologiczna
    elif "manipulac" in topic_lower:
        specific_sections = [
            {
                "title": "Strategie manipulacyjne",
                "content": "W badanym przypadku identyfikujemy wykorzystanie lęku przed porzuceniem jako głównego narzędzia kontroli. Manipulator świadomie potęguje niepewność partnera."
            },
            {
                "title": "Cykle manipulacji",
                "content": "Analiza ujawnia powtarzające się cykle: prowokacja - konflikt - pozorne przeprosiny - krótki okres spokoju - kolejna prowokacja. Ten wzorzec utrzymuje ofiarę w stanie chronicznego stresu."
            },
            {
                "title": "Instrumentalizacja emocji",
                "content": "Manipulator wykorzystuje emocjonalne przywiązanie partnera jako broń. Deklaracje miłości są używane selektywnie - tylko gdy służą osiągnięciu określonych celów."
            }
        ]
    
    # Alienacja rodzicielska
    elif "alienac" in topic_lower:
        specific_sections = [
            {
                "title": "Mechanizmy alienacji",
                "content": "Dokumentacja pokazuje systematyczne działania mające na celu osłabienie więzi dziecka z drugim rodzicem. Wykorzystywane są manipulacyjne narracje przedstawiające jednego rodzica jako 'złego'."
            },
            {
                "title": "Wpływ na dziecko",
                "content": "Dziecko staje się nieświadomym narzędziem w konflikcie dorosłych. Obserwujemy instrumentalizację potrzeb dziecka dla usprawiedliwienia własnych działań."
            },
            {
                "title": "Długoterminowe konsekwencje",
                "content": "Alienacja rodzicielska powoduje trwałe szkody w rozwoju emocjonalnym dziecka i jego przyszłych relacjach interpersonalnych."
            }
        ]
    
    # Narcyzm
    elif "narcyz" in topic_lower or "grandioz" in topic_lower:
        specific_sections = [
            {
                "title": "Narcystyczna regulacja samooceny",
                "content": "Badana osoba wymaga ciągłej walidacji z zewnątrz. Brak uznania prowadzi do narcystycznej rany i agresywnych reakcji obronnych."
            },
            {
                "title": "Brak empatii poznawczej",
                "content": "Dokumentowane zachowania wskazują na niezdolność do rzeczywistego zrozumienia i uwzględnienia potrzeb innych osób. Empatia jest symulowana tylko gdy służy własnym celom."
            },
            {
                "title": "Narcystyczne projekcje",
                "content": "Własne negatywne cechy są systematycznie przypisywane innym. To mechanizm ochrony przed konfrontacją z prawdziwym obrazem siebie."
            }
        ]
    
    # Projekcja winy
    elif "projekcja" in topic_lower or "wina" in topic_lower:
        specific_sections = [
            {
                "title": "Mechanizmy projekcji winy",
                "content": "Analiza komunikacji pokazuje systematyczne przenoszenie odpowiedzialności za własne czyny na inne osoby. Każde destrukcyjne zachowanie jest usprawiedliwiane winą partnera."
            },
            {
                "title": "Odwrócenie ról sprawca-ofiara",
                "content": "Rzeczywista ofiara manipulacji jest konsekwentnie przedstawiana jako agresor. Ten mechanizm służy unikaniu odpowiedzialności za szkody wyrządzone w relacji."
            },
            {
                "title": "Funkcje obronne projekcji",
                "content": "Projekcja winy chroni przed dyskomfortem poznawczym wynikającym z konfrontacji z własnymi destrukcyjnymi zachowaniami."
            }
        ]
    
    # Splitting/segmentacja tożsamości  
    elif "splitting" in topic_lower or "segmentac" in topic_lower or "tożsam" in topic_lower:
        specific_sections = [
            {
                "title": "Mechanizm splitting",
                "content": "Obserwujemy dychotomiczne myślenie typu 'wszystko albo nic'. Ludzie są kategoryzowani jako całkowicie dobrzy lub całkowicie źli, bez odcieni szarości."
            },
            {
                "title": "Segmentacja życia",
                "content": "Różne sfery życia są hermetycznie oddzielone. To pozwala na uniknięcie konfrontacji z sprzecznościami między deklarowanymi wartościami a rzeczywistymi czynami."
            },
            {
                "title": "Idealizacja i dewaluacja",
                "content": "Cykle przemiennej idealizacji i dewaluacji tej samej osoby. Partner jest naprzemiennie postrzegany jako zbawca lub prześladowca."
            }
        ]
    
    # Podwójne życie
    elif "podwójn" in topic_lower or "dwulicow" in topic_lower:
        specific_sections = [
            {
                "title": "Architektura podwójnego życia",
                "content": "Systematyczna organizacja dwóch równoległych rzeczywistości relacyjnych. Każda relacja jest prezentowana jako jedyna i prawdziwa."
            },
            {
                "title": "Zarządzanie kłamstwami",
                "content": "Złożony system fałszywych narracji utrzymywanych jednocześnie. Wymaga to znacznych zasobów poznawczych i emocjonalnych."
            },
            {
                "title": "Psychologiczne koszty dwulicowości",
                "content": "Prowadzenie podwójnego życia generuje chroniczny stres związany z ryzykiem wykrycia oraz fragmentację tożsamości."
            }
        ]
    
    # Emotional dumping
    elif "emotional" in topic_lower and "dump" in topic_lower:
        specific_sections = [
            {
                "title": "Wzorce emotional dumping",
                "content": "Niekontrolowane wyładowywanie negatywnych emocji na partnera bez uwzględnienia jego stanu psychicznego czy możliwości przyjęcia tego obciążenia."
            },
            {
                "title": "Brak reciprocity emocjonalnej",
                "content": "Jednostronne wykorzystywanie partnera jako 'kosza na śmieci' emocjonalne. Własne potrzeby wsparcia są ignorowane lub minimalizowane."
            },
            {
                "title": "Konsekwencje dla odbiorcy",
                "content": "Chroniczne narażenie na emotional dumping prowadzi do emocjonalnego wyczerpania i wtórnej traumatyzacji u partnera."
            }
        ]
    
    # Triangulacja
    elif "triangulac" in topic_lower:
        specific_sections = [
            {
                "title": "Mechanizmy triangulacji",
                "content": "Włączanie trzecich osób w dyadic conflict w celu rozproszenia napięcia lub uzyskania przewagi. Często wykorzystywane są dzieci lub członkowie rodziny."
            },
            {
                "title": "Funkcje triangulacji",
                "content": "Triangulacja służy unikaniu bezpośredniej konfrontacji oraz przerzucaniu odpowiedzialności za problemy relacyjne na czynniki zewnętrzne."
            },
            {
                "title": "Destrukcyjny wpływ na system rodzinny",
                "content": "Triangulacja destabilizuje naturalne granice w systemie rodzinnym i wciąga niewinne osoby w konflikty dorosłych."
            }
        ]
    
    # Domyślne sekcje dla innych tematów
    else:
        specific_sections = [
            {
                "title": f"Charakterystyka wzorca '{title.lower()}'",
                "content": f"Analiza materiałów dowodowych ujawnia specyficzne cechy związane z {title.lower()}. Wzorzec ten przejawia się w systematycznych zachowaniach dokumentowanych przez okres trzech lat."
            },
            {
                "title": "Mechanizmy obronne",
                "content": "Badana osoba wykorzystuje złożone mechanizmy obronne do unikania konfrontacji z konsekwencjami własnych działań. Główną strategią jest externalizacja winy."
            },
            {
                "title": "Progresja wzorca",
                "content": "Dokumentacja pokazuje ewolucję i nasilanie się problemowych zachowań w czasie. Brak interwencji prowadzi do eskalacji destrukcyjnych wzorców."
            }
        ]
    
    # Tworzenie głównej treści
    main_content_parts = [
        f"<h2>Analiza Case Study: {title}</h2>",
        
        f"<p><strong>Kontekst badawczy:</strong> Niniejsza analiza opiera się na rzeczywistych materiałach dowodowych - SMS-ach, logach rozmów i udokumentowanych zachowaniach. Jest to ekspertcka ocena psychologiczna wzorców behawioralnych przeprowadzona metodą case study.</p>",
        
        f"<p><strong>Główna teza badawcza:</strong> {thesis}</p>",
        
        "<h3>Materiały dowodowe</h3>",
        "<p>Analiza opiera się na autentycznej dokumentacji komunikacji obejmującej tysiące SMS-ów z okresu maj 2021 - wrzesień 2024, logi rozmów z października 2024 oraz udokumentowane wzorce zachowań w relacjach międzyosobowych.</p>"
    ]
    
    # Dodanie specyficznych sekcji
    for section in specific_sections:
        main_content_parts.append(f"<h3>{section['title']}</h3>")
        main_content_parts.append(f"<p>{section['content']}</p>")
    
    # Uniwersalne sekcje końcowe
    main_content_parts.extend([
        "<h3>Wpływ na system rodzinny</h3>",
        "<p>Analiza pokazuje systematyczne wzorce krzywdzenia osób w najbliższym otoczeniu oraz długoterminowe konsekwencje manipulacji dla wszystkich zaangażowanych stron.</p>",
        
        "<h3>Prognozy behawioralne</h3>", 
        "<p>Na podstawie analizy wzorców można prognozować kontynuację destrukcyjnych zachowań przy braku profesjonalnej interwencji terapeutycznej.</p>",
        
        "<h3>Znaczenie dla praktyki klinicznej</h3>",
        "<p>Ten case study dostarcza cennych informacji dla terapeutów i ilustruje mechanizmy obronne typowe dla zaburzeń osobowości z klastra B.</p>",
        
        "<h3>Wnioski końcowe</h3>",
        "<p>Przedstawiona analiza demaskuje złożony system mechanizmów obronnych i wzorców manipulacyjnych. Wymaga to profesjonalnej interwencji oraz stanowi materiał edukacyjny dla zwiększania świadomości społecznej.</p>",
        
        "<p><em>Analiza przeprowadzona na podstawie rzeczywistych materiałów dowodowych dla celów edukacyjnych i zwiększenia świadomości mechanizmów manipulacji psychologicznej.</em></p>"
    ])
    
    html_content = "\n".join(main_content_parts)
    
    # FAQ dostosowane do tematu
    topic_specific_faq = f"""
<div class='faq-section'>
<h2>Najczęściej zadawane pytania</h2>
<div class='faq-item'>
<h3>Czy analiza "{title}" opiera się na rzeczywistych wydarzeniach?</h3>
<p>Tak, wszystkie analizowane wzorce pochodzą z autentycznych materiałów dowodowych zebranych w okresie maj 2021 - wrzesień 2024.</p>
</div>
<div class='faq-item'>
<h3>Jakie mechanizmy psychologiczne są analizowane w kontekście "{title.lower()}"?</h3>
<p>Główny fokus to mechanizmy obronne charakterystyczne dla zaburzeń osobowości klastra B, ze szczególnym uwzględnieniem wzorców związanych z {title.lower()}.</p>
</div>
<div class='faq-item'>
<h3>Czy można zastosować te wnioski do innych przypadków {title.lower()}?</h3>
<p>Wzorce behawioralne opisane w analizie są charakterystyczne dla określonych zaburzeń osobowości i mogą występować w podobnych konstelacjach relacyjnych.</p>
</div>
</div>
    """
    
    related_articles = f"""
<div class='related-articles'>
<h2>Powiązane analizy case study</h2>
<p>Inne szczegółowe analizy psychologiczne z kategorii "{campaign}" oparte na rzeczywistych materiałach dowodowych z tej samej kolekcji case studies.</p>
</div>
    """
    
    return {
        "title": title,
        "meta_description": f"Szczegółowa analiza psychologiczna: {title}. Demaskowanie mechanizmów obronnych na podstawie rzeczywistych materiałów dowodowych - SMS-y, rozmowy, zachowania.",
        "html_content": html_content,
        "faq_html": topic_specific_faq,
        "related_articles_html": related_articles,
        "faq_json_ld": {}
    }

def regenerate_articles_with_unique_content():
    """Regeneruje wszystkie artykuły z unikalną treścią."""
    
    pages_dir = Path("pages")
    if not pages_dir.exists():
        print("Brak katalogu pages/")
        return
    
    # Pobierz wszystkie pliki HTML
    html_files = list(pages_dir.glob("*.html"))
    print(f"Znaleziono {len(html_files)} artykułów do regeneracji")
    
    # Wczytaj szablon
    template_path = Path("szablon_wpisu.html")
    if not template_path.exists():
        print("Brak szablonu szablon_wpisu.html")
        return
        
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Przygotuj mapowanie kampanii na podstawie nazw plików
    campaign_mapping = {
        "gaslighting": "Gaslighting i Projekcja",
        "manipulac": "Manipulacja Psychologiczna", 
        "alienac": "Alienacja Rodzicielska",
        "narcyz": "Narcyzm i Grandiozja",
        "projekcja": "Gaslighting i Projekcja",
        "splitting": "Segmentacja Tożsamości",
        "podwójn": "Anatomia Nielojalności",
        "emotional": "Manipulacja Psychologiczna",
        "triangulac": "Anatomia Nielojalności",
        "instrumentaliz": "Instrumentalizacja Relacji",
        "chaos": "Duchowy Chaos",
        "lęk": "Lęki i Kompulsje",
        "toksyczn": "Toksyczne Wzorce",
        "konsekwencj": "Konsekwencje Behawioralne",
        "obron": "Mechanizmy Obronne"
    }
    
    regenerated_count = 0
    
    for html_file in html_files:  # Wszystkie pliki
        filename = html_file.stem
        print(f"🔄 Regeneruję: {filename}")
        
        # Wyodrębnij tytuł z nazwy pliku
        title_parts = filename.replace('-', ' ').split()
        # Usuń datę z końca
        if len(title_parts) > 1 and title_parts[-1].isdigit():
            title_parts = title_parts[:-1]
        
        title = ' '.join(title_parts).title()
        
        # Określ kampanię na podstawie słów kluczowych
        campaign = "Analiza Case Study"
        for keyword, camp in campaign_mapping.items():
            if keyword in filename.lower():
                campaign = camp
                break
        
        # Wyodrębnij datę z nazwy pliku  
        date_match = re.search(r'(\d{8})(?:\.html)?$', filename)
        if date_match:
            date_str = date_match.group(1)
            try:
                target_date = datetime.strptime(date_str, '%Y%m%d')
            except ValueError:
                target_date = datetime.now()
        else:
            target_date = datetime.now()
        
        # Wygeneruj unikalną treść
        thesis = f"Studium przypadku demaskuje ukryte aspekty {title.lower()} w relacjach toksycznych."
        content_data = generate_unique_content_for_topic(title, thesis, campaign)
        
        # Wypełnij szablon
        post_url = f"https://trueresults.online/pages/{html_file.name}"
        
        # Ustawienie polskiej lokalizacji dla daty
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
        except locale.Error:
            pass
        
        human_date = target_date.strftime('%d %B %Y')
        iso_date = target_date.isoformat()
        
        html = template_content
        html = html.replace("{{TYTUL}}", content_data['title'])
        html = html.replace("{{OPIS}}", content_data['meta_description'])
        html = html.replace("{{META_OPIS}}", content_data['meta_description'])
        html = html.replace("{{KANONICAL}}", post_url)
        html = html.replace("{{DATA}}", iso_date)
        html = html.replace("{{DATA_LUDZKA}}", human_date)
        html = html.replace("{{KATEGORIA}}", campaign)
        html = html.replace("{{TRESC_ARTYKULU}}", content_data['html_content'])
        html = html.replace("{{TRESC_HTML}}", content_data['html_content'])
        html = html.replace("{{FAQ_JSON_LD}}", "")
        html = html.replace("{{FAQ_HTML}}", content_data['faq_html'])
        html = html.replace("{{POWIAZANE_POSTY_HTML}}", content_data['related_articles_html'])
        
        # Zapisz plik
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        regenerated_count += 1
        print(f"✅ Regenerowano: {filename} (kampania: {campaign})")
    
    print(f"\n🎉 Zregenerowano {regenerated_count} artykułów z unikalną treścią!")

if __name__ == "__main__":
    regenerate_articles_with_unique_content()