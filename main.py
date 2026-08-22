import logging
import os
import threading
import urllib.parse

import asyncpg
import discord
from discord.ext import commands
from flask import Flask, redirect, request, session
import requests

# ========================================
# Flask
# ========================================

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

app = Flask(__name__)
# セッション（OAuth2の維持）に必要なシークレットキー
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get(
    "REDIRECT_URI",
    "https://discord-bot-py-4mzn.onrender.com/auth/callback",
)

# 拒否したい特定のサーバーID
TARGET_GUILD_ID = "1392780216241491968"


@app.route("/")
def home():
  return "Bot is running!"


# 1. 認証開始ルート
@app.route("/auth/login")
def auth_login():
  if not CLIENT_ID or not REDIRECT_URI:
    return "Client ID または Redirect URI が設定されていません。", 500

  discord_login_url = (
      f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}"
      f"&response_type=code"
      f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
      f"&scope=guilds+identify"
  )
  return redirect(discord_login_url)


# 2. Discord認証コールバックルート
@app.route("/auth/callback")
def auth_callback():
  code = request.args.get("code")
  if not code:
    return "認証コードが取得できませんでした。", 400

  data = {
      "client_id": CLIENT_ID,
      "client_secret": CLIENT_SECRET,
      "grant_type": "authorization_code",
      "code": code,
      "redirect_uri": REDIRECT_URI,
  }
  headers = {"Content-Type": "application/x-www-form-urlencoded"}

  response = requests.post(
      "https://discord.com/api/oauth2/token", data=data, headers=headers
  )
  tokens = response.json()

  if "access_token" not in tokens:
    return (
        f"アクセストークンの取得に失敗しました: {tokens.get('error_description', tokens)}",
        400,
    )

  access_token = tokens["access_token"]
  api_headers = {"Authorization": f"Bearer {access_token}"}

  # ユーザーが参加しているサーバー一覧を取得
  guilds_response = requests.get(
      "https://discord.com/api/users/@me/guilds", headers=api_headers
  )
  user_guilds = guilds_response.json()

  if isinstance(user_guilds, dict) and "error" in user_guilds:
    return (
        f"サーバー情報の取得に失敗しました: {user_guilds.get('message')}",
        400,
    )

  # 特定のサーバー（TARGET_GUILD_ID）に入っているかチェック
  is_in_target = any(
      str(guild.get("id")) == TARGET_GUILD_ID for guild in user_guilds
  )

  if is_in_target:
    return (
        "❌ 認証失敗: あなたは参加が禁止されている特定のサーバーに加入しているため、"
        "認証を完了できません。"
    )

  return (
      "✨ 認証成功！禁止されている特定サーバーへの加入は確認されませんでした。"
      "（ロール付与や次の処理へ進めます）"
  )


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# ========================================
# Discord Bot
# ========================================

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ========================================
# Bot Ready
# ========================================


@bot.event
async def on_ready():
  print(f"=== ログイン成功: {bot.user.name} (ID: {bot.user.id}) ===", flush=True)

  # ========================================
  # PostgreSQL
  # ========================================

  if not hasattr(bot, "pool"):
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
      try:
        bot.pool = await asyncpg.create_pool(
            database_url, min_size=1, max_size=5, statement_cache_size=0
        )
        print("✅ PostgreSQLへの接続に成功しました！", flush=True)
      except Exception as e:
        print(f"❌ PostgreSQL接続失敗: {e}", flush=True)
    else:
      print("⚠️ DATABASE_URL が設定されていません。", flush=True)

  # ========================================
  # Cogs
  # ========================================

  if os.path.exists("./cogs"):
    for filename in os.listdir("./cogs"):
      if not filename.endswith(".py"):
        continue

      if filename.startswith("_"):
        continue

      cog_name = f"cogs.{filename[:-3]}"

      if cog_name in bot.extensions:
        continue

      try:
        await bot.load_extension(cog_name)
        print(f"✅ Cog読み込み成功: {cog_name}", flush=True)
      except Exception as e:
        print(f"❌ Cog読み込み失敗: {cog_name}: {e}", flush=True)

  # ========================================
  # Slash Commands
  # ========================================

  try:
    synced = await bot.tree.sync()
    print(f"🌟 スラッシュコマンド同期成功 ({len(synced)}個)", flush=True)
  except Exception as e:
    print(f"❌ スラッシュコマンド同期失敗: {e}", flush=True)


# ========================================
# Main
# ========================================

if __name__ == "__main__":
  print("--- プログラムを開始します ---", flush=True)

  # Flask
  flask_thread = threading.Thread(target=run_flask, daemon=True)
  flask_thread.start()

  print("Flaskサーバーを別スレッドで起動しました。", flush=True)

  # Discord Token
  token = os.environ.get("DISCORD_TOKEN")

  if not token:
    print("❌ DISCORD_TOKEN が設定されていません！", flush=True)
  else:
    print(f"DISCORD_TOKENを取得しました (文字数: {len(token)})", flush=True)
    try:
      bot.run(token)
    except Exception as e:
      print(f"❌ Bot起動エラー: {e}", flush=True)
