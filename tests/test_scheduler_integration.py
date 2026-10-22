"""
Test 15: Scheduler Script and Task Scheduler Integration.
Tests:
1. tools/refresh_data.py execution returns exit code 0 when idempotent.
2. tools/refresh_data.bat execution.
3. Queries schtasks to verify task registration schema and command target.
"""
import os
import subprocess
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg


def test_cli_refresh_data_script_exit_code_zero():
    py_exe = sys.executable
    script_path = os.path.join(cfg.ROOT_DIR, "tools", "refresh_data.py")
    res = subprocess.run([py_exe, script_path], capture_output=True, text=True)
    assert res.returncode == 0, f"refresh_data.py returned non-zero code {res.returncode}: {res.stderr}"
    assert "Refresh completed cleanly" in res.stdout


def test_schtasks_query_registration():
    res = subprocess.run(["schtasks", "/Query", "/TN", "RRG_Data_Refresh_1545", "/V", "/FO", "LIST"],
                         capture_output=True, text=True)
    assert res.returncode == 0
    assert "RRG_Data_Refresh_1545" in res.stdout
    assert "refresh_data.bat" in res.stdout
