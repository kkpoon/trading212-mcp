import argparse
import httpx
from typing import Literal, Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: Optional[str] = Field(default=None, alias="T212_API_KEY")
    api_secret: Optional[str] = Field(default=None, alias="T212_API_SECRET")
    use_live_env: Optional[bool] = Field(default=False, alias="T212_USE_LIVE")
    host: str = Field(default="127.0.0.1", alias="MCP_HOST")
    port: int = Field(default=8000, alias="MCP_PORT")

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

def _get(path: str, **kwargs: Any) -> Any:
    response = client.get(path, **kwargs)
    response.raise_for_status()
    return response.json()

def _post(path: str, **kwargs: Any) -> Any:
    response = client.post(path, **kwargs)
    response.raise_for_status()
    return response.json()

def _delete(path: str) -> None:
    response = client.delete(path)
    response.raise_for_status()

def _params(**kwargs: Any) -> Dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}

mcp = FastMCP(
    "Trading212",
    instructions="Provides tools to interact with your Trading212 account. Always ensure you have the necessary permissions and understand the implications of your actions when placing orders or accessing account data.",
    host=settings.host,
    port=settings.port,
)

@mcp.tool()
def get_account_summary() -> Dict[str, Any]:
    """Provides a breakdown of your account's cash and investment metrics."""
    return _get("/equity/account/summary")

@mcp.tool()
def get_open_positions(ticker: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all open positions for your account, optionally filtered by ticker."""
    return _get("/equity/positions", params=_params(ticker=ticker))

@mcp.tool()
def get_all_instruments() -> List[Dict[str, Any]]:
    """Retrieves all accessible instruments."""
    return _get("/equity/metadata/instruments")

@mcp.tool()
def get_exchanges() -> List[Dict[str, Any]]:
    """Retrieves all accessible exchanges and their corresponding working schedules."""
    return _get("/equity/metadata/exchanges")

@mcp.tool()
def get_pending_orders() -> List[Dict[str, Any]]:
    """Retrieves a list of all orders that are currently active."""
    return _get("/equity/orders")

@mcp.tool()
def place_market_order(ticker: str, quantity: float, extended_hours: bool = False) -> Dict[str, Any]:
    """Creates a new Market order. Use positive quantity for BUY, negative for SELL."""
    return _post("/equity/orders/market", json={
        "ticker": ticker,
        "quantity": quantity,
        "extendedHours": extended_hours
    })

@mcp.tool()
def place_limit_order(ticker: str, quantity: float, limit_price: float, time_validity: str = "DAY") -> Dict[str, Any]:
    """Creates a new Limit order. Use positive quantity for BUY, negative for SELL.
    time_validity can be 'DAY' or 'GOOD_TILL_CANCEL'."""
    return _post("/equity/orders/limit", json={
        "ticker": ticker,
        "quantity": quantity,
        "limitPrice": limit_price,
        "timeValidity": time_validity
    })

@mcp.tool()
def place_stop_order(ticker: str, quantity: float, stop_price: float, time_validity: str = "DAY") -> Dict[str, Any]:
    """Creates a new Stop order. Use positive quantity for BUY, negative for SELL."""
    return _post("/equity/orders/stop", json={
        "ticker": ticker,
        "quantity": quantity,
        "stopPrice": stop_price,
        "timeValidity": time_validity
    })

@mcp.tool()
def place_stop_limit_order(ticker: str, quantity: float, stop_price: float, limit_price: float, time_validity: str = "DAY") -> Dict[str, Any]:
    """Creates a new Stop-Limit order."""
    return _post("/equity/orders/stop_limit", json={
        "ticker": ticker,
        "quantity": quantity,
        "stopPrice": stop_price,
        "limitPrice": limit_price,
        "timeValidity": time_validity
    })

@mcp.tool()
def cancel_order(order_id: int) -> str:
    """Attempts to cancel an active, unfilled order by its unique ID."""
    _delete(f"/equity/orders/{order_id}")
    return f"Order {order_id} cancellation request accepted."

@mcp.tool()
def get_historical_dividends(ticker: Optional[str] = None, limit: int = 20, cursor: Optional[int] = None) -> Dict[str, Any]:
    """Get paid out dividends with optional filtering."""
    return _get("/equity/history/dividends", params=_params(limit=limit, ticker=ticker, cursor=cursor))

@mcp.tool()
def get_historical_orders(ticker: Optional[str] = None, limit: int = 20, cursor: Optional[int] = None) -> Dict[str, Any]:
    """Get historical orders data with optional filtering."""
    return _get("/equity/history/orders", params=_params(limit=limit, ticker=ticker, cursor=cursor))

@mcp.tool()
def get_transactions(limit: int = 20, cursor: Optional[str] = None, time: Optional[str] = None) -> Dict[str, Any]:
    """Get superficial information about movements to and from your account."""
    return _get("/equity/history/transactions", params=_params(limit=limit, cursor=cursor, time=time))

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
    data: Dict[str, Any] = {
        "dataIncluded": {
            "includeDividends": include_dividends,
            "includeInterest": include_interest,
            "includeOrders": include_orders,
            "includeTransactions": include_transactions
        }
    }
    if time_from:
        data["timeFrom"] = time_from
    if time_to:
        data["timeTo"] = time_to
    return _post("/equity/history/exports", json=data)

@mcp.tool()
def list_csv_reports() -> List[Dict[str, Any]]:
    """Retrieves a list of all requested CSV reports and their current status."""
    return _get("/equity/history/exports")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trading212 MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport to use (default: stdio)",
    )
    args = parser.parse_args()
    transport: Literal["stdio", "streamable-http"] = "streamable-http" if args.transport == "http" else "stdio"
    mcp.run(transport=transport)
