# main.py — النسخة المعدلة الجاهزة

```python
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
    r = requests.post(url, json=payload, timeout=10)
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
    if strength == "STRONG":
        return "⚡️ STRONG"
    if strength == "NORMAL":
        return "✨ NORMAL"
    if strength == "WEAK":
        return "⚠️ WEAK"
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
        f"🛑 SL: {sl}",
        "",
        f"💰 TP1: {tp1}",
        f"💰 TP2: {tp2}",
        f"💰 TP3: {tp3}",
        "",
        "⚠️ عند وصول الهدف الأول انقل الستوب إلى نقطة الدخول",
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

    # ==========================================
    # إذا التنبيه نص عادي وليس JSON
    # ==========================================
    if not data:

        raw_text = request.data.decode("utf-8")

        print("RAW TEXT:", raw_text)

        if raw_text:
            send_telegram_message(raw_text)
            return {"status": "plain_text_sent"}, 200

        return {"status": "empty"}, 400

    # ==========================================
    # JSON ALERTS
    # ==========================================

    event_name = str(data.get("event", "")).strip().upper()
    pair = data.get("ticker", data.get("pair", "XAUUSD"))
    timeframe = data.get("timeframe", "15")
    side = data.get("side", data.get("direction", ""))
    strength = data.get("strength", "")

    # ENTRY
    if event_name == "ENTRY":

        entry = data.get("entry", "0")
        sl = data.get("sl", "0")
        tp1 = data.get("tp1", "0")
        tp2 = data.get("tp2", "0")
        tp3 = data.get("tp3", "0")

        text = build_entry_message(
            pair=pair,
            timeframe=timeframe,
            direction=side,
            strength=strength,
            entry=entry,
            sl=sl,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3
        )

        send_telegram_message(text)
        return {"status": "sent_entry_alert"}, 200

    # أي JSON ثاني
    send_telegram_message(str(data))

    return {"status": "json_received"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
```

## بعد التعديل:

1. احفظ الملف.
2. اعمل Push على GitHub.
3. من Render اضغط:

   * Manual Deploy
   * Deploy latest commit

هيك:

* READY alerts النصية تشتغل.
* JSON alerts تشتغل.
* ما عاد يطلع:
  ❌ No valid JSON received
