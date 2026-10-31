"""Regression tests against standard grammar paradigms (Allen & Greenough,
Wheelock). Run: python3 tests/test_paradigms.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from latin_morph.analyze import Analyzer          # noqa: E402
from latin_morph.lexicon import get_lexicon       # noqa: E402
from latin_morph.paradigm import Builder          # noqa: E402

LEX = get_lexicon()
B = Builder(LEX)
A = Analyzer(LEX)
FAIL = []


def forms(word, morpho, model=None):
    lems = LEX.find(word)
    if model:
        lems = [l for l in lems if l.model == model] or lems
    return B.f(lems[0], morpho, rare=False)


def check(word, start, expected, model=None, exact=True):
    for i, exp in enumerate(expected):
        got = forms(word, start + i, model)
        ok = exp in got if exact else any(exp == g.replace("ā", "a").replace("ē", "e").replace("ī", "i")
                                         .replace("ō", "o").replace("ū", "u") for g in got)
        if not ok:
            FAIL.append(f"{word} #{start + i}: expected {exp!r}, got {got}")


# ---------------------------------------------------------------- verbs (with macrons)
check("amo", 121, ["amō", "amās", "amat", "amāmus", "amātis", "amant"])
check("amo", 127, ["amābam", "amābās", "amābat", "amābāmus", "amābātis", "amābant"])
check("amo", 139, ["amāvī", "amāvistī", "amāvit", "amāvimus", "amāvistis", "amāvērunt"])
check("amo", 175, ["amāvissem", "amāvissēs", "amāvisset", "amāvissēmus", "amāvissētis", "amāvissent"])
check("amo", 267, ["amor", "amāris", "amātur", "amāmur", "amāminī", "amantur"])
check("moneo", 121, ["moneō", "monēs", "monet", "monēmus", "monētis", "monent"])
check("moneo", 157, ["moneam", "moneās", "moneat", "moneāmus", "moneātis", "moneant"])
check("rego", 133, ["regam", "regēs", "reget", "regēmus", "regētis", "regent"])
check("rego", 121, ["regō", "regis", "regit", "regimus", "regitis", "regunt"])
check("capio", 121, ["capiō", "capis", "capit", "capimus", "capitis", "capiunt"])
check("capio", 163, ["caperem", "caperēs", "caperet", "caperēmus", "caperētis", "caperent"])
check("audio", 121, ["audiō", "audīs", "audit", "audīmus", "audītis", "audiunt"])
check("audio", 139, ["audīvī", "audīvistī", "audīvit", "audīvimus", "audīvistis", "audīvērunt"])
check("sum", 121, ["sum", "es", "est", "sumus", "estis", "sunt"])
check("sum", 157, ["sim", "sīs", "sit", "sīmus", "sītis", "sint"])
check("sum", 163, ["essem", "essēs", "esset", "essēmus", "essētis", "essent"])
check("possum", 121, ["possum", "potes", "potest", "possumus", "potestis", "possunt"])
check("fero", 121, ["ferō", "fers", "fert", "ferimus", "fertis", "ferunt"])
check("fero", 163, ["ferrem", "ferrēs", "ferret", "ferrēmus", "ferrētis", "ferrent"])
check("eo", 121, ["eō", "īs", "it", "īmus", "ītis", "eunt"])
check("eo", 133, ["ībō", "ībis", "ībit", "ībimus", "ībitis", "ībunt"])
check("volo", 121, ["volō", "vīs", "vult", "volumus", "vultis", "volunt"])
check("volo", 157, ["velim", "velīs", "velit", "velīmus", "velītis", "velint"])
check("nolo", 181, ["nōlī", "nōlīte"])
check("fio", 121, ["fīō", "fīs", "fit", "fīmus", "fītis", "fīunt"])
check("fio", 163, ["fierem", "fierēs", "fieret", "fierēmus", "fierētis", "fierent"])
check("imitor", 121, ["imitor", "imitāris", "imitātur", "imitāmur", "imitāminī", "imitantur"])
check("sequor", 121, ["sequor", "sequeris", "sequitur", "sequimur", "sequiminī", "sequuntur"])
check("patior", 121, ["patior", "pateris", "patitur", "patimur", "patiminī", "patiuntur"])
check("amo", 187, ["amāre"]); check("amo", 302, ["amārī"]); check("rego", 302, ["regī"])
check("amo", 189, ["amāns"]); check("amo", 192, ["amantis"]); check("amo", 339, ["amandus"])
check("rego", 139, ["rēxī"]); check("venio", 139, ["vēnī"]); check("facio", 139, ["fēcī"])
check("duco", 181, ["dūc"]); check("dico", 181, ["dīc"]); check("facio", 181, ["fac"])

# ---------------------------------------------------------------- nouns
CASES = [0, 3, 4, 2, 5, 1]  # nom gen dat acc abl voc offsets in morpho order


def decl(word, sg, pl, model=None):
    for off, exp in zip(CASES, sg):
        if exp not in forms(word, 1 + off, model):
            FAIL.append(f"{word} sg #{1 + off}: expected {exp!r}, got {forms(word, 1 + off, model)}")
    for off, exp in zip(CASES, pl):
        if exp not in forms(word, 7 + off, model):
            FAIL.append(f"{word} pl #{7 + off}: expected {exp!r}, got {forms(word, 7 + off, model)}")


decl("rosa", ["rosa", "rosae", "rosae", "rosam", "rosā", "rosa"],
     ["rosae", "rosārum", "rosīs", "rosās", "rosīs", "rosae"])
decl("dominus", ["dominus", "dominī", "dominō", "dominum", "dominō", "domine"],
     ["dominī", "dominōrum", "dominīs", "dominōs", "dominīs", "dominī"])
decl("puer", ["puer", "puerī", "puerō", "puerum", "puerō", "puer"],
     ["puerī", "puerōrum", "puerīs", "puerōs", "puerīs", "puerī"])
decl("ager", ["ager", "agrī", "agrō", "agrum", "agrō", "ager"],
     ["agrī", "agrōrum", "agrīs", "agrōs", "agrīs", "agrī"])
decl("templum", ["templum", "templī", "templō", "templum", "templō", "templum"],
     ["templa", "templōrum", "templīs", "templa", "templīs", "templa"])
decl("rex", ["rēx", "rēgis", "rēgī", "rēgem", "rēge", "rēx"],
     ["rēgēs", "rēgum", "rēgibus", "rēgēs", "rēgibus", "rēgēs"])
decl("corpus", ["corpus", "corporis", "corporī", "corpus", "corpore", "corpus"],
     ["corpora", "corporum", "corporibus", "corpora", "corporibus", "corpora"])
decl("civis", ["cīvis", "cīvis", "cīvī", "cīvem", "cīve", "cīvis"],
     ["cīvēs", "cīvium", "cīvibus", "cīvēs", "cīvibus", "cīvēs"])
decl("mare", ["mare", "maris", "marī", "mare", "marī", "mare"],
     ["maria", "marium", "maribus", "maria", "maribus", "maria"])
decl("manus", ["manus", "manūs", "manuī", "manum", "manū", "manus"],
     ["manūs", "manuum", "manibus", "manūs", "manibus", "manūs"])
decl("res", ["rēs", "reī", "reī", "rem", "rē", "rēs"],
     ["rēs", "rērum", "rēbus", "rēs", "rēbus", "rēs"])
decl("dies", ["diēs", "diēī", "diēī", "diem", "diē", "diēs"],
     ["diēs", "diērum", "diēbus", "diēs", "diēbus", "diēs"])

# ---------------------------------------------------------------- adjectives / pronouns
check("bonus", 13, ["bonus", "bone", "bonum", "bonī", "bonō", "bonō"])
check("bonus", 49, ["melior"]); check("bonus", 85, ["optimus"])
check("acer", 13, ["ācer"]); check("acer", 25, ["ācris"]); check("acer", 37, ["ācre"])
check("fortis", 49, ["fortior"]); check("fortis", 85, ["fortissimus"])
check("facilis", 85, ["facillimus"]); check("miser", 85, ["miserrimus"])
check("hic", 13, ["hīc"]); check("hic", 25, ["haec"]); check("hic", 37, ["hōc"]); check("hic", 15, ["hunc"])
check("qui", 13, ["quī"]); check("qui", 25, ["quae"]); check("qui", 37, ["quod"]); check("qui", 16, ["cūius"])
check("is", 13, ["is"]); check("is", 25, ["ea"]); check("is", 37, ["id"]); check("is", 16, ["ēius"])

# ---------------------------------------------------------------- analysis
def ana(word, lemma_key, morpho):
    res = A.analyze(word)
    for g in res["analyses"]:
        if g["key"].rstrip("0123456789") == lemma_key:
            if any(f["morpho_id"] == morpho for f in g["forms"]):
                return
    FAIL.append(f"analyze {word!r}: expected {lemma_key}/{morpho}, got "
                f"{[(g['key'], [f['morpho_id'] for f in g['forms']]) for g in res['analyses']]}")


ana("amavisset", "amo", 177)
ana("amasti", "amo", 140)
ana("virumque", "uir", 3)
ana("cecinit", "cano", 141)
ana("tulerunt", "fero", 144)
ana("Romae", "roma", 413)
ana("ierunt", "eo", 144)
ana("vult", "uolo", 123)
ana("hominibus", "homo", 11)
ana("fortissimorum", "fortis", 94)
ana("capiendi", "capio", 262)

if __name__ == "__main__":
    total = "see above"
    if FAIL:
        print(f"{len(FAIL)} FAILURES")
        for f in FAIL:
            print(" -", f)
        sys.exit(1)
    print("all paradigm & analysis checks passed")
