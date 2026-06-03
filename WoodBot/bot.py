
import random
import discord
from discord.ext import tasks
import sqlite3
from discord.ext import commands
import io
import datetime

import os


from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "WoodBot is running!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()



TOKEN = os.getenv("TOKEN")

OWNER_ID = 1361735588029399193

SELLER_ROLE = "seller"
SCAMMER_ROLE = "scammer"

VIP_ROLE = "👑 VIP"

CUSTOMER_ROLE = "🌲 Customer"
REGULAR_ROLE = "🪵 Regular"
LUMBERJACK_ROLE = "⚒️ Lumberjack"
ELITE_ROLE = "💠 Elite Customer"
LEGENDARY_ROLE = "🐉 Legendary Buyer"

LOG_CHANNEL_NAME = "📜・order-logs"
VOUCH_CHANNEL = "⭐・vouches"
ORDER_CATEGORY = "🪵 Wood Orders"

db = sqlite3.connect("woodbot.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    orders INTEGER DEFAULT 0,
    spent INTEGER DEFAULT 0,
    vouches INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS invites (
    user_id INTEGER PRIMARY KEY,
    invites INTEGER DEFAULT 0
)
""")

db.commit()

WOOD_PRICES = {
    "oak": 90000,
    "elm": 90000,
    "walnut": 135000,
    "cherry": 90000,
    "pine": 140000,
    "fir": 140000,
    "lava": 90000,
    "birch": 130000,
    "zombie": 170000,
    "gold": 170000,
    "koa": 150000,
    "frost": 200000,
    "cavecrawler": 115000,
    "snowglow": 200000,
    "palm": 220000,
    "phantom": 350000,
    "blue spruce": 275000,
    "spook": 400000,
    "sinister": 400000
}

WOOD_ALIASES = {
    "oak": "oak",
    "elm": "elm",
    "walnut": "walnut",
    "wal": "walnut",
    "cherry": "cherry",
    "pine": "pine",
    "fir": "fir",
    "lava": "lava",
    "birch": "birch",
    "zombie": "zombie",
    "zomb": "zombie",
    "gold": "gold",
    "koa": "koa",
    "frost": "frost",
    "cavecrawler": "cavecrawler",
    "cave": "cavecrawler",
    "blue neon": "cavecrawler",
    "bn": "cavecrawler",
    "snowglow": "snowglow",
    "snow": "snowglow",
    "palm": "palm",
    "phantom": "phantom",
    "blue spruce": "blue spruce",
    "spruce": "blue spruce",
    "bs": "blue spruce",
    "spook": "spook",
    "sinister": "sinister",
    "sin": "sinister"
}

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def is_owner(interaction):
    return interaction.user.id == OWNER_ID

def get_user_data(user_id):

    cursor.execute(
        "SELECT orders, spent, vouches FROM users WHERE user_id = ?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data is None:

        cursor.execute(
            "INSERT INTO users (user_id) VALUES (?)",
            (user_id,)
        )

        db.commit()

        return (0, 0, 0)

    return data

def add_order(user_id, amount):

    orders, spent, vouches = get_user_data(user_id)

    cursor.execute(
        """
        UPDATE users
        SET orders = ?, spent = ?
        WHERE user_id = ?
        """,
        (
            orders + 1,
            spent + amount,
            user_id
        )
    )

    db.commit()

def add_vouch(user_id):

    orders, spent, vouches = get_user_data(user_id)

    cursor.execute(
        """
        UPDATE users
        SET vouches = ?
        WHERE user_id = ?
        """,
        (
            vouches + 1,
            user_id
        )
    )

    db.commit()


DEALS = {
    0: [  # Monday
        "🌳 MONDAY OAK SALE\nOak Wood 10% OFF Today Only",
        "🌲 MONDAY SPECIAL\nElm Wood orders get priority queue"
    ],

    1: [  # Tuesday
        "🍒 TUESDAY DEAL\nCherry Wood 15% OFF Today Only",
        "🔥 TUESDAY BONUS\nLava Wood orders include bonus planks"
    ],

    2: [  # Wednesday
        "🌲 MIDWEEK SPECIAL\nBirch Wood 10% OFF",
        "🪵 WALNUT WEDNESDAY\nWalnut Wood available at reduced prices"
    ],

    3: [  # Thursday
        "🌴 KOA THURSDAY\nKoa Wood priority delivery today",
        "🌲 PINE DEAL\nPine Wood bulk orders get discounts"
    ],

    4: [  # Friday
        "💎 FROST FRIDAY\nFrost Wood 15% OFF Today Only",
        "🧟 ZOMBIE FRIDAY\nZombie Wood limited stock available"
    ],

    5: [  # Saturday
        "🔥 PREMIUM SATURDAY\nBlue Spruce discounted today",
        "👻 SPOOK SATURDAY\nSpook Wood available for limited time"
    ],

    6: [  # Sunday
        "💀 SINISTER SUNDAY\nSinister Wood flash sale today",
        "🌑 PHANTOM SUNDAY\nPhantom Wood priority orders enabled"
    ]
}


@tasks.loop(hours=6)
async def daily_deals():

    current_day = datetime.datetime.now().weekday()

    todays_deals = DEALS[current_day]

    for guild in bot.guilds:

        channel = discord.utils.get(
            guild.text_channels,
            name="🔥・daily-deals"
        )

        if channel:

            deal = random.choice(todays_deals)

            embed = discord.Embed(
                title="🔥 Daily Deal",
                description=deal,
                color=discord.Color.orange()
            )

            await channel.send(embed=embed)


@tasks.loop(minutes=10)
async def update_stats():

    for guild in bot.guilds:

        channel = discord.utils.get(
            guild.text_channels,
            name="📊・stats"
        )

        if not channel:
            continue

        cursor.execute(
            "SELECT SUM(orders), SUM(spent), SUM(vouches) FROM users"
        )

        data = cursor.fetchone()

        total_orders = data[0] or 0
        total_revenue = data[1] or 0
        total_vouches = data[2] or 0

        vip_role = discord.utils.get(
            guild.roles,
            name=VIP_ROLE
        )

        vip_count = len(vip_role.members) if vip_role else 0

        open_tickets = 0

        for c in guild.text_channels:
            if c.name.startswith("ticket-"):
                open_tickets += 1

        embed = discord.Embed(
            title="📊 Server Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name="📦 Orders Completed",
            value=str(total_orders),
            inline=False
        )

        embed.add_field(
            name="💰 Total Revenue",
            value=f"{total_revenue:,}",
            inline=False
        )

        embed.add_field(
            name="⭐ Total Vouches",
            value=str(total_vouches),
            inline=False
        )

        embed.add_field(
            name="👑 VIP Customers",
            value=str(vip_count),
            inline=False
        )

        embed.add_field(
            name="🔥 Open Tickets",
            value=str(open_tickets),
            inline=False
        )

        try:

            messages = [
                message async for message in channel.history(limit=5)
            ]

            if messages:
                await messages[0].edit(embed=embed)
            else:
                await channel.send(embed=embed)

        except:
            await channel.send(embed=embed)





@bot.event
async def on_member_join(member):

    customer_role = discord.utils.get(
        member.guild.roles,
        name=CUSTOMER_ROLE
    )

    if customer_role:
        await member.add_roles(customer_role)

class CloseTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="❌ Close Ticket",
        style=discord.ButtonStyle.red,
        custom_id="persistent_close_button"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        transcript = ""

        async for msg in interaction.channel.history(
            limit=None,
            oldest_first=True
        ):
            transcript += f"{msg.author}: {msg.content}\n"

        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"{interaction.channel.name}.txt"
        )

        log_channel = discord.utils.get(
            interaction.guild.text_channels,
            name=LOG_CHANNEL_NAME
        )

        if log_channel:

            embed = discord.Embed(
                title="📜 Ticket Closed",
                description=f"{interaction.channel.name} closed by {interaction.user.mention}",
                color=discord.Color.red()
            )

            await log_channel.send(embed=embed)
            await log_channel.send(file=transcript_file)

        await interaction.response.send_message(
            "❌ Closing ticket...",
            ephemeral=True
        )

        await interaction.channel.delete()


class OrderModal(discord.ui.Modal, title="🪵 Wood Order Form"):

    orders = discord.ui.TextInput(
        label="FORMAT: amount wood amount wood",
        placeholder="FORMAT: 5 birch 5 koa 5 cave",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):

        guild = interaction.guild

        if SCAMMER_ROLE.lower() in [
            role.name.lower() for role in interaction.user.roles
        ]:

            await interaction.response.send_message(
                "❌ You are blacklisted from ordering.",
                ephemeral=True
            )
            return

        open_tickets = 0

        for channel in guild.text_channels:
            if channel.name.startswith("ticket-"):
                open_tickets += 1

        queue_position = open_tickets + 1

        if VIP_ROLE.lower() in [
            role.name.lower() for role in interaction.user.roles
        ]:
            queue_position = max(1, queue_position - 2)

        seller_role = discord.utils.get(
            guild.roles,
            name=SELLER_ROLE
        )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )
        }

        if seller_role:
            overwrites[seller_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )

        category = discord.utils.get(
            guild.categories,
            name=ORDER_CATEGORY
        )

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name.lower()}",
            overwrites=overwrites,
            category=category
        )

        text = self.orders.value.lower()
        words = text.split()

        total_cost = 0
        total_wait_minutes = 0
        total_truckloads = 0
        discount_used = False
        order_summary = ""

        i = 0

        while i < len(words):

            if words[i].isdigit():

                quantity = int(words[i])

                total_truckloads += quantity

                i += 1

                wood_words = []

                while i < len(words) and not words[i].isdigit():
                    wood_words.append(words[i])
                    i += 1

                wood_input = " ".join(wood_words)

                matched_wood = None

                for alias in WOOD_ALIASES:
                    if alias in wood_input:
                        matched_wood = WOOD_ALIASES[alias]
                        break

                if matched_wood:

                    price = WOOD_PRICES[matched_wood] * quantity

                    if quantity >= 5:
                        price = int(price * 0.8)
                        discount_used = True

                    orders, spent, vouches = get_user_data(
                        interaction.user.id
                    )

                    if orders >= 5:
                        price = int(price * 0.9)

                    total_cost += price

                    total_wait_minutes += quantity * 30

                    order_summary += (
                        f"🪵 {matched_wood.title()} x{quantity} = {price:,}\n"
                    )

        if total_truckloads > 10:

            await interaction.response.send_message(
                "❌ Maximum of 10 truck loads per order.",
                ephemeral=True
            )

            await channel.delete()
            return

        hours = total_wait_minutes // 60
        minutes = total_wait_minutes % 60

        embed = discord.Embed(
            title="🧾 Wood Order",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name="📦 Orders",
            value=order_summary,
            inline=False
        )

        embed.add_field(
            name="💰 Total Cost",
            value=f"{total_cost:,}",
            inline=False
        )

        embed.add_field(
            name="📦 Queue Position",
            value=f"You are #{queue_position} in queue",
            inline=False
        )

        embed.add_field(
            name="🕒 Estimated Wait",
            value=f"{hours}h {minutes}m",
            inline=False
        )

        if discount_used:
            embed.add_field(
                name="✅ Bulk Discount",
                value="20% discount applied",
                inline=False
            )

        orders, spent, vouches = get_user_data(
            interaction.user.id
        )

        if orders >= 5:
            embed.add_field(
                name="🏆 Loyalty Discount",
                value="10% repeat customer discount applied",
                inline=False
            )

        seller_ping = seller_role.mention if seller_role else "@here"

        await channel.send(
            f"🔔 {seller_ping} New order opened!",
            embed=embed,
            view=CloseTicketView()
        )

        add_order(interaction.user.id, total_cost)

    
        orders, spent, vouches = get_user_data(
            interaction.user.id
        )

        vip_role = discord.utils.get(
            guild.roles,
            name=VIP_ROLE
        )

        if orders >= 10 and vip_role:

            if vip_role not in interaction.user.roles:

                await interaction.user.add_roles(vip_role)

                await channel.send(
                    f"👑 {interaction.user.mention} unlocked VIP status!"
                )


        log_channel = discord.utils.get(
            guild.text_channels,
            name=LOG_CHANNEL_NAME
        )

        if log_channel:
            await log_channel.send(
                f"📜 {interaction.user} placed an order worth {total_cost:,}"
            )

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

class TicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🛒 Create Order",
        style=discord.ButtonStyle.green,
        custom_id="persistent_create_button"
    )
    async def create_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(OrderModal())

STATUSES = [
    "🌲 Selling Premium Wood",
    "🪵 Processing Orders",
    "🔥 Daily Deals Active",
    "⭐ Use /vouch",
    "💎 VIP Rewards Available"
]

@tasks.loop(minutes=5)
async def rotate_status():

    status = random.choice(STATUSES)

    await bot.change_presence(
        activity=discord.Game(status)
    )



@bot.event
async def on_ready():

    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())

    synced = await tree.sync()

    await bot.change_presence(
        activity=discord.Game("Selling Premium Wood 🌲")
    )

    if not daily_deals.is_running():
        daily_deals.start()

    if not update_stats.is_running():
        update_stats.start()

    
    if not rotate_status.is_running():
        rotate_status.start()


    print(f"Synced {len(synced)} command(s)")
    print(f"Logged in as {bot.user}")




@tree.command(name="setup", description="Post order panel")
async def setup(interaction: discord.Interaction):

    if not is_owner(interaction):
        return

    embed = discord.Embed(
        title="🪵 1x1 Cut TL's Price List",
        description=(
            "📦 Maximum 10 truck loads per order\n"
            "💰 20% discount on bulk orders over 5 truck loads\n"
            "🏆 Returning customers receive 10% off\n"
            "🛠️ Modded wood also available — just ask"
        ),
        color=discord.Color.gold()
    )

    embed.add_field(
        name="🌳 Standard Woods",
        value=(
            "• Oak Wood — 90k\n"
            "• Elm Wood — 90k\n"
            "• Cherry Wood — 90k\n"
            "• Lava Wood — 90k"
        ),
        inline=False
    )

    embed.add_field(
        name="🌲 Mid Tier Woods",
        value=(
            "• Cavecrawler / Blue Neon — 115k\n"
            "• Birch Wood — 130k\n"
            "• Walnut Wood — 135k\n"
            "• Pine Wood — 140k\n"
            "• Fir Wood — 140k\n"
            "• Koa Wood — 150k"
        ),
        inline=False
    )

    embed.add_field(
        name="💎 Rare Woods",
        value=(
            "• Zombie Wood — 170k\n"
            "• Gold Wood — 170k\n"
            "• Frost Wood — 200k\n"
            "• Snowglow Wood — 200k\n"
            "• Palm Wood — 220k"
        ),
        inline=False
    )

    embed.add_field(
        name="🔥 Premium Woods",
        value=(
            "• Blue Spruce Wood — 275k\n"
            "• Phantom Wood — 350k\n"
            "• Spook Wood — 400k\n"
            "• Sinister Wood — 400k"
        ),
        inline=False
    )

    embed.set_footer(
        text="Press the button below to place an order"
    )

    await interaction.response.send_message(
        embed=embed,
        view=TicketView()
    )



@tree.command(name="rewards", description="View rewards")
async def rewards(interaction: discord.Interaction):

    if not is_owner(interaction):
        return

    embed = discord.Embed(
        title="🎁 Server Rewards",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="🚀 Booster Rewards",
        value="2x Boost = 2 Free TLs",
        inline=False
    )

    embed.add_field(
        name="🏆 Loyalty Rewards",
        value="10 Orders = VIP",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

@tree.command(name="sales", description="View sales")
async def sales(interaction: discord.Interaction):

    if not is_owner(interaction):
        return

    cursor.execute(
        "SELECT SUM(spent) FROM users"
    )

    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    embed = discord.Embed(
        title="📊 Sales Stats",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="💰 Revenue",
        value=f"{total:,}",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

@tree.command(name="vouch", description="Vouch customer")
async def vouch(
    interaction: discord.Interaction,
    user: discord.Member
):

    if interaction.channel.name != VOUCH_CHANNEL:
        return

    add_vouch(user.id)

    embed = discord.Embed(
        title="⭐ Customer Vouch",
        description=f"{user.mention} received a vouch!",
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed)

@tree.command(name="close", description="Close ticket")
async def close(interaction: discord.Interaction):

    if not is_owner(interaction):
        return

    await interaction.channel.delete()

@tree.command(name="scam", description="Blacklist user")
async def scam(
    interaction: discord.Interaction,
    user: discord.Member
):

    if not is_owner(interaction):
        return

    scammer_role = discord.utils.get(
        interaction.guild.roles,
        name=SCAMMER_ROLE
    )

    if scammer_role:
        await user.add_roles(scammer_role)

    await interaction.response.send_message(
        f"🚫 {user.mention} marked as scammer."
    )

keep_alive()
bot.run(TOKEN)

