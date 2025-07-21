import os
import time
import sys
import pyttsx3
import requests
import json
import warnings

# 抑制警告
warnings.filterwarnings("ignore", category=UserWarning, module="langchain")

# 配置环境
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-4973364e4eab4ba8bcfef9bc52c26dfc")

# 整合的国家语言信息映射表
COUNTRY_INFO = {
    # ISO国家代码: (国家名称, 显示语言, 提示语言, 语音引擎语言)
    "US": ("United States", "American English", "English", "en"),
    "GB": ("United Kingdom", "British English", "English", "en"),
    "CN": ("China", "简体中文", "Simplified Chinese", "zh"),
    "TW": ("Taiwan", "繁體中文", "Traditional Chinese", "zh"),
    "JP": ("Japan", "日本語", "Japanese", "ja"),
    "KR": ("South Korea", "한국어", "Korean", "ko"),
    "FR": ("France", "Français", "French", "fr"),
    "DE": ("Germany", "Deutsch", "German", "de"),
    "ES": ("Spain", "Español", "Spanish", "es"),
    "PT": ("Portugal", "Português", "Portuguese", "pt"),
    "RU": ("Russia", "Русский", "Russian", "ru"),
    "AR": ("Saudi Arabia", "العربية", "Arabic", "ar"),
    "TH": ("Thailand", "ภาษาไทย", "Thai", "th"),
    "VN": ("Vietnam", "Tiếng Việt", "Vietnamese", "vi"),
    "ID": ("Indonesia", "Bahasa Indonesia", "Indonesian", "id"),
    "SL": ("Sri Lanka", "සිංහල", "Sinhala", "si")
}

def welcome():
    """登录界面"""
    print("=" * 70)
    print("欢迎使用对外汉语大模型".center(70))
    print("=" * 70)
    print("本系统支持以下语言:".center(70))
    print("-" * 70)
    
    # 显示支持的语言列表（只展示显示语言）
    languages = sorted(set(i[1] for i in COUNTRY_INFO.values()))
    
    for i, lang in enumerate(languages, 1):
        print(f"{i}. {lang}", end="\t")
        if i % 4 == 0:
            print()
    print("\n" + "-" * 70)

def get_country_choice():
    print("\n请选择您的国家或语言偏好:")
    country_codes = sorted(COUNTRY_INFO.keys())
    
    # 显示国家选择菜单
    for i, code in enumerate(country_codes, 1):
        country_name, display_lang, _, _ = COUNTRY_INFO[code]
        print(f"{i}. {country_name} ({display_lang})")
    
    while True:
        try:
            choice = int(input("\n请输入选项编号 (1-{}): ".format(len(country_codes))))
            if 1 <= choice <= len(country_codes):
                return country_codes[choice-1]
            print("无效的选择，请重新输入。")
        except ValueError:
            print("请输入有效的数字。")

def get_user_level():
    """获取用户汉语水平"""
    print("\n请选择您的汉语水平:")
    levels = {
        1: "零基础 (Beginner)",
        2: "初级 (Elementary)",
        3: "中级 (Intermediate)",
        4: "高级 (Advanced)"
    }
    
    for key, value in levels.items():
        print(f"{key}. {value}")
    
    while True:
        try:
            choice = int(input("\n请输入选项编号 (1-4): "))
            if choice in levels:
                return choice
            print("无效的选择，请重新输入。")
        except ValueError:
            print("请输入有效的数字。")

def call_deepseek_api(language, level_desc, question):
    """直接调用DeepSeek API"""
    # 构建系统提示
    system_prompt = (
        f"你是一位专业的对外汉语大模型，请使用{language}与学生交流。\n"
        f"学生汉语水平: {level_desc}\n"
        "教学要求:\n"
        "1. 根据学生水平调整语言复杂度\n"
        "2. 适当提供文化背景知识\n"
        "3. 重点解释汉语特有表达\n"
        "4. 每次回答包含一个语言学习点\n"
        "5. **必须使用用户选择的语言回答**\n"
    )
    
    # 构建API请求
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.9,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"API调用失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"错误详情: {e.response.text}")
        return "抱歉，处理您的请求时出现问题。"

def main():
    """主交互循环"""
    welcome()
    # 1. 获取用户选择
    country_code = get_country_choice()
    user_level = get_user_level()
    
    # 2. 提取正确的信息
    country_name, display_language, prompt_language, speech_language = COUNTRY_INFO[country_code]
    
    # 根据用户水平定制提示词
    level_descriptions = {
        1: "使用简单词汇和短句，解释基本概念",
        2: "使用常用词汇和基本语法结构，适当解释新词",
        3: "使用复杂句式和较高级词汇，提供文化背景",
        4: "使用专业术语和复杂表达，深入探讨语言文化"
    }
    level_desc = level_descriptions.get(user_level, "")
    
    print(f"\n{'='*60}")
    print(f"系统设置完成! 国家: {country_name}, 语言: {display_language}, 汉语水平: {user_level}")
    print(f"{'='*60}\n")
    
    # 显示学习提示
    print("您可以询问以下类型的问题:")
    print("- 汉语词汇解释 (如: '你好' 是什么意思?)")
    print("- 语法问题 (如: 怎么用 '了'?)")
    print("- 文化问题 (如: 中国人怎么庆祝春节?)")
    print("- 学习建议 (如: 如何提高汉语听力?)")
    print("- 练习对话 (如: 练习点餐对话)")
    print("- 翻译帮助 (如: 翻译 'How are you?')\n")
    
    # 交互循环
    while True:
        question = input("\n请输入您的问题 (输入 'exit' 退出, 'change' 更改设置): ")
        
        if question.lower() == 'exit':
            print("\n感谢使用对外汉语教学系统，再见！")
            break
            
        if question.lower() == 'change':
            print("\n重新设置系统...")
            return main()
        
        try:
            print("\n思考中...", end='', flush=True)
            
            # 模拟思考过程
            for _ in range(3):
                print('.', end='', flush=True)
                time.sleep(0.5)
            print()
            
            # 调用API
            response = call_deepseek_api(prompt_language, level_desc, question)
            
            print("\n" + "=" * 60)
            print(f"AI教师回复 ({display_language}):")
            print("-" * 60)
            print(response)
            print("-" * 60)
            print("提示: 您可以继续提问，或输入 'change' 更改设置")
            print("=" * 60)

            
                
            print("提示: 您可以继续提问，或输入 'change' 更改设置")
            print("=" * 60)
        except Exception as e:
                    print(f"\n请求失败: {str(e)}")
        if "401" in str(e):
                print("错误: 认证失败，请检查API密钥")
        elif "404" in str(e):
                print("错误: API终结点不存在")
        else:
                print("可能原因: 网络问题或服务不可用")

if __name__ == "__main__":
    main()