import os
import re
import markdown
import time
from dotenv import load_dotenv
from llm_client import DeepSeekClient
from main import PromptManager, deploy_to_github

load_dotenv()

def run_test():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    selected_model = "deepseek-reasoner"
    selected_style = "psychology"
    
    selected_title = "停止将矛盾个人化：工作中大部分抵抗，与领导本人无关"
    selected_angle = "【权威偏见与基本归因错误】 - 分析我们常将抵触情绪归因于权威者个人（如“领导针对我”），而忽略情境因素（如系统压力、角色要求）的心理误区。"
    
    print(f"--- 启动自动化测试 (Model: {selected_model}, Style: {selected_style}) ---")
    
    llm = DeepSeekClient(api_key, model=selected_model)
    pm = PromptManager()
    prompts = pm.prompts[selected_style]

    # Stage 2 (Outline)
    print(f"[2/4] 正在生成大纲...")
    stage2_prompt = prompts["Stage 2"].format(title=selected_title, angle=selected_angle)
    outline = llm.generate(stage2_prompt)
    print("大纲已完成。")

    # Stage 3 (Content)
    print(f"[3/4] 正在撰写正文...")
    stage3_prompt = prompts["Stage 3"].format(outline=outline)
    content = llm.generate(stage3_prompt)
    print("正文已完成。")

    # Stage 4 (Review)
    print(f"[4/4] 正在进行后期润色...")
    stage4_prompt = prompts["Stage 4"].format(content=content)
    final_article_md = llm.generate(stage4_prompt)
    print("润色已完成。")

    # Format & Export
    html_content = markdown.markdown(final_article_md, extensions=['extra'])
    os.makedirs("output", exist_ok=True)
    clean_title = re.sub(r'[\/:*?"<>|]', '_', selected_title)
    filename = f"output/{clean_title}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"本地文件已生成: {filename}")

    # Deploy
    deploy_to_github(f"{clean_title}.html", html_content)

if __name__ == "__main__":
    run_test()
