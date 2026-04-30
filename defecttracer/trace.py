"""GDB backtrace parser.

Real GDB emits backtraces in a stable text form like:

    #0  0x000055cd99 in foo (x=42) at src/foo.c:17
    #1  0x000055cd11 in main (argc=2) at src/main.c:8

We parse this into a typed `Trace`. The signal that triggered the
crash is on a separate line (e.g. `Program received signal SIGSEGV,
Segmentation fault.`). We capture both.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_FRAME = re.compile(
    r"^#(?P<idx>\d+)\s+"
    r"(?:0x[0-9a-fA-F]+\s+)?"   # optional address
    r"(?:in\s+)?"                # optional 'in' keyword (gdb prints both forms)
    r"(?P<symbol>[\w:.~<>]+)\s*(?:\([^)]*\))?"
    r"(?:\s+at\s+(?P<file>[\w./\\-]+):(?P<line>\d+))?",
    re.MULTILINE,
)
_SIGNAL = re.compile(
    r"Program received signal\s+(?P<sig>SIG\w+)\b[,\s]*(?P<reason>[^\n]*)",
    re.MULTILINE,
)
_FAULTY_ADDR = re.compile(
    r"(?:reading from|writing to)\s+address\s+(0x[0-9a-fA-F]+)"
)


@dataclass(frozen=True, slots=True)
class Frame:
    idx: int
    symbol: str
    file: str | None
    line: int | None


@dataclass(frozen=True, slots=True)
class Trace:
    signal: str | None
    reason: str | None
    frames: tuple[Frame, ...]
    faulty_addr: str | None  # populated when GDB reports a memory fault address


def parse_backtrace(text: str) -> Trace:
    sig: str | None = None
    reason: str | None = None
    addr: str | None = None
    if m := _SIGNAL.search(text):
        sig = m.group("sig")
        reason = (m.group("reason") or "").strip() or None
    if m := _FAULTY_ADDR.search(text):
        addr = m.group(1)
    frames: list[Frame] = []
    for m in _FRAME.finditer(text):
        frames.append(
            Frame(
                idx=int(m.group("idx")),
                symbol=m.group("symbol"),
                file=m.group("file"),
                line=int(m.group("line")) if m.group("line") else None,
            )
        )
    return Trace(signal=sig, reason=reason, frames=tuple(frames), faulty_addr=addr)
