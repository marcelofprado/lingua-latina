# Lingua Latina — Latin paradigms for Claude

Latin conjugation and declension tables for **~82,000 lemmata** — type a word, get every
form in tables (like cactus2000), with vowel quantities, principal parts and parsing of
inflected forms.

## Install

- **Claude (web, desktop, mobile, Cowork):** add *Lingua Latina* from the Claude directory.
- **Claude Code:** `/plugin install lingua-latina --marketplace marcelofprado/lingua-latina`
- **Any MCP client:** add the remote server `https://latin.diodorus.com.br/mcp`
  (streamable HTTP, no authentication).

Then ask: *"conjugate fero"*, *"decline ācer"*, *"what form is amāvisset?"*,
*"principal parts of patior"*.

## How it works

This branch (`main`) is the plugin: a skill (`skills/latin-morphology/SKILL.md`) plus a
reference to the remote MCP server (`.mcp.json`). The engine — a Python re-implementation of
the Collatinus inflection model, with periphrastic tenses, deponents, irregular and
defective verbs, reverse analysis and natural vowel quantities — runs on that server.

The engine, the server (REST API, MCP, web UI), deployment files, tests and an **offline
skill** that runs the engine locally live on the
[`server` branch](https://github.com/marcelofprado/lingua-latina/tree/server).

| Server endpoint | |
|---|---|
| `POST /mcp` | MCP tools `latin_lookup`, `latin_analyze`, `latin_paradigm` |
| `GET /v1/lookup?q=amavisset&format=md` | analysis + paradigm (JSON or Markdown) |
| `GET /` | web UI |

## Credits & licence

Lexicon, models and irregular forms: **Collatinus** © Yves Ouvrard & Philippe Verkerk
(<https://github.com/biblissima/collatinus>), GPL-3.0. Engine and plugin: GPL-3.0
(see `LICENSE`). Not affiliated with cactus2000.
