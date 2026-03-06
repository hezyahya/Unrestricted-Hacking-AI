"""
agent/tools.py
──────────────
Tool execution layer — every "action" the AI picks routes through here.
Each function runs against the live E2B sandbox and returns a string
that gets fed back to the AI as the next observation.
"""

from __future__ import annotations
import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from e2b import Sandbox
    from config.settings import Settings


# ─── ANSI color helpers ───────────────────────────────────────────────────────
class C:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    PURPLE = "\033[95m"
    DIM    = "\033[90m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"


def _box(title: str, body: str, color: str = C.CYAN) -> None:
    width = 68
    print(f"\n{color}┌─ {title} {'─' * (width - len(title) - 3)}┐{C.RESET}")
    for line in body.splitlines()[:40]:  # cap display lines
        print(f"{color}│{C.RESET} {line}")
    print(f"{color}└{'─' * (width)}┘{C.RESET}")


# ─── Tool: execute_command ────────────────────────────────────────────────────

def execute_command(sandbox: "Sandbox", settings: "Settings",
                    command: str, timeout: int = 120) -> str:
    """Run a shell command in the E2B sandbox. Returns stdout+stderr."""

    _box("⚡ EXECUTE", command, C.YELLOW)

    try:
        result = sandbox.commands.run(command, timeout=timeout)
        raw = f"EXIT_CODE: {result.exit_code}\n"
        if result.stdout:
            raw += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            raw += f"STDERR:\n{result.stderr}\n"

        # Truncate if massive
        if len(raw) > settings.MAX_OUTPUT_CHARS:
            half = settings.MAX_OUTPUT_CHARS // 2
            raw = raw[:half] + f"\n\n[... OUTPUT TRUNCATED — {len(raw)} chars total ...]\n\n" + raw[-1500:]

        _box("📤 OUTPUT", raw[:1500], C.DIM)
        return raw

    except Exception as e:
        err = f"TOOL_ERROR: execute_command failed — {e}"
        print(f"{C.RED}{err}{C.RESET}")
        return err


# ─── Tool: write_file ─────────────────────────────────────────────────────────

def write_file(sandbox: "Sandbox", path: str, content: str) -> str:
    """Write a file to the sandbox filesystem."""
    try:
        sandbox.files.write(path, content)
        msg = f"✓ File written: {path} ({len(content)} bytes)"
        print(f"{C.GREEN}{msg}{C.RESET}")
        return msg
    except Exception as e:
        err = f"TOOL_ERROR: write_file failed — {e}"
        print(f"{C.RED}{err}{C.RESET}")
        return err


# ─── Tool: read_file ──────────────────────────────────────────────────────────

def read_file(sandbox: "Sandbox", settings: "Settings", path: str) -> str:
    """Read a file from the sandbox. Returns contents (capped)."""
    try:
        content = sandbox.files.read(path)
        if len(content) > settings.MAX_OUTPUT_CHARS:
            content = content[:settings.MAX_OUTPUT_CHARS] + "\n[... FILE TRUNCATED ...]"
        print(f"{C.GREEN}✓ Read: {path} ({len(content)} chars){C.RESET}")
        return content
    except Exception as e:
        err = f"TOOL_ERROR: read_file failed — {e}"
        print(f"{C.RED}{err}{C.RESET}")
        return err


# ─── Tool: report_finding ─────────────────────────────────────────────────────

SEVERITY_COLORS = {
    "CRITICAL": C.RED,
    "HIGH":     "\033[38;5;208m",   # orange
    "MEDIUM":   C.YELLOW,
    "LOW":      C.CYAN,
    "INFO":     C.DIM,
}

def report_finding(findings_log: list,
                   severity: str,
                   title: str,
                   description: str,
                   proof: str = "",
                   remediation: str = "") -> str:
    """Log a finding to memory + display it prominently."""

    entry = {
        "id":           len(findings_log) + 1,
        "severity":     severity.upper(),
        "title":        title,
        "description":  description,
        "proof":        proof,
        "remediation":  remediation,
        "timestamp":    datetime.now().isoformat(),
    }
    findings_log.append(entry)

    color = SEVERITY_COLORS.get(severity.upper(), C.DIM)
    body  = (
        f"Title:       {title}\n"
        f"Severity:    {severity}\n"
        f"Description: {description}\n"
        f"Proof:       {proof}\n"
        f"Remediation: {remediation}"
    )
    _box(f"🚨 FINDING #{entry['id']} — {severity}", body, color)

    return f"Finding #{entry['id']} logged: [{severity}] {title}"


# ─── Tool: mission_complete ───────────────────────────────────────────────────

def mission_complete(summary: str) -> str:
    _box("✅ MISSION COMPLETE", summary, C.GREEN)
    return "__MISSION_COMPLETE__"


# ─── Dispatcher ───────────────────────────────────────────────────────────────

def dispatch(action: str, args: dict,
             sandbox: "Sandbox",
             settings: "Settings",
             findings_log: list) -> str:
    """Route an AI action to the correct tool function."""

    if action == "execute_command":
        return execute_command(
            sandbox, settings,
            command=args.get("command", "echo 'no command given'"),
            timeout=int(args.get("timeout", settings.CMD_TIMEOUT))
        )

    elif action == "write_file":
        return write_file(
            sandbox,
            path=args.get("path", "/tmp/phantom_file"),
            content=args.get("content", "")
        )

    elif action == "read_file":
        return read_file(
            sandbox, settings,
            path=args.get("path", "/tmp/phantom_file")
        )

    elif action == "report_finding":
        return report_finding(
            findings_log,
            severity=args.get("severity", "INFO"),
            title=args.get("title", "Untitled"),
            description=args.get("description", ""),
            proof=args.get("proof", ""),
            remediation=args.get("remediation", "")
        )

    elif action == "mission_complete":
        return mission_complete(summary=args.get("summary", "Engagement complete."))

    else:
        return f"TOOL_ERROR: Unknown action '{action}'"
