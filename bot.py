import os
import discord
from discord.ext import commands
from discord import app_commands

# Prende il token dalle Environment Variables di Render
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
ticket_roles = {}  # Dizionario per chi può rispondere ai ticket
ticket_channel_id = None  # ID del canale per l'embed dei ticket

@bot.event
async def on_ready():
    print(f"✅ {bot.user} è online!")
    try:
        synced = await bot.tree.sync()  # Sincronizza i comandi slash
        print(f"🔄 Comandi slash sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"❌ Errore nella sincronizzazione: {e}")

@bot.tree.command(name="setup", description="Imposta la categoria per l'embed dei ticket")
async def setup(interaction: discord.Interaction, channel: discord.TextChannel):
    """Imposta il canale dove inviare l'embed dei ticket."""
    global ticket_channel_id
    ticket_channel_id = channel.id
    await interaction.response.send_message(f"✅ Canale ticket impostato: {channel.mention}!", ephemeral=True)

@bot.tree.command(name="setup_ticket", description="Crea l'embed con il pannello dei ticket")
async def setup_ticket(interaction: discord.Interaction):
    """Crea l'embed con il pulsante per aprire un ticket."""
    if ticket_channel_id is None:
        await interaction.response.send_message("❌ Usa /setup per configurare un canale prima.", ephemeral=True)
        return

    channel = interaction.guild.get_channel(ticket_channel_id)
    if not channel:
        await interaction.response.send_message("❌ Canale non trovato.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📩 Supporto Ticket",
        description="Apri un ticket cliccando il pulsante in basso!",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2950/2950521.png")
    embed.set_footer(text="Seleziona una categoria per aprire un ticket.")

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
    await interaction.response.send_message(f"✅ Ticket panel creato in {channel.mention}.", ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Gestisce i pulsanti cliccati per aprire ticket."""
    if interaction.data["custom_id"] in ["support", "sos", "feedback", "report"]:
        guild = interaction.guild
        user = interaction.user
        category_name = interaction.data["custom_id"]

        category = discord.utils.get(guild.categories, name="🎫 Ticket")
        if not category:
            await interaction.response.send_message("❌ Categoria '🎫 Ticket' non trovata.", ephemeral=True)
            return

        ticket_channel = await guild.create_text_channel(f"{category_name}-{user.name}", category=category)
        await ticket_channel.set_permissions(user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(guild.default_role, read_messages=False)

        if guild.id in ticket_roles:
            role = guild.get_role(ticket_roles[guild.id])
            if role:
                await ticket_channel.set_permissions(role, read_messages=True, send_messages=True)

        view = discord.ui.View()
        close_button = discord.ui.Button(label="🔒 Chiudi Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
        view.add_item(close_button)

        await ticket_channel.send(f"{user.mention} Il tuo ticket è stato creato! Lo staff ti risponderà presto.", view=view)
        await interaction.response.send_message(f"✅ Ticket aperto in {ticket_channel.mention}.", ephemeral=True)

    elif interaction.data["custom_id"] == "close_ticket":
        await interaction.channel.delete()

# Avvia il bot con il token di Render
bot.run(TOKEN)
