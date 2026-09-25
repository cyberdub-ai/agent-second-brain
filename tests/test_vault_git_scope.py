"""/process commits only the vault and never pushes (B-14).

`vault/` sits inside the project repo, so an unscoped `git add -A` from the
vault swept project code into "process daily" commits (same hole as A-08).
"""

import pathlib
import subprocess

from d_brain.services.git import VaultGit

HANDLER = (
    pathlib.Path(__file__).resolve().parent.parent
    / "src" / "d_brain" / "bot" / "handlers" / "process.py"
)


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def test_process_handler_never_pushes():
    assert "commit_and_push" not in HANDLER.read_text()


def test_commit_changes_stays_inside_vault(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("note")
    (tmp_path / "code.py").write_text("half-done")

    assert VaultGit(vault).commit_changes("chore: process daily")

    committed = _git(tmp_path, "show", "--name-only", "--format=", "HEAD").split()
    assert committed == ["vault/note.md"]
    assert "?? code.py" in _git(tmp_path, "status", "--porcelain")


def test_no_vault_changes_means_no_commit(tmp_path):
    _git(tmp_path, "init", "-q")
    vault = tmp_path / "vault"
    vault.mkdir()
    (tmp_path / "code.py").write_text("outside")

    assert not VaultGit(vault).commit_changes("chore: process daily")
