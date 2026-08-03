from datetime import datetime, timedelta
import discord
from discord import app_commands
from discord.ext import commands
from zoneinfo import ZoneInfo


class Schedule(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  schedule_group = app_commands.Group(
      name="schedule", description="メッセージの送信予約を行います"
  )

  @schedule_group.command(
      name="set", description="新しいメッセージの送信を予約します（最大1年以内）"
  )
  @app_commands.describe(
      channel="送信先のチャンネル",
      message="送信するメッセージの内容",
      time="送信日時 (例: 2026-07-30 15:00)",
  )
  @app_commands.checks.has_permissions(manage_messages=True)
  async def schedule_set(
      self,
      interaction: discord.Interaction,
      channel: discord.TextChannel,
      message: str,
      time: str,
  ):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id)

    normalized_time_str = time.replace(" ", "T") + "+09:00"
    try:
      target_date = datetime.fromisoformat(normalized_time_str)
    except ValueError:
      await interaction.followup.send(
          "❌ 日時の形式が正しくありません。「`YYYY-MM-DD HH:MM`」の形式で入力してください（例:"
          " `2026-07-30 15:00`）。"
      )
      return

    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    one_year_later = now + timedelta(days=365)

    if target_date <= now:
      await interaction.followup.send(
          "❌ 過去の日時は指定できません。未来の時間を設定してください。"
      )
      return
    if target_date > one_year_later:
      await interaction.followup.send(
          "❌ 予約できるのは現在から1年以内までです。"
      )
      return

    # 🟢 データベース保存用に日本時間のままタイムゾーン情報を外した日時に変換
    target_date_jst = target_date.astimezone(ZoneInfo("Asia/Tokyo")).replace(
        tzinfo=None
    )

    pool = self.bot.pool
    await pool.execute(
        "INSERT INTO scheduled_messages (guild_id, channel_id, author_id,"
        " message_content, send_at) VALUES ($1, $2, $3, $4, $5)",
        guild_id,
        str(channel.id),
        str(interaction.user.id),
        message,
        target_date_jst,
    )

    formatted_time = target_date.strftime("%Y/%m/%d %H:%M:%S")
    await interaction.followup.send(
        f"✨ {channel.mention} へのメッセージ送信を **{formattedTime}** に予約しました！"
    )

  @schedule_group.command(
      name="list", description="現在登録されている予約一覧を表示します"
  )
  @app_commands.checks.has_permissions(manage_messages=True)
  async def schedule_list(self, interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id)
    pool = self.bot.pool

    res = await pool.fetch(
        "SELECT id, channel_id, message_content, send_at FROM"
        " scheduled_messages WHERE guild_id = $1 ORDER BY send_at ASC",
        guild_id,
    )

    if not res:
      await interaction.followup.send(
          "📭 このサーバーに登録されている予約メッセージはありません。"
      )
      return

    list_text = "📋 **現在の予約メッセージ一覧**\n"
    for row in res:
      # 🟢 取得した日時に日本時間のタイムゾーンを付与して正しく表示
      dt = row["send_at"]
      if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("Asia/Tokyo"))
      date_str = dt.strftime("%Y/%m/%d %H:%M:%S")

      content = row["message_content"]
      preview = content[:20] + "..." if len(content) > 20 else content
      list_text += (
          f"• **ID: {row['id']}** | チャンネル: <#{row['channel_id']}> | 予定:"
          f" {date_str}\n  内容: `{preview}`\n"
      )

    await interaction.followup.send(list_text)

  @schedule_group.command(
      name="cancel", description="IDを指定して予約をキャンセルします"
  )
  @app_commands.describe(id="キャンセルする予約のID (listコマンドで確認できます)")
  @app_commands.checks.has_permissions(manage_messages=True)
  async def schedule_cancel(self, interaction: discord.Interaction, id: int):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id)
    pool = self.bot.pool

    res = await pool.fetchrow(
        "DELETE FROM scheduled_messages WHERE id = $1 AND guild_id = $2"
        " RETURNING id",
        id,
        guild_id,
    )

    if not res:
      await interaction.followup.send(
          f"❌ ID `{id}` の予約が見つからないか、このサーバーの予約ではありません。"
      )
      return

    await interaction.followup.send(f"🗑️ ID `{id}` の予約をキャンセルしました。")


async def setup(bot):
  await bot.add_cog(Schedule(bot))
