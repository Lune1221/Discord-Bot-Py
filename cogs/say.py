import discord
from discord import app_commands
from discord.ext import commands

class SayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="say",
        description="指定したチャンネルにメッセージを送信させます【管理者専用】"
    )
    @app_commands.describe(
        channel="メッセージを送信するテキストチャンネルを指定してください",
        text="Embedに表示させたい本文を入力してください",
        color="Embedの色（例: #3498db などの16進数カラーコード。省略時は青）"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def say(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        text: str,
        color: str = "#3498db"
    ):
        await interaction.response.defer(ephemeral=True)

        try:
            # 16進数カラーコードを整数に変換
            clean_color = color.lstrip('#')
            color_int = int(clean_color, 16)

            embed = discord.Embed(
                description=text,
                color=color_int
            )
            embed.timestamp = discord.utils.utcnow()

            # 指定されたチャンネルにEmbedを送信[span_0](start_span)[span_0](end_span)
            await channel.send(embed=embed)

            # 実行した本人に成功を通知[span_1](start_span)[span_1](end_span)
            await interaction.editReply(
                content=f"✅ {channel.mention} にメッセージを送信しました！"
            )
        except Exception as error:
            print(error)
            await interaction.editReply(
                content="❌ メッセージの送信に失敗しました（カラーコードの形式が間違っているか、権限が不足しています）。"
            )

async def setup(bot):
    await bot.add_cog(SayCog(bot))
