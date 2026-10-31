"""Build complete, structured paradigms (declension / conjugation tables)."""
from __future__ import annotations

import re

from .lexicon import Lemma, Lexicon, get_lexicon
from .text import display, key

CASES = [("Nom.", 0), ("Gen.", 3), ("Dat.", 4), ("Acc.", 2), ("Abl.", 5), ("Voc.", 1)]
PERSONS = ["1st sg.", "2nd sg.", "3rd sg.", "1st pl.", "2nd pl.", "3rd pl."]

SUM = {
    "pres": ["sum", "es", "est", "sumus", "estis", "sunt"],
    "impf": ["eram", "erās", "erat", "erāmus", "erātis", "erant"],
    "fut": ["erō", "eris", "erit", "erimus", "eritis", "erunt"],
    "spres": ["sim", "sīs", "sit", "sīmus", "sītis", "sint"],
    "simpf": ["essem", "essēs", "esset", "essēmus", "essētis", "essent"],
}

VERB_CLASSES = [
    ("sum", "irregular (sum)"), ("possum", "irregular (possum)"), ("prosum", "irregular (prōsum)"),
    ("absum", "irregular (sum compound)"), ("fero", "irregular (ferō)"), ("eo", "irregular (eō)"),
    ("uolo", "irregular (volō)"), ("nolo", "irregular (nōlō)"), ("malo", "irregular (mālō)"),
    ("edo", "irregular (edō)"), ("fio", "irregular (fīō)"), ("aio", "defective (aiō)"),
    ("patior", "3rd conjugation -iō, deponent"), ("potior", "4th conjugation, deponent"),
    ("sequor", "3rd conjugation, deponent"), ("uereor", "2nd conjugation, deponent"),
    ("imitor", "1st conjugation, deponent"),
    ("audio", "4th conjugation"), ("capio", "3rd conjugation -iō"), ("lego", "3rd conjugation"),
    ("licet", "2nd conjugation, impersonal"), ("moneo", "2nd conjugation"),
    ("do", "1st conjugation (dō: short a)"), ("amo", "1st conjugation"),
]
NOUN_CLASSES = [
    ("uita", "1st declension"), ("lupus", "2nd declension"), ("templum", "2nd declension"),
    ("ciuis", "3rd declension (i-stem)"), ("mare", "3rd declension (neuter i-stem)"),
    ("miles", "3rd declension"), ("domus", "4th/2nd declension (mixed)"),
    ("manus", "4th declension"), ("res", "5th declension"),
]
ADJ_CLASSES = [("fortis", "3rd declension"), ("doctus", "1st/2nd declension")]
GENDERS = {"m": "masculine", "f": "feminine", "n": "neuter"}


class Builder:
    def __init__(self, lex: Lexicon | None = None, orth: str = "iv"):
        self.lex = lex or get_lexicon()
        self.orth = orth

    # ------------------------------------------------------------ forms
    SHORT_O = {"ego", "duo", "ambo", "modo", "cito", "octo", "ergo", "quomodo", "immo", "illico"}

    def final_o_long(self, lem: Lemma) -> bool:
        """Common final -ŏ/-ō: long in verbs (amō) and nouns (homō); short in
        ego, duo, modo... (pronouns, numerals, adverbs)."""
        return self.lex.model(lem).pos not in ("p", "d", "m") and key(lem.cle) not in self.SHORT_O

    def headword(self, lem: Lemma) -> str:
        """Dictionary form with natural quantities (generated, so amō not amo)."""
        k = self.kind(lem)
        order = {"verb": (121, 139, 123), "noun": (1, 7), "adjective": (13, 19, 37),
                 "pronoun": (13, 25, 37, 19, 15), "adverb": (414,)}.get(k, ())
        target = key(lem.grq.split(",")[0])
        for mo in order:
            for fm in self.f(lem, mo, rare=False):
                if key(fm) == target:
                    return fm
        return display(lem.grq.split(",")[0], self.refs(lem), orth=self.orth,
                       final_o_long=self.final_o_long(lem))

    def refs(self, lem: Lemma) -> list[str]:
        """Natural-quantity references: the lemma, plus (nouns/3rd-decl.
        adjectives) the oblique stem in an open syllable (rēx ← rēg-is)."""
        r = [lem.natural]
        m = self.lex.model(lem)
        if (m.pos == "n" or m.is_a("fortis")) and lem.radicals.get(1):
            r.append(display(lem.radicals[1][0] + "is"))
        return r

    def f(self, lem: Lemma, morpho: int, rare: bool = True) -> list[str]:
        out = []
        verbal = self.lex.model(lem).pos == "v"
        refs = self.refs(lem)
        for fm, rar, stem, nr in self.lex.forms_detail(lem, morpho):
            d = display(fm, refs if stem is not None else None, stem=stem, keep_x=(verbal and nr == 1), orth=self.orth,
                        long_only=(verbal and nr in (1, 2)), final_o_long=self.final_o_long(lem))
            if rar <= 3:
                if not rare:
                    continue
                d = f"({d})"
            if d not in out:
                out.append(d)
        return out

    def cell(self, lem: Lemma, morpho: int) -> str:
        return ", ".join(self.f(lem, morpho)) or "—"

    def first(self, lem: Lemma, morpho: int) -> str | None:
        fs = self.f(lem, morpho, rare=False)
        return fs[0] if fs else None

    # ------------------------------------------------------------ classify
    def kind(self, lem: Lemma) -> str:
        m = self.lex.model(lem)
        if m.name == "inv":
            return "invariable"
        p = m.pos
        if p == "v":
            return "verb"
        if p == "n":
            return "noun"
        if "p" in lem.pos[:1] or m.is_a("ipse"):
            return "pronoun"
        if p in ("a", "m"):
            return "adjective"
        if p == "p":
            return "pronoun"
        if p == "d":
            return "adverb"
        return "invariable"

    def verb_class(self, lem: Lemma) -> str:
        table = dict(VERB_CLASSES)
        for name in self.lex.model(lem).ancestry():
            if name in table:
                return table[name]
        return "verb"

    def deponent(self, lem: Lemma) -> bool:
        return self.lex.model(lem).is_a("imitor")

    def semideponent(self, lem: Lemma) -> bool:
        return (not self.deponent(lem) and bool(re.search(r"\w+us sum\b", lem.info))
                and 1 not in lem.explicit)

    def perfect_only(self, lem: Lemma) -> bool:
        nat = key(lem.natural)
        if key(lem.cle) in ("coepio",):
            return True
        return (self.kind(lem) == "verb" and nat.endswith("i") and 1 in lem.radicals
                and not self.deponent(lem))

    def gender(self, lem: Lemma) -> str:
        info = " " + lem.info + " "
        g = []
        for tag, name in ((" m.", "m"), (" f.", "f"), (" n.", "n")):
            if tag in info:
                g.append(name)
        return "/".join(g)

    # ------------------------------------------------------------ entry
    def build(self, lem: Lemma, full: bool = False) -> dict:
        k = self.kind(lem)
        out = {
            "lemma": self.headword(lem),
            "key": key(lem.cle),
            "homonym": lem.hom or None,
            "pos": k,
            "model": lem.model,
            "dictionary": lem.info,
            "gloss": lem.gloss,
            "frequency": lem.freq,
            "extended_lexicon": lem.ext,
            "sections": [],
        }
        if k == "verb":
            self._verb(lem, out, full)
        elif k == "noun":
            self._noun(lem, out)
        elif k == "adjective":
            self._adjective(lem, out, full)
        elif k == "pronoun":
            self._pronoun(lem, out)
        elif k == "adverb":
            self._adverb(lem, out)
        else:
            out["class"] = "indeclinable"
            out["principal_parts"] = out["lemma"]
        return out

    # ------------------------------------------------------------ nouns
    def _case_table(self, lem: Lemma, base: int, title: str) -> dict | None:
        rows = []
        sg_any = pl_any = False
        for label, off in CASES:
            sg = self.cell(lem, base + off)
            pl = self.cell(lem, base + 6 + off)
            sg_any |= sg != "—"
            pl_any |= pl != "—"
            rows.append([label, sg, pl])
        loc = self.f(lem, 413)
        if loc:
            rows.append(["Loc.", ", ".join(loc), "—"])
        if not sg_any and not pl_any:
            return None
        cols = ["Case", "Singular", "Plural"]
        if not pl_any:
            cols = ["Case", "Singular"]
            rows = [r[:2] for r in rows]
        elif not sg_any:
            cols = ["Case", "Plural"]
            rows = [[r[0], r[2]] for r in rows]
        return {"title": title, "columns": cols, "rows": rows}

    def _noun(self, lem: Lemma, out: dict):
        anc = self.lex.model(lem).ancestry()
        cls = next((lab for n, lab in NOUN_CLASSES if n in anc), "irregular / Greek")
        g = self.gender(lem)
        out["class"] = cls
        out["gender"] = g
        nom = self.first(lem, 1) or self.first(lem, 7)
        gen = self.first(lem, 4) or self.first(lem, 10)
        out["principal_parts"] = ", ".join(x for x in (nom, gen) if x) + (f", {g}." if g else "")
        t = self._case_table(lem, 1, "Declension")
        if t:
            out["sections"].append(t)

    # ------------------------------------------------------------ adjectives & pronouns
    def _gender_table(self, lem: Lemma, base: int, title: str) -> dict | None:
        """base = first morpho of masc. nom. sg. (13, 49, 85, 189, 225, 303, 339, 375)."""
        cols_spec = []
        for num_label, num_off in (("sg.", 0), ("pl.", 6)):
            for g_label, g_off in (("M", 0), ("F", 12), ("N", 24)):
                cols_spec.append((f"{g_label} {num_label}", g_off + num_off))
        grid = {c: [self.cell(lem, base + off + co) for _l, co in CASES] for c, off in cols_spec}
        # drop empty columns
        grid = {c: v for c, v in grid.items() if any(x != "—" for x in v)}
        if not grid:
            return None
        keep_rows = [i for i in range(len(CASES)) if any(v[i] != "—" for v in grid.values())]
        # merge identical gender columns within a number (M/F, M/F/N)
        merged: dict[str, list[str]] = {}
        for num in ("sg.", "pl."):
            cols = [(c, v) for c, v in grid.items() if c.endswith(num)]
            while cols:
                c, v = cols.pop(0)
                same = [c2 for c2, v2 in cols if v2 == v]
                cols = [(c2, v2) for c2, v2 in cols if v2 != v]
                if same:
                    gs = "/".join([c.split()[0]] + [s.split()[0] for s in same])
                    merged[f"{gs} {num}"] = v
                else:
                    merged[c] = v
        columns = ["Case"] + list(merged)
        rows = [[CASES[i][0]] + [merged[c][i] for c in merged] for i in keep_rows]
        return {"title": title, "columns": columns, "rows": rows}

    def _three(self, lem: Lemma, base: int, full_forms: bool = False) -> str | None:
        """Compact 'bonus, -a, -um' / 'fortis, -e' / 'ingēns, gen. ingentis'."""
        m, f_, n = self.first(lem, base), self.first(lem, base + 12), self.first(lem, base + 24)
        if not m:
            return n or f_
        forms = [x for x in (m, f_, n) if x]
        distinct = []
        for x in forms:
            if x not in distinct:
                distinct.append(x)
        if len(distinct) == 1:
            gen = self.first(lem, base + 3)
            return f"{m}, gen. {gen}" if gen and gen != m else m
        pre = 0
        while all(pre < len(x) for x in distinct) and len({x[pre] for x in distinct}) == 1:
            pre += 1
        if full_forms or pre < 2:
            return ", ".join(distinct)
        return ", ".join([m] + ["-" + x[pre:] for x in distinct[1:]])

    def _adjective(self, lem: Lemma, out: dict, full: bool):
        anc = self.lex.model(lem).ancestry()
        out["class"] = next((lab for n, lab in ADJ_CLASSES if n in anc), "irregular")
        out["principal_parts"] = self._three(lem, 13) or out["lemma"]
        t = self._gender_table(lem, 13, "Positive")
        if t:
            out["sections"].append(t)
        comp = self._three(lem, 49)
        sup = self._three(lem, 85)
        degrees = []
        if comp:
            degrees.append(["Comparative", comp])
        if sup:
            degrees.append(["Superlative", sup])
        adv = self._find_adverb(lem)
        irr = self.ADV_IRREG.get(key(lem.cle))
        if irr:
            degrees.append(["Adverb", irr if self.orth != "uv" else irr.replace("v", "u")])
        elif adv:
            degrees.append(["Adverb", " · ".join(x for x in (
                self.cell(adv, 414), self.cell(adv, 411), self.cell(adv, 412)) if x != "—")])
        if degrees:
            out["sections"].append({"title": "Degrees", "columns": ["Degree", "Forms"], "rows": degrees})
        if full:
            for base, title in ((49, "Comparative"), (85, "Superlative")):
                t = self._gender_table(lem, base, title)
                if t:
                    out["sections"].append(t)

    ADV_MODELS = {"adve", "advr", "fortiter", "acriter", "misere", "humiliter", "facile"}
    ADV_IRREG = {"bonus": "bene · melius · optimē", "malus": "male · peius · pessimē",
                 "paruus": "parum · minus · minimē", "multus": "multum · plūs · plūrimum",
                 "magnus": "magnopere · magis · maximē", "facilis": "facile · facilius · facillimē"}

    def _find_adverb(self, lem: Lemma) -> Lemma | None:
        r0 = lem.radicals.get(0, [])
        if not r0:
            return None
        stem = key(r0[0])
        for suffix in ("e", "iter", "ter", "er", "e2"):
            for lid in self.lex.by_key.get(stem + suffix, []):
                cand = self.lex.lemmas[lid]
                if cand.model in self.ADV_MODELS:
                    return cand
        return None

    def _pronoun(self, lem: Lemma, out: dict):
        out["class"] = "pronoun"
        out["principal_parts"] = self._three(lem, 13, full_forms=True) or out["lemma"]
        t = self._gender_table(lem, 13, "Declension")
        if t:
            out["sections"].append(t)

    def _adverb(self, lem: Lemma, out: dict):
        out["class"] = "adverb"
        rows = []
        for lab, mo in (("Positive", 414), ("Comparative", 411), ("Superlative", 412)):
            c = self.cell(lem, mo)
            if c != "—":
                rows.append([lab, c])
        out["principal_parts"] = " · ".join(r[1] for r in rows) or out["lemma"]
        if len(rows) > 1:
            out["sections"].append({"title": "Degrees", "columns": ["Degree", "Form"], "rows": rows})

    # ------------------------------------------------------------ verbs
    def _compound(self, part_sg: str | None, part_pl: str | None, aux: list[str]) -> list[str]:
        if not part_sg:
            return ["—"] * 6
        pl = part_pl or part_sg
        return [f"{part_sg if i < 3 else pl} {a}" for i, a in enumerate(aux)]

    def _tense_table(self, title: str, cols: list[tuple[str, list[str]]]) -> dict | None:
        cols = [(c, v) for c, v in cols if any(x != "—" for x in v)]
        if not cols:
            return None
        rows = [[PERSONS[i]] + [v[i] for _c, v in cols] for i in range(6)]
        rows = [r for r in rows if any(x != "—" for x in r[1:])]
        return {"title": title, "columns": ["Person"] + [c for c, _ in cols], "rows": rows}

    def _cells(self, lem: Lemma, start: int) -> list[str]:
        return [self.cell(lem, start + i) for i in range(6)]

    def _verb(self, lem: Lemma, out: dict, full: bool):
        dep = self.deponent(lem)
        semi = self.semideponent(lem)
        perf_only = self.perfect_only(lem)
        out["class"] = self.verb_class(lem) + (", semi-deponent" if semi else "") + \
            (", defective (perfect system only)" if perf_only else "")
        out["voice"] = "deponent" if dep else ("semi-deponent" if semi else "active/passive")

        # participle bases
        ppp_m, ppp_mpl = self.first(lem, 303), self.first(lem, 309)
        ppa_m, ppa_mpl = self.first(lem, 375), self.first(lem, 381)   # deponent perfect
        perf_part = (ppa_m, ppa_mpl) if dep else (ppp_m, ppp_mpl)
        fap_acc = self.first(lem, 227)
        sup = self.first(lem, 265)

        # principal parts
        pres1 = self.first(lem, 121)
        inf = self.first(lem, 187)
        perf1 = self.first(lem, 139)
        pp = [x for x in (pres1, inf) if x and not perf_only]
        if dep or semi:
            if perf_part[0]:
                pp.append(f"{perf_part[0]} sum")
        else:
            if perf1:
                pp.append(perf1)
            if sup:
                pp.append(sup)
            elif ppp_m:
                pp.append(ppp_m)
            elif self.first(lem, 225):
                pp.append(self.first(lem, 225))
        if perf_only:
            pp = [x for x in (perf1, self.first(lem, 188)) if x]
            if sup or ppp_m:
                pp.append(sup or ppp_m)
        out["principal_parts"] = ", ".join(pp) or out["lemma"]

        S = out["sections"]
        empty = ["—"] * 6
        has_pass = (not dep and not semi and not perf_only and
                    (any(self.lex.has(lem, m) for m in range(267, 302)) or bool(ppp_m)))
        act = " active" if has_pass else ""
        # ---------------- active (or deponent) finite forms
        a_title = "Indicative" + act
        if dep:
            perf = self._compound(*perf_part, SUM["pres"])
            plpf = self._compound(*perf_part, SUM["impf"])
            fpf = self._compound(*perf_part, SUM["fut"])
        elif semi:
            perf = self._compound(ppp_m, ppp_mpl, SUM["pres"])
            plpf = self._compound(ppp_m, ppp_mpl, SUM["impf"])
            fpf = self._compound(ppp_m, ppp_mpl, SUM["fut"])
        else:
            perf, plpf, fpf = self._cells(lem, 139), self._cells(lem, 145), self._cells(lem, 151)
        pres_sys = not perf_only
        t = self._tense_table(a_title, [
            ("Present", self._cells(lem, 121) if pres_sys else empty),
            ("Imperfect", self._cells(lem, 127) if pres_sys else empty),
            ("Future", self._cells(lem, 133) if pres_sys else empty),
            ("Perfect", perf), ("Pluperfect", plpf), ("Future perfect", fpf)])
        if t:
            S.append(t)
        if dep:
            sperf = self._compound(*perf_part, SUM["spres"])
            splpf = self._compound(*perf_part, SUM["simpf"])
        elif semi:
            sperf = self._compound(ppp_m, ppp_mpl, SUM["spres"])
            splpf = self._compound(ppp_m, ppp_mpl, SUM["simpf"])
        else:
            sperf, splpf = self._cells(lem, 169), self._cells(lem, 175)
        t = self._tense_table("Subjunctive" + act, [
            ("Present", self._cells(lem, 157) if pres_sys else empty),
            ("Imperfect", self._cells(lem, 163) if pres_sys else empty),
            ("Perfect", sperf), ("Pluperfect", splpf)])
        if t:
            S.append(t)

        # ---------------- passive
        if has_pass:
            pperf = self._compound(ppp_m, ppp_mpl, SUM["pres"]) if not semi else empty
            pplpf = self._compound(ppp_m, ppp_mpl, SUM["impf"]) if not semi else empty
            pfpf = self._compound(ppp_m, ppp_mpl, SUM["fut"]) if not semi else empty
            if True:
                t = self._tense_table("Indicative passive", [
                    ("Present", self._cells(lem, 267)), ("Imperfect", self._cells(lem, 273)),
                    ("Future", self._cells(lem, 279)), ("Perfect", pperf),
                    ("Pluperfect", pplpf), ("Future perfect", pfpf)])
                if t:
                    S.append(t)
                t = self._tense_table("Subjunctive passive", [
                    ("Present", self._cells(lem, 285)), ("Imperfect", self._cells(lem, 291)),
                    ("Perfect", self._compound(ppp_m, ppp_mpl, SUM["spres"]) if not semi else empty),
                    ("Pluperfect", self._compound(ppp_m, ppp_mpl, SUM["simpf"]) if not semi else empty)])
                if t:
                    S.append(t)

        # ---------------- imperative
        if not perf_only:
            rows = []
            act_i = {"2nd sg.": (181, 183), "3rd sg.": (None, 184), "2nd pl.": (182, 185), "3rd pl.": (None, 186)}
            if dep:   # deponent future imperative lives in the passive slots (299-301)
                act_i = {"2nd sg.": (181, 299), "3rd sg.": (None, 300), "2nd pl.": (182, None), "3rd pl.": (None, 301)}
            pas = {"2nd sg.": (297, 299), "3rd sg.": (None, 300), "2nd pl.": (298, None), "3rd pl.": (None, 301)}
            for p in ("2nd sg.", "3rd sg.", "2nd pl.", "3rd pl."):
                r = [p]
                for (a, b) in (act_i[p],) + ((pas[p],) if has_pass else ()):
                    r.append(self.cell(lem, a) if a else "—")
                    r.append(self.cell(lem, b) if b else "—")
                rows.append(r)
            cols = ["Person", "Present", "Future"] if not has_pass else \
                ["Person", "Present act.", "Future act.", "Present pass.", "Future pass."]
            # drop empty columns
            keep = [0] + [i for i in range(1, len(cols)) if any(r[i] != "—" for r in rows)]
            if len(keep) > 1:
                S.append({"title": "Imperative", "columns": [cols[i] for i in keep],
                          "rows": [[r[i] for i in keep] for r in rows if any(r[i] != "—" for i in keep[1:])]})
            # memento-type (memini): future imperative only, handled above via irregs
        elif self.lex.has(lem, 183):
            S.append({"title": "Imperative", "columns": ["Person", "Future"],
                      "rows": [r for r in (["2nd sg.", self.cell(lem, 183)], ["2nd pl.", self.cell(lem, 185)])
                               if r[1] != "—"]})

        # ---------------- infinitives
        def esse(x):
            return f"{x} esse" if x else "—"
        fut_act = esse(fap_acc) if fap_acc else (self.cell(lem, 416) if self.lex.has(lem, 416) else "—")
        if self.lex.has(lem, 416) and fap_acc:
            fut_act = f"{esse(fap_acc)}, {self.cell(lem, 416)}"
        if dep:
            inf_rows = [["Present", self.cell(lem, 187)],
                        ["Perfect", esse(self.first(lem, 377))],
                        ["Future", fut_act]]
            inf_cols = ["Tense", "Infinitive"]
        else:
            ppp_acc = self.first(lem, 305)
            p_perf = esse(ppp_acc) if not semi else "—"
            a_perf = self.cell(lem, 188) if not semi else esse(ppp_acc)
            inf_rows = [["Present", self.cell(lem, 187) if pres_sys else "—", self.cell(lem, 302)],
                        ["Perfect", a_perf, p_perf],
                        ["Future", fut_act, f"{sup} īrī" if sup and not semi else "—"]]
            inf_cols = ["Tense", "Active", "Passive"]
            if not has_pass:
                for r in inf_rows:
                    r[2] = "—"
            if all(r[2] == "—" for r in inf_rows):
                inf_cols = inf_cols[:2]
                inf_rows = [r[:2] for r in inf_rows]
        inf_rows = [r for r in inf_rows if any(x != "—" for x in r[1:])]
        if inf_rows:
            S.append({"title": "Infinitive", "columns": inf_cols, "rows": inf_rows})

        # ---------------- participles, gerund, supine
        prows = []
        pres_p = self.first(lem, 189) if not perf_only else None
        if pres_p:
            gen = self.first(lem, 192)
            prows.append(["Present active", f"{pres_p}, gen. {gen}" if gen else pres_p])
        if dep and ppa_m:
            prows.append(["Perfect", self._three(lem, 375)])
        elif ppp_m:
            prows.append(["Perfect passive", self._three(lem, 303)])
        if self.first(lem, 225):
            prows.append(["Future active", self._three(lem, 225)])
        if self.first(lem, 339) and not perf_only:
            prows.append(["Gerundive", self._three(lem, 339)])
        if prows:
            S.append({"title": "Participles", "columns": ["Participle", "Forms"], "rows": prows})
        ger = [self.cell(lem, m) if not perf_only else "—" for m in (262, 263, 261, 264)]
        sup_rows = []
        if any(x != "—" for x in ger):
            sup_rows.append(["Gerund", f"gen. {ger[0]} · dat. {ger[1]} · acc. {ger[2]} · abl. {ger[3]}"])
        s1, s2 = self.cell(lem, 265), self.cell(lem, 266)
        if s1 != "—" or s2 != "—":
            sup_rows.append(["Supine", f"{s1} · {s2}"])
        if sup_rows:
            S.append({"title": "Gerund & supine", "columns": ["Form", "Forms"], "rows": sup_rows})
        if full:
            for base, title in ((189, "Present active participle"), (303, "Perfect passive participle"),
                                (375, "Perfect participle (deponent)"), (225, "Future active participle"),
                                (339, "Gerundive")):
                if self.first(lem, base):
                    t = self._gender_table(lem, base, title)
                    if t:
                        S.append(t)
        if lem.model == "facio" and not any(self.lex.has(lem, m) for m in range(267, 303)):
            out["note"] = "Passive supplied by fīō, fierī, factus sum."
