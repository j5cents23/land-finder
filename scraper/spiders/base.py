import random
from abc import ABC, abstractmethod

import httpx


class BaseSpider(ABC):
    name: str = ""

    def __init__(self, user_agents: list[str] | None = None, delay: float = 2.0):
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ]
        self.delay = delay

    def _random_headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers=self._random_headers(),
            follow_redirects=True,
            timeout=30.0,
        )

    @abstractmethod
    async def scrape(self, criteria: dict) -> list[dict]:
        """Scrape listings and return raw dicts."""
        ...
