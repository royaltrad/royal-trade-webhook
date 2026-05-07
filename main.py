from flask import Flask, request
import requests
import json
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8614676714:AAEggjQ79qRGlP6Bl9k74A2Rfo8uuTDXBEQ"
CHAT_ID = "5170185345"
MT5_WEBHOOK_URL = "https://ladder-mortally-pouncing.ngrok-free.dev/webhook"


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    return requests.post(url, json=payload, timeout=10)


def send_to_mt5(data):
    try:
        r = requests.post(
            MT5_WEBHOOK_URL,
            json=data,
            headers={
                "ngrok-skip-browser-warning": "true"
            },
            timeout=10
        )

        print("MT5 STATUS:", r.status_code)
        print("MT5 RESPONSE:", r.text)

    except Exception as e:
        print("MT5 ERROR:", e)


def now_text():
    return datetime.now().strftime("%H:%M")


def clean_side(side):
    side = str(side).upper()

    if "BUY" in side:
        return "BUY"

    if "SELL" in side:
        return "SELL"

    return side


def normalize_event(event, side=""):
    event = str(event).upper()
    side = str(side).upper()

    if (
        event in [
            "READY",
            "CHOCH_WAIT_ZONE",
            "ENTRY",
            "BUY",
            "SELL",
            "SIGNAL"
        ]
        or "READY" in side
    ):
        return "ENTRY"

    return event


def build_trade_message(data):
    pair = data.get("ticker", "XAUUSD")
    tf = data.get("timeframe", "1")
    side = clean_side(data.get("side", ""))

    entry = data.get("entry", "-")
    vsl = data.get("virtual_sl", "-")

    tp1 = data.get("tp1", "-")
    tp2 = data.get("tp2", "-")
    tp3 = data.get("tp3", "-")

    lot = data.get("lot", "-")

    return f"""
👑 ROYAL TRADE SIGNAL 👑

📊 Pair: {pair}
⏱ TF: {tf}

{"🟢 BUY" if side == "BUY" else "🔴 SELL"}

━━━━━━━━━━━━━━

🎯 Entry: {entry}
🛡 Virtual SL: {vsl}

🎖 TP1 → {tp1}
🎖 TP2 → {tp2}
🏆 TP3 → {tp3}

━━━━━━━━━━━━━━

📌 Lot: {lot}

📝 Risk Management:
• لا تخاطر بأكثر من 1%-2%
• عند TP1 انقل الستوب للدخول
• التزم بالخطة

🕒 {now_text()}

#Royal_Trade
"""


@app.route("/", methods=["GET"])
def home():
    return "ROYAL TRADE WEBHOOK IS RUNNING", 200


@app.route("/webhook", methods=["POST"])
def webhook():

    raw_text = request.data.decode("utf-8", errors="ignore")

    print("RAW:", raw_text)

    data = request.get_json(silent=True)

    if not data:

        try:
            fixed = raw_text.replace("'", '"')
            data = json.loads(fixed)

        except:
            return {
                "status": "invalid_json"
            }, 200

    print("DATA:", data)

    event_name = normalize_event(
        data.get("event", ""),
        data.get("side", "")
    )

    data["event"] = event_name

    text = build_trade_message(data)

    send_telegram_message(text)

    if event_name == "ENTRY":

        mt5_data = {
            "event": "ENTRY",
            "ticker": data.get("ticker", "XAUUSD"),
            "side": clean_side(data.get("side", "")),
            "entry": data.get("entry", ""),
            "sl": data.get("sl", ""),
            "virtual_sl": data.get("virtual_sl", ""),
            "tp1": data.get("tp1", ""),
            "tp2": data.get("tp2", ""),
            "tp3": data.get("tp3", ""),
            "lot": data.get("lot", "0.01"),
            "timeframe": data.get("timeframe", "1")
        }

        print("SENDING TO MT5:", mt5_data)

        send_to_mt5(mt5_data)

    return {
        "status": "success"
    }, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
