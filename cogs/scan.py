import discord
from discord import app_commands
from discord.ext import commands


class Scan(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="scan", description="過去のメッセージを遡って集計します【管理者権限】"
  )
  @app_commands.checks.has_permissions(administrator=True)
  async def scan(self, interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send("スキャン中...")
    await interaction.guild.members.fetch()

    guild = interaction.guild
    text_channels = [
        c for c in guild.channels if isinstance(c, discord.TextChannel)
    ]
    local_counts = {}

    for channel in text_channels:
      last_id = None
      while True:
        try:
          messages = [
              m
              async for m in channel.history(
                  limit=100,
                  before=discord.Object(id=last_id) if last_id else None,
              )
          ]
          if not messages:
            break
          for msg in messages:
            if msg.author.bot:
              continue
            local_counts[str(msg.author.id)] = (
                local_counts.get(str(msg.author.id), 0) + 1
            )
          last_id = messages[-1].id
        except Exception as error:
          print(error)
          break

    pool = self.bot.pool
    query_text = """
            INSERT INTO message_counts (user_id, guild_id, count) 
            VALUES ($1, $2, $3) 
            ON CONFLICT(user_id, guild_id) 
            DO UPDATE SET count = message_counts.count + $3
        """
    for u_id, total_count in local_counts.items():
      await pool.execute(query_text, u_id, str(guild.id), total_count)

    await interaction.edit_original_response(content="✅ 同期完了しました！")


async def setup(bot):
  await bot.add_cog(Scan(bot))
