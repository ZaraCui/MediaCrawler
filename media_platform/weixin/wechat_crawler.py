# media_platform/wechat/wechat_crawler.py

import asyncio
import random

import config
from base.base_crawler import AbstractCrawler
from media_platform.weixin.search import BingWeChatSearcher


class WeChatCrawler(AbstractCrawler):
    """
    微信公众号爬虫（基于搜索引擎）
    """

    async def start(self):
        if not getattr(config, "ENABLE_WECHAT", False):
            self.logger.info("WeChat crawler disabled by config")
            return

        searcher = BingWeChatSearcher(headers=self.headers)

        for account in config.WECHAT_ACCOUNTS:
            await self._crawl_account(searcher, account)
            await asyncio.sleep(
                random.uniform(*config.WECHAT_ACCOUNT_DELAY)
            )

    async def _crawl_account(self, searcher: BingWeChatSearcher, account: str):
        self.logger.info(f"[WeChat] Crawling account: {account}")

        for page in range(config.WECHAT_MAX_PAGE):
            urls = searcher.search(account, page)

            for url in urls:
                await self.save_item({
                    "platform": "wechat",
                    "account": account,
                    "url": url,
                })

            await asyncio.sleep(
                random.uniform(*config.WECHAT_REQUEST_DELAY)
            )
