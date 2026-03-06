"""
config/settings.py
──────────────────
All configuration loaded from environment variables.
On Replit: set these in the Secrets tab (padlock icon).
Locally:   copy .env.example → .env and fill in values.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    # ── AI Model (OpenRouter) ──────────────────────────────────────────
    # dolphin-deepseek = the uncensored R1 mixture you mentioned
    # Swap MODEL_ID in your .env to try others (see README for options)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    MODEL_ID: str = os.getenv(
        "MODEL_ID",
        "cognitivecomputations/dolphin3.0-r1-mistral-24b:free"   # default: free dolphin-deepseek
    )

    # ── E2B Sandbox ────────────────────────────────────────────────────
    E2B_API_KEY: str = os.getenv("E2B_API_KEY", "")

    # How long the sandbox lives (seconds). 3600 = 1 hr
    SANDBOX_TIMEOUT: int = int(os.getenv("SANDBOX_TIMEOUT", "3600"))

    # Default command timeout inside sandbox (seconds)
    CMD_TIMEOUT: int = int(os.getenv("CMD_TIMEOUT", "120"))

    # ── Agent Behavior ─────────────────────────────────────────────────
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "60"))

    # Truncate sandbox output sent back to AI (chars)
    MAX_OUTPUT_CHARS: int = int(os.getenv("MAX_OUTPUT_CHARS", "6000"))

    # AI temperature: lower = more focused/deterministic
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.25"))

    # Max tokens the AI generates per turn
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))

    # ── Reports ────────────────────────────────────────────────────────
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", "./reports")

    def validate(self) -> list[str]:
        """Return list of missing required env vars."""
        missing = []
        if not self.OPENROUTER_API_KEY:
            missing.append("OPENROUTER_API_KEY")
        if not self.E2B_API_KEY:
            missing.append("E2B_API_KEY")
        return missing
