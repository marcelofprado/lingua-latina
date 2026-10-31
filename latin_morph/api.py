"""High-level entry points used by the CLI, the REST API and the MCP server."""
from __future__ import annotations

from .analyze import Analyzer
from .lexicon import get_lexicon
from .paradigm import Builder
from .text import key

SECTION_ALIASES = {
    "indicative": ["Indicative", "Indicative active", "Indicative passive"],
    "subjunctive": ["Subjunctive", "Subjunctive active", "Subjunctive passive"],
    "active": ["Indicative active", "Subjunctive active", "Indicative", "Subjunctive"],
    "passive": ["Indicative passive", "Subjunctive passive"],
    "imperative": ["Imperative"], "infinitive": ["Infinitive"],
    "participles": ["Participles", "Present active participle", "Perfect passive participle",
                    "Perfect participle (deponent)", "Future active participle", "Gerundive"],
    "gerund": ["Gerund & supine"], "declension": ["Declension", "Positive"],
    "degrees": ["Degrees", "Comparative", "Superlative"],
}


def lookup(word: str, full: bool = False, all_lemmas: bool = False, orth: str = "iv",
           sections: list[str] | None = None, ext: bool = True) -> dict:
    """Analyse `word` (lemma or inflected form) and return paradigm(s).

    Returns {"input", "analyses": [...], "paradigms": [...], "candidates": [...]}.
    """
    lex = get_lexicon()
    an = Analyzer(lex, orth)
    b = Builder(lex, orth)
    res = an.analyze(word, ext=ext)
    analyses = res.get("analyses", [])

    # lemmata to inflect: exact headword matches first, then analysed lemmata
    targets = []
    if " " not in word.strip():
        targets = [l for l in lex.find(word) if ext or not l.ext]
        if any(not l.ext for l in targets):
            targets = [l for l in targets if not l.ext]
    seen = {l.lid for l in targets}
    for g in analyses:
        lid = g["_lid"]
        if lid not in seen:
            targets.append(lex.lemmas[lid])
            seen.add(lid)
    if not all_lemmas:
        # keep the headword match(es) only if the word is itself a lemma;
        # otherwise the most frequent analysed lemma
        targets = targets[:1] if targets else []
    paradigms = [b.build(l, full=full) for l in targets]
    if sections:
        wanted = set()
        for s in sections:
            wanted |= set(SECTION_ALIASES.get(s.lower(), [s]))
        for p in paradigms:
            p["sections"] = [s for s in p["sections"] if s["title"] in wanted]
    shown = {p["key"] + str(p["homonym"] or "") for p in paradigms}
    candidates = []
    for g in analyses:
        sig = g["key"] + str(g["homonym"] or "")
        if sig not in shown:
            candidates.append({"lemma": g["lemma"], "pos": g["pos"], "gloss": g["gloss"],
                               "key": g["key"]})
    for g in analyses:
        g.pop("_lid", None)
    for w in res.get("words", []):
        for g in w.get("analyses", []):
            g.pop("_lid", None)
    out = {"input": word, "analyses": analyses, "paradigms": paradigms, "candidates": candidates}
    if "words" in res:
        out["words"] = res["words"]
    if not analyses and not paradigms and not res.get("words"):
        out["error"] = suggest(word)
    return out


def analyze(word: str, orth: str = "iv", ext: bool = True) -> dict:
    res = Analyzer(get_lexicon(), orth).analyze(word, ext=ext)
    for g in res.get("analyses", []):
        g.pop("_lid", None)
    return res


def paradigm(lemma: str, full: bool = False, orth: str = "iv") -> list[dict]:
    lex = get_lexicon()
    b = Builder(lex, orth)
    return [b.build(l, full=full) for l in lex.find(lemma)]


def suggest(word: str, n: int = 5) -> str:
    """Closest headwords (simple edit-distance search) for unknown input."""
    import difflib
    lex = get_lexicon()
    k = key(word)
    close = difflib.get_close_matches(k, lex.by_key.keys(), n=n, cutoff=0.75)
    if close:
        return f"Unknown form '{word}'. Did you mean: " + ", ".join(close) + "?"
    return f"Unknown form '{word}'."
