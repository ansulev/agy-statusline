#!/usr/bin/env python3
"""
agy_statusline.py — Native Gemini usage, cost, and rate limit tracker for Antigravity CLI (agy)
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
    if not isinstance(text, str):
        text = str(text)
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
    
    raw_name = model_info.get("display_name") or model_info.get("id") or ""
    display_name = "Flash" if tier == "flash" else "Pro"
    if raw_name:
        import re
        m = re.search(r"gemini\s+([\d.]+)\s+(flash|pro)(?:\s*\(([^)]+)\)|\s+([a-zA-Z]+))?", raw_name, re.IGNORECASE)
        if m:
            version = m.group(1)
            type_name = m.group(2).capitalize()
            effort = m.group(3) or m.group(4)
            if effort:
                display_name = f"{type_name} {version} ({effort.capitalize()})"
            else:
                display_name = f"{type_name} {version}"
        else:
            if "flash" in raw_name.lower():
                display_name = "Flash"
            elif "pro" in raw_name.lower():
                display_name = "Pro"
            else:
                display_name = raw_name

    now = datetime.now(timezone.utc)
    five_hours_ago = now - timedelta(hours=5)
    seven_days_ago = now - timedelta(days=7)
    
    # Calculate local midnight in system timezone (aware)
    now_local = datetime.now()
    today_start_local = datetime(now_local.year, now_local.month, now_local.day).astimezone()

    session_tokens = 0
    session_cost = 0.0
    
    five_hour_tokens = 0
    seven_day_tokens = 0
    today_tokens = 0
    
    five_hour_cost = 0.0
    seven_day_cost = 0.0
    today_cost = 0.0

    # Expand ~ safely
    home_dir = os.path.expanduser("~")
    brain_pattern = os.path.join(home_dir, ".gemini/antigravity-cli/brain/*/.system_generated/logs/transcript.jsonl")
    
    for file_path in glob.glob(brain_pattern):
        is_current_session = bool(session_id) and (session_id in file_path)
        history_tokens = 0
        file_rates = PRICING["flash"]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        step = json.loads(line)
                        
                        content = step.get("content", "")
                        if "<USER_SETTINGS_CHANGE>" in content and "Model Selection" in content:
                            match = re.search(r"Model Selection.*?to\s+([^\n]+)", content)
                            if match:
                                m_name = match.group(1).lower()
                                if "pro" in m_name or "opus" in m_name or "sonnet" in m_name:
                                    file_rates = PRICING["pro"]
                                else:
                                    file_rates = PRICING["flash"]
                                    
                        created_str = step.get("created_at")
                        if not created_str: continue
                        created_str = created_str.replace("Z", "+00:00")
                        created_time = datetime.fromisoformat(created_str)
                        step_type = step.get("type", "")
                        thinking = step.get("thinking", "")
                        
                        step_tok = estimate_tokens(content) + estimate_tokens(thinking)
                        
                        if created_time >= five_hours_ago:
                            five_hour_tokens += step_tok
                        if created_time >= seven_days_ago:
                            seven_day_tokens += step_tok
                        if created_time >= today_start_local:
                            today_tokens += step_tok
                        
                        if step_type == "PLANNER_RESPONSE":
                            input_tok = history_tokens
                            output_tok = step_tok
                            
                            step_cost = (input_tok * file_rates["input"]) + (output_tok * file_rates["output"])
                            
                            if created_time >= five_hours_ago:
                                five_hour_cost += step_cost
                            if created_time >= seven_days_ago:
                                seven_day_cost += step_cost
                            if created_time >= today_start_local:
                                today_cost += step_cost
                                
                            if is_current_session:
                                session_cost += step_cost
                                
                            history_tokens += output_tok
                        else:
                            history_tokens += step_tok
                    except Exception:
                        continue
            if is_current_session:
                session_tokens = history_tokens
        except Exception:
            continue

    def fmt_tok(t):
        if t >= 1000:
            return f"{t/1000:.0f}k"
        return str(t)

    # Budgets (€30/mo for Flash, €50/mo for Pro)
    monthly_budget = 50.0 if tier == "pro" else 30.0
    today_budget = monthly_budget / 30.0
    
    today_budget_pct = min(999, int((today_cost / today_budget) * 100)) if today_budget > 0 else 0
    today_token_pct = min(100, int((today_tokens / (CAPS[tier]["7d"] / 7.0)) * 100))
    
    # Calculate utilization against configurable capacity caps or use native quota
    quota = input_data.get("quota", {})
    gemini_5h = quota.get("gemini-5h", {})
    gemini_weekly = quota.get("gemini-weekly", {})
    
    if gemini_5h:
        five_hour_pct = min(100, int((1.0 - gemini_5h.get("remaining_fraction", 1.0)) * 100))
        reset_in_seconds = gemini_5h.get("reset_in_seconds", 0)
    else:
        five_hour_pct = min(100, int((five_hour_tokens / CAPS[tier]["5h"]) * 100))
        reset_in_seconds = 0
        
    if gemini_weekly:
        seven_day_pct = min(100, int((1.0 - gemini_weekly.get("remaining_fraction", 1.0)) * 100))
    else:
        seven_day_pct = min(100, int((seven_day_tokens / CAPS[tier]["7d"]) * 100))

    # Use native context window stats if available
    cw = input_data.get("context_window", {})
    if cw and "current_usage" in cw:
        u = cw["current_usage"]
        session_tokens = u.get("input_tokens", 0) + u.get("output_tokens", 0)
        context_pct = int(cw.get("used_percentage", 0))
    else:
        context_limit = 2_000_000
        context_pct = min(100, int((session_tokens / context_limit) * 100))

    cwd = input_data.get("cwd") or "~/.gemini"
    if cwd.startswith(home_dir):
        cwd = cwd.replace(home_dir, "~", 1)

    plan_tier = input_data.get("plan_tier", "API")
    is_subs = "API" not in plan_tier and plan_tier != "Free"

    if is_subs:
        timer_str = ""
        if five_hour_pct >= 100 and reset_in_seconds > 0:
            hrs = reset_in_seconds // 3600
            mins = (reset_in_seconds % 3600) // 60
            timer_str = f"⏳{hrs}h{mins:02d}m |  "
            
        print(f"🤖{display_name} │ {timer_str}🕔Today: {today_token_pct}% | 🔥5h: {five_hour_pct}% |  🧠{fmt_tok(session_tokens)}({context_pct}%) │ 📊5h:{five_hour_pct}% 7d:{seven_day_pct}% │ {cwd}")
    else:
        print(f"🤖{display_name} │ 💰${session_cost:.2f} │ 🕔Today: ${today_cost:.2f} ({today_budget_pct}%) │ 🔥5h: ${five_hour_cost:.2f} │ 🧠{fmt_tok(session_tokens)}({context_pct}%) │ 📊5h:{five_hour_pct}% 7d:{seven_day_pct}% │ {cwd}")

if __name__ == "__main__":
    main()
