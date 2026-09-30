import discord
from discord import app_commands
from discord.ext import commands


class Scan(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="scan",
      description="過去のメッセージを遡って集計します【管理者権限】"
  )
  @app_commands.checks.has_permissions(administrator=True)
  async def scan(self, interaction: discord.Interaction):

    await interaction.response.defer()

    await interaction.followup.send(
        "スキャン中..."
    )

    guild = interaction.guild

    if guild is None:
      await interaction.edit_original_response(
          content="❌ サーバー内でのみ使用できます。"
      )
      return

    # =====================================================
    # テキストチャンネル取得
    # =====================================================

    text_channels = [
        channel
        for channel in guild.channels
        if isinstance(channel, discord.TextChannel)
    ]

    # ユーザーごとの今回のスキャン結果
    local_counts = {}

    # =====================================================
    # 過去メッセージを全チャンネルから取得
    # =====================================================

    for channel in text_channels:

      last_id = None

      while True:

        try:

          messages = [
              message
              async for message in channel.history(
                  limit=100,
                  before=(
                      discord.Object(id=last_id)
                      if last_id
                      else None
                  ),
              )
          ]

          if not messages:
            break

          for message in messages:

            # Botのメッセージはカウントしない
            if message.author.bot:
              continue

            user_id = str(
                message.author.id
            )

            local_counts[user_id] = (
                local_counts.get(user_id, 0) + 1
            )

          # 次のページへ
          last_id = messages[-1].id

        except Exception as error:

          print(
              f"スキャンエラー "
              f"(#{channel.name}): {error}"
          )

          break

    # =====================================================
    # PostgreSQLへ反映
    # =====================================================

    pool = getattr(
        self.bot,
        "pool",
        None
    )

    if pool is None:

      await interaction.edit_original_response(
          content="❌ データベースに接続できません。"
      )

      return

    query_text = """
        INSERT INTO message_counts
            (user_id, guild_id, count)
        VALUES
            ($1, $2, $3)
        ON CONFLICT(user_id, guild_id)
        DO UPDATE SET
            count = message_counts.count + $3
    """

    for user_id, total_count in local_counts.items():

      await pool.execute(
          query_text,
          user_id,
          str(guild.id),
          total_count
      )

    # =====================================================
    # 完了
    # =====================================================

    await interaction.edit_original_response(
        content=(
            f"✅ 同期完了しました！\n"
            f"📊 対象チャンネル: {len(text_channels)}\n"
            f"👤 対象ユーザー: {len(local_counts)}"
        )
    )


async def setup(bot):
  await bot.add_cog(
      Scan(bot)
  )
