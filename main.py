from flask import Flask, request, jsonify
import requests
import json
import os
import time
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8614676714:AAEggjQ79qRGlP6Bl9k74A2Rfo8uuTDXBEQ"
CHAT_ID = "5170185345"

# EA يسحب من /last_signal، لذلك ngrok اختياري وليس ضروري هنا
MT5_WEBHOOK_URL = "https://ladder-mortally-pouncing.ngrok-free.dev/webhook"

LAST_SIGNAL = {}


def send_telegram_message(text):
    try:
        if not BOT_TOKEN or not CHAT_ID:
            print("TELEGRAM SKIPPED: BOT_TOKEN or CHAT_ID is empty")
            return None

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text}
        r = requests.post(url, json=payload, timeout=10)

        print("TELEGRAM STATUS:", r.status_code)
        print("TELEGRAM RESPONSE:", r.text)
        return r

    except Exception as e:
        print("TELEGRAM ERROR:", e)
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


def detect_event(data, raw_text):
    event_raw = str(get_value(data, "event", default="")).upper().strip()
    pending_raw = str(get_value(data, "pending_type", "order_type", default="")).upper().strip()
    side_raw = str(get_value(data, "side", "direction", default="")).upper().strip()
    check = (str(data) + " " + str(raw_text)).upper()

    if event_raw == "LIMIT" or pending_raw in ["BUY_LIMIT", "SELL_LIMIT"]:
        return "LIMIT"

    if event_raw in ["ENTRY", "TP1", "TP2", "TP3", "SL", "BREAKEVEN"]:
        return event_raw

    if "CHOCH_WAIT_ZONE" in check:
        return "LIMIT"

    if "READY" in check:
        return "ENTRY"

    if "BUY" in side_raw or "SELL" in side_raw:
        return "ENTRY"

    return event_raw or "UPDATE"


def detect_pending_type(data, event_name):
    pending_type = str(get_value(data, "pending_type", "order_type", default="")).upper().strip()
    side = clean_side(get_value(data, "side", "direction", default=""))

    if pending_type in ["BUY_LIMIT", "SELL_LIMIT"]:
        return pending_type

    if event_name == "LIMIT":
        if side == "BUY":
            return "BUY_LIMIT"
        if side == "SELL":
            return "SELL_LIMIT"

    return ""


def build_message(data, event_name):
    pair = get_value(data, "ticker", "pair", default="XAUUSD")
    tf = get_value(data, "timeframe", "tf", default="1")
    side = clean_side(get_value(data, "side", "direction", default=""))
    pending_type = detect_pending_type(data, event_name)

    entry = get_value(data, "entry", default="-")
    vsl = get_value(data, "virtual_sl", "vsl", "sl", default="-")
    tp1 = get_value(data, "tp1", default="-")
    tp2 = get_value(data, "tp2", default="-")
    tp3 = get_value(data, "tp3", default="-")
    lot = get_value(data, "lot", default="-")

    direction_line = "🟢 Direction: BUY" if side == "BUY" else "🔴 Direction: SELL" if side == "SELL" else f"Direction: {side}"

    if event_name == "LIMIT":
        title = "👑 ROYAL TRADE LIMIT ORDER 👑"
        status = f"📌 Pending Order Ready\n🧾 Type: {pending_type}"
    elif event_name == "ENTRY":
        title = "👑 ROYAL TRADE SIGNAL 👑"
        status = "📌 Trade Activated"
    elif event_name == "TP1":
        title = "👑 ROYAL TRADE TP1 👑"
        status = "✅ TP1 HIT\n💰 Trade Closed"
    elif event_name == "TP2":
        title = "👑 ROYAL TRADE TP2 👑"
        status = "🎯 TP2 HIT"
    elif event_name == "TP3":
        title = "👑 ROYAL TRADE TP3 👑"
        status = "🏆 TP3 HIT\n💰 Trade Closed"
    elif event_name == "SL":
        title = "👑 ROYAL TRADE SL 👑"
        status = "🛑 VIRTUAL SL HIT\n❌ Trade Closed"
    elif event_name == "BREAKEVEN":
        title = "👑 ROYAL TRADE BREAKEVEN 👑"
        status = "🟠 Breakeven Hit\nTrade Closed"
    else:
        title = "👑 ROYAL TRADE UPDATE 👑"
        status = "📢 Trade Update"

    return f"""{title}

📊 Pair: {pair}
⏱ TF: {tf}
{direction_line}

━━━━━━━━━━━━━━

🎯 Entry: {entry}
🛡 Virtual SL: {vsl}

✅ TP1: {tp1}
✅ TP2: {tp2}
🏆 TP3: {tp3}

━━━━━━━━━━━━━━

📌 Lot: {lot}

{status}

📋 Risk Management:
• SL وهمي حسب المؤشر
• الصفقة تُغلق تلقائياً عند TP1 حسب طلبك
• التزم بإدارة رأس المال

🕒 {now_text()}

#Royal_Trade"""


def build_signal_payload(data, event_name):
    pair = get_value(data, "ticker", "pair", default="XAUUSD")
    tf = get_value(data, "timeframe", "tf", default="1")
    side = clean_side(get_value(data, "side", "direction", default=""))
    pending_type = detect_pending_type(data, event_name)

    entry = get_value(data, "entry", default="")
    sl = get_value(data, "sl", "virtual_sl", "vsl", default="")
    vsl = get_value(data, "virtual_sl", "vsl", "sl", default="")
    tp1 = get_value(data, "tp1", default="")
    tp2 = get_value(data, "tp2", default="")
    tp3 = get_value(data, "tp3", default="")
    lot = get_value(data, "lot", default="0.01")

    signal_id = str(get_value(data, "signal_id", "id", "time", default=""))
    if signal_id == "" or signal_id == "-":
        signal_id = f"{int(time.time())}_{event_name}_{pair}_{side}_{entry}_{tp1}"

    payload = {
        "status": "signal",
        "id": signal_id,
        "event": event_name,
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
        "source": "ROYAL_TRADE_RENDER",
        "received_at": datetime.utcnow().isoformat()
    }

    if event_name == "LIMIT":
        payload["pending_type"] = pending_type

    return payload


@app.route("/", methods=["GET"])
def home():
    return "ROYAL TRADE WEBHOOK IS RUNNING", 200


@app.route("/last_signal", methods=["GET"])
def last_signal():
    if not LAST_SIGNAL:
        return jsonify({"status": "no_signal"}), 200
    return jsonify(LAST_SIGNAL), 200


@app.route("/clear_signal", methods=["GET", "POST"])
def clear_signal():
    global LAST_SIGNAL
    LAST_SIGNAL = {}
    return jsonify({"status": "cleared"}), 200


@app.route("/webhook", methods=["POST"])
def webhook():
    global LAST_SIGNAL

    data, raw_text = parse_data()
    print("DATA:", data)

    if not data:
        return {"status": "empty"}, 200

    event_name = detect_event(data, raw_text)
    side = clean_side(get_value(data, "side", "direction", default=""))

    data["event"] = event_name
    data["side"] = side

    if event_name == "LIMIT":
        data["pending_type"] = detect_pending_type(data, event_name)

    if event_name == "PLAIN_TEXT":
        msg = data.get("message", "")
        if msg:
            send_telegram_message(msg)
        return {"status": "plain_text_sent"}, 200

    if event_name in ["ENTRY", "LIMIT", "TP1", "TP2", "TP3", "SL", "BREAKEVEN", "UPDATE"]:
        text = build_message(data, event_name)
        send_telegram_message(text)

    # مهم: نحفظ الدخول والخروج حتى الـ EA يسحبهم
    if event_name in ["ENTRY", "LIMIT", "TP1", "TP3", "SL", "BREAKEVEN"]:
        LAST_SIGNAL = build_signal_payload(data, event_name)
        print("SAVED LAST_SIGNAL:", LAST_SIGNAL)

    return {
        "status": "success",
        "event": event_name,
        "pending_type": data.get("pending_type", ""),
        "saved_for_mt5": event_name in ["ENTRY", "LIMIT", "TP1", "TP3", "SL", "BREAKEVEN"]
    }, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
