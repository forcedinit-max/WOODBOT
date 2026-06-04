
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
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 10000)),
        
        threaded=True
    )



def keep_alive():
    t = Thread(target=run_web)
    t.start()



TOKEN = os.getenv("TOKEN")

OWNER_ID = 1361735588029399193

SELLER_ROLE = "seller"
SCAMMER_ROLE = "scammer"

VIP_ROLE = "👑 VIP"
SELLER_CATEGORY = "🛠️ Seller Apps"
CUSTOMER_ROLE = "🌲 Customer"
REGULAR_ROLE = "🪵 Regular"
LUMBERJACK_ROLE = "⚒️ Lumberjack"
ELITE_ROLE = "💠 Elite Customer"
LEGENDARY_ROLE = "🐉 Legendary Buyer"
AXE_ORDER_CATEGORY = "🪓 Axe Orders"
AXE_CHANNEL = "🪓・axe-prices"
LOG_CHANNEL_NAME = "📜・order-logs"
VOUCH_CHANNEL = "⭐・vouches"
ORDER_CATEGORY = "🪵 Wood Orders"
WOOD_CHANNEL = "💰・wood-prices"
GIFT_CHANNEL = "🎁・gift-prices"
SERVICE_CHANNEL = "🛠️・service-prices"
GIFT_ORDER_CATEGORY = "🎁 Gift Orders"
SERVICE_ORDER_CATEGORY = "🛠️ Service Orders"


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

    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, orders, spent, vouches)
        VALUES (?, 0, 0, 0)
        """,
        (user_id,)
    )

    cursor.execute(
        """
        UPDATE users
        SET vouches = vouches + 1
        WHERE user_id = ?
        """,
        (user_id,)
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

    role = discord.utils.get(
        member.guild.roles,
        name=CUSTOMER_ROLE
    )

    if role:
        await member.add_roles(role)

    try:

        embed = discord.Embed(
            title="🌲 Welcome To ShopWood",
            description=(
                f"Welcome {member.mention}!\n\n"

                "🪵 Need wood?\n"
                "Use the order panel to create a ticket.\n\n"

                "⭐ Remember to vouch after successful orders.\n\n"

                "🔥 Check:\n"
                "• 📜・rules\n"
                "• 💰・prices\n"
                "• 🎁・rewards\n"
                "• 🔥・daily-deals\n\n"

                "Enjoy your stay!"
            ),
            color=discord.Color.green()
        )

        await member.send(embed=embed)

    except:
        pass

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
   
class SellerApplicationView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🛠️ Apply For Seller",
        style=discord.ButtonStyle.blurple,
        custom_id="persistent_seller_apply"
    )
    async def seller_apply(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild

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
                name=SELLER_CATEGORY
            )



        channel = await guild.create_text_channel(
            name=f"seller-app-{interaction.user.name.lower()}",
            overwrites=overwrites,
            category=category
        )

        embed = discord.Embed(
            title="🛠️ Seller Application",
            description=(
                "Thank you for applying to become a seller.\n\n"

                "### Expectations\n"
                "• Be active and professional\n"
                "• Deliver orders quickly\n"
                "• Treat customers respectfully\n"
                "• No trolling or fake promises\n\n"

                "### Important\n"
                "Scamming will NOT be tolerated.\n"
                "Any seller caught scamming will:\n"
                "• Be removed from the seller team\n"
                "• Receive the scammer role\n"
                "• Be permanently blacklisted\n\n"
            ),
            color=discord.Color.orange()
        )

        await channel.send(
            content=f"{interaction.user.mention}",
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ Seller application created: {channel.mention}",
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
    bot.add_view(SellerApplicationView())
    bot.add_view(AxeTicketView())
    bot.add_view(ServiceTicketView())
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



@tree.command(
    name="sellerpanel",
    description="Post seller application panel"
)
async def sellerpanel(interaction: discord.Interaction):

    if not is_owner(interaction):
        return

    embed = discord.Embed(
        title="🛠️ Apply To Be A Seller",
        description=(
            "Want to join the seller team?\n\n"
            "Open a ticket below and apply.\n\n"
            "Trusted and active sellers only."
        ),
        color=discord.Color.orange()
    )

    await interaction.channel.send(
        embed=embed,
        view=SellerApplicationView()
    )

    await interaction.response.send_message(
        "✅ Seller panel posted.",
        ephemeral=True
    )



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

   
    await interaction.channel.send(
        embed=embed,
        view=TicketView()
    )

    await interaction.response.send_message(
        "✅ Order panel posted.",
        ephemeral=True
    )




@tree.command(name="rules", description="Post server rules")
async def rules(interaction: discord.Interaction):

    if not is_owner(interaction):
        return

    embed = discord.Embed(
        title="About the Server",
        description=(
            "The server follows rules set up by Discord's and Roblox's Terms of Use.\n\n"
            "Guidelines mentioned here are covered in their most basic form. "
            "Use common sense and respect all members."
        ),
        color=discord.Color.blue()
    )

    embed.add_field(
        name="General Guidelines",
        value=(
            "[Discord Terms of Use](https://discord.com/terms)\n"
            "[Roblox Terms of Use](https://en.help.roblox.com/hc/en-us/articles/115004647846-Roblox-Terms-of-Use)\n\n"

            "**Treat members respectfully.** "
            "Be polite to others; harassment or discriminatory behavior is not tolerated.\n\n"

            "**No extreme profanity.** "
            "Light swearing is allowed, but abuse may result in punishment.\n\n"

            "**Portray yourself appropriately.** "
            "Profiles should not contain offensive names or inappropriate content.\n\n"

            "**No personal information.** "
            "The privacy of members is extremely important.\n\n"

            "**No advertising.** "
            "Do not advertise servers or social media in chats or DMs.\n\n"

            "**No NSFW or illegal content.** "
            "Illegal activity or inappropriate discussions are forbidden.\n\n"

            "**Do not leak content.** "
            "Respect unreleased or private content.\n\n"

            "**No suspicious files or media.** "
            "Only safe embeddable files should be shared.\n\n"

            "**Use common sense.** "
            "Loopholes or rule bypassing will still be handled by staff."
        ),
        inline=False
    )

    embed.set_footer(
        text="ShopWood"
    )

    await interaction.channel.send(
        embed=embed,
    )

    await interaction.response.send_message(
        "✅ Rules panel posted.",
        ephemeral=True
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
        value=(
            "• 2x Boost = 2 Free TLs\n"
            "• Priority support\n"
            "• Exclusive role"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🏆 Loyalty Rewards",
        value=(
            "• 5 Orders = 10% Discount\n"
            "• 10 Orders = VIP\n"
            "• 25 Orders = Elite Customer\n"
            "• 50 Orders = Legendary Buyer"
        ),
        inline=False
    )

    embed.add_field(
        name="🎉 Event Rewards",
        value=(
            "• Random Giveaways\n"
            "• Flash Sales\n"
            "• Daily Deals"
        ),
        inline=False
    )
    
    
        
    await interaction.channel.send(
        embed=embed,
    )
    
    await interaction.response.send_message(
        "✅ Rewards panel posted.",
        ephemeral=True
    )

class ServiceTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🛠️ Order Service",
        style=discord.ButtonStyle.blurple,
        custom_id="persistent_service_ticket"
    )
    async def create_service_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild
        for channel in guild.text_channels:

            if channel.name == f"service-{interaction.user.name.lower()}":

                await interaction.response.send_message(
                    "❌ You already have an open service ticket.",
                    ephemeral=True
                )

                return



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
            name=SERVICE_ORDER_CATEGORY
        )

        channel = await guild.create_text_channel(
            name=f"service-{interaction.user.name.lower()}",
            overwrites=overwrites,
            category=category
        )

        embed = discord.Embed(
            title="🛠️ Service Order",
            description=(
                "Please explain:\n\n"
                "• Which service you want\n"
                "• Quantity\n"
                "• Any extra details"
            ),
            color=discord.Color.orange()
        )

        await channel.send(
            content=f"{interaction.user.mention}",
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ Service ticket created: {channel.mention}",
            ephemeral=True
        )


@tree.command(name="servicepanel", description="Post service panel")
async def servicepanel(interaction: discord.Interaction):

    if not is_owner(interaction):
        return

    embed = discord.Embed(
        title="🛠️ LT2 Services",
        description=(
            "Professional Lumber Tycoon 2 services.\n"
            "Trusted staff and fast completion."
        ),
        color=discord.Color.orange()
    )

    embed.add_field(
        name="🏗️ Building Services",
        value=(
            "• Storage Containers — 50k per container\n"
            "• Auto Wood Sorters — 80k per container\n"
            "• 1x1 Unit Cutter — 150k\n"
            "• Auto Vehicle Unloader — 200k\n"
            "• Small Shop Build — 500k\n"
            "• Large Shop Build — 2m"
        ),
        inline=False
    )

    embed.add_field(
        name="🛒 Purchasing Services",
        value=(
            "• Normal Wires — 200k per truckload\n"
            "• Neon Wires — 400k per truckload\n"
            "• Glass — 100k per truckload\n\n"
            "Truckloads of conveyors, trucks and other items\n"
            "can be discussed in a ticket."
        ),
        inline=False
    )

    embed.add_field(
        name="🔧 Misc Services",
        value=(
            "• Help Getting Golden Blueprint — 50k\n"
            "• Fill Blueprints — 150k\n\n"
            "❌ No discounts available for services."
        ),
        inline=False
    )

    embed.set_footer(
        text="Press the button below to order services"
    )

    await interaction.channel.send(
        embed=embed,
        view=ServiceTicketView()
    )

    await interaction.response.send_message(
        "✅ Service panel posted.",
        ephemeral=True
    )

class AxeTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🪓 Order Axes",
        style=discord.ButtonStyle.red,
        custom_id="persistent_axe_ticket"
    )
    async def create_axe_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild

        for channel in guild.text_channels:

            if channel.name == f"axe-{interaction.user.name.lower()}":

                await interaction.response.send_message(
                    "❌ You already have an open axe ticket.",
                    ephemeral=True
                )

                return

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
            name=AXE_ORDER_CATEGORY
        )

        channel = await guild.create_text_channel(
            name=f"axe-{interaction.user.name.lower()}",
            overwrites=overwrites,
            category=category
        )

        embed = discord.Embed(
            title="🪓 Axe Order",
            description=(
                "Please explain:\n\n"
                "• Which axe you want\n"
                "• Gift / Boxed / Loose\n"
                "• Quantity"
            ),
            color=discord.Color.red()
        )

        await channel.send(
            content=f"{interaction.user.mention}",
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ Axe ticket created: {channel.mention}",
            ephemeral=True
        )


@tree.command(name="axepanel", description="Post axe panel")
async def axepanel(interaction: discord.Interaction):

    if not is_owner(interaction):
        return

    embed = discord.Embed(
        title="🪓 LT2 Axe Prices",
        description=(
            "Premium axes available.\n"
            "Gifted, boxed and loose variants.\n" 
            "💰 20% bulk discount on orders of 10+ axes."
        ),
        color=discord.Color.red()
    )

    embed.add_field(
        name="🌿 Overgrown Axe",
        value=(
            "• Gift — 30k\n"
            "• Boxed — 20k\n"
            "• Loose — 10k"
        ),
        inline=False
    )

    embed.add_field(
        name="🔥 Fire Axe",
        value=(
            "• Gift — 20k\n"
            "• Boxed — 20k\n"
            "• Loose — 10k"
        ),
        inline=False
    )

    embed.add_field(
        name="🐷 Pig Axe",
        value=(
            "• Boxed — 25k\n"
            "• Loose — 20k"
        ),
        inline=False
    )

    embed.add_field(
        name="⏳ Endtimes Axe",
        value=(
            "• Boxed — 25k\n"
            "• Loose — 15k"
        ),
        inline=False
    )

    embed.add_field(
        name="🪓 Many Axe",
        value=(
            "• Boxed — 25k\n"
            "• Loose — 15k"
        ),
        inline=False
    )

    embed.add_field(
        name="🟠 Amber Axe",
        value=(
            "• Boxed — 30k\n"
            "• Loose — 20k"
        ),
        inline=False
    )

    embed.add_field(
        name="🔄 Inverse Axe",
        value=(
            "• Gift — 45k\n"
            "• Boxed — 35k\n"
            "• Loose — 20k"
        ),
        inline=False
    )

    embed.add_field(
        name="🍬 Event Axes",
        value=(
            "• Candy Corn Axe — 15k\n"
            "• Rukiry Axe — 10k\n"
            "• Bird Axe — 10k\n"
            "• Beta Axe — 15k"
        ),
        inline=False
    )

    embed.add_field(
        name="🎄 Seasonal Axes",
        value=(
            "• Gingerbread Axe\n"
            "Gift — 30k | Boxed — 20k | Loose — 15k\n\n"

            "• Frost Axe\n"
            "Gift — 30k | Boxed — 20k | Loose — 10k"
        ),
        inline=False
    )

    embed.add_field(
        name="⚒️ Utility Axes",
        value=(
            "• Chicken Axe\n"
            "Gift — 25k | Boxed — 20k | Loose — 10k\n\n"

            "• Refined Axe\n"
            "Gift — 35k | Boxed — 20k | Loose — 10k\n\n"

            "• Alpha Axe\n"
            "Boxed — 15k | Loose — 10k\n\n"

            "• Cave Axe\n"
            "Gift — 30k | Boxed — 20k | Loose — 10k"
        ),
        inline=False
    )

    embed.set_footer(
        text="Press the button below to order axes"
    )

    await interaction.channel.send(
        embed=embed,
        view=AxeTicketView()
    )

    await interaction.response.send_message(
        "✅ Axe panel posted.",
        ephemeral=True
    )


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

