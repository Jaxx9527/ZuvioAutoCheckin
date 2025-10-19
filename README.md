# ZuvioAutoCheckin

Zuvio自動簽到腳本  
支援GPS簽到、非GPS簽到  
在原腳本基礎上，避免了重複簽到、增加隨機座標偏移、簽到成功TG通知


## 配置
賬號密碼  
```python
    zuvio_user = zuvio(
        user_mail='@nkust.edu.tw',
        password=''
    )
```
簽到座標
```python
    zuvio_user.rollcall_data = {
        'lat': 22.647300,
        'lng': 120.328798
    }
```
接收簽到成功訊息
```
    def send_telegram_message(self, message):
        bot_token = "YOUR_BOT_TOKEN"
        chat_id = "YOUR_CHAT_ID"
```

## 部署
### 使用青龍面板
在 `依賴管理` 中安裝[requirements.txt](./requirements.txt)內依賴  
在 `文件管理` 中新增AutoCheckin.py文件，並填寫配置文件  
在 `定時任務` 中新增 `開機運行` 任務， `命令/腳本` 中輸入文件名如AutoCheckin.py   
當狀態持續顯示為運行中即為成功部署  
### 使用screen 
使用pip 安裝[requirements.txt](./requirements.txt)內依賴  
使用screen保持腳本在後台運行

