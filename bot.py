import discord
from discord.ext import commands
from discord import app_commands

TOKEN = "MTMzOTk5NDc4OTE0MzM3OTk5OQ.GnwJBh.c4g7YmnesL2_bcvoad-x1xiFbuA3uY8-U0gY9s"  # Sostituisci con il nuovo token

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
ticket_roles = {}  # Dizionario per salvare chi può rispondere ai ticket
ticket_channel_id = None  # Variabile per salvare l'ID del canale dove inviare l'embed


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
    """Comando per impostare la categoria (canale) dove inviare l'embed dei ticket."""
    global ticket_channel_id
    ticket_channel_id = channel.id  # Salva l'ID del canale dove inviare l'embed
    await interaction.response.send_message(f"✅ La categoria/il canale scelto è: {channel.mention}!", ephemeral=True)


@bot.tree.command(name="setup_ticket", description="Crea l'embed con il pannello per aprire i ticket")
async def setup_ticket(interaction: discord.Interaction):
    """Crea l'embed con il pulsante per aprire un ticket nel canale configurato."""
    if ticket_channel_id is None:
        await interaction.response.send_message("❌ Non hai configurato un canale per i ticket! Usa `/setup` per farlo.", ephemeral=True)
        return
    
    channel = interaction.guild.get_channel(ticket_channel_id)
    if not channel:
        await interaction.response.send_message("❌ Canale configurato non trovato. Verifica se esiste.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📩 Hai bisogno di supporto?",
        description="Apri un ticket scegliendo una delle seguenti opzioni!",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2950/2950521.png")  # Icona di moderazione
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
    await interaction.response.send_message(f"✅ L'embed dei ticket è stato creato in {channel.mention}.", ephemeral=True)


@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Gestisce i pulsanti cliccati dagli utenti."""
    
    if interaction.data["custom_id"] in ["support", "sos", "feedback", "report"]:
        guild = interaction.guild
        user = interaction.user
        category_name = interaction.data["custom_id"]

        # Cerca una categoria esistente chiamata "🎫 Ticket"
        category = discord.utils.get(guild.categories, name="🎫 Ticket")
        
        if not category:
            # Se la categoria non esiste, avvisiamo e non procediamo
            await interaction.response.send_message("❌ La categoria '🎫 Ticket' non è stata trovata. Assicurati che esista.", ephemeral=True)
            return

        # Creiamo il canale del ticket all'interno della categoria esistente
        ticket_channel = await guild.create_text_channel(f"{category_name}-{user.name}", category=category)
        
        # Impostiamo i permessi
        await ticket_channel.set_permissions(user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(guild.default_role, read_messages=False)

        # Imposta il ruolo che può rispondere ai ticket, se è stato configurato
        if guild.id in ticket_roles:
            role = guild.get_role(ticket_roles[guild.id])
            if role:
                await ticket_channel.set_permissions(role, read_messages=True, send_messages=True)

        # Creiamo il pulsante per chiudere il ticket
        view = discord.ui.View()
        close_button = discord.ui.Button(label="🔒 Chiudi Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
        view.add_item(close_button)

        await ticket_channel.send(f"{user.mention} Il tuo ticket è stato creato! Un membro dello staff ti risponderà presto.", view=view)
        
        await interaction.response.send_message(f"✅ Ticket aperto! Controlla {ticket_channel.mention}.", ephemeral=True)

    elif interaction.data["custom_id"] == "close_ticket":
        await interaction.channel.delete()


bot.run(TOKEN)
