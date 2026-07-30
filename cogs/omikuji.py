import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime
import pytz

omikuji_results = [
    '大吉 ', 
    '中吉 ', '中吉 ', 
    '小吉 ', '小吉 ', 
    '吉 ', '吉 ', '吉 ',
    '凶 ', '凶 '
]

class Omikuji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="omikuji", description="今日のおみくじを引きます（1日1回限定）")
    async def omikuji(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id) if interaction.guild else None
        user_id = str(interaction.user.id)
        
        # 日本時間の今日の日付文字列を取得
        jst = pytz.timezone('Asia/Tokyo')
        today_str = datetime.now(jst).strftime('%Y/%m/%d')

        pool = self.bot.pool
        async with pool.acquire() as conn:
            # 1. 1日1回制限の重複チェック
            cooldown = await conn.fetchrow(
                "SELECT last_date FROM omikuji_cooldowns WHERE user_id = $1 AND guild_id = $2",
                user_id, guild_id
            )

            if cooldown and cooldown['last_date'] == today_str:
                embed_error = discord.Embed(
                    title="❌ おみくじは1日1回まで",
                    description="今日のおみくじは既に引いています！また明日引いてね！",
                    color=0xff4757
                )
                embed_error.timestamp = discord.utils.utcnow()
                await interaction.editReply(embed=embed_error)
                return

            # 2. 運勢をランダムで選択
            fortune = random.choice(omikuji_results)

            # 3. データベースに保存・更新
            await conn.execute("""
                INSERT INTO omikuji_cooldowns (user_id, guild_id, last_date) 
                VALUES ($1, $2, $3) 
                ON CONFLICT (user_id, guild_id) DO UPDATE SET last_date = $3
            """, user_id, guild_id, today_str)

        # 4. 結果の埋め込みを表示
        embed = discord.Embed(
            title="おみくじ結果",
            description=f"<@{user_id}> さんの今日の運勢は...",
            color=0xff4757
        )
        embed.add_field(name="【運勢】", value=f"**{fortune}**")
        embed.timestamp = discord.utils.utcnow()

        await interaction.editReply(embed=embed)

async def setup(bot):
    await bot.add_cog(Omikuji(bot))
