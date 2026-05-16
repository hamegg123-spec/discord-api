# app.py ver27.1 (Python 3.14+ 完全互換・スレッドバグ修正版)

import os
import asyncio
import threading
import datetime
from flask import Flask, request, jsonify
import main  # main.py をインポート

app = Flask(__name__)

def log_api(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [FlaskAPI] {msg}")

# Discord Botを別スレッドで安全に非同期実行する
def run_discord():
    # Python 3.14以降の仕様に合わせて、新しくクリーンなループを生成して割り当てる
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # main.py 側の loop 参照をこちらに同期する
    main.bot.loop = loop
    
    token = os.environ.get("DISCORD_TOKEN")
    try:
        # loop.run_until_complete の代わりに現代的なループ維持を使用
        loop.run_until_complete(main.bot.start(token))
    except Exception as e:
        log_api(f"❌ Discord Botループ終了エラー: {e}")
    finally:
        loop.close()

# アプリ起動時にバックグラウンドでDiscord Botを立ち上げる
log_api("Discord Botのバックグラウンドループ（新方式）を準備中...")
t = threading.Thread(target=run_discord, daemon=True)
t.start()
log_api("Discord Botのバックグラウンドスレッドを切り離しました。")

@app.route('/')
def home():
    status = "ONLINE" if main.bot_ready else "STARTING"
    return f"Bot Status: {status}", 200

@app.route('/postCastleEvent', methods=['POST'])
def post_castle_event():
    log_api("/postCastleEvent 受信しました")
    
    # 15秒間の起動待ち（少し長めに設定）
    for i in range(15):
        if main.bot_ready:
            break
        log_api(f"⏳ Botのログインを待っています... ({i}秒経過)")
        import time
        time.sleep(1)
        
    if not main.bot_ready:
        log_api("🔴 Botログイン待ちタイムアウト。503を返します。")
        return jsonify({"status": "error", "message": "Bot is not ready"}), 503

    try:
        data = request.json or {}
        channel_id = int(data.get("channelId", 0))
        text = data.get("text", "")
        
        channel = main.bot.get_channel(channel_id)
        if not channel:
            log_api(f"❌ チャンネルが見つかりません: {channel_id}")
            return jsonify({"status": "error", "message": "Channel not found"}), 400

        log_api(f"📥 スレッド安全にキューへ追加します → Channel: {channel_id}")
        
        # 安全にDiscordのイベントループにコルーチンを投げ込む
        asyncio.run_coroutine_threadsafe(
            main.send_queue.put((channel, text)), 
            main.bot.loop
        )
        
        return jsonify({"status": "success", "message": "Queued successfully"}), 200
        
    except Exception as e:
        log_api(f"❌ エラー発生: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
