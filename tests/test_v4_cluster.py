from __future__ import annotations

from defecttracer import RootCause
from defecttracer.cluster import bucket
from defecttracer.repro import reproduce_from_text


def _bt(line_in_user_code: str) -> str:
    return (
        "Program received signal SIGSEGV, Segmentation fault.\n"
        "The fault was caused by reading from address 0x10\n"
        f"#0  in {line_in_user_code} () at src/x.c:42\n"
    )


def test_same_signature_buckets_together() -> None:
    reps = [reproduce_from_text(_bt("foo")) for _ in range(5)]
    buckets = bucket(reps)
    assert len(buckets) == 1
    assert buckets[0].count == 5


def test_different_signatures_in_separate_buckets() -> None:
    reps = [
        reproduce_from_text(_bt("foo")),
        reproduce_from_text(_bt("foo")),
        reproduce_from_text(_bt("bar")),
    ]
    buckets = bucket(reps)
    assert len(buckets) == 2
    # Sorted by count desc — foo first.
    assert buckets[0].count == 2
    assert buckets[1].count == 1


def test_signature_includes_file() -> None:
    rep = reproduce_from_text(_bt("foo"))
    buckets = bucket([rep])
    assert "src/x.c" in buckets[0].signature


def test_root_cause_separates_buckets_even_with_same_frame() -> None:
    # Same symbol but different signal class → different bucket.
    rep_seg = reproduce_from_text(_bt("foo"))
    rep_fpe = reproduce_from_text(
        "Program received signal SIGFPE, Arithmetic exception.\n"
        "#0  in foo () at src/x.c:42\n"
    )
    buckets = bucket([rep_seg, rep_fpe])
    assert len(buckets) == 2
    causes = sorted(b.root_cause.value for b in buckets)
    assert RootCause.DIVIDE_BY_ZERO.value in causes


def test_empty_input_returns_empty_list() -> None:
    assert bucket([]) == []
