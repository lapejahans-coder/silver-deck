from flask import Flask, Response
from silver_deck.data import get_market_data
from silver_deck.engine import generate_signal
import io

app = Flask(__name__)

@app.route('/')
def home():
    try:
        data = get_market_data()
        signal = generate_signal(data)
        
        output = io.StringIO()
        output.write("═══════════════════════════════════════\n")
        output.write("SILVER FUTURES SIGNAL\n")
        output.write("═══════════════════════════════════════\n")
        output.write(f"ACTION: {signal.action}\n")
        output.write(f"MARKET: {signal.market}\n")
        output.write(f"PRICE: {signal.price:.2f}\n")
        output.write(f"SESSION: {signal.session}\n")
        output.write(f"REGIME: {signal.regime}\n")
        output.write(f"SETUP TYPE: {signal.setup}\n")
        output.write(f"CONFIDENCE: {signal.confidence}\n\n")
        
        output.write("ENTRY PLAN\n")
        output.write(f"- Entry: {signal.entry:.2f}\n")
        output.write(f"- Stop: {signal.stop:.2f}\n")
        output.write(f"- Target 1: {signal.targets[0]:.2f}\n")
        output.write(f"- Target 2: {signal.targets[1]:.2f}\n")
        output.write(f"- Risk/Reward: 1:{signal.rr:.1f}\n\n")
        
        output.write("KEY LEVELS\n")
        for level, value in signal.levels.items():
            output.write(f"- {level}: {value:.2f}\n")
        output.write("- Opening Range High: XXXX.XX\n")
        output.write("- Opening Range Low: XXXX.XX\n")
        output.write("- Weekly Level in Play: XXXX.XX\n\n")
        
        output.write("SCORECARD\n")
        for step, (score, reason) in signal.scores.items():
            output.write(f"- {step}: {score} — {reason}\n")
        output.write("\n")
        
        output.write("REASONING\n")
        if signal.action == "WAIT":
            output.write("- Market conditions do not meet high-confidence criteria.\n")
            output.write("- Waiting for macro and technical alignment.\n")
        else:
            output.write(f"- {signal.setup} setup identified based on {signal.regime} regime.\n")
            output.write(f"- Macro bias is {signal.scores['Macro Filter'][0]} providing tailwinds.\n")
        output.write("\n")
        
        output.write("EXIT TRIGGERS\n")
        output.write("- Take partial profit if Target 1 is reached.\n")
        output.write("- Hold for Target 2 if momentum remains strong.\n")
        output.write("- Exit early if price closes back below/above entry structure.\n")
        output.write("- Exit on time basis if trade fails to move within 4 hours.\n\n")
        
        output.write("INVALIDATION\n")
        output.write(f"- Price hits stop at {signal.stop:.2f}\n")
        output.write("- Macro bias shifts to neutral or opposite.\n\n")
        
        output.write("NEWS IMPACT\n")
        output.write(f"- {signal.news}\n\n")
        
        output.write("SOURCES\n")
        output.write("- https://finance.yahoo.com\n")
        
        return Response(output.getvalue(), mimetype='text/plain')
    except Exception as e:
        return Response(f"Error generating signal: {str(e)}", status=500, mimetype='text/plain')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
