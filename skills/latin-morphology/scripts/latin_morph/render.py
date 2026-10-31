"""Markdown rendering of lookup results (concise, table-first)."""
from __future__ import annotations


def _table(sec: dict) -> str:
    cols = sec["columns"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in sec["rows"]:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines)


def _head(p: dict) -> str:
    bits = [p["pos"]]
    if p.get("class") and p["class"] not in (p["pos"],):
        bits.append(p["class"])
    meta = " · ".join(bits)
    gloss = p.get("gloss") or ""
    if len(gloss) > 140:
        gloss = gloss[:137].rsplit(" ", 1)[0] + "…"
    s = f"## {p.get('principal_parts') or p['lemma']}\n*{meta}*"
    if gloss:
        s += f" — {gloss}"
    if p.get("note"):
        s += f"\n\n> {p['note']}"
    return s


def render_paradigm(p: dict) -> str:
    parts = [_head(p)]
    for sec in p["sections"]:
        parts.append(f"**{sec['title']}**\n\n" + _table(sec))
    return "\n\n".join(parts)


ABBR = [("participle", "ptcp."), ("perfect", "perf."), ("pluperfect", "plupf."),
        ("imperfect", "impf."), ("present", "pres."), ("future", "fut."),
        ("indicative", "ind."), ("subjunctive", "subj."), ("imperative", "imper."),
        ("infinitive", "inf."), ("active", "act."), ("passive", "pass."),
        ("nominative", "nom."), ("vocative", "voc."), ("accusative", "acc."),
        ("genitive", "gen."), ("dative", "dat."), ("ablative", "abl."), ("locative", "loc."),
        ("singular", "sg."), ("plural", "pl."), ("masculine", "m."), ("feminine", "f."),
        ("neuter", "n."), ("comparative", "comp."), ("superlative", "superl."),
        ("gerundive", "gerundive"), ("1st", "1"), ("2nd", "2"), ("3rd", "3")]


def abbreviate(label: str) -> str:
    import re
    out = label
    for a, b in ABBR:
        out = re.sub(rf"\b{a}\b", b, out)
    return out.replace("plu" + "perf.", "plupf.")


def render_analyses(res: dict) -> str:
    if not res.get("analyses"):
        return ""
    rows: list[list[str]] = []
    index: dict[tuple, int] = {}
    for g in res["analyses"]:
        lemma = g["lemma"] + (f" ({g['homonym']})" if g.get("homonym") else "")
        gloss = (g.get("gloss") or "").split(";")[0].split(",")[0][:40]
        for f in g["forms"]:
            lab = abbreviate(f["morphology"])
            if f.get("enclitic"):
                lab += f" + {f['enclitic']}"
            if f.get("note"):
                lab += f" ({f['note']})"
            sig = (f["form"], lemma)
            if sig in index:
                rows[index[sig]][3] += "; " + lab
            else:
                index[sig] = len(rows)
                rows.append([f["form"], lemma, g["pos"] + (f" — {gloss}" if gloss else ""), lab])
    t = {"columns": ["Form", "Lemma", "Meaning", "Analysis"], "rows": rows}
    return f"**Analysis of _{res['input']}_**\n\n" + _table(t)


def render(result: dict) -> str:
    from .text import key
    out = []
    if result.get("error"):
        return result["error"]
    ana = result.get("analyses", [])
    headword = any(p["key"].rstrip("0123456789") == key(result["input"])
                   for p in result.get("paradigms", []))
    if ana and not headword:
        out.append(render_analyses(result))
    for w in result.get("words", []):
        r = render_analyses(w)
        if r:
            out.append(r)
    for p in result.get("paradigms", []):
        out.append(render_paradigm(p))
    cands = [c for c in result.get("candidates", []) if c.get("gloss")]
    if cands:
        out.append("*Also:* " + "; ".join(
            f"{c['lemma']} ({c['pos']}, {c['gloss'].split(';')[0][:50]})" for c in cands))
    return "\n\n".join(x for x in out if x)
