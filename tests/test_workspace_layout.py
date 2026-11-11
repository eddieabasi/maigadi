"""Guard the uv workspace layout so every package is registered consistently.

Convention (spec/BUILD_PLAN.md, "Proposed repo structure"):
``<area>/<name>/`` -> distribution ``maigadi-<name>`` -> module ``maigadi_<name>``
in a ``src/`` layout with a ``py.typed`` marker. Each member must also appear in
the root pyproject's dependencies, workspace sources and mypy_path.
"""

import importlib
import tomllib
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
AREAS = ("shared", "edge", "cloud", "tools")
PYPROJECT: dict[str, Any] = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
MEMBERS: list[str] = PYPROJECT["tool"]["uv"]["workspace"]["members"]


def dist_name(member: str) -> str:
    return "maigadi-" + Path(member).name.replace("_", "-")


def module_name(member: str) -> str:
    return "maigadi_" + Path(member).name


def test_members_are_explicit_and_exist() -> None:
    assert MEMBERS, "workspace has no members"
    for member in MEMBERS:
        assert "*" not in member, f"list members explicitly, not as globs: {member}"
        assert (ROOT / member / "pyproject.toml").is_file(), f"missing pyproject: {member}"


def test_every_package_directory_is_a_member() -> None:
    on_disk = {
        p.parent.relative_to(ROOT).as_posix()
        for area in AREAS
        for p in (ROOT / area).glob("*/pyproject.toml")
    }
    assert on_disk == set(MEMBERS)


@pytest.mark.parametrize("member", MEMBERS)
def test_member_naming_and_typed_marker(member: str) -> None:
    meta = tomllib.loads((ROOT / member / "pyproject.toml").read_text(encoding="utf-8"))
    assert meta["project"]["name"] == dist_name(member)
    package_dir = ROOT / member / "src" / module_name(member)
    assert (package_dir / "__init__.py").is_file()
    assert (package_dir / "py.typed").is_file(), "PEP 561 marker required (mypy strict)"


@pytest.mark.parametrize("member", MEMBERS)
def test_member_imports_from_this_checkout(member: str) -> None:
    module = importlib.import_module(module_name(member))
    assert module.__doc__, f"{module.__name__} needs a docstring stating its purpose"
    assert module.__file__ is not None
    assert Path(module.__file__).resolve().is_relative_to(ROOT / member / "src")


def test_root_project_depends_on_every_member() -> None:
    expected = {dist_name(m) for m in MEMBERS}
    assert set(PYPROJECT["project"]["dependencies"]) == expected
    sources: dict[str, Any] = PYPROJECT["tool"]["uv"]["sources"]
    for name in expected:
        assert sources.get(name) == {"workspace": True}, f"missing workspace source: {name}"


def test_mypy_path_covers_every_member() -> None:
    mypy_path: list[str] = PYPROJECT["tool"]["mypy"]["mypy_path"]
    for member in MEMBERS:
        assert f"$MYPY_CONFIG_FILE_DIR/{member}/src" in mypy_path, member
