import requests

url = "https://api.siliconflow.cn/v1/audio/speech"
headers = {
    "Authorization": "Bearer sk-ordueuitgryiaflmkxtwslzduevnmlxxcncmggkhagfcylml",
    "Content-Type": "application/json"
}
payload = {
    "model": "FunAudioLLM/CosyVoice2-0.5B",
    "input": "ПpиBeT, Mиp",
    "voice": "FunAudioLLM/CosyVoice2-0.5B:alex",  
    "response_format": "mp3",
    "speed": 1.0,
    "gain": 0.0
}

response = requests.post(url, headers=headers, json=payload)
print(response.status_code)

if response.ok:
    with open("test_tts.mp3", "wb") as f:
        f.write(response.content)
    print("合成成功！已保存为 test_tts.mp3")
else:
    print("失败，响应内容：", response.text)
