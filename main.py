import asyncio
import os
import threading
import asyncpg
from discord.ext import commands
import discord
from dotenv import load_dotenv
from flask import Flask

# 環境変数の読み込み
load_dotenv()

# Webサーバーの設定 (Renderなどの24時間稼働対策)
app = Flask(__name__)


@app.route("/")
def home():
  return "Botは24時間稼働中です！"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# PostgreSQLのデータベース初期化
async def init_database(pool):
  async with pool.acquire() as connection:
    await connection.execute("""
            CREATE TABLE IF NOT EXISTS message_counts (user_id TEXT, guild_id TEXT, count INTEGER DEFAULT 0, PRIMARY KEY (user_id, guild_id));
            CREATE TABLE IF NOT EXISTS omikuji_cooldowns (user_id TEXT, guild_id TEXT, last_date TEXT, PRIMARY KEY (user_id, guild_id));
            CREATE TABLE IF NOT EXISTS guild_settings (guild_id TEXT PRIMARY KEY, level_channel_id TEXT);
            CREATE TABLE IF NOT EXISTS sticky_messages (channel_id VARCHAR(32) PRIMARY KEY, message_id VARCHAR(32), title TEXT, description TEXT);
            CREATE TABLE IF NOT EXISTS scheduled_messages (id SERIAL PRIMARY KEY, guild_id TEXT, channel_id TEXT, author_id TEXT, message_content TEXT, send_at TIMESTAMP);
            CREATE TABLE IF NOT EXISTS intro_channel_settings (id SERIAL PRIMARY KEY, guild_id TEXT, source_channel_id TEXT, keyword TEXT DEFAULT '名前：');
            CREATE TABLE IF NOT EXISTS antiraid_settings (guild_id TEXT PRIMARY KEY, enabled BOOLEAN DEFAULT FALSE);
        """)


# インテントの設定
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  print(f"ログインしました: {bot.user}")


async def main():
  # Webサーバーを別スレッドでバックグラウンド起動
  threading.Thread(target=run_web, daemon=True).start()

  # PostgreSQLのプールを作成し、データベースを初期化
  database_url = os.environ.get("DATABASE_URL")
  pool = await asyncpg.create_pool(database_url)
  await init_database(pool)

  # ボットからデータベースプールを参照できるようにする
  bot.pool = pool

  # cogs フォルダ内のファイルをすべて読み込む
  if os.path.exists("./cogs"):
    for filename in os.listdir("./cogs"):
      if filename.endswith(".py"):
        cog_name = f"cogs.{filename[:-3]}"
        await bot.load_extension(cog_name)
        print(f"読み込みました: {cog_name}")

  async with bot:
    # 🟢 ご提示いただいたサーバーID（1464160132765319305）に即時同期します
    TEST_GUILD_ID = discord.Object(id=1464160132765319305)

    print("指定サーバーへコマンドを即時同期中...")
    bot.tree.copy_global_to(guild=TEST_GUILD_ID)
    await bot.tree.sync(guild=TEST_GUILD_ID)
    print("同期が完了しました！")

    # ボットの起動
    token = os.environ.get("DISCORD_TOKEN")
    await bot.start(token)


if __name__ == "__main__":
  asyncio.run(main())
