"""Nightly process.sh commits only the vault and never pushes (B-08).

`git add -A` over the whole repo once swept half-done code into
"process daily" commits, and `origin` is someone else's upstream.
"""

import pathlib
import re

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "process.sh"


def _code_lines():
    return [
        line.strip()
        for line in SCRIPT.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_never_pushes():
    assert not [line for line in _code_lines() if "git push" in line]


def test_every_git_add_is_scoped_to_vault():
    adds = [line for line in _code_lines() if re.search(r"\bgit add\b", line)]
    assert adds, "process.sh must still commit vault changes"
    assert all(line.endswith("git add -A -- vault") for line in adds), adds


def test_every_commit_is_scoped_to_vault():
    commits = [line for line in _code_lines() if re.search(r"\bgit commit\b", line)]
    assert commits
    assert all("-- vault" in line for line in commits), commits


def test_vault_snapshot_taken_before_processing():
    text = SCRIPT.read_text()
    snap = text.index('vault-$TODAY.tgz')
    assert snap < text.index("d_brain.pipeline daily")
    assert snap < text.index("empty daily, graph-only")


def test_backup_dir_closed_to_group():
    code = "\n".join(_code_lines())
    assert 'chmod 700 "$BACKUP_DIR"' in code
    assert re.search(r"umask 077;\s*tar -czf", code)
