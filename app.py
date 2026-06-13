import os
import io
import oandapyV20
import requests
import threading
from flask import Flask, Response, request
from apscheduler.schedulers.background import BackgroundScheduler
from silver_deck.data_oanda import get_oanda_market_data, OandaData
from silver_deck.engine import generate_signal
from silver_deck.execution import execute_oanda_trade
from silver_deck.notifications import send_telegram_message, format_signal_for_telegram

app = Flask(__name__)

# Config
OANDA_API_KEY = os.environ.get("OANDA_API_KEY")
OANDA_ACCOUNT_ID = os.environ.get("OANDA_ACCOUNT_ID")
OANDA_ENV = os.environ.get("OANDA_ENVIRONMENT", "practice")
ENABLE_EXECUTION = os.environ.get("ENABLE_EXECUTION", "false").lower() == "true"
EXEC_MODE = os.environ.get("EXECUTION_MODE", "practice")
INTERVAL_MINS = int(os.environ.get("ANALYSIS_INTERVAL_MINS", "15"))
APP_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://silver-deck-v3-fixed.onrender.com")

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
        if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
            print("Scheduler: Missing OANDA credentials. Cycle aborted.")
            return

        print(f"--- HEARTBEAT: Starting analysis cycle ({EXEC_MODE.upper()}) ---")
        
        # Fetch data
        data = get_oanda_market_data(OANDA_API_KEY, OANDA_ACCOUNT_ID)
        print("--- CONNECTIVITY: Data Fetched Successfully ---")
        
        signal = generate_signal(data)
        
        if signal.action != "WAIT":
            msg = format_signal_for_telegram(signal)
            
            # Execute trade if enabled
            client = oandapyV20.API(access_token=OANDA_API_KEY, environment=OANDA_ENV)
            exec_result = execute_oanda_trade(client, OANDA_ACCOUNT_ID, signal)
            
            msg += f"\n\n<b>ENGINE STATUS</b>\n"
            msg += f"- Mode: {EXEC_MODE.upper()}\n"
            msg += f"- Execution: {'Enabled' if ENABLE_EXECUTION else 'Disabled (Simulation)'}\n"
            msg += f"- Result: {exec_result}"
                
            send_telegram_message(msg)
            print(f"--- Signal {signal.action} processed. Notification sent. ---")
        else:
            print(f"--- Cycle result: WAIT. No tradeable setup found. ---")
            
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
    
    oanda_status = "PENDING"
    try:
        if OANDA_API_KEY and OANDA_ACCOUNT_ID:
            oanda = OandaData(OANDA_API_KEY, OANDA_ACCOUNT_ID, environment=OANDA_ENV)
            if oanda.check_connection():
                oanda_status = "CONNECTED ✅"
            else:
                oanda_status = "AUTH ERROR ⚠️"
        else:
            oanda_status = "MISSING CREDENTIALS ❌"
    except Exception as e:
        oanda_status = f"ERROR ⚠️ ({str(e)})"

    status_msg = (
        "🚀 <b>SILVER DECK v3.3.1 ONLINE</b>\n\n"
        f"<b>OANDA Status:</b> {oanda_status}\n"
        f"<b>Mode:</b> {EXEC_MODE.upper()}\n"
        f"<b>Execution:</b> {'ENABLED' if ENABLE_EXECUTION else 'DISABLED'}\n"
        f"<b>Interval:</b> {INTERVAL_MINS} minutes\n\n"
        "<i>Stability fix applied. Monitoring XAG/USD.</i>"
    )
    send_telegram_message(status_msg)

# Initialize scheduler only once
if not scheduler.running:
    scheduler.start()
    # Initial startup notification
    threading.Timer(5.0, notify_startup).start()

@app.route('/')
def home():
    """Dashboard view (Triggers OANDA request)."""
    if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
        return "System ONLINE. Please configure OANDA_API_KEY and OANDA_ACCOUNT_ID."
    
    try:
        data = get_oanda_market_data(OANDA_API_KEY, OANDA_ACCOUNT_ID)
        signal = generate_signal(data)
        
        output = io.StringIO()
        output.write("═══════════════════════════════════════\n")
        output.write(f"SILVER DECK v3.3.1 (OANDA {OANDA_ENV.upper()})\n")
        output.write("═══════════════════════════════════════\n")
        output.write(f"ACTION: {signal.action}\n")
        output.write(f"MARKET: {signal.market}\n")
        output.write(f"PRICE: {signal.price:.3f}\n\n")
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
