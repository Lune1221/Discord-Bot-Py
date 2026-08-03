import asyncio
import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# --- 1. Flaskサーバーの準備 (Web稼働用) ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is running!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# --- 2. Discordボットの準備 ---
intents = discord.Intents.default()
intents.message_content = True  # メッセージの内容読み取りに必須

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  print(f"ログインしました: {bot.user.name} (ID: {bot.user.id})")

  # cogsフォルダ内のファイルを自動読み込み
  for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
      cog_name = f"cogs.{filename[:-3]}"
      try:
        await bot.load_extension(cog_name)
        print(f"読み込みました: {cog_name}")
      except Exception as e:
        print(f"読み込み失敗 {cog_name}: {e}")


# --- 3. 同時起動のメイン処理 ---
async def main():
  # Flaskを別スレッドでバックグラウンド起動
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  token = os.environ.get("DISCORD_TOKEN")
  if not token:
    print("エラー: DISCORD_TOKEN が環境変数に設定されていません。")
    return

  async with bot:
    await bot.start(token)


if __name__ == "__main__":
  asyncio.run(main())
