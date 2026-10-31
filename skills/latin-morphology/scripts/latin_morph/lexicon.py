"""Collatinus-compatible inflection engine (re-implemented in Python).

Data files (GPL, © Yves Ouvrard / Philippe Verkerk, Collatinus project):
  modeles.la  paradigm models (endings per morphology number, radicals)
  lemmes.la   ~24 000 lemmata  (lem_ext.la: ~58 000 extension lemmata)
  irregs.la   irregular forms
  lemmes.en   English glosses
"""
from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass, field

from .text import COMB_BREVE, atone, deramise, key, strip_homonym

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------

@dataclass
class Ending:
    grq: str          # with quantities ('' for zero ending)
    morpho: int
    numrad: int
    rarity: int = 10


@dataclass
class Model:
    name: str
    parent: "Model | None" = None
    pos: str = ""
    radgen: dict = field(default_factory=dict)     # num -> rule string
    endings: dict = field(default_factory=dict)    # morpho -> [Ending]
    absents: set = field(default_factory=set)

    def is_a(self, name: str) -> bool:
        m = self
        while m is not None:
            if m.name == name:
                return True
            m = m.parent
        return False

    def ancestry(self) -> list[str]:
        out, m = [], self
        while m is not None:
            out.append(m.name)
            m = m.parent
        return out

    def add(self, e: Ending):
        self.endings.setdefault(e.morpho, []).append(e)


def _intervals(s: str) -> list[int]:
    out = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def _mk_ending(g: str, morpho: int, nr: int) -> Ending:
    rar = 10
    if g and g[-1].isdigit() and g[-1] != "0":
        rar = int(g[-1])
        g = g[:-1]
    if g == "-":
        g = ""
    return Ending(g, morpho, nr, rar)


def _allonge(s: str) -> str:
    """Lengthen (metrically) a vowel before a final consonant (sufd)."""
    m = re.search(r"([aăeĕiĭoŏuŭyў])([bcdfghjklmnpqrstvxz])$", s)
    if not m:
        return s
    rep = {"a": "ā", "ă": "ā", "e": "ē", "ĕ": "ē", "i": "ī", "ĭ": "ī",
           "o": "ō", "ŏ": "ō", "u": "ū", "ŭ": "ū", "y": "ȳ", "ў": "ȳ"}
    if s[-3:-1].lower() in ("āe", "āu", "ēu", "ōe"):
        return s
    return s[:m.start()] + rep[m.group(1)] + m.group(2)


def load_models(path: str) -> dict[str, Model]:
    variables: dict[str, str] = {}
    blocks: list[list[str]] = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n").strip()
            if not line or line.startswith("!"):
                continue
            if line.startswith("$"):
                k, v = line[1:].split("=", 1)
                variables[k] = v
                continue
            if line.startswith("modele:"):
                blocks.append([line])
            elif blocks:
                blocks[-1].append(line)

    var_re = re.compile(r"(?<=[:;])([^:;$]*?)\+?\$(\w+)")

    def subst(line: str) -> str:
        while True:
            m = var_re.search(line)
            if not m:
                return line
            pre, name = m.group(1), m.group(2)
            val = variables[name].replace(";", ";" + pre)
            line = line[:m.start()] + pre + val + line[m.end():]

    models: dict[str, Model] = {}
    for block in blocks:
        m = Model(name="")
        suffixes: list[tuple[str, list[int]]] = []
        sufd = ""
        for line in block:
            line = subst(line)
            parts = line.split(":")
            k = parts[0]
            if k == "modele":
                m.name = parts[1]
            elif k == "pere":
                m.parent = models.get(parts[1])
            elif k in ("des", "des+"):
                li = _intervals(parts[1])
                r = int(parts[2])
                ld = parts[3].split(";") if len(parts) > 3 else [""]
                for i, morpho in enumerate(li):
                    chunk = ld[i] if i < len(ld) else ld[-1]
                    for g in chunk.split(","):
                        m.add(_mk_ending(g, morpho, r))
                if k == "des+" and m.parent is not None:
                    for morpho in li:
                        for d in m.parent.endings.get(morpho, []):
                            m.add(Ending(d.grq + sufd, d.morpho, d.numrad, d.rarity))
            elif k == "R":
                m.radgen[int(parts[1])] = parts[2] if len(parts) > 2 else ""
            elif k == "abs":
                # cumulative within one block (Collatinus overwrites: possum lost
                # its first abs line, so it had an imperative and a fut. participle)
                m.absents |= set(_intervals(parts[1]))
            elif k == "abs+":
                m.absents |= set(_intervals(parts[1]))
            elif k == "suf":
                suffixes.append((parts[2], _intervals(parts[1])))
            elif k == "sufd":
                if m.parent is not None:
                    sufd = parts[1]
                    for morpho, lst in list(m.parent.endings.items()):
                        if morpho in m.absents:
                            continue
                        for d in lst:
                            m.add(Ending(_allonge(d.grq) + sufd, d.morpho, d.numrad, d.rarity))
            elif k == "pos":
                m.pos = parts[1][:1]
        # inheritance
        if m.parent is not None:
            p = m.parent
            if not m.pos:
                m.pos = p.pos
            for morpho, lst in p.endings.items():
                if morpho in m.endings or morpho in m.absents:
                    continue
                for d in lst:
                    m.add(Ending(d.grq + sufd, d.morpho, d.numrad, d.rarity))
            for lst in m.endings.values():
                for d in lst:
                    if d.numrad not in m.radgen:
                        m.radgen[d.numrad] = p.radgen.get(d.numrad, "")
            m.absents = m.absents | p.absents
        # suffixes (suf:)
        added = []
        for suff, li in suffixes:
            for lst in m.endings.values():
                for d in lst:
                    if d.morpho in li:
                        added.append(Ending(d.grq + suff, d.morpho, d.numrad, d.rarity))
        for d in added:
            m.add(d)
        models[m.name] = m
    return models


# --------------------------------------------------------------------------
# Lemmata
# --------------------------------------------------------------------------

@dataclass
class Lemma:
    lid: int
    cle: str            # key with homonym number (abdico2)
    hom: int            # homonym number (0 = none)
    natural: str        # headword with natural quantities (left of '=')
    grq: str            # metric headword(s), comma separated
    model: str
    radicals: dict      # num -> [metric radical]
    info: str           # dictionary info (is, ere, duxi, ductum)
    freq: int
    ext: bool           # from the extension lexicon
    explicit: tuple = ()  # radical numbers given explicitly in lemmes.la
    gloss: str = ""
    pos: str = ""
    irregs: dict = field(default_factory=dict)       # morpho -> [grq]
    irreg_excl: set = field(default_factory=set)

    @property
    def head(self) -> str:
        return atone(self.grq.split(",")[0])


def _lemma_pos(info: str, model_pos: str) -> str:
    pos = ""
    for needle, p in (("adj.", "a"), ("conj", "c"), ("excl.", "e"),
                      ("interj", "i"), ("num.", "m"), ("pron.", "p"),
                      ("prép", "r"), ("adv", "d"), (" nom ", "n"), ("npr.", "n")):
        if needle in info:
            pos += p
    return pos or model_pos


def _compute_radicals(lem: Lemma, m: Model):
    rad = {k: list(v) for k, v in lem.radicals.items()}
    for num, gen in m.radgen.items():
        if num in rad:
            continue
        if gen == "-":
            continue
        vals = []
        for g in lem.grq.split(","):
            g = g.strip()
            if not g:
                continue
            if gen == "K":
                vals.append(g)
                continue
            oter, _, ajouter = gen.partition(",")
            oter = int(oter or 0)
            if g.endswith(COMB_BREVE):
                g = g[:-1]
            g = g[:len(g) - oter] if oter else g
            if ajouter and ajouter != "0":
                g += ajouter
            vals.append(g)
        rad[num] = vals
    return rad


class Lexicon:
    def __init__(self, use_ext: bool = True):
        self.models = load_models(os.path.join(DATA, "modeles.la"))
        self.lemmas: list[Lemma] = []
        self.by_key: dict[str, list[int]] = defaultdict(list)
        self.by_cle: dict[str, int] = {}
        self._load_lemmas("lemmes.la", ext=False)
        if use_ext:
            self._load_lemmas("lem_ext.la", ext=True)
        self._load_glosses("lemmes.en")
        if use_ext:
            self._load_glosses("lem_ext.en")
        self._load_glosses("glosses_extra.en", override=True)
        self._load_irregs("irregs.la")
        self._load_irregs("irregs_extra.la")
        self._load_morphos()
        self._index()

    # ---------------- loading
    def _load_lemmas(self, fname: str, ext: bool):
        with open(os.path.join(DATA, fname), encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("!"):
                    continue
                ecl = line.split("|")
                if len(ecl) < 5:
                    continue
                lg = ecl[0].split("=")
                cle = atone(deramise(lg[0]))
                natural, hom = strip_homonym(lg[0])
                grq = lg[1] if len(lg) > 1 else natural
                model = ecl[1]
                if model not in self.models:
                    continue
                if ext and cle in self.by_cle:
                    continue  # main lexicon wins
                radicals = {}
                for i in (2, 3):
                    if i < len(ecl) and ecl[i] and ecl[i] != "-":
                        radicals[i - 1] = [r for r in ecl[i].split(",") if r and r != "-"]
                freq = 0
                if len(ecl) > 5:
                    try:
                        freq = int(ecl[5])
                    except ValueError:
                        freq = 0
                lem = Lemma(lid=len(self.lemmas), cle=cle, hom=hom,
                            natural=natural.split(",")[0], grq=grq, model=model,
                            radicals=radicals, info=ecl[4], freq=freq, ext=ext)
                m = self.models[model]
                lem.explicit = tuple(radicals)
                lem.pos = _lemma_pos(" " + lem.info + " ", m.pos)
                lem.radicals = _compute_radicals(lem, m)
                self.lemmas.append(lem)
                self.by_cle[cle] = lem.lid
                k, _ = strip_homonym(key(cle))
                self.by_key[k].append(lem.lid)

    def _load_glosses(self, fname: str, override: bool = False):
        p = os.path.join(DATA, fname)
        if not os.path.exists(p):
            return
        with open(p, encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                if not line or line.startswith("!") or ":" not in line:
                    continue
                cle, gloss = line.split(":", 1)
                lid = self.by_cle.get(cle)
                if lid is None:
                    lid = self.by_cle.get(atone(deramise(cle)))
                if lid is not None and (override or not self.lemmas[lid].gloss):
                    self.lemmas[lid].gloss = gloss.strip().rstrip(";").strip()

    def _load_irregs(self, fname: str):
        cleared: set = set()
        override = fname != "irregs.la"
        with open(os.path.join(DATA, fname), encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("!"):
                    continue
                parts = line.split(":")
                if len(parts) < 3:
                    continue
                form, cle, morphs = parts[0], parts[1], parts[2]
                excl = form.endswith("*")
                form = form.rstrip("*")
                lid = self.by_cle.get(cle)
                if lid is None:
                    continue
                lem = self.lemmas[lid]
                for mo in _intervals(morphs):
                    if override and excl and (lid, mo) not in cleared:
                        lem.irregs.pop(mo, None)
                        cleared.add((lid, mo))
                    if form != "-":
                        lem.irregs.setdefault(mo, []).append(form)
                    if excl:
                        lem.irreg_excl.add(mo)

    def _load_morphos(self):
        self.morpho_labels: dict[int, str] = {}
        with open(os.path.join(DATA, "morphos.en"), encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                m = re.match(r"^(\d+):(.*)$", line)
                if m:
                    self.morpho_labels[int(m.group(1))] = m.group(2).strip()

    # ---------------- indexes for analysis
    def _index(self):
        self.rad_index: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
        for lem in self.lemmas:
            for num, vals in lem.radicals.items():
                for r in vals:
                    self.rad_index[key(r)].append((lem.lid, num, r))
        self.end_index: dict[str, dict[str, list[Ending]]] = {}
        for name, m in self.models.items():
            idx: dict[str, list[Ending]] = defaultdict(list)
            for lst in m.endings.values():
                for d in lst:
                    idx[key(d.grq)].append(d)
            self.end_index[name] = dict(idx)
        self.irreg_index: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
        for lem in self.lemmas:
            for mo, forms in lem.irregs.items():
                for fm in forms:
                    self.irreg_index[key(fm).replace(" ", "")].append((lem.lid, mo, fm))
        self.max_end = max((len(k) for idx in self.end_index.values() for k in idx), default=0)

    # ---------------- generation
    def forms(self, lem: Lemma, morpho: int) -> list[tuple[str, int]]:
        """All metric forms of a lemma for a morphology number, with rarity."""
        return [(f, rar) for f, rar, _s, _n in self.forms_detail(lem, morpho)]

    def forms_detail(self, lem: Lemma, morpho: int) -> list[tuple[str, int, str | None, int]]:
        """(metric form, rarity, stem or None for irregulars, radical number)."""
        out: list[tuple[str, int, str | None, int]] = []
        if morpho not in lem.irreg_excl:
            m = self.models[lem.model]
            for d in m.endings.get(morpho, []):
                for r in lem.radicals.get(d.numrad, []):
                    out.append((r + d.grq, d.rarity, r, d.numrad))
        for fm in lem.irregs.get(morpho, []):
            out.append((fm, 9, None, -1))
        # dedupe keeping order, highest frequency first
        seen, res = set(), []
        for item in sorted(out, key=lambda x: -x[1]):
            if item[0] in seen:
                continue
            seen.add(item[0])
            res.append(item)
        return res

    def has(self, lem: Lemma, morpho: int) -> bool:
        return bool(self.forms(lem, morpho))

    def model(self, lem: Lemma) -> Model:
        return self.models[lem.model]

    def find(self, word: str) -> list[Lemma]:
        """Lemmata whose headword matches `word` (homonym digits allowed)."""
        w = word.strip()
        base, hom = strip_homonym(w)
        k = key(base)
        lids = list(self.by_key.get(k, []))
        if not lids:
            # headword variants (comma separated grq)
            pass
        lems = [self.lemmas[i] for i in lids]
        if hom:
            lems = [l for l in lems if l.hom == hom] or lems
        lems.sort(key=lambda l: (l.ext, -l.freq))
        return lems


_LEX: Lexicon | None = None


def get_lexicon() -> Lexicon:
    """Load the lexicon once per process (about 2 s; kept in memory)."""
    global _LEX
    if _LEX is None:
        _LEX = Lexicon()
    return _LEX
