import requests
import re
import json
import random
import traceback
import time
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class WeixinUrlParser:
    def __init__(self):
        # 初始化请求会话，保持连接
        self.session = requests.Session()

    def get_pc_useragent(self):
        """随机获取PC端User-Agent"""
        pc_useragent_list = [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.3",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        return random.choice(pc_useragent_list)

    def _wx_get_uigs_para(self, html_str):
        """提取uigs参数（修复索引越界问题）"""
        if 'var uigs_para = ' in html_str:
            try:
                # 匹配uigs_para主参数
                uigs_para_match = re.findall(r'var uigs_para = (.*?);', html_str, re.S)
                if not uigs_para_match:
                    print("未匹配到uigs_para主参数")
                    return {}
                uigs_para = uigs_para_match[0]
                uigs_para = uigs_para.replace('passportUserId ? "1" : "0"', '"0"')
                uigs_para = json.loads(uigs_para)
                
                # 匹配exp_id（容错处理）
                exp_id_match = re.findall('uigs_para.exp_id = "(.*?)";', html_str, re.S)
                if exp_id_match:
                    uigs_para['exp_id'] = exp_id_match[0][:-1]
                uigs_para['right'] = 'right0_0'
                return uigs_para
            except Exception as e:
                print(f"提取uigs参数失败: {e}")
                return {}
        else:
            print('页面中未找到uigs_para参数，可能触发人机验证或页面结构变化')
            return {}

    def _wx_get_cookie(self, uigs_para, content_url):
        """构造有效Cookie"""
        cookie_params = {}
        try:
            if 'snuid' not in uigs_para:
                print("uigs_para中无snuid参数")
                return cookie_params
                
            cookie_params['SNUID'] = uigs_para['snuid']
            headers = {
                "User-Agent": self.get_pc_useragent(),
                "Accept": "text/css,*/*;q=0.1",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://weixin.sogou.com/",
                "Connection": "keep-alive",
                "Cookie": f"SNUID={uigs_para['snuid']}"
            }
            
            # 1. 获取SUID
            resp = self.session.get(
                "https://www.sogou.com/sug/css/m3.min.v.7.css",
                headers=headers,
                verify=False,
                timeout=10
            )
            if 'Set-Cookie' in resp.headers:
                suid = re.findall('SUID=(.*?);', resp.headers['Set-Cookie'], re.S)
                if suid:
                    cookie_params['SUID'] = suid[0]

            # 2. 获取JSESSIONID
            headers["Host"] = "weixin.sogou.com"
            headers["Referer"] = content_url
            resp = self.session.get(
                "https://weixin.sogou.com/websearch/wexinurlenc_sogou_profile.jsp",
                headers=headers,
                verify=False,
                timeout=10
            )
            if 'Set-Cookie' in resp.headers:
                jsessionid = re.findall('JSESSIONID=(.*?);', resp.headers['Set-Cookie'], re.S)
                if jsessionid:
                    cookie_params['JSESSIONID'] = jsessionid[0]

            # 3. 获取SUV
            headers["Host"] = "pb.sogou.com"
            headers["Referer"] = "https://weixin.sogou.com/"
            resp = self.session.get(
                "https://pb.sogou.com/pv.gif",
                headers=headers,
                params=uigs_para,
                verify=False,
                timeout=10
            )
            if 'Set-Cookie' in resp.headers:
                suv = re.findall('SUV=(.*?);', resp.headers['Set-Cookie'], re.S)
                if suv:
                    cookie_params['SUV'] = suv[0]
                    
            return cookie_params
        except Exception as e:
            print(f"构造Cookie失败: {e}")
            return {}

    def get_cookie(self, html_str, content_url):
        """对外提供Cookie获取接口"""
        try:
            uigs_para = self._wx_get_uigs_para(html_str)
            if not uigs_para:
                return ""
            cookie_params = self._wx_get_cookie(uigs_para, content_url)
            if 'SNUID' in cookie_params and 'SUV' in cookie_params:
                return f"SNUID={cookie_params['SNUID']}; SUV={cookie_params['SUV']}"
            return ""
        except Exception as e:
            print(f"获取Cookie异常: {e}")
            return ""

    def _wx_get_k_h(self, url):
        """拼接k和h参数"""
        try:
            b = int(random.random() * 100) + 1
            a = url.find("url=")
            if a == -1 or len(url) < a + 4 + 21 + b + 1:
                print(f"URL格式异常，无法拼接k/h参数: {url}")
                return url
            h_value = url[a + 4 + 21 + b: a + 4 + 21 + b + 1]
            return f"{url}&k={b}&h={h_value}"
        except Exception as e:
            print(f"拼接k/h参数失败: {e}")
            return url

    def get_real_url(self, url, html_str):
        """核心方法：解析真实微信文章URL"""
        real_url = ''
        try:
            # 1. 获取有效Cookie
            cookie = self.get_cookie(html_str, url)
            if not cookie:
                print("Cookie获取失败，尝试跳过Cookie直接解析")
                # 无Cookie时仍尝试请求
                headers = {"User-Agent": self.get_pc_useragent()}
            else:
                headers = {
                    "User-Agent": self.get_pc_useragent(),
                    "Cookie": cookie,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Referer": "https://weixin.sogou.com/",
                    "Connection": "keep-alive"
                }
            
            # 2. 拼接k/h参数
            url = self._wx_get_k_h(url)
            
            # 3. 发送请求（允许跳转，多轮尝试）
            for _ in range(2):  # 最多尝试2次
                resp = self.session.get(
                    url=url,
                    headers=headers,
                    allow_redirects=True,
                    verify=False,
                    timeout=15
                )
                # 直接返回最终跳转的URL
                if resp.url and resp.url.startswith('https://mp.weixin.qq.com/'):
                    real_url = resp.url
                    break
                # 从响应文本解析
                elif resp.status_code == 200:
                    url_parts = re.findall(r"url \+= '(.*?)'", resp.text, re.S)
                    if url_parts:
                        real_url = ''.join(url_parts).replace("@", "")
                        if real_url.startswith('//'):
                            real_url = 'https:' + real_url
                        break
                time.sleep(1)  # 重试前延时
                
            # 清理URL
            if real_url:
                if '#' in real_url:
                    real_url = real_url.split('#')[0]
                if '&amp;' in real_url:
                    real_url = real_url.replace('&amp;', '&')
        except Exception as e:
            print(f"解析真实URL异常: {traceback.format_exc()}")
        return real_url

# ==================== 针对你的Token运行 ====================
if __name__ == "__main__":
    # 初始化解析器
    parser = WeixinUrlParser()
    
    # 1. 构造完整的搜狗跳转链接（使用你的Token）
    YOUR_TOKEN = "dn9a_-gY295K0Rci_xozVXfdMkSQTLW6cwJThYulHEtVjXrGTiVgS6OZocm_zbFRkjNXDo_uSGAglOopRc3FnFqXa8Fplpd9KUDhGrmnMxFDervkPT75uYAroSq-pKZKF2ebcQCj-3hbjvQf4RSlFHUycpHZF7U851YDus3pVaO7W928yfs-C3_Yg_J_gYOhfzHsZAYekAu9jSwKaDxp79TSQtyenPP2HYbmCQw7v81iynmULkbBHu-WVN--SdwTuaoqfo7KmcN6VKrzu_4XKA"
    content_url = f"https://weixin.sogou.com/link?url={YOUR_TOKEN}"
    print(f"构造的搜狗链接: {content_url}")
    
    # 2. 先访问搜狗微信首页获取有效html_str（避免搜索标题的麻烦）
    try:
        # 模拟人工访问，添加延时
        time.sleep(random.uniform(2, 4))
        index_url = "https://weixin.sogou.com/"
        headers = {
            "User-Agent": parser.get_pc_useragent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        resp = parser.session.get(index_url, headers=headers, verify=False, timeout=15)
        resp.encoding = "utf-8"
        html_str = resp.text
        print(f"获取搜狗首页源码长度: {len(html_str)}")
        
        # 3. 解析真实URL
        real_url = parser.get_real_url(content_url, html_str)
        if real_url:
            print(f"\n✅ 解析成功！真实微信文章URL: {real_url}")
        else:
            print("\n❌ 解析失败！可能原因：Token已过期/IP被拦截/需要微信登录")
            # 备选方案：直接尝试访问链接（手动验证Token是否有效）
            print("\n🔍 备选验证：直接访问搜狗链接（浏览器打开）:")
            print(content_url)
            
    except Exception as e:
        print(f"获取搜狗首页源码失败: {e}")