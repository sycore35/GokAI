"""
GÖK SYSTEMS TECH — Browser Verification Tool
Provides headless web testing, page verification, screenshot capture,
and console error collection. Supports Playwright with an automatic HTTP/DOM fallback.
"""

import asyncio
import base64
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from gokai.packages.shared.logger import get_logger

logger = get_logger("browser_tool")


class BrowserResult(BaseModel):
    url: str
    status_code: int = 200
    title: str = ""
    content: str = ""
    console_errors: List[str] = Field(default_factory=list)
    screenshot_base64: Optional[str] = None
    duration_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


class BrowserTool:
    """Unified browser interface supporting automation and headless verification."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._has_playwright = self._check_playwright_installed()

    def _check_playwright_installed(self) -> bool:
        try:
            import playwright  # noqa: F401
            return True
        except ImportError:
            return False

    async def open_and_verify(
        self,
        url: str,
        wait_seconds: float = 2.0,
        capture_screenshot: bool = False
    ) -> BrowserResult:
        """Opens URL, collects text, console errors, and validates HTTP status."""
        start_time = time.perf_counter()

        if self._has_playwright:
            try:
                return await self._verify_playwright(url, wait_seconds, capture_screenshot, start_time)
            except Exception as ex:
                logger.warning(f"Playwright execution failed: {ex}. Falling back to HTTP client verification.")

        # HTTP/DOM fallback
        return await self._verify_http(url, start_time)

    async def _verify_playwright(
        self,
        url: str,
        wait_seconds: float,
        capture_screenshot: bool,
        start_time: float
    ) -> BrowserResult:
        from playwright.async_api import async_playwright

        console_errors: List[str] = []
        screenshot_b64 = None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: console_errors.append(str(err)))

            response = await page.goto(url, timeout=15000)
            status_code = response.status if response else 200

            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            title = await page.title()
            content = await page.content()

            if capture_screenshot:
                ss_bytes = await page.screenshot()
                screenshot_b64 = base64.b64encode(ss_bytes).decode("utf-8")

            await browser.close()

        duration = (time.perf_counter() - start_time) * 1000.0
        return BrowserResult(
            url=url,
            status_code=status_code,
            title=title,
            content=content[:5000],
            console_errors=console_errors,
            screenshot_base64=screenshot_b64,
            duration_ms=duration,
            success=status_code < 400 and len(console_errors) == 0
        )

    async def _verify_http(self, url: str, start_time: float) -> BrowserResult:
        import httpx
        import re

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url)
                duration = (time.perf_counter() - start_time) * 1000.0

                title_match = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else ""

                return BrowserResult(
                    url=url,
                    status_code=resp.status_code,
                    title=title,
                    content=resp.text[:5000],
                    console_errors=[],
                    duration_ms=duration,
                    success=resp.status_code < 400
                )
        except Exception as ex:
            duration = (time.perf_counter() - start_time) * 1000.0
            return BrowserResult(
                url=url,
                status_code=0,
                title="",
                content="",
                console_errors=[str(ex)],
                duration_ms=duration,
                success=False,
                error_message=str(ex)
            )
