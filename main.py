from flask import Flask, request
import requests
import os
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
        r = requests.post(MT5_WEBHOOK_URL, json=data, timeout=10)

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
    event = str(event).upper().strip()

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


@app.route("/", methods=["GET"])
def home():
    return "ROYAL TRADE WEBHOOK IS RUNNING", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    print("DATA RECEIVED:", data)

    if not data:
        raw_text = request.data.decode("utf-8")
        print("RAW TEXT:", raw_text)
        return {"status": "empty_or_invalid_json"}, 400

    event_name = str(data.get("event", "")).strip().upper()

    pair = data.get("ticker", data.get("pair", "XAUUSD"))
    timeframe = data.get("timeframe", "15")
    side = data.get("side", data.get("direction", ""))

    entry = data.get("entry", "-")
    sl = data.get("sl", "-")
    vsl = data.get("virtual_sl", sl)

    tp1 = data.get("tp1", "-")
    tp2 = data.get("tp2", "-")
    tp3 = data.get("tp3", "-")

    lot = data.get("lot", "-")

    if event_name in ["ENTRY", "TP1", "TP2", "TP3", "SL", "BREAKEVEN"]:
        text = build_trade_message(
            event=event_name,
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

        if event_name == "ENTRY":
            send_to_mt5(data)

        return {
            "status": "sent",
            "event": event_name
        }, 200

    return {
        "status": "ignored_unknown_event"
    }, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
