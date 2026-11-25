from tooling.tool_mannager import ToolManager
from get_repository_structure import RepositoryStructure

if __name__ == "__main__":
    tool_manager = ToolManager(auto_install=True)
    tool_manager.ensure_all()
    repo_structure = RepositoryStructure("../../windirstat/")
    repo_structure.get_git_info()
    print(repo_structure.git_commit)
    