# media_platform/wechat/wechat_crawler.py

import asyncio
import random

import config
from base.base_crawler import AbstractCrawler
from media_platform.weixin.search import BingWeChatSearcher


class WeChatCrawler(AbstractCrawler):
    """
    微信公众号爬虫（基于搜索引擎）

    说明：
    - 微信公众号无公开 API
    - 不需要浏览器自动化（Playwright / CDP）
    - 不使用 AbstractCrawler 中的原生 search 机制
    - 实际采集逻辑在 start() 中完成
    """

    # ========= 必须实现的抽象方法（接口适配） =========

    async def launch_browser(self):
        """
        WeChat crawler does NOT require browser automation.

        This method exists only to satisfy the AbstractCrawler interface.
        """
        return None

    async def search(self):
        """
        WeChat crawler does NOT use platform-native search.

        Actual crawling logic is implemented in start().
        """
        return None

    # ========= 实际业务逻辑 =========

    async def start(self):
        """
        Entry point of WeChat crawler.
        """
        if not getattr(config, "ENABLE_WECHAT", False):
            self.logger.info("WeChat crawler disabled by config")
            return

        self.logger.info("[WeChat] Crawler started")

        searcher = BingWeChatSearcher(headers=self.headers)

        for account in config.WECHAT_ACCOUNTS:
            await self._crawl_account(searcher, account)
            await asyncio.sleep(
                random.uniform(*config.WECHAT_ACCOUNT_DELAY)
            )

        self.logger.info("[WeChat] Crawler finished")

    async def _crawl_account(self, searcher: BingWeChatSearcher, account: str):
        """
        Crawl articles for a single WeChat official account name
        via search engine results.
        """
        self.logger.info(f"[WeChat] Crawling account: {account}")

        for page in range(config.WECHAT_MAX_PAGE):
            urls = searcher.search(account, page)

            if not urls:
                self.logger.info(
                    f"[WeChat] No results on page {page + 1} for account {account}"
                )
                continue

            for url in urls:
                await self.save_item(
                    {
                        "platform": "wechat",
                        "account": account,
                        "url": url,
                    }
                )

            await asyncio.sleep(
                random.uniform(*config.WECHAT_REQUEST_DELAY)
            )
