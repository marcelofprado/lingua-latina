---
name: latin-morphology
description: Inflect and parse any Latin word like cactus2000 — full conjugation and declension tables with vowel quantities, principal parts, and identification of inflected forms (amavisset → amō, plupf. subj. act. 3 sg.). Use whenever the user asks for a Latin paradigm, conjugation, declension, principal parts, comparison, or to parse/identify a Latin form.
license: GPL-3.0 (engine and Collatinus data)
---

# Latin morphology (paradigms, conjugations, declensions)

A complete Latin inflection engine runs locally from this skill: ~82,000 lemmata and 141
inflection models from the Collatinus project, plus periphrastic tenses, deponents,
semi-deponents, defective and irregular verbs, enclitics (-que/-ne/-ve), contracted
perfects (amāstī) and assimilated prefixes (afferō/adferō). **Never conjugate or decline
from memory — always run the engine and present its output.**

## How to run

```bash
python3 scripts/latin.py <word> [options]
```

`<word>` can be a dictionary form (`amo`, `rex`, `bonus`, `hic`), any inflected form
(`amavisset`, `regibus`, `fortissimorum`, `populusque`), or a periphrastic form in quotes
(`"laudati essent"`, `"ducturum esse"`, `"monitum iri"`). Macrons, j/v and capitals in the
input are optional.

| Option | Effect |
|---|---|
| *(none)* | analysis of the form (if it is not the headword) + full paradigm of the most likely lemma, as Markdown |
| `--section X` (repeatable) | only some tables: `indicative`, `subjunctive`, `active`, `passive`, `imperative`, `infinitive`, `participles`, `gerund`, `declension`, `degrees` |
| `--full` | also decline every participle, and comparative/superlative, in full tables |
| `--all` | inflect every homonym/candidate lemma (e.g. *volo* "wish" and *volo* "fly") |
| `--analyze` | identification only, no paradigm |
| `--lemma` | treat input strictly as a headword; homonyms with a digit: `volo2` |
| `--orth uv` / `--orth jv` | spelling u-only (*uolo*) or with j (*jam*); default i/v |
| `--no-ext` | ignore the 58k-entry extension lexicon (rare words, proper names) |
| `--json` | structured JSON instead of Markdown |

## How to answer

1. Run the script. Choose the narrowest call that answers the question:
   - "conjugate / decline X", "paradigm of X" → `latin.py X`
   - "what form is X?", "parse X" → `latin.py X --analyze` (add the paradigm only if asked)
   - a single requested form ("3rd pl. pluperfect subjunctive passive of *fero*") → run with
     the matching `--section` and quote just that cell, plus one line of context.
   - "principal parts of X" → `latin.py X --section none` (prints only the heading line with
     principal parts, class and gloss).
2. **Present the tables exactly as returned** (they are already concise and structured).
   Do not re-type forms by hand, do not add or drop macrons, do not merge tables.
   On a narrow screen, keep at most the tables the user asked for.
3. Table labels are in English (Nom./Gen., 1st sg., Present, Perfect…). Write any surrounding
   prose in the user's language.
4. If several lemmata match a form, the output lists them ("Also: …" or several analysis rows).
   Mention the alternatives briefly; rerun with `--all` or `--lemma <key>` when the user
   means another one.
5. If the word is unknown, the script suggests close headwords; offer them. Do not invent
   a paradigm.

## Notes on the data

- Vowel quantities are natural quantities derived from Collatinus' metrical marks: long
  vowels carry a macron (amāvissēmus). Hidden quantities before two consonants are shown
  only where the dictionary form or the oblique stem attests them (rēx, rēgis; but *actum*,
  not *āctum*). Variant and rare forms appear after a comma; very rare ones in parentheses.
- Periphrastic tenses use the masculine participle (amātus sum; amātī sumus); feminine and
  neuter follow the participle line (-a, -um).
- Deponents show passive forms with active meaning under "Indicative"/"Subjunctive";
  semi-deponents (audeō, gaudeō, fīō) show perfect-system forms with *sum*.
- Glosses are short English dictionary glosses from Collatinus.

## Optional: hosted API / MCP

The same engine is served as a REST API and an MCP server (see the project README):
`GET https://<host>/v1/lookup?q=amavisset&format=md` returns the same Markdown.
If the environment cannot run Python but has network access, call that endpoint instead.

Data: Collatinus (Yves Ouvrard & Philippe Verkerk), GPL-3.0. Engine: GPL-3.0.
