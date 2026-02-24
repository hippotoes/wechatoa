import os
import markdown
import json
import datetime
import re
from main import deploy_to_github

def test_batch():
    test_articles = [
        # Day 1
        {"title": "理解‘聚光灯效应’：你没那么多人关注", "date": "2026-02-22"},
        {"title": "为什么我们总是想讨好所有人？", "date": "2026-02-22"},
        {"title": "如何克服社交焦虑的三个小技巧", "date": "2026-02-22"},
        # Day 2
        {"title": "延迟满足感：通往成功的必经之路", "date": "2026-02-23"},
        {"title": "确认偏误：为什么你只相信你愿意相信的", "date": "2026-02-23"},
        {"title": "职场中的‘达克效应’及其应对", "date": "2026-02-23"},
        # Day 3
        {"title": "如何建立健康的边界感", "date": "2026-02-24"},
        {"title": "心理暗示：如何给自己积极的力量", "date": "2026-02-24"},
        {"title": "拒绝内耗的5个心理学建议", "date": "2026-02-24"},
    ]

    for art in test_articles:
        print(f"Generating mock article: {art['title']} for {art['date']}")
        dummy_content = f"<p>这是关于 {art['title']} 的测试正文内容。</p><p>发布于 {art['date']}。</p>"
        clean_title = re.sub(r'[\/:*?"<>|]', '_', art['title'])
        deploy_to_github(f"{clean_title}.html", dummy_content, art['title'], art['date'])

if __name__ == "__main__":
    # Ensure docs is empty for a clean test
    if os.path.exists("docs/articles.json"):
        os.remove("docs/articles.json")
    test_batch()
