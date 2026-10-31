"""Orthographic helpers: diacritic stripping, normalisation and display of
vowel quantity.

Collatinus marks *metrical* quantity: a vowel long by position carries a
macron (ā), a short vowel a breve (ă), a vowel of common/ambiguous quantity
both (ā̆). For a dictionary-style paradigm we want *natural* quantity
(amāvissēmus, not ămāvīssēmŭs). `display()` converts one to the other.
"""
from __future__ import annotations

import re
import unicodedata

COMB_BREVE = "̆"
COMB_MACRON = "̄"

_ATONE = str.maketrans({
    "ā": "a", "ă": "a", "ē": "e", "ĕ": "e", "ī": "i", "ĭ": "i",
    "ō": "o", "ŏ": "o", "ū": "u", "ŭ": "u", "ȳ": "y", "ў": "y",
    "Ā": "A", "Ă": "A", "Ē": "E", "Ĕ": "E", "Ī": "I", "Ĭ": "I",
    "Ō": "O", "Ŏ": "O", "Ū": "U", "Ŭ": "U", "Ȳ": "Y", "Ў": "Y",
    "ë": "e", "ï": "i", "ü": "u", "ä": "a", "ö": "o",
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ý": "y",
    "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
    "â": "a", "ê": "e", "î": "i", "ô": "o", "û": "u",
    COMB_BREVE: None, COMB_MACRON: None, "́": None, "̀": None,
    "̈": None,
})

_LONG = {"a": "ā", "e": "ē", "i": "ī", "o": "ō", "u": "ū", "y": "ȳ",
         "A": "Ā", "E": "Ē", "I": "Ī", "O": "Ō", "U": "Ū", "Y": "Ȳ"}
_LONG_CHARS = set(_LONG.values()) | {"ў"}  # ў is not long; handled separately
_LONG_CHARS.discard("ў")
_SHORT_TO_PLAIN = str.maketrans({
    "ă": "a", "ĕ": "e", "ĭ": "i", "ŏ": "o", "ŭ": "u", "ў": "y",
    "Ă": "A", "Ĕ": "E", "Ĭ": "I", "Ŏ": "O", "Ŭ": "U", "Ў": "Y",
})
_PLAIN = {v: k for k, v in _LONG.items()}

VOWELS = set("aeiouyAEIOUY")
CONSONANTS = set("bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ")
STOPS = set("bcdgptf")
LIQUIDS = set("lr")


def atone(s: str) -> str:
    """Remove every quantity/accent diacritic."""
    s = unicodedata.normalize("NFC", s)
    return s.translate(_ATONE)


def deramise(s: str) -> str:
    """Non-Ramist spelling: j→i, v→u, æ→ae, œ→oe."""
    return (s.replace("J", "I").replace("j", "i").replace("v", "u")
             .replace("V", "U").replace("æ", "ae").replace("Æ", "Ae")
             .replace("œ", "oe").replace("Œ", "Oe").replace("ụ", "u"))


def key(s: str) -> str:
    """Lookup key: lower case, no diacritics, i/u spelling."""
    return deramise(atone(s)).lower().strip()


def strip_homonym(s: str) -> tuple[str, int]:
    m = re.match(r"^(.*?)(\d+)$", s)
    if m:
        return m.group(1), int(m.group(2))
    return s, 0


# --------------------------------------------------------------------------
# Display of natural quantities
# --------------------------------------------------------------------------

def _graphemes(s: str) -> list[str]:
    """Split into base char + following combining marks."""
    out: list[str] = []
    for ch in s:
        if out and unicodedata.combining(ch):
            out[-1] += ch
        else:
            out.append(ch)
    return out


def _base(g: str) -> str:
    return atone(g[0]) if g else g


def _is_long(g: str) -> bool:
    """Grapheme marked long, and not 'common' (macron + breve)."""
    return g[0] in _LONG_CHARS and COMB_BREVE not in g


def _simplify(g: str, final: bool, final_o_long: bool = True) -> str:
    """Map one metric grapheme to a natural-quantity grapheme."""
    if COMB_BREVE in g:            # common quantity (ā̆): plain, except final ō
        b = _base(g)
        if final and final_o_long and b in "oO":
            return _LONG[b]
        return b
    g = g.replace(COMB_MACRON, "")
    return g.translate(_SHORT_TO_PLAIN)


def _vowel(g: str) -> bool:
    return _base(g) in VOWELS


def _cons_cluster(gs: list[str], i: int) -> str:
    """Return the consonant string following grapheme i (until a vowel or
    a word boundary). 'qu' counts as one consonant (u is not a vowel)."""
    out = []
    j = i + 1
    while j < len(gs):
        b = _base(gs[j]).lower()
        if b in VOWELS:
            # consonantal u after q / g in 'ngu', 'su' not handled
            if b == "u" and out and out[-1] == "q":
                out.append("u")
                j += 1
                continue
            break
        if b == " " or b == "-":
            break
        out.append(b)
        j += 1
    return "".join(out).replace("qu", "q")


def _positional(cluster: str) -> bool:
    """Is a vowel before this cluster long by position only?"""
    c = cluster.replace("h", "")
    weight = sum(2 if ch in "xz" else 1 for ch in c)
    if weight < 2:
        return False
    if len(c) == 2 and c[0] in STOPS and c[1] in LIQUIDS:
        return False  # muta cum liquida: Collatinus already marks common
    return True


def _keeps_length(cluster: str) -> bool:
    """Vowels are long by nature before ns, nf (and nct/nx)."""
    return cluster.startswith(("ns", "nf", "nct", "nx"))


def display(form: str, natural=None, stem: str | None = None,
            keep_x: bool = False, orth: str = "iv", long_only: bool = False,
            final_o_long: bool = True) -> str:
    """Convert a Collatinus metric form into a natural-quantity form.

    natural  -- the lemma in natural quantity (left of '=' in lemmes.la);
                its marks win over the common prefix it shares with `form`.
    keep_x   -- keep a long vowel before x (perfect stems: rēxī, dīxī).
    orth     -- 'iv' (j→i, keep v), 'uv' (j→i, v→u), 'jv' (raw).
    """
    if not form:
        return form
    form = unicodedata.normalize("NFC", form)
    gs = _graphemes(form)
    n = len(gs)
    # natural-lemma prefix: 'L' long, 'S' short, '?' unmarked (unknown).
    # `natural` may be a list of references; the first that marks a vowel wins.
    nat_marks: list[str] = []
    refs = [natural] if isinstance(natural, str) else list(natural or [])
    limit = len(_graphemes(unicodedata.normalize("NFC", stem))) if stem is not None else n
    for ref in refs:
        if not ref:
            continue
        ng = _graphemes(unicodedata.normalize("NFC", ref))
        marks = []
        pairs = list(zip(gs, ng))[:limit]
        for j, (a, b) in enumerate(pairs):
            if key(a) != key(b):
                break
            if _is_long(b):
                marks.append("L")
            elif (b[0] in "ăĕĭŏŭўĂĔĬŎŬЎ" and COMB_MACRON not in b and not long_only
                  # vocalis ante vocalem: shortness is contextual (audĭo / audīvī)
                  and not (j + 1 < len(ng) and _vowel(ng[j + 1]))):
                marks.append("S")
            else:
                marks.append("?")
        for i, mk in enumerate(marks):
            if i >= len(nat_marks):
                nat_marks.append(mk)
            elif nat_marks[i] == "?":
                nat_marks[i] = mk
    out = []
    for i, g in enumerate(gs):
        final = (i == n - 1) or (i + 1 < n and _base(gs[i + 1]) == " ")
        if _vowel(g) and i + 1 < n:
            bl0, nx0 = _base(g).lower(), gs[i + 1].lower()
            if ((bl0 in "ao" and nx0 == "e") or (bl0 == "a" and nx0 == "u")) and (
                    _is_long(g) or (i < len(nat_marks) and nat_marks[i] == "L")):
                out.append(_base(g))      # diphthong ae / oe / au
                continue
        if i < len(nat_marks) and _vowel(g) and nat_marks[i] != "?":
            b = _base(g)
            out.append(_LONG.get(b, b) if nat_marks[i] == "L" else b)
            continue
        if _vowel(g) and _is_long(g):
            b = _base(g)
            nxt = gs[i + 1].lower() if i + 1 < n else ""   # raw grapheme
            bl = b.lower()
            # diphthongs āe, ōe, āu (second vowel unmarked) → plain
            if (bl in "ao" and nxt == "e") or (bl == "a" and nxt == "u"):
                out.append(b)
                continue
            if bl == "e" and nxt == "u" and (i + 2 >= n or not _vowel(gs[i + 2])):
                out.append(b)  # neu, ceu, seu
                continue
            cl = _cons_cluster(gs, i)
            if _positional(cl) and not _keeps_length(cl) and not (keep_x and cl.startswith("x")):
                out.append(b)
                continue
            out.append(_LONG.get(b, b))
            continue
        out.append(_simplify(g, final, final_o_long))
    s = "".join(out)
    return orthography(s, orth)


def orthography(s: str, orth: str = "iv") -> str:
    if orth == "jv":
        return s
    s = s.replace("j", "i").replace("J", "I")
    if orth == "uv":
        s = s.replace("v", "u").replace("V", "U")
    return s


def plain(form: str, orth: str = "iv") -> str:
    """Form without any quantity marks."""
    return orthography(atone(form), orth)
