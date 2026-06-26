from .data import get_market_data
from .engine import generate_signal

def main():
    print("Pulling current data...")
    try:
        data = get_market_data()
        signal = generate_signal(data)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    print("═══════════════════════════════════════")
    print("NASDAQ FUTURES SIGNAL")
    print("═══════════════════════════════════════")
    print(f"ACTION: {signal.action}")
    print(f"MARKET: {signal.market}")
    print(f"PRICE: {signal.price:.2f}")
    print(f"SESSION: {signal.session}")
    print(f"REGIME: {signal.regime}")
    print(f"SETUP TYPE: {signal.setup}")
    print(f"CONFIDENCE: {signal.confidence}")
    print("")
    print("PROP-FIRM RISK PLAN")
    print(f"- Account Balance: ₦{signal.risk_plan['Account Balance']:,.0f}")
    print(f"- Max Drawdown: ₦{signal.risk_plan['Max Drawdown']:,.0f}")
    print(f"- Phase Target: ₦{signal.risk_plan['Phase Target']:,.0f}")
    print(f"- Normal Risk/Trade: ₦{signal.risk_plan['Normal Risk/Trade']:,.0f}")
    print(f"- Hard Max Risk/Trade: ₦{signal.risk_plan['Hard Max Risk/Trade']:,.0f}")
    print(f"- Contract: {signal.risk_plan['Contract']}")
    print(f"- Stop Distance: {signal.risk_plan['Stop Distance']:.2f} points")
    if signal.risk_plan["Estimated Risk NGN"] is None and signal.action != "WAIT":
        print("- Estimated Risk: set USD_NGN_RATE to convert MNQ dollar risk into naira.")
    elif signal.action != "WAIT":
        print(f"- Estimated Risk: ₦{signal.risk_plan['Estimated Risk NGN']:,.0f}")
    print(f"- Daily Stop: ₦{signal.risk_plan['Daily Stop']:,.0f} or 2 consecutive losses")
    print("")
    print("ENTRY PLAN")
    print(f"- Entry: {signal.entry:.2f}")
    print(f"- Stop: {signal.stop:.2f}")
    print(f"- Target 1: {signal.targets[0]:.2f}")
    print(f"- Target 2: {signal.targets[1]:.2f}")
    print(f"- Risk/Reward: 1:{signal.rr:.1f}")
    print("")
    print("KEY LEVELS")
    for level, value in signal.levels.items():
        print(f"- {level}: {value:.2f}")
    print("- Opening Range High: XXXX.XX")  # Placeholder as per template
    print("- Opening Range Low: XXXX.XX")   # Placeholder as per template
    print("- Weekly Level in Play: XXXX.XX") # Placeholder as per template
    print("")
    print("SCORECARD")
    for step, (score, reason) in signal.scores.items():
        print(f"- {step}: {score} — {reason}")
    print("")
    print("REASONING")
    if signal.action == "WAIT":
        print("- Market conditions do not meet high-confidence criteria.")
        print("- Waiting for macro and technical alignment.")
    else:
        print(f"- {signal.setup} setup identified based on {signal.regime} regime.")
        print(f"- Macro bias is {signal.scores['Macro Filter'][0]} providing tailwinds.")
    print("")
    print("EXIT TRIGGERS")
    print("- Take partial profit if Target 1 is reached.")
    print("- Hold for Target 2 if momentum remains strong.")
    print("- Exit early if price closes back below/above entry structure.")
    print("- Exit on time basis if trade fails to move within 4 hours.")
    print("")
    print("INVALIDATION")
    print(f"- Price hits stop at {signal.stop:.2f}")
    print("- Macro bias shifts to neutral or opposite.")
    print("")
    print("NEWS IMPACT")
    print(f"- {signal.news}")
    print("")
    print("SOURCES")
    print("- https://finance.yahoo.com")

if __name__ == "__main__":
    main()
