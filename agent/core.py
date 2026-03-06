"""
agent/core.py
─────────────
The main ReAct (Reason → Act → Observe) loop.

Flow:
  1. Build messages list with system prompt + mission
  2. Call OpenRouter (dolphin-deepseek-r1) → get JSON response
  3. Parse JSON → extract action + args
  4. Dispatch action to tools.py → get observation string
  5. Append observation to messages → loop back to 2
  6. Stop when AI calls mission_complete OR max_iterations hit
  7. Save JSON report to ./reports/
"""

from __future__ import annotations
import json
import os
import re
import sys
from datetime import datetime
from openai import OpenAI  # OpenRouter uses OpenAI-compatible API

from agent.prompts import SYSTEM_PROMPT, build_mission_prompt
from agent import tools
from config.settings import Settings

try:
    from e2b import Sandbox
except ImportError:
    print("\033[91m[ERROR] e2b not installed. Run: pip install e2b\033[0m")
    sys.exit(1)


# ─── ANSI helpers (re-use same palette as tools.py) ──────────────────────────
class C:
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    PURPLE = "\033[95m"
    DIM    = "\033[90m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"


# ─── PhantomAgent ─────────────────────────────────────────────────────────────

class PhantomAgent:

    def __init__(self, settings: Settings):
        self.settings = settings
        self.findings: list[dict] = []
        self.sandbox: Sandbox | None = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # OpenRouter client (OpenAI-compatible)
        self.client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )

    # ── Sandbox lifecycle ──────────────────────────────────────────────

    def _start_sandbox(self) -> None:
        print(f"{C.CYAN}[*] Spinning up E2B sandbox...{C.RESET}")
        self.sandbox = Sandbox(timeout=self.settings.SANDBOX_TIMEOUT)
        print(f"{C.GREEN}[+] Sandbox ready  id={self.sandbox.sandbox_id}{C.RESET}")

        # Install common pentest tools on first boot
        print(f"{C.YELLOW}[*] Installing base toolset (background)...{C.RESET}")
        install_cmd = (
            "apt-get update -qq && "
            "apt-get install -y -qq nmap curl wget whois dnsutils python3-pip git "
            "nikto sqlmap hydra gobuster ffuf netcat-openbsd && "
            "pip install -q wafw00f && "
            "GO111MODULE=on go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest 2>/dev/null; "
            "GO111MODULE=on go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest 2>/dev/null; "
            "GO111MODULE=on go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest 2>/dev/null; "
            "echo 'TOOLSET_READY'"
        )
        # Fire-and-forget — AI can still start while tools install
        self.sandbox.commands.run(install_cmd, timeout=300)
        print(f"{C.GREEN}[+] Base toolset installed{C.RESET}")

    def _stop_sandbox(self) -> None:
        if self.sandbox:
            try:
                self.sandbox.kill()
                print(f"{C.DIM}[*] Sandbox terminated{C.RESET}")
            except Exception:
                pass

    # ── AI call ───────────────────────────────────────────────────────

    def _call_ai(self, messages: list[dict]) -> str:
        """Call OpenRouter and return the raw text response."""
        response = self.client.chat.completions.create(
            model=self.settings.MODEL_ID,
            messages=messages,
            temperature=self.settings.TEMPERATURE,
            max_tokens=self.settings.MAX_TOKENS,
            extra_headers={
                "HTTP-Referer": "https://phantom-agent.local",
                "X-Title": "PhantomAgent",
            }
        )
        return response.choices[0].message.content or ""

    # ── JSON parser (fault-tolerant) ──────────────────────────────────

    def _parse_action(self, raw: str) -> dict | None:
        """
        Extract a JSON object from the AI response.
        Handles: clean JSON, ```json fences, embedded JSON in prose.
        """
        # 1. Strip markdown fences
        clean = re.sub(r"```json|```", "", raw).strip()

        # 2. Try direct parse
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass

        # 3. Find first {...} block
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # 4. Give up
        print(f"\033[91m[PARSE ERROR] Could not extract JSON from AI response:\033[0m")
        print(f"\033[90m{raw[:500]}\033[0m")
        return None

    # ── Report saver ──────────────────────────────────────────────────

    def _save_report(self, mission: str) -> str:
        os.makedirs(self.settings.REPORTS_DIR, exist_ok=True)
        path = os.path.join(self.settings.REPORTS_DIR, f"phantom_{self.session_id}.json")

        severity_counts = {s: 0 for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]}
        for f in self.findings:
            sev = f.get("severity", "INFO").upper()
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        report = {
            "session_id":      self.session_id,
            "mission":         mission,
            "timestamp":       datetime.now().isoformat(),
            "model":           self.settings.MODEL_ID,
            "total_findings":  len(self.findings),
            "severity_counts": severity_counts,
            "findings":        self.findings,
        }

        with open(path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n{C.GREEN}[+] Report saved: {path}{C.RESET}")
        return path

    # ── Summary printer ───────────────────────────────────────────────

    def _print_summary(self) -> None:
        w = 60
        print(f"\n{C.PURPLE}╔{'═' * w}╗{C.RESET}")
        print(f"{C.PURPLE}║{'  📊  ENGAGEMENT SUMMARY':^{w}}║{C.RESET}")
        print(f"{C.PURPLE}╠{'═' * w}╣{C.RESET}")

        sev_colors = {
            "CRITICAL": "\033[91m", "HIGH": "\033[38;5;208m",
            "MEDIUM": C.YELLOW,     "LOW": C.CYAN, "INFO": C.DIM
        }
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            count = sum(1 for f in self.findings if f.get("severity") == sev)
            bar   = "█" * count
            col   = sev_colors[sev]
            print(f"{C.PURPLE}║{C.RESET}  {col}{sev:<10}{C.RESET}  {col}{bar:<30}{C.RESET}  {count:>3}  {C.PURPLE}║{C.RESET}")

        print(f"{C.PURPLE}╠{'═' * w}╣{C.RESET}")
        print(f"{C.PURPLE}║{C.RESET}  {'Total Findings':<44} {len(self.findings):>3}  {C.PURPLE}║{C.RESET}")
        print(f"{C.PURPLE}╚{'═' * w}╝{C.RESET}\n")

    # ── Main run loop ─────────────────────────────────────────────────

    def run(self, mission: str) -> None:
        self._start_sandbox()

        messages: list[dict] = [
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": build_mission_prompt(mission)},
        ]

        print(f"\n{C.CYAN}[*] Agent loop starting  (max {self.settings.MAX_ITERATIONS} iterations){C.RESET}\n")

        try:
            for iteration in range(1, self.settings.MAX_ITERATIONS + 1):

                print(f"{C.DIM}{'─' * 60}{C.RESET}")
                print(f"{C.DIM}  Iteration {iteration}/{self.settings.MAX_ITERATIONS}{C.RESET}")
                print(f"{C.DIM}{'─' * 60}{C.RESET}")

                # 1. Ask the AI
                raw_response = self._call_ai(messages)

                # 2. Show raw reasoning (first 300 chars)
                preview = raw_response[:300].replace("\n", " ")
                print(f"{C.PURPLE}[AI] {preview}...{C.RESET}")

                # 3. Parse JSON action
                parsed = self._parse_action(raw_response)

                if not parsed:
                    # Ask AI to retry with valid JSON
                    messages.append({
                        "role": "assistant",
                        "content": raw_response
                    })
                    messages.append({
                        "role": "user",
                        "content": "Your last response was not valid JSON. Reply with ONLY a valid JSON object matching the required schema."
                    })
                    continue

                action   = parsed.get("action", "")
                args     = parsed.get("args", {})
                reasoning = parsed.get("reasoning", "")

                if reasoning:
                    print(f"{C.CYAN}[REASONING] {reasoning[:200]}{C.RESET}")

                # 4. Dispatch to tool
                observation = tools.dispatch(
                    action=action,
                    args=args,
                    sandbox=self.sandbox,
                    settings=self.settings,
                    findings_log=self.findings,
                )

                # 5. Check for mission completion signal
                if observation == "__MISSION_COMPLETE__":
                    print(f"\n{C.GREEN}[+] Mission complete after {iteration} iterations{C.RESET}")
                    break

                # 6. Feed observation back to AI
                messages.append({"role": "assistant", "content": raw_response})
                messages.append({
                    "role": "user",
                    "content": f"OBSERVATION:\n{observation}\n\nContinue the engagement. Output only valid JSON."
                })

                # 7. Prune message history to avoid context overflow
                #    Keep system + mission + last 20 message pairs
                if len(messages) > 44:
                    messages = messages[:2] + messages[-40:]

            else:
                print(f"\n{C.YELLOW}[!] Max iterations reached ({self.settings.MAX_ITERATIONS}){C.RESET}")

        except KeyboardInterrupt:
            print(f"\n{C.YELLOW}[!] Interrupted by user{C.RESET}")

        finally:
            self._stop_sandbox()
            self._print_summary()
            self._save_report(mission)
