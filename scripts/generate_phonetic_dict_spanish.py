"""Regenerates games_corpus/data/phonetic_dicts/games-spanish.txt (batches 1 and 2).

Recipe of the original (lost) phonetic-dict-uba.txt, from audio-tt-ml's "generate phonetic
dictionaries" notebook: phonemizer + eSpeak, Latin American Spanish ("es-la" in old eSpeak,
"es-419" in eSpeak NG); "uu" and <tags> have no phones; one-letter words are their own phone.

Needs eSpeak NG (e.g. `brew install espeak-ng`) and the corpus data.
Usage: uv run --with phonemizer python scripts/generate_phonetic_dict_spanish.py [corpus_path]
"""

import os
import sys
from collections import Counter
from pathlib import Path

_HOMEBREW_ESPEAK = "/opt/homebrew/lib/libespeak-ng.dylib"  # phonemizer doesn't find it on its own
if "PHONEMIZER_ESPEAK_LIBRARY" not in os.environ and os.path.exists(_HOMEBREW_ESPEAK):
    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = _HOMEBREW_ESPEAK
from phonemizer import phonemize  # noqa: E402
from phonemizer.separator import Separator  # noqa: E402

from games_corpus import SpanishGamesCorpus  # noqa: E402
from games_corpus.phonetics import UNINTELLIGIBLE  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "games_corpus/data/phonetic_dicts/games-spanish.txt"

corpus = SpanishGamesCorpus()
corpus.load(local_path=sys.argv[1] if len(sys.argv) > 1 else None)
assert corpus.sessions is not None
counts = Counter(w.text for s in corpus.sessions.values() for t in s.tasks for i in t.ipus for w in i.words)
regular = sorted(w for w in counts if len(w) > 1 and w != "uu" and not w.startswith("<") and w not in UNINTELLIGIBLE)
phones = dict(
    zip(
        regular,
        phonemize(
            regular,
            language="es-419",
            backend="espeak",
            strip=True,
            separator=Separator(phone=" ", word="", syllable=""),
        ),
    )
)
for w in counts:
    phones.setdefault(w, w if len(w) == 1 and w not in UNINTELLIGIBLE else "")
OUT.write_text("".join(f"{c}\t{w}\t{phones[w]}\n" for w, c in counts.most_common()), encoding="utf-8")
print(f"{len(counts)} words -> {OUT}")
