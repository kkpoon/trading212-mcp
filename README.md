# Trading 212 MCP Server

An MCP server implementation for the [Trading 212 Public API](https://docs.trading212.com/api).

## Features

- **Accounts:** Get account summary.
- **Instruments:** List all tradable instruments.
- **Orders:** Place market/limit orders, cancel pending orders, and list active orders.
- **Positions:** List all open positions.
- **History:** Fetch historical dividends.

## Setup

1. Install dependencies using `uv`:

   ```bash
   uv sync
   ```

2. Configure environment variables:
   Copy `.env.example` to `.env` and fill in your Trading 212 API key and secret.

   ```bash
   cp .env.example .env
   ```

3. Run the server:
   ```bash
   uv run main.py
   ```

## Environment Variables

- `T212_API_KEY`: Your Trading 212 API key.
- `T212_API_SECRET`: Your Trading 212 API secret.
- `T212_USE_LIVE`: Set to `True` for live trading, `False` (default) for demo/paper trading.

## Docker

Build the image:

```bash
docker build -t trading212-mcp .
```

Run with stdio transport (default):

```bash
docker run -i \
  -e T212_API_KEY=your_key \
  -e T212_API_SECRET=your_secret \
  trading212-mcp
```

Run with HTTP transport:

```bash
docker run -p 8000:8000 \
  -e T212_API_KEY=your_key \
  -e T212_API_SECRET=your_secret \
  trading212-mcp --transport http
```

## Agent Settings

### Gemini

`.gemini/settings.json`

```json
{
  "mcpServers": {
    "trading212": {
      "command": "uv",
      "args": ["run", "main.py"],
      "env": {
        "T212_API_KEY": "$T212_API_KEY",
        "T212_API_SECRET": "$T212_API_SECRET",
        "T212_USE_LIVE": "True"
      },
      "cwd": "./path/to/trading212-mcp",
      "timeout": 30000,
      "trust": true
    }
  }
}
```
