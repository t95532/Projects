"""
utils/browser.py
Playwright browser manager with human-like delay helpers.
"""

from __future__ import annotations
import asyncio
import random
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserManager:
    def __init__(self, headless: bool = False, slow_mo: int = 80):
        self.headless = headless
        self.slow_mo = slow_mo
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def start(self) -> BrowserContext:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        # Mask webdriver flag
        await self._context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return self._context

    async def new_page(self) -> Page:
        if self._context is None:
            await self.start()
        return await self._context.new_page()

    async def stop(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @staticmethod
    async def human_delay(min_ms: int = 500, max_ms: int = 1800):
        """Sleep for a random human-like duration."""
        ms = random.randint(min_ms, max_ms)
        await asyncio.sleep(ms / 1000)

    @staticmethod
    async def type_like_human(page: Page, selector: str, text: str):
        """Type text character by character with random delays."""
        await page.click(selector)
        for char in text:
            await page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.04, 0.14))
