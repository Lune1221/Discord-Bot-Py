from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands


class RankingView(discord.ui.View):

  def __init__(self, guild, current_user_id, executor_id, pool):
    super().__init__(timeout=180)
    self.guild = guild
    self.current_user_id = current_user_id
    self.executor_id = executor_id
    self.pool = pool
    self.current_page = 1
    self.max_pages = 1
    self.update_buttons()

  async def update_page_data(self):
    res = await self.pool.fetch(
        "SELECT user_id, count FROM message_counts WHERE guild_id = $1 ORDER BY"
        " count DESC",
        str(self.guild.id),
    )
    active_users = []
    my_rank = "圏外"
    my_count = 0
    active_rank = 0

    for row in res:
      user_id = row["user_id"]
      active_rank += 1
      active_users.append(
          {"rank": active_rank, "userId": user_id, "count": row["count"]}
      )
      if user_id == str(self.current_user_id):
        my_rank = f"{active_rank}位"
        my_count = row["count"]

    if not active_users:
      return None

    self.max_pages = max(1, (len(active_users) + 9) // 10)
    self.current_page = max(1, min(self.current_page, self.max_pages))

    page_users = active_users[
        (self.current_page - 1) * 10 : self.current_page * 10
    ]
    ranking_text = ""
    medals = ["🥇", "🥈", "🥉"]

    for u in page_users:
      medal = medals[u["rank"] - 1] if u["rank"] <= 3 else f"  {u['rank']}位."
      ranking_text += f"{medal} <@{u['userId']}>: **{u['count']}回**\n"

    embed = discord.Embed(
        title=(
            f"🏆 発言回数ランキング ({self.current_page} /"
            f" {self.max_pages} ページ)"
        ),
        description=ranking_text,
        color=discord.Color.from_str("#FFD700"),
    )
    embed.add_field(
        name="👤 あなたの現在の順位", value=f"**{my_rank}** ({my_count}回)"
    )
    embed.timestamp = datetime.now()

    self.update_buttons()
    return embed

  def update_buttons(self):
    self.clear_items()

    prev_button = discord.ui.Button(
        label="前へ ◀",
        style=discord.ButtonStyle.secondary,
        disabled=(self.current_page == 1),
    )
    prev_button.callback = self.prev_callback
    self.add_item(prev_button)

    next_button = discord.ui.Button(
        label="▶ 次へ",
        style=discord.ButtonStyle.primary,
        disabled=(self.current_page == self.max_pages),
    )
    next_button.callback = self.next_callback
    self.add_item(next_button)

  async def prev_callback(self, interaction: discord.Interaction):
    if interaction.user.id != self.executor_id:
      await interaction.response.send_message(
          "他の人のランキング操作はできません。", ephemeral=True
      )
      return
    self.current_page -= 1
    embed = await self.update_page_data()
    await interaction.response.edit_message(embed=embed, view=self)

  async def next_callback(self, interaction: discord.Interaction):
    if interaction.user.id != self.executor_id:
      await interaction.response.send_message(
          "他の人のランキング操作はできません。", ephemeral=True
      )
      return
    self.current_page += 1
    embed = await self.update_page_data()
    await interaction.response.edit_message(embed=embed, view=self)


class Ranking(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="ranking", description="このサーバーの発言回数ランキングを表示します"
  )
  async def ranking(self, interaction: discord.Interaction):
    await interaction.response.defer()
    if not interaction.guild:
      await interaction.followup.send(
          "このコマンドはサーバー内でみ使用できます。"
      )
      return

    view = RankingView(
        interaction.guild,
        interaction.user.id,
        interaction.user.id,
        self.bot.pool,
    )
    embed = await view.update_page_data()

    if not embed:
      await interaction.followup.send("データがありません。")
      return

    await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
  await bot.add_cog(Ranking(bot))
