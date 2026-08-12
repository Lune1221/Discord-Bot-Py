import discord
from discord import app_commands
from discord.ext import commands


# ボタンのビュー（永続的、またはBot起動中有効）
class RoleButtonView(discord.ui.View):

  def __init__(self, role_id: int):
    super().__init__(timeout=None)
    self.role_id = role_id

    # 動的にボタンを生成（カスタムIDにロールIDを埋め込む）
    self.add_item(RoleToggleButton(role_id))


class RoleToggleButton(discord.ui.Button):

  def __init__(self, role_id: int):
    super().__init__(
        style=discord.ButtonStyle.primary,
        label="ロールを受け取る / 外す",
        custom_id=f"role_panel_{role_id}",
    )
    self.role_id = role_id

  async def callback(self, interaction: discord.Interaction):
    guild = interaction.guild
    member = interaction.user

    if not guild:
      return

    role = guild.get_role(self.role_id)
    if not role:
      await interaction.response.send_message(
          "❌ 対象のロールが見つかりませんでした（削除された可能性があります）。",
          ephemeral=True,
      )
      return

    # 権限チェック（ボットにロール管理権限があるか）
    if guild.me.top_role <= role:
      await interaction.response.send_message(
          "❌ ボットの権限不足によりロールを付与できません。ボットのロールを対象ロールより上に配置してください。",
          ephemeral=True,
      )
      return

    try:
      if role in member.roles:
        await member.remove_roles(role)
        await interaction.response.send_message(
            f"🔄 ロール **{role.name}** を外しました。", ephemeral=True
        )
      else:
        await member.add_roles(role)
        await interaction.response.send_message(
            f"✅ ロール **{role.name}** を付与しました！", ephemeral=True
        )
    except Exception as e:
      await interaction.response.send_message(
          f"❌ エラーが発生しました: {e}", ephemeral=True
      )


class RolePanel(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  panel_group = app_commands.Group(
      name="rolepanel", description="ロールパネルを管理します"
  )

  @panel_group.command(
      name="set", description="ボタン式のロール付与パネルを設置します"
  )
  @app_commands.describe(
      channel="パネルを送信するチャンネル",
      role="付与・剥奪するロール",
      title="パネルのタイトル（埋め込み用）",
      description="パネルの説明文（埋め込み用）",
  )
  @app_commands.checks.has_permissions(administrator=True)
  async def rolepanel_set(
      self,
      interaction: discord.Interaction,
      channel: discord.TextChannel,
      role: discord.Role,
      title: str = "ロールパネル",
      description: "下のボタンを押してロールを取得・解除してください。",
  ):
    if not interaction.guild:
      return

    # ボットがそのロールを付与できる権限があるかチェック
    if interaction.guild.me.top_role <= role:
      await interaction.response.send_message(
          "❌ ボットの役職が指定したロールよりも下にあるため、このロールを管理できません。",
          ephemeral=True,
      )
      return

    # パネル用Embedの作成
    embed = discord.Embed(
        title=title, description=description, color=discord.Color.blue()
    )
    embed.set_footer(text=f"対象ロール: {role.name}")

    # ボタンViewの作成
    view = RoleButtonView(role.id)

    try:
      # 指定チャンネルにパネルを送信
      await channel.send(embed=embed, view=view)
      await interaction.response.send_message(
          f"✨ {channel.mention} にロールパネルを設置しました！", ephemeral=True
      )
    except Exception as e:
      await interaction.response.send_message(
          f"❌ パネルの送信に失敗しました: {e}", ephemeral=True
      )


async def setup(bot):
  await bot.add_cog(RolePanel(bot))
