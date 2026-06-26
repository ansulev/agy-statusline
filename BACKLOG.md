# BACKLOG

Current status of planned improvements, bug fixes, and feature requests for `agy-statusline`.

## 🚀 Planned Features

*(No planned features left! The backlog is fully clear!)*

## 🐛 Known Limitations

- **Model Mapping Accuracy**: Deducing models on very old sessions where the `<USER_SETTINGS_CHANGE>` log is missing relies on fallback defaults (e.g., assuming Flash).

## ✅ Completed (v0.5.0)

- **Dynamic Pricing Updates**: Load pricing tables, capacity caps, and budgets dynamically from `~/.gemini/antigravity-cli/settings.json` (under `statusLine.pricing`, `statusLine.caps`, and `statusLine.budgets`).
- **Third-Party Model Support**: Added robust heuristics and mapping for non-Google models (e.g., Anthropic Claude, OpenAI GPT) pricing schemes, token limits, and quota formats.

## ✅ Completed (v0.4.0)

- **Subscription Mode UI**: Introduced pure percentage metrics and dynamic timer resets (`⏳XhYYm`), hiding cash values when a Pro subscription is active.
- **Cost Calculation Accuracy**: Dynamically parse transcripts for model changes per step rather than applying the current session's rate globally.
- **Naming Compliance**: Refactored entry points to follow kebab-case scripts (`setup-statusline.sh`) and snake_case python files (`agy_statusline.py`).
- **OpenCode Statusline Utility**: Added `opencode_statusline.py` as a bonus utility tracking OpenCode database stats locally for Waybar/Tmux compatibility.
- **Custom Separators**: Allow configuring display separators (e.g., `│`, `|`, `•`) via `~/.gemini/antigravity-cli/settings.json`.
- **JSON Caching**: Cache historical token calculations incrementally to avoid traversing transcript logs on every CLI command execution.

