import json
import re
from pathlib import Path

import pytest

from skeletal.cli import main


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--version"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert re.match(r"^skeletal \d+\.\d+", captured.out)


def test_info_json(capsys: pytest.CaptureFixture[str], tmp_cwd: Path) -> None:
    exit_code = main(["info", "--json"])
    captured = capsys.readouterr()
    assert exit_code == 0
    data = json.loads(captured.out)
    assert data["app_name"] == "skeletal"


def test_info_table(capsys: pytest.CaptureFixture[str], tmp_cwd: Path) -> None:
    exit_code = main(["info"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "app_name" in captured.out


def test_run_iterations(tmp_cwd: Path) -> None:
    exit_code = main(["run", "--iterations", "3"])
    assert exit_code == 0
    log_file = tmp_cwd / "logs" / "app.log"
    assert log_file.is_file()
    content = log_file.read_text(encoding="utf-8")
    assert content.count("iteration") == 3


def test_run_zero_iterations_is_usage_error(tmp_cwd: Path) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["run", "--iterations", "0"])
    assert exc_info.value.code == 2


def test_bogus_command_is_usage_error(tmp_cwd: Path) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["bogus"])
    assert exc_info.value.code == 2


def test_run_failure_returns_one(
    monkeypatch: pytest.MonkeyPatch, tmp_cwd: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def _boom(_iterations: int) -> None:
        message = "boom"
        raise RuntimeError(message)

    monkeypatch.setattr("skeletal.cli._run_workload", _boom)
    exit_code = main(["run", "--iterations", "1"])
    assert exit_code == 1
