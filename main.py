import httpx
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    api_key: Optional[str] = Field(default=None, alias="T212_API_KEY")
    api_secret: Optional[str] = Field(default=None, alias="T212_API_SECRET")
    use_live_env: Optional[bool] = Field(default=False, alias="T212_USE_LIVE")

settings = Settings()

if settings.api_key is None or settings.api_secret is None:
    raise ValueError("T212_API_KEY and T212_API_SECRET must be set in environment variables")

BASE_URL = "https://live.trading212.com/api/v0" if settings.use_live_env else "https://demo.trading212.com/api/v0"

# HTTP Client with Basic Auth
client = httpx.Client(
    base_url=BASE_URL,
    auth=(settings.api_key, settings.api_secret),
    timeout=30.0
)

mcp = FastMCP(
    "Trading212", 
    instructions="Provides tools to interact with your Trading212 account. Always ensure you have the necessary permissions and understand the implications of your actions when placing orders or accessing account data."
)

@mcp.tool()
def get_account_summary() -> Dict[str, Any]:
    """Provides a breakdown of your account's cash and investment metrics."""
    response = client.get("/equity/account/summary")
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_open_positions(ticker: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all open positions for your account, optionally filtered by ticker."""
    params = {}
    if ticker:
        params["ticker"] = ticker
    response = client.get("/equity/positions", params=params)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_all_instruments() -> List[Dict[str, Any]]:
    """Retrieves all accessible instruments."""
    response = client.get("/equity/metadata/instruments")
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_exchanges() -> List[Dict[str, Any]]:
    """Retrieves all accessible exchanges and their corresponding working schedules."""
    response = client.get("/equity/metadata/exchanges")
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_pending_orders() -> List[Dict[str, Any]]:
    """Retrieves a list of all orders that are currently active."""
    response = client.get("/equity/orders")
    response.raise_for_status()
    return response.json()

@mcp.tool()
def place_market_order(ticker: str, quantity: float, extended_hours: bool = False) -> Dict[str, Any]:
    """Creates a new Market order. Use positive quantity for BUY, negative for SELL."""
    data = {
        "ticker": ticker,
        "quantity": quantity,
        "extendedHours": extended_hours
    }
    response = client.post("/equity/orders/market", json=data)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def place_limit_order(ticker: str, quantity: float, limit_price: float, time_validity: str = "DAY") -> Dict[str, Any]:
    """Creates a new Limit order. Use positive quantity for BUY, negative for SELL. 
    time_validity can be 'DAY' or 'GOOD_TILL_CANCEL'."""
    data = {
        "ticker": ticker,
        "quantity": quantity,
        "limitPrice": limit_price,
        "timeValidity": time_validity
    }
    response = client.post("/equity/orders/limit", json=data)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def place_stop_order(ticker: str, quantity: float, stop_price: float, time_validity: str = "DAY") -> Dict[str, Any]:
    """Creates a new Stop order. Use positive quantity for BUY, negative for SELL."""
    data = {
        "ticker": ticker,
        "quantity": quantity,
        "stopPrice": stop_price,
        "timeValidity": time_validity
    }
    response = client.post("/equity/orders/stop", json=data)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def place_stop_limit_order(ticker: str, quantity: float, stop_price: float, limit_price: float, time_validity: str = "DAY") -> Dict[str, Any]:
    """Creates a new Stop-Limit order."""
    data = {
        "ticker": ticker,
        "quantity": quantity,
        "stopPrice": stop_price,
        "limitPrice": limit_price,
        "timeValidity": time_validity
    }
    response = client.post("/equity/orders/stop_limit", json=data)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def cancel_order(order_id: int) -> str:
    """Attempts to cancel an active, unfilled order by its unique ID."""
    response = client.delete(f"/equity/orders/{order_id}")
    response.raise_for_status()
    return f"Order {order_id} cancellation request accepted."

@mcp.tool()
def get_historical_dividends(ticker: Optional[str] = None, limit: int = 20, cursor: Optional[int] = None) -> Dict[str, Any]:
    """Get paid out dividends with optional filtering."""
    params = {"limit": limit}
    if ticker:
        params["ticker"] = ticker # type: ignore
    if cursor:
        params["cursor"] = cursor
    response = client.get("/equity/history/dividends", params=params)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_historical_orders(ticker: Optional[str] = None, limit: int = 20, cursor: Optional[int] = None) -> Dict[str, Any]:
    """Get historical orders data with optional filtering."""
    params = {"limit": limit}
    if ticker:
        params["ticker"] = ticker # type: ignore
    if cursor:
        params["cursor"] = cursor
    response = client.get("/equity/history/orders", params=params)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_transactions(limit: int = 20, cursor: Optional[str] = None, time: Optional[str] = None) -> Dict[str, Any]:
    """Get superficial information about movements to and from your account."""
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor # type: ignore
    if time:
        params["time"] = time # type: ignore
    response = client.get("/equity/history/transactions", params=params)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def request_csv_report(
    include_dividends: bool = True,
    include_interest: bool = True,
    include_orders: bool = True,
    include_transactions: bool = True,
    time_from: Optional[str] = None,
    time_to: Optional[str] = None
) -> Dict[str, Any]:
    """Initiates the generation of a CSV report containing historical account data."""
    data = {
        "dataIncluded": {
            "includeDividends": include_dividends,
            "includeInterest": include_interest,
            "includeOrders": include_orders,
            "includeTransactions": include_transactions
        }
    }
    if time_from:
        data["timeFrom"] = time_from # type: ignore
    if time_to:
        data["timeTo"] = time_to # type: ignore
    response = client.post("/equity/history/exports", json=data)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def list_csv_reports() -> List[Dict[str, Any]]:
    """Retrieves a list of all requested CSV reports and their current status."""
    response = client.get("/equity/history/exports")
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    mcp.run(transport="stdio")
