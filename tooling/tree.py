from pathlib import Path

from tooling.tool_errors import CommandError
from tooling.command_runner import CommandRunner, CommandResult

class TreeError(CommandError):
    '''Tree Error'''

class TreePermissionError(TreeError):
    '''insuffient Permission'''

class TreeClient:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._runner = runner if runner else CommandRunner()

    def _tree(self, args: list[str], cwd: str | Path | None = None, 
              check: bool = False, timeout: float | None = None) -> CommandResult:
        import shutil
        tree_path = shutil.which("tree")
        result = self._runner.run([tree_path] + args, cwd=cwd, check=check, timeout=timeout)
        return result

    def travel_f(self, cwd: str | Path | None = None, check: bool = False, 
                 timeout: float | None = None) -> str:
        tree_command = ["/A", "/F"]
        result = self._tree(args=tree_command, cwd=cwd, check=check, timeout=timeout)
        stderr = result.stderr
        if stderr:
            if "denied" in stderr.lower() or "拒绝" in stderr or "invalid" in stderr.lower():
                raise TreePermissionError(f"Partially successful; insufficient permissions for some directories: {stderr}", 
                                      argv = list(result.argv), cwd=result.cwd)
            raise TreeError(stderr, argv=list(result.argv), cwd = result.cwd)

        return result.stdout.strip()

