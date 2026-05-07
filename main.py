from flask import Flask, request
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8614676714:AAEggjQ79qRGlP6Bl9k74A2Rfo8uuTDXBEQ"
CHAT_ID = "5170185345"

MT5_WEBHOOK_URL = "https://ladder-mortally-pouncing.ngrok-free.dev/webhook"


def send_telegram_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text}
        r = requests.post(url, json=payload, timeout=10)
        print("TELEGRAM STATUS:", r.status_code)
        print("TELEGRAM RESPONSE:", r.text)
        return r
    except Exception as e:
        print("TELEGRAM ERROR:", e)
        return None


def send_to_mt5(data):
    try:
        r = requests.post(
            MT5_WEBHOOK_URL,
            json=data,
            headers={"ngrok-skip-browser-warning": "true"},
            timeout=10
        )
        print("MT5 STATUS:", r.status_code)
        print("MT5 RESPONSE:", r.text)
        return r
    except Exception as e:
        print("MT5 ERROR:", e)
        return None


def now_text():
    return datetime.now().strftime("%H:%M")


def clean_side(value):
    text = str(value).upper().strip()
    if "BUY" in text:
        return "BUY"
    if "SELL" in text:
        return "SELL"
    return text


def get_value(data, *keys, default="-"):
    for k in keys:
        if k in data and str(data[k]).strip() != "":
            return data[k]
    return default


def force_entry_check(data, raw_text):
    check = (str(data) + " " + str(raw_text)).upper()

    if "READY" in check:
        return True

    if "CHOCH_WAIT_ZONE" in check:
        return True

    if '"EVENT": "ENTRY"' in check or "'EVENT': 'ENTRY'" in check:
        return True

    if '"EVENT":"ENTRY"' in check or "'EVENT':'ENTRY'" in check:
        return True

    if "BUY READY" in check or "SELL READY" in check:
        return True

    return False


def parse_data():
    data = request.get_json(silent=True)
    raw_text = request.data.decode("utf-8", errors="ignore").strip()

    print("RAW:", raw_text)

    if data:
        return data, raw_text

    if not raw_text:
        return {}, raw_text

    try:
        return json.loads(raw_text), raw_text
    except Exception:
        pass

    try:
        fixed = raw_text.replace("'", '"')
        return json.loads(fixed), raw_text
    except Exception:
        pass

    return {"event": "PLAIN_TEXT", "message": raw_text}, raw_text


def build_message(data, event_name):
    pair = get_value(data, "ticker", "pair", default="XAUUSD")
    tf = get_value(data, "timeframe", "tf", default="1")
    side = clean_side(get_value(data, "side", "direction", default=""))

    entry = get_value(data, "entry", default="-")
    vsl = get_value(data, "virtual_sl", "vsl", "sl", default="-")
    tp1 = get_value(data, "tp1", default="-")
    tp2 = get_value(data, "tp2", default="-")
    tp3 = get_value(data, "tp3", default="-")
    lot = get_value(data, "lot", default="-")

    direction_line = "🟢 Direction: BUY" if side == "BUY" else "🔴 Direction: SELL" if side == "SELL" else f"Direction: {side}"

    if event_name == "TP1":
        title = "👑 ROYAL TRADE TP1 👑"
        status = "✅ TP1 HIT\n🔒 Move SL to Entry"
    elif event_name == "TP2":
        title = "👑 ROYAL TRADE TP2 👑"
        status = "🎯 TP2 HIT"
    elif event_name == "TP3":
        title = "👑 ROYAL TRADE TP3 👑"
        status = "🏆 TP3 HIT"
    elif event_name == "SL":
        title = "👑 ROYAL TRADE SL 👑"
        status = "🛑 STOP LOSS HIT"
    else:
        title = "👑 ROYAL TRADE SIGNAL 👑"
        status = "📌 Trade Activated"

    return f"""{title}

📊 Pair: {pair}
⏱ TF: {tf}

{direction_line}

━━━━━━━━━━━━━━

🎯 Entry: {entry}
🛡 Virtual SL: {vsl}

🎖 TP1 → {tp1}
🎖 TP2 → {tp2}
🏆 TP3 → {tp3}

━━━━━━━━━━━━━━

📌 Lot: {lot}

{status}

📝 Risk Management:
• لا تخاطر بأكثر من 1% - 2%
• عند وصول TP1 يُفضّل نقل الستوب إلى الدخول
• التزم بإدارة رأس المال
• الصفقة حسب إعدادات المؤشر وليست نصيحة مالية

🕒 {now_text()}

#Royal_Trade"""


def build_mt5_payload(data):
    pair = get_value(data, "ticker", "pair", default="XAUUSD")
    tf = get_value(data, "timeframe", "tf", default="1")
    side = clean_side(get_value(data, "side", "direction", default=""))

    entry = get_value(data, "entry", default="")
    sl = get_value(data, "sl", "virtual_sl", "vsl", default="")
    vsl = get_value(data, "virtual_sl", "vsl", "sl", default="")
    tp1 = get_value(data, "tp1", default="")
    tp2 = get_value(data, "tp2", default="")
    tp3 = get_value(data, "tp3", default="")
    lot = get_value(data, "lot", default="0.01")

    return {
        "event": "ENTRY",
        "ticker": pair,
        "pair": pair,
        "timeframe": tf,
        "side": side,
        "direction": side,
        "entry": entry,
        "sl": sl,
        "virtual_sl": vsl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "lot": lot,
        "source": "ROYAL_TRADE_RENDER"
    }


@app.route("/", methods=["GET"])
def home():
    return "ROYAL TRADE WEBHOOK IS RUNNING", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data, raw_text = parse_data()

    print("DATA:", data)

    if not data:
        return {"status": "empty"}, 200

    event_raw = str(get_value(data, "event", default="")).upper().strip()
    side_raw = str(get_value(data, "side", "direction", default="")).upper().strip()

    if force_entry_check(data, raw_text):
        event_name = "ENTRY"
    elif event_raw in ["TP1", "TP2", "TP3", "SL", "BREAKEVEN"]:
        event_name = event_raw
    elif "BUY" in side_raw or "SELL" in side_raw:
        event_name = "ENTRY"
    else:
        event_name = event_raw or "UPDATE"

    data["event"] = event_name
    data["side"] = clean_side(get_value(data, "side", "direction", default=""))

    if event_name in ["ENTRY", "TP1", "TP2", "TP3", "SL", "BREAKEVEN", "UPDATE"]:
        text = build_message(data, event_name)
        send_telegram_message(text)

    if event_name == "ENTRY":
        mt5_payload = build_mt5_payload(data)
        print("SENDING TO MT5:", mt5_payload)
        send_to_mt5(mt5_payload)

    return {
        "status": "success",
        "event": event_name
    }, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
