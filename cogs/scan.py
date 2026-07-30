import discord
from discord import app_commands
from discord.ext import commands

class ScanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="scan",
        description="過去のメッセージを遡って集計します【管理者権限】"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def scan(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if not guild:
            return

        await guild.members.fetch()
        await interaction.editReply(content="スキャン中...[span_2](start_span)[span_2](end_span)[span_3](start_span)[span_3](end_span)")

        local_counts = {}

        # サーバー内のすべてのテキストチャンネルを走査
        for channel in guild.text_channels:
            try:
                async for msg in channel.history(limit=None):
                    if msg.author.bot:
                        continue
                    author_id = str(msg.author.id)
                    local_counts[author_id] = local_counts.get(author_id, 0) + 1
            except Exception as error:
                print(f"チャンネル読み込みエラー ({channel.name}): {error}")
                continue

        pool = self.bot.pool
        guild_id = str(guild.id)

        try:
            async with pool.acquire() as conn:
                for user_id, total_count in local_counts.items():
                    await conn.execute(
                        """
                        INSERT INTO message_counts (user_id, guild_id, count) 
                        VALUES ($1, $2, $3) 
                        ON CONFLICT(user_id, guild_id) 
                        DO UPDATE SET count = message_counts.count + $3
                        """,
                        user_id, guild_id, total_count
                    )
            await interaction.editReply(content="✅ 同期完了しました！[span_4](start_span)[span_4](end_span)[span_5](start_span)[span_5](end_span)")
        except Exception as error:
            print(f"DB保存エラー: {error}")
            await interaction.editReply(content="❌ データベースへの保存中にエラーが発生しました。")

async def setup(bot):
    await bot.add_cog(ScanCog(bot))
