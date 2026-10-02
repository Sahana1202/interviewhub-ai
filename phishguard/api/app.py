from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from flask import Flask, jsonify, request
from flask_cors import CORS
from model import phishing_probability

app = Flask(__name__)
CORS(app)

SUSPICIOUS_WORDS = ("login", "verify", "secure", "update", "account", "wallet", "signin", "banking", "password")
BRAND_WORDS = ("paypal", "microsoft", "google", "apple", "amazon", "netflix", "facebook", "instagram")
RISKY_TLDS = (".zip", ".top", ".xyz", ".click", ".work", ".gq", ".tk", ".ml")


def add_signal(signals: list[dict], points: int, label: str, detail: str) -> int:
    signals.append({"points": points, "label": label, "detail": detail})
    return points


def analyze(payload: dict) -> dict:
    url = str(payload.get("url", "")).strip()
    page = payload.get("page", {}) or {}
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = (parsed.hostname or "").lower()
    signals, score = [], 0

    if parsed.scheme == "http":
        score += add_signal(signals, 12, "Unencrypted connection", "This page uses HTTP instead of HTTPS.")
    try:
        ipaddress.ip_address(host)
        score += add_signal(signals, 28, "IP address used as domain", "Legitimate services normally use a named domain.")
    except ValueError:
        pass
    if "@" in parsed.netloc:
        score += add_signal(signals, 25, "Misleading URL format", "An @ character can hide the real destination.")
    if host.count("-") >= 2:
        score += add_signal(signals, 10, "Hyphen-heavy domain", "Multiple hyphens are common in impersonation domains.")
    if any(host.endswith(tld) for tld in RISKY_TLDS):
        score += add_signal(signals, 15, "High-risk domain ending", "This domain ending is frequently abused in phishing campaigns.")
    if len(url) > 90:
        score += add_signal(signals, 8, "Long URL", "Long URLs can be used to obscure the real destination.")
    path_words = set(re.findall(r"[a-z]+", (host + parsed.path).lower()))
    keyword_hits = sorted(path_words.intersection(SUSPICIOUS_WORDS))
    if keyword_hits:
        score += add_signal(signals, min(18, 5 * len(keyword_hits)), "Credential-related wording", f"Found: {', '.join(keyword_hits)}.")
    brand_hits = [word for word in BRAND_WORDS if word in host]
    if brand_hits and host not in (f"{brand}.com" for brand in brand_hits):
        score += add_signal(signals, 22, "Possible brand impersonation", f"Brand term found in domain: {', '.join(brand_hits)}.")

    passwords = int(page.get("passwordFields", 0) or 0)
    external_action = bool(page.get("externalFormAction", False))
    title = str(page.get("title", "")).lower()
    if passwords:
        score += add_signal(signals, 12, "Password field detected", "The page requests a password.")
    if passwords and parsed.scheme == "http":
        score += add_signal(signals, 25, "Password requested over HTTP", "Credentials could be exposed in transit.")
    if external_action:
        score += add_signal(signals, 20, "External login submission", "The login form submits to another domain.")
    if any(word in title for word in ("verify", "suspended", "unusual activity", "urgent")):
        score += add_signal(signals, 10, "Urgency language", "The page title uses pressure-oriented wording.")

    features = [
        int(parsed.scheme == "http"),
        int(bool(re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host))),
        int(host.count("-") >= 2),
        int(any(host.endswith(tld) for tld in RISKY_TLDS)),
        int(len(url) > 90), int(bool(keyword_hits)), int(bool(passwords)),
        int(external_action), int(bool(brand_hits)),
    ]
    ml_probability = phishing_probability(features)
    ml_points = round(ml_probability * 25)
    if ml_points >= 8:
        score += add_signal(ml_points, "ML phishing pattern match", f"Classifier confidence: {ml_probability:.0%}.")

    score = min(score, 100)
    level = "Critical" if score >= 75 else "High" if score >= 50 else "Medium" if score >= 25 else "Low"
    verdict = "Avoid entering credentials." if score >= 50 else "Review carefully before sharing sensitive information." if score >= 25 else "No strong phishing signals were found."
    return {"url": url, "score": score, "level": level, "verdict": verdict, "mlProbability": round(ml_probability, 3), "signals": signals}


@app.post("/analyze")
def analyze_url():
    return jsonify(analyze(request.get_json(silent=True) or {}))


@app.get("/health")
def health():
    return {"status": "ok", "service": "PhishGuard API"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
