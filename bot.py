import os
import discord
from discord.ext import commands
from flask import Flask
import threading

# Configurazione server Flask per mantenere il bot attivo su Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_web).start()

# Prende il token di Discord dalle variabili d'ambiente di Render
TOKEN = os.getenv("DISCORD_TOKEN")

# Configurazione bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
ticket_roles = {}  # Dizionario per i ruoli admin/moderatori che possono gestire i ticket
ticket_channel_id = None  # Canale per il pannello ticket

@bot.event
async def on_ready():
    print(f"✅ {bot.user} è online!")
    try:
        synced = await bot.tree.sync()  # Sincronizza i comandi slash
        print(f"🔄 Comandi sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"❌ Errore sincronizzazione: {e}")

# Comando per impostare il canale dei ticket
@bot.tree.command(name="setup", description="Imposta il canale per il pannello ticket")
async def setup(interaction: discord.Interaction, channel: discord.TextChannel):
    global ticket_channel_id
    ticket_channel_id = channel.id
    await interaction.response.send_message(f"✅ Canale impostato: {channel.mention}", ephemeral=True)

# Comando per creare il pannello ticket
@bot.tree.command(name="setup_ticket", description="Crea il pannello per aprire i ticket")
async def setup_ticket(interaction: discord.Interaction):
    if ticket_channel_id is None:
        await interaction.response.send_message("❌ Imposta prima un canale con /setup.", ephemeral=True)
        return

    channel = interaction.guild.get_channel(ticket_channel_id)
    if not channel:
        await interaction.response.send_message("❌ Canale non trovato.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📩 Supporto",
        description="Apri un ticket cliccando il pulsante!",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2950/2950521.png")
    embed.set_footer(text="Seleziona una categoria.")

    view = discord.ui.View()
    categories = {
        "🛠️ Supporto": "support",
        "🚨 SOS": "sos",
        "💡 Feedback": "feedback",
        "⚠️ Report": "report"
    }
    for label, custom_id in categories.items():
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id)
        view.add_item(button)

    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ Pannello ticket creato in {channel.mention}.", ephemeral=True)

# Comando per impostare il ruolo admin/moderatore dei ticket
@bot.tree.command(name="set_admin", description="Imposta il ruolo che può gestire i ticket")
async def set_admin(interaction: discord.Interaction, role: discord.Role):
    ticket_roles[interaction.guild.id] = role.id
    await interaction.response.send_message(f"✅ Il ruolo {role.mention} può ora gestire i ticket.", ephemeral=True)

# Gestione ticket
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if "custom_id" in interaction.data:
        category_id = interaction.data["custom_id"]
        if category_id in ["support", "sos", "feedback", "report"]:
            guild = interaction.guild
            user = interaction.user

            category = discord.utils.get(guild.categories, name="🎫 Ticket")
            if not category:
                await interaction.response.send_message("❌ Categoria '🎫 Ticket' non trovata.", ephemeral=True)
                return

            ticket_channel = await guild.create_text_channel(f"{category_id}-{user.name}", category=category)
            await ticket_channel.set_permissions(user, read_messages=True, send_messages=True)
            await ticket_channel.set_permissions(guild.default_role, read_messages=False)

            if guild.id in ticket_roles:
                role = guild.get_role(ticket_roles[guild.id])
                if role:
                    await ticket_channel.set_permissions(role, read_messages=True, send_messages=True)

            view = discord.ui.View()
            close_button = discord.ui.Button(label="🔒 Chiudi Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
            view.add_item(close_button)

            await ticket_channel.send(f"{user.mention} Il tuo ticket è stato creato! Un membro dello staff ti risponderà presto.", view=view)
            await interaction.response.send_message(f"✅ Ticket aperto in {ticket_channel.mention}.", ephemeral=True)

        elif category_id == "close_ticket":
            await interaction.channel.delete()

bot.run(TOKEN)