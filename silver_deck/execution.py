import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import MarketOrderRequest
from silver_deck.engine import Signal

def execute_oanda_trade(client, account_id: str, signal: Signal):
    if signal.action == "WAIT":
        return "No action taken (WAIT signal)."

    units = 100 # Default/Small size for paper trading education
    if signal.action == "SHORT":
        units = -units

    # Create Market Order
    # Stop Loss and Take Profit can be added here based on signal.stop and signal.targets
    mo = MarketOrderRequest(
        instrument="XAG_USD",
        units=units,
        takeProfitOnFill={"price": str(round(signal.targets[0], 3))},
        stopLossOnFill={"price": str(round(signal.stop, 3))}
    )

    r = orders.OrderCreate(accountID=account_id, data=mo.data)
    try:
        client.request(r)
        return f"Trade executed: {signal.action} {units} units of XAG_USD. Order ID: {r.response.get('orderFillTransaction').get('id')}"
    except Exception as e:
        return f"Failed to execute trade: {str(e)}"
