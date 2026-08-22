from datetime import datetime, timedelta, timezone
import discord
from discord import app_commands
from discord.ext import commands


class MessagePurge(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(
      name="purge",
      description="指定した期間のメッセージをサーバー内全チャンネルから一括削除します",
  )
  @app_commands.describe(
      period="削除する期間を選択してください",
      target_user="（任意）Discordメンバーとして選択する場合",
      target_query=(
          "（任意）ユーザーが選べない場合、ユーザー名やユーザーID(数字)を入力"
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

    guild = interaction.guild
    if not guild:
      await interaction.followup.send(
          "❌ サーバー内で実行してください。", ephemeral=True
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
        f"🧹 サーバー内の全チャンネルから過去 `{period_name}` のメッセージをスキャン・削除中...",
        ephemeral=True,
    )

    total_deleted = 0
    total_failed = 0
    scanned_channels = 0

    # サーバー内のすべてのテキストチャンネルを巡回
    for channel in guild.text_channels:
      # ボットがそのチャンネルのメッセージ履歴を読めない、または消せない場合はスキップ
      permissions = channel.permissions_for(guild.me)
      if not (permissions.read_message_history and permissions.manage_messages):
        continue

      scanned_channels += 1

      try:
        async for message in channel.history(limit=None, after=time_limit):
          author = message.author

          # 絞り込み判定
          if target_user and author.id != target_user.id:
            continue

          if target_query:
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
            total_deleted += 1
          except Exception:
            total_failed += 1
      except Exception:
        # チャンネルの読み込み等でエラーが出た場合はスキップして次へ
        continue

    # ログ表示用の説明文作成
    filter_info = ""
    if target_user:
      filter_info = f"（対象メンバー: {target_user.mention}）"
    elif target_query:
      filter_info = f"（検索クエリ: `{target_query}`）"

    await interaction.followup.send(
        f"✅ サーバー全体の全チャンネル一括削除が完了しました！\n"
        f"・対象期間: 過去の `{period_name}` {filter_info}\n"
        f"・スキャンしたチャンネル数: `{scanned_channels}個`\n"
        f"・削除成功: `{total_deleted}件`\n"
        f"・削除失敗: `{total_failed}件`",
        ephemeral=True,
    )


async def setup(bot: commands.Bot):
  await bot.add_cog(MessagePurge(bot))
