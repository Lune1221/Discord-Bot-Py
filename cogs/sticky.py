import asyncio
import discord
from discord import app_commands
from discord.ext import commands


class Sticky(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.locks = {}  # チャンネルごとの同時実行を防ぐロック

  def get_lock(self, channel_id):
    if channel_id not in self.locks:
      self.locks[channel_id] = asyncio.Lock()
    return self.locks[channel_id]

  sticky_group = app_commands.Group(
      name="sticky", description="チャンネルに固定メッセージを設定します"
  )

  @sticky_group.command(
      name="set", description="このチャンネルに固定メッセージを設定します"
  )
  @app_commands.describe(title="タイトル", description="説明文・本文")
  @app_commands.checks.has_permissions(manage_messages=True)
  async def sticky_set(
      self, interaction: discord.Interaction, title: str, description: str
  ):
    await interaction.response.defer(ephemeral=True)
    channel_id = str(interaction.channel_id)
    pool = self.bot.pool

    lock = self.get_lock(channel_id)
    async with lock:
      # 既に設定されている古いメッセージがあれば削除
      row = await pool.fetchrow(
          "SELECT message_id FROM sticky_messages WHERE channel_id = $1",
          channel_id,
      )
      if row and row["message_id"]:
        try:
          old_msg = await interaction.channel.fetch_message(
              int(row["message_id"])
          )
          await old_msg.delete()
        except Exception:
          pass

      # 新しい固定メッセージを送信
      embed = discord.Embed(
          title=title, description=description, color=discord.Color.blue()
      )
      sent_msg = await interaction.channel.send(embed=embed)

      # データベースに保存
      await pool.execute(
          """
                INSERT INTO sticky_messages (channel_id, message_id, title, description)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (channel_id) 
                DO UPDATE SET message_id = $2, title = $3, description = $4
            """,
          channel_id,
          str(sent_msg.id),
          title,
          description,
      )

    await interaction.followup.send(
        "📌 このチャンネルに固定メッセージを設定しました！", ephemeral=True
    )

  @sticky_group.command(
      name="remove", description="このチャンネルの固定メッセージを解除します"
  )
  @app_commands.checks.has_permissions(manage_messages=True)
  async def sticky_remove(self, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel_id = str(interaction.channel_id)
    pool = self.bot.pool

    lock = self.get_lock(channel_id)
    async with lock:
      row = await pool.fetchrow(
          "SELECT message_id FROM sticky_messages WHERE channel_id = $1",
          channel_id,
      )
      if row and row["message_id"]:
        try:
          old_msg = await interaction.channel.fetch_message(
              int(row["message_id"])
          )
          await old_msg.delete()
        except Exception:
          pass

      await pool.execute(
          "DELETE FROM sticky_messages WHERE channel_id = $1", channel_id
      )

    await interaction.followup.send(
        "🗑️ 固定メッセージを解除しました。", ephemeral=True
    )

  @commands.Cog.listener()
  async def on_message(self, message: discord.Message):
    if message.author.bot or not message.guild:
      return

    channel_id = str(message.channel.id)
    pool = self.bot.pool

    # チャンネルごとにロックをかけて同時に処理されないようにする
    lock = self.get_lock(channel_id)
    async with lock:
      row = await pool.fetchrow(
          "SELECT message_id, title, description FROM sticky_messages WHERE"
          " channel_id = $1",
          channel_id,
      )
      if not row:
        return

      # 古い固定メッセージを削除
      old_message_id = row["message_id"]
      if old_message_id:
        try:
          old_msg = await message.channel.fetch_message(int(old_message_id))
          await old_msg.delete()
        except Exception:
          pass

      # 新しい固定メッセージを送信
      embed = discord.Embed(
          title=row["title"],
          description=row["description"],
          color=discord.Color.blue(),
      )
      new_msg = await message.channel.send(embed=embed)

      # データベースのメッセージIDを更新
      await pool.execute(
          "UPDATE sticky_messages SET message_id = $1 WHERE channel_id = $2",
          str(new_msg.id),
          channel_id,
      )


async def setup(bot):
  await bot.add_cog(Sticky(bot))
