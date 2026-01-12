# media_platform/weixin/wechat_crawler.py

import asyncio
import random
import logging

import config
from base.base_crawler import AbstractCrawler
from media_platform.weixin.search import BingWeChatSearcher


class WeChatCrawler(AbstractCrawler):
    """
    微信公众号爬虫（基于搜索引擎）

    特点：
    - 不需要浏览器自动化
    - 不使用平台原生 API
    - 通过搜索引擎间接采集文章链接
    """

    def __init__(self):
        # 调用父类初始化（仍然需要）
        super().__init__()

        # ✅ 关键修复：显式初始化 logger（不依赖父类实现）
        self.logger = logging.getLogger("WeChatCrawler")

        # 避免 logger 未配置时无输出
        if not self.logger.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s %(levelname)s %(name)s - %(message)s",
            )

    # ========= 抽象方法适配（必须存在） =========

    async def launch_browser(self):
        """
        WeChat crawler does NOT require browser automation.
        """
        return None

    async def search(self):
        """
        WeChat crawler does NOT use platform-native search.
        """
        return None

    # ========= 实际业务逻辑 =========

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
