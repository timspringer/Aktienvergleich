"""Configuration for all supported stock indexes across regions."""

INDEX_CONFIG = {
    # German indexes (via finanzen.net)
    "DAX": {
        "display_name": "DAX",
        "region": "Germany",
        "currency": "EUR",
        "data_source": "finanzen_net",
        "url": "https://www.finanzen.net/index/dax",
        "description": "German Blue Chip Index (40 largest German companies)",
    },
    "MDAX": {
        "display_name": "MDAX",
        "region": "Germany",
        "currency": "EUR",
        "data_source": "finanzen_net",
        "url": "https://www.finanzen.net/index/mdax",
        "description": "Mid-Cap German Companies",
    },
    "SDAX": {
        "display_name": "SDAX",
        "region": "Germany",
        "currency": "EUR",
        "data_source": "finanzen_net",
        "url": "https://www.finanzen.net/index/sdax",
        "description": "Small-Cap German Companies",
    },
    "TecDAX": {
        "display_name": "TecDAX",
        "region": "Germany",
        "currency": "EUR",
        "data_source": "finanzen_net",
        "url": "https://www.finanzen.net/index/tecdax",
        "description": "Technology-focused German Companies",
    },
    # European indexes
    "STOXX50": {
        "display_name": "Euro Stoxx 50",
        "region": "Europe",
        "currency": "EUR",
        "data_source": "yahoo_finance",
        "ticker": "^STOXX50E",
        "description": "Leading blue-chip companies across Eurozone",
    },
    "STOXX600": {
        "display_name": "STOXX 600",
        "region": "Europe",
        "currency": "EUR",
        "data_source": "yahoo_finance",
        "ticker": "^STOXX",
        "description": "Large, mid and small-cap companies across Europe",
    },
    "CAC40": {
        "display_name": "CAC 40",
        "region": "Europe",
        "currency": "EUR",
        "data_source": "yahoo_finance",
        "ticker": "^FCHI",
        "description": "French blue-chip index",
    },
    "FTSE100": {
        "display_name": "FTSE 100",
        "region": "Europe",
        "currency": "GBP",
        "data_source": "yahoo_finance",
        "ticker": "^FTSE",
        "description": "UK blue-chip index",
    },
    # US indexes
    "SPX": {
        "display_name": "S&P 500",
        "region": "USA",
        "currency": "USD",
        "data_source": "yahoo_finance",
        "ticker": "^GSPC",
        "description": "500 largest US companies",
    },
    "CCMP": {
        "display_name": "NASDAQ 100",
        "region": "USA",
        "currency": "USD",
        "data_source": "yahoo_finance",
        "ticker": "^CCMP",
        "description": "100 largest non-financial companies on NASDAQ",
    },
    "RUT": {
        "display_name": "Russell 2000",
        "region": "USA",
        "currency": "USD",
        "data_source": "yahoo_finance",
        "ticker": "^RUT",
        "description": "Small-cap US companies",
    },
}


def get_index_config(index_name: str) -> dict | None:
    """Get configuration for a specific index."""
    return INDEX_CONFIG.get(index_name)


def get_indexes_by_region(region: str) -> dict:
    """Get all indexes for a specific region."""
    return {k: v for k, v in INDEX_CONFIG.items() if v["region"] == region}


def get_all_index_names() -> list[str]:
    """Get all configured index names."""
    return list(INDEX_CONFIG.keys())
