import os
import json
from pathlib import Path
from typing import Sequence
from collections import Counter

from deepseek_harness import DeepSeekHarness
from dotenv import load_dotenv

from tooling.git import GitClient
from tooling.ripgrep import RipgrepClient
from tooling.tree import TreeClient
from tooling.scc import SccClient

load_dotenv()
api_key = os.environ["DEEPSEEK_API_KEY"] 

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


REPO_STRUCTURE_PATH = "./windir_architecture/00_repository_map/01_repository_structure.md"
def ensure_clean(s: str, label: str = "string") -> str:
    """验证字符串无替换符、可被 UTF-8 严格编码。"""
    if not isinstance(s, str):
        raise TypeError(f"{label} 是 {type(s).__name__}，应为 str")
    if "\ufffd" in s:
        raise ValueError(f"{label} 含替换符 �，上游解码已损坏")
    s.encode("utf-8", errors="strict")  # 抓不可编码的脏码点
    return s

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

def write_to_file(out_path: str | Path , content: Sequence[str], mode) -> None:
    out_path = Path(out_path)
    if not out_path.exists():
        out_path.touch()
    if not out_path.is_file():
        return
    with open(out_path, mode=mode, encoding="utf-8", errors="replace") as f:
        f.writelines(content)

class RepositoryStructure:
    def __init__(self, repo_path : str | Path,
                 git_runner: GitClient | None = None,
                 ripgrep_runner: RipgrepClient | None = None,
                 tree_runner: TreeClient | None = None,
                 scc_runner: SccClient | None = None):
        self.git_commit = None
        self.prog_lang = []
        self.code_size = 0
        self.repo_path = resolve_path(repo_path)
        self._git_runner = git_runner if git_runner else GitClient(self.repo_path)
        self._ripgrep_runner = ripgrep_runner if ripgrep_runner else RipgrepClient()
        # self.out_path = resolve_path(out_path) if out_path is not None else resolve_path(REPO_STRUCTURE_PATH)
        self._tree_runner = tree_runner if tree_runner else TreeClient()
        self._scc_runner = scc_runner if scc_runner else SccClient()

    def get_git_commit(self) -> None:
        self.git_commit = self._git_runner.rev_parse_head()
        write_to_file("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\01_repository_structure.md",
                      ["- repository current commit HASH: ",
                       self.git_commit,
                       "\n"],
                       mode = 'a')

    def get_git_branch(self) -> None:
        branch = self._git_runner.current_branch()
        write_to_file("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\01_repository_structure.md", 
                      [ "- repository current git branch: ",
                       branch,
                       "\n"],
                       mode='a')
    
    def get_git_status(self) -> None:
        status = self._git_runner.short_status()
        write_to_file("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\01_repository_structure.md",
                      ["- repository git status: ",
                      status,
                      "\n"],
                      mode = 'a')
        
    def get_file_list(self, glob: str = "!**/.git/**") -> None:
        file_list = self._ripgrep_runner.travel_files(glob=glob, cwd=self.repo_path)
        write_to_file("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\inventory\\architecture-files.txt",
                      [file_list],
                      mode='w')

    def count_file_extension(self, source: str | Path):
        with open(source, mode='r', encoding="utf-8") as f:
            content = f.readlines()
        
        counter = Counter()
        for file in content:
            extension = file.split(".")[-1].strip()
            counter["." + extension] += 1
        with open("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\inventory\\extension-stats.json",
                  mode = 'w', encoding="utf-8") as f:
            json.dump(counter, f, indent=2, ensure_ascii=False)

    def get_file_tree(self):
        file_tree = self._tree_runner.travel_f(self.repo_path)

        write_to_file("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\inventory\\repository-tree.txt",
                      [file_tree],
                      mode='w')

    def get_repo_code_stats(self) -> None:
        data = self._scc_runner.code_stats(cwd=self.repo_path)

        with open("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\inventory\\repository-code-statistics.json",
                  mode='w', encoding="utf-8", errors="replace") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        for item in data:
            self.prog_lang.append(item.get("Name"))
            self.code_size += item.get("Code",0)

    def get_repo_structure(self):
        with open("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\inventory\\repository-tree.txt",
                  mode='r', encoding="utf-8") as f:
            repo_dir_tree = f.readlines()

        with open("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\inventory\\architecture-files.txt",
                  mode='r', encoding="utf-8") as f:
            file_list = f.readlines()
        with open("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\inventory\\extension-stats.json",
                  mode = 'r', encoding="utf-8") as f:
            file_extension_stats = json.load(f)

        prompt = REPO_STRUCTURE_PROMPT.format(self.git_commit,
                                            ", ".join(self.prog_lang),
                                            str(self.code_size),
                                            ''.join(repo_dir_tree),
                                                              file_list,
                                                              file_extension_stats)
        prompt = ensure_clean(prompt)
        with DeepSeekHarness(
            dsh_home=r"E:\Indie developer\project\C drive clean tool\AI-Powered-Engnieering-Knowledge-System\dsh-home",   # 必填，SDK 不会自动发现 ~/.dsh
            cwd=r"E:\Indie developer\project\C drive clean tool\AI-Powered-Engnieering-Knowledge-System\windirstat_architecture\00_repository_map",                # agent 的工作区
            provider="deepseek-official",
            model="deepseek-v4-pro",
            reasoning_effort="max",
            runtime_cwd = r"C:\Users\31608\dsh"
            ) as harness:
            session = harness.start_session("get windirstat repo structure - test")
            perm_result = session.run("/permission workspace-write")
            # print(perm_result.finish_reason)

            result = session.run(prompt)
        print("--- events ---")
        for ev in result.events:
            print(ev)
        print(f"session_id: {result.session_id}")
        print(f"final_response: {result.final_response}")
        print("--- finish_reason ---")
        print(f"finish_reason: {result.finish_reason}")
        # print(f"events: {result.events}")
        print("--- notifications ---")
        print(f"notifications: {result.notifications}")
        
        





if __name__ == "__main__":
    windirstat_struct = RepositoryStructure("../../windirstat/")
    windirstat_struct.get_git_commit()
    windirstat_struct.get_git_branch()
    windirstat_struct.get_git_status()
    windirstat_struct.get_file_list()
    windirstat_struct.count_file_extension("E:\\Indie developer\\project\\C drive clean tool\\AI-Powered-Engnieering-Knowledge-System\\windirstat_architecture\\00_repository_map\\inventory\\architecture-files.txt")
    windirstat_struct.get_file_tree()
    windirstat_struct.get_repo_code_stats()
    windirstat_struct.get_repo_structure()
    
