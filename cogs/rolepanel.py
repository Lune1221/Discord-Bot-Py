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

        # ========================================
        # まずInteractionを即座にACK
        # ========================================

        try:
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

            await interaction.followup.send(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )

            return

        # ========================================
        # Member取得
        # ========================================

        member = interaction.guild.get_member(
            interaction.user.id
        )

        if member is None:

            try:
                member = await interaction.guild.fetch_member(
                    interaction.user.id
                )
            except discord.HTTPException:

                await interaction.followup.send(
                    "❌ ユーザー情報を取得できませんでした。",
                    ephemeral=True
                )

                return

        # ========================================
        # ロール取得
        # ========================================

        role = interaction.guild.get_role(
            self.role_id
        )

        if role is None:

            await interaction.followup.send(
                "❌ このロールは存在しません。",
                ephemeral=True
            )

            return

        # ========================================
        # Bot取得
        # ========================================

        bot_member = interaction.guild.me

        if bot_member is None:

            await interaction.followup.send(
                "❌ Bot情報を取得できませんでした。",
                ephemeral=True
            )

            return

        # ========================================
        # @everyone
        # ========================================

        if role.is_default():

            await interaction.followup.send(
                "❌ @everyone ロールは操作できません。",
                ephemeral=True
            )

            return

        # ========================================
        # 管理ロール・Botより上のロール確認
        # ========================================

        if role >= bot_member.top_role:

            await interaction.followup.send(
                "❌ このロールはBotが操作できません。\n"
                "Botのロールを対象ロールより上に移動してください。",
                ephemeral=True
            )

            return

        # ========================================
        # ロール操作
        # ========================================

        try:

            # ----------------------------------------
            # 持っている → 解除
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

            await interaction.followup.send(
                "❌ Botにロールを操作する権限がありません。\n"
                "Botのロールが対象ロールより上にあることを確認してください。",
                ephemeral=True
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

            except discord.HTTPException as followup_error:

                print(
                    f"❌ エラー通知にも失敗しました: {followup_error}",
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

            except discord.HTTPException as followup_error:

                print(
                    f"❌ エラー通知にも失敗しました: {followup_error}",
                    flush=True
                )


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
        # ロール取得
        # ========================================

        role = interaction.guild.get_role(
            self.role_id
        )

        if role is None:

            await interaction.response.send_message(
                "❌ このロールは存在しません。",
                ephemeral=True
            )

            return

        # ========================================
        # Bot取得
        # ========================================

        bot_member = interaction.guild.me

        if bot_member is None:

            await interaction.response.send_message(
                "❌ Bot情報を取得できませんでした。",
                ephemeral=True
            )

            return

        # ========================================
        # Botが操作できるロールか確認
        # ========================================

        if role >= bot_member.top_role:

            await interaction.response.send_message(
                "❌ このロールはBotが操作できません。\n"
                "Botのロールを対象ロールより上に移動してください。",
                ephemeral=True
            )

            return

        # ========================================
        # ユーザー
        # ========================================

        member = interaction.user

        # ========================================
        # ロール付与 / 解除
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

                await interaction.response.send_message(
                    f"🔴 **{role.name}** を解除しました。",
                    ephemeral=True
                )

            # ----------------------------------------
            # 持っていない → 付与
            # ----------------------------------------

            else:

                await member.add_roles(
                    role,
                    reason="ロールパネルから取得"
                )

                await interaction.response.send_message(
                    f"🟢 **{role.name}** を取得しました。",
                    ephemeral=True
                )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ Botにロールを操作する権限がありません。",
                ephemeral=True
            )

        except discord.HTTPException as e:

            print(
                f"Discord APIエラー: {e}",
                flush=True
            )

            await interaction.response.send_message(
                "❌ Discord APIでエラーが発生しました。",
                ephemeral=True
            )

        except Exception as e:

            print(
                f"ロール操作エラー: {e}",
                flush=True
            )

            await interaction.response.send_message(
                "❌ ロール操作中にエラーが発生しました。",
                ephemeral=True
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

            emoji = ROLE_EMOJIS[index]

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

        # ========================================
        # 保存済みパネル復元
        # ========================================

        await self.restore_panels()

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

            guild = self.bot.get_guild(
                row["guild_id"]
            )

            if guild is None:
                continue

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

            # 全ロールが消えている場合
            if not roles:

                await self.bot.pool.execute(
                    """
                    DELETE FROM role_panels
                    WHERE id = $1
                    """,
                    row["id"]
                )

                deleted += 1

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

        bot_member = interaction.guild.me

        if bot_member is None:

            await interaction.response.send_message(
                "❌ Bot情報を取得できませんでした。",
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
            "🟢 ボタンを押す → ロール取得\n"
            "🔴 もう一度押す → ロール解除\n\n"
        )

        for role in roles:

            description += (
                f"・{role.mention}\n"
            )

        embed = discord.Embed(
            title="🎭 ロールパネル",
            description=description,
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="ボタンを押すことでロールを取得・解除できます。"
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
        # パネル送信
        # ========================================

        message = await interaction.channel.send(
            embed=embed,
            view=view
        )

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
                    interaction.guild.id,
                    interaction.channel.id,
                    message.id,
                    role_ids
                )

                # message_idを指定して永続View登録
                self.bot.add_view(
                    view,
                    message_id=message.id
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
        description="このチャンネルのロールパネルをDBから削除します"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def rolepanel_delete(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )

            return

        if not hasattr(self.bot, "pool"):

            await interaction.response.send_message(
                "❌ PostgreSQLに接続されていません。",
                ephemeral=True
            )

            return

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
            f"🗑️ このチャンネルのパネル情報を削除しました。\n"
            f"`{result}`",
            ephemeral=True
        )

    # ========================================
    # エラーハンドリング
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

        if not interaction.response.is_done():

            await interaction.response.send_message(
                message,
                ephemeral=True
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
