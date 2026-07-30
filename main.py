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
    
    def log_message(self, format, *args):
        pass

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# 別スレッドでWebサーバーを常時起動
threading.Thread(target=run_web_server, daemon=True).start()


# --- 2. データベース（PostgreSQL）の初期化処理 ---
async def init_database(pool):
    async with pool.acquire() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS message_counts (
                user_id TEXT, 
                guild_id TEXT, 
                count INTEGER DEFAULT 0, 
                PRIMARY KEY (user_id, guild_id)
            );
            CREATE TABLE IF NOT EXISTS omikuji_cooldowns (
                user_id TEXT, 
                guild_id TEXT, 
                last_date TEXT, 
                PRIMARY KEY (user_id, guild_id)
            );
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id TEXT PRIMARY KEY, 
                level_channel_id TEXT
            );
            CREATE TABLE IF NOT EXISTS sticky_messages (
                channel_id VARCHAR(32) PRIMARY KEY, 
                message_id VARCHAR(32), 
                title TEXT, 
                description TEXT
            );
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id SERIAL PRIMARY KEY, 
                guild_id TEXT, 
                channel_id TEXT, 
                author_id TEXT, 
                message_content TEXT, 
                send_at TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS intro_channel_settings (
                id SERIAL PRIMARY KEY, 
                guild_id TEXT, 
                source_channel_id TEXT, 
                keyword TEXT DEFAULT '名前：'
            );
            CREATE TABLE IF NOT EXISTS antiraid_settings (
                guild_id TEXT PRIMARY KEY, 
                enabled BOOLEAN DEFAULT FALSE
            );
        """)
    print("🗄️ データベースのテーブルを確認・初期化しました。")


# --- 3. Discordボットのメインクラス ---
class MyBot(commands.Bot):
    def __init__(self):
        # JS版と同等のインテントを設定
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        intents.message_content = True
        intents.guild_members = True
        intents.guild_voice_states = True

        super().__init__(command_prefix="!", intents=intents)
        self.pool = None

    async def setup_hook(self):
        # PostgreSQL接続プールを作成 (Renderの DATABASE_URL を使用)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # SSL接続のオプションが必要な場合は ssl="require" などを指定
            self.pool = await asyncpg.create_pool(dsn=database_url, ssl="require")
            await init_database(self.pool)
        else:
            print("⚠️ 警告: DATABASE_URL が設定されていません。")

        # cogsフォルダ内の拡張機能を自動読み込み
        if os.path.exists("./cogs"):
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py"):
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"📁 Cog読み込み完了: {filename}")

        # スラッシュコマンドの同期
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
