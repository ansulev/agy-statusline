#!/bin/bash
# setup-opencode.sh — Automated installer for the bonus opencode-statusline script

set -e

BIN_DIR="$HOME/.bin"
SCRIPT_NAME="opencode-statusline"

echo "🚀 Installing opencode-statusline..."

# 1. Ensure ~/.bin exists
mkdir -p "$BIN_DIR"
echo "✅ Verified directory: $BIN_DIR"

# 2. Copy statusline engine to ~/.bin
cp opencode_statusline.py "$BIN_DIR/$SCRIPT_NAME"
echo "✅ Copied script to $BIN_DIR/$SCRIPT_NAME"

# 3. Set executable permissions
chmod +x "$BIN_DIR/$SCRIPT_NAME"
echo "✅ Set executable permissions."

echo -e "\n🎉 Installation complete!"
echo -e "You can now run '$SCRIPT_NAME' from anywhere in your terminal."
echo -e "\nIntegrations:"
echo -e "  • Tmux: Add '#($SCRIPT_NAME)' to your tmux.conf status-right."
echo -e "  • Waybar: Add a custom script module pointing to '$SCRIPT_NAME --json'."
