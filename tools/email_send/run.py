#!/usr/bin/env python3
"""Email sender — Resend API (preferred) or SMTP fallback.

Provider selection (auto-detect from env):
  1. RESEND_API_KEY set → Resend API (also needs RESEND_FROM_EMAIL)
  2. SMTP_HOST set     → SMTP (needs SMTP_USER, SMTP_PASSWORD, SMTP_FROM)

All parameters arrive via TOOL_PARAMS env var as JSON (injected by garudust).
"""

import json
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    import httpx
except ImportError:
    print("error: httpx not installed — run: pip install httpx", file=sys.stderr)
    sys.exit(1)


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    try:
        p = json.loads(os.environ.get("TOOL_PARAMS", "{}"))
    except json.JSONDecodeError:
        die("invalid TOOL_PARAMS JSON")

    to: str = p.get("to", "").strip()
    subject: str = p.get("subject", "").strip()
    body: str = p.get("body", "").strip()
    html: bool = bool(p.get("html", False))
    from_name: str = p.get("from_name", "").strip()
    cc: str = p.get("cc", "").strip()

    if not to:
        die("'to' is required")
    if not subject:
        die("'subject' is required")
    if not body:
        die("'body' is required")

    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    smtp_host = os.environ.get("SMTP_HOST", "").strip()

    if resend_key:
        send_resend(to, subject, body, html, from_name, cc, resend_key)
    elif smtp_host:
        send_smtp(to, subject, body, html, from_name, cc, smtp_host)
    else:
        die(
            "no email provider configured — set RESEND_API_KEY (Resend) "
            "or SMTP_HOST (SMTP) in ~/.garudust/.env"
        )


def send_resend(
    to: str,
    subject: str,
    body: str,
    html: bool,
    from_name: str,
    cc: str,
    api_key: str,
) -> None:
    from_email = os.environ.get("RESEND_FROM_EMAIL", "").strip()
    if not from_email:
        die("RESEND_FROM_EMAIL is required when using Resend")

    from_field = f"{from_name} <{from_email}>" if from_name else from_email
    to_list = [e.strip() for e in to.split(",") if e.strip()]

    payload: dict = {
        "from": from_field,
        "to": to_list,
        "subject": subject,
        "html" if html else "text": body,
    }
    if cc:
        payload["cc"] = [e.strip() for e in cc.split(",") if e.strip()]

    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        die(f"Resend API error {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        die(f"Resend request failed: {e}")

    data = resp.json()
    print(f"sent via Resend — id: {data.get('id', 'unknown')}")


def send_smtp(
    to: str,
    subject: str,
    body: str,
    html: bool,
    from_name: str,
    cc: str,
    smtp_host: str,
) -> None:
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASSWORD", "").strip()
    from_email = os.environ.get("SMTP_FROM", smtp_user).strip()

    if not smtp_user:
        die("SMTP_USER is required")
    if not from_email:
        die("SMTP_FROM (or SMTP_USER) is required")

    from_field = f"{from_name} <{from_email}>" if from_name else from_email
    to_list = [e.strip() for e in to.split(",") if e.strip()]
    cc_list = [e.strip() for e in cc.split(",") if e.strip()] if cc else []

    if html:
        msg: MIMEMultipart | MIMEText = MIMEMultipart("alternative")
        assert isinstance(msg, MIMEMultipart)
        msg.attach(MIMEText(body, "html", "utf-8"))
    else:
        msg = MIMEText(body, "plain", "utf-8")

    msg["Subject"] = subject
    msg["From"] = from_field
    msg["To"] = to
    if cc:
        msg["Cc"] = cc

    recipients = to_list + cc_list

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            if smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, recipients, msg.as_string())
    except smtplib.SMTPException as e:
        die(f"SMTP error: {e}")
    except OSError as e:
        die(f"connection error: {e}")

    print(f"sent via SMTP to {', '.join(to_list)}")


if __name__ == "__main__":
    main()
