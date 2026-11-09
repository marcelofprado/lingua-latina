---
name: latin-morphology
description: Inflect and parse any Latin word like cactus2000 — full conjugation and declension tables with vowel quantities, principal parts, and identification of inflected forms (amavisset → amō, plupf. subj. act. 3 sg.). Use whenever the user asks for a Latin paradigm, conjugation, declension, principal parts, comparison, or to parse/identify a Latin form.
---

# Latin morphology (paradigms, conjugations, declensions)

This plugin connects to the **lingua-latina** server: a Latin inflection engine with
~82,000 lemmata and 141 inflection models (Collatinus data), periphrastic tenses,
deponents, semi-deponents, defective and irregular verbs, enclitics (-que/-ne/-ve),
contracted perfects (amāstī) and assimilated prefixes (afferō/adferō).
**Never conjugate or decline from memory — always call the tools and present their output.**

## Tools

| Tool | Use it for |
|---|---|
| `latin_lookup(word, full?, all_lemmas?, sections?, orthography?)` | analysis of the form (if it is not the headword) **and** the full paradigm, as Markdown tables |
| `latin_analyze(word)` | identification only ("what form is X?", "parse X") |
| `latin_paradigm(lemma, full?)` | paradigm of an exact headword; homonyms with a digit: `volo2` |

`word` may be a dictionary form (`amo`, `rex`, `bonus`, `hic`), any inflected form
(`amavisset`, `regibus`, `populusque`) or a periphrastic form (`laudati essent`,
`ducturum esse`, `monitum iri`). Macrons, j/v and capitals are optional.

Options of `latin_lookup`:
- `sections`: limit the tables — `indicative`, `subjunctive`, `active`, `passive`,
  `imperative`, `infinitive`, `participles`, `gerund`, `declension`, `degrees`;
  `["none"]` returns only the heading line (principal parts, class, gloss).
- `full: true`: also decline every participle, and comparative/superlative, in full.
- `all_lemmas: true`: inflect every homonym/candidate lemma (e.g. *volo* "wish" and *volo* "fly").
- `orthography`: `iv` (default), `uv` (u only: *uolo*), `jv` (with j: *jam*).

## How to answer

1. Pick the narrowest call:
   - "conjugate / decline X", "paradigm of X" → `latin_lookup(X)`
   - "what form is X?", "parse X" → `latin_analyze(X)` (add the paradigm only if asked)
   - one requested form ("3rd pl. pluperfect subjunctive passive of *fero*") →
     `latin_lookup` with the matching `sections`, then quote just that cell plus one line of context
   - "principal parts of X" → `latin_lookup(X, sections=["none"])`
2. **Present the tables exactly as returned.** Do not re-type forms by hand, do not add or drop
   macrons, do not merge tables. On a narrow screen keep only the tables the user asked for.
3. Table labels are in English (Nom./Gen., 1st sg., Present, Perfect…). Write the surrounding
   prose in the user's language.
4. If several lemmata match, the output lists them ("Also: …" or several analysis rows).
   Mention the alternatives briefly; call again with `all_lemmas` or `latin_paradigm` when the
   user means another one.
5. If the word is unknown, the tool suggests close headwords; offer them. Never invent a paradigm.
6. If the tools are unavailable, say that the Lingua Latina server could not be reached
   instead of producing forms from memory.

## Notes on the data

- Long vowels carry a macron (amāvissēmus). Hidden quantities before two consonants are shown
  only where the dictionary form or the oblique stem attests them (rēx, rēgis; *actum*).
  Variant forms follow a comma; very rare ones are in parentheses.
- Periphrastic tenses use the masculine participle (amātus sum; amātī sumus).
- Deponents show passive forms with active meaning under "Indicative"/"Subjunctive";
  semi-deponents (audeō, gaudeō, fīō) show perfect-system forms with *sum*.
- Glosses are short English dictionary glosses from Collatinus.

Data: Collatinus (Yves Ouvrard & Philippe Verkerk), GPL-3.0.
