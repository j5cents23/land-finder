import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = str(PROJECT_ROOT / "db" / "land_finder.db")


@dataclass(frozen=True)
class SpiderConfig:
    enabled: bool = True
    interval_hours: float = 4.0
    max_pages: int = 10
    delay_seconds: float = 2.0


@dataclass(frozen=True)
class AlertConfig:
    email_enabled: bool = True
    email_to: str = os.getenv("ALERT_EMAIL", "")
    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    hot_deal_ppa_threshold: int = 200000  # cents — $2,000/acre


@dataclass(frozen=True)
class AppConfig:
    db_path: str = DB_PATH
    spiders: dict[str, SpiderConfig] = field(default_factory=lambda: {
        "zillow": SpiderConfig(),
        "landwatch": SpiderConfig(),
        "land_com": SpiderConfig(),
        "craigslist": SpiderConfig(),
        "facebook": SpiderConfig(),
    })
    alerts: AlertConfig = field(default_factory=AlertConfig)
    user_agents: list[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    ])
