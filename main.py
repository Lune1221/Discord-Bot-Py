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
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get(
    "REDIRECT_URI",
    "https://discord-bot-py-4mzn.onrender.com/auth/callback",
)

TARGET_GUILD_ID = "1392780216241491968"


@app.route("/")
def home():
  return "Bot is running!"


@app.route("/auth/login")
def auth_login():
  if not CLIENT_ID or not REDIRECT_URI:
    return "Client ID または Redirect URI が設定されていません。", 500

  # パネルから渡された role_id を取得して state に含める
  role_id = request.args.get("role_id", "")

  discord_login_url = (
      f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}"
      f"&response_type=code"
      f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
      f"&scope=guilds+identify"
      f"&state={role_id}"
  )
  return redirect(discord_login_url)


@app.route("/auth/callback")
def auth_callback():
  code = request.args.get("code")
  grant_role_id = request.args.get("state")  # stateからロールIDを受け取る

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

  guilds_response = requests.get(
      "https://discord.com/api/users/@me/guilds", headers=api_headers
  )
  user_guilds = guilds_response.json()

  if isinstance(user_guilds, dict) and "error" in user_guilds:
    return (
        f"サーバー情報の取得に失敗しました: {user_guilds.get('message')}",
        400,
    )

  is_in_target = any(
      str(guild.get("id")) == TARGET_GUILD_ID for guild in user_guilds
  )

  # -----------------------------------------
  # 失敗時のデザイン画面（禁止サーバーにいる場合）
  # -----------------------------------------
  if is_in_target:
    return """
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>認証失敗</title>
            <style>
                body { background-color: #1e1e2e; color: #cdd6f4; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .card { background-color: #313244; padding: 2.5rem; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); text-align: center; max-width: 400px; width: 90%; }
                .icon { font-size: 3rem; margin-bottom: 1rem; }
                h1 { color: #f38ba8; font-size: 1.5rem; margin-bottom: 1rem; }
                p { color: #a6adc8; font-size: 0.95rem; line-height: 1.6; }
            </style>
        </head>
        <body>
            <div class="card">
                <div class="icon">❌</div>
                <h1>認証に失敗しました</h1>
                <p>参加が禁止されている特定のサーバーに加入しているため、ロールを付与できません。</p>
            </div>
        </body>
        </html>
        """

  # -----------------------------------------
  # 成功時：ロールが指定されていれば自動付与
  # -----------------------------------------
  if grant_role_id and grant_role_id.isdigit():
    user_info_response = requests.get(
        "https://discord.com/api/users/@me", headers=api_headers
    )
    user_data = user_info_response.json()
    user_id = user_data.get("id")

    if user_id:
      bot_token = os.environ.get("DISCORD_TOKEN")
      role_headers = {
          "Authorization": f"Bot {bot_token}",
          "Content-Type": "application/json",
      }
      # 付与対象のメインサーバーID（ここでは TARGET_GUILD_ID 以外のメインサーバーIDにする場合は書き換えてください）
      GUILD_ID = "あなたのメインサーバーのID"

      role_url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{user_id}/roles/{grant_role_id}"
      role_res = requests.put(role_url, headers=role_headers)
      if role_res.status_code != 204:
        print(f"ロール付与失敗: {role_res.text}", flush=True)

  # -----------------------------------------
  # 成功時のデザイン画面
  # -----------------------------------------
  return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>認証完了</title>
        <style>
            body { background-color: #1e1e2e; color: #cdd6f4; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background-color: #313244; padding: 2.5rem; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); text-align: center; max-width: 400px; width: 90%; }
            .icon { font-size: 3rem; margin-bottom: 1rem; }
            h1 { color: #a6e3a1; font-size: 1.5rem; margin-bottom: 1rem; }
            p { color: #a6adc8; font-size: 0.95rem; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">✨</div>
            <h1>認証に成功しました！</h1>
            <p>特定サーバーへの加入は確認されませんでした。<br>ロールが正常に付与されましたので、Discordに戻って確認してください。</p>
        </div>
    </body>
    </html>
    """


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


@bot.event
async def on_ready():
  print(f"=== ログイン成功: {bot.user.name} (ID: {bot.user.id}) ===", flush=True)

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

  if os.path.exists("./cogs"):
    for filename in os.listdir("./cogs"):
      if not filename.endswith(".py") or filename.startswith("_"):
        continue
      cog_name = f"cogs.{filename[:-3]}"
      if cog_name not in bot.extensions:
        try:
          await bot.load_extension(cog_name)
          print(f"✅ Cog読み込み成功: {cog_name}", flush=True)
        except Exception as e:
          print(f"❌ Cog読み込み失敗: {cog_name}: {e}", flush=True)

  try:
    synced = await bot.tree.sync()
    print(f"🌟 スラッシュコマンド同期成功 ({len(synced)}個)", flush=True)
  except Exception as e:
    print(f"❌ スラッシュコマンド同期失敗: {e}", flush=True)


def start_discord_bot():
  token = os.environ.get("DISCORD_TOKEN")
  if token:
    try:
      bot.run(token)
    except Exception as e:
      print(f"❌ Bot起動エラー: {e}", flush=True)


threading.Thread(target=start_discord_bot, daemon=True).start()
