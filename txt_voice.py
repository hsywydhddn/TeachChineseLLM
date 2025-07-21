# tts_module.py
import requests
import tempfile
import os
from playsound import playsound

def text_to_speech(text):
    url = "https://api.siliconflow.cn/v1/audio/speech"
    headers = {
        "Authorization": "Bearer sk-ordueuitgryiaflmkxtwslzduevnmlxxcncmggkhagfcylml",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "FunAudioLLM/CosyVoice2-0.5B",
        "input": text,
        "voice": "FunAudioLLM/CosyVoice2-0.5B:alex",
        "response_format": "mp3",
        "speed": 1.0,
        "gain": 0.0
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.ok:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(response.content)
            temp_path = f.name
        playsound(temp_path)
        os.remove(temp_path)
    else:
        print("❌ 语音合成失败：", response.text)
