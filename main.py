from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = "8614676714:AAEggjQ79qRGlP6Bl9k74A2Rfo8uuTDXBEQ"
CHAT_ID = "5170185345"


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    r = requests.post(url, json=payload)
    print("TELEGRAM STATUS:", r.status_code)
    print("TELEGRAM RESPONSE:", r.text)
    return r


@app.route("/", methods=["GET"])
def home():
    return "ROYAL TRADE WEBHOOK IS RUNNING", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    if not data:
        send_telegram_message("❌ ما وصل JSON صحيح إلى webhook")
        return {"status": "error"}, 400

    pair = data.get("pair", "XAUUSD")
    timeframe = data.get("timeframe", "15m")
    direction = str(data.get("direction", "BUY")).upper()

    entry = data.get("entry", "0")
    sl = data.get("sl", "0")
    tp1 = data.get("tp1", "0")
    tp2 = data.get("tp2", "0")
    tp3 = data.get("tp3", "0")

    message = f"""👑 ROYAL TRADE SIGNAL 👑

📊 Pair: {pair}
⏱️ Timeframe: {timeframe}
📌 Direction: {direction}

🎯 Entry: {entry}
🛑 SL: {sl}

💰 TP1: {tp1}
💰 TP2: {tp2}
💰 TP3: {tp3}
"""

    send_telegram_message(message)
    return {"status": "sent"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
