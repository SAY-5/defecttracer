from __future__ import annotations

from defecttracer import RootCause, classify, parse_backtrace
from defecttracer.corpus import canonical_corpus


def test_null_deref_classified() -> None:
    t = parse_backtrace(
        "Program received signal SIGSEGV, Segmentation fault.\n"
        "The fault was caused by reading from address 0x0000000000000010\n"
        "#0  in foo () at f.c:1\n"
    )
    assert classify(t) == RootCause.NULL_DEREF


def test_stack_smash_classified() -> None:
    t = parse_backtrace(
        "Program received signal SIGABRT, Aborted.\n"
        "#0  in raise ()\n"
        "#1  in __stack_chk_fail ()\n"
        "#2  in copy_into_buf () at u.c:8\n"
    )
    assert classify(t) == RootCause.STACK_SMASH


def test_double_free_classified() -> None:
    t = parse_backtrace(
        "Program received signal SIGABRT, Aborted. double free or corruption (out)\n"
        "#0  in raise ()\n"
        "#1  in free ()\n"
        "#2  in cleanup () at s.c:1\n"
    )
    assert classify(t) == RootCause.DOUBLE_FREE


def test_assert_failure_classified() -> None:
    t = parse_backtrace(
        "Program received signal SIGABRT, Aborted.\n"
        "#0  in raise ()\n"
        "#1  in __assert_fail ()\n"
        "#2  in finalize () at c.c:9\n"
    )
    assert classify(t) == RootCause.ASSERT_FAILURE


def test_divide_by_zero_classified() -> None:
    t = parse_backtrace(
        "Program received signal SIGFPE, Arithmetic exception.\n"
        "#0  in compute_density () at d.c:9\n"
    )
    assert classify(t) == RootCause.DIVIDE_BY_ZERO


def test_use_after_free_classified() -> None:
    t = parse_backtrace(
        "Program received signal SIGSEGV, Segmentation fault.\n"
        "The fault was caused by reading from address 0x00007ffff7c00bee\n"
        "#0  in _int_malloc ()\n"
        "#1  in malloc ()\n"
        "#2  in alloc_node () at l.c:14\n"
    )
    assert classify(t) == RootCause.USE_AFTER_FREE


def test_canonical_corpus_meets_accuracy_target() -> None:
    corpus = canonical_corpus()
    assert len(corpus) == 60
    correct = sum(1 for e in corpus if classify(parse_backtrace(e.backtrace)) == e.expected)
    accuracy = correct / len(corpus)
    assert accuracy >= 0.95
