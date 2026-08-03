import asyncio
import os
import threading
import asyncpg
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask

# 環境変数の読み込み
load_dotenv()

# Webサーバーの設定 (Renderなどの24時間稼働対策)
app = Flask(__name__)


@app.route("/")
def home():
  return "Botは24時間稼働中です！", 200


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# PostgreSQLのデータベース初期化（sticky_messagesを削除済み）
async def init_database(pool):
  async with pool.acquire() as connection:
    await connection.execute("""
            CREATE TABLE IF NOT EXISTS message_counts (user_id TEXT, guild_id TEXT, count INTEGER DEFAULT 0, PRIMARY KEY (user_id, guild_id));
            CREATE TABLE IF NOT EXISTS omikuji_cooldowns (user_id TEXT, guild_id TEXT, last_date TEXT, PRIMARY KEY (user_id, guild_id));
            CREATE TABLE IF NOT EXISTS guild_settings (guild_id TEXT PRIMARY KEY, level_channel_id TEXT);
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


class MyBot(commands.Bot):

  async def setup_hook(self):
    # PostgreSQLのプールを作成し、データベースを初期化
    database_url = os.environ.get("DATABASE_URL")
    self.pool = await asyncpg.create_pool(database_url)
    await init_database(self.pool)

    # cogs フォルダ内のファイルをすべて自動読み込み（sticky.pyファイル本体を削除していれば読み込まれません）
    if os.path.exists("./cogs"):
      for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
          cog_name = f"cogs.{filename[:-3]}"
          await self.load_extension(cog_name)
          print(f"読み込みました: {cog_name}")

    # スラッシュコマンドの同期
    try:
      TEST_GUILD_ID = discord.Object(id=1464160132765319305)
      await self.tree.sync(guild=TEST_GUILD_ID)
      print("指定サーバーへのコマンド同期が完了しました！")
    except Exception as e:
      print(f"同期に失敗しました: {e}")


bot = MyBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  print(f"ログインしました: {bot.user}")


async def main():
  # 1. Webサーバー（Flask）を別スレッドでバックグラウンド起動（Render対策）
  threading.Thread(target=run_web, daemon=True).start()

  # 2. ボットの起動
  token = os.environ.get("DISCORD_TOKEN") or os.environ.get(
      "DISCORD_BOT_TOKEN"
  )
  if not token:
    print(
        "❌ エラー: DISCORD_TOKEN（または DISCORD_BOT_TOKEN）が設定されていません。"
    )
    return

  await bot.start(token)


if __name__ == "__main__":
  asyncio.run(main())
