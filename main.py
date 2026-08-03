import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# --- 1. Flaskサーバーの準備 ---
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
  print(f"=== ログイン成功: {bot.user.name} (ID: {bot.user.id}) ===")

  # cogsフォルダ内のファイルを自動読み込み
  if os.path.exists("./cogs"):
    for filename in os.listdir("./cogs"):
      if filename.endswith(".py"):
        cog_name = f"cogs.{filename[:-3]}"
        try:
          await bot.load_extension(cog_name)
          print(f"読み込み成功: {cog_name}")
        except Exception as e:
          print(f"読み込み失敗 {cog_name}: {e}")
  else:
    print("警告: cogsフォルダが見つかりません。")


# --- 3. メイン起動処理 ---
if __name__ == "__main__":
  print("--- プログラムを開始します ---")

  # Flaskを別スレッドでバックグラウンド起動
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()
  print("Flaskサーバーを別スレッドで起動しました。")

  # トークンの確認と起動
  token = os.environ.get("DISCORD_TOKEN")
  if not token:
    print("【エラー】DISCORD_TOKEN が環境変数に設定されていません！")
  else:
    print(f"DISCORD_TOKEN を取得しました（文字数: {len(token)}）。ボットを起動します...")
    try:
      bot.run(token)
    except Exception as e:
      print(f"ボットの起動中にエラーが発生しました: {e}")
