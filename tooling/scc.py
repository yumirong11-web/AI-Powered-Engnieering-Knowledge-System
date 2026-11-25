import json
from pathlib import Path

from tooling.tool_errors import CommandError
from tooling.command_runner import CommandRunner, CommandResult

class SccError(CommandError):
    '''scc Error'''

class SccOutputError(SccError):
    '''Error happened when parsing scc output'''

class SccClient():
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._runner = runner if runner else CommandRunner()

    def _scc(self, args: list[str], cwd: str | Path | None = None,
            timeout: float | None = 120.0, check: bool = False) -> CommandResult:
        result = self._runner.run(["scc"] + args, cwd=cwd, timeout=timeout, check=check)
        return result

    def code_stats(self, cwd: str | Path | None = None, 
                   timeout: float | None = None):
        scc_command = ["--format", "json"]
        result = self._scc(scc_command, cwd=cwd, timeout=timeout)
        stdout = result.stdout.strip()

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise SccOutputError(f"scc 输出不是合法 JSON: {e}; 片段: {stdout[:200]}",
                                 argv=list(result.argv), cwd=result.cwd) from e

        return data