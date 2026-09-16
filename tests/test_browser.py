"""
Tests for BrowserTool verification.
"""

import asyncio
from gokai.packages.tools.browser import BrowserTool


def test_browser_verification():
    async def _run():
        browser = BrowserTool()
        # Verify browser can run verification on public or local endpoint
        # Even if offline, BrowserResult is cleanly returned without throwing unhandled exceptions
        res = await browser.open_and_verify("https://httpbin.org/get", wait_seconds=0.5)
        assert res is not None
        assert isinstance(res.console_errors, list)
        assert res.duration_ms >= 0

    asyncio.run(_run())
