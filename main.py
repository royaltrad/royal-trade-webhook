from flask import Flask, request
import requests
import os
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8614676714:AAEggjQ79qRGlP6Bl9k74A2Rfo8uuTDXBEQ"
CHAT_ID = "5170185345"


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    r = requests.post(url, json=payload)
    print("TELEGRAM STATUS:", r.status_code)
    print("TELEGRAM RESPONSE:", r.text)
    return r


def now_text():
    return datetime.now().strftime("%H:%M")


def format_timeframe(tf):
    tf = str(tf).strip().upper()
    if tf.isdigit():
        return f"{tf}M"
    return tf


def format_direction(direction):
    direction = str(direction).upper().strip()
    if direction == "BUY":
        return "📈 BUY"
    if direction == "SELL":
        return "📉 SELL"
    return f"📍 {direction}"


def format_strength(strength):
    strength = str(strength).upper().strip()
    if not strength:
        return ""
    return f"⚡️ {strength}"


def build_entry_message(pair, timeframe, direction, strength, entry, sl, tp1, tp2, tp3):
    direction_line = format_direction(direction)
    strength_line = format_strength(strength)
    tf = format_timeframe(timeframe)

    lines = [
        "👑 ROYAL TRADE SIGNAL 👑",
        "",
        f"📊 {pair} | {tf}",
        direction_line,
    ]

    if strength_line:
        lines.append(strength_line)

    lines += [
        "",
        f"🎯 Entry: {entry}",
        f"🛑 SL: {sl} (وهمي)",
        "",
        f"💰 TP1: {tp1}",
        f"💰 TP2: {tp2}",
        f"💰 TP3: {tp3}",
        "",
        "⚠️ وقف الخسارة وهمي",
        "🔒 عند وصول الهدف الأول انقل الستوب إلى نقطة الدخول",
        "",
        f"🕒 {now_text()}"
    ]

    return "\n".join(lines)


def normalize_manage_text(text):
    t = str(text).strip()
    upper_t = t.upper()

    if "TP1" in upper_t:
        return "✅ TP1 HIT\n🔒 Move SL to Entry"
    if "TP2" in upper_t:
        return "🎯 TP2 HIT\n🔒 SL remains at Entry"
    if "TP3" in upper_t:
        return "🏁 TP3 HIT\n💰 Full Target Achieved"
    if "STOP LOSS" in upper_t or "SL HIT" in upper_t:
        return "🛑 STOP LOSS HIT\n❌ Trade Closed"

    return t


def build_manage_message(pair, timeframe, raw_message):
    tf = format_timeframe(timeframe)
    msg = normalize_manage_text(raw_message)

    lines = [
        "👑 ROYAL TRADE UPDATE 👑",
        "",
        f"📊 {pair} | {tf}",
        "",
        msg,
        "",
        f"🕒 {now_text()}"
    ]
    return "\n".join(lines)


@app.route("/", methods=["GET"])
def home():
    return "ROYAL TRADE WEBHOOK IS RUNNING", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    print("DATA RECEIVED:", data)

    if not data:
        send_telegram_message("❌ ما وصل JSON صحيح إلى webhook")
        return {"status": "error"}, 400

    pair = data.get("pair", "XAUUSD")
    timeframe = data.get("timeframe", "15")

    manage_message = data.get("message")
    if manage_message:
        text = build_manage_message(pair, timeframe, manage_message)
        send_telegram_message(text)
        return {"status": "sent_manage_alert"}, 200

    direction = data.get("direction", "")
    strength = data.get("strength", "")

    entry = data.get("entry", "0")
    sl = data.get("sl", "0")
    tp1 = data.get("tp1", "0")
    tp2 = data.get("tp2", "0")
    tp3 = data.get("tp3", "0")

    text = build_entry_message(
        pair=pair,
        timeframe=timeframe,
        direction=direction,
        strength=strength,
        entry=entry,
        sl=sl,
        tp1=tp1,
        tp2=tp2,
        tp3=tp3
    )

    send_telegram_message(text)
    return {"status": "sent_entry_alert"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
