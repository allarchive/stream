import discord
from discord.ext import commands
import http.client
import json
import asyncio
import random
from datetime import datetime, timedelta

# tworzenie połączenia HTTP do Auth0
conn = http.client.HTTPSConnection("dev-qnrg1sv6bi45l6bs.us.auth0.com")
payload = "{\"client_id\":\"WzHyhyEuD5sxdAFkkQF8ER4POJlPnKTK\",\"client_secret\":\"JcRMnkERSqmotdK0H0qePfE8Vk7uSv0Zi6l_1s3j_aGMo3H6b6JuhFanjZxv8j1I\",\"audience\":\"https://dev-qnrg1sv6bi45l6bs.us.auth0.com/api/v2/\",\"grant_type\":\"client_credentials\"}"
headers = { 'content-type': "application/json" }
conn.request("POST", "/oauth/token", payload, headers)
res = conn.getresponse()
data = res.read()

# funkcja dodająca użytkownika do Auth0
def add_user_to_auth0(email, password):
    conn = http.client.HTTPSConnection("dev-qnrg1sv6bi45l6bs.us.auth0.com")
    payload = "{\"email\":\"" + email + "\",\"password\":\"" + password + "\",\"connection\":\"Username-Password-Authentication\"}"
    headers = { 'content-type': "application/json", 'authorization': "Bearer " + json.loads(data.decode("utf-8"))['access_token'] }
    conn.request("POST", "/api/v2/users", payload, headers)
    res = conn.getresponse()
    if res.status == 201:
        return True
    else:
        return False

# obsługa komendy !dodaj



client = commands.Bot(command_prefix="?", intents=discord.Intents().all())
@commands.has_any_role('Administrator', 'STAFF')
@client.command()
async def dodaj(ctx, email: str, password: str):
    if isinstance(ctx.channel, discord.DMChannel):
        if len(email) == 0 or len(password) == 0:
            await ctx.send('Podaj poprawne dane logowania')
        else:
            if add_user_to_auth0(email, password):
                response_message = f'Twoje konto {email} zostało zarejestrowane.'
            else:
                response_message = 'Wystąpił błąd.'

            # wysyłanie wiadomości odpowiedzi
            response = await ctx.send(response_message)

            # usuwanie wiadomości po minucie
            await asyncio.sleep(10)

    else:
        await ctx.message.delete()
        await ctx.author.send('Zarejestrować możesz się jedynie w prywatnej wiadomości z botem. Użyj tutaj komendy.')
        await asyncio.sleep(5)
        await client.user.delete_message(ctx.author.dm_channel.last_message)
        await client.user.delete_message(ctx.message)

@client.command()
async def rej(ctx, email: str, password: str):
    if not check_cooldowns(str(ctx.author.id)):
        await ctx.send(
            "Niestety, ale juz wyslales prosbe o zarejstrowanie, jezeli cos zle wpisales napisz na kanale <#997564202044633238>.")
        return

    author = ctx.message.author
    role_names = [role.name for role in author.roles]
    if "Index Access" in role_names:
        destination_channel_id = 1069256725229731850
    elif "Nitro Booster" in role_names:
        destination_channel_id = 1069280134613454909
    else:
        await ctx.send("Nie posiadasz odpowiedniej roli, aby uzyc tej komendy.")
        return

    destination_channel = client.get_channel(destination_channel_id)
    embed = discord.Embed(title="Nowa rejstracja", description=f"Email: {email}\nHasło: {password}", color=0xff0000)
    message = await destination_channel.send(content=ctx.message.author.mention, embed=embed)
    await message.add_reaction('✅')

    try:
        reaction, user = await client.wait_for('reaction_add', timeout=604800, check=lambda reaction, user: str(reaction.emoji) == '✅' and reaction.message.id == message.id)
    except asyncio.TimeoutError:
        await ctx.send('Czas na potwierdzenie reakcją minął.')
        return

    if add_user_to_auth0(email, password):
        await ctx.send(f'Konto {email} zostało zarejestrowane.')
        await author.send(f'Twoje konto {email} zostało pomyślnie zarejestrowane.')
    else:
        await ctx.send('Wystąpił błąd podczas rejestracji | Wykonaj rejestracje manualnie.')


def check_cooldowns(user_id):
    try:
        with open("cooldown.json", "r") as f:
            cooldowns = json.load(f)
    except:
        cooldowns = {}

    now = datetime.utcnow()
    last_use = cooldowns.get(user_id, None)
    if last_use is None:
        cooldowns[user_id] = now.strftime("%Y-%m-%d %H:%M:%S")
        with open("cooldown.json", "w") as f:
            json.dump(cooldowns, f)
        return True
    elif (now - datetime.strptime(last_use, "%Y-%m-%d %H:%M:%S")).days >= 365:
        cooldowns[user_id] = now.strftime("%Y-%m-%d %H:%M:%S")
        with open("cooldown.json", "w") as f:
            json.dump(cooldowns, f)
        return True
    else:
        return False

@client.command()
@commands.has_any_role('Administrator', 'STAFF')
async def zezwol(ctx, user_id: int):
    try:
        with open("cooldown.json", "r") as f:
            cooldowns = json.load(f)
    except:
        cooldowns = {}

    if str(user_id) in cooldowns:
        del cooldowns[str(user_id)]
        with open("cooldown.json", "w") as f:
            json.dump(cooldowns, f)
        await ctx.send(f"Użytkownik o <@{user_id}> może ponownie się zarejestrować.")
        user = await client.fetch_user(user_id)
        await user.send("Możesz się ponownie zarejestrować. Wpisz teraz poprawnie dane do zarejestrowania!")
    else:
        await ctx.send(f"Użytkownik się jeszcze nie rejestrował.")

@client.command()
@commands.has_any_role("Index Access", "Nitro Booster")
async def link(ctx):
    embed=discord.Embed(title="PIRATEFILMS - KLIKNIJ", url="https://pay.piratefilms.gq/", description="**Nigdy nie udostępniaj nikomu linku oraz swoich danych logowania!**", color=0xff0000)
    embed.set_image(url="https://media.discordapp.net/attachments/938336404998594593/1002584282008653874/20220709_122224.png")
    try:
        await ctx.author.send(embed=embed)
        await ctx.send("Wysłano prywatną wiadomość.")
    except:
        await ctx.send(f"{ctx.author.mention}, nie udało się wysłać prywatnej wiadomości.")

@client.command()
async def kanal(ctx):
    user = ctx.message.author
    guild = ctx.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True)
    }
    channel = await guild.create_text_channel(f"rejstracja-{user.name}", overwrites=overwrites)
    await ctx.send(f"Stworzono kanal prywatny: {channel.mention}")
    await channel.send("Masz 5 minut na zarejstrowanie sie! Przyklad rejstracji **?rej twojemail@wp.pl TwojeHaslo123**")
    await asyncio.sleep(300) # czekaj 5 minut (300 sekund)
    await channel.delete()

# uruchomienie bota
client.run('MTA0OTQxNTQ5NjEwNzI5NDgzMQ.GWpE0e.4-H6DtqY5jRgGu4n6nJlQuYhQU9TsdxBrERwUM')
