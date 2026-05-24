# 🚀 agy-statusline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-brightgreen.svg)]()
[![Built for](https://img.shields.io/badge/Built%20for-Antigravity%20CLI%20(agy)-blue.svg)]()

An ultra-fast, local-first statusline for **Antigravity CLI** (`agy` / Gemini Code agent) designed to monitor your active Gemini session, real-time token spend, today's accumulated costs, and dynamic 5h/7d budget limits directly in your terminal.

*Inspired by [ccusage](https://github.com/ryoppippi/ccusage) and [ccusage-statusline-rs](https://github.com/ticpu/ccusage-statusline-rs) for Claude Code.*

---

## ✨ Features

- **Live Gemini API Pricing**: Automatically calculates exact costs using real Google AI Studio pricing ($0.075/1M input & $0.30/1M output for Flash; $1.25/1M input & $5.00/1M output for Pro).
- **Daily Budget tracking**: Aggregates and displays your accumulated costs today relative to your daily target budget (€30/month for Flash; €50/month for Pro).
- **5h/7d Time Windows**: Aggregates token spend from local `transcript.jsonl` files in the last 5 hours and 7 days.
- **Accurate Context Window**: Estimates context usage percentage against the Gemini 2-million token window.
- **100% Local & Fast**: Zero network API requests, zero dependencies. Parsed in sub-milliseconds purely from your local `agy` logs.
- **Bulletproof Fallbacks**: Handles `model: null` on startup and missing transcript files gracefully without crashing your CLI.

---

## 📸 Display Preview

When loaded, your `agy` bottom status bar will look like this:

```text
🤖Pro │ 💰$0.18 │ 🕔Today: $0.45 (26%) │ 🔥5h: $0.45 │ 🧠36k(1%) │ 📊5h:5% 7d:5% │ ~/.gemini
```

| Widget | Description |
|---|---|
| `🤖Pro` | Active model tier (`Pro` or `Flash`). |
| `💰$0.18` | Total API spend for the **current active session**. |
| `🕔Today` | Total accumulated spend today and % of daily target budget. |
| `🔥5h` | Spend during the last 5 hours across all sessions. |
| `🧠36k(1%)` | Current session active tokens and % of 2M context window. |
| `📊5h/7d` | Token spend over the last 5h and 7d relative to monthly budget limits. |

---

## 🛠️ Quick Installation (1-Click)

Clone this repository and run the automated installer:

```bash
git clone https://github.com/ansulev/agy-statusline.git
cd agy-statusline
chmod +x setup.sh
./setup.sh
```

The installer will copy the files into your `~/.gemini/antigravity-cli/scratch` directory, set the correct permissions, and automatically configure your `settings.json`.

---

## ⚙️ Manual Installation

If you prefer to configure it manually:

1. Copy `agy-statusline.py` to `~/.gemini/antigravity-cli/scratch/gemini_stats.py`.
2. Create an executable bash wrapper at `~/.gemini/antigravity-cli/scratch/agy-statusline`:
   ```bash
   #!/bin/bash
   python "$HOME/.gemini/antigravity-cli/scratch/gemini_stats.py"
   ```
3. Set executable permissions:
   ```bash
   chmod +x ~/.gemini/antigravity-cli/scratch/agy-statusline
   ```
4. Point to the wrapper script in your `~/.gemini/antigravity-cli/settings.json`:
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "~/.gemini/antigravity-cli/scratch/agy-statusline"
     }
   }
   ```

---

## 🤝 Credits & Acknowledgements

- **[ccusage](https://github.com/ryoppippi/ccusage)** by ryoppippi for the original TypeScript Claude Code statusline concept.
- **[ccusage-statusline-rs](https://github.com/ticpu/ccusage-statusline-rs)** by ticpu for the high-performance status bar UI inspiration.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
