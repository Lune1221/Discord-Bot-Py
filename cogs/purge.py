from datetime import datetime, timedelta, timezone
import discord
from discord import app_commands
from discord.ext import commands


class MessagePurge(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(
      name="purge",
      description=(
          "指定した期間のメッセージを一括削除します（ユーザー名・ID指定可）"
      ),
  )
  @app_commands.describe(
      period="削除する期間を選択してください",
      target_user="（任意）Discordメンバーとして選択する場合",
      target_query=(
          "（任意）垢消しなどで選べない場合、ユーザー名やユーザーID(数字)を入力"
      ),
  )
  @app_commands.choices(
      period=[
          app_commands.Choice(name="24時間以内", value="24h"),
          app_commands.Choice(name="3日間以内", value="3d"),
          app_commands.Choice(name="1週間以内", value="1w"),
          app_commands.Choice(name="1ヶ月以内", value="1m"),
          app_commands.Choice(name="1年間以内", value="1y"),
      ]
  )
  @app_commands.checks.has_permissions(manage_messages=True)
  async def purge(
      self,
      interaction: discord.Interaction,
      period: str,
      target_user: discord.Member | None = None,
      target_query: str | None = None,
  ):
    await interaction.response.defer(ephemeral=True)

    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
      await interaction.followup.send(
          "❌ テキストチャンネルでのみ使用可能です。", ephemeral=True
      )
      return

    # 期間に応じたtimedeltaを計算
    now = datetime.now(timezone.utc)
    if period == "24h":
      time_limit = now - timedelta(hours=24)
      period_name = "24時間以内"
    elif period == "3d":
      time_limit = now - timedelta(days=3)
      period_name = "3日間以内"
    elif period == "1w":
      time_limit = now - timedelta(weeks=1)
      period_name = "1週間以内"
    elif period == "1m":
      time_limit = now - timedelta(days=30)
      period_name = "1ヶ月以内"
    elif period == "1y":
      time_limit = now - timedelta(days=365)
      period_name = "1年間以内"
    else:
      await interaction.followup.send(
          "❌ 無効な期間が選択されました。", ephemeral=True
      )
      return

    await interaction.followup.send(
        f"🧹 過去 `{period_name}` のメッセージをスキャン中...", ephemeral=True
    )

    deleted_count = 0
    failed_count = 0

    try:
      async for message in channel.history(limit=None, after=time_limit):
        author = message.author

        # 絞り込み判定
        if target_user and author.id != target_user.id:
          continue

        if target_query:
          # 入力された文字列が「ユーザーID(完全一致)」「ユーザー名(部分一致)」「表示名(部分一致)」のどれかにヒットするか
          query = target_query.strip()
          is_id_match = query.isdigit() and author.id == int(query)
          is_name_match = (
              query.lower() in author.name.lower()
              or query in author.display_name
          )
          if not (is_id_match or is_name_match):
            continue

        try:
          await message.delete()
          deleted_count += 1
        except Exception:
          failed_count += 1
    except Exception as e:
      await interaction.followup.send(
          f"❌ メッセージの取得中にエラーが発生しました: {e}", ephemeral=True
      )
      return

    # ログ表示用の説明文作成
    filter_info = ""
    if target_user:
      filter_info = f"（対象メンバー: {target_user.mention}）"
    elif target_query:
      filter_info = f"（検索クエリ: `{target_query}`）"

    await interaction.followup.send(
        f"✅ 削除が完了しました！\n"
        f"・期間: 過去の `{period_name}` {filter_info}\n"
        f"・削除成功: `{deleted_count}件`\n"
        f"・削除失敗: `{failed_count}件`",
        ephemeral=True,
    )


async def setup(bot: commands.Bot):
  await bot.add_cog(MessagePurge(bot))
