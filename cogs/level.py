import discord
from discord import app_commands
from discord.ext import commands

# グラフの数式（二次関数）に基づいて、そのレベルに必要なメッセージ数を返す関数[span_2](start_span)[span_2](end_span)
def get_required_messages(level):
    return int(10 + (level * level * 2))

# 累計メッセージ数から現在のレベルを逆算する関数[span_3](start_span)[span_3](end_span)
def get_level_info(total_count):
    level = 0
    count = total_count

    while True:
        required = get_required_messages(level)
        if count >= required:
            count -= required
            level += 1
        else:
            return {"level": level, "current": count, "required": required}

class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /level コマンド
    @app_commands.command(name="level", description="指定したユーザーのレベルとメッセージ数を確認します")
    @app_commands.describe(user="ユーザー（空欄なら自分）")
    async def level(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id) if interaction.guild else None
        target_user = user or interaction.user
        user_id = str(target_user.id)

        pool = self.bot.pool
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT count FROM message_counts WHERE user_id = $1 AND guild_id = $2",
                user_id, guild_id
            )
            total_count = row['count'] if row else 0

        info = get_level_info(total_count)
        remaining = info['required'] - info['current']

        embed = discord.Embed(
            color=0x3498db,
            title=f"{targetUser.name} さんのレベル情報"
        )
        embed.add_field(name="現在のレベル", value=str(info['level']), inline=True)
        embed.add_field(name="次のレベルまで", value=f"あと {remaining} メッセージ", inline=False)
        embed.timestamp = discord.utils.utcnow()

        await interaction.editReply(embed=embed)

    # /level-set コマンド（管理者専用）
    @app_commands.command(name="level-set", description="レベリングの通知を送信するチャンネルを設定します【管理者専用】")
    @app_commands.describe(channel="通知を送るテキストチャンネルを指定してください")
    @app_commands.checks.has_permissions(administrator=True)
    async def level_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)

        pool = self.bot.pool
        try:
            async with pool.acquire() as conn:
                # データベースにチャンネルIDを保存（すでに存在する場合は更新）[span_4](start_span)[span_4](end_span)
                await conn.execute(
                    """
                    INSERT INTO guild_settings (guild_id, level_channel_id) 
                    VALUES ($1, $2) 
                    ON CONFLICT (guild_id) 
                    DO UPDATE SET level_channel_id = EXCLUDED.level_channel_id
                    """,
                    guild_id, str(channel.id)
                )

            await interaction.editReply(content=f"✅ レベルアップ通知チャンネルを {channel.mention} に設定しました！")
        except Exception as error:
            print(error)
            await interaction.editReply(content="❌ 設定の保存に失敗しました。")

async def setup(bot):
    await bot.add_cog(LevelCog(bot))
