from pathlib import Path

from tooling.tool_errors import CommandExitError, CommandError
from tooling.command_runner import CommandRunner, CommandResult

class GitError(CommandError):
    '''Capture git semantic error'''

class NotAGitRepoError(GitError):
    '''not a git repository'''

class DetachedHeadError(GitError):
    '''In a detached HEAD state'''

class GitRepoCorruptedError(GitError):
    '''Git repo corrupted'''

class GitLockError(GitError):
    '''index.lock conflict; another Git process is currently performing an operation.'''

class GitPermissionError(GitError):
    '''git repo/directory permission insuffient'''

class GitDubiousOwnershipError(GitError):
    '''safe.directory: Untrusted'''

class GitStatusWarning(GitError):
    '''git status success but warning exists, output maybe incomplete'''

class GitClient:
    def __init__(self, repo_path: str | Path, runner: CommandRunner | None = None):
        self.repo_path = Path(repo_path)
        self._runner = runner if runner else CommandRunner()

    def _git(self, args: list[str], timeout: float | None = None, 
             check: bool = False) -> CommandResult:
        self._check_repo_dir()
        result = self._runner.run(["git"] + args, cwd=self.repo_path, 
                                  timeout=timeout, check=check)
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "not a git repository" in stderr:
                raise NotADirectoryError(f"not a git repository: {self.repo_path}",
                    argv=list(result.argv), cwd=result.cwd)
            elif "dubious ownership" in stderr:
                raise GitDubiousOwnershipError(
                f"repository ownership not trusted: {self.repo_path}",
                argv=list(result.argv), cwd=result.cwd)
            elif any(kw in stderr for kw in ("bad object", "corrupt", "missing")):
                raise GitRepoCorruptedError(
                    f"repository appears corrupted: {stderr}",
                    argv=list(result.argv), cwd=result.cwd)
            elif "permission denied" in stderr.lower():
                raise GitPermissionError(
                    f"insufficient permission: {stderr}",
                    argv=list(result.argv), cwd=result.cwd)
            elif "no space left" in stderr.lower():
                raise GitError(
                    f"disk full: {stderr}",
                    argv=list(result.argv), cwd=result.cwd)
            else:
                raise CommandExitError(argv=list(result.argv), cwd=result.cwd, returncode=result.returncode,
                                   stdout=result.stdout, stderr=result.stderr)
        
        return result
        
    def _check_repo_dir(self) -> None:
        if not self.repo_path.exists():
            raise FileNotFoundError(f"repo directory does not exist: {self.repo_path}")
        if not self.repo_path.is_dir():
            raise NotADirectoryError(f"repo direcory is not a directory: {self.repo_path}")
                
    def _check_lock_error(self, result: CommandResult) -> None:
        if result.returncode != 0 and "index.lock" in result.stderr:
            raise GitLockError(
                "another git process is running (index.lock exists)",
                argv=list(result.argv), cwd=result.cwd,
            )
        
    def rev_parse_head(self) -> str:
        git_command = ["rev-parse", "HEAD"]        
        res = self._git(git_command)
        commit = res.stdout.strip()
        if not commit:
            raise GitError(f"git rev-parse HEAD return empty output",
                           argv=list(res.argv), cwd=self.repo_path)
        return commit

    def current_branch(self) -> str:
        git_command = ["branch", "--show-current"]                
        result = self._git(git_command)
        branch = result.stdout.strip()
        if not branch:
            raise DetachedHeadError("HEAD is detached, not on any branch",
                argv=list(result.argv), cwd=result.cwd)
        return branch

    def short_status(self) -> str:
        git_command = ["status", "--short"]
        result = self._git(git_command)
        self._check_lock_error(result)
        stderr = result.stderr.strip()
        if stderr:
            # todo 增加日志记录
            pass
            # logger.warning(f"git status warnings: {stderr}")
        return result.stdout.strip()
