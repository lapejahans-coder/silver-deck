import os
import io
import requests
import threading
from flask import Flask, Response, request
from apscheduler.schedulers.background import BackgroundScheduler
from silver_deck.data import get_market_data
from silver_deck.engine import generate_signal
from silver_deck.notifications import send_telegram_message, format_signal_for_telegram

app = Flask(__name__)

# Config
EXEC_MODE = os.environ.get("EXECUTION_MODE", "practice")
INTERVAL_MINS = int(os.environ.get("ANALYSIS_INTERVAL_MINS", "15"))
APP_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://signal-deck-nasdaq.onrender.com")

# Lock to prevent concurrent analysis cycles
analysis_lock = threading.Lock()

def self_ping():
    """Self-ping logic to keep the Render service awake."""
    try:
        health_url = f"{APP_URL.rstrip('/')}/health"
        print(f"Self-ping: Pinging {health_url}...")
        response = requests.get(health_url, timeout=10)
        print(f"Self-ping: Status Code {response.status_code}")
    except Exception as e:
        print(f"Self-ping failed: {e}")

def run_analysis_cycle():
    """Scheduled task to run analysis, execution and notifications."""
    if not analysis_lock.acquire(blocking=False):
        print("Analysis Cycle: Already running. Skipping this heartbeat.")
        return

    try:
        print(f"--- HEARTBEAT: Starting analysis cycle ({EXEC_MODE.upper()}) ---")
        
        # Fetch data
        data = get_market_data()
        print("--- CONNECTIVITY: Data Fetched Successfully ---")
        
        signal = generate_signal(data)
        
        msg = format_signal_for_telegram(signal)
        msg += f"\n\n<b>ENGINE STATUS</b>\n"
        msg += f"- Mode: {EXEC_MODE.upper()}\n"
        msg += "- Execution: Disabled (paper-trading analysis only)\n"
        send_telegram_message(msg)
        print(f"--- Cycle result: {signal.action}. Notification sent. ---")
            
    except Exception as e:
        error_msg = f"Cycle Error: {str(e)}"
        print(error_msg)
    finally:
        analysis_lock.release()

# Scheduler setup
scheduler = BackgroundScheduler()
# Analysis cycle
scheduler.add_job(func=run_analysis_cycle, trigger="interval", minutes=INTERVAL_MINS, id="analysis_job")
# Self-ping hits /health to avoid triggering full analysis
scheduler.add_job(func=self_ping, trigger="interval", minutes=10, id="ping_job")

# Startup Notification
def notify_startup():
    print("System starting up...")

    status_msg = (
        "🚀 <b>SIGNAL DECK NASDAQ ONLINE</b>\n\n"
        f"<b>Mode:</b> {EXEC_MODE.upper()}\n"
        "<b>Execution:</b> DISABLED (paper-trading analysis only)\n"
        f"<b>Interval:</b> {INTERVAL_MINS} minutes\n\n"
        "<i>Monitoring front-month NQ futures with MNQ prop-firm risk controls.</i>"
    )
    send_telegram_message(status_msg)

# Initialize scheduler only once
if not scheduler.running:
    scheduler.start()
    # Initial startup notification
    threading.Timer(5.0, notify_startup).start()

@app.route('/')
def home():
    """Dashboard view."""
    try:
        data = get_market_data()
        signal = generate_signal(data)
        
        output = io.StringIO()
        output.write("═══════════════════════════════════════\n")
        output.write("SIGNAL DECK NASDAQ\n")
        output.write("═══════════════════════════════════════\n")
        output.write(f"ACTION: {signal.action}\n")
        output.write(f"MARKET: {signal.market}\n")
        output.write(f"PRICE: {signal.price:.2f}\n")
        output.write(f"SESSION: {signal.session}\n")
        output.write(f"CONFIDENCE: {signal.confidence}\n\n")
        output.write("PROP-FIRM RISK\n")
        output.write(f"Account Balance: ₦{signal.risk_plan['Account Balance']:,.0f}\n")
        output.write(f"Max Drawdown: ₦{signal.risk_plan['Max Drawdown']:,.0f}\n")
        output.write(f"Phase Target: ₦{signal.risk_plan['Phase Target']:,.0f}\n")
        output.write(f"Normal Risk/Trade: ₦{signal.risk_plan['Normal Risk/Trade']:,.0f}\n\n")
        output.write("SYSTEM STATUS: Active ✅\n")
        
        return Response(output.getvalue(), mimetype='text/plain')
    except Exception as e:
        return Response(f"System Error: {str(e)}", status=500, mimetype='text/plain')

@app.route('/health')
def health():
    """Lightweight health check for Render and Self-Ping."""
    return "OK", 200

@app.route('/run')
def run_now():
    """Manual trigger endpoint."""
    threading.Thread(target=run_analysis_cycle).start()
    return "Analysis cycle triggered in background."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
