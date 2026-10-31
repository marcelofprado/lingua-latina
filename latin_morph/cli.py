"""Command line: python -m latin_morph <word> [options]"""
from __future__ import annotations

import argparse
import json
import sys

from .api import analyze, lookup, paradigm
from .render import render, render_analyses, render_paradigm


def main(argv=None):
    ap = argparse.ArgumentParser(prog="latin_morph",
                                 description="Latin paradigms, conjugations and declensions (Collatinus data).")
    ap.add_argument("word", nargs="+", help="lemma or inflected form (e.g. amo, amavisset, 'amatus est')")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--full", action="store_true",
                    help="also decline participles / comparative / superlative in full")
    ap.add_argument("--all", action="store_true", help="inflect every matching lemma, not only the best")
    ap.add_argument("--analyze", action="store_true", help="morphological analysis only (no tables)")
    ap.add_argument("--lemma", action="store_true", help="treat input strictly as a headword")
    ap.add_argument("--section", action="append",
                    help="limit tables: indicative, subjunctive, active, passive, imperative, "
                         "infinitive, participles, gerund, declension, degrees (repeatable)")
    ap.add_argument("--orth", choices=["iv", "uv", "jv"], default="iv",
                    help="spelling: iv = i/v (default), uv = u only, jv = j and v")
    ap.add_argument("--no-ext", action="store_true", help="ignore the 58k-entry extension lexicon")
    a = ap.parse_args(argv)
    word = " ".join(a.word)

    if a.analyze:
        res = analyze(word, orth=a.orth, ext=not a.no_ext)
        print(json.dumps(res, ensure_ascii=False, indent=1) if a.json
              else (render_analyses(res) or f"Unknown form '{word}'."))
        return
    if a.lemma:
        ps = paradigm(word, full=a.full, orth=a.orth)
        if not a.all:
            ps = ps[:1]
        print(json.dumps(ps, ensure_ascii=False, indent=1) if a.json
              else ("\n\n".join(render_paradigm(p) for p in ps) or f"No lemma '{word}'."))
        return
    res = lookup(word, full=a.full, all_lemmas=a.all, orth=a.orth, sections=a.section,
                 ext=not a.no_ext)
    print(json.dumps(res, ensure_ascii=False, indent=1) if a.json else render(res))


if __name__ == "__main__":
    main(sys.argv[1:])
