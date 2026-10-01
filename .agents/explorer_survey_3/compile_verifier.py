#!/usr/bin/env python3
"""
MetaEditor64 Compilation Verification Harness & Log Parser.
Used for zero-defect verification of MQL5 Expert Advisors.
"""

import sys
import subprocess
import os
import re
from pathlib import Path

METAEDITOR_PATH = r"C:\Program Files\MetaTrader 5\MetaEditor64.exe"

def compile_mq5(source_path: str, log_path: str = None) -> dict:
    source_p = Path(source_path).resolve()
    if not source_p.exists():
        return {
            "success": False,
            "error": f"Source file does not exist: {source_p}",
            "errors_count": 1,
            "warnings_count": 0,
            "lines": []
        }
    
    if not os.path.exists(METAEDITOR_PATH):
        return {
            "success": False,
            "error": f"MetaEditor64.exe not found at: {METAEDITOR_PATH}",
            "errors_count": 1,
            "warnings_count": 0,
            "lines": []
        }
        
    if log_path is None:
        log_p = source_p.with_suffix(".log")
    else:
        log_p = Path(log_path).resolve()
        
    if log_p.exists():
        try:
            log_p.unlink()
        except Exception:
            pass
            
    cmd = [METAEDITOR_PATH, f"/compile:{str(source_p)}", f"/log:{str(log_p)}"]
    
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Compilation timed out after 60s",
            "errors_count": 1,
            "warnings_count": 0,
            "lines": []
        }
        
    if not log_p.exists():
        return {
            "success": False,
            "error": f"Log file was not generated at: {log_p}",
            "errors_count": 1,
            "warnings_count": 0,
            "lines": []
        }
        
    # Read UTF-16 log file
    try:
        content = log_p.read_text(encoding="utf-16")
    except UnicodeError:
        try:
            content = log_p.read_text(encoding="utf-16-le")
        except UnicodeError:
            content = log_p.read_text(encoding="utf-8", errors="replace")
            
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    
    errors = []
    warnings = []
    result_line = ""
    
    result_regex = re.compile(r"Result:\s*(\d+)\s+errors,\s*(\d+)\s+warnings", re.IGNORECASE)
    error_regex = re.compile(r":\s*error\s+\d+:", re.IGNORECASE)
    warning_regex = re.compile(r":\s*warning\s+\d+:", re.IGNORECASE)
    
    errors_count = 0
    warnings_count = 0
    
    for line in lines:
        m = result_regex.search(line)
        if m:
            result_line = line
            errors_count = int(m.group(1))
            warnings_count = int(m.group(2))
        elif error_regex.search(line):
            errors.append(line)
        elif warning_regex.search(line):
            warnings.append(line)
            
    success = (errors_count == 0 and warnings_count == 0 and (source_p.with_suffix(".ex5").exists()))
    
    return {
        "success": success,
        "source": str(source_p),
        "ex5": str(source_p.with_suffix(".ex5")),
        "ex5_exists": source_p.with_suffix(".ex5").exists(),
        "errors_count": errors_count,
        "warnings_count": warnings_count,
        "result_line": result_line,
        "errors": errors,
        "warnings": warnings,
        "raw_lines": lines
    }

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else r"c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v1.mq5"
    res = compile_mq5(target)
    print(f"Compilation Target: {res.get('source')}")
    print(f"Status: {'PASS' if res['success'] else 'FAIL'}")
    print(f"Result: {res.get('result_line')}")
    print(f"EX5 Generated: {res.get('ex5_exists')}")
    if res.get("errors"):
        print("\nErrors:")
        for err in res["errors"]:
            print(f"  [ERROR] {err}")
    if res.get("warnings"):
        print("\nWarnings:")
        for w in res["warnings"]:
            print(f"  [WARN] {w}")
    sys.exit(0 if res["success"] else 1)
