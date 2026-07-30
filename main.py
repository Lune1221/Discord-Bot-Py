import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands
import asyncpg
from dotenv import load_dotenv

# ローカル環境用
load_dotenv()

# --- 1. Renderのポート要件を満たすための簡易Webサーバー ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    
    # ログを大量に出さないようにする設定
    def log_message(self, format, *args):
        pass

def run_web_server():
    # Renderから指定されるポート番号（デフォルトは10000）を取得
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# 別スレッドでWebサーバーを起動しておく
threading.Thread(target=run_web_server, daemon=True).start()


# --- 2. Discordボットのメイン処理 ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        self.pool = None

    async def setup_hook(self):
        if os.path.exists("./cogs"):
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py"):
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"📁 読み込み完了: {filename}")

        await self.tree.sync()
        print("🌐 スラッシュコマンドを同期しました。")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

bot = MyBot()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ エラー: DISCORD_TOKEN が環境変数に設定されていません。")
else:
    bot.run(TOKEN)
