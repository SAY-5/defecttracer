"""v4: crash bucketing — group similar crashes for triage.

The corpus + classifier (v3) tell you what kind of bug each crash
is. v4 tells you which crashes are *the same bug*. A flood of
production crashes is usually 5-10 distinct bugs reported many
times each; bucketing collapses the duplicates so triage works on
unique bugs, not raw crash count.

The bucket key is (root_cause, crashing_frame_signature) where
the signature is the top non-libc frame's (symbol, file). Two
crashes with the same key are treated as the same bug.
"""

from __future__ import annotations

from dataclasses import dataclass

from defecttracer.classify import RootCause
from defecttracer.repro import ReproReport


@dataclass(frozen=True, slots=True)
class CrashBucket:
    root_cause: RootCause
    signature: str   # human-readable bucket id
    count: int
    sample_rationale: str


def _signature(rep: ReproReport) -> str:
    """Bucket key: 'symbol@file' for the top user frame, or just
    'symbol' if no file. Falls back to '<unknown>' for frame-less
    reports."""
    if not rep.crashing_frame:
        return "<unknown>"
    # Look up the file the crashing_frame came from, if available.
    for f in rep.trace.frames:
        if f.symbol == rep.crashing_frame:
            if f.file:
                return f"{f.symbol}@{f.file}"
            return f.symbol
    return rep.crashing_frame


def bucket(reports: list[ReproReport]) -> list[CrashBucket]:
    grouped: dict[tuple[RootCause, str], list[ReproReport]] = {}
    for r in reports:
        key = (r.root_cause, _signature(r))
        grouped.setdefault(key, []).append(r)
    out: list[CrashBucket] = []
    for (cause, sig), reps in grouped.items():
        out.append(
            CrashBucket(
                root_cause=cause,
                signature=sig,
                count=len(reps),
                sample_rationale=reps[0].rationale,
            )
        )
    out.sort(key=lambda b: b.count, reverse=True)
    return out
