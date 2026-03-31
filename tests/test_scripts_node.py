from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def test_patch_workflow_script_syntax(repo_root: Path) -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    script = repo_root / "scripts" / "patch-workflow-ai-rate-limit.js"
    r = subprocess.run(
        [node, "--check", str(script)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
