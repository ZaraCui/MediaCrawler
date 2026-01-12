# media_platform/weixin/wechat_crawler.py

import asyncio
import random
import logging

import config
from base.base_crawler import AbstractCrawler
from media_platform.weixin.search import BingWeChatSearcher


class WeChatCrawler(AbstractCrawler):
    """
    微信公众号爬虫（基于搜索引擎，如 Bing）
    """

    def __init__(self):
        super().__init__()

        # 显式初始化 logger（AbstractCrawler 不保证有）
        self.logger = logging.getLogger("WeChatCrawler")

        # 显式初始化 headers（因为不走浏览器流程）
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    async def start(self):
        if not getattr(config, "ENABLE_WECHAT", False):
            self.logger.info("[WeChat] Crawler disabled by config")
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
