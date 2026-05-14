# Manideep Sai C
# Reg.no 23BCE0737

import spacy
import wikipediaapi
from ddgs import DDGS
import requests
import re
from collections import Counter
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed

nlp = spacy.load("en_core_web_sm")
wiki = wikipediaapi.Wikipedia(user_agent="SyntaxQA/2025", language="en", extract_format=wikipediaapi.ExtractFormat.WIKI)
BLACKLIST = {"san francisco", "wikipedia", "article", "city", "country", "capital"}

YEAR_PATTERN = re.compile(r"\d{4}")
CAPITAL_PATTERNS = [
    re.compile(r'capital(?: city)? of [A-Z][a-z]+ (?:is|,)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'),
    re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*) is the capital of [A-Z][a-z]+')
]
CLEAN_PATTERN = re.compile(r"[^A-Za-z0-9.,\- ]")

@lru_cache(maxsize=128)
def focus(q):
    d = nlp(q)
    for t in d:
        if t.dep_ in ("dobj", "pobj", "attr", "nsubj"):
            for n in d.noun_chunks:
                if n.start <= t.i < n.end:
                    return n.text
            return t.text
    c = list(d.noun_chunks)
    return c[-1].text if c else q

def wiki_titles(q):
    try:
        r = requests.get("https://api.wikimedia.org/core/v1/wikipedia/en/search/page",
                         params={"q": q, "limit": 3}, timeout=5,
                         headers={"User-Agent": "SyntaxQA/2025"})
        r.raise_for_status()
        return [p["title"] for p in r.json().get("pages", [])]
    except Exception:
        return []

def fetch_wiki_page(title):
    try:
        p = wiki.page(title)
        if p.exists() and p.summary:
            return p.summary[:1500]
    except Exception:
        pass
    return None

def wiki_texts(q):
    titles = wiki_titles(q)
    if not titles:
        return []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(fetch_wiki_page, t) for t in titles]
        return [f.result() for f in as_completed(futures) if f.result()]

def duck_texts(q):
    res = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(q, max_results=5):
                b = r.get("body") or r.get("text") or r.get("title") or ""
                if b:
                    res.append(b[:1000])
    except Exception:
        pass
    return res

def extract(txts, typ, cues=None):
    c = []
    ql_cues = set(cues) if cues else None
    
    for x in txts:
        d = nlp(x)
        for s in d.sents:
            s_lower = s.text.lower()
            if ql_cues and not any(v in s_lower for v in ql_cues):
                continue
            
            for e in s.ents:
                if typ == "PERSON" and e.label_ == "PERSON":
                    word_count = len(e.text.split())
                    if 1 < word_count <= 3:
                        c.append(e.text)
                elif typ == "DATE" and e.label_ == "DATE":
                    if YEAR_PATTERN.search(e.text):
                        c.append(e.text)
                elif typ == "GPE" and e.label_ == "GPE":
                    v = e.text.strip()
                    if v.lower() not in BLACKLIST:
                        c.append(v)
                elif typ == "NUMBER" and e.label_ in ("CARDINAL", "QUANTITY", "PERCENT"):
                    c.append(e.text)
                elif typ == "LOCATION" and e.label_ in ("GPE", "LOC", "FAC"):
                    v = e.text.strip()
                    if v.lower() not in BLACKLIST:
                        c.append(v)
    return c

def extract_capital(txts, q):
    allc = []
    q_lower = q.lower()
    
    for t in txts:
        for p in CAPITAL_PATTERNS:
            m = p.search(t)
            if m:
                v = m.group(1).strip()
                if v.lower() not in q_lower and v.lower() not in BLACKLIST:
                    allc.append(v)
    
    if not allc:
        g = extract(txts, "GPE")
        allc = [v for v in g if v.lower() not in q_lower and v.lower() not in BLACKLIST]
    
    if allc:
        a, _ = Counter(allc).most_common(1)[0]
        return a
    return ""

def clean(a):
    if not a:
        return ""
    a = CLEAN_PATTERN.sub("", a).strip()
    words = a.split()
    if len(words) > 3:
        a = " ".join(words[:3])
    return a

def determine_tag(q):
    ql = q.lower()
    if ql.startswith("who"):
        return "PERSON"
    elif "capital" in ql:
        return "PLACE"
    elif ql.startswith("when"):
        return "DATE"
    elif ql.startswith("where") or "located" in ql:
        return "LOCATION"
    elif ql.startswith("how many") or ql.startswith("how much") or "percentage" in ql:
        return "NUMBER"
    return None

def process(q, tag):
    f = focus(q)
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        wiki_future = executor.submit(wiki_texts, f)
        duck_future = executor.submit(duck_texts, q)
        w = wiki_future.result()
        d = duck_future.result()
    
    alltxt = w + d
    if not alltxt:
        return ""
    
    ql = q.lower()
    c = []
    
    if tag == "PERSON":
        c = extract(alltxt, "PERSON", {"discovered", "invented", "created", "developed", "founded"})
    elif tag == "PLACE":
        return clean(extract_capital(alltxt, q))
    elif tag == "DATE":
        c = extract(alltxt, "DATE", {"founded", "established", "created", "launched", "started"})
    elif tag == "LOCATION":
        c = extract(alltxt, "LOCATION", {"located", "situated", "found in", "based in"})
    elif tag == "NUMBER":
        c = extract(alltxt, "NUMBER")
    
    if not c:
        c = extract(alltxt, "PERSON") or extract(alltxt, "GPE") or extract(alltxt, "DATE")
    
    if c:
        occ = Counter([x for x in c if x.lower() not in ql and x.lower() not in BLACKLIST])
        if occ:
            a, _ = occ.most_common(1)[0]
            return clean(a)
    return ""


if __name__ == "__main__":
    with open("questions.txt", "r", encoding="utf-8") as f:
        data = [line.strip() for line in f if line.strip()]
    
    results = []
    for i, item in enumerate(data, 1):
        tag = determine_tag(item)
        
        if tag:
            output = process(item, tag)
            print(f"Question {i}: {item}")
            print(f"Tag: {tag}")
            print(f"Result: {output}")
            results.append(f"Question {i}: {output} ({tag})")
    
    with open("answers.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(results))
