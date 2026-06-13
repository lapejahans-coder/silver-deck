import os
import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import MarketOrderRequest
from silver_deck.engine import Signal

def execute_oanda_trade(client, account_id: str, signal: Signal):
    enable_execution = os.environ.get("ENABLE_EXECUTION", "false").lower() == "true"
    execution_mode = os.environ.get("EXECUTION_MODE", "practice").lower()
    units_size = int(os.environ.get("OANDA_UNITS", "100"))
    
    print(f"Execution Engine: ENABLE_EXECUTION={enable_execution}, MODE={execution_mode}, UNITS={units_size}")
    
    if not enable_execution:
        return f"SIMULATION: {signal.action} signal detected. Execution is DISABLED."

    if signal.action == "WAIT":
        return "No action taken (WAIT signal)."

    if signal.confidence == "LOW":
        return "SKIP: Confidence too low for automated trade execution."

    units = units_size 
    if signal.action == "SHORT":
        units = -units

    # Use 3 decimal places for XAG_USD prices
    tp_price = f"{signal.targets[0]:.3f}"
    sl_price = f"{signal.stop:.3f}"

    mo = MarketOrderRequest(
        instrument="XAG_USD",
        units=units,
        takeProfitOnFill={"price": tp_price},
        stopLossOnFill={"price": sl_price}
    )

    r = orders.OrderCreate(accountID=account_id, data=mo.data)
    try:
        client.request(r)
        fill = r.response.get('orderFillTransaction')
        order_id = fill.get('id') if fill else "N/A"
        return f"SUCCESS: {signal.action} {units} units of XAG_USD in {execution_mode.upper()} mode. Order ID: {order_id}"
    except Exception as e:
        return f"FAILURE: OANDA API error in {execution_mode} mode: {str(e)}"
