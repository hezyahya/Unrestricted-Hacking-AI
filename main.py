#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════╗
║         PHANTOM AGENT - Autonomous Pentest AI         ║
║   Dolphin-DeepSeek R1 + E2B Sandbox  |  v1.0.0       ║
╚═══════════════════════════════════════════════════════╝
"""

import sys
import os
from agent.core import PhantomAgent
from config.settings import Settings

def banner():
    print("""
\033[91m
██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
\033[0m
\033[90m         Autonomous Pentest Agent | Dolphin-DeepSeek R1\033[0m
\033[90m         E2B Cloud Sandbox | Bug Bounty Edition v1.0\033[0m
    """)

def main():
    banner()
    
    settings = Settings()
    
    # Validate required env vars
    missing = settings.validate()
    if missing:
        print(f"\033[91m[ERROR] Missing required env vars: {', '.join(missing)}\033[0m")
        print("\033[93m[INFO]  Copy .env.example to .env and fill in your keys\033[0m")
        sys.exit(1)

    print("\033[92m[+] Environment validated ✓\033[0m")
    print(f"\033[92m[+] Model: {settings.MODEL_ID}\033[0m")
    print(f"\033[92m[+] E2B Sandbox: Ready\033[0m\n")

    # ── Get mission from user ──────────────────────────────────────────
    if len(sys.argv) > 1:
        # Mission passed as CLI arg: python main.py "target.com full recon"
        mission_input = " ".join(sys.argv[1:])
    else:
        # Interactive mode
        print("\033[96m┌─ MISSION BRIEFING ─────────────────────────────────────────┐\033[0m")
        print("\033[96m│ Describe your target + objectives. Be specific.             │\033[0m")
        print("\033[96m│ Example: 'testphp.vulnweb.com - full recon, find SQLi/XSS'  │\033[0m")
        print("\033[96m└─────────────────────────────────────────────────────────────┘\033[0m")
        mission_input = input("\n\033[93mMission > \033[0m").strip()
    
    if not mission_input:
        print("\033[91m[ERROR] No mission provided. Exiting.\033[0m")
        sys.exit(1)

    # ── Launch agent ───────────────────────────────────────────────────
    agent = PhantomAgent(settings=settings)
    agent.run(mission=mission_input)


if __name__ == "__main__":
    main()
