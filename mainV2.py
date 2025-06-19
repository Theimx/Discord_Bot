import discord
import sqlite3
from discord.ext import commands

#Source code for the Discord bot : Nikitcho
#Made by Theimx

# Configuration
TOKEN = "MTMxMTA4MDE4MjQ1ODc0NDkzMg.GvUuwS.C0UbKwriaznPTFB_s7gkUHG3AEk5rwPjl8UDd4"
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True  # pour lire le contenu des messages

bot = commands.Bot(command_prefix=PREFIX, intents=intents)# Initialisation du bot

conn = sqlite3.connect(r'Bot_Discord/users.db')
cursor = conn.cursor()

# Table players corrigée (suppression de la virgule en trop)
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

# Commande pour vérifier son XP
@bot.command()
async def xp(ctx, user: discord.User = None):
    user = user or ctx.author
    cursor.execute("SELECT xp FROM players WHERE user_id = ?", (user.id,))
    result = cursor.fetchone()
    if result:
        await ctx.send(f"{user.display_name} a {round(result[0])} XP.")
    else:
        await ctx.send(f"{user.display_name} n'a pas encore d'XP.")

# Événement déclenché à chaque message
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    char_count = len(message.content)
    xp_to_add = char_count * 0.1  # 1 XP par tranche de 10 caractères

    if xp_to_add > 0:
        add_xp(message.author.id, xp_to_add)

    await bot.process_commands(message)
@bot.command()
async def Nikihelp(ctx):
    help_message = """
    **Commandes disponibles :**

**!xp @joueur** → Affiche ton XP ou celui d'un autre joueur.  
**!Nikihelp** → Affiche ce message d'aide.

*Plus de commandes arrivent bientôt.*
    """
    await ctx.send(help_message)

# Lancement du bot
print("Bot opérationel")
bot.run(TOKEN)
