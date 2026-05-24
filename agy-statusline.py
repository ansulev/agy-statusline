#!/usr/bin/env python3
"""
agy-statusline.py — Native Gemini usage, cost, and rate limit tracker for Antigravity CLI (agy)
Inspired by ccusage for Claude Code.
"""

import sys
import os
import json
import glob
from datetime import datetime, timezone, timedelta

# Real Gemini AI Studio API Pricing
PRICING = {
    "flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
    "pro": {"input": 1.25 / 1_000_000, "output": 5.00 / 1_000_000}
}

# Configurable Token Capacity Caps (160k cap matches exactly 60% used/40% remaining for 97k tokens)
CAPS = {
    "flash": {
        "5h": 160_000,      # 160k tokens per 5 hours
        "7d": 1_600_000     # 1.6M tokens per 7 days
    },
    "pro": {
        "5h": 160_000,      # 160k tokens per 5 hours
        "7d": 1_600_000     # 1.6M tokens per 7 days
    }
}

def estimate_tokens(text):
    if not text:
        return 0
    # standard 1 token ≈ 3.8 characters for code/text
    return max(1, int(len(text) / 3.8))

def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        input_data = {}

    session_id = input_data.get("session_id", "")
    model_info = input_data.get("model") or {}
    model_id = (model_info.get("id") or "gemini-3.5-flash").lower()
    
    tier = "pro" if "pro" in model_id or "opus" in model_id or "sonnet" in model_id else "flash"
    rates = PRICING[tier]
    
    display_name = model_info.get("display_name") or ("Pro" if tier == "pro" else "Flash")
    if "flash" in display_name.lower():
        display_name = "Flash"
    elif "pro" in display_name.lower():
        display_name = "Pro"

    now = datetime.now(timezone.utc)
    five_hours_ago = now - timedelta(hours=5)
    seven_days_ago = now - timedelta(days=7)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    session_input_tokens = 0
    session_output_tokens = 0
    
    five_hour_tokens = 0
    seven_day_tokens = 0
    
    five_hour_cost = 0.0
    seven_day_cost = 0.0
    today_cost = 0.0

    # Expand ~ safely
    home_dir = os.path.expanduser("~")
    brain_pattern = os.path.join(home_dir, ".gemini/antigravity-cli/brain/*/.system_generated/logs/transcript.jsonl")
    
    for file_path in glob.glob(brain_pattern):
        is_current_session = session_id in file_path
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        step = json.loads(line)
                        created_str = step.get("created_at")
                        if not created_str:
                            continue
                        
                        created_str = created_str.replace("Z", "+00:00")
                        created_time = datetime.fromisoformat(created_str)
                        
                        source = step.get("source", "")
                        step_type = step.get("type", "")
                        
                        input_tok = 0
                        output_tok = 0
                        
                        if source == "USER_EXPLICIT" or step_type == "USER_INPUT":
                            content = step.get("content", "")
                            input_tok = estimate_tokens(content)
                        elif source == "MODEL" or step_type == "PLANNER_RESPONSE":
                            content = step.get("content", "")
                            thinking = step.get("thinking", "")
                            output_tok = estimate_tokens(content) + estimate_tokens(thinking)
                        
                        total_tok = input_tok + output_tok
                        
                        if is_current_session:
                            session_input_tokens += input_tok
                            session_output_tokens += output_tok
                        
                        step_cost = (input_tok * rates["input"]) + (output_tok * rates["output"])
                        
                        if created_time >= five_hours_ago:
                            five_hour_cost += step_cost
                            five_hour_tokens += total_tok
                        if created_time >= seven_days_ago:
                            seven_day_cost += step_cost
                            seven_day_tokens += total_tok
                        if created_time >= today_start:
                            today_cost += step_cost
                    except Exception:
                        continue
        except Exception:
            continue

    session_tokens = session_input_tokens + session_output_tokens
    session_cost = (session_input_tokens * rates["input"]) + (session_output_tokens * rates["output"])
    
    def fmt_tok(t):
        if t >= 1000:
            return f"{t/1000:.0f}k"
        return str(t)

    # Budgets (€30/mo for Flash, €50/mo for Pro)
    monthly_budget = 50.0 if tier == "pro" else 30.0
    today_budget = monthly_budget / 30.0
    
    today_pct = min(999, int((today_cost / today_budget) * 100)) if today_budget > 0 else 0
    
    # Calculate utilization against configurable capacity caps instead of monthly budget fractions
    five_hour_pct = min(100, int((five_hour_tokens / CAPS[tier]["5h"]) * 100))
    seven_day_pct = min(100, int((seven_day_tokens / CAPS[tier]["7d"]) * 100))

    context_limit = 2_000_000
    context_pct = min(100, int((session_tokens / context_limit) * 100))

    print(f"🤖{display_name} │ 💰${session_cost:.2f} │ 🕔Today: ${today_cost:.2f} ({today_pct}%) │ 🔥5h: ${five_hour_cost:.2f} │ 🧠{fmt_tok(session_tokens)}({context_pct}%) │ 📊5h:{five_hour_pct}% 7d:{seven_day_pct}% │ ~/.gemini")

if __name__ == "__main__":
    main()
