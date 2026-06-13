import os
import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import MarketOrderRequest
from silver_deck.engine import Signal

def execute_oanda_trade(client, account_id: str, signal: Signal):
    enable_execution = os.environ.get("ENABLE_EXECUTION", "false").lower() == "true"
    execution_mode = os.environ.get("EXECUTION_MODE", "practice").lower()
    units_size = int(os.environ.get("OANDA_UNITS", "100"))
    
    # Smart Trailing Logic: Trailing distance is derived from ATR (2.5x ATR)
    # signal.stop was calculated as entry +/- 2x ATR. 
    # We'll use the difference between entry and stop as our initial trailing distance.
    trailing_distance = abs(signal.entry - signal.stop)
    
    print(f"Execution Engine: ENABLE_EXECUTION={enable_execution}, MODE={execution_mode}, UNITS={units_size}, TRAILING_DIST={trailing_distance:.3f}")
    
    if not enable_execution:
        return f"SIMULATION: {signal.action} @ {signal.entry:.3f}. Trailing SL Dist: {trailing_distance:.3f}."

    if signal.action == "WAIT":
        return "No action taken (WAIT signal)."

    if signal.confidence == "LOW":
        return "SKIP: Confidence too low for automated trade execution."

    units = units_size 
    if signal.action == "SHORT":
        units = -units

    # Build Market Order with Trailing Stop
    mo_data = MarketOrderRequest(
        instrument="XAG_USD",
        units=units,
        takeProfitOnFill={"price": f"{signal.targets[0]:.3f}"},
        # We replace fixed stopLoss with trailingStopLoss for 'Smart Stop' logic
        trailingStopLossOnFill={"distance": f"{trailing_distance:.3f}"}
    )

    r = orders.OrderCreate(accountID=account_id, data=mo_data.data)
    try:
        client.request(r)
        fill = r.response.get('orderFillTransaction')
        order_id = fill.get('id') if fill else "N/A"
        return f"SUCCESS: {signal.action} {units} units. Trailing SL active ({trailing_distance:.3f}). Order ID: {order_id}"
    except Exception as e:
        return f"FAILURE: OANDA API error: {str(e)}"
