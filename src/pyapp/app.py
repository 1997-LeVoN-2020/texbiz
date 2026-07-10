import os
import smtplib
import time
from collections import defaultdict
from email.header import Header
from email.mime.text import MIMEText

from flask import Flask, jsonify, request

app = Flask(__name__)

TO_ADDR = "info@tex-biz.ru"
FROM_ADDR = os.environ.get("MAIL_FROM", "noreply@tex-biz.ru")
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "25"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

RATE_LIMIT_WINDOW = 600  # seconds
RATE_LIMIT_MAX = 5  # requests per IP per window

# In-memory only — resets per worker process on restart, and isn't shared
# across multiple Passenger worker processes. Good enough to blunt naive
# spam/flooding on this low-traffic lead form without adding a dependency.
_rate_limit_hits = defaultdict(list)


def clean(value):
    return (value or "").replace("\r", " ").replace("\n", " ").strip()


def client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limited(ip):
    now = time.time()
    hits = _rate_limit_hits[ip]
    hits[:] = [t for t in hits if now - t < RATE_LIMIT_WINDOW]
    if len(hits) >= RATE_LIMIT_MAX:
        return True
    hits.append(now)
    return False


@app.route("/send", methods=["POST"])
def send():
    if rate_limited(client_ip()):
        return jsonify(ok=False, error="rate_limited"), 429

    name = clean(request.form.get("name"))
    phone = clean(request.form.get("phone"))
    object_type = clean(request.form.get("object"))
    message = clean(request.form.get("message"))
    honeypot = clean(request.form.get("website"))
    agree = request.form.get("agree")

    # Honeypot: bots fill hidden fields, humans don't. Pretend success without sending.
    if honeypot:
        return jsonify(ok=True)

    if not name or not phone or not object_type or not agree:
        return jsonify(ok=False, error="missing_fields"), 422

    body = (
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Тип объекта: {object_type}\n"
        f"Задача: {message or '-'}\n"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header("Новая заявка с сайта ТЕХБИЗ", "utf-8")
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR
    msg["Reply-To"] = FROM_ADDR

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            if SMTP_USER and SMTP_PASSWORD:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_ADDR, [TO_ADDR], msg.as_string())
    except Exception:
        return jsonify(ok=False, error="send_failed"), 500

    return jsonify(ok=True)


# Passenger (ISPmanager) imports this exact name as the WSGI entry point.
application = app

if __name__ == "__main__":
    app.run(debug=True)
