class CommandError(Exception):

    def __init__(self, message: str, *, argv: list[str], cwd: str | None = None):
        self.argv = list(argv)
        self.cwd = cwd
        super.__init__(message)

class ExecutableNotFoundError(CommandError):
    '''Executable File Not Found'''

class CommandLaunchError(CommandError):
    '''Child process failed to start: insufficient permissions, exhausted resources, etc. '''

class CommandTimeoutError(CommandError, TimeoutError):
    '''Execution Timeout'''

class CommandExitError(CommandError):
    def __init__(self, *, argv: list[str], cwd: str | None = None, returncode: int,
                 stdout: str, stderr: str):
        self.returncode = returncode,
        self.stdout = stdout,
        self.stderr = stderr,
        super().__init__(f"command failed (exit={returncode}): {' '.join(argv)}\n{stderr.strip()}",
                         argv=argv, cwd=cwd)