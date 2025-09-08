
# duckbot/settings_menu.py
import os, sys
from duckbot.settings_gpt import load_settings, save_settings, DEFAULTS, apply_to_env

def _ask(prompt, current, validator=None):
    raw = input(f"{prompt} [{current}]: ").strip()
    if raw == "": return current
    if validator:
        try:
            if not validator(raw): raise ValueError("invalid")
        except Exception:
            print("  -> Invalid value, keeping current.")
            return current
    return raw

def is_float(x):
    try:
        float(x); return True
    except Exception:
        return False

def is_int(x):
    try:
        int(x); return True
    except Exception:
        return False

def main():
    print("=== DuckBot AI Manager Settings ===")
    s = load_settings()
    print("Values saved to duckbot/ai_manager_settings.json and applied at startup.")
    print("Press Enter to keep current value.\n")

    s["AI_LOCAL_STRICT"]        = _ask("Prefer local only when possible? (1/0)", s["AI_LOCAL_STRICT"], lambda v: v in ("0","1"))
    s["AI_LOCAL_MAX_ATTEMPTS"]  = _ask("Local attempts before cloud", s["AI_LOCAL_MAX_ATTEMPTS"], is_int)
    s["AI_LOCAL_CONF_MIN"]      = _ask("Min local confidence (0-1)", s["AI_LOCAL_CONF_MIN"], is_float)
    s["OPENROUTER_BUDGET_PER_MIN"] = _ask("Max cloud calls per minute", s["OPENROUTER_BUDGET_PER_MIN"], is_int)
    s["AI_TTL_CACHE_SEC"]       = _ask("Cache TTL seconds", s["AI_TTL_CACHE_SEC"], is_int)
    s["AI_MAX_HOPS_ROUTINE"]    = _ask("Max hops (routine tasks)", s["AI_MAX_HOPS_ROUTINE"], is_int)
    s["AI_MAX_HOPS_CRITICAL"]   = _ask("Max hops (critical tasks)", s["AI_MAX_HOPS_CRITICAL"], is_int)
    s["AI_CONFIDENCE_MIN"]      = _ask("Global confidence threshold", s["AI_CONFIDENCE_MIN"], is_float)

    save_settings(s)
    apply_to_env(s)
    print("\nSaved. New values will be picked up automatically on next start (sitecustomize.py).")
    print("You can also export these vars in the shell to override temporarily.")

if __name__ == "__main__":
    main()
