# ============================================================
# notification_config.py
# Safe SMTP/Gmail configuration loader.
# Reads credentials from environment variables (never hard-coded).
# ============================================================

import os

# Try loading .env if python-dotenv is installed; if not, don't crash
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass   # .env is optional; env vars may be set system-wide instead


# ------------------------------------------------------------
# Read env safely
# ------------------------------------------------------------
def _env(key, default=""):
    val = os.environ.get(key, default)
    return val.strip() if isinstance(val, str) else default


# ------------------------------------------------------------
# Main config accessors
# ------------------------------------------------------------
def get_smtp_host():
    return _env("LMS_SMTP_HOST", "smtp.gmail.com")


def get_smtp_port():
    try:
        return int(_env("LMS_SMTP_PORT", "587"))
    except ValueError:
        return 587


def get_smtp_user():
    return _env("LMS_SMTP_USER")


def get_smtp_pass():
    # Gmail app passwords are 16 chars; users often paste with spaces
    return _env("LMS_SMTP_PASS").replace(" ", "")


def get_library_name():
    return _env("LMS_LIBRARY_NAME", "Library Management System")


# ------------------------------------------------------------
# Check whether email is fully configured
# ------------------------------------------------------------
def is_email_configured():
    return bool(get_smtp_user()) and bool(get_smtp_pass())


# ------------------------------------------------------------
# Diagnostic info (safe to display — never shows the password)
# ------------------------------------------------------------
def describe_config():
    return {
        "host": get_smtp_host(),
        "port": get_smtp_port(),
        "user": get_smtp_user() or "(not set)",
        "password_set": "yes" if get_smtp_pass() else "no",
        "configured": is_email_configured(),
    }


if __name__ == "__main__":
    print("SMTP configuration:")
    for k, v in describe_config().items():
        print(f"  {k:15}: {v}")
    if is_email_configured():
        print("\nEmail is READY to send.")
    else:
        print("\nEmail is NOT configured. Create a .env file with LMS_SMTP_USER and LMS_SMTP_PASS.")