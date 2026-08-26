import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
_SCRIPT_PATH = _SCRIPTS_DIR / "rename_project.py"

if not _SCRIPT_PATH.is_file():
    pytest.skip(
        "rename_project.py is not present (already-generated project)",
        allow_module_level=True,
    )

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import rename_project  # noqa: E402


def _build_tree(root: Path) -> None:
    (root / "src" / "skeletal").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pyproject.toml").write_text(
        '[project]\nname = "python-skeletal"\nrequires-python = ">=3.11"\n'
        '[tool.ruff]\ntarget-version = "py311"\n[tool.mypy]\npython_version = "3.11"\n',
        encoding="utf-8",
    )
    (root / "src" / "skeletal" / "__init__.py").write_text(
        '"""skeletal package."""\n', encoding="utf-8"
    )
    (root / "README.md").write_text(
        "# python-skeletal\n\nBy Lucas de Lima <106186397+lucas-lima-s@users.noreply.github.com>\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_x.py").write_text(
        "from skeletal import __version__\n", encoding="utf-8"
    )
    (root / "copier.yml").write_text("project_name: {type: str}\n", encoding="utf-8")


def _copy_script_into(root: Path) -> Path:
    scripts_dir = root / "scripts"
    scripts_dir.mkdir()
    destination = scripts_dir / "rename_project.py"
    source = _SCRIPTS_DIR / "rename_project.py"
    destination.write_bytes(source.read_bytes())
    return destination


def test_module_is_importable() -> None:
    assert isinstance(rename_project, ModuleType)


def test_apply_renames_and_scrubs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _build_tree(tmp_path)
    _copy_script_into(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = rename_project.main(
        [
            "--project-name",
            "demo-app",
            "--package-name",
            "demo_app",
            "--project-description",
            "d",
            "--author-name",
            "A",
            "--author-email",
            "a@example.com",
            "--github-user",
            "u",
            "--python-min",
            "3.12",
            "--apply",
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "src" / "demo_app").is_dir()
    assert not (tmp_path / "src" / "skeletal").exists()
    assert not (tmp_path / "copier.yml").exists()
    assert not (tmp_path / "scripts" / "rename_project.py").exists()

    for path in tmp_path.rglob("*"):
        if path.is_file() and path.suffix != ".pyc":
            content = path.read_text(encoding="utf-8", errors="ignore")
            assert "skeletal" not in content


def test_dry_run_changes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _build_tree(tmp_path)
    _copy_script_into(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    exit_code = rename_project.main(
        [
            "--project-name",
            "demo-app",
            "--author-name",
            "A",
            "--author-email",
            "a@example.com",
            "--github-user",
            "u",
        ]
    )

    assert exit_code == 0
    after = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert before == after
