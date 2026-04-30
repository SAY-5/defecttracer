"""GDB driver.

Wraps a `gdb` subprocess in script mode. The contract:

    driver = GdbDriver(binary="./crashy", input_file="case42.bin")
    session = driver.run()
    print(session.backtrace_text)

For tests, `GdbSession` is a plain dataclass that test fixtures
populate directly with canned GDB output. The tests don't shell out;
that's fine because we're testing the parser + classifier, not GDB
itself.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GdbSession:
    binary: str
    input_file: str | None
    exit_status: int
    stdout: str
    backtrace_text: str


@dataclass
class GdbDriver:
    binary: str
    input_file: str | None = None
    timeout_secs: float = 30.0
    gdb_path: str = "gdb"

    def script(self) -> str:
        """The GDB command sequence we run on every defect:
        - run the program with the input piped in
        - on crash, capture the backtrace
        - quit
        """

        run_cmd = "run"
        if self.input_file is not None:
            run_cmd = f"run < {self.input_file}"
        return "\n".join(
            [
                "set pagination off",
                "set confirm off",
                "set print frame-arguments all",
                run_cmd,
                "bt",
                "info registers",
                "quit",
            ]
        )

    def run(self) -> GdbSession:
        cmd = [
            self.gdb_path,
            "--batch",
            "--ex", self.script(),
            self.binary,
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout_secs,
            check=False,
        )
        return GdbSession(
            binary=self.binary,
            input_file=self.input_file,
            exit_status=proc.returncode,
            stdout=proc.stdout,
            backtrace_text=proc.stdout,
        )
