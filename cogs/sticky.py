from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands


class Sticky(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  sticky_group = app_commands.Group(
      name="sticky",
      description=(
          "指定したチャンネルにスティッキーメッセージ（固定埋め込み）を設定・解除します"
      ),
  )

  @sticky_group.command(
      name="set", description="スティッキーメッセージを設定します"
  )
  @app_commands.describe(
      title="埋め込みのタイトル",
      description="埋め込みの説明文",
      channel="送信先のチャンネル（省略した場合は現在のチャンネル）",
  )
  @app_commands.checks.has_permissions(manage_messages=True)
  async def sticky_set(
      self,
      interaction: discord.Interaction,
      title: str,
      description: str,
      channel: discord.TextChannel = None,
  ):
    await interaction.response.defer()
    target_channel = channel or interaction.channel
    channel_id = str(target_channel.id)
    pool = self.bot.pool

    await pool.execute("""
            CREATE TABLE IF NOT EXISTS sticky_messages (
                channel_id VARCHAR(32) PRIMARY KEY,
                message_id VARCHAR(32),
                title TEXT,
                description TEXT
            )
        """)

    res = await pool.fetchrow(
        "SELECT message_id FROM sticky_messages WHERE channel_id = $1",
        channel_id,
    )
    if res and res["message_id"]:
      try:
        old_msg = await target_channel.fetch_message(int(res["message_id"]))
        if old_msg:
          await old_msg.delete()
      except Exception:
        pass

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.from_str("#3498db"),
    )
    embed.timestamp = datetime.now()

    sent_message = await target_channel.send(embed=embed)

    await pool.execute(
        """
            INSERT INTO sticky_messages (channel_id, message_id, title, description)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (channel_id) 
            DO UPDATE SET message_id = $2, title = $3, description = $4
        """,
        channel_id,
        str(sent_message.id),
        title,
        description,
    )

    await interaction.followup.send(
        f"✨ {target_channel.mention} にスティッキーメッセージを設定しました！"
    )

  @sticky_group.command(
      name="remove",
      description="指定したチャンネルのスティッキーメッセージを解除します",
  )
  @app_commands.describe(
      channel="解除するチャンネル（省略した場合は現在のチャンネル）"
  )
  @app_commands.checks.has_permissions(manage_messages=True)
  async def sticky_remove(
      self, interaction: discord.Interaction, channel: discord.TextChannel = None
  ):
    await interaction.response.defer()
    target_channel = channel or interaction.channel
    channel_id = str(target_channel.id)
    pool = self.bot.pool

    res = await pool.fetchrow(
        "SELECT message_id FROM sticky_messages WHERE channel_id = $1",
        channel_id,
    )

    if res:
      if res["message_id"]:
        try:
          old_msg = await target_channel.fetch_message(int(res["message_id"]))
          if old_msg:
            await old_msg.delete()
        except Exception:
          pass
      await pool.execute(
          "DELETE FROM sticky_messages WHERE channel_id = $1", channel_id
      )
      await interaction.followup.send(
          f"🗑️ {target_channel.mention} のスティッキーメッセージを解除しました。"
      )
    else:
      await interaction.followup.send(
          f"⚠️ {target_channel.mention} にはスティッキーメッセージが設定されていません。"
      )


async def setup(bot):
  await bot.add_cog(Sticky(bot))
