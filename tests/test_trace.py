from __future__ import annotations

from defecttracer import parse_backtrace

SAMPLE = """\
Program received signal SIGSEGV, Segmentation fault.
The fault was caused by reading from address 0x000000000000010
#0  0x0000555555555200 in render_page (page=0x0) at src/render.c:42
#1  0x0000555555555280 in main () at src/main.c:18
"""


def test_signal_extracted() -> None:
    t = parse_backtrace(SAMPLE)
    assert t.signal == "SIGSEGV"


def test_frames_parsed() -> None:
    t = parse_backtrace(SAMPLE)
    assert len(t.frames) == 2
    assert t.frames[0].symbol == "render_page"
    assert t.frames[0].file == "src/render.c"
    assert t.frames[0].line == 42


def test_faulty_addr_extracted() -> None:
    t = parse_backtrace(SAMPLE)
    assert t.faulty_addr == "0x000000000000010"


def test_no_signal_returns_none() -> None:
    t = parse_backtrace("(gdb) run\nProgram exited normally.\n")
    assert t.signal is None
    assert t.frames == ()
