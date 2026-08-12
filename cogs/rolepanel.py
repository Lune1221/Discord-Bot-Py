import discord
from discord.ext import commands
from discord import app_commands


# ========================================
# ロールボタン
# ========================================

class RoleButton(discord.ui.Button):

    def __init__(
        self,
        role: discord.Role,
        emoji: str
    ):
        super().__init__(
            label=role.name,
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f"role_panel:{role.id}"
        )

        self.role_id = role.id

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(self.role_id)

        if role is None:
            await interaction.response.send_message(
                "❌ このロールは存在しません。",
                ephemeral=True
            )
            return

        member = interaction.user

        # Botが操作できるロールか確認
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ このロールはBotが操作できません。\n"
                "Botのロールを対象ロールより上に移動してください。",
                ephemeral=True
            )
            return

        try:

            # 持っている → 解除
            if role in member.roles:

                await member.remove_roles(role)

                await interaction.response.send_message(
                    f"🔴 **{role.name}** を解除しました。",
                    ephemeral=True
                )

            # 持っていない → 付与
            else:

                await member.add_roles(role)

                await interaction.response.send_message(
                    f"🟢 **{role.name}** を取得しました。",
                    ephemeral=True
                )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ Botにロールを操作する権限がありません。",
                ephemeral=True
            )

        except Exception as e:

            print(
                f"ロール操作エラー: {e}",
                flush=True
            )

            await interaction.response.send_message(
                "❌ ロールの操作中にエラーが発生しました。",
                ephemeral=True
            )


# ========================================
# ロールパネル
# ========================================

class RolePanelView(discord.ui.View):

    def __init__(
        self,
        roles: list[discord.Role]
    ):

        super().__init__(timeout=None)

        emojis = ["📢", "🎮", "🎉"]

        for index, role in enumerate(roles):

            self.add_item(
                RoleButton(
                    role=role,
                    emoji=emojis[index]
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
        # ロール一覧を作成
        # ========================================

        roles = [role1]

        if role2 is not None:
            roles.append(role2)

        if role3 is not None:
            roles.append(role3)

        # ========================================
        # 重複チェック
        # ========================================

        if len(roles) != len(set(role.id for role in roles)):

            await interaction.response.send_message(
                "❌ 同じロールを複数指定することはできません。",
                ephemeral=True
            )
            return

        # ========================================
        # Botが操作可能か確認
        # ========================================

        bot_member = interaction.guild.me

        invalid_roles = [
            role
            for role in roles
            if role >= bot_member.top_role
        ]

        if invalid_roles:

            names = ", ".join(
                role.name
                for role in invalid_roles
            )

            await interaction.response.send_message(
                f"❌ 以下のロールはBotが操作できません。\n"
                f"`{names}`\n\n"
                f"Botのロールを対象ロールより上に移動してください。",
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
            description += f"・{role.mention}\n"

        embed = discord.Embed(
            title="🎭 ロールパネル",
            description=description,
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="ボタンを押すことでロールを取得・解除できます。"
        )

        # ========================================
        # パネル送信
        # ========================================

        await interaction.channel.send(
            embed=embed,
            view=RolePanelView(roles)
        )

        await interaction.response.send_message(
            "✅ ロールパネルを作成しました。",
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

            await interaction.response.send_message(
                "❌ このコマンドは管理者のみ使用できます。",
                ephemeral=True
            )

        else:

            print(
                f"/rolepanel エラー: {error}",
                flush=True
            )

            if not interaction.response.is_done():

                await interaction.response.send_message(
                    "❌ コマンドの実行中にエラーが発生しました。",
                    ephemeral=True
                )


# ========================================
# Cog読み込み
# ========================================

async def setup(
    bot: commands.Bot
):
    await bot.add_cog(
        RolePanel(bot)
    )
