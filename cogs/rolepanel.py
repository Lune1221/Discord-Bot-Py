import discord
from discord.ext import commands
from discord import app_commands


# ========================================
# 絵文字
# ========================================

ROLE_EMOJIS = [
    "📢",
    "🎮",
    "🎉"
]


# ========================================
# Role Button
# ========================================

class RoleButton(discord.ui.Button):

    def __init__(
        self,
        role_id: int,
        label: str,
        emoji: str
    ):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f"rolepanel:{role_id}"
        )

        self.role_id = role_id

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        """
        ロールボタンが押されたときの処理。

        重要:
        Interactionは最初に1回だけACKする。
        ここでは defer() を使い、その後は必ず followup.send() を使う。
        """

        # ========================================
        # Interactionを最初にACK
        # ========================================

        try:
            if not interaction.response.is_done():
                await interaction.response.defer(
                    ephemeral=True
                )
        except discord.HTTPException as e:
            print(
                f"❌ Interaction defer エラー: {e}",
                flush=True
            )
            return

        # ========================================
        # サーバー確認
        # ========================================

        if interaction.guild is None:

            try:
                await interaction.followup.send(
                    "❌ サーバー内で使用してください。",
                    ephemeral=True
                )
            except Exception as e:
                print(
                    f"❌ Followup送信エラー: {e}",
                    flush=True
                )

            return

        guild = interaction.guild

        # ========================================
        # ユーザー取得
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
                f"❌ ユーザー取得エラー: {e}",
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
        # ロール取得
        # ========================================

        role = guild.get_role(
            self.role_id
        )

        if role is None:

            try:
                await interaction.followup.send(
                    "❌ このロールは存在しません。",
                    ephemeral=True
                )
            except Exception:
                pass

            return

        # ========================================
        # Bot取得
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
        # Botが操作できるロールか確認
        # ========================================

        if role >= bot_member.top_role:

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
        # ロール操作
        # ========================================

        try:

            # ----------------------------------------
            # 既に持っている → 解除
            # ----------------------------------------

            if role in member.roles:

                await member.remove_roles(
                    role,
                    reason="ロールパネルから解除"
                )

                await interaction.followup.send(
                    f"🔴 **{role.name}** を解除しました。",
                    ephemeral=True
                )

            # ----------------------------------------
            # 持っていない → 取得
            # ----------------------------------------

            else:

                await member.add_roles(
                    role,
                    reason="ロールパネルから取得"
                )

                await interaction.followup.send(
                    f"🟢 **{role.name}** を取得しました。",
                    ephemeral=True
                )

        # ========================================
        # 権限エラー
        # ========================================

        except discord.Forbidden:

            print(
                f"❌ ロール操作権限エラー: "
                f"guild={guild.id}, "
                f"user={member.id}, "
                f"role={role.id}",
                flush=True
            )

            try:
                await interaction.followup.send(
                    "❌ Botにロールを操作する権限がありません。\n"
                    "Botのロールが対象ロールより上にあることを確認してください。",
                    ephemeral=True
                )
            except Exception as e:
                print(
                    f"❌ エラー通知にも失敗しました: {e}",
                    flush=True
                )

        # ========================================
        # Discord APIエラー
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
            except Exception as followup_error:
                print(
                    f"❌ エラー通知にも失敗しました: "
                    f"{followup_error}",
                    flush=True
                )

        # ========================================
        # その他のエラー
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
            except Exception as followup_error:
                print(
                    f"❌ エラー通知にも失敗しました: "
                    f"{followup_error}",
                    flush=True
                )


# ========================================
# Role Panel View
# ========================================

class RolePanelView(discord.ui.View):

    def __init__(
        self,
        roles: list[tuple[int, str]]
    ):

        # 永続View
        super().__init__(
            timeout=None
        )

        for index, (role_id, role_name) in enumerate(roles):

            # 絵文字の数を超えないようにする
            if index < len(ROLE_EMOJIS):
                emoji = ROLE_EMOJIS[index]
            else:
                emoji = "🏷️"

            self.add_item(
                RoleButton(
                    role_id=role_id,
                    label=role_name,
                    emoji=emoji
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

        # PostgreSQLがない場合
        if not hasattr(self.bot, "pool"):

            print(
                "⚠️ rolepanel: PostgreSQLが利用できないため、"
                "パネル復元をスキップします。",
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
        # 保存済みパネル復元
        # ========================================

        try:

            await self.restore_panels()

        except Exception as e:

            print(
                f"❌ ロールパネル復元エラー: {e}",
                flush=True
            )

    # ========================================
    # DBからパネル復元
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

            # ========================================
            # Guild取得
            # ========================================

            guild = self.bot.get_guild(
                row["guild_id"]
            )

            if guild is None:
                continue

            # ========================================
            # Channel取得
            # ========================================

            channel = guild.get_channel(
                row["channel_id"]
            )

            if channel is None:
                continue

            # ========================================
            # ロール取得
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
            # 全ロールが消えている場合
            # ========================================

            if not roles:

                try:

                    await self.bot.pool.execute(
                        """
                        DELETE FROM role_panels
                        WHERE id = $1
                        """,
                        row["id"]
                    )

                    deleted += 1

                except Exception as e:

                    print(
                        f"❌ パネルDB削除エラー: {e}",
                        flush=True
                    )

                continue

            # ========================================
            # View復元
            # ========================================

            try:

                view = RolePanelView(
                    roles
                )

                self.bot.add_view(
                    view,
                    message_id=row["message_id"]
                )

                restored += 1

            except Exception as e:

                print(
                    f"❌ パネル復元失敗 "
                    f"(message_id={row['message_id']}): {e}",
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
        # サーバー確認
        # ========================================

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )

            return

        guild = interaction.guild

        # ========================================
        # ロール一覧
        # ========================================

        roles = [
            role1
        ]

        if role2 is not None:
            roles.append(role2)

        if role3 is not None:
            roles.append(role3)

        # ========================================
        # 重複チェック
        # ========================================

        role_ids = [
            role.id
            for role in roles
        ]

        if len(role_ids) != len(set(role_ids)):

            await interaction.response.send_message(
                "❌ 同じロールを複数指定することはできません。",
                ephemeral=True
            )

            return

        # ========================================
        # Botの最高位ロール
        # ========================================

        bot_member = guild.me

        if bot_member is None:

            await interaction.response.send_message(
                "❌ Bot情報を取得できませんでした。",
                ephemeral=True
            )

            return

        # ========================================
        # @everyoneチェック
        # ========================================

        if any(role.is_default() for role in roles):

            await interaction.response.send_message(
                "❌ @everyone ロールは指定できません。",
                ephemeral=True
            )

            return

        # ========================================
        # 操作できないロール確認
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

            await interaction.response.send_message(
                "❌ 以下のロールはBotが操作できません。\n\n"
                f"{names}\n\n"
                "Botのロールを対象ロールより上に移動してください。",
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
            title=" ロールパネル",
            description=description,
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="ボタンを押すことでロールを取得できます。"
        )

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
            view_roles
        )

        # ========================================
        # チャンネル確認
        # ========================================

        if interaction.channel is None:

            await interaction.response.send_message(
                "❌ チャンネルを取得できませんでした。",
                ephemeral=True
            )

            return

        # ========================================
        # パネル送信
        # ========================================

        try:

            message = await interaction.channel.send(
                embed=embed,
                view=view
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ このチャンネルにメッセージを送信する権限がありません。",
                ephemeral=True
            )

            return

        except discord.HTTPException as e:

            print(
                f"❌ パネル送信エラー: {e}",
                flush=True
            )

            await interaction.response.send_message(
                "❌ ロールパネルの送信に失敗しました。",
                ephemeral=True
            )

            return

        # ========================================
        # DB保存
        # ========================================

        if hasattr(self.bot, "pool"):

            try:

                await self.bot.pool.execute(
                    """
                    INSERT INTO role_panels (
                        guild_id,
                        channel_id,
                        message_id,
                        role_ids
                    )
                    VALUES ($1, $2, $3, $4)
                    """,
                    guild.id,
                    interaction.channel.id,
                    message.id,
                    role_ids
                )

                print(
                    f"✅ ロールパネル保存: "
                    f"message_id={message.id}",
                    flush=True
                )

            except Exception as e:

                print(
                    f"❌ ロールパネルDB保存失敗: {e}",
                    flush=True
                )

        else:

            print(
                "⚠️ PostgreSQLがないため、"
                "パネルはDBに保存されません。",
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

        await interaction.response.send_message(
            "✅ ロールパネルを作成しました。",
            ephemeral=True
        )

    # ========================================
    # /rolepanel_delete
    # ========================================

    @app_commands.command(
        name="rolepanel_delete",
        description="このチャンネルのロールパネル情報をDBから削除します"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def rolepanel_delete(
        self,
        interaction: discord.Interaction
    ):

        # ========================================
        # サーバー確認
        # ========================================

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )

            return

        # ========================================
        # PostgreSQL確認
        # ========================================

        if not hasattr(self.bot, "pool"):

            await interaction.response.send_message(
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
                interaction.guild.id,
                interaction.channel.id
            )

            await interaction.response.send_message(
                "🗑️ このチャンネルのロールパネル情報を削除しました。\n"
                f"`{result}`",
                ephemeral=True
            )

        except Exception as e:

            print(
                f"❌ ロールパネル削除エラー: {e}",
                flush=True
            )

            await interaction.response.send_message(
                "❌ ロールパネル情報の削除に失敗しました。",
                ephemeral=True
            )

    # ========================================
    # /rolepanel エラーハンドリング
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

        # まだInteractionに返答していない場合だけ送信
        if not interaction.response.is_done():

            await interaction.response.send_message(
                message,
                ephemeral=True
            )

        else:

            try:

                await interaction.followup.send(
                    message,
                    ephemeral=True
                )

            except Exception as e:

                print(
                    f"❌ エラーメッセージ送信失敗: {e}",
                    flush=True
                )

    # ========================================
    # /rolepanel_delete エラーハンドリング
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

        if not interaction.response.is_done():

            await interaction.response.send_message(
                message,
                ephemeral=True
            )

        else:

            try:

                await interaction.followup.send(
                    message,
                    ephemeral=True
                )

            except Exception as e:

                print(
                    f"❌ エラーメッセージ送信失敗: {e}",
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
