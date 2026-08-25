#!/usr/bin/env python3
"""
agy_statusline.py — Native Gemini usage, cost, and rate limit tracker for Antigravity CLI (agy)
Inspired by ccusage for Claude Code.
"""

import sys
import os
import json
import glob
import re
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

def get_rates_for_model(model_name, pricing_table):
    model_name = model_name.lower()
    for key, rates in pricing_table.items():
        if key in model_name:
            return rates
    if any(x in model_name for x in ["pro", "opus", "sonnet", "4o", "gpt-4"]):
        return pricing_table.get("pro", pricing_table.get("flash"))
    return pricing_table.get("flash")

def get_caps_for_model(model_name, caps_table):
    model_name = model_name.lower()
    for key, caps in caps_table.items():
        if key in model_name:
            return caps
    if any(x in model_name for x in ["pro", "opus", "sonnet", "4o", "gpt-4"]):
        return caps_table.get("pro", caps_table.get("flash"))
    return caps_table.get("flash")

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
    except Exception as e:
        print(f"Statusline Error parsing stdin: {e}", file=sys.stderr)
        input_data = {}

    session_id = input_data.get("session_id", "")
    
    # Load custom separators and pricing/caps/budgets from settings.json
    outer_sep = " │ "
    inner_sep = " | "
    home_dir = os.path.expanduser("~")
    settings_path = os.path.join(home_dir, ".gemini/antigravity-cli/settings.json")
    
    budgets = {
        "flash": 30.0,
        "pro": 50.0
    }
    
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)
                if not isinstance(settings, dict):
                    settings = {}
                
                status_line = settings.get("statusLine")
                if not isinstance(status_line, dict):
                    status_line = {}
                
                # Separators
                custom_seps = status_line.get("separators")
                if isinstance(custom_seps, dict):
                    if "outer" in custom_seps:
                        outer_sep = custom_seps["outer"]
                    if "inner" in custom_seps:
                        inner_sep = custom_seps["inner"]
                        
                # Custom pricing overrides
                custom_pricing = status_line.get("pricing")
                if isinstance(custom_pricing, dict):
                    for t, rates_dict in custom_pricing.items():
                        if isinstance(rates_dict, dict):
                            if t not in PRICING:
                                PRICING[t] = {}
                            for key in ["input", "output"]:
                                if key in rates_dict:
                                    val = float(rates_dict[key])
                                    # If rate is > 1e-5, assume it is per 1M tokens and convert to per-token
                                    if val > 1e-5:
                                        val = val / 1_000_000
                                    PRICING[t][key] = val
                                    
                # Custom caps overrides
                custom_caps = status_line.get("caps")
                if isinstance(custom_caps, dict):
                    for t, caps_dict in custom_caps.items():
                        if isinstance(caps_dict, dict):
                            if t not in CAPS:
                                CAPS[t] = {}
                            for key in ["5h", "7d"]:
                                if key in caps_dict:
                                    CAPS[t][key] = int(caps_dict[key])
                                    
                # Custom budgets overrides
                custom_budgets = status_line.get("budgets")
                if isinstance(custom_budgets, dict):
                    for t, b in custom_budgets.items():
                        try:
                            budgets[t] = float(b)
                        except (ValueError, TypeError):
                            pass
        except Exception:
            pass

    model_info = input_data.get("model")
    if not isinstance(model_info, dict):
        model_info = {}
    model_id = (model_info.get("id") or "gemini-3.5-flash").lower()
    
    # Resolve active tier
    tier = "flash"
    matched_tier = None
    for p_tier in PRICING:
        if p_tier in model_id:
            matched_tier = p_tier
            break
    if matched_tier:
        tier = matched_tier
    else:
        if any(x in model_id for x in ["pro", "opus", "sonnet", "4o", "gpt-4"]):
            tier = "pro"
        else:
            tier = "flash"
    
    raw_name = model_info.get("display_name") or model_info.get("id") or ""
    display_name = "Flash" if tier == "flash" else "Pro"
    if raw_name:
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
    brain_dir = os.path.join(home_dir, ".gemini/antigravity-cli/brain")
    state_dir = os.path.join(home_dir, ".gemini/antigravity-cli/state")
    os.makedirs(state_dir, exist_ok=True)
    db_path = os.path.join(state_dir, "usage.db")
    
    import sqlite3
    try:
        conn = sqlite3.connect(db_path, timeout=2.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        
        # Schema setup
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                file_path TEXT PRIMARY KEY,
                mtime REAL,
                session_tokens INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS steps (
                file_path TEXT,
                t REAL,
                k INTEGER,
                c REAL,
                is_resp INTEGER
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_steps_t ON steps(t)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_steps_file_path ON steps(file_path)")
        
        # Get cached mtimes
        c = conn.cursor()
        c.execute("SELECT file_path, mtime, session_tokens FROM files")
        cache = {row[0]: {"mtime": row[1], "session_tokens": row[2]} for row in c.fetchall()}
        
        # Scan for files efficiently using os.scandir
        active_files = set()
        if os.path.exists(brain_dir):
            for entry in os.scandir(brain_dir):
                if entry.is_dir():
                    file_path = os.path.join(entry.path, ".system_generated/logs/transcript.jsonl")
                    try:
                        mtime = os.path.getmtime(file_path)
                    except Exception:
                        continue
                    
                    active_files.add(file_path)
                    
                    is_current_session = bool(session_id) and (session_id in file_path)
                    cached_entry = cache.get(file_path)
                    
                    if cached_entry and cached_entry["mtime"] == mtime:
                        if is_current_session:
                            session_tokens = cached_entry["session_tokens"]
                        continue
                    
                    # File changed or new, parse it
                    steps = []
                    history_tokens = 0
                    file_rates = get_rates_for_model("flash", PRICING)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            for line in f:
                                try:
                                    step = json.loads(line)
                                    if not isinstance(step, dict):
                                        continue
                                    content = step.get("content", "")
                                    if "<USER_SETTINGS_CHANGE>" in content and "Model Selection" in content:
                                        match = re.search(r"Model Selection.*?to\s+([^\n]+)", content)
                                        if match:
                                            m_name = match.group(1).lower()
                                            file_rates = get_rates_for_model(m_name, PRICING)
                                                
                                    created_str = step.get("created_at")
                                    if not created_str:
                                        continue
                                    created_str = created_str.replace("Z", "+00:00")
                                    created_time = datetime.fromisoformat(created_str)
                                    step_type = step.get("type", "")
                                    thinking = step.get("thinking", "")
                                    
                                    step_tok = estimate_tokens(content) + estimate_tokens(thinking)
                                    
                                    step_cost = 0.0
                                    if step_type == "PLANNER_RESPONSE":
                                        input_tok = history_tokens
                                        output_tok = step_tok
                                        step_cost = (input_tok * file_rates["input"]) + (output_tok * file_rates["output"])
                                        history_tokens += output_tok
                                    else:
                                        history_tokens += step_tok
                                        
                                    # Only save steps from the last 7 days to keep DB small
                                    if created_time >= seven_days_ago:
                                        steps.append((file_path, created_time.timestamp(), step_tok, step_cost, 1 if step_type == "PLANNER_RESPONSE" else 0))
                                except Exception:
                                    continue
                    except Exception:
                        continue
                    
                    # Update DB
                    conn.execute("DELETE FROM steps WHERE file_path = ?", (file_path,))
                    if steps:
                        conn.executemany("INSERT INTO steps (file_path, t, k, c, is_resp) VALUES (?, ?, ?, ?, ?)", steps)
                    conn.execute("INSERT OR REPLACE INTO files (file_path, mtime, session_tokens) VALUES (?, ?, ?)", (file_path, mtime, history_tokens))
                    
                    if is_current_session:
                        session_tokens = history_tokens

        # Cleanup deleted files
        deleted_files = set(cache.keys()) - active_files
        for df in deleted_files:
            conn.execute("DELETE FROM steps WHERE file_path = ?", (df,))
            conn.execute("DELETE FROM files WHERE file_path = ?", (df,))
            
        # Optional: cleanup old steps globally
        conn.execute("DELETE FROM steps WHERE t < ?", (seven_days_ago.timestamp(),))
        
        conn.commit()

        # Query metrics directly from SQLite
        c.execute("""
            SELECT 
                SUM(CASE WHEN t >= ? THEN k ELSE 0 END) as five_hour_tokens,
                SUM(CASE WHEN t >= ? AND is_resp = 1 THEN c ELSE 0 END) as five_hour_cost,
                SUM(CASE WHEN t >= ? THEN k ELSE 0 END) as seven_day_tokens,
                SUM(CASE WHEN t >= ? AND is_resp = 1 THEN c ELSE 0 END) as seven_day_cost,
                SUM(CASE WHEN t >= ? THEN k ELSE 0 END) as today_tokens,
                SUM(CASE WHEN t >= ? AND is_resp = 1 THEN c ELSE 0 END) as today_cost
            FROM steps
        """, (
            five_hours_ago.timestamp(), five_hours_ago.timestamp(),
            seven_days_ago.timestamp(), seven_days_ago.timestamp(),
            today_start_local.timestamp(), today_start_local.timestamp()
        ))
        row = c.fetchone()
        if row:
            five_hour_tokens = row[0] or 0
            five_hour_cost = row[1] or 0.0
            seven_day_tokens = row[2] or 0
            seven_day_cost = row[3] or 0.0
            today_tokens = row[4] or 0
            today_cost = row[5] or 0.0
            
        # Get current session cost from DB
        if session_id:
            c.execute("SELECT SUM(c) FROM steps WHERE file_path LIKE ? AND is_resp = 1", (f"%{session_id}%",))
            res = c.fetchone()
            session_cost = res[0] or 0.0

    except Exception as e:
        print(f"Statusline Error: {e}", file=sys.stderr)
        # Fallback to zero values
        pass
    finally:
        if 'conn' in locals():
            conn.close()

    def fmt_tok(t):
        if t >= 1000:
            return f"{t/1000:.0f}k"
        return str(t)

    # Budgets (€30/mo for Flash, €50/mo for Pro, or customized)
    monthly_budget = budgets.get(tier, 30.0)
    today_budget = monthly_budget / 30.0
    
    active_caps = get_caps_for_model(model_id, CAPS)
    
    today_budget_pct = min(999, int((today_cost / today_budget) * 100)) if today_budget > 0 else 0
    today_token_pct = min(100, int((today_tokens / (active_caps["7d"] / 7.0)) * 100))
    
    # Calculate utilization against configurable capacity caps or use native quota
    quota = input_data.get("quota")
    if not isinstance(quota, dict):
        quota = {}
    gemini_5h = quota.get("gemini-5h")
    if not isinstance(gemini_5h, dict):
        gemini_5h = {}
    gemini_weekly = quota.get("gemini-weekly")
    if not isinstance(gemini_weekly, dict):
        gemini_weekly = {}
    
    if gemini_5h:
        five_hour_pct = min(100, int((1.0 - gemini_5h.get("remaining_fraction", 1.0)) * 100))
        reset_in_seconds = gemini_5h.get("reset_in_seconds", 0)
    else:
        five_hour_pct = min(100, int((five_hour_tokens / active_caps["5h"]) * 100))
        reset_in_seconds = 0
        
    if gemini_weekly:
        seven_day_pct = min(100, int((1.0 - gemini_weekly.get("remaining_fraction", 1.0)) * 100))
    else:
        seven_day_pct = min(100, int((seven_day_tokens / active_caps["7d"]) * 100))

    # Use native context window stats if available
    cw = input_data.get("context_window")
    if not isinstance(cw, dict):
        cw = {}
    u = cw.get("current_usage")
    if isinstance(u, dict):
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
            timer_str = f"⏳{hrs}h{mins:02d}m{inner_sep} "
            
        print(f"🤖{display_name}{outer_sep}{timer_str}🕔Today: {today_token_pct}%{inner_sep}🔥5h: {five_hour_pct}%{inner_sep} 🧠{fmt_tok(session_tokens)}({context_pct}%){outer_sep}📊5h:{five_hour_pct}% 7d:{seven_day_pct}%{outer_sep}{cwd}")
    else:
        print(f"🤖{display_name}{outer_sep}💰${session_cost:.2f}{outer_sep}🕔Today: ${today_cost:.2f} ({today_budget_pct}%){outer_sep}🔥5h: ${five_hour_cost:.2f}{outer_sep}🧠{fmt_tok(session_tokens)}({context_pct}%){outer_sep}📊5h:{five_hour_pct}% 7d:{seven_day_pct}%{outer_sep}{cwd}")

if __name__ == "__main__":
    main()
