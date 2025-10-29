#!/usr/bin/env python3
"""
tracelabs_full_report.py

Python 3.10+
Usage:
    python tracelabs_full_report.py --email victim@example.com
    python tracelabs_full_report.py --email victim@example.com --outdir ./work --timeout 600

Description:
- Orchestrates SpiderFoot, Sherlock, Holehe, theHarvester, ExifTool, and Recon-ng where installed.
- Captures each tool's raw output into <outdir>/raw/<tool>_output.*
- Normalizes basic findings and generates tracelabs_full_report.html in outdir.
- Uses only built-in libraries and subprocess.
- Exit codes: 0 success. 2 invalid args. 3 runtime error.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import html
import json
import logging
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---- Config ----
TOOLS = ["spiderfoot", "sherlock", "holehe", "theHarvester", "exiftool", "recon-ng"]
DEFAULT_OUTDIR = "tracelabs_work"
RAW_DIRNAME = "raw"
REPORT_FILENAME = "tracelabs_full_report.html"
DEFAULT_TIMEOUT = 300
MAX_INPUT_LENGTH = 255
# ----------------

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security-related exceptions"""
    pass


class TimeoutError(Exception):
    """Timeout exceptions"""
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def validate_email(email: str) -> bool:
    """Validate email format and length"""
    if len(email) > MAX_INPUT_LENGTH:
        return False
    pattern = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    return bool(pattern.match(email))


def sanitize_input(text: str) -> str:
    """Sanitize input for use in shell commands"""
    if len(text) > MAX_INPUT_LENGTH:
        raise SecurityError(f"Input too long: {len(text)} characters")
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[;&|$`]', '', text)
    return shlex.quote(sanitized)


def validate_domain(domain: str) -> bool:
    """Validate domain format"""
    if len(domain) > MAX_INPUT_LENGTH:
        return False
    pattern = re.compile(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    return bool(pattern.match(domain))


def ensure_dirs(base: str) -> Dict[str, str]:
    """Create necessary directories"""
    base = os.path.abspath(base)
    raw = os.path.join(base, RAW_DIRNAME)
    try:
        os.makedirs(raw, exist_ok=True)
        # Ensure directories are writable
        test_file = os.path.join(raw, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except (OSError, IOError) as e:
        logger.error(f"Directory creation failed: {e}")
        raise
    return {"base": base, "raw": raw}


def which_tool(name: str) -> str | None:
    """Find tool executable with alternative names"""
    tool_alternatives = {
        "spiderfoot": ["spiderfoot", "spiderfoot-cli", "sf.py"],
        "theHarvester": ["theharvester", "theHarvester"],
        "recon-ng": ["recon-ng", "recon"],
        "holehe": ["holehe"],
        "sherlock": ["sherlock"],
        "exiftool": ["exiftool", "exif"]
    }
    
    alternatives = tool_alternatives.get(name, [name])
    for alt in alternatives:
        path = shutil.which(alt)
        if path:
            logger.info(f"Found {name} at {path}")
            return path
    logger.warning(f"Tool not found: {name}")
    return None


def run_subprocess(command: List[str], timeout: int = DEFAULT_TIMEOUT, 
                  input_data: str | None = None) -> Dict[str, Any]:
    """Run subprocess with timeout and proper signal handling"""
    # Set up timeout handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        proc = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
            input=input_data,
            encoding='utf-8',
            errors='ignore'
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.TimeoutExpired as e:
        logger.warning(f"Command timed out: {' '.join(command)}")
        return {"returncode": 124, "stdout": "", "stderr": f"TimeoutExpired: {e}"}
    except Exception as e:
        logger.error(f"Command failed: {' '.join(command)} - Error: {e}")
        return {"returncode": 1, "stdout": "", "stderr": str(e)}
    finally:
        signal.alarm(0)  # Disable the alarm


def try_json_load(text: str) -> Any | None:
    """Safely attempt to parse JSON"""
    if not text.strip():
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.debug(f"JSON parsing failed: {e}")
        return None


def save_raw(outdir_raw: str, tool: str, ext: str, content: str) -> str:
    """Save raw output to file with error handling"""
    try:
        path = os.path.join(outdir_raw, f"{tool}_output.{ext}")
        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(content)
        logger.info(f"Saved raw output: {path}")
        return path
    except IOError as e:
        logger.error(f"Failed to save raw output: {e}")
        raise


def normalize_spiderfoot(data: Any) -> List[Dict[str, Any]]:
    """Normalize SpiderFoot output"""
    results: List[Dict[str, Any]] = []
    if isinstance(data, dict):
        for key in ("events", "data", "results"):
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    if isinstance(item, dict):
                        results.append({
                            "source": "spiderfoot",
                            "type": item.get("type") or item.get("eventType") or "finding",
                            "value": item.get("value") or item.get("name") or str(item),
                            "confidence": item.get("confidence") or "medium",
                            "description": item.get("description", ""),
                            "raw": item,
                        })
                if results:
                    return results
        
        # Fallback: flatten top-level items
        for k, v in data.items():
            if isinstance(v, (str, int, float, bool)):
                results.append({
                    "source": "spiderfoot", 
                    "type": k, 
                    "value": str(v), 
                    "confidence": "medium", 
                    "raw": v
                })
    elif isinstance(data, list):
        for item in data:
            results.append({
                "source": "spiderfoot", 
                "type": "item", 
                "value": str(item), 
                "confidence": "medium", 
                "raw": item
            })
    
    return results


def normalize_sherlock(data: Any) -> List[Dict[str, Any]]:
    """Normalize Sherlock output"""
    results: List[Dict[str, Any]] = []
    
    if isinstance(data, dict):
        for platform, info in data.items():
            if isinstance(info, dict):
                # Modern Sherlock JSON format
                url_user = info.get("url_user", "")
                exists = info.get("exists", False)
                if url_user and exists:
                    results.append({
                        "source": "sherlock",
                        "type": "account",
                        "value": f"{platform}: {url_user}",
                        "confidence": "high",
                        "raw": info
                    })
            elif info:
                # Legacy format
                results.append({
                    "source": "sherlock",
                    "type": "account",
                    "value": platform,
                    "confidence": "high",
                    "raw": info
                })
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                results.append({
                    "source": "sherlock", 
                    "type": "account", 
                    "value": str(item.get("url_user", item)),
                    "confidence": "medium", 
                    "raw": item
                })
    
    # Parse text output as fallback
    if not results:
        text = str(data)
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if "[+]" in line and ":" in line:
                # Format: [+] username: https://platform.com/username
                parts = line.split(":", 1)
                if len(parts) == 2:
                    platform = parts[0].replace("[+]", "").strip()
                    url = parts[1].strip()
                    results.append({
                        "source": "sherlock",
                        "type": "account",
                        "value": f"{platform}: {url}",
                        "confidence": "high",
                        "raw": line
                    })
    
    return results


def normalize_holehe(data: Any) -> List[Dict[str, Any]]:
    """Normalize Holehe output"""
    results: List[Dict[str, Any]] = []
    
    if isinstance(data, dict):
        for service, info in data.items():
            if isinstance(info, dict):
                exists = info.get("exists", False)
                email_recovery = info.get("emailrecovery")
                if exists:
                    results.append({
                        "source": "holehe",
                        "type": "breached_account",
                        "value": f"{service}: {email_recovery or 'Account exists'}",
                        "confidence": "high",
                        "raw": info
                    })
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                results.append({
                    "source": "holehe", 
                    "type": "service", 
                    "value": str(item),
                    "confidence": "medium", 
                    "raw": item
                })
    
    # Parse text output
    if not results:
        text = str(data)
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if "]" in line and ":" in line:
                # Format: [x] Service: Status
                parts = line.split(":", 1)
                if len(parts) == 2:
                    service = parts[0].split("]")[1].strip()
                    status = parts[1].strip()
                    if "exists" in status.lower() or "ok" in status.lower():
                        results.append({
                            "source": "holehe",
                            "type": "breached_account",
                            "value": f"{service}: {status}",
                            "confidence": "medium",
                            "raw": line
                        })
    
    return results


def normalize_theharvester(data: Any) -> List[Dict[str, Any]]:
    """Normalize theHarvester output"""
    results: List[Dict[str, Any]] = []
    text = ""
    
    if isinstance(data, (dict, list)):
        text = json.dumps(data, indent=2)
    else:
        text = str(data)
    
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, line)
        for email in emails:
            results.append({
                "source": "theHarvester",
                "type": "email",
                "value": email,
                "confidence": "medium",
                "raw": line
            })
        
        # Extract hosts/subdomains
        if line and not any(email in line for email in emails):
            if "." in line and " " not in line and len(line) < 100:
                results.append({
                    "source": "theHarvester",
                    "type": "host",
                    "value": line,
                    "confidence": "low",
                    "raw": line
                })
    
    return results


def normalize_exiftool(data: Any) -> List[Dict[str, Any]]:
    """Normalize ExifTool output"""
    results: List[Dict[str, Any]] = []
    
    if isinstance(data, list):
        for obj in data:
            if isinstance(obj, dict):
                filename = obj.get("SourceFile", "unknown")
                # Extract interesting metadata
                interesting_fields = {
                    "GPSPosition": obj.get("GPSPosition"),
                    "CreateDate": obj.get("CreateDate"),
                    "ModifyDate": obj.get("ModifyDate"),
                    "Software": obj.get("Software"),
                    "Author": obj.get("Author"),
                    "Creator": obj.get("Creator"),
                }
                for field, value in interesting_fields.items():
                    if value:
                        results.append({
                            "source": "exiftool",
                            "type": "metadata",
                            "value": f"{filename}: {field}={value}",
                            "confidence": "high",
                            "raw": obj
                        })
    elif isinstance(data, dict):
        results.append({
            "source": "exiftool",
            "type": "metadata",
            "value": json.dumps(data),
            "confidence": "medium",
            "raw": data
        })
    
    return results


def normalize_reconng(data: Any) -> List[Dict[str, Any]]:
    """Normalize Recon-ng output"""
    results: List[Dict[str, Any]] = []
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # Parse CSV-like output
                host = item.get("host") or item.get("ip") or item.get("domain")
                if host:
                    results.append({
                        "source": "recon-ng",
                        "type": "host",
                        "value": str(host),
                        "confidence": "medium",
                        "raw": item
                    })
    elif isinstance(data, dict):
        results.append({
            "source": "recon-ng",
            "type": "export",
            "value": json.dumps(data),
            "confidence": "medium",
            "raw": data
        })
    else:
        # Parse text output
        text = str(data)
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" in line and not line.startswith("[+"):
                results.append({
                    "source": "recon-ng",
                    "type": "info",
                    "value": line,
                    "confidence": "low",
                    "raw": line
                })
    
    return results


NORMALIZERS = {
    "spiderfoot": normalize_spiderfoot,
    "sherlock": normalize_sherlock,
    "holehe": normalize_holehe,
    "theHarvester": normalize_theharvester,
    "exiftool": normalize_exiftool,
    "recon-ng": normalize_reconng,
}


def attempt_tool_run(tool: str, email: str, username: str, domain: str, 
                    rawdir: str, timeout: int) -> Dict[str, Any]:
    """Execute tool with proper error handling and security measures"""
    found_path = which_tool(tool)
    status = {
        "installed": bool(found_path), 
        "path": found_path, 
        "attempted_cmd": None, 
        "run_result": None, 
        "raw_path": None
    }
    
    if not found_path:
        return status

    try:
        # Sanitize inputs
        safe_username = sanitize_input(username)
        safe_domain = sanitize_input(domain)
        safe_email = sanitize_input(email)

        if tool == "sherlock":
            out_json = os.path.join(rawdir, "sherlock_output.json")
            cmd = [found_path, safe_username, "--json", out_json, "--timeout", "10"]
            status["attempted_cmd"] = cmd
            res = run_subprocess(cmd, timeout=timeout)
            
            if res["returncode"] == 0 and os.path.exists(out_json):
                status["raw_path"] = out_json
                status["run_result"] = {"type": "file_json", "content": None}
            else:
                # Fallback to stdout
                cmd2 = [found_path, safe_username, "--timeout", "10"]
                status["attempted_cmd"] = cmd2
                res = run_subprocess(cmd2, timeout=timeout)
                status["run_result"] = {"type": "stdout", "content": res}

        elif tool == "holehe":
            cmd = [found_path, safe_email, "--no-color"]
            status["attempted_cmd"] = cmd
            res = run_subprocess(cmd, timeout=timeout)
            
            if res["returncode"] == 0:
                status["run_result"] = {"type": "stdout", "content": res}
            else:
                # Try with JSON output
                cmd2 = [found_path, safe_email, "--json"]
                status["attempted_cmd"] = cmd2
                res = run_subprocess(cmd2, timeout=timeout)
                status["run_result"] = {"type": "stdout", "content": res}

        elif tool == "theHarvester":
            out_file = os.path.join(rawdir, "theharvester_output")
            cmd = [found_path, "-d", safe_domain, "-b", "all", "-f", out_file]
            status["attempted_cmd"] = cmd
            res = run_subprocess(cmd, timeout=timeout)
            status["run_result"] = {"type": "stdout", "content": res}
            
            # Check for generated files
            for ext in [".xml", ".html", ".txt"]:
                possible_file = out_file + ext
                if os.path.exists(possible_file):
                    status["raw_path"] = possible_file
                    break

        elif tool == "exiftool":
            artifacts_dir = os.path.join(os.getcwd(), "artifacts")
            if os.path.isdir(artifacts_dir):
                cmd = [found_path, "-json", artifacts_dir]
                status["attempted_cmd"] = cmd
                res = run_subprocess(cmd, timeout=timeout)
                if res["stdout"].strip():
                    status["raw_path"] = save_raw(rawdir, "exiftool", "json", res["stdout"])
                    status["run_result"] = {"type": "stdout", "content": res}
                else:
                    status["run_result"] = {"type": "stdout", "content": res}
            else:
                status["run_result"] = {"type": "skipped", "reason": f"No artifacts directory at {artifacts_dir}"}

        elif tool == "spiderfoot":
            out_json = os.path.join(rawdir, "spiderfoot_output.json")
            cmd = [found_path, "-s", safe_email, "-o", "json", "-q"]
            status["attempted_cmd"] = cmd
            res = run_subprocess(cmd, timeout=max(timeout, 600))  # SpiderFoot needs more time
            
            if res["returncode"] == 0 and res["stdout"].strip():
                status["raw_path"] = save_raw(rawdir, "spiderfoot", "json", res["stdout"])
                status["run_result"] = {"type": "stdout", "content": res}
            else:
                status["run_result"] = {"type": "stdout", "content": res}

        elif tool == "recon-ng":
            # Create proper recon-ng workflow
            rc_commands = [
                "workspaces create tracelabs_temp",
                f"add domains {safe_domain}",
                "use recon/domains-hosts/google_site_web",
                "run",
                "use recon/domains-hosts/bing_domain_web",
                "run", 
                "use recon/hosts-hosts/resolve",
                "run",
                "use reporting/csv",
                "set TABLE hosts",
                "set FILENAME /dev/stdout",
                "run",
                "exit"
            ]
            
            rc_content = "\n".join(rc_commands)
            status["attempted_cmd"] = ["recon-ng", "-r", "commands.rc"]
            res = run_subprocess([found_path], input_data=rc_content, timeout=timeout)
            status["run_result"] = {"type": "stdout", "content": res}

        # Save stdout if we have content but no raw_path
        rr = status.get("run_result")
        if rr and rr.get("type") == "stdout" and not status.get("raw_path"):
            content = rr["content"]["stdout"] if isinstance(rr["content"], dict) else str(rr["content"])
            if content.strip():
                ext = "json" if try_json_load(content) is not None else "txt"
                status["raw_path"] = save_raw(rawdir, tool, ext, content)

    except SecurityError as e:
        logger.error(f"Security error running {tool}: {e}")
        status["error"] = f"Security violation: {e}"
    except Exception as e:
        logger.error(f"Unexpected error running {tool}: {e}")
        status["error"] = str(e)

    return status


def read_raw_file(path: str) -> str:
    """Safely read raw output file"""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read {path}: {e}")
        return ""


def parse_and_normalize(tool: str, raw_path: str, run_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse and normalize tool output"""
    content = ""
    if raw_path and os.path.exists(raw_path):
        content = read_raw_file(raw_path)
    elif run_result and run_result.get("type") == "stdout":
        content = run_result["content"]["stdout"]
    
    parsed = try_json_load(content)
    normalizer = NORMALIZERS.get(
        tool, 
        lambda d: [{
            "source": tool, 
            "type": "raw", 
            "value": str(d), 
            "confidence": "medium", 
            "raw": d
        }]
    )
    
    try:
        return normalizer(parsed if parsed is not None else content)
    except Exception as e:
        logger.error(f"Normalization failed for {tool}: {e}")
        return [{
            "source": tool,
            "type": "error",
            "value": f"Normalization error: {e}",
            "confidence": "low",
            "raw": content[:1000]  # Truncate very long content
        }]


def group_by_confidence(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group findings by confidence level"""
    groups = {"high": [], "medium": [], "low": []}
    for it in items:
        conf = str(it.get("confidence", "")).lower()
        if "high" in conf:
            groups["high"].append(it)
        elif "low" in conf:
            groups["low"].append(it)
        else:
            groups["medium"].append(it)
    return groups


def generate_html_report(outdir: str, email: str, tool_statuses: Dict[str, Any], 
                        findings: List[Dict[str, Any]]) -> str:
    """Generate comprehensive HTML report"""
    gen_time = datetime.datetime.utcnow().isoformat(sep=" ", timespec="seconds") + " UTC"
    total = len(findings)
    groups = group_by_confidence(findings)
    
    # Enhanced CSS
    css = """
    body { font-family: Arial, Helvetica, sans-serif; margin: 20px; background: #f5f5f5; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { color: #34495e; margin-top: 25px; }
    h3 { color: #7f8c8d; }
    .summary { background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; font-size: 14px; }
    th, td { border: 1px solid #bdc3c7; padding: 8px 12px; text-align: left; }
    th { background: #3498db; color: white; }
    tr:nth-child(even) { background: #f8f9fa; }
    .toolbox { background: #d5edf7; padding: 10px; border-radius: 5px; margin-bottom: 15px; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 5px; }
    .badge.installed { background: #27ae60; color: white; }
    .badge.missing { background: #e74c3c; color: white; }
    .badge.error { background: #f39c12; color: white; }
    .raw { white-space: pre-wrap; background: #2c3e50; color: #ecf0f1; padding: 12px; border-radius: 5px; overflow: auto; max-height: 400px; font-family: monospace; font-size: 12px; }
    .confidence-high { border-left: 4px solid #27ae60; }
    .confidence-medium { border-left: 4px solid #f39c12; }
    .confidence-low { border-left: 4px solid #e74c3c; }
    .count { font-weight: bold; color: #3498db; }
    """
    
    parts: List[str] = []
    parts.append("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>")
    parts.append("<title>TraceLabs Unified OSINT Report</title>")
    parts.append(f"<style>{css}</style></head><body>")
    parts.append("<div class='container'>")
    
    # Header
    parts.append("<h1>🔍 TraceLabs Unified OSINT Report</h1>")
    parts.append(f"<div class='summary'><strong>Target Email:</strong> {html.escape(email)}<br>")
    parts.append(f"<strong>Generated:</strong> {gen_time}<br>")
    parts.append(f"<strong>Total Findings:</strong> <span class='count'>{total}</span></div>")

    # Tool status
    parts.append("<h2>🛠️ Tool Status</h2>")
    parts.append("<div class='toolbox'>")
    for tool, status in tool_statuses.items():
        installed = status.get("installed", False)
        has_error = "error" in status
        if has_error:
            badge_class = "error"
            badge_text = "error"
        elif installed:
            badge_class = "installed"
            badge_text = "installed"
        else:
            badge_class = "missing"
            badge_text = "missing"
        
        parts.append(f"<span class='badge {badge_class}'>{html.escape(tool)}: {badge_text}</span> ")
    parts.append("</div>")

    # Summary counts
    counts: Dict[str, int] = {}
    for f in findings:
        counts[f["source"]] = counts.get(f["source"], 0) + 1
    
    parts.append("<h2>📊 Summary by Tool</h2>")
    parts.append("<table><tr><th>Tool</th><th>Findings</th></tr>")
    for tool in TOOLS:
        count = counts.get(tool, 0)
        parts.append(f"<tr><td>{html.escape(tool)}</td><td><span class='count'>{count}</span></td></tr>")
    parts.append("</table>")

    # Findings by confidence
    for conf_level in ("high", "medium", "low"):
        conf_findings = groups[conf_level]
        parts.append(f"<h2>🎯 {conf_level.title()} Confidence Findings ({len(conf_findings)})</h2>")
        
        if conf_findings:
            parts.append(f"<div class='confidence-{conf_level}'>")
            parts.append("<table><tr><th>Source</th><th>Type</th><th>Value</th></tr>")
            for finding in conf_findings:
                value = html.escape(str(finding.get("value", "")))
                parts.append(f"<tr><td>{html.escape(finding.get('source',''))}</td>")
                parts.append(f"<td>{html.escape(str(finding.get('type','')))}</td>")
                parts.append(f"<td>{value}</td></tr>")
            parts.append("</table></div>")
        else:
            parts.append(f"<p>No {conf_level} confidence findings.</p>")

    # Raw outputs
    parts.append("<h2>📋 Raw Tool Outputs</h2>")
    for tool, status in tool_statuses.items():
        parts.append(f"<h3>{html.escape(tool)}</h3>")
        
        if not status.get("installed"):
            parts.append("<p>Tool not installed on PATH.</p>")
            continue
        
        if "error" in status:
            parts.append(f"<p>Error: {html.escape(status['error'])}</p>")
        
        raw_path = status.get("raw_path")
        if raw_path and os.path.exists(raw_path):
            content = read_raw_file(raw_path)
            if content.strip():
                parts.append(f"<div class='raw'>{html.escape(content)}</div>")
            else:
                parts.append("<p>Raw output file is empty.</p>")
        else:
            run_result = status.get("run_result")
            if run_result and run_result.get("type") == "stdout":
                content = run_result["content"]
                stdout = content.get("stdout", "") if isinstance(content, dict) else ""
                stderr = content.get("stderr", "") if isinstance(content, dict) else ""
                output = f"{stdout}\n\nSTDERR:\n{stderr}".strip()
                if output:
                    parts.append(f"<div class='raw'>{html.escape(output)}</div>")
                else:
                    parts.append("<p>No output captured.</p>")
            else:
                parts.append("<p>No raw output available.</p>")

    parts.append("</div></body></html>")
    
    html_out = "\n".join(parts)
    outpath = os.path.join(outdir, REPORT_FILENAME)
    
    try:
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(html_out)
        logger.info(f"Report generated: {outpath}")
        return outpath
    except IOError as e:
        logger.error(f"Failed to write report: {e}")
        raise


def main(argv: List[str] | None = None) -> int:
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="TraceLabs unified OSINT report generator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--email", required=True, help="Target email address.")
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help="Output working directory.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, 
                       help=f"Tool execution timeout in seconds (default: {DEFAULT_TIMEOUT}).")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    
    args = parser.parse_args(argv)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate inputs
    email = args.email.strip()
    if not validate_email(email):
        eprint("❌ Invalid email format.")
        return 2
    
    if args.timeout < 30:
        eprint("❌ Timeout must be at least 30 seconds.")
        return 2
    
    try:
        username, domain = email.split("@", 1)
        if not validate_domain(domain):
            logger.warning(f"Domain validation warning: {domain}")
    except ValueError:
        eprint("❌ Invalid email format.")
        return 2
    
    logger.info(f"Starting OSINT collection for: {email}")
    logger.info(f"Output directory: {args.outdir}")
    logger.info(f"Timeout: {args.timeout}s")
    
    try:
        dirs = ensure_dirs(args.outdir)
        rawdir = dirs["raw"]
    except Exception as e:
        eprint(f"❌ Failed to create directories: {e}")
        return 3

    tool_statuses: Dict[str, Any] = {}
    all_findings: List[Dict[str, Any]] = []

    # Execute tools
    for tool in TOOLS:
        logger.info(f"Running {tool}...")
        try:
            status = attempt_tool_run(tool, email, username, domain, rawdir, args.timeout)
            tool_statuses[tool] = status
            
            # Parse results
            findings = parse_and_normalize(
                tool, 
                status.get("raw_path") or "", 
                status.get("run_result") or {}
            )
            
            # Add context
            for finding in findings:
                finding.setdefault("target_email", email)
                finding.setdefault("derived_username", username)
                finding.setdefault("derived_domain", domain)
            
            all_findings.extend(findings)
            logger.info(f"{tool}: {len(findings)} findings")
            
        except Exception as exc:
            logger.error(f"Tool {tool} failed: {exc}")
            tool_statuses[tool] = {
                "installed": which_tool(tool) is not None, 
                "error": str(exc)
            }

    # Generate report
    try:
        report_path = generate_html_report(dirs["base"], email, tool_statuses, all_findings)
        print(f"✅ Report generated: {report_path}")
        print(f"📊 Total findings: {len(all_findings)}")
        
        # Print summary
        counts = {}
        for f in all_findings:
            counts[f["source"]] = counts.get(f["source"], 0) + 1
        
        print("\nFindings by tool:")
        for tool in TOOLS:
            count = counts.get(tool, 0)
            print(f"  {tool}: {count}")
            
        return 0
        
    except Exception as exc:
        eprint(f"❌ Failed to generate report: {exc}")
        return 3


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(3)
