"""Reverse morphological analysis: inflected form -> lemma(s) + morphology."""
from __future__ import annotations

import os
import re

from .lexicon import DATA, Lemma, Lexicon, get_lexicon
from .text import display, key

ENCLITICS = ("que", "ne", "ue", "ve")


def _load_pairs(fname: str) -> list[tuple[str, str]]:
    out = []
    with open(os.path.join(DATA, fname), encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("!") or ":" not in line:
                continue
            a, b = line.split(":", 1)
            out.append((key(a), key(b)))
    return out


_CONTR = None
_ASSIM = None


def _contractions():
    global _CONTR
    if _CONTR is None:
        _CONTR = sorted(_load_pairs("contractions.la"), key=lambda p: -len(p[0]))
    return _CONTR


def _assims():
    global _ASSIM
    if _ASSIM is None:
        _ASSIM = _load_pairs("assimilations.la")
    return _ASSIM


class Analyzer:
    def __init__(self, lex: Lexicon | None = None, orth: str = "iv"):
        self.lex = lex or get_lexicon()
        self.orth = orth

    def _raw(self, k: str) -> list[tuple[int, int, str, str | None, int]]:
        """(lemma id, morpho, metric form, stem, numrad) for an exact key."""
        res = []
        lex = self.lex
        for i in range(0, len(k) + 1):
            r, d = k[:i], k[i:]
            if len(d) > lex.max_end:
                continue
            for lid, nr, rad in lex.rad_index.get(r, ()):
                lem = lex.lemmas[lid]
                for e in lex.end_index[lem.model].get(d, ()):
                    if e.numrad != nr or e.morpho in lem.irreg_excl:
                        continue
                    res.append((lid, e.morpho, rad + e.grq, rad, nr))
        for lid, mo, fm in lex.irreg_index.get(k, ()):
            res.append((lid, mo, fm, None, -1))
        # dedupe
        seen, out = set(), []
        for item in res:
            sig = (item[0], item[1])
            if sig in seen:
                continue
            seen.add(sig)
            out.append(item)
        return out

    def _variants(self, k: str) -> list[tuple[str, str]]:
        """Spelling variants to try when the exact form is unknown."""
        out = []
        for short, long in _contractions():
            if k.endswith(short) and len(k) > len(short):
                out.append((k[: -len(short)] + long, f"contracted form of -{long}"))
        for a, b in _assims():
            if k.startswith(b):
                out.append((a + k[len(b):], "assimilated prefix"))
            if k.startswith(a):
                out.append((b + k[len(a):], "unassimilated prefix"))
        return out

    def analyze(self, word: str, ext: bool = True) -> dict:
        word = word.strip()
        self._surface = word.lower()
        k = key(word)
        k = re.sub(r"[^a-z ]", "", k)
        if " " in k:
            return self._multi(word, k)
        hits = [(h, None, None) for h in self._raw(k)]
        if not hits:
            for v, note in self._variants(k):
                hits += [(h, None, note) for h in self._raw(v)]

        if not hits:
            for enc in ENCLITICS:
                if k.endswith(enc) and len(k) > len(enc) + 1:
                    base = k[: -len(enc)]
                    hits += [(h, enc, None) for h in self._raw(base)]
        if not ext:
            hits = [h for h in hits if not self.lex.lemmas[h[0][0]].ext]
        elif any(not self.lex.lemmas[h[0][0]].ext for h in hits):
            hits = [h for h in hits if not self.lex.lemmas[h[0][0]].ext]
        return {"input": word, "analyses": self._group(hits)}

    def _label(self, lem: Lemma, morpho: int) -> str:
        lab = self.lex.morpho_labels.get(morpho, str(morpho))
        m = self.lex.model(lem)
        if morpho == 416 and m.pos == "v":
            return "future infinitive"
        if morpho == 416:
            return "indeclinable"
        if m.is_a("imitor") and 121 <= morpho <= 266:
            lab = lab.replace(" active", "") + " (deponent)"
        if m.pos in ("p",) and 13 <= morpho <= 48:
            pass
        return lab

    def _group(self, hits) -> list[dict]:
        groups: dict[int, dict] = {}
        for (lid, mo, fm, stem, nr), enc, note in hits:
            lem = self.lex.lemmas[lid]
            g = groups.get(lid)
            if g is None:
                from .paradigm import Builder
                b = Builder(self.lex, self.orth)
                g = groups[lid] = {
                    "lemma": b.headword(lem),
                    "key": key(lem.cle), "homonym": lem.hom or None,
                    "pos": b.kind(lem), "dictionary": lem.info, "gloss": lem.gloss,
                    "frequency": lem.freq, "extended_lexicon": lem.ext, "forms": []}
                g["_lid"] = lid
            verbal = self.lex.model(lem).pos == "v"
            from .paradigm import Builder as _B
            disp = display(fm, _B(self.lex, self.orth).refs(lem) if stem is not None else None, stem=stem, keep_x=(verbal and nr == 1), orth=self.orth,
                                long_only=(verbal and nr in (1, 2)),
                                final_o_long=_B(self.lex, self.orth).final_o_long(lem))
            if note and note.startswith(("contracted", "assimilated", "unassimilated")):
                note = f"{note.split(' form')[0].split(' prefix')[0]} = {disp}"
                disp = getattr(self, "_surface", disp)
            if any(f["form"] == disp and f["morphology"] == self._label(lem, mo) for f in g["forms"]):
                continue
            g["forms"].append({
                "form": disp,
                "morphology": self._label(lem, mo), "morpho_id": mo,
                **({"enclitic": "-" + enc} if enc else {}),
                **({"note": note} if note else {})})
        out = sorted(groups.values(), key=lambda g: (g["extended_lexicon"], -g["frequency"]))
        for g in out:
            g["forms"].sort(key=lambda f: f["morpho_id"])
        return out

    # ------------------------------------------------------------ periphrastic
    AUX = {
        "sum": ("present", "1st singular"), "es": ("present", "2nd singular"), "est": ("present", "3rd singular"),
        "sumus": ("present", "1st plural"), "estis": ("present", "2nd plural"), "sunt": ("present", "3rd plural"),
        "eram": ("imperfect", "1st singular"), "eras": ("imperfect", "2nd singular"), "erat": ("imperfect", "3rd singular"),
        "eramus": ("imperfect", "1st plural"), "eratis": ("imperfect", "2nd plural"), "erant": ("imperfect", "3rd plural"),
        "ero": ("future", "1st singular"), "eris": ("future", "2nd singular"), "erit": ("future", "3rd singular"),
        "erimus": ("future", "1st plural"), "eritis": ("future", "2nd plural"), "erunt": ("future", "3rd plural"),
        "sim": ("psubj", "1st singular"), "sis": ("psubj", "2nd singular"), "sit": ("psubj", "3rd singular"),
        "simus": ("psubj", "1st plural"), "sitis": ("psubj", "2nd plural"), "sint": ("psubj", "3rd plural"),
        "essem": ("isubj", "1st singular"), "esses": ("isubj", "2nd singular"), "esset": ("isubj", "3rd singular"),
        "essemus": ("isubj", "1st plural"), "essetis": ("isubj", "2nd plural"), "essent": ("isubj", "3rd plural"),
        "esse": ("inf", ""), "iri": ("iri", ""),
    }
    TENSE = {"present": "perfect indicative", "imperfect": "pluperfect indicative",
             "future": "future perfect indicative", "psubj": "perfect subjunctive",
             "isubj": "pluperfect subjunctive"}

    def _multi(self, word: str, k: str) -> dict:
        toks = k.split()
        if len(toks) == 2 and toks[1] in self.AUX:
            part, aux = toks
            tense, person = self.AUX[aux]
            res = []
            for lid, mo, fm, stem, nr in self._raw(part):
                lem = self.lex.lemmas[lid]
                dep = self.lex.model(lem).is_a("imitor")
                lab = None
                if tense == "iri" and mo == 265:
                    lab = "future infinitive passive"
                elif tense == "inf" and (303 <= mo <= 338 or 375 <= mo <= 410):
                    lab = "perfect infinitive " + ("(deponent)" if dep or mo >= 375 else "passive")
                elif tense == "inf" and 225 <= mo <= 260:
                    lab = "future infinitive active"
                elif tense not in ("inf", "iri") and (303 <= mo <= 338 or 375 <= mo <= 410):
                    sg = self.lex.morpho_labels.get(mo, "")
                    nom = "nominative" in sg
                    plural_ok = ("plural" in sg) == ("plural" in person)
                    if nom and plural_ok:
                        voice = "(deponent)" if (dep or mo >= 375) else "passive"
                        g = re.search(r"(masculine|feminine|neuter)", sg)
                        lab = f"{self.TENSE[tense]} {voice} {person}" + (f" ({g.group(1)})" if g else "")
                if lab:
                    res.append(((lid, mo, fm + " " + aux, stem, nr), None, None))
                    res[-1] = ((lid, mo, fm, stem, nr), None, lab)
            groups = self._group(res)
            for g in groups:
                seen, forms = set(), []
                for f in g["forms"]:
                    f["morphology"] = f.pop("note")
                    f["form"] = f["form"] + " " + toks[1]
                    if (f["form"], f["morphology"]) in seen:
                        continue
                    seen.add((f["form"], f["morphology"]))
                    forms.append(f)
                g["forms"] = forms
            if groups:
                return {"input": word, "analyses": groups}
        # fall back: analyse each word
        return {"input": word, "analyses": [], "words": [self.analyze(t) for t in toks]}
