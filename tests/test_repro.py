from __future__ import annotations

from defecttracer import RootCause
from defecttracer.repro import reproduce_from_text


def test_repro_emits_classified_report() -> None:
    text = (
        "Program received signal SIGSEGV, Segmentation fault.\n"
        "The fault was caused by reading from address 0x00\n"
        "#0  in foo () at f.c:1\n"
    )
    rep = reproduce_from_text(text)
    assert rep.root_cause == RootCause.NULL_DEREF
    assert rep.crashing_frame == "foo"
    assert "SEGV" in rep.rationale


def test_crashing_frame_skips_libc() -> None:
    text = (
        "Program received signal SIGABRT, Aborted.\n"
        "#0  in raise ()\n"
        "#1  in abort ()\n"
        "#2  in __stack_chk_fail ()\n"
        "#3  in user_code () at u.c:9\n"
    )
    rep = reproduce_from_text(text)
    assert rep.crashing_frame == "user_code"
    assert rep.root_cause == RootCause.STACK_SMASH


def test_unrecognized_signal_is_unclassified() -> None:
    rep = reproduce_from_text("(gdb) run\nProgram exited normally.\n")
    assert rep.root_cause == RootCause.UNCLASSIFIED
