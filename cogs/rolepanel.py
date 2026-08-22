import discord
from discord import app_commands
from discord.ext import commands

# ========================================
# 絵文字
# ========================================

ROLE_EMOJIS = ["1️⃣", "2️⃣", "3️⃣"]


# ========================================
# Role Link Button
# ========================================


class RoleButton(discord.ui.Button):

  def __init__(self, guild_id: int, role_id: int, label: str, emoji: str):
    # サーバーIDとロールIDを結合してstateに含める (例: 1392..._1507...)
    state_value = f"{guild_id}_{role_id}"
    auth_url = (
        f"https://discord-bot-py-4mzn.onrender.com/auth/login?state={state_value}"
    )

    super().__init__(
        label=f"{label} を取得",
        emoji=emoji,
        style=discord.ButtonStyle.link,
        url=auth_url,
    )


# ========================================
# Role Panel View
# ========================================


class RolePanelView(discord.ui.View):

  def __init__(self, guild_id: int, roles: list[tuple[int, str]]):
    super().__init__(timeout=None)  # 永続リンクボタンにするためタイムアウトなし

    for index, (role_id, role_name) in enumerate(roles):
      emoji = ROLE_EMOJIS[index] if index < len(ROLE_EMOJIS) else "🏷️"
      self.add_item(
          RoleButton(
              guild_id=guild_id, role_id=role_id, label=role_name, emoji=emoji
          )
      )


# ========================================
# Cog
# ========================================


class RolePanel(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  async def cog_load(self):
    if not hasattr(self.bot, "pool"):
      print("⚠️ rolepanel: PostgreSQLが利用できません。", flush=True)
      return

    try:
      await self.bot.pool.execute(
          """
                CREATE TABLE IF NOT EXISTS role_panels (
                    id BIGSERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    channel_id BIGINT NOT NULL,
                    message_id BIGINT NOT NULL UNIQUE,
                    role_ids BIGINT[] NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
      )
      print("✅ role_panels テーブルを確認しました。", flush=True)
    except Exception as e:
      print(f"❌ role_panels テーブル作成エラー: {e}", flush=True)
      return

    try:
      await self.restore_panels()
    except Exception as e:
      print(f"❌ ロールパネル復元エラー: {e}", flush=True)

  async def restore_panels(self):
    rows = await self.bot.pool.fetch(
        """
            SELECT
                id,
                guild_id,
                channel_id,
                message_id,
                role_ids
            FROM role_panels
            ORDER BY id
            """
    )

    restored = 0
    deleted = 0

    for row in rows:
      panel_id = row["id"]
      guild = self.bot.get_guild(row["guild_id"])
      if guild is None:
        continue

      channel = guild.get_channel(row["channel_id"])
      if channel is None:
        continue

      roles = []
      for role_id in row["role_ids"]:
        role = guild.get_role(role_id)
        if role is not None:
          roles.append((role.id, role.name))

      if not roles:
        try:
          await self.bot.pool.execute(
              """
                        DELETE FROM role_panels
                        WHERE id = $1
                        """,
              panel_id,
          )
          deleted += 1
        except Exception as e:
          print(f"❌ DB削除エラー: {e}", flush=True)
        continue

      try:
        view = RolePanelView(guild_id=guild.id, roles=roles)
        self.bot.add_view(view, message_id=row["message_id"])
        restored += 1
      except Exception as e:
        print(f"❌ パネル復元失敗: {e}", flush=True)

    print(
        f"🔄 ロールパネル復元: {restored}個 / 削除: {deleted}個", flush=True
    )

  @app_commands.command(
      name="rolepanel",
      description=(
          "外部認証を通ってロールを取得するためのパネルを作成します"
      ),
  )
  @app_commands.describe(
      role1="1つ目のロール", role2="2つ目のロール", role3="3つ目のロール"
  )
  @app_commands.checks.has_permissions(administrator=True)
  async def rolepanel(
      self,
      interaction: discord.Interaction,
      role1: discord.Role,
      role2: discord.Role | None = None,
      role3: discord.Role | None = None,
  ):
    try:
      if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)
    except Exception:
      return

    guild = interaction.guild
    if guild is None:
      await interaction.followup.send(
          "❌ サーバー内で使用してください。", ephemeral=True
      )
      return

    roles = [role1]
    if role2 is not None:
      roles.append(role2)
    if role3 is not None:
      roles.append(role3)

    role_ids = [role.id for role in roles]
    if len(role_ids) != len(set(role_ids)):
      await interaction.followup.send(
          "❌ 同じロールを複数指定することはできません。", ephemeral=True
      )
      return

    bot_member = guild.get_member(self.bot.user.id)
    if bot_member is None:
      try:
        bot_member = await guild.fetch_member(self.bot.user.id)
      except Exception:
        pass

    if bot_member is None:
      await interaction.followup.send(
          "❌ Bot情報を取得できませんでした。", ephemeral=True
      )
      return

    if any(role.is_default() for role in roles):
      await interaction.followup.send(
          "❌ @everyone ロールは指定できません。", ephemeral=True
      )
      return

    bot_top_role = getattr(bot_member, "top_role", None)
    if bot_top_role is None:
      await interaction.followup.send(
          "❌ Botの最高ロールが取得できませんでした。", ephemeral=True
      )
      return

    invalid_roles = [role for role in roles if role >= bot_top_role]
    if invalid_roles:
      names = "\n".join(f"・{role.mention}" for role in invalid_roles)
      await interaction.followup.send(
          "❌ 以下のロールはBotが操作できません。\n\n" f"{names}",
          ephemeral=True,
      )
      return

    if not bot_member.guild_permissions.manage_roles:
      await interaction.followup.send(
          "❌ Botに「ロールの管理」権限がありません。", ephemeral=True
      )
      return

    description = "下のボタンを押して外部認証を完了すると、ロールが取得できます。\n\n"
    for role in roles:
      description += f"・{role.mention}\n"

    embed = discord.Embed(
        title="✨ 外部認証ロールパネル",
        description=description,
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="ボタンを押すとWeb認証ページが開きます。")

    if not hasattr(self.bot, "pool"):
      await interaction.followup.send(
          "❌ PostgreSQLに接続されていません。", ephemeral=True
      )
      return

    try:
      row = await self.bot.pool.fetchrow(
          """
                INSERT INTO role_panels (
                    guild_id,
                    channel_id,
                    message_id,
                    role_ids
                )
                VALUES ($1, $2, 0, $3)
                RETURNING id
                """,
          guild.id,
          interaction.channel.id,
          role_ids,
      )
      panel_id = row["id"]
    except Exception as e:
      print(f"❌ パネルID作成エラー: {e}", flush=True)
      await interaction.followup.send(
          "❌ ロールパネル情報の保存に失敗しました。", ephemeral=True
      )
      return

    view_roles = [(role.id, role.name) for role in roles]
    view = RolePanelView(guild_id=guild.id, roles=view_roles)

    channel = interaction.channel
    try:
      message = await channel.send(embed=embed, view=view)
    except Exception as e:
      await self.bot.pool.execute(
          "DELETE FROM role_panels WHERE id = $1", panel_id
      )
      await interaction.followup.send(
          "❌ ロールパネルの送信に失敗しました。", ephemeral=True
      )
      return

    try:
      await self.bot.pool.execute(
          "UPDATE role_panels SET message_id = $1 WHERE id = $2",
          message.id,
          panel_id,
      )
      self.bot.add_view(view, message_id=message.id)
      await interaction.followup.send(
          "✅ 外部認証ロールパネルを作成しました。", ephemeral=True
      )
    except Exception as e:
      print(f"❌ パネル保存処理エラー: {e}", flush=True)

  @app_commands.command(
      name="rolepanel_delete",
      description="このチャンネルのロールパネル情報を削除します",
  )
  @app_commands.checks.has_permissions(administrator=True)
  async def rolepanel_delete(self, interaction: discord.Interaction):
    try:
      if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)
    except Exception:
      return

    guild = interaction.guild
    if guild is None:
      await interaction.followup.send(
          "❌ サーバー内で使用してください。", ephemeral=True
      )
      return

    if not hasattr(self.bot, "pool"):
      await interaction.followup.send(
          "❌ PostgreSQLに接続されていません。", ephemeral=True
      )
      return

    try:
      await self.bot.pool.execute(
          """
                DELETE FROM role_panels
                WHERE guild_id = $1
                  AND channel_id = $2
                """,
          guild.id,
          interaction.channel.id,
      )
      await interaction.followup.send(
          "🗑️ このチャンネルのロールパネル情報を削除しました。", ephemeral=True
      )
    except Exception as e:
      print(f"❌ ロールパネル削除エラー: {e}", flush=True)
      await interaction.followup.send(
          "❌ ロールパネル情報の削除に失敗しました。", ephemeral=True
      )


async def setup(bot: commands.Bot):
  await bot.load_extension(bot, RolePanel(bot)) # type: ignore
