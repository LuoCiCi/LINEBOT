import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

# LINE Bot 的 Channel Access Token 和 Channel Secret
line_bot_api = LineBotApi('你的 Channel Access Token')
handler = WebhookHandler('你的 Channel Secret')

# 天氣圖片抓取函式（不存圖片，只回傳圖片 URL）
def get_weather_image_urls():
    # 使用 ChromeDriverManager 自動管理 ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # 打開目標網頁
    driver.get("https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html")

    # 等待網頁完全加載
    time.sleep(5)

    # 查找所有圖片元素
    images = driver.find_elements(By.TAG_NAME, 'img')
    image_urls = []

    # 遍歷所有找到的圖片，並篩選來自 Data/rainfall 目錄的圖片
    for img in images:
        img_url = img.get_attribute('src')

        # 只回傳來自 Data/rainfall 的圖片 URL
        if "Data/rainfall" in img_url:
            image_urls.append(img_url)

    # 關閉瀏覽器
    driver.quit()

    return image_urls

# 回應訊息的邏輯
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    if '天氣圖片' in user_message:
        image_urls = get_weather_image_urls()  # 取得天氣圖片 URL
        if image_urls:
            # 發送圖片
            for img_url in image_urls:
                line_bot_api.reply_message(
                    event.reply_token,
                    ImageSendMessage(original_content_url=img_url, preview_image_url=img_url)
                )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="未找到天氣圖片。")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入 '天氣圖片' 來獲取最新的天氣圖片")
        )

if __name__ == "__main__":
    app.run(debug=True)

