# Architecture

## Pipeline

```
input ──gdb --batch──▶ backtrace text
                            │
                            ▼
                       parse_backtrace
                            │
                            ▼
                       Trace{signal, reason,
                              frames, faulty_addr}
                            │
                            ▼
                       classify(trace) → RootCause
                            │
                            ▼
                       ReproReport{cause, frame, rationale}
```

## GDB driver

`GdbDriver` runs `gdb --batch --ex "<script>" <binary>`. The script:

```
set pagination off
set confirm off
run [< input_file]
bt
info registers
quit
```

`pagination off` keeps GDB from waiting for `RET` on long output;
`confirm off` skips "are you sure?" prompts. The script is the
same on every defect — variation lives in the input file.

`info registers` is captured for SEGV cases where the faulty
address lives in a register; the parser doesn't currently use it
but it's there for future work (production tools cross-reference
register values with allocation metadata).

## Backtrace parser

Three regexes:

1. `_SIGNAL`: matches `Program received signal SIGFOO[, reason]`.
   Captures sig + reason on the same line so messages like "double
   free or corruption (out)" land in the reason.
2. `_FRAME`: matches `#N [0x... ] [in ] symbol [(args)] [at file:line]`.
   The address and `in` keyword are both optional because GDB
   prints both forms (with addr for symbolicated frames, without
   for inline frames).
3. `_FAULTY_ADDR`: matches `reading from address 0x...` or
   `writing to address 0x...`. Used to distinguish null-deref
   (address < 4096) from other SEGV classes.

## Classifier (v3)

Rule-based, prioritized:

| Signal | Trigger | RootCause |
|---|---|---|
| SIGFPE | always | DIVIDE_BY_ZERO |
| SIGABRT | `__stack_chk_fail` in stack | STACK_SMASH |
| SIGABRT | `__assert_fail` in stack | ASSERT_FAILURE |
| SIGABRT | "double free" in reason | DOUBLE_FREE |
| SIGABRT | malloc/free/realloc in stack | HEAP_CORRUPTION |
| SIGSEGV | faulty address < 4096 | NULL_DEREF |
| SIGSEGV | malloc/free/realloc in stack | USE_AFTER_FREE |
| SIGSEGV | otherwise (with addr) | USE_AFTER_FREE |
| any | nothing matches | UNCLASSIFIED |

The 4096-byte threshold is ARM/x86 page size; addresses below this
are universally guard-page faults (NULL deref or near-NULL pointer
indexing).

## Crashing-frame heuristic

`reproduce` reports the *crashing frame* — the user's code that's
the most actionable starting point for triage. We skip frames whose
symbol starts with `__`, `_int_`, `abort`, `raise` because those
are libc plumbing the user can't fix. The first non-libc frame is
the crash site.

## Canonical 60-issue corpus (v3)

Six representative backtrace patterns × ten variations each = 60
entries. The CI gate runs the corpus through the classifier + asserts
≥95% accuracy. The corpus is intentionally synthetic — real field
crashes carry proprietary symbols. The patterns reflect the common
classes seen in C systems software.

## What's deliberately not here

- **Symbolicated stack walks for stripped binaries.** Production
  tools layer `addr2line` + DWARF; we assume the build keeps
  symbols.
- **Core file analysis.** The driver targets live `gdb` sessions;
  for a post-mortem core, run `gdb <binary> <core>` instead.
- **Cross-process tracking** (children that crash after a fork).
  GDB has follow-fork-mode for this; out of scope.
