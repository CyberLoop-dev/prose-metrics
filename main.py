#!/usr/bin/env python3
"""Offline text statistics and an approximate English readability estimate."""
import argparse
import json
import re
import sys
from collections import Counter

WORD_RE = re.compile(r"[\\w]+(?:['’][\\w]+)?", re.UNICODE)
STOP_WORDS = {"the","and","for","that","with","this","from","you","your","are","was","were","have","has","had","but","not","they","their","its","into","about","there","then","than","when","what","which","will","would","could","should","can","all","one","two","out","our","who","how","why","his","her","she","him","them","been","being","also","just"}

def syllables(word):
    """Rough English syllable estimate; useful for trends, not phonetic analysis."""
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and not word.endswith(("le", "ye")) and count > 1:
        count -= 1
    if word.endswith("le") and len(word) > 2 and word[-3] not in "aeiouy":
        count += 1
    return max(1, count)

def analyze(text):
    words = WORD_RE.findall(text)
    sentences = [s for s in re.split(r"(?<=[.!?])\\s+", text.strip()) if s.strip()]
    if words and not sentences:
        sentences = [text.strip()]
    paragraphs = [p for p in re.split(r"\\n\\s*\\n", text.strip()) if p.strip()]
    word_count = len(words)
    sentence_count = len(sentences)
    syllable_count = sum(syllables(w) for w in words)
    average_sentence = word_count / sentence_count if sentence_count else 0
    average_word_length = sum(len(w) for w in words) / word_count if word_count else 0
    flesch = None
    if word_count and sentence_count:
        flesch = 206.835 - 1.015 * average_sentence - 84.6 * (syllable_count / word_count)
    counts = Counter(w.lower() for w in words if len(w) > 3 and w.lower() not in STOP_WORDS)
    return {
        "characters": len(text),
        "characters_without_spaces": len(re.sub(r"\\s", "", text)),
        "words": word_count,
        "sentences": sentence_count,
        "paragraphs": len(paragraphs),
        "syllables_estimated": syllable_count,
        "average_words_per_sentence": round(average_sentence, 2),
        "average_word_length": round(average_word_length, 2),
        "reading_time_minutes_at_225_wpm": round(word_count / 225, 2),
        "flesch_reading_ease_approx": round(flesch, 1) if flesch is not None else None,
        "frequent_terms": [{"word": w, "count": n} for w, n in counts.most_common(8)]
    }

def main():
    parser = argparse.ArgumentParser(description="Analyze a text file or piped input without uploading it.")
    parser.add_argument("file", nargs="?", help="UTF-8 text file; omit to read stdin")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    if args.file:
        try:
            text = open(args.file, "r", encoding="utf-8").read()
        except OSError as exc:
            parser.error(str(exc))
    else:
        if sys.stdin.isatty():
            parser.error("provide a file path or pipe text into stdin")
        text = sys.stdin.read()
    result = analyze(text)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("PROSE METRICS")
    print("=" * 42)
    for key, value in result.items():
        if key == "frequent_terms":
            print("frequent_terms:")
            for item in value:
                print("  - {word}: {count}".format(**item))
        else:
            print("{:<38} {}".format(key, value if value is not None else "n/a"))
    print("\nNote: the Flesch score uses a rough English syllable estimate.")

if __name__ == "__main__":
    main()
