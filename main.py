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


def build_event_message(pair, timeframe, side, strength, event_name, custom_message=""):
    tf = format_timeframe(timeframe)
    side_line = format_direction(side) if side else ""
    strength_line = format_strength(strength) if strength else ""

    event_upper = str(event_name).upper().strip()

    if event_upper == "TP1":
        status_text = "✅ TP1 HIT\n🔒 Move SL to Entry"
    elif event_upper == "TP2":
        status_text = "🎯 TP2 HIT"
    elif event_upper == "TP3":
        status_text = "🏁 TP3 HIT\n💰 Full Target Achieved"
    elif event_upper == "SL":
        status_text = "🛑 STOP LOSS HIT\n❌ Trade Closed"
    elif event_upper == "BREAKEVEN":
        status_text = "🔒 BREAKEVEN HIT\n✅ Trade Closed at Entry"
    else:
        status_text = custom_message if custom_message else f"📢 {event_upper}"

    lines = [
        "👑 ROYAL TRADE UPDATE 👑",
        "",
        f"📊 {pair} | {tf}",
    ]

    if side_line:
        lines.append(side_line)

    if strength_line:
        lines.append(strength_line)

    lines += [
        "",
        status_text,
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
        send_telegram_message("❌ No valid JSON received on /webhook")
        return {"status": "error", "message": "invalid json"}, 400

    # fields from Pine alert()
    event_name = str(data.get("event", "")).strip().upper()
    pair = data.get("ticker", data.get("pair", "XAUUSD"))
    timeframe = data.get("timeframe", "15")
    side = data.get("side", data.get("direction", ""))
    strength = data.get("strength", "")
    custom_message = data.get("message", "")

    # ENTRY ALERT
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

    # TP1 / TP2 / TP3 / SL / BREAKEVEN
    if event_name in ["TP1", "TP2", "TP3", "SL", "BREAKEVEN"]:
        text = build_event_message(
            pair=pair,
            timeframe=timeframe,
            side=side,
            strength=strength,
            event_name=event_name,
            custom_message=custom_message
        )
        send_telegram_message(text)
        return {"status": "sent_event_alert", "event": event_name}, 200

    # fallback لو وصل شي مختلف
    fallback_text = (
        "👑 ROYAL TRADE WEBHOOK 👑\n\n"
        f"📊 {pair} | {format_timeframe(timeframe)}\n"
        f"📩 RAW DATA:\n{data}\n\n"
        f"🕒 {now_text()}"
    )
    send_telegram_message(fallback_text)
    return {"status": "sent_fallback"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
