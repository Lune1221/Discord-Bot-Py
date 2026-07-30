import discord
from discord import app_commands
from discord.ext import commands

class NukeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="nuke",
        description="現在のチャンネルを初期化（再作成）します【管理者専用】"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def nuke(self, interaction: discord.Interaction):
        # チャンネルが削除されるため、先にインタラクションを応答（非公開）しておく
        await interaction.response.defer(ephemeral=True)
        
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.editReply(content="❌ テキストチャンネルでのみ実行可能です。")

        try:
            # 現在のチャンネルの設定を引き継いでクローン（複製）を作成
            new_channel = await channel.clone(reason=f"Nuked by {interaction.user}")
            
            # 元のチャンネルを削除
            await channel.delete(reason=f"Nuked by {interaction.user}")

            # 埋め込みを作成し、指定されたTenorのGIF直リンクを配置
            embed = discord.Embed(
                title="💥 チャンネルを初期化しました！",
                color=0x3498db
            )
            embed.set_image(url="https://media1.tenor.com/m/VRF-66wvOe4AAAAC/megumin-explosion-megumin-konosuba.gif")
            embed.timestamp = discord.utils.utcnow()

            # 新しく生成されたチャンネルにメッセージを送信
            await new_channel.send(embed=embed)

        except Exception as error:
            print(error)
            try:
                await interaction.editReply(content="❌ チャンネルの初期化に失敗しました（Botの管理者権限やチャンネル管理権限を確認してください）。")
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(NukeCog(bot))
