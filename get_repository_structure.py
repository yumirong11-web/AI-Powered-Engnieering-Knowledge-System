import subprocess

from pathlib import Path

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


class GitNotInstalledError(Exception):
    """git 未安装且自动安装失败。"""


def _install_git() -> None:
    """根据平台调用包管理器安装 git，失败时抛 GitNotInstalledError。"""
    system = platform.system()

    if system == "Windows":
        # Windows 无统一包管理器，优先尝试 winget，其次提示手动安装
        if _which("winget"):
            cmd = ["winget", "install", "--id", "Git.Git", "-e", "--source", "winget"]
        elif _which("choco"):
            cmd = ["choco", "install", "git", "-y"]
        else:
            raise GitNotInstalledError(
                "未找到 winget 或 choco，请手动安装 Git: https://git-scm.com/downloads"
            )
    elif system == "Darwin":  # macOS
        if _which("brew"):
            cmd = ["brew", "install", "git"]
        else:
            raise GitNotInstalledError(
                "未找到 Homebrew，请先安装 brew 或手动安装 Git"
            )
    elif system == "Linux":
        # 根据发行版选择包管理器
        if _which("apt-get"):
            cmd = ["sudo", "apt-get", "install", "-y", "git"]
        elif _which("dnf"):
            cmd = ["sudo", "dnf", "install", "-y", "git"]
        elif _which("yum"):
            cmd = ["sudo", "yum", "install", "-y", "git"]
        elif _which("pacman"):
            cmd = ["sudo", "pacman", "-S", "--noconfirm", "git"]
        else:
            raise GitNotInstalledError("未识别的包管理器，请手动安装 Git")
    else:
        raise GitNotInstalledError(f"不支持的系统: {system}")

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise GitNotInstalledError(
            f"自动安装 Git 失败: {e.stderr.strip()}"
        ) from e
    except FileNotFoundError as e:
        raise GitNotInstalledError(f"安装命令不可用: {cmd[0]}") from e


def _which(name: str) -> bool:
    """检查命令是否在 PATH 中。"""
    from shutil import which
    return which(name) is not None


def _git_installed() -> bool:
    """检查 git 是否可用。"""
    return _which("git")

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
    def __init__(self, repo_path : str):
        self.git_commit = None
        self.prog_lang = None
        self.code_size = None
        self.repo_path = resolve_path(repo_path)
    def get_git_info(self):
        if(Path(self.repo_path).is_dir()):
            # todo 异常处理
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            self.git_commit = result.stdout.strip()
        else:
            raise NotADirectoryError(f"It is expected to be a directory, but in reality, it is not: {self.repo_path}")

if __name__ == "__main__":
    windirstat_struct = RepositoryStructure("../../windirstat/")
    windirstat_struct.get_git_info()
    print(windirstat_struct.git_commit)