import logging
import os
import threading

import asyncpg
import discord
from discord.ext import commands
from flask import Flask


# ========================================
# Flask
# ========================================

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running!"


def run_flask():
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )


# ========================================
# Discord Bot
# ========================================

intents = discord.Intents.default()

intents.message_content = True
intents.voice_states = True
intents.members = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ========================================
# Bot Ready
# ========================================

@bot.event
async def on_ready():

    print(
        f"=== ログイン成功: {bot.user.name} "
        f"(ID: {bot.user.id}) ===",
        flush=True
    )

    # ========================================
    # PostgreSQL
    # ========================================

    if not hasattr(bot, "pool"):

        database_url = os.environ.get(
            "DATABASE_URL"
        )

        if database_url:

            try:

                bot.pool = await asyncpg.create_pool(
                    database_url,
                    min_size=1,
                    max_size=5
                )

                print(
                    "✅ PostgreSQLへの接続に成功しました！",
                    flush=True
                )

            except Exception as e:

                print(
                    f"❌ PostgreSQL接続失敗: {e}",
                    flush=True
                )

        else:

            print(
                "⚠️ DATABASE_URL が設定されていません。",
                flush=True
            )

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

            # 既に読み込まれているCogはスキップ
            if cog_name in bot.extensions:
                continue

            try:

                await bot.load_extension(
                    cog_name
                )

                print(
                    f"✅ Cog読み込み成功: {cog_name}",
                    flush=True
                )

            except Exception as e:

                print(
                    f"❌ Cog読み込み失敗: "
                    f"{cog_name}: {e}",
                    flush=True
                )

    # ========================================
    # Slash Commands
    # ========================================

    try:

        synced = await bot.tree.sync()

        print(
            f"🌟 スラッシュコマンド同期成功 "
            f"({len(synced)}個)",
            flush=True
        )

    except Exception as e:

        print(
            f"❌ スラッシュコマンド同期失敗: {e}",
            flush=True
        )


# ========================================
# Main
# ========================================

if __name__ == "__main__":

    print(
        "--- プログラムを開始します ---",
        flush=True
    )

    # Flask
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    print(
        "Flaskサーバーを別スレッドで起動しました。",
        flush=True
    )

    # Discord Token
    token = os.environ.get(
        "DISCORD_TOKEN"
    )

    if not token:

        print(
            "❌ DISCORD_TOKEN が設定されていません！",
            flush=True
        )

    else:

        print(
            f"DISCORD_TOKENを取得しました "
            f"(文字数: {len(token)})",
            flush=True
        )

        try:

            bot.run(token)

        except Exception as e:

            print(
                f"❌ Bot起動エラー: {e}",
                flush=True
            )
