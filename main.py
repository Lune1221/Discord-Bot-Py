import os
import discord
from discord.ext import commands
import asyncpg
from dotenv import load_dotenv

# ローカル環境用：.envファイルから環境変数を読み込む
load_dotenv()

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        self.pool = None

    async def setup_hook(self):
        # データベース接続（必要に応じて設定してください）
        # self.pool = await asyncpg.create_pool(user="...", password="...", database="...", host="...")
        
        # cogsフォルダ内のファイルを自動読み込み
        if os.path.exists("./cogs"):
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py"):
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"📁 読み込み完了: {filename}")

        # スラッシュコマンドの同期
        await self.tree.sync()
        print("🌐 スラッシュコマンドを同期しました。")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

bot = MyBot()

# 環境変数からトークンを取得（変数名は DISCORD_TOKEN としています）
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ エラー: DISCORD_TOKEN が環境変数に設定されていません。")
else:
    bot.run(TOKEN)
