"""CLI: `dtrace classify < backtrace.txt` parses + classifies.
`dtrace corpus` runs the canonical 60-issue corpus."""

from __future__ import annotations

import sys

from defecttracer import canonical_corpus, classify, parse_backtrace
from defecttracer.repro import reproduce_from_text


def _classify_stdin() -> int:
    text = sys.stdin.read()
    rep = reproduce_from_text(text)
    print(f"signal       : {rep.trace.signal}")
    print(f"root cause   : {rep.root_cause.value}")
    print(f"crashing fn  : {rep.crashing_frame}")
    print(f"rationale    : {rep.rationale}")
    return 0 if rep.root_cause.value != "unclassified" else 1


def _run_corpus() -> int:
    corpus = canonical_corpus()
    correct = 0
    for entry in corpus:
        trace = parse_backtrace(entry.backtrace)
        got = classify(trace)
        if got == entry.expected:
            correct += 1
        else:
            print(f"  ! {entry.id}: expected {entry.expected.value}, got {got.value}",
                  file=sys.stderr)
    accuracy = correct / len(corpus)
    print(f"corpus accuracy: {correct}/{len(corpus)} ({accuracy * 100:.1f}%)")
    return 0 if accuracy >= 0.95 else 1


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: dtrace {classify|corpus}", file=sys.stderr)
        return 2
    cmd = args[0]
    if cmd == "classify":
        return _classify_stdin()
    if cmd == "corpus":
        return _run_corpus()
    print(f"unknown: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
