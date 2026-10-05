#!/usr/bin/env python3
"""Run in Azure Cloud Shell to configure Gmail without editing secret placeholders.

Uses only Python standard library and the authenticated Azure CLI. Does not start
or deploy the app. Never upgrades the subscription or overwrites an existing .env.
"""
import argparse
import getpass
import ipaddress
import json
import re
import secrets
import shutil
import subprocess
import sys

REMOTE_SCRIPT = r"""python3 - <<'PY'
import os, re, secrets, smtplib, ssl
from pathlib import Path

path = Path("/opt/speakforge/.env")
if path.exists():
    raise SystemExit("CONFIG_EXISTS: existing configuration was not changed.")
mail = os.environ.get("SF_MAIL", "").strip()
password = "".join(os.environ.get("SF_APP_PASSWORD", "").split())
if not re.fullmatch(r"[A-Za-z0-9._%+-]+@(gmail|googlemail)\.com", mail, re.I):
    raise SystemExit("Enter a valid personal Gmail address first.")
if not re.fullmatch(r"[A-Za-z0-9]{16}", password):
    raise SystemExit("Enter the 16-character Google App Password first.")
try:
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(mail, password)
except Exception as exc:
    raise SystemExit("SMTP_CHECK_FAILED: " + type(exc).__name__) from None
host = os.environ["SF_IP"].replace(".", "-") + ".sslip.io"
front = "https://speakforge." + host
back = "https://api.speakforge." + host
cfg = {key: secrets.token_hex(32) for key in (
    "MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "SECRET_KEY", "ADMIN_SECRET_KEY")}
cfg.update(ENVIRONMENT="production", ACME_EMAIL=mail, FRONTEND_URL=front,
    BACKEND_URL=back, VITE_API_URL=back, ALLOWED_ORIGINS=front,
    UPLOAD_DIR="/data/uploads", MAIL_SERVER="smtp.gmail.com", MAIL_PORT="587",
    MAIL_USERNAME=mail, MAIL_FROM=mail, MAIL_PASSWORD=password,
    MAIL_STARTTLS="True", MAIL_SSL_TLS="False", USE_CREDENTIALS="True")
cfg["DATABASE_URL"] = "mysql+pymysql://speakforge:" + cfg["MYSQL_PASSWORD"] + "@db:3306/speakforge"
with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as f:
    f.write("".join(key + "=" + value + "\n" for key, value in cfg.items()))
print("SMTP_AUTH_OK; CONFIG_SAVED")
PY
"""


def azure(args, sensitive=()):
    result = subprocess.run(["az", *args, "--only-show-errors"],
                            capture_output=True, text=True)
    if result.returncode:
        message = result.stderr or "Azure CLI command failed."
        for value in sensitive:
            if value:
                message = message.replace(value, "[redacted]")
        raise RuntimeError(message.strip())
    return result.stdout


def capture_credentials():
    while True:
        mail = input("Gmail address: ").strip()
        if re.fullmatch(r"[A-Za-z0-9._%+-]+@(gmail|googlemail)\.com", mail, re.I):
            break
        print("Enter a personal Gmail address.")
    while True:
        password = "".join(getpass.getpass("Google App Password (hidden): ").split())
        if re.fullmatch(r"[A-Za-z0-9]{16}", password):
            return mail, password
        print("Received", len(password), "non-space characters; expected 16 letters/numbers. Try again.")


def configure(group, vm):
    details = json.loads(azure(["vm", "show", "-g", group, "-n", vm,
        "--show-details", "--query", "{location:location,ip:publicIps}", "-o", "json"]))
    address = str(ipaddress.IPv4Address(details["ip"]))
    mail, password = capture_credentials()
    name = "speakforge-config-" + secrets.token_hex(6)
    print("Checking Gmail and saving configuration on the VM. Please wait...")
    azure(["vm", "run-command", "create", "-g", group, "--vm-name", vm,
        "--name", name, "--location", details["location"],
        "--async-execution", "false", "--timeout-in-seconds", "300",
        "--script", REMOTE_SCRIPT, "--parameters", "SF_IP=" + address,
        "--protected-parameters", "SF_MAIL=" + mail, "SF_APP_PASSWORD=" + password,
        "--output", "none"], sensitive=(password, mail))
    raw = azure(["vm", "run-command", "show", "-g", group, "--vm-name", vm,
        "--name", name, "--expand", "instanceView", "--query", "instanceView", "-o", "json"],
        sensitive=(password, mail))
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise RuntimeError("Azure did not return execution status. Run command name: " + name)
    if (result.get("executionState") != "Succeeded" or result.get("exitCode") != 0
            or "SMTP_AUTH_OK; CONFIG_SAVED" not in result.get("output", "")):
        error = result.get("error") or result.get("executionMessage") or "Configuration not confirmed."
        for value in (password, mail):
            error = error.replace(value, "[redacted]")
        raise RuntimeError(error + "\nRun command name: " + name)
    print("SMTP_AUTH_OK; CONFIG_SAVED")
    print("The app is not started yet. Return this success message to continue.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-group", default="speakforge-rg")
    parser.add_argument("--vm", default="speakforge-vm")
    args = parser.parse_args()
    if not sys.stdin.isatty():
        parser.exit(1, "Run this downloaded file directly in Cloud Shell, not through a pipe.\n")
    if not shutil.which("az"):
        parser.exit(1, "Azure CLI is required. Run this in your Azure Cloud Shell.\n")
    try:
        configure(args.resource_group, args.vm)
    except (RuntimeError, ValueError, KeyError, EOFError) as exc:
        print("SETUP_FAILED:", str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
