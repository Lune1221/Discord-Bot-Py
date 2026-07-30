import discord
from discord import app_commands
from discord.ext import commands
import math

class RankingView(discord.ui.View):
    def __init__(self, page: int, max_pages: int, executor_id: str, cog, guild, pool):
        super().__init__(timeout=180)
        self.page = page
        self.max_pages = max_pages
        self.executor_id = executor_id
        self.cog = cog
        self.guild = guild
        self.pool = pool

        # 前へボタン[span_2](start_span)[span_2](end_span)[span_3](start_span)[span_3](end_span)
        prev_button = discord.ui.Button(
            label="前へ ◀",
            style=discord.ButtonStyle.secondary,
            custom_id=f"prev_{page}_{executor_id}",
            disabled=(page == 1)
        )
        prev_button.callback = self.interaction_callback
        self.add_item(prev_button)

        # 次へボタン[span_4](start_span)[span_4](end_span)[span_5](start_span)[span_5](end_span)
        next_button = discord.ui.Button(
            label="▶ 次へ",
            style=discord.ButtonStyle.primary,
            custom_id=f"next_{page}_{executor_id}",
            disabled=(page == max_pages)
        )
        next_button.callback = self.interaction_callback
        self.add_item(next_button)

    async def interaction_callback(self, interaction: discord.Interaction):
        # 本人チェック[span_6](start_span)[span_6](end_span)
        if str(interaction.user.id) != self.executor_id:
            await interaction.response.send_message("❌ 本人しか操作できません。", ephemeral=True)
            return

        custom_id = interaction.data["custom_id"]
        action, page_str, _ = custom_id.split("_")
        current_page = int(page_str)
        new_page = current_page - 1 if action == "prev" else current_page + 1

        await self.cog.update_ranking_message(interaction, self.pool, new_page, self.executor_id)

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ranking",
        description="このサーバーの発言回数ランキングを表示します"
    )
    async def ranking(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild = interaction.guild
        if not guild:
            return

        await guild.members.fetch()[span_7](start_span)[span_7](end_span)[span_8](start_span)[span_8](end_span)
        pool = self.bot.pool
        user_id = str(interaction.user.id)

        page_data = await self.generate_page(guild, 1, user_id, user_id, pool)
        if "error" in page_data:
            return await interaction.editReply(content="データがありません。")[span_9](start_span)[span_9](end_span)[span_10](start_span)[span_10](end_span)

        await interaction.editReply(embeds=page_data["embeds"], view=page_data["view"])

    async def generate_page(self, guild, current_page_id, current_user_id, executor_id, pool):
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT user_id, count FROM message_counts WHERE guild_id = $1 ORDER BY count DESC",
                str(guild.id)
            )[span_11](start_span)[span_11](end_span)[span_12](start_span)[span_12](end_span)

        active_users = []
        my_rank = "圏外"
        my_count = 0
        active_rank = 0

        for row in rows:
            user_id = row['user_id']
            count = row['count']
            active_rank += 1
            active_users.append({"rank": active_rank, "userId": user_id, "count": count})
            if user_id == current_user_id:
                my_rank = f"{active_rank}位"
                my_count = count

        if not active_users:
            return {"error": "なし"}[span_13](start_span)[span_13](end_span)[span_14](start_span)[span_14](end_span)

        max_pages = math.ceil(len(active_users) / 10)
        page = max(1, min(current_page_id, max_pages))
        page_users = active_users[(page - 1) * 10 : page * 10]

        ranking_text = ""
        medals = ['🥇', '🥈', '🥉'][span_15](start_span)[span_15](end_span)[span_16](start_span)[span_16](end_span)

        for u in page_users:
            medal_or_rank = medals[u['rank'] - 1] if (u['rank'] - 1) < len(medals) else f"  {u['rank']}位."
            ranking_text += f"{medal_or_rank} <@{u['userId']}>: **{u['count']}回**\n[span_17](start_span)[span_18](start_span)"[span_17](end_span)[span_18](end_span)

        embed = discord.Embed(
            title=f"🏆 発言回数ランキング ({page} / {max_pages} ページ)",
            description=ranking_text,
            color=0xFFD700
        )
        embed.add_field(name="👤 あなたの現在の順位", value=f"**{my_rank}** ({my_count}回)")[span_19](start_span)[span_19](end_span)[span_20](start_span)[span_20](end_span)
        embed.timestamp = discord.utils.utcnow()

        view = RankingView(page, max_pages, executor_id, self, guild, pool)
        return {"embeds": [embed], "view": view}

    async def update_ranking_message(self, interaction: discord.Interaction, pool, new_page, executor_id):
        await interaction.response.defer()
        guild = interaction.guild
        if not guild:
            return

        page_data = await self.generate_page(guild, new_page, str(interaction.user.id), executor_id, pool)
        if "error" in page_data:
            return await interaction.editReply(content="データがありません。", view=None)

        await interaction.editReply(embeds=page_data["embeds"], view=page_data["view"])

    # 外部のグローバルリスナー等から呼び出される場合の互換用メソッド
    async def execute_button(self, interaction: discord.Interaction, pool, new_page, executor_id):
        await self.update_ranking_message(interaction, pool, new_page, executor_id)

async def setup(bot):
    await bot.add_cog(Ranking(bot))
