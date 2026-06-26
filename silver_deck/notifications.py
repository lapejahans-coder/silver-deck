import requests
import os

def send_telegram_message(message: str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Telegram notification skipped: Token or Chat ID not set.")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def format_signal_for_telegram(signal) -> str:
    msg = f"<b>══════════════════════</b>\n"
    msg += f"<b>NASDAQ FUTURES SIGNAL</b>\n"
    msg += f"<b>══════════════════════</b>\n"
    msg += f"<b>ACTION:</b> {signal.action}\n"
    msg += f"<b>MARKET:</b> {signal.market}\n"
    msg += f"<b>PRICE:</b> {signal.price:.3f}\n"
    msg += f"<b>REGIME:</b> {signal.regime}\n"
    msg += f"<b>SETUP:</b> {signal.setup}\n"
    msg += f"<b>CONFIDENCE:</b> {signal.confidence}\n\n"
    
    msg += f"<b>ENTRY PLAN</b>\n"
    msg += f"- Entry: {signal.entry:.3f}\n"
    msg += f"- Stop: {signal.stop:.3f}\n"
    msg += f"- Target: {signal.targets[0]:.3f}\n\n"

    msg += f"<b>PROP-FIRM RISK</b>\n"
    msg += f"- Balance: ₦{signal.risk_plan['Account Balance']:,.0f}\n"
    msg += f"- Max DD: ₦{signal.risk_plan['Max Drawdown']:,.0f}\n"
    msg += f"- Phase Target: ₦{signal.risk_plan['Phase Target']:,.0f}\n"
    msg += f"- Normal Risk/Trade: ₦{signal.risk_plan['Normal Risk/Trade']:,.0f}\n"
    msg += f"- Daily Stop: ₦{signal.risk_plan['Daily Stop']:,.0f} or 2 losses\n\n"
    
    msg += f"<b>REASONING:</b> {signal.scores['Macro Filter'][1]}\n"
    
    return msg
