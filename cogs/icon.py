import discord
from discord import app_commands
from discord.ext import commands


class Avatar(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="icon", description="指定したユーザーのアイコンを表示します"
  )
  @app_commands.describe(user="アイコンを表示したいユーザーを選択してください")
  async def avatar(
      self, interaction: discord.Interaction, user: discord.Member = None
  ):
    # ユーザーが指定されなかった場合は、コマンドを実行した本人を対象にする
    if user is None:
      user = interaction.user

    # ユーザーのアイコンのURLを取得（サイズは綺麗に見える1024px、拡張子は自動対応）
    avatar_url = user.display_avatar.url

    # 埋め込み（Embed）を作成
    embed = discord.Embed(
        title=f"{user.display_name} のアイコン", color=discord.Color.blurple()
    )
    embed.set_image(url=avatar_url)

    # `ephemeral=True` にすることで、使用した本人にしか見えないようにする
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
  await bot.add_cog(Avatar(bot))
