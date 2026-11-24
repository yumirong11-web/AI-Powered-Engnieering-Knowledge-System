import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from tool_errors import (
    CommandError,
    CommandLaunchError,
    CommandExitError,
    CommandTimeoutError,
    ExecutableNotFoundError
)

DEFAUTE_TIMEOUT = 30.0

@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    cwd: str | None
    returncode: int
    stdout: str
    stderr: str

class CommandRunner:
    def __init__(self, defaute_timeout: float = DEFAUTE_TIMEOUT):
        self._default_timeout = defaute_timeout

    def run(self, argv: Sequence[str], *, cwd: str | Path | None = None,
            timeout: float | None = None, check: bool = True) -> CommandResult:
        
        argv_list = [str(item) for item in argv]
        cwd_str = str(cwd) if cwd is not None else None
        try:
            proc = subprocess.run(argv_list,cwd=cwd_str,capture_output=True,text=True,
                                  encoding="utf-8",errors="replace",
                                  timeout=self._default_timeout if timeout is None else timeout,
                                  check=False)
        except FileNotFoundError as e:
            if cwd_str is not None and not Path(cwd_str).exists():
                raise CommandError(f"working directory dose not exist: {cwd_str}",
                                   argv=argv_list, cwd=cwd_str) from e
            raise ExecutableNotFoundError(f"executable Not Found: {argv_list[0]!r}",
                                          argv=argv_list, cwd=cwd_str) from e
        except NotADirectoryError as e:
            raise CommandError(f"working directory is not a directory: {cwd_str}",
                               argv=argv_list, cwd=cwd_str) from e
        except PermissionError as e:
            raise CommandLaunchError(f"cannot lauch {argv_list[0]!r}: Permission denied "
                                     f"(check the exec bit of binary and x(right) of every cwd parent) : {e}",
                                     argv=argv_list, cwd=cwd_str) from e
        except subprocess.TimeoutExpired as e:
            raise CommandTimeoutError(f"command timed out after {e.timeout}s: {' '.join(argv_list)}",
                                      argv=argv_list, cwd=cwd_str) from e
        except OSError as e:
            raise CommandLaunchError(f"failed to launch {' '.join(argv_list)} : {e}",
                                     argv=argv_list, cwd=cwd_str) from e
        result = CommandResult(argv=argv, cwd=cwd_str, returncode=proc.returncode,
                               stdout=proc.stdout, stderr=proc.stderr)
        if check and result.returncode != 0:
            raise CommandExitError(argv=argv_list, cwd=cwd_str, returncode=result.returncode,
                                   stdout=result.stdout, stderr=result.stderr)
        return result

        
        
        


