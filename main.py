from flask import Flask, request
import requests
import os
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

    r = requests.post(url, json=payload, timeout=10)

    print("TELEGRAM STATUS:", r.status_code)
    print("TELEGRAM RESPONSE:", r.text)

    return r


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

        return r

    except Exception as e:
        print("MT5 SEND ERROR:", e)
        return None


def now_text():
    return datetime.now().strftime("%H:%M")


def format_timeframe(tf):
    tf = str(tf).strip().upper()

    if tf.isdigit():
        return f"{tf}M"

    return tf


def format_direction(side):
    side = str(side).upper().strip()

    if side == "BUY":
        return "🟢 Direction: BUY"

    if side == "SELL":
        return "🔴 Direction: SELL"

    return f"📍 Direction: {side}"


def risk_management_text(event):
    event = str(event).upper().strip()

    if event == "TP1":
        return (
            "📝 Risk Management:\n"
            "• TP1 تم تحقيقه بنجاح\n"
            "• يُفضّل نقل الستوب إلى نقطة الدخول\n"
            "• خفّف المخاطرة واحمِ الأرباح\n"
            "• التزم بإدارة رأس المال"
        )

    if event == "SL":
        return (
            "📝 Risk Management:\n"
            "• الصفقة أُغلقت على وقف الخسارة\n"
            "• لا تدخل صفقة جديدة بدون إشارة واضحة\n"
            "• التزم بنسبة مخاطرة ثابتة\n"
            "• لا تعوّض الخسارة بعشوائية"
        )

    if event == "TP3":
        return (
            "📝 Risk Management:\n"
            "• تم تحقيق الهدف الكامل\n"
            "• لا تطارد السوق بعد الهدف\n"
            "• احمِ أرباحك وانتظر فرصة جديدة\n"
            "• التداول يحتاج انضباط"
        )

    return (
        "📝 Risk Management:\n"
        "• استخدم إدارة رأس مال مناسبة\n"
        "• لا تخاطر بأكثر من 1% - 2% من الحساب\n"
        "• عند وصول TP1 يُفضّل نقل الستوب إلى الدخول\n"
        "• الصفقة حسب إعدادات المؤشر وليست نصيحة مالية"
    )


def normalize_event(event):
    event = str(event).upper().strip()

    if event in [
        "CHOCH_WAIT_ZONE",
        "READY",
        "READY_ENTRY",
        "READY_TO_ENTER",
        "WAIT_ZONE",
        "BUY",
        "SELL",
        "SIGNAL",
        "TRADE",
        "OPEN"
    ]:
        return "ENTRY"

    return event


def build_trade_message(
    event,
    pair,
    timeframe,
    side,
    entry,
    sl,
    vsl,
    tp1,
    tp2,
    tp3,
    lot
):
    tf = format_timeframe(timeframe)
    event = normalize_event(event)

    if event == "ENTRY":
        title = "👑 ROYAL TRADE SIGNAL 👑"
        status = "📌 Trade Activated"

    elif event == "TP1":
        title = "👑 ROYAL TRADE TP1 👑"
        status = "✅ TP1 HIT\n🔒 Move SL to Entry"

    elif event == "TP2":
        title = "👑 ROYAL TRADE TP2 👑"
        status = "🎯 TP2 HIT"

    elif event == "TP3":
        title = "👑 ROYAL TRADE TP3 👑"
        status = "🏆 TP3 HIT\n💰 Full Target Achieved"

    elif event == "SL":
        title = "👑 ROYAL TRADE SL 👑"
        status = "🛑 STOP LOSS HIT\n❌ Trade Closed"

    elif event == "BREAKEVEN":
        title = "👑 ROYAL TRADE BREAKEVEN 👑"
        status = "📌 Risk Management Active\n🔒 Breakeven Activated"

    else:
        title = "👑 ROYAL TRADE UPDATE 👑"
        status = "📢 Trade Update"

    lines = [
        title,
        "",
        f"📊 Pair: {pair}",
        f"⏱️ TF: {tf}",
        "",
        format_direction(side),
        "",
        "━━━━━━━━━━━━━━",
        "",
        f"🎯 Entry: {entry}",
        f"🛡 Virtual SL: {vsl}",
        "",
        "⚠️ SL وهمي ويُحسب حسب إعدادات المؤشر",
        "",
        "━━━━━━━━━━━━━━",
        "",
        f"🎖 TP1 → {tp1}",
        f"🎖 TP2 → {tp2}",
        f"🏆 TP3 → {tp3}",
        "",
        "━━━━━━━━━━━━━━",
        "",
        f"📌 Lot: {lot}",
        "",
        status,
        "",
        risk_management_text(event),
        "",
        "━━━━━━━━━━━━━━",
        "",
        f"🕒 {now_text()}",
        "",
        "#Royal_Trade"
    ]

    return "\n".join(lines)


def parse_request_data():
    data = request.get_json(silent=True)

    if data:
        return data

    raw_text = request.data.decode("utf-8", errors="ignore").strip()
    print("RAW TEXT:", raw_text)

    if not raw_text:
        return None

    try:
        fixed_text = raw_text.replace("'", '"')
        return json.loads(fixed_text)
    except Exception as e:
        print("JSON PARSE ERROR:", e)

    return {
        "event": "PLAIN_TEXT",
        "message": raw_text
    }


def build_mt5_payload(data, event_name, pair, timeframe, side, entry, sl, vsl, tp1, tp2, tp3, lot):
    mt5_data = data.copy()

    mt5_data["event"] = "ENTRY"
    mt5_data["ticker"] = pair
    mt5_data["pair"] = pair
    mt5_data["timeframe"] = timeframe
    mt5_data["side"] = str(side).upper().strip()
    mt5_data["direction"] = str(side).upper().strip()

    mt5_data["entry"] = entry
    mt5_data["sl"] = sl
    mt5_data["virtual_sl"] = vsl

    mt5_data["tp1"] = tp1
    mt5_data["tp2"] = tp2
    mt5_data["tp3"] = tp3

    mt5_data["lot"] = lot

    mt5_data["source_event"] = event_name
    mt5_data["trade_mode"] = "AUTO_ENTRY"

    return mt5_data


@app.route("/", methods=["GET"])
def home():
    return "ROYAL TRADE WEBHOOK IS RUNNING", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = parse_request_data()

    print("DATA RECEIVED:", data)

    if not data:
        return {"status": "empty"}, 200

    event_name = str(data.get("event", "")).strip().upper()
    normalized_event = normalize_event(event_name)

    if normalized_event == "PLAIN_TEXT":
        msg = data.get("message", "")
        if msg:
            send_telegram_message(msg)

        return {"status": "plain_text_sent"}, 200

    pair = data.get("ticker", data.get("pair", "XAUUSD"))
    timeframe = data.get("timeframe", data.get("tf", "15"))
    side = data.get("side", data.get("direction", ""))

    entry = data.get("entry", "-")
    sl = data.get("sl", "-")
    vsl = data.get("virtual_sl", data.get("vsl", sl))

    tp1 = data.get("tp1", "-")
    tp2 = data.get("tp2", "-")
    tp3 = data.get("tp3", "-")

    lot = data.get("lot", "-")

    telegram_events = [
        "ENTRY",
        "TP1",
        "TP2",
        "TP3",
        "SL",
        "BREAKEVEN"
    ]

    mt5_events = [
        "ENTRY"
    ]

    if normalized_event in telegram_events:
        text = build_trade_message(
            event=normalized_event,
            pair=pair,
            timeframe=timeframe,
            side=side,
            entry=entry,
            sl=sl,
            vsl=vsl,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            lot=lot
        )

        send_telegram_message(text)

    if normalized_event in mt5_events:
        mt5_data = build_mt5_payload(
            data=data,
            event_name=event_name,
            pair=pair,
            timeframe=timeframe,
            side=side,
            entry=entry,
            sl=sl,
            vsl=vsl,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            lot=lot
        )

        print("SENDING SIGNAL TO MT5...")
        print("MT5 PAYLOAD:", mt5_data)

        send_to_mt5(mt5_data)

    return {
        "status": "processed",
        "original_event": event_name,
        "normalized_event": normalized_event
    }, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
