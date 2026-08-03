import logging
import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# Flaskの開発サーバー警告とアクセスログを非表示にする
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

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
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  print(
      f"=== ログイン成功: {bot.user.name} (ID: {bot.user.id}) ===", flush=True
  )

  # 1. バッドアップル用のコグを読み込み
  try:
    await bot.load_extension("cogs.bad_apple_discord_player")
    print("読み込み成功: cogs.bad_apple_discord_player", flush=True)
  except Exception as e:
    print(f"【読み込み失敗】Bad Apple: {e}", flush=True)

  # 2. 画像をAAにするコグを読み込み（※ファイル名を image_to_aa.py にした場合）
  try:
    await bot.load_extension("cogs.image_to_aa")
    print("読み込み成功: cogs.image_to_aa", flush=True)
  except Exception as e:
    print(f"【読み込み失敗】Image to AA: {e}", flush=True)

  # 3. 【最重要】スラッシュコマンドをDiscordに同期する
  try:
    synced = await bot.tree.sync()
    print(
        f"🌟 スラッシュコマンドの同期に成功しました（合計 {len(synced)} 個）",
        flush=True,
    )
  except Exception as e:
    print(f"【同期失敗】エラー詳細: {e}", flush=True)


# --- 3. メイン起動処理 ---
if __name__ == "__main__":
  print("--- プログラムを開始します ---", flush=True)

  # Flaskを別スレッドでバックグラウンド起動
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()
  print("Flaskサーバーを別スレッドで起動しました。", flush=True)

  # トークンの確認と起動
  token = os.environ.get("DISCORD_TOKEN")
  if not token:
    print("【エラー】DISCORD_TOKEN が環境変数に設定されていません！", flush=True)
  else:
    print(
        f"DISCORD_TOKEN を取得しました（文字数: {len(token)}）。ボットを起動します...",
        flush=True,
    )
    try:
      bot.run(token)
    except Exception as e:
      print(f"ボットの起動中にエラーが発生しました: {e}", flush=True)
