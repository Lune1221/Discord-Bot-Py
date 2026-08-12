import logging
import os
import threading
import asyncpg
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
intents.voice_states = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(
        f"=== ログイン成功: {bot.user.name} (ID: {bot.user.id}) ===",
        flush=True
    )

    # ========================================
    # PostgreSQL
    # ========================================

    if not hasattr(bot, "pool"):
        database_url = os.environ.get("DATABASE_URL")

        if database_url:
            try:
                bot.pool = await asyncpg.create_pool(database_url)

                print(
                    "✅ データベース（PostgreSQL）への接続に成功しました！",
                    flush=True
                )

            except Exception as e:
                print(
                    f"❌ 【データベース接続失敗】 エラー詳細: {e}",
                    flush=True
                )

        else:
            print(
                "⚠️ 【警告】DATABASE_URL が環境変数に設定されていません。",
                flush=True
            )

    # ========================================
    # Cogs読み込み
    # ========================================

    if os.path.exists("./cogs"):

        for filename in os.listdir("./cogs"):

            if not filename.endswith(".py"):
                continue

            if filename.startswith("_"):
                continue

            cog_name = f"cogs.{filename[:-3]}"

            # 既に読み込まれている場合はスキップ
            if cog_name in bot.extensions:
                continue

            try:
                await bot.load_extension(cog_name)

                print(
                    f"読み込み成功: {cog_name}",
                    flush=True
                )

            except Exception as e:
                print(
                    f"【読み込み失敗】 {cog_name}: {e}",
                    flush=True
                )

    # ========================================
    # スラッシュコマンド同期
    # ========================================

    try:
        synced = await bot.tree.sync()

        print(
            f"🌟 スラッシュコマンドの同期に成功しました"
            f"（合計 {len(synced)} 個）",
            flush=True
        )

    except Exception as e:
        print(
            f"【同期失敗】エラー詳細: {e}",
            flush=True
        )


# --- 3. メイン起動処理 ---
if __name__ == "__main__":

    print(
        "--- プログラムを開始します ---",
        flush=True
    )

    # Flaskを別スレッドでバックグラウンド起動
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    print(
        "Flaskサーバーを別スレッドで起動しました。",
        flush=True
    )

    # トークンの確認と起動
    token = os.environ.get("DISCORD_TOKEN")

    if not token:

        print(
            "【エラー】DISCORD_TOKEN が環境変数に設定されていません！",
            flush=True
        )

    else:

        print(
            f"DISCORD_TOKEN を取得しました"
            f"（文字数: {len(token)}）。"
            f"ボットを起動します...",
            flush=True
        )

        try:
            bot.run(token)

        except Exception as e:

            print(
                f"ボットの起動中にエラーが発生しました: {e}",
                flush=True
            )
