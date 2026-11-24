import subprocess

from pathlib import Path

from git import GitClient

REPO_STRUCTURE_PROMPT = '''
You are a senior C++ software architect.

Your task is to analyze the repository structure
and produce a Repository Structure Map.

Repository information:
- Git commit: {}
- Programming language: {}
- Approximate source code size: {} LOC

Input:
1. Repository directory tree:{}
2. File inventory:{}
3. File extension statistics:{}

Analyze the repository from these perspectives:

1. Identify major directories.
2. Identify source-code directories.
3. Identify resource and configuration directories.
4. Identify build-related directories.
5. Identify third-party or vendored code.
6. Identify generated files.
7. Identify potential logical modules.
8. Identify directories that cannot yet be classified.

Important constraints:

- Do not assume directory names represent architectural components.
- Do not infer component responsibilities solely from filenames.
- Distinguish observed facts from hypotheses.
- Every important conclusion must reference relevant paths.
- Do not invent relationships that are not supported by evidence.

For each directory, provide:

- Path
- File count
- Main file types
- Observed purpose
- Potential module
- Evidence
- Confidence
- Unresolved questions

Output:

1. repository_structure.md
2. directory_inventory.csv
3. A list of questions requiring source-code inspection.
'''
REPO_DIR_TREE_PATH = "./repository-tree.txt"
FILE_INVENTORY_PATH = "./inventory-file.txt"
FILE_EXT_STATS_PATH = "./extension-stats.csv"

import subprocess
import sys
import platform
from pathlib import Path

def resolve_path(path: str | Path, base: str | Path | None = None) -> Path:
    """
    将 path 转为绝对路径。
    - 已是绝对路径：直接返回规范化结果。
    - 相对路径：base 提供时基于 base 解析，否则基于当前工作目录。
    """
    p = Path(path).expanduser()
    if p.is_absolute():
        return p.resolve()
    if base is None:
        base = Path(__file__).resolve()
    return (Path(base).expanduser().resolve() / p).resolve()

class RepositoryStructure:
    def __init__(self, repo_path : str, git_runner: GitClient | None = None):
        self.git_commit = None
        self.prog_lang = None
        self.code_size = None
        self.repo_path = resolve_path(repo_path)
        self._git_runner = git_runner if git_runner is not None else GitClient(self.repo_path)

    def get_git_commit(self) -> None:
        self.git_commit = self._git_runner.rev_parse_head()

    def get_git_branch(self) -> None:
        result = self._git_runner.current_branch()
        # 写入到某个文件
    
    def get_git_status(self) -> None:
        result = self._git_runner.short_status()
        # 写入到某个文件



if __name__ == "__main__":
    windirstat_struct = RepositoryStructure("../../windirstat/")
    windirstat_struct.get_git_info()
    print(windirstat_struct.git_commit)