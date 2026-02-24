import os
import json
import markdown
import datetime
import re
import argparse
from llm_client import DeepSeekClient
from main import PromptManager, deploy_to_github

def run_generate():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--angle", required=True)
    parser.add_argument("--date", default="")
    parser.add_argument("--style", default="psychology")
    args = parser.parse_args()

    pm = PromptManager()
    if args.style not in pm.prompts:
        print(f"Error: Style {args.style} not found.")
        return

    prompts = pm.prompts[args.style]
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not found in environment.")
        return

    llm = DeepSeekClient(api_key, model="deepseek-reasoner")
    
    print(f"--- 正在生成文章: {args.title} ---")
    
    print("[1/3] 正在生成大纲 (Reasoner Thinking)...")
    outline = llm.generate(prompts['Stage 2'].format(title=args.title, angle=args.angle))
    
    print("[2/3] 正在撰写正文...")
    content = llm.generate(prompts['Stage 3'].format(outline=outline))
    
    print("[3/3] 正在润色审查...")
    final_md = llm.generate(prompts['Stage 4'].format(content=content))
    
    html = markdown.markdown(final_md, extensions=['extra'])
    date_str = args.date if args.date else datetime.datetime.now().strftime('%Y-%m-%d')
    clean_title = re.sub(r'[\/:*?"<>|]', '_', args.title)
    
    deploy_to_github(f"{clean_title}.html", html, args.title, date_str)
    print(f"--- 任务完成: {args.title} ---")

if __name__ == "__main__":
    run_generate()
