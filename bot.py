import discord
from discord import app_commands
from discord.ui import Modal, TextInput, View
import asyncio
import time

# ============================================================
#  SETTINGS – fill these in!
# ============================================================

BOT_TOKEN     = "TOKEN"
YOUR_USER_ID  = 1513186874649219276

ORDERS_CHANNEL_ID    = 1513254320567615559  # #orders-webhook
COMPLETED_CHANNEL_ID = 1513546398249914560  # #completed-orders
REVIEWS_CHANNEL_ID   = 1513546505896595639  # #reviews
WELCOME_CHANNEL_ID   = 1513194285212897504  # #welcome

# ============================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree   = app_commands.CommandTree(client)

cooldowns = {}
COOLDOWN_SECONDS = 300


# ============================================================
#  WELCOME MESSAGE
# ============================================================
@client.event
async def on_member_join(member):
    channel = client.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="👋 Welcome to RobloxDevStudio!",
            description=f"Hey {member.mention}, welcome to the server!\n\nWe build professional Roblox games for you. Check out our channels to get started!",
            color=0x1a4a9e
        )
        embed.add_field(name="📋 Rules",     value="Read #rules first!",              inline=True)
        embed.add_field(name="🛒 Order",     value="Use /order to order a game!",     inline=True)
        embed.add_field(name="❓ Questions", value="Ask us anything in #general!",    inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="RobloxDevStudio – Professional Roblox Development")
        await channel.send(embed=embed)


# ============================================================
#  ORDER MODAL
# ============================================================
class OrderModal(Modal, title="🎮 Order a Roblox Game"):

    category = TextInput(
        label="Game Category",
        placeholder="e.g. Obby, Tycoon, RPG, Simulator, Horror...",
        required=True,
        max_length=50
    )

    description = TextInput(
        label="Describe your game",
        placeholder="What should the game do? More detail = better result!",
        style=discord.TextStyle.paragraph,
        required=True,
        min_length=30,
        max_length=600
    )

    budget = TextInput(
        label="Budget",
        placeholder="e.g. 500 Robux / 5 Euro Giftcard / Paysafecard",
        required=True,
        max_length=80
    )

    payment = TextInput(
        label="Payment method",
        placeholder="Gamepass, Giftcard or Paysafecard?",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.user
        guild  = interaction.guild

        # Anti-spam check
        spam_words = ["asdf", "test123", "aaaa", "haha", "xd", "fffff"]
        for word in spam_words:
            if word in self.description.value.lower():
                await interaction.response.send_message(
                    "❌ Your order looks like spam. Please be serious!", ephemeral=True
                )
                return

        # Create private ticket channel
        owner = guild.get_member(YOUR_USER_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member:             discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if owner:
            overwrites[owner] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"order-{member.name}", overwrites=overwrites
        )

        # Order embed
        embed = discord.Embed(title="🎮 New Order!", color=0x1a4a9e)
        embed.add_field(name="👤 Customer",    value=member.mention,         inline=True)
        embed.add_field(name="🎯 Category",    value=self.category.value,    inline=True)
        embed.add_field(name="💰 Budget",      value=self.budget.value,      inline=True)
        embed.add_field(name="💳 Payment",     value=self.payment.value,     inline=True)
        embed.add_field(name="📝 Description", value=self.description.value, inline=False)
        embed.set_footer(text="RobloxDevStudio – New Order")

        await channel.send(
            content=f"{member.mention} ticket created! {owner.mention if owner else ''} – new order! 🔔",
            embed=embed,
            view=CloseView()
        )

        # Also post in orders channel
        orders_ch = guild.get_channel(ORDERS_CHANNEL_ID)
        if orders_ch:
            await orders_ch.send(embed=embed)

        cooldowns[member.id] = time.time()

        await interaction.response.send_message(
            f"✅ Order submitted! Go here: {channel.mention}", ephemeral=True
        )


# ============================================================
#  CLOSE TICKET BUTTON
# ============================================================
class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != YOUR_USER_ID:
            await interaction.response.send_message("❌ Only the developer can close tickets!", ephemeral=True)
            return
        await interaction.response.send_message("🔒 Closing in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()


# ============================================================
#  REVIEW STARS
# ============================================================
class ReviewView(View):
    def __init__(self, text: str):
        super().__init__(timeout=60)
        self.text = text

    async def post(self, interaction: discord.Interaction, stars: int):
        ch = interaction.guild.get_channel(REVIEWS_CHANNEL_ID)
        if ch:
            embed = discord.Embed(
                title=f"{'⭐' * stars} New Review",
                description=self.text,
                color=0x1a4a9e
            )
            embed.set_author(name=interaction.user.display_name)
            embed.set_footer(text="RobloxDevStudio – Customer Review")
            await ch.send(embed=embed)
        await interaction.response.send_message(f"✅ Thanks for your {'⭐' * stars} review!", ephemeral=True)
        self.stop()

    @discord.ui.button(label="⭐",         style=discord.ButtonStyle.secondary)
    async def s1(self, i, b): await self.post(i, 1)

    @discord.ui.button(label="⭐⭐",       style=discord.ButtonStyle.secondary)
    async def s2(self, i, b): await self.post(i, 2)

    @discord.ui.button(label="⭐⭐⭐",     style=discord.ButtonStyle.secondary)
    async def s3(self, i, b): await self.post(i, 3)

    @discord.ui.button(label="⭐⭐⭐⭐",   style=discord.ButtonStyle.secondary)
    async def s4(self, i, b): await self.post(i, 4)

    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.success)
    async def s5(self, i, b): await self.post(i, 5)


# ============================================================
#  COMMANDS
# ============================================================

@tree.command(name="order", description="Order a Roblox game from RobloxDevStudio")
async def order(interaction: discord.Interaction):
    uid = interaction.user.id
    if uid in cooldowns and time.time() - cooldowns[uid] < COOLDOWN_SECONDS:
        wait = int(COOLDOWN_SECONDS - (time.time() - cooldowns[uid]))
        await interaction.response.send_message(f"⏳ Please wait **{wait}s** before ordering again.", ephemeral=True)
        return
    await interaction.response.send_modal(OrderModal())


@tree.command(name="status", description="Send a status update to a customer (owner only)")
@app_commands.describe(member="The customer", update="Status message")
async def status(interaction: discord.Interaction, member: discord.Member, update: str):
    if interaction.user.id != YOUR_USER_ID:
        await interaction.response.send_message("❌ Owner only!", ephemeral=True)
        return
    try:
        embed = discord.Embed(title="📦 Order Update", description=update, color=0x1a4a9e)
        embed.set_footer(text="RobloxDevStudio")
        await member.send(embed=embed)
        await interaction.response.send_message(f"✅ Update sent to {member.mention}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Could not DM this user.", ephemeral=True)


@tree.command(name="complete", description="Mark an order as completed (owner only)")
@app_commands.describe(member="The customer", game="Game name")
async def complete(interaction: discord.Interaction, member: discord.Member, game: str):
    if interaction.user.id != YOUR_USER_ID:
        await interaction.response.send_message("❌ Owner only!", ephemeral=True)
        return
    ch = interaction.guild.get_channel(COMPLETED_CHANNEL_ID)
    if ch:
        embed = discord.Embed(title="✅ Order Completed!", color=0x1a4a9e)
        embed.add_field(name="👤 Customer", value=member.mention, inline=True)
        embed.add_field(name="🎮 Game",     value=game,           inline=True)
        embed.set_footer(text="RobloxDevStudio")
        await ch.send(embed=embed)
    try:
        await member.send(f"🎉 Your game **{game}** is ready! Please leave a review with `/review` – thank you!")
    except discord.Forbidden:
        pass
    await interaction.response.send_message(f"✅ Marked as completed!", ephemeral=True)


@tree.command(name="review", description="Leave a review for RobloxDevStudio")
@app_commands.describe(text="Your review")
async def review(interaction: discord.Interaction, text: str):
    if len(text) < 10:
        await interaction.response.send_message("❌ Please write at least 10 characters!", ephemeral=True)
        return
    await interaction.response.send_message("⭐ How many stars?", view=ReviewView(text), ephemeral=True)


@tree.command(name="help", description="Show all commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🎮 RobloxDevStudio – Commands", color=0x1a4a9e)
    embed.add_field(name="/order",    value="Order a Roblox game",                     inline=False)
    embed.add_field(name="/review",   value="Leave a review after receiving your game", inline=False)
    embed.add_field(name="/help",     value="Show this message",                        inline=False)
    embed.set_footer(text="RobloxDevStudio – Professional Roblox Development")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ============================================================
#  START
# ============================================================
@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="🎮 robloxdevstudio.pages.dev")
    )
    print(f"✅ Bot online: {client.user}")
    print(f"📋 Commands synced!")


client.run(BOT_TOKEN)