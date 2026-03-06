# Unrestricted-Hacking-AI

# 👻 PHANTOM AGENT

> **Autonomous Penetration Testing AI** — Dolphin-DeepSeek R1 × E2B Cloud Sandbox

An autonomous red team agent that thinks, plans, and executes a full pentest engagement inside a live cloud sandbox — no human-in-the-loop required.

```
YOU → Mission Briefing
         ↓
   Dolphin-DeepSeek R1 (reasons + plans)
         ↓
   JSON Action → tools.py dispatcher
         ↓
   E2B Linux Sandbox (executes commands)
         ↓
   Observation back to AI → loop
         ↓
   Findings Report (./reports/)
```

---

## 🗂️ File Map

```
phantom-agent/
│
├── main.py               ← Entry point. Run this.
│
├── agent/
│   ├── __init__.py       ← Package export
│   ├── core.py           ← ReAct loop: AI ↔ sandbox ↔ AI
│   ├── tools.py          ← Tool executor (E2B commands, file I/O, findings)
│   └── prompts.py        ← System prompt + JSON schema + mission template
│
├── config/
│   ├── __init__.py       ← Package export
│   └── settings.py       ← All settings from env vars
│
├── reports/              ← Auto-generated JSON reports per session
│
├── requirements.txt      ← pip dependencies
├── .env.example          ← Copy → .env, fill in keys
├── .replit               ← Replit run config
└── replit.nix            ← Replit nix packages
```

---

## 🚀 Setup (Replit — fastest path)

### 1. Fork / import this repo into Replit

### 2. Add secrets (padlock icon in sidebar)
| Secret | Where to get it |
|--------|----------------|
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys (free) |
| `E2B_API_KEY` | https://e2b.dev/dashboard (free) |

### 3. Install deps (Shell tab)
```bash
pip install -r requirements.txt
```

### 4. Run
```bash
# Interactive mission prompt
python main.py

# Or pass mission directly
python main.py "target: testphp.vulnweb.com — full recon + vuln scan + SQLi test"
```

---

## 🚀 Setup (Local)

```bash
git clone https://github.com/YOU/phantom-agent
cd phantom-agent
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
python main.py
```

---

## 🤖 Model Options

Set `MODEL_ID` in your secrets/`.env`:

| Model | Notes | Cost |
|-------|-------|------|
| `cognitivecomputations/dolphin3.0-r1-mistral-24b:free` | **DEFAULT** — Dolphin+DeepSeek R1 uncensored | Free |
| `deepseek/deepseek-r1:free` | Pure DeepSeek R1, elite reasoning | Free |
| `cognitivecomputations/dolphin-mixtral-8x22b` | Dolphin Mixtral, very capable | Paid |
| `nousresearch/nous-hermes-2-mixtral-8x7b` | Fast, great JSON compliance | Paid |
| `meta-llama/llama-3.3-70b-instruct:free` | Strong free fallback | Free |

---

## 🎯 Example Missions

```
testphp.vulnweb.com — full recon, find and exploit SQLi, document all findings
```

```
TARGET: demo.testfire.net
SCOPE: All endpoints, all ports
GOALS: Auth bypass, XSS, session hijacking, admin panel discovery
```

```
TARGET: hackthebox.eu practice lab IP: 10.10.11.x
Full pentest methodology: recon → enum → exploit → post-exploit → report
```

---

## 📊 Reports

Every session auto-saves to `./reports/phantom_YYYYMMDD_HHMMSS.json`:

```json
{
  "session_id": "20240315_143022",
  "mission": "...",
  "total_findings": 7,
  "severity_counts": { "CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 1, "INFO": 0 },
  "findings": [...]
}
```

---

## ⚠️ Legal

This tool is for authorized security testing only. Only use against targets you own or have explicit written permission to test. The authors are not responsible for misuse.

---

## 🔧 Tuning

| Env Var | Default | Description |
|---------|---------|-------------|
| `MAX_ITERATIONS` | 60 | Max agent loop cycles |
| `TEMPERATURE` | 0.25 | AI creativity (lower = more focused) |
| `CMD_TIMEOUT` | 120 | Seconds before sandbox command times out |
| `SANDBOX_TIMEOUT` | 3600 | Total sandbox lifetime (seconds) |
| `MAX_OUTPUT_CHARS` | 6000 | Truncate large tool output before sending to AI |
