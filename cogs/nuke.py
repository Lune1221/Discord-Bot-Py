import discord
from discord import app_commands
from discord.ext import commands

class Nuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="nuke", description="現在のチャンネルを初期化します")
    @app_commands.checks.has_permissions(administrator=True)
    async def nuke(self, interaction: discord.Interaction):
        if not interaction.guild:
            return

        channel = interaction.channel

        try:
            # 現在のチャンネル設定を引き継いでクローン（複製）を作成
            cloned = await channel.clone(
                name=channel.name,
                reason=f"{interaction.user} によってチャンネルが初期化されました"
            )

            # 埋め込みメッセージと爆発GIFを設定
            embed = discord.Embed(
                title="💥 チャンネル初期化 (Nuke)",
                description=f"{interaction.user.mention} によってチャンネルが初期化されました！",
                color=0xff4500
            )
            embed.set_image(url="https://media.giphy.com/media/3ohzdWq8xlkscbDRxC/giphy.gif")
            embed.timestamp = discord.utils.utcnow()

            # 新しいチャンネルに埋め込みを送信
            await cloned.send(embed=embed)

            # 古いチャンネルを削除
            await channel.delete()

        except Exception as error:
            print(f"Nukeコマンドエラー: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ チャンネルの初期化に失敗しました。ボットに「チャンネルの管理」権限があるか確認してください。",
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(Nuke(bot))
