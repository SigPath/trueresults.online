#!/usr/bin/env python3
"""
Silnik publikacyjny TrueResults v5 (alternatywny czysty plik)
=============================================================
UWAGA: Oryginalny plik update_blog.py jest przeładowany i trudny do czyszczenia etapowego.
Ten plik zawiera minimalną, działającą implementację v5.0 zgodnie z założeniami:
1. Wybór tematu (rotacja + historia)
2. Master prompt + case study (jeśli istnieją)
3. Generacja artykułu (Gemini lub fallback gdy brak klucza)
4. Zapis pages/<slug>.html
5. Aktualizacja index.html (sekcja <!--AUTO-BLOG-->) do 21 kart
6. Generacja spis.html, feed.xml, sitemap.xml, JSON-LD
7. Commit + (opcjonalny) push Git
8. Log w logs/last_run.txt
9. Masowa regeneracja (MASS_REGENERATE=N)

Aby używać: python engine_v5.py  (lub ustaw cron zamiast update_blog.py)
Po weryfikacji można zastąpić nim update_blog.py (przenazwać / usunąć stary).
"""
from __future__ import annotations
import os, re, json, textwrap, datetime as dt, random, html
from pathlib import Path
from typing import Optional, List, Dict

# === KROK 4: Implementacja trybu "Dry Run" ===
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def safe_write(path: Path, content: str, *, binary: bool = False):
    if DRY_RUN:
        print(f"[DRY RUN] Zapis pliku pominięty: {path}")
        return
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        with open(path, "wb") as f:
            f.write(content)  # type: ignore[arg-type]
    else:
        path.write_text(content, encoding="utf-8")

ROOT = Path(__file__).parent
PAGES = ROOT / "pages"
PROMPTS = ROOT / "prompts"
LOG_DIR = ROOT / "logs"
TEMPLATE = ROOT / "template.html"
INDEX_FILE = ROOT / "index.html"
SPIS_FILE = ROOT / "spis.html"
FEED_FILE = ROOT / "feed.xml"
SITEMAP_FILE = ROOT / "sitemap.xml"
HISTORY_FILE = ROOT / "history_topics.txt"
LOG_FILE = LOG_DIR / "last_run.txt"

BASE_URL = os.getenv("BASE_URL", "https://trueresults.online").rstrip('/')
SITE_NAME = "True Results Online"
MAX_INDEX_CARDS = 21
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "WPROWADZ_KLUCZ_LOKALNIE")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")

CAMPAIGNS = [
    "Fundamenty świadomości relacyjnej",
    "Architektura emocjonalna decyzji",
    "Systemy zaufania i sygnały bezpieczeństwa",
    "Mechanizmy projekcji i zniekształceń",
    "Regulacja wewnętrzna vs. poszukiwanie bodźców",
]

def current_campaign(day: Optional[dt.date] = None) -> str:
    d = day or dt.date.today()
    return CAMPAIGNS[d.isocalendar().week % len(CAMPAIGNS)]

BASE_TOPICS = [
    "Granice poznawcze w relacjach intymnych",
    "Dynamika mikrorozczarowań w komunikacji",
    "Rola ciszy i pauzy w eskalacji konfliktu",
    "Psychologiczna inercja w toksycznych układach",
    "Wewnętrzne modele bezpieczeństwa a ekspozycja na stres",
]

def load_topic_history() -> List[str]:
    if not HISTORY_FILE.exists(): return []
    try: return [l.strip() for l in HISTORY_FILE.read_text(encoding='utf-8').splitlines() if l.strip()]
    except Exception: return []

def save_topic_history(hist: List[str]) -> None:
    try: HISTORY_FILE.write_text("\n".join(hist[-500:]), encoding='utf-8')
    except Exception: pass

def pick_topic(day: Optional[dt.date] = None) -> str:
    hist = load_topic_history(); pool = BASE_TOPICS[:]; random.shuffle(pool)
    for t in pool:
        if t not in hist[-50:]: hist.append(t); save_topic_history(hist); return t
    t = random.choice(BASE_TOPICS); hist.append(t); save_topic_history(hist); return t

_MASTER: Optional[str] = None
_CASE: Optional[str] = None

def load_master_prompt() -> str:
    global _MASTER
    if _MASTER is None:
        p = PROMPTS / "master_prompt.py"
        try: _MASTER = p.read_text(encoding='utf-8')
        except Exception: _MASTER = "# brak master prompt"
    return _MASTER

def load_case_study() -> str:
    global _CASE
    if _CASE is None:
        p = PROMPTS / "case_study.txt"
        try: _CASE = p.read_text(encoding='utf-8')[:6000]
        except Exception: _CASE = "(brak case study)"
    return _CASE

def call_gemini(prompt: str) -> str:
    if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
        return "FALLBACK (brak klucza)\n\n" + prompt[:400]
    try:
        import google.generativeai as gen  # type: ignore
        gen.configure(api_key=GEMINI_API_KEY)
        model = gen.GenerativeModel(MODEL_NAME)
        resp = model.generate_content(prompt)
        if getattr(resp, 'text', None): return resp.text
        try: return ''.join(p.text for p in resp.parts if getattr(p, 'text', None))  # type: ignore
        except Exception: return "(empty response)"
    except Exception as e:
        return f"FALLBACK Gemini error: {e}\n\n" + prompt[:400]

def build_generation_prompt(topic: str) -> str:
    return textwrap.dedent(f"""
    Jesteś systemem generującym pogłębione analizy relacyjne (pl, styl: kliniczno‑analityczny, strukturalny).
    KAMPANIA: {current_campaign()}
    TEMAT DNIA: {topic}
    MASTER PROMPT (fragment):\n{load_master_prompt()[:3500]}\n---\nCASE STUDY (fragment):\n{load_case_study()}\n---
    OUTPUT = JSON (jedna linia) z polami: title, description, html_content.
    Zasady:
    - title ≤ 72 znaki, tytuł informacyjny, bez cudzysłowów.
    - description 140–160 znaków, bez autopowtórzeń.
    - html_content: czyste HTML: <h1>, <h2>, <p>, <ul>, <li>, <strong>. Bez markdown.
    - Każda sekcja wnosi nową warstwę (zero tautologii / wypełniaczy).
    - Zwróć WYŁĄCZNIE JSON.
    """).strip()

def parse_ai_json(raw: str) -> Dict[str,str]:
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return {"title":"Artykuł Bez Tytułu","description":"Analiza.","html_content":f"<p>{html.escape(raw[:400])}</p>"}
    try:
        data = json.loads(m.group(0))
    except Exception:
        return {"title":"Artykuł – fallback","description":"Analiza.","html_content":f"<p>{html.escape(raw[:400])}</p>"}
    for k in ("title","description","html_content"): data.setdefault(k,"")
    return data

def ensure_unique_title(title: str) -> str:
    return title.strip().replace('\n',' ')[:120]

def generate_article(topic: str) -> Dict[str,str]:
    data = parse_ai_json(call_gemini(build_generation_prompt(topic)))
    data['title'] = ensure_unique_title(data['title'] or topic.title())
    if not data['description'].strip():
        plain = re.sub(r"<[^>]+>"," ",data['html_content']).strip()
        data['description'] = (plain[:155]+'…') if len(plain)>155 else plain[:160]
    return data

# === FAQ Generation (v5.1) ===
def generate_faq(article_html: str, topic: str) -> List[Dict[str,str]]:
    """Wygeneruj listę QA (max 6) dotyczącą tematu i treści artykułu.

    Zwraca listę słowników: [{question, answer}, ...]. Fallback gdy brak API:
    - Wyciąga nagłówki <h2> i buduje proste pytania.
    """
    # Fallback / brak klucza
    if GEMINI_API_KEY == "WPROWADZ_KLUCZ_LOKALNIE":
        heads = re.findall(r"<h2[^>]*>(.*?)</h2>", article_html)[:4]
        faq = []
        for h in heads:
            q = f"Co warto zapamiętać z sekcji: {re.sub(r'<[^>]+>', '', h)}?"
            a = f"Sekcja '{re.sub(r'<[^>]+>', '', h)}' rozwija aspekt tematu: {topic}."[:380]
            faq.append({"question": q, "answer": a})
        return faq

    prompt = textwrap.dedent(f"""
    Przygotuj zwięzłe FAQ w języku polskim w formacie JSON ONLY.
    TEMAT: {topic}
    KONTEKST_HTML (fragment): {article_html[:5000]}
    Wymagania:
    - 4 do 6 par.
    - Każdy element: {{"question": "...", "answer": "..."}}
    - Pytania analityczne, unikaj tautologii, bez numeracji.
    - Odpowiedzi 1-3 zdania, konkretne.
    - Zwróć tylko listę JSON (np. [{{...}}, {{...}}]) bez dodatkowego tekstu.
    """
    ).strip()

    raw = call_gemini(prompt)
    m = re.search(r"\[[\s\S]*\]", raw)
    if not m:
        return []

# === Related Posts (v5.1) ===
def select_related_posts(current_slug: str, limit: int = 3) -> List[Dict[str,str]]:
    """Wybierz do 'limit' innych wpisów z katalogu pages/ (losowo).

    Zwraca listę dict {title, url, slug}. Pomija bieżący slug i pliki bez <h1>.
    """
    if not PAGES.exists():
        return []
    candidates: List[Dict[str,str]] = []
    for f in PAGES.glob('*.html'):
        slug = f.stem
        if slug == current_slug:
            continue
        try:
            txt = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        m = re.search(r"<h1[^>]*>(.*?)</h1>", txt)
        if not m:
            continue
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if not title:
            continue
        candidates.append({"title": title[:140], "url": f"pages/{slug}.html", "slug": slug})
    if not candidates:
        return []
    random.shuffle(candidates)
    return candidates[:limit]
    try:
        data = json.loads(m.group(0))
        faq: List[Dict[str,str]] = []
        for item in data[:6]:
            if not isinstance(item, dict):
                continue
            q = str(item.get("question", "")).strip()
            a = str(item.get("answer", "")).strip()
            if q and a:
                faq.append({"question": q[:220], "answer": a[:600]})
        return faq
    except Exception:
        return []

def load_template() -> str:
    if TEMPLATE.exists():
        try: return TEMPLATE.read_text(encoding='utf-8')
        except Exception: pass
    return ("<!DOCTYPE html><html lang='pl'><head><meta charset='utf-8'/><title>{{TYTUL}} – True Results Online</title>"
            "<meta name='description' content='{{OPIS}}'/><link rel='canonical' href='{{KANON}}'/>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'/></head><body><main>"
            "<article>{{TRESC}}</article>{{FAQ_HTML}}{{RELATED_POSTS_HTML}}"  # placeholders v5.1
            "</main></body></html>")

def build_post_html(data: Dict[str,str], slug: str, date: dt.date) -> str:
    tpl = load_template()

    # Render FAQ
    faq_items = data.get('faq') or []
    faq_html = ""
    if isinstance(faq_items, list) and faq_items:
        faq_parts = ["<section class='faq'><h2>FAQ</h2><dl>"]
        for qa in faq_items:
            if not isinstance(qa, dict):
                continue
            q = html.escape(str(qa.get('question','')).strip())
            a = html.escape(str(qa.get('answer','')).strip())
            if q and a:
                faq_parts.append(f"<dt>{q}</dt><dd>{a}</dd>")
        faq_parts.append("</dl></section>")
        faq_html = "\n".join(faq_parts)

    # Render related posts
    related = data.get('related') or []
    related_html = ""
    if isinstance(related, list) and related:
        rel_parts = ["<aside class='related'><h2>Powiązane wpisy</h2><ul>"]
        for r in related:
            if not isinstance(r, dict):
                continue
            rt = html.escape(str(r.get('title','')).strip())
            ru = html.escape(str(r.get('url','')).strip())
            if rt and ru:
                rel_parts.append(f"<li><a href='{ru}'>{rt}</a></li>")
        rel_parts.append("</ul></aside>")
        related_html = "\n".join(rel_parts)

    full_html = (tpl.replace("{{TYTUL}}", data['title'])
                    .replace("{{OPIS}}", html.escape(data['description']))
                    .replace("{{KANON}}", f"{BASE_URL}/pages/{slug}.html")
                    .replace("{{TRESC_HTML}}", data['html_content'])
                    .replace("{{TRESC}}", data['html_content'])
                    .replace("{{FAQ_HTML}}", faq_html)
                    .replace("{{RELATED_POSTS_HTML}}", related_html)
                    .replace("{{DATA}}", date.strftime('%Y-%m-%d')))
    return full_html

def insert_card(slug: str, data: Dict[str,str], date: dt.date, campaign: str) -> None:
    if not INDEX_FILE.exists(): return
    try: txt = INDEX_FILE.read_text(encoding='utf-8')
    except Exception: return
    cards = re.findall(r"<article class='post-card'[\s\S]*?</article>", txt)
    card = (f"<article class='post-card'>\n<h2><a href='pages/{slug}.html'>{html.escape(data['title'])}</a></h2>\n"
            f"<p class='meta'>{date.strftime('%Y-%m-%d')} • {html.escape(campaign)}</p>\n"
            f"<p class='desc'>{html.escape(data['description'])}</p>\n</article>")
    cards.insert(0, card); cards = cards[:MAX_INDEX_CARDS]
    block = "<!--AUTO-BLOG-->\n" + "\n".join(cards)
    if "<!--AUTO-BLOG-->" in txt:
        txt = re.sub(r"<!--AUTO-BLOG-->[\s\S]*?(</main>)", block+"\n\\1", txt, count=1)
    else:
        txt = txt.replace("</main>", block+"\n</main>", 1)
    try:
        if DRY_RUN:
            print(f"[DRY RUN] Aktualizacja index.html (sekcja AUTO-BLOG) pominięta")
        else:
            INDEX_FILE.write_text(txt, encoding='utf-8')
    except Exception: pass

def collect_posts() -> List[Dict[str,str]]:
    out: List[Dict[str,str]] = []
    for f in PAGES.glob('*.html'):
        slug = f.name[:-5]
        m = re.search(r'-(\d{8})$', slug); date_s = dt.date.today().strftime('%Y-%m-%d')
        if m: r=m.group(1); date_s=f"{r[0:4]}-{r[4:6]}-{r[6:8]}"
        try: txt = f.read_text(encoding='utf-8', errors='ignore')
        except Exception: continue
        mt = re.search(r"<h1[^>]*>(.*?)</h1>", txt)
        md = re.search(r"<meta name='description' content='(.*?)'", txt) or re.search(r'<meta name="description" content="(.*?)"', txt)
        title = mt.group(1).strip() if mt else slug
        desc = md.group(1).strip() if md else "Analiza."
        out.append({"slug": slug, "title": title, "description": desc, "date": date_s})
    out.sort(key=lambda x: x['date'], reverse=True)
    return out

def build_spis(posts: List[Dict[str,str]]) -> None:
    lines = ["<!DOCTYPE html><html lang='pl'><head><meta charset='utf-8'/><title>Spis Treści – True Results Online</title>",
             "<meta name='description' content='Pełny spis treści analiz'/>",
             f"<link rel='canonical' href='{BASE_URL}/spis.html'/></head><body><main><h1>Spis Treści</h1>"]
    for p in posts:
        lines.append(f"<article><h2><a href='pages/{p['slug']}.html'>{html.escape(p['title'])}</a></h2><p class='d'>{p['date']}</p><p>{html.escape(p['description'])}</p></article>")
    lines.append("</main></body></html>")
    try:
        if DRY_RUN:
            print("[DRY RUN] spis.html pominięty")
        else:
            SPIS_FILE.write_text("\n".join(lines), encoding='utf-8')
    except Exception: pass

def generate_rss(posts: List[Dict[str,str]]) -> None:
    import email.utils as eut
    items=[]
    for p in posts[:30]:
        pub_dt=dt.datetime.strptime(p['date'],'%Y-%m-%d')
        items.append(f"<item><title>{html.escape(p['title'])}</title><link>{BASE_URL}/pages/{p['slug']}.html</link><guid>{BASE_URL}/pages/{p['slug']}.html</guid><pubDate>{eut.format_datetime(pub_dt)}</pubDate><description>{html.escape(p['description'])}</description></item>")
    feed=("<?xml version='1.0' encoding='UTF-8'?><rss version='2.0'><channel><title>"+SITE_NAME+"</title><link>"+BASE_URL+"</link><description>Relacyjne analizy poznawcze.</description>"+"".join(items)+"</channel></rss>")
    try:
        if DRY_RUN:
            print("[DRY RUN] feed.xml pominięty")
        else:
            FEED_FILE.write_text(feed, encoding='utf-8')
    except Exception: pass

def generate_sitemap(posts: List[Dict[str,str]]) -> None:
    lines=["<?xml version='1.0' encoding='UTF-8'?>","<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>",f"  <url><loc>{BASE_URL}/</loc><priority>1.0</priority></url>"]
    if SPIS_FILE.exists(): lines.append(f"  <url><loc>{BASE_URL}/spis.html</loc><priority>0.8</priority></url>")
    for p in posts: lines.append(f"  <url><loc>{BASE_URL}/pages/{p['slug']}.html</loc><priority>0.55</priority></url>")
    lines.append("</urlset>")
    try:
        if DRY_RUN:
            print("[DRY RUN] sitemap.xml pominięty")
        else:
            SITEMAP_FILE.write_text("\n".join(lines), encoding='utf-8')
    except Exception: pass

def update_index_jsonld(posts: List[Dict[str,str]]) -> None:
    if not INDEX_FILE.exists(): return
    try: txt = INDEX_FILE.read_text(encoding='utf-8')
    except Exception: return
    data={"@context":"https://schema.org","@type":"Blog","name":SITE_NAME,
          "blogPost":[{"@type":"BlogPosting","headline":p['title'],"datePublished":p['date'],"url":f"{BASE_URL}/pages/{p['slug']}.html","description":p['description']} for p in posts[:50]]}
    block=f"<script type='application/ld+json'>{json.dumps(data,ensure_ascii=False)}</script>"
    if "application/ld+json" in txt:
        txt=re.sub(r"<script[^>]+application/ld\+json[\s\S]*?</script>",block,txt,count=1)
    else:
        txt=txt.replace("</head>",block+"\n</head>",1)
    try:
        if DRY_RUN:
            print("[DRY RUN] JSON-LD w index.html pominięty")
        else:
            INDEX_FILE.write_text(txt,encoding='utf-8')
    except Exception: pass

def git_commit_and_push(slug: str, title: str) -> None:
    if os.getenv("DISABLE_GIT","0") == "1": return
    if DRY_RUN:
        print("[DRY RUN] git commit/push pominięty")
        return
    try:
        from git import Repo  # type: ignore
        repo=Repo(ROOT)
    except Exception: return
    try:
        repo.git.add(all=True)
        if not repo.is_dirty(untracked_files=True): return
        prefix=os.getenv("GIT_COMMIT_PREFIX","[auto]")
        repo.index.commit(f"{prefix} wpis: {title} ({slug})")
        if os.getenv("GIT_PUSH","1") == "1":
            try: repo.remote(name='origin').push()
            except Exception: pass
    except Exception: pass

def create_single_post(for_date: Optional[dt.date]=None) -> dict:
    day = for_date or dt.date.today()
    topic = pick_topic(day); campaign = current_campaign(day)
    data = generate_article(topic)
    # Generate auxiliary structures (FAQ & related)
    data['faq'] = generate_faq(data['html_content'], topic)
    # related will be selected after slug is known to avoid self-reference
    slug = re.sub(r"[^a-z0-9-]","-",data['title'].lower().replace(" ","-")).strip('-')
    slug = re.sub(r"-+","-",slug) + f"-{day.strftime('%Y%m%d')}"
    data['related'] = select_related_posts(slug)
    PAGES.mkdir(exist_ok=True, parents=True)
    if DRY_RUN:
        print(f"[DRY RUN] Pominięto zapis pages/{slug}.html")
    else:
        (PAGES/f"{slug}.html").write_text(build_post_html(data,slug,day),encoding='utf-8')
    insert_card(slug,data,day,campaign)
    posts = collect_posts(); build_spis(posts); generate_rss(posts); generate_sitemap(posts); update_index_jsonld(posts)
    git_commit_and_push(slug,data['title'])  # TODO DRY_RUN
    LOG_DIR.mkdir(exist_ok=True, parents=True)
    plain = re.sub(r"<[^>]+>"," ",data['html_content'])
    wc = len([w for w in plain.split() if w.strip()])
    if DRY_RUN:
        print("[DRY RUN] Log pominięty")
    else:
        with LOG_FILE.open('a',encoding='utf-8') as f:
            f.write(f"DATA={dt.datetime.now().isoformat()} | KAMPANIA={campaign} | TEMAT={topic} | SLUG={slug} | TYTUL={data['title']} | SŁOWA={wc}\n")
    print(f"Dodano wpis: {data['title']} -> {slug}.html ({wc} słów)")
    return {"slug": slug, "title": data['title']}

def mass_regenerate(count: int) -> None:
    if count <= 0: raise SystemExit("MASS_REGENERATE > 0")
    if PAGES.exists():
        for f in PAGES.glob('*.html'):
            try: f.unlink()
            except Exception: pass
    today = dt.date.today()
    for off in range(count-1,-1,-1):
        d = today - dt.timedelta(days=off)
        try: create_single_post(d)
        except Exception as e: print(f"[MASS] Błąd dnia {d}: {e}")
    print(f"[MASS] Zakończono – {count} wpisów.")

def main():
    mass = os.getenv('MASS_REGENERATE')
    if mass:
        try: n=int(mass)
        except ValueError: raise SystemExit('MASS_REGENERATE musi być liczbą')
        return mass_regenerate(n)
    create_single_post()

if __name__ == '__main__':
    main()
