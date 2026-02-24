import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeChatClient:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None

    def get_access_token(self):
        """获取微信 Access Token"""
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"
        response = requests.get(url)
        data = response.json()
        if "access_token" in data:
            self.access_token = data["access_token"]
            logger.info("Successfully obtained Access Token")
            return self.access_token
        else:
            logger.error(f"Failed to get Access Token: {data}")
            raise Exception(f"WeChat Auth Failed: {data}")

    def upload_draft(self, title, content, author="", digest="", content_source_url="", thumb_media_id=""):
        """
        新建草稿
        thumb_media_id: 图文消息的封面图片素材id（必须有）
        """
        if not self.access_token:
            self.get_access_token()

        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"
        
        article = {
            "title": title,
            "author": author,
            "digest": digest,
            "content": content, # 注意：微信接口接收的是 HTML 格式
            "content_source_url": content_source_url,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1,
            "only_fans_can_comment": 0
        }
        
        payload = {
            "articles": [article]
        }
        
        # 微信接口要求中文字符不转义
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, data=data)
        result = response.json()
        
        if result.get("media_id"):
            logger.info(f"Draft uploaded successfully. Media ID: {result['media_id']}")
            return result["media_id"]
        else:
            logger.error(f"Failed to upload draft: {result}")
            return None
