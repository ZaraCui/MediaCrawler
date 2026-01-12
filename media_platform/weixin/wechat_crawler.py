# media_platform/weixin/wechat_crawler.py

import asyncio
import json
import os
import random
import time

import config
from base.base_crawler import AbstractCrawler
from media_platform.weixin.search import BingWeChatSearcher


class WeChatCrawler(AbstractCrawler):
    """
    微信公众号爬虫（基于 Bing 搜索）
    """

    def __init__(self):
        self.results = []

    async def start(self):
        if not config.ENABLE_WECHAT:
            print("[WeChat] Crawler disabled by config")
            return

        print("[WeChat] Crawler started")

        searcher = BingWeChatSearcher()

        for account in config.WECHAT_ACCOUNTS:
            print(f"[WeChat] Crawling account: {account}")

            for page in range(config.WECHAT_MAX_PAGE):
                urls = searcher.search(account, page)

                for url in urls:
                    print("FOUND:", account, url)
                    self.results.append({
                        "platform": "wechat",
                        "account": account,
                        "url": url,
                    })

                await asyncio.sleep(random.uniform(*config.WECHAT_REQUEST_DELAY))

            await asyncio.sleep(random.uniform(*config.WECHAT_ACCOUNT_DELAY))

        self._save_json()

    def _save_json(self):
        os.makedirs("data/wechat", exist_ok=True)

        filename = f"data/wechat/wechat_search_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"[WeChat] Saved {len(self.results)} items to {filename}")

    # ====== 为了满足 AbstractCrawler，不用但必须写 ======

    async def search(self):
        pass

    async def launch_browser(self, *args, **kwargs):
        raise NotImplementedError("WeChat crawler does not use browser")
