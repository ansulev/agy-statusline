#!/bin/bash
# setup.sh — Automated installer for agy-statusline

set -e

AGY_DIR="$HOME/.gemini/antigravity-cli"
SCRATCH_DIR="$AGY_DIR/scratch"
SETTINGS_FILE="$AGY_DIR/settings.json"

echo "🚀 Installing agy-statusline..."

if [ ! -d "$AGY_DIR" ]; then
  echo "❌ Error: Antigravity CLI directory ($AGY_DIR) not found."
  exit 1
fi

mkdir -p "$SCRATCH_DIR"

# Copy files
cp agy-statusline.py "$SCRATCH_DIR/gemini_stats.py"
echo "✅ Copied stats engine to scratch."

# Create the wrapper script
cat << 'EOF' > "$SCRATCH_DIR/agy-statusline"
#!/bin/bash
python "$HOME/.gemini/antigravity-cli/scratch/gemini_stats.py"
EOF

chmod +x "$SCRATCH_DIR/agy-statusline"
echo "✅ Created and set executable: $SCRATCH_DIR/agy-statusline"

# Backup settings.json
if [ -f "$SETTINGS_FILE" ]; then
  cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
  echo "✅ Backed up settings.json to settings.json.bak"
  
  # Inject statusLine settings using python (no external jq dependency for shell execution)
  python3 -c "
import json
with open('$SETTINGS_FILE', 'r') as f:
    data = json.load(f)
data['statusLine'] = {
    'type': 'command',
    'command': '$SCRATCH_DIR/agy-statusline'
}
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
  echo "✅ Successfully updated settings.json with agy-statusline command!"
else
  echo "⚠️ settings.json not found, creating a new one..."
  cat << EOF > "$SETTINGS_FILE"
{
  "statusLine": {
    "type": "command",
    "command": "$SCRATCH_DIR/agy-statusline"
  }
}
EOF
  echo "✅ Created new settings.json!"
fi

echo -e "\n🎉 Installation complete! Please restart your agy session to load the new statusline."
