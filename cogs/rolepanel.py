import discord
from discord.ext import commands
from discord import app_commands


# ========================================
# 絵文字
# ========================================

ROLE_EMOJIS = [
    "1️⃣",
    "2️⃣",
    "3️⃣"
]


# ========================================
# Role Button
# ========================================

class RoleButton(discord.ui.Button):

    def __init__(
        self,
        role_id: int,
        label: str,
        emoji: str,
        panel_id: int
    ):
        # ========================================
        # custom_idをパネルごとに一意にする
        # ========================================

        custom_id = (
            f"rolepanel:{panel_id}:{role_id}"
        )

        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            custom_id=custom_id
        )

        self.role_id = role_id
        self.panel_id = panel_id

    # ========================================
    # ボタンCallback
    # ========================================

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        # ========================================
        # Interactionを最優先でACK
        # ========================================

        try:

            if not interaction.response.is_done():

                await interaction.response.defer(
                    ephemeral=True
                )

        except discord.InteractionResponded:

            pass

        except discord.NotFound:

            print(
                "❌ Interactionが期限切れです。",
                flush=True
            )

            return

        except discord.HTTPException as e:

            print(
                f"❌ Interaction defer エラー: {e}",
                flush=True
            )

            return

        # ========================================
        # Guild確認
        # ========================================

        guild = interaction.guild

        if guild is None:

            try:

                await interaction.followup.send(
                    "❌ サーバー内で使用してください。",
                    ephemeral=True
                )

            except Exception:
                pass

            return

        # ========================================
        # Member取得
        # ========================================

        try:

            member = guild.get_member(
                interaction.user.id
            )

            if member is None:

                member = await guild.fetch_member(
                    interaction.user.id
                )

        except discord.HTTPException as e:

            print(
                f"❌ Member取得エラー: {e}",
                flush=True
            )

            try:

                await interaction.followup.send(
                    "❌ ユーザー情報を取得できませんでした。",
                    ephemeral=True
                )

            except Exception:
                pass

            return

        # ========================================
        # Role取得
        # ========================================

        role = guild.get_role(
            self.role_id
        )

        if role is None:

            print(
                f"❌ ロールが存在しません: "
                f"guild={guild.id}, "
                f"role_id={self.role_id}",
                flush=True
            )

            try:

                await interaction.followup.send(
                    "❌ 指定されたロールIDは無効です。\n"
                    "ロールが削除されている可能性があります。",
                    ephemeral=True
                )

            except Exception:
                pass

            return

        # ========================================
        # Bot Member取得
        # ========================================

        bot_member = guild.me

        if bot_member is None:

            try:

                await interaction.followup.send(
                    "❌ Bot情報を取得できませんでした。",
                    ephemeral=True
                )

            except Exception:
                pass

            return

        # ========================================
        # @everyone確認
        # ========================================

        if role.is_default():

            try:

                await interaction.followup.send(
                    "❌ @everyone ロールは操作できません。",
                    ephemeral=True
                )

            except Exception:
                pass

            return

        # ========================================
        # Botのロールより上か確認
        # ========================================

        if role >= bot_member.top_role:

            print(
                f"❌ Botが操作できないロール: "
                f"guild={guild.id}, "
                f"role={role.id}, "
                f"role_position={role.position}, "
                f"bot_position={bot_member.top_role.position}",
                flush=True
            )

            try:

                await interaction.followup.send(
                    "❌ このロールはBotが操作できません。\n"
                    "Botのロールを対象ロールより上に移動してください。",
                    ephemeral=True
                )

            except Exception:
                pass

            return

        # ========================================
        # BotにManage Rolesがあるか
        # ========================================

        if not bot_member.guild_permissions.manage_roles:

            try:

                await interaction.followup.send(
                    "❌ Botに「ロールの管理」権限がありません。",
                    ephemeral=True
                )

            except Exception:
                pass

            return

        # ========================================
        # ロール操作
        # ========================================

        try:

            # ----------------------------------------
            # 既に持っている
            # → 解除
            # ----------------------------------------

            if role in member.roles:

                await member.remove_roles(
                    role,
                    reason="ロールパネルから解除"
                )

                print(
                    f"ロール解除: "
                    f"user={member.id}, "
                    f"role={role.id}",
                    flush=True
                )

                try:

                    await interaction.followup.send(
                        f"**{role.name}** を解除しました。",
                        ephemeral=True
                    )

                except Exception as e:

                    print(
                        f"❌ 結果送信エラー: {e}",
                        flush=True
                    )

            # ----------------------------------------
            # 持っていない
            # → 取得
            # ----------------------------------------

            else:

                await member.add_roles(
                    role,
                    reason="ロールパネルから取得"
                )

                print(
                    f"ロール取得: "
                    f"user={member.id}, "
                    f"role={role.id}",
                    flush=True
                )

                try:

                    await interaction.followup.send(
                        f"**{role.name}** を取得しました。",
                        ephemeral=True
                    )

                except Exception as e:

                    print(
                        f"❌ 結果送信エラー: {e}",
                        flush=True
                    )

        # ========================================
        # 権限エラー
        # ========================================

        except discord.Forbidden:

            print(
                f"❌ ロール操作Forbidden: "
                f"guild={guild.id}, "
                f"user={member.id}, "
                f"role={role.id}",
                flush=True
            )

            try:

                await interaction.followup.send(
                    "❌ Botにロールを操作する権限がありません。\n\n"
                    "Botのロールが対象ロールより上にあるか、"
                    "「ロールの管理」権限があるか確認してください。",
                    ephemeral=True
                )

            except Exception:
                pass

        # ========================================
        # HTTPエラー
        # ========================================

        except discord.HTTPException as e:

            print(
                f"❌ Discord APIエラー: {e}",
                flush=True
            )

            try:

                await interaction.followup.send(
                    "❌ Discord APIでエラーが発生しました。",
                    ephemeral=True
                )

            except Exception:
                pass

        # ========================================
        # その他
        # ========================================

        except Exception as e:

            print(
                f"❌ ロール操作エラー: {e}",
                flush=True
            )

            try:

                await interaction.followup.send(
                    "❌ ロール操作中にエラーが発生しました。",
                    ephemeral=True
                )

            except Exception:
                pass


# ========================================
# Role Panel View
# ========================================

class RolePanelView(discord.ui.View):

    def __init__(
        self,
        roles: list[tuple[int, str]],
        panel_id: int
    ):

        super().__init__(
            timeout=None
        )

        for index, (role_id, role_name) in enumerate(roles):

            if index < len(ROLE_EMOJIS):

                emoji = ROLE_EMOJIS[index]

            else:

                emoji = "🏷️"

            self.add_item(
                RoleButton(
                    role_id=role_id,
                    label=role_name,
                    emoji=emoji,
                    panel_id=panel_id
                )
            )


# ========================================
# Cog
# ========================================

class RolePanel(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):

        self.bot = bot

    # ========================================
    # Cog Load
    # ========================================

    async def cog_load(self):

        if not hasattr(self.bot, "pool"):

            print(
                "⚠️ rolepanel: PostgreSQLが利用できません。",
                flush=True
            )

            return

        # ========================================
        # DBテーブル作成
        # ========================================

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

            print(
                "✅ role_panels テーブルを確認しました。",
                flush=True
            )

        except Exception as e:

            print(
                f"❌ role_panels テーブル作成エラー: {e}",
                flush=True
            )

            return

        # ========================================
        # パネル復元
        # ========================================

        try:

            await self.restore_panels()

        except Exception as e:

            print(
                f"❌ ロールパネル復元エラー: {e}",
                flush=True
            )

    # ========================================
    # DBから復元
    # ========================================

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

            # ========================================
            # Guild
            # ========================================

            guild = self.bot.get_guild(
                row["guild_id"]
            )

            if guild is None:

                continue

            # ========================================
            # Channel
            # ========================================

            channel = guild.get_channel(
                row["channel_id"]
            )

            if channel is None:

                continue

            # ========================================
            # Role
            # ========================================

            roles = []

            for role_id in row["role_ids"]:

                role = guild.get_role(
                    role_id
                )

                if role is not None:

                    roles.append(
                        (
                            role.id,
                            role.name
                        )
                    )

            # ========================================
            # 全ロールが消えている
            # ========================================

            if not roles:

                try:

                    await self.bot.pool.execute(
                        """
                        DELETE FROM role_panels
                        WHERE id = $1
                        """,
                        panel_id
                    )

                    deleted += 1

                except Exception as e:

                    print(
                        f"❌ DB削除エラー: {e}",
                        flush=True
                    )

                continue

            # ========================================
            # View復元
            # ========================================

            try:

                view = RolePanelView(
                    roles=roles,
                    panel_id=panel_id
                )

                self.bot.add_view(
                    view,
                    message_id=row["message_id"]
                )

                restored += 1

                print(
                    f"🔄 パネル復元: "
                    f"panel_id={panel_id}, "
                    f"message_id={row['message_id']}, "
                    f"role_ids={row['role_ids']}",
                    flush=True
                )

            except Exception as e:

                print(
                    f"❌ パネル復元失敗: "
                    f"message_id={row['message_id']}: {e}",
                    flush=True
                )

        print(
            f"🔄 ロールパネル復元: "
            f"{restored}個 / 削除: {deleted}個",
            flush=True
        )

    # ========================================
    # /rolepanel
    # ========================================

    @app_commands.command(
        name="rolepanel",
        description="指定したロールの取得パネルを作成します"
    )
    @app_commands.describe(
        role1="1つ目のロール",
        role2="2つ目のロール",
        role3="3つ目のロール"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def rolepanel(
        self,
        interaction: discord.Interaction,
        role1: discord.Role,
        role2: discord.Role | None = None,
        role3: discord.Role | None = None
    ):

        # ========================================
        # 最初にACK
        # ========================================

        try:

            if not interaction.response.is_done():

                await interaction.response.defer(
                    ephemeral=True
                )

        except discord.HTTPException as e:

            print(
                f"❌ /rolepanel deferエラー: {e}",
                flush=True
            )

            return

        # ========================================
        # Guild
        # ========================================

        guild = interaction.guild

        if guild is None:

            try:

                await interaction.followup.send(
                    "❌ サーバー内で使用してください。",
                    ephemeral=True
                )

            except Exception:
                pass

            return

        # ========================================
        # Role一覧
        # ========================================

        roles = [
            role1
        ]

        if role2 is not None:

            roles.append(role2)

        if role3 is not None:

            roles.append(role3)

        # ========================================
        # 重複
        # ========================================

        role_ids = [
            role.id
            for role in roles
        ]

        if len(role_ids) != len(set(role_ids)):

            await interaction.followup.send(
                "❌ 同じロールを複数指定することはできません。",
                ephemeral=True
            )

            return

        # ========================================
        # Bot
        # ========================================

        bot_member = guild.me

        if bot_member is None:

            await interaction.followup.send(
                "❌ Bot情報を取得できませんでした。",
                ephemeral=True
            )

            return

        # ========================================
        # @everyone
        # ========================================

        if any(role.is_default() for role in roles):

            await interaction.followup.send(
                "❌ @everyone ロールは指定できません。",
                ephemeral=True
            )

            return

        # ========================================
        # Botが操作できるか
        # ========================================

        invalid_roles = [
            role
            for role in roles
            if role >= bot_member.top_role
        ]

        if invalid_roles:

            names = "\n".join(
                f"・{role.mention}"
                for role in invalid_roles
            )

            await interaction.followup.send(
                "❌ 以下のロールはBotが操作できません。\n\n"
                f"{names}\n\n"
                "Botのロールを対象ロールより上に移動してください。",
                ephemeral=True
            )

            return

        # ========================================
        # Manage Roles
        # ========================================

        if not bot_member.guild_permissions.manage_roles:

            await interaction.followup.send(
                "❌ Botに「ロールの管理」権限がありません。",
                ephemeral=True
            )

            return

        # ========================================
        # Embed
        # ========================================

        description = (
            "取得したいロールのボタンを押してください。\n\n"
        )

        for role in roles:

            description += (
                f"・{role.mention}\n"
            )

        embed = discord.Embed(
            title="ロールパネル",
            description=description,
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="ボタンを押すことでロールを取得できます。"
        )

        # ========================================
        # DBへ先にパネルIDを確保
        # ========================================

        if not hasattr(self.bot, "pool"):

            await interaction.followup.send(
                "❌ PostgreSQLに接続されていません。",
                ephemeral=True
            )

            return

        # ========================================
        # 仮ID取得
        # ========================================

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
                role_ids
            )

            panel_id = row["id"]

        except Exception as e:

            print(
                f"❌ パネルID作成エラー: {e}",
                flush=True
            )

            await interaction.followup.send(
                "❌ ロールパネル情報の保存に失敗しました。",
                ephemeral=True
            )

            return

        # ========================================
        # View
        # ========================================

        view_roles = [
            (
                role.id,
                role.name
            )
            for role in roles
        ]

        view = RolePanelView(
            roles=view_roles,
            panel_id=panel_id
        )

        # ========================================
        # チャンネル確認
        # ========================================

        channel = interaction.channel

        if channel is None:

            await self.bot.pool.execute(
                """
                DELETE FROM role_panels
                WHERE id = $1
                """,
                panel_id
            )

            await interaction.followup.send(
                "❌ チャンネルを取得できませんでした。",
                ephemeral=True
            )

            return

        # ========================================
        # パネル送信
        # ========================================

        try:

            message = await channel.send(
                embed=embed,
                view=view
            )

        except discord.Forbidden:

            await self.bot.pool.execute(
                """
                DELETE FROM role_panels
                WHERE id = $1
                """,
                panel_id
            )

            await interaction.followup.send(
                "❌ このチャンネルにメッセージを送信する権限がありません。",
                ephemeral=True
            )

            return

        except discord.HTTPException as e:

            print(
                f"❌ パネル送信エラー: {e}",
                flush=True
            )

            await self.bot.pool.execute(
                """
                DELETE FROM role_panels
                WHERE id = $1
                """,
                panel_id
            )

            await interaction.followup.send(
                "❌ ロールパネルの送信に失敗しました。",
                ephemeral=True
            )

            return

        # ========================================
        # Message ID保存
        # ========================================

        try:

            await self.bot.pool.execute(
                """
                UPDATE role_panels
                SET message_id = $1
                WHERE id = $2
                """,
                message.id,
                panel_id
            )

            print(
                f"✅ ロールパネル保存: "
                f"message_id={message.id}, "
                f"role_ids={role_ids}",
                flush=True
            )

        except Exception as e:

            print(
                f"❌ ロールパネルDB更新失敗: {e}",
                flush=True
            )

        # ========================================
        # 永続View登録
        # ========================================

        try:

            self.bot.add_view(
                view,
                message_id=message.id
            )

        except Exception as e:

            print(
                f"❌ View登録エラー: {e}",
                flush=True
            )

        # ========================================
        # 完了
        # ========================================

        try:

            await interaction.followup.send(
                "✅ ロールパネルを作成しました。",
                ephemeral=True
            )

        except Exception as e:

            print(
                f"❌ 完了メッセージ送信エラー: {e}",
                flush=True
            )

    # ========================================
    # /rolepanel_delete
    # ========================================

    @app_commands.command(
        name="rolepanel_delete",
        description="このチャンネルのロールパネル情報を削除します"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def rolepanel_delete(
        self,
        interaction: discord.Interaction
    ):

        # ========================================
        # 最初にACK
        # ========================================

        try:

            if not interaction.response.is_done():

                await interaction.response.defer(
                    ephemeral=True
                )

        except discord.HTTPException as e:

            print(
                f"❌ /rolepanel_delete deferエラー: {e}",
                flush=True
            )

            return

        # ========================================
        # Guild
        # ========================================

        guild = interaction.guild

        if guild is None:

            await interaction.followup.send(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )

            return

        # ========================================
        # PostgreSQL
        # ========================================

        if not hasattr(self.bot, "pool"):

            await interaction.followup.send(
                "❌ PostgreSQLに接続されていません。",
                ephemeral=True
            )

            return

        # ========================================
        # DB削除
        # ========================================

        try:

            result = await self.bot.pool.execute(
                """
                DELETE FROM role_panels
                WHERE guild_id = $1
                  AND channel_id = $2
                """,
                guild.id,
                interaction.channel.id
            )

            await interaction.followup.send(
                "🗑️ このチャンネルのロールパネル情報を削除しました。\n"
                f"`{result}`",
                ephemeral=True
            )

        except Exception as e:

            print(
                f"❌ ロールパネル削除エラー: {e}",
                flush=True
            )

            await interaction.followup.send(
                "❌ ロールパネル情報の削除に失敗しました。",
                ephemeral=True
            )

    # ========================================
    # /rolepanel エラー
    # ========================================

    @rolepanel.error
    async def rolepanel_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):

        if isinstance(
            error,
            app_commands.errors.MissingPermissions
        ):

            message = (
                "❌ このコマンドは管理者のみ使用できます。"
            )

        else:

            print(
                f"/rolepanel エラー: {error}",
                flush=True
            )

            message = (
                "❌ コマンドの実行中にエラーが発生しました。"
            )

        try:

            if interaction.response.is_done():

                await interaction.followup.send(
                    message,
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )

        except Exception as e:

            print(
                f"❌ /rolepanelエラー通知失敗: {e}",
                flush=True
            )

    # ========================================
    # /rolepanel_delete エラー
    # ========================================

    @rolepanel_delete.error
    async def rolepanel_delete_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):

        if isinstance(
            error,
            app_commands.errors.MissingPermissions
        ):

            message = (
                "❌ このコマンドは管理者のみ使用できます。"
            )

        else:

            print(
                f"/rolepanel_delete エラー: {error}",
                flush=True
            )

            message = (
                "❌ コマンドの実行中にエラーが発生しました。"
            )

        try:

            if interaction.response.is_done():

                await interaction.followup.send(
                    message,
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )

        except Exception as e:

            print(
                f"❌ /rolepanel_deleteエラー通知失敗: {e}",
                flush=True
            )


# ========================================
# Setup
# ========================================

async def setup(
    bot: commands.Bot
):

    await bot.add_cog(
        RolePanel(bot)
    )
