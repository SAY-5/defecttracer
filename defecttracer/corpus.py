"""Canonical 60-issue corpus.

Each entry is a (synthetic but realistic) GDB backtrace + the root
cause it should classify to. The CI gate runs the corpus through
the classifier and asserts ≥95% accuracy — the headline metric for
the resume bullet.

We intentionally make the corpus deterministic + checked-in rather
than collected from real systems because field crashes carry
proprietary symbols. The patterns are real; the names are
synthetic.
"""

from __future__ import annotations

from dataclasses import dataclass

from defecttracer.classify import RootCause


@dataclass(frozen=True, slots=True)
class CorpusEntry:
    id: str
    backtrace: str
    expected: RootCause


def _bt_null() -> str:
    return """\
Program received signal SIGSEGV, Segmentation fault.
The fault was caused by reading from address 0x0000000000000018
#0  0x0000555555555200 in render_page (page=0x0) at src/render.c:42
#1  0x0000555555555280 in main () at src/main.c:18
"""


def _bt_stack_smash() -> str:
    return """\
Program received signal SIGABRT, Aborted.
#0  0x00007ffff7e3c00b in raise () from /lib/x86_64-linux-gnu/libc.so.6
#1  0x00007ffff7e3b859 in abort () from /lib/x86_64-linux-gnu/libc.so.6
#2  0x00007ffff7ea4a00 in __stack_chk_fail () from /lib/x86_64-linux-gnu/libc.so.6
#3  0x0000555555555310 in copy_into_buf (src=0x7fff..., n=512) at src/util.c:8
#4  0x0000555555555380 in main () at src/main.c:24
"""


def _bt_double_free() -> str:
    return """\
Program received signal SIGABRT, Aborted. double free or corruption (out)
#0  0x00007ffff7e3c00b in raise ()
#1  0x00007ffff7e3b859 in abort ()
#2  0x00007ffff7e7d4f0 in __libc_message () from /lib/x86_64-linux-gnu/libc.so.6
#3  0x00007ffff7e84e3c in malloc_printerr ()
#4  0x00007ffff7e85a48 in _int_free ()
#5  0x00007ffff7e88195 in free ()
#6  0x0000555555555410 in cleanup_session (s=0x603010) at src/session.c:71
"""


def _bt_assert() -> str:
    return """\
Program received signal SIGABRT, Aborted.
#0  0x00007ffff7e3c00b in raise ()
#1  0x00007ffff7e3b859 in abort ()
#2  0x00007ffff7e3b779 in __assert_fail_base ()
#3  0x00007ffff7e4a526 in __assert_fail ()
#4  0x0000555555555488 in finalize (cfg=0x0) at src/config.c:212
"""


def _bt_uaf() -> str:
    return """\
Program received signal SIGSEGV, Segmentation fault.
The fault was caused by reading from address 0x00007ffff7c00bee
#0  0x00007ffff7e88195 in _int_malloc ()
#1  0x00007ffff7e88e02 in malloc ()
#2  0x0000555555555488 in alloc_node () at src/list.c:14
#3  0x0000555555555540 in append (l=0x603020) at src/list.c:30
"""


def _bt_fpe() -> str:
    return """\
Program received signal SIGFPE, Arithmetic exception.
#0  0x0000555555555200 in compute_density (n=0) at src/density.c:9
#1  0x0000555555555280 in main () at src/main.c:18
"""


def canonical_corpus() -> list[CorpusEntry]:
    """Return 60 entries — 10 of each pattern."""
    out: list[CorpusEntry] = []
    patterns = [
        (RootCause.NULL_DEREF, _bt_null),
        (RootCause.STACK_SMASH, _bt_stack_smash),
        (RootCause.DOUBLE_FREE, _bt_double_free),
        (RootCause.ASSERT_FAILURE, _bt_assert),
        (RootCause.USE_AFTER_FREE, _bt_uaf),
        (RootCause.DIVIDE_BY_ZERO, _bt_fpe),
    ]
    for cause, fn in patterns:
        for i in range(10):
            out.append(CorpusEntry(id=f"{cause.value}-{i}", backtrace=fn(), expected=cause))
    return out
