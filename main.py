import discord
import sqlite3
import aiohttp
import io
from discord.ext import commands

#Source code for the Discord bot : Светлана
#Made by Theimx

# Configuration
TOKEN = ""
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # nécessaire pour on_member_join et on_member_remove

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Table players
cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        hp INTEGER DEFAULT 100,
        attack INTEGER DEFAULT 10,
        defense INTEGER DEFAULT 5,
        speed INTEGER DEFAULT 5,
        luck INTEGER DEFAULT 1,
        Cc INTEGER DEFAULT 1,
        Dc INTEGER DEFAULT 1
    )
""")
conn.commit()

# Table items
cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        categorie TEXT,
        effect TEXT,
        description TEXT
    )
""")
conn.commit()

# Table inventory
cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER,
        item_id INTEGER,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES players(user_id),
        FOREIGN KEY (item_id) REFERENCES items(item_id)
    )
""")
conn.commit()

# Table equipment
cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment (
        user_id INTEGER PRIMARY KEY,
        weapon_id INTEGER,
        armor_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES players(user_id),
        FOREIGN KEY (weapon_id) REFERENCES items(item_id),
        FOREIGN KEY (armor_id) REFERENCES items(item_id)
    )
""")
conn.commit()

# Table configuration des salons
cursor.execute("""
    CREATE TABLE IF NOT EXISTS server_config (
        guild_id INTEGER PRIMARY KEY,
        welcome_channel_id INTEGER,
        leave_channel_id INTEGER
    )
""")
conn.commit()

# Fonction utilitaire : récupérer un avatar en fichier
async def avatar_to_file(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
            return discord.File(io.BytesIO(data), filename=filename)

@bot.event
async def on_member_join(member):
    cursor.execute("SELECT welcome_channel_id FROM server_config WHERE guild_id = ?", (member.guild.id,))
    result = cursor.fetchone()
    if result and result[0]:
        channel = bot.get_channel(result[0])
        if channel:
            avatar_url = member.display_avatar.url
            file = await avatar_to_file(avatar_url, f"{member.name}.png")
            await channel.send(f"🎉 Bienvenue {member.mention} sur **{member.guild.name}** !", file=file)

@bot.event
async def on_member_remove(member):
    cursor.execute("SELECT leave_channel_id FROM server_config WHERE guild_id = ?", (member.guild.id,))
    result = cursor.fetchone()
    if result and result[0]:
        channel = bot.get_channel(result[0])
        if channel:
            avatar_url = member.display_avatar.url
            file = await avatar_to_file(avatar_url, f"{member.name}.png")
            await channel.send(f"👋 {member.name} a quitté **{member.guild.name}**.", file=file)

# Commande : configurer salon de bienvenue
@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome(ctx, channel: discord.TextChannel):
    cursor.execute("""
        INSERT INTO server_config (guild_id, welcome_channel_id)
        VALUES (?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET welcome_channel_id=excluded.welcome_channel_id
    """, (ctx.guild.id, channel.id))
    conn.commit()
    await ctx.send(f"✅ Salon de bienvenue configuré sur {channel.mention}")

# Commande : configurer salon de départ
@bot.command()
@commands.has_permissions(administrator=True)
async def setleave(ctx, channel: discord.TextChannel):
    cursor.execute("""
        INSERT INTO server_config (guild_id, leave_channel_id)
        VALUES (?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET leave_channel_id=excluded.leave_channel_id
    """, (ctx.guild.id, channel.id))
    conn.commit()
    await ctx.send(f"✅ Salon de départ configuré sur {channel.mention}")

# Commande d'aide
@bot.command()
async def Nikihelp(ctx):
    help_message = """
**Commandes disponibles :**

!xp @joueur → Affiche ton XP ou celui d'un autre joueur  
!inventaire @joueur → Affiche ton inventaire ou celui d'un autre joueur  
!Nikitrade @joueur id quantité → Échange un objet  
!setwelcome #salon → Configure le salon de bienvenue  
!setleave #salon → Configure le salon des départs  

*Plus de commandes bientôt...*
    """
    await ctx.send(help_message)

# Reste de tes fonctions et commandes (add_xp, inventaire, trade, etc.)...

# Fonction pour ajouter de l'XP
def add_xp(user_id, xp_to_add):
    cursor.execute("SELECT xp FROM players WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        new_xp = result[0] + xp_to_add
        cursor.execute("UPDATE players SET xp = ? WHERE user_id = ?", (new_xp, user_id))
    else:
        cursor.execute("INSERT INTO players (user_id, xp) VALUES (?, ?)", (user_id, xp_to_add))
    conn.commit()

# Commande XP
@bot.command()
async def xp(ctx, user: discord.User = None):
    user = user or ctx.author
    cursor.execute("SELECT xp FROM players WHERE user_id = ?", (user.id,))
    result = cursor.fetchone()
    if result:
        await ctx.send(f"{user.display_name} a {round(result[0])} XP.")
    else:
        await ctx.send(f"{user.display_name} n'a pas encore d'XP.")

# Gestion des messages et XP
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    char_count = len(message.content)
    xp_to_add = char_count * 0.1
    if xp_to_add > 0:
        add_xp(message.author.id, xp_to_add)

    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = None):
    if amount is not None:
        if amount <= 0:
            await ctx.send("❌ Merci d'indiquer un nombre positif.")
            return
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 pour inclure la commande elle-même
        await ctx.send(f"✅ {len(deleted)-1} message(s) supprimé(s).", delete_after=3)
    else:
        # Supprime tout le salon
        await ctx.send("🧹 Nettoyage complet du salon...", delete_after=2)
        deleted = await ctx.channel.purge()
        await ctx.send(f"✅ Salon entièrement nettoyé ({len(deleted)} messages supprimés).", delete_after=3)


# Lancement du bot
print("Bot opérationnel")
bot.run(TOKEN)
