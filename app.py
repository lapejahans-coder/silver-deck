import os
import io
import oandapyV20
from flask import Flask, Response, request
from apscheduler.schedulers.background import BackgroundScheduler
from silver_deck.data_oanda import get_oanda_market_data
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

def run_analysis_cycle():
    """Scheduled task to run analysis, execution and notifications."""
    if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
        print("Scheduler: Missing OANDA credentials. Cycle aborted.")
        return

    try:
        print(f"Starting analysis cycle... (Mode: {EXEC_MODE}, Execution: {ENABLE_EXECUTION})")
        data = get_oanda_market_data(OANDA_API_KEY, OANDA_ACCOUNT_ID)
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
            print(f"Signal {signal.action} processed. Notification sent.")
        else:
            print(f"Cycle result: WAIT. No notification sent.")
            
    except Exception as e:
        error_msg = f"Cycle Error: {str(e)}"
        print(error_msg)

# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(func=run_analysis_cycle, trigger="interval", minutes=INTERVAL_MINS)
scheduler.start()

@app.route('/')
def home():
    if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
        return "System ONLINE. Please configure OANDA_API_KEY and OANDA_ACCOUNT_ID in Render environment variables."
    
    try:
        data = get_oanda_market_data(OANDA_API_KEY, OANDA_ACCOUNT_ID)
        signal = generate_signal(data)
        
        output = io.StringIO()
        output.write("═══════════════════════════════════════\n")
        output.write(f"SILVER DECK v3.0 (OANDA {OANDA_ENV.upper()})\n")
        output.write("═══════════════════════════════════════\n")
        output.write(f"ACTION: {signal.action}\n")
        output.write(f"MARKET: {signal.market} (XAG/USD)\n")
        output.write(f"PRICE: {signal.price:.3f}\n\n")
        
        output.write("SYSTEM STATUS\n")
        output.write(f"- Mode: {EXEC_MODE.upper()}\n")
        output.write(f"- Execution: {'ENABLED' if ENABLE_EXECUTION else 'DISABLED (Simulation)'}\n")
        output.write(f"- Scheduler: Active ({INTERVAL_MINS}m window)\n\n")
        
        output.write("SCORECARD\n")
        for step, (score, reason) in signal.scores.items():
            output.write(f"- {step}: {score} — {reason}\n")
        
        output.write("\nENTRY PLAN (If Active)\n")
        output.write(f"- Entry: {signal.entry:.3f}\n")
        output.write(f"- Stop: {signal.stop:.3f} (Trailing Dist: {abs(signal.entry-signal.stop):.3f})\n")
        output.write(f"- Target: {signal.targets[0]:.3f}\n")
        
        return Response(output.getvalue(), mimetype='text/plain')
    except Exception as e:
        return Response(f"System Error: {str(e)}", status=500, mimetype='text/plain')

@app.route('/run')
def run_now():
    """Manual trigger endpoint."""
    run_analysis_cycle()
    return "Analysis and Notification cycle triggered manually."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
