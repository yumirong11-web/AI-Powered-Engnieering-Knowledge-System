"""Windows 下第三方工具检测与自动安装。Windows-only。"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


class ToolStatus(Enum):
    PRESENT = "present"          # 已存在
    INSTALLED = "installed"      # 本次安装成功
    MISSING = "missing"          # 缺失且未安装
    INSTALL_FAILED = "install_failed"
    SKIPPED = "skipped"          # 非必需且未安装，跳过


@dataclass(frozen=True)
class ToolSpec:
    """一个第三方工具的描述。"""
    name: str                              # 展示名，如 "git"
    check: Callable[[], bool]              # 检测函数
    install: Callable[[], bool] | None     # 安装函数，返回是否成功；None 表示无法自动安装
    required: bool = True                  # 是否必需
    note: str = ""                         # 补充说明（如安装指引）


@dataclass
class ToolResult:
    name: str
    status: ToolStatus
    detail: str = ""


# ---------- 检测原语 ----------

def _which(name: str) -> bool:
    return shutil.which(name) is not None


def _powershell_has(cmdlet: str) -> bool:
    """检测 PowerShell 内置 cmdlet/alias 是否存在。"""
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if ps is None:
        return False
    try:
        # todo 可对cmdlet进行参数化或改用白名单校验，增加安全性
        r = subprocess.run(
            [ps, "-NoProfile", "-NonInteractive", "-Command",
             f"if (Get-Command '{cmdlet}' -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}"],
            capture_output=True, text=True, timeout=5,
        )
        return r.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


# ---------- 安装原语 ----------

def _run_install(cmd: list[str]) -> bool:
    """执行安装命令，返回是否成功。"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return r.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def _install_via_winget(pkg_id: str) -> bool:
    if not _which("winget"):
        return False
    return _run_install([
        "winget", "install", "--id", pkg_id, "-e",
        "--accept-package-agreements", "--accept-source-agreements",
        "--silent",
    ])


def _install_via_choco(pkg: str) -> bool:
    if not _which("choco"):
        return False
    return _run_install(["choco", "install", pkg, "-y"])


def _install_git() -> bool:
    return _install_via_winget("Git.Git") or _install_via_choco("git")


def _install_rg() -> bool:
    # ripgrep 在 winget 的 id 是 BurntSushi.ripgrep.MSVC
    return _install_via_winget("BurntSushi.ripgrep.MSVC") or _install_via_choco("ripgrep")


def _install_tree() -> bool:
    # Windows 自带 tree.com，通常无需安装；若需 GNU tree 可走 choco
    return _install_via_choco("tree")


# ---------- 注册表：新增工具只改这里 ----------

DEFAULT_TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="git",
        check=lambda: _which("git"),
        install=_install_git,
        required=True,
        note="https://git-scm.com/downloads",
    ),
    ToolSpec(
        name="rg",
        check=lambda: _which("rg"),
        install=_install_rg,
        required=False,
        note="https://github.com/BurntSushi/ripgrep",
    ),
    ToolSpec(
        name="tree",
        check=lambda: _which("tree"),
        install=_install_tree,
        required=False,
        note="Windows 自带 tree.com；GNU tree 可通过 choco 安装",
    )
]


# ---------- 管理器 ----------

class ToolManager:
    """检测并（可选）自动安装第三方工具。"""

    def __init__(
        self,
        tools: list[ToolSpec] | None = None,
        auto_install: bool = False,
        logger: Callable[[str], None] | None = None,
    ):
        if platform.system() != "Windows":
            raise RuntimeError("ToolManager 仅支持 Windows")
        self.tools = tools if tools is not None else DEFAULT_TOOLS
        self.auto_install = auto_install
        self.log = logger or print

    def check(self, name: str) -> bool:
        spec = self._get(name)
        return spec.check()

    def check_all(self) -> dict[str, bool]:
        return {t.name: t.check() for t in self.tools}

    def ensure(self, name: str) -> ToolResult:
        """确保单个工具可用：存在则返回；缺失且允许安装则安装后复检。"""
        spec = self._get(name)
        if spec.check():
            return ToolResult(spec.name, ToolStatus.PRESENT)

        if not self.auto_install:
            return ToolResult(spec.name, ToolStatus.MISSING, spec.note)

        if spec.install is None:
            status = ToolStatus.MISSING if spec.required else ToolStatus.SKIPPED
            return ToolResult(spec.name, status, spec.note)

        self.log(f"[ToolManager] 正在安装 {spec.name} ...")
        ok = spec.install()
        if ok and spec.check():
            self.log(f"[ToolManager] {spec.name} 安装成功")
            return ToolResult(spec.name, ToolStatus.INSTALLED)

        # 安装命令返回成功但 PATH 未刷新时，再给一次机会
        if ok:
            self.log(f"[ToolManager] {spec.name} 安装命令成功，但复检未通过（可能需重启终端）")
            return ToolResult(spec.name, ToolStatus.INSTALL_FAILED, "安装后复检失败，可能需重启终端")

        return ToolResult(spec.name, ToolStatus.INSTALL_FAILED, spec.note)

    def ensure_all(self) -> list[ToolResult]:
        return [self.ensure(t.name) for t in self.tools]

    def raise_if_missing(self) -> None:
        """必需工具缺失时抛异常，适合在程序启动时调用。"""
        results = self.ensure_all()
        missing = [
            r for r in results
            if r.status in (ToolStatus.MISSING, ToolStatus.INSTALL_FAILED)
        ]
        required_missing = [
            r for r in missing if self._get(r.name).required
        ]
        if required_missing:
            names = ", ".join(r.name for r in required_missing)
            raise RuntimeError(f"缺少必需工具: {names}")

    def _get(self, name: str) -> ToolSpec:
        for t in self.tools:
            if t.name == name:
                return t
        raise KeyError(f"未注册的工具: {name}")

if __name__ == "__main__":
    tm = ToolManager(auto_install=True)
    tm.ensure_all()