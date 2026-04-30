"""v3: root-cause classifier.

Given a parsed `Trace`, decide which bug class triggered it:

- NULL_DEREF: SIGSEGV with faulty address near 0
- HEAP_CORRUPTION: SIGABRT after a glibc malloc check, or signal in
  free / malloc / realloc / chunk operations
- STACK_SMASH: SIGABRT with __stack_chk_fail in the trace
- USE_AFTER_FREE: SIGSEGV in symbols that are unlikely to be the
  user's code (e.g., destructors after a freed object's container
  was iterated)
- DOUBLE_FREE: SIGABRT with a glibc 'double free' message
- DIVIDE_BY_ZERO: SIGFPE
- ASSERT_FAILURE: SIGABRT with __assert_fail
- UNCLASSIFIED: signal seen but no matching pattern

The classifier is intentionally rule-based — production tools like
crash bucketing in Crashpad use ML on top of similar signals. The
rule set covers the common 60-issue corpus deterministically.
"""

from __future__ import annotations

from enum import StrEnum

from defecttracer.trace import Trace


class RootCause(StrEnum):
    NULL_DEREF = "null_deref"
    HEAP_CORRUPTION = "heap_corruption"
    STACK_SMASH = "stack_smash"
    USE_AFTER_FREE = "use_after_free"
    DOUBLE_FREE = "double_free"
    DIVIDE_BY_ZERO = "divide_by_zero"
    ASSERT_FAILURE = "assert_failure"
    UNCLASSIFIED = "unclassified"


_HEAP_FUNCS = {"malloc", "free", "realloc", "calloc", "_int_free", "_int_malloc"}


def _addr_int(addr: str | None) -> int | None:
    if not addr:
        return None
    try:
        return int(addr, 16)
    except ValueError:
        return None


def classify(trace: Trace) -> RootCause:
    sig = trace.signal or ""
    reason = (trace.reason or "").lower()
    syms = [f.symbol for f in trace.frames]
    sym_set = set(syms)

    # SIGFPE → divide-by-zero or related arithmetic fault.
    if sig == "SIGFPE":
        return RootCause.DIVIDE_BY_ZERO

    if sig == "SIGABRT":
        if "__stack_chk_fail" in sym_set:
            return RootCause.STACK_SMASH
        if "__assert_fail" in sym_set:
            return RootCause.ASSERT_FAILURE
        if "double free" in reason:
            return RootCause.DOUBLE_FREE
        if any(s in sym_set for s in _HEAP_FUNCS):
            return RootCause.HEAP_CORRUPTION
        return RootCause.UNCLASSIFIED

    if sig == "SIGSEGV":
        addr = _addr_int(trace.faulty_addr)
        if addr is not None and addr < 4096:
            return RootCause.NULL_DEREF
        # Heap function on the stack on a SEGV is usually UAF — the
        # program reused freed memory and tried to chase a dangling
        # pointer.
        if any(s in sym_set for s in _HEAP_FUNCS):
            return RootCause.USE_AFTER_FREE
        # If the address is finite but unmapped, fall back to UAF
        # too — it's the most common SEGV not caught above.
        if addr is not None:
            return RootCause.USE_AFTER_FREE
        return RootCause.UNCLASSIFIED

    return RootCause.UNCLASSIFIED
