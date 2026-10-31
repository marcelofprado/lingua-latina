# Lingua Latina — Latin paradigms for Claude

Latin conjugation and declension tables for **~82,000 lemmata** — type a word, get every
form in tables (like cactus2000), with vowel quantities, principal parts, and parsing of
inflected forms.

## Install

**Claude (web, desktop, mobile, Cowork):** add *Lingua Latina* from the Claude directory
(once listed), or download `latin-morphology-skill.zip` from the
[releases page](https://github.com/marcelofprado/lingua-latina/releases) and upload it in
**Customize → Skills**.

**Claude Code:**

```
/plugin install lingua-latina --marketplace marcelofprado/lingua-latina
```

Then just ask: *"conjugate fero"*, *"decline ācer"*, *"what form is amāvisset?"*,
*"principal parts of patior"*.

## What it does

```
amāvisset → amō (verb, 1st conj.): pluperfect subjunctive active 3rd sg.

## amō, amāre, amāvī, amātum
Indicative active | Subjunctive active | Indicative passive (amātus sum …) |
Subjunctive passive | Imperative | Infinitive (amātūrum esse, amātum īrī) |
Participles | Gerund & supine
```

- **Verbs**: every synthetic form from the 141 Collatinus models, plus periphrastic perfect
  passive, future/perfect infinitives, deponents and semi-deponents, defective verbs
  (meminī, ōdī, coepī) and irregulars (sum, possum, ferō, eō, volō, nōlō, mālō, fīō, edō).
- **Nouns, adjectives, pronouns**: all cases incl. locative, i-stems, Greek nouns,
  comparison (melior, optimus) and derived adverbs (fortiter · fortius · fortissimē).
- **Analysis**: any form → lemma + morphology, incl. enclitics (*populusque*), contracted
  perfects (*amāstī*), assimilated prefixes (*afferō*), periphrastic forms
  (*laudātae essent*, *ductūrum esse*, *monitum īrī*).
- **Vowel quantities**: Collatinus marks metrical quantity; the engine converts it to
  natural quantity (amāvissēmus, not ămāvīssēmŭs).

Everything runs locally inside the skill (pure Python standard library, no network, no
dependencies). The engine and data are in `skills/latin-morphology/scripts/latin_morph/`.

## Repository layout

| Path | |
|---|---|
| `.claude-plugin/` | plugin manifest, marketplace file, icon |
| `skills/latin-morphology/` | the skill: `SKILL.md`, `scripts/latin.py`, engine and data |
| `tests/test_paradigms.py` | regression tests against standard grammar paradigms |
| `build_skill.sh` | zips the skill for manual upload |

A REST API / MCP server / web UI built on the same engine lives on the
[`server` branch](https://github.com/marcelofprado/lingua-latina/tree/server).

## Credits & licence

Lexicon, models and irregular forms: **Collatinus** © Yves Ouvrard & Philippe Verkerk
(<https://github.com/biblissima/collatinus>), GPL-3.0. This engine is an independent
Python re-implementation of the Collatinus inflection model, with corrections in
`irregs_extra.la` / `glosses_extra.en`. Licensed **GPL-3.0** (see `LICENSE`).
Not affiliated with cactus2000.
