import discord
from discord import app_commands
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="このBotで使えるコマンドの一覧メニューを表示します"
    )
    async def help(self, interaction: discord.Interaction):
        await interaction.response.defer()

        embed = discord.Embed(
            title="📖 コマンドメニュー",
            description="このBotで使えるコマンドの一覧です。",
            color=0x2ecc71
        )
        embed.add_field(name=" /count [ユーザー]", value="指定した人の発言回数を見ることが出来ます。", inline=False)[span_11](start_span)[span_11](end_span)
        embed.add_field(name=" /ranking", value="発言回数が多い人順にランキングを表示します。", inline=False)[span_12](start_span)[span_12](end_span)
        embed.add_field(name=" /omikuji", value="今日のおみくじを引きます。(1日1回まで)", inline=False)[span_13](start_span)[span_13](end_span)
        embed.add_field(name=" /level", value="自分のレベルを見ることができます。", inline=False)[span_14](start_span)[span_14](end_span)
        embed.add_field(name=" /level-set", value="【管理者専用】レベル通知のチャンネルを設定します。", inline=False)[span_15](start_span)[span_15](end_span)
        embed.add_field(name=" /say", value="【管理者専用】チャンネルを指定してそのチャンネルにBotを経由してメッセージを送信します。", inline=False)[span_16](start_span)[span_16](end_span)
        embed.add_field(name=" /scan", value="【管理者専用】過去ログをすべて読み込み、サーバーと同期します。", inline=False)[span_17](start_span)[span_17](end_span)
        embed.add_field(name=" /schedule", value="【管理者専用】チャンネルと日時を指定して指定された所にメッセージを送信します。", inline=False)[span_18](start_span)[span_18](end_span)
        
        embed.set_footer(text="※クラウドに安全に自動記録されています。")[span_19](start_span)[span_19](end_span)
        embed.timestamp = discord.utils.utcnow()

        await interaction.editReply(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
