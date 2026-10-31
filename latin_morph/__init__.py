"""latin_morph — Latin inflection engine (paradigms, conjugations, declensions,
reverse analysis), built on the Collatinus lexicon and models. GPL-3.0."""
from .api import analyze, lookup, paradigm  # noqa: F401
__version__ = "1.0.0"
