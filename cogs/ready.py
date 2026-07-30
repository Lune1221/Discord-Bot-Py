import discord
from discord.ext import tasks, commands
from datetime import datetime

class ReadyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduled_message_loop.start()

    def cog_unload(self):
        self.scheduled_message_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} でログインしました！[span_5](start_span)[span_5](end_span)")
        
        # ステータス設定
        guild_count = len(self.bot.guilds)
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"{guild_count} 個のサーバーで稼働")
        await self.bot.change_presence(activity=activity)

        # スラッシュコマンドのグローバル同期
        try:
            await self.bot.tree.sync()
            print("✨ スラッシュコマンド登録完了[span_6](start_span)[span_6](end_span)")
        except Exception as e:
            print(f"コマンド登録エラー: {e}[span_7](start_span)[span_7](end_span)")

    # 1分ごとの予約メッセージ送信ループ
    @tasks.loop(minutes=1)
    async def scheduled_message_loop(self):
        if not self.bot.pool:
            return
        
        try:
            async with self.bot.pool.acquire() as conn:
                res = await conn.fetch(
                    'SELECT * FROM scheduled_messages WHERE send_at <= $1', 
                    datetime.now()
                )
                for row in res:
                    channel = self.bot.get_channel(int(row['channel_id']))
                    if not channel:
                        try:
                            channel = await self.bot.fetch_channel(int(row['channel_id']))
                        except:
                            pass
                    
                    if channel:
                        await channel.send(row['message_content'])
                    
                    await conn.execute('DELETE FROM scheduled_messages WHERE id = $1', row['id'])
        except Exception as e:
            print(f"予約メッセージエラー: {e}[span_8](start_span)[span_8](end_span)")

async def setup(bot):
    await bot.add_cog(ReadyCog(bot))
