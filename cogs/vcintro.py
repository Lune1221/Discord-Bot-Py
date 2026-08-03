import discord
from discord import app_commands
from discord.ext import commands


class VcIntro(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  vcintro_group = app_commands.Group(
      name="vcintro", description="VC参加時の自己紹介自動表示の設定を管理します"
  )

  @vcintro_group.command(
      name="set", description="自己紹介チャンネルとの連携設定を追加します"
  )
  @app_commands.describe(
      source="自己紹介が投稿されているテキストチャンネル（例: #自己紹介）",
      keyword="検索するキーワード（例: 名前：、ハンネ：等。省略時は「名前：」）",
  )
  @app_commands.checks.has_permissions(manage_guild=True)
  async def vcintro_set(
      self,
      interaction: discord.Interaction,
      source: discord.TextChannel,
      keyword: str = "名前：",
  ):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id)
    pool = self.bot.pool

    await pool.execute(
        """
            INSERT INTO intro_channel_settings (guild_id, source_channel_id, keyword) 
            VALUES ($1, $2, $3)
        """,
        guild_id,
        str(source.id),
        keyword,
    )

    await interaction.followup.send(
        f"✨ VC自己紹介の設定を追加しました！\n• 読み取り元チャンネル:"
        f" {source.mention}\n• 検索ワード: `{keyword}`\n*(※"
        " 参加したVCのインサイドチャットに自動で送信されます)*"
    )

  @vcintro_group.command(
      name="list", description="現在登録されている自己紹介の設定一覧を表示します"
  )
  @app_commands.checks.has_permissions(manage_guild=True)
  async def vcintro_list(self, interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id)
    pool = self.bot.pool

    res = await pool.fetch(
        "SELECT id, source_channel_id, keyword FROM intro_channel_settings WHERE"
        " guild_id = $1 ORDER BY id ASC",
        guild_id,
    )

    if not res:
      await interaction.followup.send(
          "📭 現在登録されているVC自己紹介の設定はありません。"
      )
      return

    list_text = "📋 **現在のVC自己紹介設定一覧**\n"
    for row in res:
      list_text += (
          f"• **ID: {row['id']}** | 読み取り: <#{row['source_channel_id']}>"
          f" (ワード: `{row['keyword']}`)\n"
      )

    await interaction.followup.send(list_text)

  @vcintro_group.command(
      name="delete", description="IDを指定して設定を削除します"
  )
  @app_commands.describe(id="削除する設定のID (listコマンドで確認できます)")
  @app_commands.checks.has_permissions(manage_guild=True)
  async def vcintro_delete(self, interaction: discord.Interaction, id: int):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id)
    pool = self.bot.pool

    res = await pool.fetchrow(
        "DELETE FROM intro_channel_settings WHERE id = $1 AND guild_id = $2"
        " RETURNING id",
        id,
        guild_id,
    )

    if not res:
      await interaction.followup.send(
          f"❌ ID `{id}` の設定が見つからないか、このサーバーの設定ではありません。"
      )
      return

    await interaction.followup.send(f"🗑️ ID `{id}` の設定を削除しました。")


async def setup(bot):
  await bot.add_cog(VcIntro(bot))
