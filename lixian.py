import os
import time
import sys
import pyttsx3
import requests
import json
import re
import warnings
import threading  # 添加多线程支持
# 抑制警告
warnings.filterwarnings("ignore")
# 配置环境
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-4973364e4eab4ba8bcfef9bc52c26dfc")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
# 国家语言信息映射表
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
class TextToSpeech:
    """增强版文本转语音引擎（非阻塞）"""
    def __init__(self):
        self.engine = None
        self.target_language = None
        self.enabled = True
        self.speech_thread = None
        self.stop_event = threading.Event()
        self.queue = []
        self.queue_lock = threading.Lock()
    def initialize_engine(self):
        """初始化语音引擎（在需要时调用）"""
        try:
            if not self.engine:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 150)  # 默认语速
                self.engine.setProperty('volume', 0.9)  # 默认音量
                if self.target_language:
                    self._try_set_language()
        except Exception as e:
            print(f"语音引擎初始化失败: {str(e)}")
            self.enabled = False
    def toggle(self):
        """切换语音功能开关"""
        self.enabled = not self.enabled
        status = "启用" if self.enabled else "禁用"
        print(f"语音功能已{status}")
        return self.enabled
    def set_target_language(self, lang_code):
        """设置目标语言（来自COUNTRY_INFO配置）"""
        self.target_language = lang_code
        if self.engine:
            self._try_set_language()
        return self.target_language
    def _try_set_language(self):
        """尝试设置目标语言的语音"""
        if not self.target_language or not self.engine:
            return False
        voices = self.engine.getProperty('voices')
        language_found = False
        for voice in voices:
            if self.target_language.lower() in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                print(f"已设置语音为: {voice.name}")
                language_found = True
                return True
        if not language_found:
            for voice in voices:
                if self.target_language[:2].lower() in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    print(f"已设置近似语音为: {voice.name}")
                    language_found = True
                    return True
        print(f"警告: 未找到 {self.target_language} 语言的语音，使用默认语音")
        return False
    def _run_speech_thread(self):
        """运行语音线程处理队列中的任务"""
        self.stop_event.clear()
        while not self.stop_event.is_set():
            with self.queue_lock:
                if not self.queue:
                    time.sleep(0.1)
                    continue   
                text = self.queue.pop(0)
            try:
                self.engine.startLoop(False)
                self.engine.say(text)
                self.engine.iterate()
                while not self.stop_event.is_set() and self.engine.isBusy():
                    time.sleep(0.1)
                    
                self.engine.endLoop()
                
            except Exception as e:
                print(f"语音输出失败: {str(e)}")
                try:
                    self.engine = pyttsx3.init()
                    self.engine.setProperty('rate', 150)
                    self.engine.setProperty('volume', 0.9)
                    self._try_set_language()
                except:
                    print("无法恢复语音引擎，语音功能已禁用")
                    self.enabled = False
                    break
    def speak(self, text):
        """添加文本到语音队列（非阻塞）"""
        if not self.enabled or not text.strip():
            return
        if not self.engine:
            self.initialize_engine()
            if not self.engine:
                return
        with self.queue_lock:
            self.queue.append(text)
        if not self.speech_thread or not self.speech_thread.is_alive():
            self.speech_thread = threading.Thread(target=self._run_speech_thread, daemon=True)
            self.speech_thread.start()
                
    def stop(self):
        """停止当前朗读和语音线程"""
        self.stop_event.set()
        
        if self.engine and self.engine.isBusy():
            try:
                self.engine.stop()
            except:
                pass
        
        # 清空队列
        with self.queue_lock:
            self.queue.clear()
        
        # 等待线程结束
        if self.speech_thread and self.speech_thread.is_alive():
            try:
                self.speech_thread.join(timeout=0.5)
            except:
                pass

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
    print("注: 语音功能依赖系统安装的语言包".center(70))
    print("-" * 70)

def get_country_choice():
    print("\n请选择您的国家或语言偏好:")
    country_codes = sorted(COUNTRY_INFO.keys())
    
    # 显示国家选择菜单
    for i, code in enumerate(country_codes, 1):
        country_name, display_lang, _, speech_lang = COUNTRY_INFO[code]
        voice_note = ""  # 语音支持状态提示
        
        # 检查语音支持状态
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            supported = any(speech_lang.lower() in v.id.lower() for v in voices)
            voice_note = "✓" if supported else "⚠"
        except:
            voice_note = "?"
        
        print(f"{i}. {country_name} ({display_lang}) {voice_note}")
    
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

def create_system_prompt(language, user_level):
    """创建系统提示词"""
    # 根据用户水平定制提示词
    level_descriptions = {
        1: "使用简单词汇和短句，解释基本概念",
        2: "使用常用词汇和基本语法结构，适当解释新词",
        3: "使用复杂句式和较高级词汇，提供文化背景",
        4: "使用专业术语和复杂表达，深入探讨语言文化"
    }
    
    level_desc = level_descriptions.get(user_level, "")
    
    return (
        f"你是一位专业的对外汉语大模型，请使用{language}与学生交流。\n"
        f"学生汉语水平: {level_desc}\n"
        "教学要求:\n"
        "1. 根据学生水平调整语言复杂度\n"
        "2. 适当提供文化背景知识\n"
        "3. 重点解释汉语特有表达\n"
        "4. 每次回答包含一个语言学习点\n"
        "5. **必须使用用户选择的语言回答**\n"
    )

def query_deepseek_api(system_prompt, user_prompt):
    """调用DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API错误: {response.status_code} - {response.text}")
    
    except Exception as e:
        raise Exception(f"API请求失败: {str(e)}")
def main():
    """主交互循环"""
    welcome()
    country_code = get_country_choice()
    user_level = get_user_level()
    country_name, display_language, prompt_language, speech_language = COUNTRY_INFO[country_code]
    print(f"\n{'='*60}")
    print(f"系统设置完成! 国家: {country_name}, 语言: {display_language}, 汉语水平: {user_level}")
    print(f"{'='*60}\n")
    system_prompt = create_system_prompt(prompt_language, user_level)
    tts = TextToSpeech()
    tts.set_target_language(speech_language)
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        supported = any(speech_language.lower() in v.id.lower() for v in voices)
        
        if not supported:
            print(f"\n⚠ 警告: 系统未安装 {speech_language} 语言的语音包")
    except:
        pass
    enable_voice = input("是否启用语音输出功能? (y/n): ").lower() == 'y'
    tts.enabled = enable_voice
    print("\n您可以询问以下类型的问题:")
    print("- 汉语词汇解释 (如: '你好' 是什么意思?)")
    print("- 语法问题 (如: 怎么用 '了'?)")
    print("- 文化问题 (如: 中国人怎么庆祝春节?)")
    print("- 学习建议 (如: 如何提高汉语听力?)")
    print("- 练习对话 (如: 练习点餐对话)")
    print("- 翻译帮助 (如: 翻译 'How are you?')\n")
    print("特殊命令:")
    print("- 'voice on/off': 开启/关闭语音")
    print("- 'change': 更改系统设置")
    print("- 'lang': 查看当前语音语言设置")
    print("- 'exit': 退出系统\n")
    while True:
        question = input("\n请输入您的问题: ")
        
        if question.lower() == 'exit':
            print("\n感谢使用对外汉语教学系统，再见！")
            tts.stop()  # 停止语音引擎
            break
            
        if question.lower() == 'change':
            print("\n重新设置系统...")
            tts.stop()  # 停止语音引擎
            return main()
            
        if question.lower() == 'lang':
            if tts.target_language:
                print(f"当前目标语音语言: {tts.target_language}")
            else:
                print("尚未设置目标语音语言")
            continue
        if question.lower() in ['voice on', 'voice off']:
            new_status = question.split()[-1] == 'on'
            tts.enabled = new_status
            status = "启用" if new_status else "禁用"
            print(f"语音功能已{status}")
            continue
        try:
            print("\n思考中...", end='', flush=True)
            
            # 模拟思考过程
            for _ in range(3):
                print('.', end='', flush=True)
                time.sleep(0.5)
            print()
            response = query_deepseek_api(system_prompt, question)
            print("\n" + "=" * 60)
            print(f"AI教师回复 ({display_language}):")
            print("-" * 60)
            print(response)
            print("-" * 60)
            voice_status = "启用" if tts.enabled else "禁用"
            print(f"语音输出: {voice_status} (目标语言: {tts.target_language})")
            print("输入 'voice on/off' 切换语音，'lang' 查看语言设置")
            print("=" * 60)        
            if tts.enabled:
                print("\n正在朗读回复(后台)...")
                tts.speak(response)
                print("语音正在后台播放，您可以继续输入命令")           
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