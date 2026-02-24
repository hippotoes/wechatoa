import os
import re
import markdown
import subprocess
import time
from dotenv import load_dotenv
from llm_client import GeminiClient, DeepSeekClient
from wechat_client import WeChatClient

load_dotenv()

# Rate limit for free tier (seconds between requests)
RATE_LIMIT_DELAY = 10

class PromptManager:
# ... (rest of PromptManager)
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
        
        # Simple parser for Stage headers
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

def deploy_to_github(filename, content_html):
    """
    将文件发布到 GitHub Pages。
    假设当前仓库已关联 GitHub 且启用了 Pages (通常是 docs 目录或 gh-pages 分支)
    """
    print("\n[Deploy] 正在发布到 GitHub Pages...")
    
    # 确保 docs 目录存在 (GitHub Pages 常用配置)
    os.makedirs("docs", exist_ok=True)
    target_path = os.path.join("docs", os.path.basename(filename))
    
    with open(target_path, "w", encoding="utf-8") as f:
        # 添加简单的 HTML 模板使页面美观
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }}
        h1 {{ border-bottom: 2px solid #07c160; padding-bottom: 10px; }}
        strong {{ color: #07c160; }}
        blockquote {{ border-left: 4px solid #eee; padding-left: 20px; color: #666; font-style: italic; }}
    </style>
</head>
<body>
    {content_html}
</body>
</html>""")

    # 执行 Git 命令
    try:
        subprocess.run(["git", "add", target_path], check=True)
        subprocess.run(["git", "commit", "-m", f"Deploy article: {filename}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f"成功！文章已发布。如果你的 GitHub Pages 设置在 docs 目录，访问地址通常为: https://<your-username>.github.io/<repo-name>/{os.path.basename(filename)}")
    except Exception as e:
        print(f"Git 发布失败: {e}")

def main():
    # 1. 检查配置与选择 Provider
    print("--- 欢迎使用微信公众号自动化流水线 ---")
    print("请选择 AI 服务商:")
    print("1. Google Gemini")
    print("2. DeepSeek")
    provider_choice = input("请输入编号 (默认 1): ") or "1"

    if provider_choice == "2":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            api_key = input("请输入你的 DeepSeek API Key: ")
            with open(".env", "a") as f:
                f.write(f"\nDEEPSEEK_API_KEY={api_key}")
            os.environ["DEEPSEEK_API_KEY"] = api_key
        
        print("\n请选择 DeepSeek 模型:")
        print("1. deepseek-chat (V3)")
        print("2. deepseek-reasoner (R1)")
        ds_model_choice = input("请输入编号 (默认 1): ") or "1"
        selected_model = "deepseek-chat" if ds_model_choice == "1" else "deepseek-reasoner"
        llm = DeepSeekClient(api_key, model=selected_model)
    else:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("--- 初始化 Gemini ---")
            api_key = input("请输入你的 Gemini API Key: ")
            with open(".env", "a") as f:
                f.write(f"\nGEMINI_API_KEY={api_key}")
            os.environ["GEMINI_API_KEY"] = api_key
        
        print("\n请选择 Gemini 模型:")
        models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        for i, m in enumerate(models):
            print(f"{i+1}. {m}")
        model_choice = input("请输入编号 (默认 1): ") or "1"
        selected_model = models[int(model_choice)-1]
        llm = GeminiClient(api_key, model=selected_model)

    pm = PromptManager()

    # 2. 切换提示词
    print("\n请选择提示词风格:")
    available_styles = list(pm.prompts.keys())
    for i, style in enumerate(available_styles):
        print(f"{i+1}. {style}")
    
    choice = input("请输入数字编号 (默认 1): ") or "1"
    selected_style = available_styles[int(choice)-1]
    prompts = pm.prompts[selected_style]

    # 3. 开始流程
    topic = input("\n请输入初步选题方向: ")

    # Stage 1
    print(f"\n[1/4] 风格: {selected_style} | 模型: {selected_model} | 正在生成选题...")
    stage1_prompt = prompts["Stage 1"].format(topic=topic)
    titles_output = llm.generate(stage1_prompt, system_instruction=prompts.get("Stage 1_system"))
    print("\n" + titles_output)

    selected_title = input("\n请复制选定的【标题】: ")
    selected_angle = input("请简述选定的【切入点/心理学概念】: ")

    # Stage 2
    print(f"\n等待 {RATE_LIMIT_DELAY}s 以适应 API 限制...")
    time.sleep(RATE_LIMIT_DELAY)
    print(f"[2/4] 正在生成大纲...")
    stage2_prompt = prompts["Stage 2"].format(title=selected_title, angle=selected_angle)
    outline = llm.generate(stage2_prompt)

    # Stage 3
    print(f"\n等待 {RATE_LIMIT_DELAY}s 以适应 API 限制...")
    time.sleep(RATE_LIMIT_DELAY)
    print(f"[3/4] 正在撰写正文...")
    stage3_prompt = prompts["Stage 3"].format(outline=outline)
    content = llm.generate(stage3_prompt)

    # Stage 4
    print(f"\n等待 {RATE_LIMIT_DELAY}s 以适应 API 限制...")
    time.sleep(RATE_LIMIT_DELAY)
    print(f"[4/4] 正在进行后期润色...")
    stage4_prompt = prompts["Stage 4"].format(content=content)
    final_article_md = llm.generate(stage4_prompt)

    # 4. 导出与发布
    html_content = markdown.markdown(final_article_md, extensions=['extra'])
    
    os.makedirs("output", exist_ok=True)
    clean_title = re.sub(r'[\\/:*?"<>|]', '_', selected_title)
    filename = f"output/{clean_title}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n本地文章已生成: {filename}")

    print("\n请选择部署方式:")
    print("1. 上传到微信草稿箱")
    print("2. 发布到 GitHub Pages")
    print("3. 仅保留本地文件")
    
    deploy_choice = input("请输入编号: ")
    
    if deploy_choice == "1":
        app_id = os.getenv("WECHAT_APP_ID")
        app_secret = os.getenv("WECHAT_APP_SECRET")
        thumb_id = os.getenv("WECHAT_THUMB_MEDIA_ID")
        if not all([app_id, app_secret, thumb_id]):
            print("错误: 微信配置不完整，请检查 .env 文件。")
        else:
            wechat = WeChatClient(app_id, app_secret)
            wechat.upload_draft(selected_title, html_content, thumb_media_id=thumb_id)
            
    elif deploy_choice == "2":
        deploy_to_github(f"{clean_title}.html", html_content)
    else:
        print("已结束。")

if __name__ == "__main__":
    main()
