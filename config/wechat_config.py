# config/wechat_config.py
# 微信公众号平台配置（基于搜索引擎）

# 是否启用 wechat 平台
ENABLE_WECHAT = True

# 要抓取的公众号列表
WECHAT_ACCOUNTS = [
    "新民晚报",
    "澎湃新闻",
    "人民日报",
]

# Bing 搜索分页数（1 页≈10 条）
WECHAT_MAX_PAGE = 5

# 请求延时（秒）
WECHAT_REQUEST_DELAY = (2, 4)

# 公众号之间的延时（秒）
WECHAT_ACCOUNT_DELAY = (5, 10)

# 搜索引擎（目前只支持 bing）
WECHAT_SEARCH_ENGINE = "bing"
