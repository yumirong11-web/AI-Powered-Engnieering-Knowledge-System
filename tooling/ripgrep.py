from pathlib import Path

from tool_errors import CommandError
from command_runner import CommandRunner, CommandResult

class RipgrepError(CommandError):
    '''capture ripgrep semantic error'''

class RipgrepPerssionError(RipgrepError):
    '''permission insuffient'''

class RipgrepFileNotFoundError(RipgrepError):
    '''Directory/File deletion during traversal'''

class RipgrepGlobError(RipgrepError):
    '''error parsing glob'''

class RipgrepRegexError(RipgrepError):
    '''error parsing regex'''

class RipgrepArgumentError(RipgrepError):
    '''bad argument'''

class RipgrepShellexpansionError(RipgrepError):
    '''! trigger shell history expansion'''

class RipgrepClient:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._runner = runner if runner else CommandRunner()

    def _ripgrep(self, args: list[str], check: bool = False, 
                 cwd: str | Path | None = None, 
                 timeout: float | None = None):
        result = self._runner.run(["rg"] + args, cwd=cwd, timeout=timeout, check=check)
        stderr = result.stderr
        if stderr:
            if "permission denied" in stderr:
                raise RipgrepPerssionError(f"permisson insuffient: {stderr}",
                                           argv=list(result.argv), cwd=result.cwd)
            if "no such file or directory" in stderr:
                raise RipgrepFileNotFoundError(f"directory/file not found during traversal: {stderr}",
                                               argv=list(result.argv), cwd=result.cwd)
            if "error parsing glob" in stderr:
                raise RipgrepGlobError(f"error happened when parsing glob: {result.argv}",
                                       argv=list(result.argv), cwd=result.cwd)
            if "regex parse error" in stderr:
                raise RipgrepRegexError(f"error happened when parsing regex: {result.argv}",
                                        argv=list(result.argv), cwd=result.cwd)
            if "unrecognized flag" in stderr or "wasn't expected" in stderr or "requires a value" in stderr:
                raise RipgrepArgumentError(f"bad argumnet: {result.argv}",
                                           argv=list(result.argv), cwd=result.cwd)
             
        return result

    def travel_files(self, glob: str = None, cwd: str | Path | None = None) -> CommandResult:
        rg_command = ["--files"]
        if glob:
            rg_command = rg_command + ["-g", glob]
        result = self._ripgrep(rg_command, cwd=cwd)
        stderr = result.stderr
        if stderr:
            if "event not found" in stderr:
                raise RipgrepShellexpansionError(f"'!' trigger shell history expansion error: {stderr}",
                                                 argv=list(result.argv), cwd=result.cwd)
            raise RipgrepError(stderr, argv=list(result.argv), cwd=result.cwd)
        return result

if __name__ == "__main__":
    rpc = RipgrepClient()
    result = rpc.travel_files(glob="!**/.git/**", cwd=Path('E:\\Indie developer\\project\\C drive clean tool\\windirstat'))
    print(result.stdout.strip())
