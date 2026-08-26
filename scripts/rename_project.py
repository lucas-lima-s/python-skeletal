import argparse
import keyword
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

_SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".ruff_cache",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
}
_SKIP_RELATIVE_PATH_PREFIX = "docs/assets"
_PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")
_NORECEIVED_EMAIL = "106186397+lucas-lima-s@users.noreply.github.com"


@dataclass(frozen=True)
class RenamePlan:
    project_name: str
    package_name: str
    project_description: str
    author_name: str
    author_email: str
    github_user: str
    python_min: str

    @property
    def replacements(self) -> list[tuple[re.Pattern[str], str]]:
        no_dot = self.python_min.replace(".", "")
        return [
            (re.compile(re.escape("python-skeletal")), self.project_name),
            (re.compile(re.escape("skeletal")), self.package_name),
            (re.compile(re.escape("Lucas de Lima")), self.author_name),
            (re.compile(re.escape(_NORECEIVED_EMAIL)), self.author_email),
            (re.compile(re.escape("lucas-lima-s")), self.github_user),
            (
                re.compile(r'requires-python = ">=3\.11"'),
                f'requires-python = ">={self.python_min}"',
            ),
            (
                re.compile(r'target-version = "py311"'),
                f'target-version = "py3{no_dot}"',
            ),
            (
                re.compile(r'python_version = "3\.11"'),
                f'python_version = "{self.python_min}"',
            ),
        ]


def _is_valid_project_name(name: str) -> bool:
    return bool(_PROJECT_NAME_RE.match(name))


def _should_skip(relative: Path) -> bool:
    posix = relative.as_posix()
    if posix == _SKIP_RELATIVE_PATH_PREFIX or posix.startswith(f"{_SKIP_RELATIVE_PATH_PREFIX}/"):
        return True
    return any(part in _SKIP_DIR_NAMES for part in relative.parts)


def _iter_candidate_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if _should_skip(relative):
            continue
        files.append(path)
    return sorted(files)


def _read_text_if_utf8(path: Path) -> str | None:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _apply_replacements(text: str, plan: RenamePlan) -> tuple[str, int]:
    total = 0
    for pattern, replacement in plan.replacements:
        text, count = pattern.subn(replacement, text)
        total += count
    return text, total


def _scrub_scripts_references(text: str) -> str:
    marker = '"scripts/rename_project.py"'
    kept = [line for line in text.splitlines(keepends=True) if marker not in line]
    return re.sub(r', "scripts"(?=\])', "", "".join(kept))


def _transform_file(path: Path, text: str, plan: RenamePlan) -> tuple[str, int]:
    new_text, count = _apply_replacements(text, plan)
    if path.name == "pyproject.toml":
        scrubbed = _scrub_scripts_references(new_text)
        if scrubbed != new_text:
            count += 1
            new_text = scrubbed
    return new_text, count


def _remove_empty_scripts_dir(root: Path) -> None:
    scripts_dir = root / "scripts"
    if not scripts_dir.is_dir():
        return
    for leftover in sorted(scripts_dir.rglob("*"), reverse=True):
        if leftover.is_file():
            leftover.unlink()
        elif leftover.is_dir():
            leftover.rmdir()
    if not any(scripts_dir.iterdir()):
        scripts_dir.rmdir()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rename_project",
        description="Rename this project template into a new project.",
    )
    parser.add_argument("--project-name", required=True, help="new distribution name (kebab-case)")
    parser.add_argument("--package-name", default=None, help="new import package name")
    parser.add_argument("--project-description", default="", help="new project description")
    parser.add_argument("--author-name", required=True, help="new author name")
    parser.add_argument("--author-email", required=True, help="new author email")
    parser.add_argument("--github-user", required=True, help="new GitHub username")
    parser.add_argument(
        "--python-min",
        default="3.11",
        choices=["3.11", "3.12", "3.13", "3.14"],
        help="minimum supported Python version",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write changes to disk (default is a dry run)",
    )
    return parser


def _validate_names(project_name: str, package_name: str) -> str | None:
    if not _is_valid_project_name(project_name):
        return f"error: {project_name!r} is not a PEP 503 normalisable project name"
    if not package_name.isidentifier() or keyword.iskeyword(package_name):
        return f"error: {package_name!r} is not a valid Python identifier"
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project_name: str = args.project_name
    package_name: str = args.package_name or project_name.replace("-", "_")

    error = _validate_names(project_name, package_name)
    if error is not None:
        print(error, file=sys.stderr)
        return 2

    plan = RenamePlan(
        project_name=project_name,
        package_name=package_name,
        project_description=args.project_description,
        author_name=args.author_name,
        author_email=args.author_email,
        github_user=args.github_user,
        python_min=args.python_min,
    )

    root = Path.cwd()
    files_touched: list[Path] = []
    total_replacements = 0

    for path in _iter_candidate_files(root):
        text = _read_text_if_utf8(path)
        if text is None:
            continue
        new_text, count = _transform_file(path, text, plan)
        if count == 0:
            continue
        files_touched.append(path)
        total_replacements += count
        if args.apply:
            path.write_text(new_text, encoding="utf-8")

    old_package_dir = root / "src" / "skeletal"
    new_package_dir = root / "src" / package_name
    will_rename_package = old_package_dir.is_dir() and old_package_dir != new_package_dir

    copier_file = root / "copier.yml"
    self_file = root / "scripts" / "rename_project.py"
    self_test_file = root / "tests" / "test_rename_project.py"
    generator_files = [f for f in (copier_file, self_file, self_test_file) if f.is_file()]

    print(f"{'Applying' if args.apply else 'Planned (dry run)'} changes:")
    for path in files_touched:
        print(f"  edit {path.relative_to(root)}")
    if will_rename_package:
        old_rel = old_package_dir.relative_to(root)
        new_rel = new_package_dir.relative_to(root)
        print(f"  rename {old_rel} -> {new_rel}")
    for path in generator_files:
        print(f"  delete {path.relative_to(root)}")
    print(f"Files touched: {len(files_touched)}, replacements made: {total_replacements}")

    if not args.apply:
        return 0

    if will_rename_package:
        old_package_dir.rename(new_package_dir)

    for path in generator_files:
        path.unlink(missing_ok=True)
    _remove_empty_scripts_dir(root)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
