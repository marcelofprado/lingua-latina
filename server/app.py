"""latin-morph server: REST API + MCP (streamable HTTP) + minimal web UI.

  GET  /v1/lookup?q=amavisset[&full=1&all=1&orth=iv&section=indicative&format=md|json]
  GET  /v1/analyze?q=amatus%20est
  GET  /v1/paradigm?lemma=fero
  POST /mcp              MCP endpoint (tools: latin_lookup, latin_analyze, latin_paradigm)
  GET  /health
  GET  /                 web UI
"""
from __future__ import annotations

import contextlib
import json
import os
import sys
import time
from collections import defaultdict, deque
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from latin_morph import __version__  # noqa: E402
from latin_morph.api import analyze as _analyze  # noqa: E402
from latin_morph.api import lookup as _lookup  # noqa: E402
from latin_morph.api import paradigm as _paradigm  # noqa: E402
from latin_morph.lexicon import get_lexicon  # noqa: E402
from latin_morph.render import render, render_analyses, render_paradigm  # noqa: E402

RATE = int(os.environ.get("RATE_LIMIT_PER_MIN", "120"))
MAX_Q = 80
ORTHS = {"iv", "uv", "jv"}


# ------------------------------------------------------------------ core (cached)
@lru_cache(maxsize=4096)
def cached_lookup(q: str, full: bool, all_: bool, orth: str, sections: tuple) -> str:
    return json.dumps(_lookup(q, full=full, all_lemmas=all_, orth=orth,
                              sections=list(sections) or None), ensure_ascii=False)


def _clean(q: str) -> str:
    q = (q or "").strip()
    if not q or len(q) > MAX_Q:
        raise HTTPException(400, f"query must be 1-{MAX_Q} characters")
    return q


# ------------------------------------------------------------------ MCP
mcp = FastMCP(
    "latin-morph",
    instructions=(
        "Latin morphology engine (Collatinus lexicon, ~82k lemmata). Use latin_lookup for any "
        "Latin word (lemma or inflected form): it returns the morphological analysis and the full "
        "paradigm as Markdown tables with vowel quantities. Present the tables as returned."),
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@mcp.tool()
def latin_lookup(word: str, full: bool = False, all_lemmas: bool = False,
                 sections: list[str] | None = None, orthography: str = "iv") -> str:
    """Analyse a Latin word (lemma or inflected form, e.g. 'amo', 'amavisset',
    'amatus est', 'populusque') and return its morphological analysis plus the
    complete paradigm (conjugation or declension) as Markdown tables.

    full: also decline participles / comparative / superlative in full.
    all_lemmas: inflect every candidate lemma, not only the most likely one.
    sections: optional filter, any of indicative, subjunctive, active, passive,
      imperative, infinitive, participles, gerund, declension, degrees.
    orthography: 'iv' (default: i and v), 'uv' (u only), 'jv' (j and v).
    """
    q = _clean(word)
    o = orthography if orthography in ORTHS else "iv"
    return render(json.loads(cached_lookup(q, full, all_lemmas, o, tuple(sections or ()))))


@mcp.tool()
def latin_analyze(word: str) -> str:
    """Morphological analysis only (form -> lemma + case/number/tense/mood/voice),
    as a compact Markdown table. Accepts periphrastic forms like 'laudati essent'."""
    res = _analyze(_clean(word))
    if res.get("words"):
        return "\n\n".join(render_analyses(w) for w in res["words"] if w.get("analyses")) \
            or f"Unknown form '{word}'."
    return render_analyses(res) or f"Unknown form '{word}'."


@mcp.tool()
def latin_paradigm(lemma: str, full: bool = False) -> str:
    """Full paradigm for a dictionary headword (homonyms: 'volo', 'volo2')."""
    ps = _paradigm(_clean(lemma), full=full)
    return "\n\n".join(render_paradigm(p) for p in ps) or f"No lemma '{lemma}'."


# ------------------------------------------------------------------ app
@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    get_lexicon()                    # warm the lexicon
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="latin-morph", version=__version__, lifespan=lifespan,
              description="Latin paradigms, conjugations and declensions. Data: Collatinus (GPL).")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST", "OPTIONS"],
                   allow_headers=["*"], expose_headers=["Mcp-Session-Id"])

_hits: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def ratelimit(request: Request, call_next):
    if request.url.path.startswith(("/v1", "/mcp")):
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
              or (request.client.host if request.client else "?"))
        now = time.monotonic()
        dq = _hits[ip]
        while dq and now - dq[0] > 60:
            dq.popleft()
        if len(dq) >= RATE:
            return JSONResponse({"error": "rate limit exceeded"}, status_code=429)
        dq.append(now)
    return await call_next(request)


@app.get("/health")
def health():
    lex = get_lexicon()
    return {"status": "ok", "version": __version__, "lemmata": len(lex.lemmas),
            "models": len(lex.models)}


@app.get("/v1/lookup")
def v1_lookup(q: str = Query(..., description="lemma or inflected form"),
              full: bool = False, all: bool = False, orth: str = "iv",
              section: list[str] = Query(default=[]), format: str = "json"):
    q = _clean(q)
    orth = orth if orth in ORTHS else "iv"
    data = json.loads(cached_lookup(q, full, all, orth, tuple(section)))
    if format == "md":
        return PlainTextResponse(render(data), media_type="text/markdown; charset=utf-8")
    return JSONResponse(data)


@app.get("/v1/analyze")
def v1_analyze(q: str, format: str = "json"):
    res = _analyze(_clean(q))
    if format == "md":
        return PlainTextResponse(render_analyses(res) or f"Unknown form '{q}'.",
                                 media_type="text/markdown; charset=utf-8")
    return JSONResponse(res)


@app.get("/v1/paradigm")
def v1_paradigm(lemma: str, full: bool = False, format: str = "json"):
    ps = _paradigm(_clean(lemma), full=full)
    if not ps:
        raise HTTPException(404, f"no lemma '{lemma}'")
    if format == "md":
        return PlainTextResponse("\n\n".join(render_paradigm(p) for p in ps),
                                 media_type="text/markdown; charset=utf-8")
    return JSONResponse(ps)


_UI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")


@app.get("/", response_class=HTMLResponse)
def index():
    with open(_UI, encoding="utf-8") as f:
        return f.read()


# MCP streamable-HTTP endpoint at /mcp (mounted last so REST routes win)
app.mount("/", mcp.streamable_http_app())
