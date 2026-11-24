from pathlib import Path
from typing import Sequence
from tooling.git import GitClient
from tooling.ripgrep import RipgrepClient

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
from pathlib import Path

REPO_STRUCTURE_PATH = "./windir_architecture/00_repository_map/01_repository_structure.md"

def resolve_path(repo_path: str | Path, base: str | Path | None = None) -> Path:
    """
    将 path 转为绝对路径。
    - 已是绝对路径：直接返回规范化结果。
    - 相对路径：base 提供时基于 base 解析，否则基于当前工作目录。
    """
    p = Path(repo_path).expanduser()
    if p.is_absolute():
        return p.resolve()
    if base is None:
        base = Path(__file__).resolve()
    return (Path(base).expanduser().resolve() / p).resolve()

def write_to_file(out_path: str | Path , content: Sequence[str]) -> None:
    out_path = Path(out_path)
    if not out_path.exists():
        return
    with open(out_path, mode='a', encoding="utf-8", errors="replace") as f:
        f.writelines(content)

class RepositoryStructure:
    def __init__(self, repo_path : str | Path, out_path: str | Path | None = None,
                 git_runner: GitClient | None = None,
                 ripgrep_runner: RipgrepClient | None = None):
        self.git_commit = None
        self.prog_lang = None
        self.code_size = None
        self.repo_path = resolve_path(repo_path)
        self._git_runner = git_runner if git_runner else GitClient(self.repo_path)
        self._ripgrep_runner = ripgrep_runner if ripgrep_runner else RipgrepClient()
        self.out_path = resolve_path(out_path) if out_path is not None else resolve_path(REPO_STRUCTURE_PATH)

    def get_git_commit(self) -> None:
        self.git_commit = self._git_runner.rev_parse_head()

    def get_git_branch(self) -> None:
        result = self._git_runner.current_branch()
        write_to_file(self.out_path, 
                      [ "- repository current git branch: ",
                       result.stdout.strip()])
    
    def get_git_status(self) -> None:
        result = self._git_runner.short_status()
        write_to_file(self.out_path,
                      ["- repository git status: ",
                      result.stdout.strip()])
        
    def get_file_list(self, glob: str = "!**/.git/**") -> None:
        result = self._ripgrep_runner.travel_files(glob=glob, cwd=self.repo_path)
        # todo 写入文件
        write_to_file()



if __name__ == "__main__":
    windirstat_struct = RepositoryStructure("../../windirstat/")
    windirstat_struct.get_git_info()
    print(windirstat_struct.git_commit)