#!/usr/bin/env python3
"""Scan text for LLM writing tics. Usage: slopcheck.py [file ...] or pipe via stdin.
Reports line number, matched phrase, and context. Exit 1 if any hits."""

import re
import sys

PHRASES = [
    # stock phrases — delete on sight
    "you're absolutely right", "you are absolutely right",
    "that's a great question", "that's an excellent question",
    "let me be clear", "it's worth noting", "it is worth noting",
    "it bears mentioning", "that said", "at the end of the day",
    "in conclusion", "in other words", "here's the thing",
    "here's the kicker", "here's where it gets interesting",
    "the key insight", "load-bearing", "load bearing", "seam",
    "honest take", "smoking gun", "belt-and-suspenders",
    "belt and suspenders", "now i have the full picture",
    "testament to", "delve", "crucially", "game-changer", "game changer",
    "despite these challenges", "despite its challenges",
    "imagine a world where", "think of it as",
    # filler intensifiers / magic adverbs
    "actually", "genuinely", "really", "simply", "clearly",
    "honestly", "quite", "truly", "significantly", "deeply",
    "quietly", "fundamentally", "remarkably", "arguably", "certainly",
    # verbose constructions
    "utilize", "leverage", "harness", "streamline", "in order to",
    "due to the fact that", "the majority of", "a large number of",
    "prior to", "the fact that", "in terms of",
    "serves as", "stands as", "represents a",
    # hype adjectives / grandiose nouns (flag for review; keep at most one if earned)
    "seamless", "robust", "nuanced", "intricate", "elegant",
    "comprehensive", "powerful", "tapestry", "landscape", "paradigm",
    "synergy", "ecosystem",
    # vague attribution
    "experts argue", "industry reports suggest", "observers have",
]

PATTERNS = [re.compile(r"\b" + re.escape(p) + r"\b", re.IGNORECASE) for p in PHRASES]
EMDASH = re.compile(r"—|--")
UNICODE_DECOR = re.compile(r"[‘’“”→]")


def scan(text, label):
    hits = 0
    for n, line in enumerate(text.splitlines(), 1):
        for pat in PATTERNS:
            for m in pat.finditer(line):
                hits += 1
                print(f"{label}:{n}: '{m.group()}'  …{line.strip()[:80]}")
        if len(EMDASH.findall(line)) > 1:
            hits += 1
            print(f"{label}:{n}: multiple em-dashes in one line")
        if UNICODE_DECOR.search(line):
            hits += 1
            print(f"{label}:{n}: unicode decoration (smart quote/arrow)  …{line.strip()[:80]}")
    return hits


def main():
    total = 0
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            with open(path, encoding="utf-8", errors="replace") as f:
                total += scan(f.read(), path)
    else:
        total += scan(sys.stdin.read(), "stdin")
    print(f"\n{total} hit(s)." if total else "Clean: 0 hits.")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
