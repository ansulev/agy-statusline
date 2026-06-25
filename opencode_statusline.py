#!/usr/bin/env python3
"""
opencode-statusline — Slim KISS usage, cost, and session status tracker for OpenCode CLI agent.
Queries the local SQLite database directly for instant, dependency-free metrics.
"""

import os
import sqlite3
import json
import time
from datetime import datetime

def format_tokens(t):
    if t >= 1_000_000:
        return f"{t/1_000_000:.1f}M"
    if t >= 1000:
        return f"{t/1000:.0f}k"
    return str(t)

def main():
    import sys
    
    show_json = False
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ("-h", "--help"):
            print("Usage: opencode-statusline [options]")
            print("")
            print("Options:")
            print("  -h, --help    Show this help message")
            print("  -j, --json    Output in JSON format (tailored for Waybar)")
            return
        elif arg in ("-j", "--json"):
            show_json = True

    db_path = os.path.expanduser("~/.local/share/opencode/opencode.db")
    if not os.path.exists(db_path):
        if show_json:
            print(json.dumps({"text": "🤖OpenCode │ 🛑No DB", "tooltip": "Database not found"}))
        else:
            print("🤖OpenCode │ 🛑No DB")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Get most recent session info
        cursor.execute("""
            SELECT model, cost, tokens_input, tokens_output, time_updated 
            FROM session 
            ORDER BY time_updated DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        if not row:
            if show_json:
                print(json.dumps({"text": "🤖OpenCode │ 🛑No Sessions", "tooltip": "No session history"}))
            else:
                print("🤖OpenCode │ 🛑No Sessions")
            return
            
        model_json, sess_cost, sess_in, sess_out, last_updated = row
        sess_tokens = sess_in + sess_out
        
        try:
            model_data = json.loads(model_json)
            model_id = model_data.get("id", "unknown")
        except Exception:
            model_id = "unknown"
            
        # Clean up model name display (e.g. openrouter/qwen/qwen-coder -> Qwen-coder)
        model_display = model_id.split("/")[-1].replace("-free", "").capitalize()
        if not model_display:
            model_display = "Active"
            
        # 2. Get aggregates starting from local midnight today
        local_now = datetime.now()
        local_today_start = datetime(local_now.year, local_now.month, local_now.day)
        today_start_ms = int(local_today_start.timestamp() * 1000)
        
        cursor.execute("""
            SELECT SUM(cost), SUM(tokens_input + tokens_output)
            FROM session
            WHERE time_updated >= ?
        """, (today_start_ms,))
        today_cost, today_tokens = cursor.fetchone()
        today_cost = today_cost or 0.0
        today_tokens = today_tokens or 0
        
        # 3. Determine if the session was active in the last 10 minutes
        now_ms = int(time.time() * 1000)
        is_active = (now_ms - last_updated) < (10 * 60 * 1000)
        status_icon = "🟢" if is_active else "💤"
        
        if show_json:
            text = f"🤖{model_display} {status_icon} │ 💰${sess_cost:.2f} │ 🕔Today: ${today_cost:.2f} │ 🧠{format_tokens(sess_tokens)}"
            tooltip = f"Session: {format_tokens(sess_tokens)} tokens\nToday: {format_tokens(today_tokens)} tokens"
            print(json.dumps({
                "text": text,
                "tooltip": tooltip,
                "class": "active" if is_active else "idle"
            }))
        else:
            print(f"🤖{model_display} {status_icon} │ 💰${sess_cost:.2f} │ 🕔Today: ${today_cost:.2f} │ 🧠{format_tokens(sess_tokens)} (Today: {format_tokens(today_tokens)})")
        
    except Exception as e:
        if len(sys.argv) > 1 and sys.argv[1] in ("-j", "--json"):
            print(json.dumps({"text": "🤖OpenCode │ ⚠️Error", "tooltip": str(e)}))
        else:
            print(f"🤖OpenCode │ ⚠️Error: {str(e)}")
        
if __name__ == "__main__":
    main()
