# lingua-latina (latin-morph)

Latin paradigms, conjugations and declensions for **~82,000 lemmata** — the logic of
[cactus2000](https://www.cactus2000.de) (type a word, get every form in tables), with vowel
quantities and reverse analysis of inflected forms.

## Install

**Claude (web, desktop, mobile, Cowork):** add *Lingua Latina* from the Claude directory
(once listed), or download `latin-morphology-skill.zip` from the
[latest release](https://github.com/marcelofprado/lingua-latina/releases) and upload it in
**Customize → Skills**.

**Claude Code:**

```
/plugin install lingua-latina --marketplace marcelofprado/lingua-latina
```

(older versions: `/plugin marketplace add marcelofprado/lingua-latina` then
`/plugin install lingua-latina@lingua-latina`).

Then just ask: *"conjugate fero"*, *"decline ācer"*, *"what form is amāvisset?"*.

## Ways to use it

| | What | Where |
|---|---|---|
| **Claude plugin / skill** | `skills/latin-morphology/` — self-contained (engine + data), no server | directory, marketplace or `.zip` (above) |
| **REST API + web UI** | FastAPI app, `GET /v1/lookup?q=…` | Docker, `deploy/` |
| **MCP server** | streamable HTTP at `/mcp` (tools `latin_lookup`, `latin_analyze`, `latin_paradigm`) | same container; add `https://<host>/mcp` as a custom connector |

## What it does

```
$ python3 skills/latin-morphology/scripts/latin.py amavisset
| Form      | Lemma | Meaning         | Analysis                 |
| amāvisset | amō   | verb — to love  | plupf. subj. act. 3 sg.  |

## amō, amāre, amāvī, amātum
verb · 1st conjugation — to love, like …
Indicative active | Subjunctive active | Indicative passive (with amātus sum …) |
Subjunctive passive | Imperative | Infinitive (amātūrum esse, amātum īrī) |
Participles | Gerund & supine
```

- **Generation**: every synthetic form from the 141 Collatinus models; periphrastic perfect
  passive, future/perfect infinitives, deponent and semi-deponent perfects, defective verbs
  (meminī, ōdī, coepī), irregulars (sum, possum, ferō, eō, volō, nōlō, mālō, fīō, edō).
- **Nouns / adjectives / pronouns**: all cases incl. locative, i-stems, Greek nouns,
  comparison (melior, optimus) and derived adverbs (fortiter · fortius · fortissimē).
- **Analysis**: any form → lemma + morphology, incl. enclitics (*populusque*), contracted
  perfects (*amāstī*), assimilated prefixes (*afferō*), periphrastic forms
  (*laudātae essent*, *ductūrum esse*, *monitum īrī*).
- **Quantities**: Collatinus marks metrical quantity; the engine converts it to natural
  quantity (amāvissēmus, not ămāvīssēmŭs).

## Install & CLI

```bash
git clone https://github.com/marcelofprado/lingua-latina && cd lingua-latina
./build_skill.sh          # builds dist/latin-morphology-skill.zip
cd skills/latin-morphology/scripts
python3 -m latin_morph amavisset
```

The engine lives in `skills/latin-morphology/scripts/latin_morph/` (single copy, used by the
skill, the CLI, the server and the tests).


```bash
python3 -m latin_morph <word> [--section indicative ...] [--full] [--all] [--analyze]
                              [--lemma] [--orth iv|uv|jv] [--no-ext] [--json]
```

## API

| Endpoint | |
|---|---|
| `GET /v1/lookup?q=amavisset[&full=1&all=1&section=indicative&orth=iv&format=md]` | analysis + paradigm (JSON or Markdown) |
| `GET /v1/analyze?q=laudati essent` | analysis only |
| `GET /v1/paradigm?lemma=volo2` | paradigm of a headword |
| `POST /mcp` | MCP (streamable HTTP, stateless) |
| `GET /health`, `GET /docs`, `GET /` | health, OpenAPI, web UI |

Rate limit: `RATE_LIMIT_PER_MIN` (default 120/IP).

## Deploy (AWS EC2 with Docker + nginx)

```bash
HOST=ec2-user@<diodorus-1> KEY=~/.ssh/<key>.pem DOMAIN=latin.<your-domain> ./deploy/deploy.sh
```

Builds the image on the host, runs it on `127.0.0.1:8010`, and installs
`deploy/nginx-latin.conf`. Then point a Route53 record at the host/ALB and run
`sudo certbot --nginx -d latin.<your-domain>` (or terminate TLS on the ALB).

`n8n/latin-morph-workflow.json`: import into n8n for a webhook (`/webhook/latin?q=…`) and a
sub-workflow usable as a tool by an n8n AI agent.

## Tests

```bash
python3 tests/test_paradigms.py      # ~300 forms vs. standard grammar paradigms
```

## Credits & licence

Lexicon, models and irregular forms: **Collatinus** © Yves Ouvrard & Philippe Verkerk
(<https://github.com/biblissima/collatinus>), GPL-3.0. This engine is an independent
Python re-implementation of the Collatinus inflection model, with corrections in
`irregs_extra.la` / `glosses_extra.en`. Licensed **GPL-3.0** (see `LICENSE`).
Not affiliated with cactus2000.
