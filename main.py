import os
import re
import markdown
import subprocess
import time
import json
import datetime
from dotenv import load_dotenv
from llm_client import GeminiClient, DeepSeekClient
from wechat_client import WeChatClient

load_dotenv()

CONFIG_FILE = "config.json"
RATE_LIMIT_DELAY = 10

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

class PromptManager:
    def __init__(self, directory="prompts"):
        self.directory = directory
        self.prompts = {}
        self.load_all()

    def load_all(self):
        for filename in os.listdir(self.directory):
            if filename.endswith(".md"):
                name = filename[:-3]
                path = os.path.join(self.directory, filename)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.prompts[name] = self.parse_prompt(content)

    def parse_prompt(self, content):
        sections = {}
        current_stage = None
        lines = content.split('\n')
        temp_buffer = []
        for line in lines:
            if line.startswith("## Stage"):
                if current_stage:
                    sections[current_stage] = "\n".join(temp_buffer).strip()
                current_stage = line.split(":")[0].replace("#", "").strip()
                temp_buffer = []
            elif line.startswith("System:"):
                sections[f"{current_stage}_system"] = line.replace("System:", "").strip()
            elif line.startswith("User:"):
                temp_buffer.append(line.replace("User:", "").strip())
            else:
                temp_buffer.append(line)
        if current_stage:
            sections[current_stage] = "\n".join(temp_buffer).strip()
        return sections

def update_manifest(title, filename, date_str):
    manifest_path = "docs/articles.json"
    articles = []
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            articles = json.load(f)
    
    articles.append({
        "title": title,
        "url": filename,
        "date": date_str
    })
    
    # Sort by date descending
    articles.sort(key=lambda x: x['date'], reverse=True)
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

def generate_index_html():
    """生成带有日历和下拉菜单的门户页面"""
    index_tpl = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>微信文章存档</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #07c160; text-align: center; }
        .controls { display: flex; gap: 10px; margin-bottom: 20px; justify-content: center; align-items: center; flex-wrap: wrap; }
        select, input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        #article-list { list-style: none; padding: 0; }
        #article-list li { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }
        #article-list a { text-decoration: none; color: #333; font-weight: 500; }
        #article-list a:hover { color: #07c160; }
        .date { color: #999; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>微信文章存档</h1>
        <div class="controls">
            <label>按日期筛选:</label>
            <input type="date" id="date-picker">
            <label>或选择文章:</label>
            <select id="article-dropdown">
                <option value="">-- 请选择 --</option>
            </select>
        </div>
        <ul id="article-list"></ul>
    </div>

    <script>
        let allArticles = [];
        
        async function loadArticles() {
            const res = await fetch('articles.json');
            allArticles = await res.json();
            renderList(allArticles);
            populateDropdown(allArticles);
        }

        function renderList(articles) {
            const list = document.getElementById('article-list');
            list.innerHTML = articles.map(a => `
                <li>
                    <a href="${a.url}">${a.title}</a>
                    <span class="date">${a.date}</span>
                </li>
            `).join('');
        }

        function populateDropdown(articles) {
            const dropdown = document.getElementById('article-dropdown');
            articles.forEach(a => {
                const opt = document.createElement('option');
                opt.value = a.url;
                opt.textContent = a.title;
                dropdown.appendChild(opt);
            });
        }

        document.getElementById('date-picker').addEventListener('change', (e) => {
            const selected = e.target.value;
            const filtered = allArticles.filter(a => a.date === selected);
            renderList(filtered);
        });

        document.getElementById('article-dropdown').addEventListener('change', (e) => {
            if (e.target.value) window.location.href = e.target.value;
        });

        loadArticles();
    </script>
</body>
</html>"""
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(index_tpl)

def deploy_to_github(filename, content_html, title, date_str):
    print("\n[Deploy] 正在发布到 GitHub Pages...")
    os.makedirs("docs", exist_ok=True)
    target_path = os.path.join("docs", os.path.basename(filename))
    
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }}
        h1 {{ border-bottom: 2px solid #07c160; padding-bottom: 10px; }}
        .meta {{ color: #999; margin-bottom: 20px; }}
        strong {{ color: #07c160; }}
        blockquote {{ border-left: 4px solid #eee; padding-left: 20px; color: #666; font-style: italic; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="meta">发布日期: {date_str}</div>
    {content_html}
    <hr>
    <p><a href="index.html">← 返回首页</a></p>
</body>
</html>""")

    update_manifest(title, os.path.basename(filename), date_str)
    generate_index_html()

    try:
        subprocess.run(["git", "add", "docs/"], check=True)
        subprocess.run(["git", "commit", "-m", f"Add article: {title}"], check=True)
        subprocess.run(["git", "push", "origin", "HEAD"], check=True)
        print(f"成功发布！")
    except Exception as e:
        print(f"Git 发布失败: {e}")

def main():
    config = load_config()
    pm = PromptManager()
    
    # 自动选择 Provider 和 Model (根据配置)
    if config["default_provider"] == "2":
        provider_name = "DeepSeek"
        api_key = os.getenv("DEEPSEEK_API_KEY")
        selected_model = config["deepseek"]["model"]
        llm = DeepSeekClient(api_key, model=selected_model)
    else:
        provider_name = "Gemini"
        api_key = os.getenv("GEMINI_API_KEY")
        selected_model = config["gemini"]["model"]
        llm = GeminiClient(api_key, model=selected_model)

    print(f"--- 自动识别配置: {provider_name} ({selected_model}) ---")

    # 切换提示词
    print("\n请选择提示词风格:")
    styles = list(pm.prompts.keys())
    for i, s in enumerate(styles): print(f"{i+1}. {s}")
    choice = input("请输入数字 (默认 2-psychology): ") or "2"
    prompts = pm.prompts[styles[int(choice)-1]]

    topic = input("\n请输入初步选题方向: ")

    # 运行流程
    stage1_prompt = prompts["Stage 1"].format(topic=topic)
    titles_output = llm.generate(stage1_prompt, system_instruction=prompts.get("Stage 1_system"))
    print("\n" + titles_output)

    selected_title = input("\n请复制选定的【标题】: ")
    selected_angle = input("请简述选定的【切入点/心理学概念】: ")

    # Stages...
    def generate_step(stage, prompt_key, **kwargs):
        if config["default_provider"] != "2":
            time.sleep(RATE_LIMIT_DELAY)
        print(f"[{stage}/4] 正在处理...")
        return llm.generate(prompts[prompt_key].format(**kwargs))

    outline = generate_step(2, "Stage 2", title=selected_title, angle=selected_angle)
    content = generate_step(3, "Stage 3", outline=outline)
    final_md = generate_step(4, "Stage 4", content=content)

    html_content = markdown.markdown(final_md, extensions=['extra'])
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    clean_title = re.sub(r'[\\/:*?"<>|]', '_', selected_title)
    deploy_to_github(f"{clean_title}.html", html_content, selected_title, date_str)

if __name__ == "__main__":
    main()
