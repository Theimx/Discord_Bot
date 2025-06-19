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

conn = sqlite3.connect(r'users.db')
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

def create_item(name, categorie, effect, description):
    cursor.execute("""
        INSERT INTO items (name, categorie, effect, description)
        VALUES (?, ?, ?, ?)
    """, (name, categorie, effect, description))
    conn.commit()

def add_item_to_inventory(user_id, item_id, quantity=1):
    cursor.execute("""
        SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?
    """, (user_id, item_id))
    result = cursor.fetchone()

    if result:
        new_quantity = result[0] + quantity
        cursor.execute("""
            UPDATE inventory SET quantity = ? WHERE user_id = ? AND item_id = ?
        """, (new_quantity, user_id, item_id))
    else:
        cursor.execute("""
            INSERT INTO inventory (user_id, item_id, quantity)
            VALUES (?, ?, ?)
        """, (user_id, item_id, quantity))
    conn.commit()

@bot.command()
async def inventaire(ctx, user: discord.User = None):
    user = user or ctx.author
    cursor.execute("""
        SELECT items.item_id, items.name, inventory.quantity
        FROM inventory
        JOIN items ON inventory.item_id = items.item_id
        WHERE inventory.user_id = ?
    """, (user.id,))
    items = cursor.fetchall()

    if items:
        message = f"📦 Inventaire de {user.display_name} :\n"
        for item in items:
            message += f"| Item : {item[1]} x{item[2]} | id : {item[0]} |\n"
    else:
        message = f"{user.display_name} n'a aucun objet dans son inventaire."

    await ctx.send(message)

@bot.command()
async def Nikitrade(ctx, cible: discord.User, item_id: int, quantity: int):
    emetteur_id = ctx.author.id
    cible_id = cible.id

    # Vérifie que l'émetteur a l'item en quantité suffisante
    cursor.execute("""
        SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?
    """, (emetteur_id, item_id))
    result = cursor.fetchone()

    if result and result[0] >= quantity:
        # Retire de l'émetteur
        new_quantity = result[0] - quantity
        if new_quantity == 0:
            cursor.execute("""
                DELETE FROM inventory WHERE user_id = ? AND item_id = ?
            """, (emetteur_id, item_id))
        else:
            cursor.execute("""
                UPDATE inventory SET quantity = ? WHERE user_id = ? AND item_id = ?
            """, (new_quantity, emetteur_id, item_id))

        # Ajoute à la cible
        add_item_to_inventory(cible_id, item_id, quantity)
        conn.commit()

        await ctx.send(f"✅ {ctx.author.display_name} a donné {quantity} exemplaire(s) de l'item {item_id} à {cible.display_name}.")

    else:
        await ctx.send(f"❌ Tu n'as pas assez de cet objet à échanger.")


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
**!inventaire @joueur** → Affiche ton inventaire ou celui d'un autre joueur. 
**!Nikitrade @joueur id qtt** → Permet de donner un objet a un joueur.

*Plus de commandes arrivent bientôt.*
    """
    await ctx.send(help_message)


# Lancement du bot
print("Bot opérationel")
bot.run(TOKEN)
