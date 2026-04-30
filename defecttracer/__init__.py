"""defecttracer — GDB-driven defect reproduction + root-cause classifier."""

from defecttracer.classify import RootCause, classify
from defecttracer.corpus import CorpusEntry, canonical_corpus
from defecttracer.gdb import GdbDriver, GdbSession
from defecttracer.repro import ReproReport, reproduce
from defecttracer.trace import Frame, Trace, parse_backtrace

__all__ = [
    "CorpusEntry",
    "Frame",
    "GdbDriver",
    "GdbSession",
    "ReproReport",
    "RootCause",
    "Trace",
    "canonical_corpus",
    "classify",
    "parse_backtrace",
    "reproduce",
]
