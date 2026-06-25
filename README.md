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
chmod +x setup-statusline.sh
./setup-statusline.sh
```

The installer will copy the files into your `~/.gemini/antigravity-cli/scratch` directory, set the correct permissions, and automatically configure your `settings.json` with the resolved path of your home directory.

---

## ⚙️ Manual Installation

If you prefer to configure it manually:

1. Copy `agy_statusline.py` to `~/.gemini/antigravity-cli/scratch/gemini_stats.py`.
2. Create an executable bash wrapper at `~/.gemini/antigravity-cli/scratch/agy-statusline`:
   ```bash
   #!/bin/bash
   python3 "$HOME/.gemini/antigravity-cli/scratch/gemini_stats.py"
   ```
3. Set executable permissions:
   ```bash
   chmod +x ~/.gemini/antigravity-cli/scratch/agy-statusline
   ```
4. Point to the wrapper script in your `~/.gemini/antigravity-cli/settings.json` using the tilde (`~`) shell expansion prefix:
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "~/.gemini/antigravity-cli/scratch/agy-statusline"
     }
   }
   ```

## 🎁 Bonus: OpenCode Statusline (`opencode_statusline.py`)

As a bonus for users of this suite, we have included `opencode_statusline.py` to monitor the **OpenCode** CLI coding agent. 

Unlike Gemini, OpenCode stores session schemas and real-time costs inside a local SQLite database (`~/.local/share/opencode/opencode.db`). This script queries the database directly to extract cost, tokens, and active state without touching files or APIs.

It outputs to both plain text (for `tmux`, `Polybar`, `tint2`, `xfce4-panel`) and JSON format (for `Waybar` custom modules).

### Installation & Usage
Run the automated installer to copy it to your `~/.bin/` directory as `opencode-statusline` and set executable permissions:
```bash
chmod +x setup-opencode.sh
./setup-opencode.sh
```

Once installed, you can query it globally:
```bash
opencode-statusline
# Or output Waybar-compliant JSON:
opencode-statusline --json
```

### Panel Integrations

Since OpenCode does not natively support custom statusline injection inside its own TUI yet, you can attach this script to your system panels to monitor it globally:

#### 1. Waybar
Add this custom module to your `~/.config/waybar/config` (or `config.jsonc`):
```json
"custom/opencode": {
    "format": "{}",
    "return-type": "json",
    "exec": "opencode-statusline --json",
    "interval": 5,
    "tooltip": true
}
```
Then add `"custom/opencode"` to your active modules list.

#### 2. Tmux
Add this to your `~/.tmux.conf`:
```tmux
set -g status-right "#(opencode-statusline) │ %H:%M "
```
Then reload: `tmux source-file ~/.tmux.conf`

#### 3. Polybar
Add this module to your Polybar configuration:
```ini
[module/opencode]
type = custom/script
exec = opencode-statusline
interval = 5
format = <label>
```

#### 4. xfce4-panel (Generic Monitor / genmon)
Add a **Generic Monitor** (`genmon`) item to your panel, set the command to `opencode-statusline`, and set the period to `5` seconds.

---

## 🤝 Credits & Acknowledgements

- **[ccusage](https://github.com/ryoppippi/ccusage)** by ryoppippi for the original TypeScript Claude Code statusline concept.
- **[ccusage-statusline-rs](https://github.com/ticpu/ccusage-statusline-rs)** by ticpu for the high-performance status bar UI inspiration.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
