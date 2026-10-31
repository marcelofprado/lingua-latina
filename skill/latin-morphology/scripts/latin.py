#!/usr/bin/env python3
"""Entry point for the latin-morphology skill.

    python3 latin.py amavisset              # analysis + full paradigm (Markdown)
    python3 latin.py fero --section indicative --section infinitive
    python3 latin.py "laudati essent" --analyze
    python3 latin.py bonus --full --json
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("LATIN_MORPH_CACHE", os.path.join(
    os.environ.get("TMPDIR", "/tmp"), "latin_morph_cache"))

from latin_morph.cli import main  # noqa: E402

main(sys.argv[1:])
