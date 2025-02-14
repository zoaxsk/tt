import os
import discord
from discord.ext import commands
from discord import app_commands

# Token dal file di ambiente (Render)
TOKEN = os.getenv("DISCORD_TOKEN")  
if not TOKEN:
    raise ValueError("❌ ERRORE: Token Discord non trovato. Assicurati di averlo impostato su Render.")

# Impostazioni del bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
ticket_roles = {}  # Dizionario per chi può rispondere ai ticket
ticket_channel_id = None  # Canale in cui verrà inviato il pannello dei ticket

# Evento quando il bot è online
@bot.event
async def on_ready():
    print(f"✅ {bot.user} è online!")
    try:
        synced = await bot.tree.sync()  # Sincronizza i comandi slash
        print(f"🔄 Comandi slash sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"❌ Errore nella sincronizzazione: {e}")

# Comando per configurare il canale dei ticket
@bot.tree.command(name="setup", description="Imposta il canale per il pannello dei ticket")
async def setup(interaction: discord.Interaction, channel: discord.TextChannel):
    global ticket_channel_id
    ticket_channel_id = channel.id  
    await interaction.response.send_message(f"✅ Il canale scelto per i ticket è: {channel.mention}!", ephemeral=True)

# Comando per creare il pannello dei ticket
@bot.tree.command(name="setup_ticket", description="Crea il pannello dei ticket con pulsanti interattivi")
async def setup_ticket(interaction: discord.Interaction):
    if ticket_channel_id is None:
        await interaction.response.send_message("❌ Non hai configurato un canale per i ticket! Usa /setup per farlo.", ephemeral=True)
        return

    channel = interaction.guild.get_channel(ticket_channel_id)  
    if not channel:  
        await interaction.response.send_message("❌ Il canale configurato non esiste. Verifica la configurazione.", ephemeral=True)  
        return  

    embed = discord.Embed(
        title="📩 Hai bisogno di aiuto?",
        description="Apri un ticket scegliendo una delle opzioni qui sotto!",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2950/2950521.png")  
    embed.set_footer(text="Seleziona un'opzione per aprire un ticket.")  

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
    await interaction.response.send_message(f"✅ Pannello dei ticket creato in {channel.mention}.", ephemeral=True)

# Gestione dei pulsanti (apertura e chiusura dei ticket)
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data["custom_id"]

        if custom_id in ["support", "sos", "feedback", "report"]:
            guild = interaction.guild
            user = interaction.user

            category = discord.utils.get(guild.categories, name="🎫 Ticket")
            if not category:
                await interaction.response.send_message("❌ La categoria '🎫 Ticket' non esiste. Creala manualmente.", ephemeral=True)
                return

            ticket_channel = await guild.create_text_channel(f"{custom_id}-{user.name}", category=category)
            await ticket_channel.set_permissions(user, read_messages=True, send_messages=True)
            await ticket_channel.set_permissions(guild.default_role, read_messages=False)

            if guild.id in ticket_roles:
                role = guild.get_role(ticket_roles[guild.id])
                if role:
                    await ticket_channel.set_permissions(role, read_messages=True, send_messages=True)

            view = discord.ui.View()
            close_button = discord.ui.Button(label="🔒 Chiudi Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
            view.add_item(close_button)

            await ticket_channel.send(f"{user.mention} Il tuo ticket è stato aperto. Lo staff ti risponderà a breve.", view=view)
            await interaction.response.send_message(f"✅ Ticket aperto! Controlla {ticket_channel.mention}.", ephemeral=True)

        elif custom_id == "close_ticket":
            await interaction.channel.delete()

# Avvio del bot
bot.run(TOKEN)