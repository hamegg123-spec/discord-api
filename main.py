# ============================================================================
# main.py ver9 (Railway ヘルスチェック対応・完全安定版)
# ============================================================================

import os
import threading
import discord
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

print("=== main.py ver9: 起動開始 ===")

# ---------------------------------------------------------------------------
# Discord Bot
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"=== Discord Bot ログイン成功: {bot.user} ===")

def run_bot():
    print("=== Discord Bot スレッド起動開始 ===")
    token = os.environ["DISCORD_TOKEN"]
    bot.run(token)

# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------
app = FastAPI()

# ★ Railway のヘルスチェック用ルート
@app.get("/")
async def root():
    return {"status": "ok"}

class EventPayload(BaseModel):
    channelId: str
    message: str

@app.post("/post")
async def post_event(payload: EventPayload):
    print(f"=== /post 受信: {payload} ===")
    channel = bot.get_channel(int(payload.channelId))
    if channel is None:
        print("=== エラー: チャンネルが見つかりません ===")
        return {"ok": False, "error": "Channel not found"}

    await channel.send(payload.message)
    print("=== Discord 投稿成功 ===")
    return {"ok": True}

# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== main.py ver9: メイン開始 ===")

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 8080))
    print(f"=== FastAPI 起動: ポート {port} ===")
    uvicorn.run(app, host="0.0.0.0", port=port)
