"""Reproduction loop. Drives the GDB session, parses the backtrace,
classifies the root cause, returns a `ReproReport`.

For tests, `reproduce_from_text` skips the subprocess and consumes
canned GDB output. CI uses both paths: the canonical 60-issue
corpus runs through `reproduce_from_text` (deterministic, fast);
end-to-end smoke tests target real binaries.
"""

from __future__ import annotations

from dataclasses import dataclass

from defecttracer.classify import RootCause, classify
from defecttracer.gdb import GdbDriver
from defecttracer.trace import Trace, parse_backtrace


@dataclass(frozen=True, slots=True)
class ReproReport:
    root_cause: RootCause
    trace: Trace
    crashing_frame: str | None  # symbol of the top non-libc frame
    rationale: str


_LIBC_PREFIXES = ("__", "_int_", "abort", "raise")


def _crashing_frame(trace: Trace) -> str | None:
    for frame in trace.frames:
        if frame.symbol and not any(frame.symbol.startswith(p) for p in _LIBC_PREFIXES):
            return frame.symbol
    return trace.frames[0].symbol if trace.frames else None


def reproduce(driver: GdbDriver) -> ReproReport:
    session = driver.run()
    return reproduce_from_text(session.backtrace_text)


def reproduce_from_text(backtrace_text: str) -> ReproReport:
    trace = parse_backtrace(backtrace_text)
    cause = classify(trace)
    rationale = _explain(cause, trace)
    return ReproReport(
        root_cause=cause,
        trace=trace,
        crashing_frame=_crashing_frame(trace),
        rationale=rationale,
    )


def _explain(cause: RootCause, trace: Trace) -> str:
    sig = trace.signal or "unknown signal"
    base = f"signal {sig}"
    if cause == RootCause.NULL_DEREF:
        return f"{base}: SEGV at low address {trace.faulty_addr or 'unknown'}"
    if cause == RootCause.STACK_SMASH:
        return f"{base}: __stack_chk_fail in stack — buffer overflow into the stack canary"
    if cause == RootCause.ASSERT_FAILURE:
        return f"{base}: __assert_fail in stack — explicit assertion violated"
    if cause == RootCause.DOUBLE_FREE:
        return f"{base}: glibc reported double-free in stderr"
    if cause == RootCause.HEAP_CORRUPTION:
        return f"{base}: abort during heap operation — corruption likely from a prior buggy write"
    if cause == RootCause.DIVIDE_BY_ZERO:
        return f"{base}: SIGFPE — arithmetic exception (divide by zero or overflow)"
    if cause == RootCause.USE_AFTER_FREE:
        return f"{base}: SEGV in heap-related path; classic dangling-pointer dereference"
    return f"{base}: signal observed, no matching root-cause pattern"
