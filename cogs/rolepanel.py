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
        emoji: str
    ):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f"rolepanel:{role_id}",
        )

        self.role_id = int(role_id)

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        """
        ロールボタン処理

        Interactionは最初に1回だけACKする。
        defer後は interaction.followup を使用する。
        """

        # ========================================
        # Interaction ACK
        # ========================================

        try:
            if not interaction.response.is_done():
                await interaction.response.defer(
                    ephemeral=True
                )
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

        if interaction.guild is None:

            await self._followup(
                interaction,
                "❌ サーバー内で使用してください。"
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

        except discord.NotFound:

            await self._followup(
                interaction,
                "❌ ユーザー情報を取得できませんでした。"
            )

            return

        except discord.HTTPException as e:

            print(
                f"❌ ユーザー取得エラー: {e}",
                flush=True
            )

            await self._followup(
                interaction,
                "❌ ユーザー情報を取得できませんでした。"
            )

            return

        # ========================================
        # ロール取得
        #
        # get_role()だけではなく
        # fetch_role()でDiscord APIから直接取得する
        # ========================================

        role = None

        try:

            # まずキャッシュから取得
            role = guild.get_role(
                self.role_id
            )

            # キャッシュになければAPIから取得
            if role is None:

                role = await guild.fetch_role(
                    self.role_id
                )

        except discord.NotFound:

            print(
                f"❌ ロールが存在しません: "
                f"guild={guild.id}, "
                f"role_id={self.role_id}",
                flush=True
            )

            await self._followup(
                interaction,
                "❌ 指定されたロールIDは無効です。\n"
                "このパネルに保存されているロールが削除されている可能性があります。"
            )

            return

        except discord.HTTPException as e:

            print(
                f"❌ ロール取得APIエラー: "
                f"guild={guild.id}, "
                f"role_id={self.role_id}, "
                f"error={e}",
                flush=True
            )

            await self._followup(
                interaction,
                "❌ Discordからロール情報を取得できませんでした。"
            )

            return

        # ========================================
        # ロール取得確認
        # ========================================

        if role is None:

            await self._followup(
                interaction,
                "❌ ロールを取得できませんでした。"
            )

            return

        # ========================================
        # ロールがこのGuildのものか確認
        # ========================================

        if role.guild.id != guild.id:

            print(
                f"❌ Guild不一致: "
                f"interaction_guild={guild.id}, "
                f"role_guild={role.guild.id}, "
                f"role_id={role.id}",
                flush=True
            )

            await self._followup(
                interaction,
                "❌ このロールは現在のサーバーのロールではありません。"
            )

            return

        # ========================================
        # @everyone
        # ========================================

        if role.is_default():

            await self._followup(
                interaction,
                "❌ @everyone ロールは操作できません。"
            )

            return

        # ========================================
        # Bot取得
        # ========================================

        bot_member = guild.me

        if bot_member is None:

            try:
                bot_member = await guild.fetch_member(
                    self.bot.user.id
                )
            except Exception:
                bot_member = None

        if bot_member is None:

            await self._followup(
                interaction,
                "❌ Bot情報を取得できませんでした。"
            )

            return

        # ========================================
        # Botの最高位ロール確認
        # ========================================

        if role >= bot_member.top_role:

            print(
                f"❌ Botより上位のロール: "
                f"guild={guild.id}, "
                f"role={role.name}, "
                f"role_id={role.id}, "
                f"bot_top_role={bot_member.top_role.name}",
                flush=True
            )

            await self._followup(
                interaction,
                "❌ このロールはBotが操作できません。\n"
                "Botのロールを対象ロールより上に移動してください。"
            )

            return

        # ========================================
        # BotにManage Rolesがあるか
        # ========================================

        if not bot_member.guild_permissions.manage_roles:

            await self._followup(
                interaction,
                "❌ Botに「ロールの管理」権限がありません。"
            )

            return

        # ========================================
        # ロール操作
        # ========================================

        try:

            # ====================================
            # 持っている → 解除
            # ====================================

            if role in member.roles:

                await member.remove_roles(
                    role,
                    reason="ロールパネルから解除"
                )

                print(
                    f" ロール解除成功: "
                    f"user={member.id}, "
                    f"role={role.name} ({role.id})",
                    flush=True
                )

                await self._followup(
                    interaction,
                    f" **{role.name}** を解除しました。"
                )

            # ====================================
            # 持っていない → 取得
            # ====================================

            else:

                await member.add_roles(
                    role,
                    reason="ロールパネルから取得"
                )

                print(
                    f" ロール取得成功: "
                    f"user={member.id}, "
                    f"role={role.name} ({role.id})",
                    flush=True
                )

                await self._followup(
                    interaction,
                    f" **{role.name}** を取得しました。"
                )

        # ========================================
        # 権限エラー
        # ========================================

        except discord.Forbidden:

            print(
                f"❌ ロール操作Forbidden: "
                f"guild={guild.id}, "
                f"user={member.id}, "
                f"role={role.name} ({role.id}), "
                f"bot_top_role={bot_member.top_role.name}",
                flush=True
            )

            await self._followup(
                interaction,
                "❌ Botにロールを操作する権限がありません。\n"
                "Botのロールが対象ロールより上にあることを確認してください。"
            )

        # ========================================
        # Discord APIエラー
        # ========================================

        except discord.HTTPException as e:

            print(
                f"❌ Discord APIロール操作エラー: "
                f"guild={guild.id}, "
                f"user={member.id}, "
                f"role={role.name} ({role.id}), "
                f"error={e}",
                flush=True
            )

            await self._followup(
                interaction,
                "❌ Discord APIでロール操作に失敗しました。"
            )

        # ========================================
        # その他
        # ========================================

        except Exception as e:

            print(
                f"❌ ロール操作エラー: {e}",
                flush=True
            )

            await self._followup(
                interaction,
                "❌ ロール操作中にエラーが発生しました。"
            )

    # ========================================
    # Followup安全送信
    # ========================================

    async def _followup(
        self,
        interaction: discord.Interaction,
        content: str
    ):

        try:

            await interaction.followup.send(
                content,
                ephemeral=True
            )

        except discord.HTTPException as e:

            print(
                f"❌ Followup送信エラー: {e}",
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
                    role_id=int(role_id),
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

        if not hasattr(self.bot, "pool"):

            print(
                "⚠️ rolepanel: PostgreSQLが利用できないため、"
                "パネル復元をスキップします。",
                flush=True
            )

            return

        # ========================================
        # DBテーブル
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
    # パネル復元
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

            guild = self.bot.get_guild(
                int(row["guild_id"])
            )

            if guild is None:
                continue

            channel = guild.get_channel(
                int(row["channel_id"])
            )

            if channel is None:
                continue

            roles = []

            # ========================================
            # 保存されているRole IDを確認
            # ========================================

            for role_id in row["role_ids"]:

                role = guild.get_role(
                    int(role_id)
                )

                if role is not None:

                    roles.append(
                        (
                            role.id,
                            role.name
                        )
                    )

                else:

                    print(
                        f"⚠️ 保存済みロールが存在しません: "
                        f"guild={guild.id}, "
                        f"role_id={role_id}",
                        flush=True
                    )

            # ========================================
            # ロールが1つもない
            # ========================================

            if not roles:

                await self.bot.pool.execute(
                    """
                    DELETE FROM role_panels
                    WHERE id = $1
                    """,
                    row["id"]
                )

                deleted += 1

                print(
                    f"🗑️ 無効なパネルをDBから削除: "
                    f"message_id={row['message_id']}",
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
                    message_id=int(row["message_id"])
                )

                restored += 1

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

        roles = [role1]

        if role2 is not None:
            roles.append(role2)

        if role3 is not None:
            roles.append(role3)

        # ========================================
        # 重複チェック
        # ========================================

        role_ids = [
            int(role.id)
            for role in roles
        ]

        if len(role_ids) != len(set(role_ids)):

            await interaction.response.send_message(
                "❌ 同じロールを複数指定することはできません。",
                ephemeral=True
            )

            return

        # ========================================
        # Bot取得
        # ========================================

        bot_member = guild.me

        if bot_member is None:

            await interaction.response.send_message(
                "❌ Bot情報を取得できませんでした。",
                ephemeral=True
            )

            return

        # ========================================
        # Manage Roles確認
        # ========================================

        if not bot_member.guild_permissions.manage_roles:

            await interaction.response.send_message(
                "❌ Botに「ロールの管理」権限がありません。",
                ephemeral=True
            )

            return

        # ========================================
        # @everyone確認
        # ========================================

        if any(
            role.is_default()
            for role in roles
        ):

            await interaction.response.send_message(
                "❌ @everyone ロールは指定できません。",
                ephemeral=True
            )

            return

        # ========================================
        # Botより上のロール確認
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
            title="ロールパネル",
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
                int(role.id),
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
                    int(guild.id),
                    int(interaction.channel.id),
                    int(message.id),
                    role_ids
                )

                print(
                    f"✅ ロールパネル保存: "
                    f"message_id={message.id}, "
                    f"role_ids={role_ids}",
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
                int(interaction.guild.id),
                int(interaction.channel.id)
            )

            await interaction.response.send_message(
                "🗑️ このチャンネルのロールパネル情報を削除しました。\n"
                f"`{result}`",
                ephemeral=True
            )

            print(
                f"🗑️ ロールパネルDB削除: "
                f"guild={interaction.guild.id}, "
                f"channel={interaction.channel.id}, "
                f"result={result}",
                flush=True
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

            if not interaction.response.is_done():

                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )

            else:

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

            if not interaction.response.is_done():

                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )

            else:

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
