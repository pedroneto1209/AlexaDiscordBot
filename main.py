import asyncio
import os

import classes
import functions

import sys
import discord
from discord.ext import commands
from discord.utils import get

import youtube_dl
import lxml
import urllib.request
from time import sleep
from random import choice
from random import shuffle
from lxml import etree


def run():

	# Suppress noise about console usage from errors
	youtube_dl.utils.bug_reports_message = lambda: ''


	ytdl_format_options = {
		'format': 'bestaudio/best',
		'outtmpl': './musics/%(extractor)s-%(id)s-%(title)s.%(ext)s',
		'restrictfilenames': True,
		'noplaylist': True,
		'nocheckcertificate': True,
		'ignoreerrors': False,
		'logtostderr': False,
		'quiet': True,
		'no_warnings': True,
		'default_search': 'auto',
		'max_filesize': 100000000,
		'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
	}

	ffmpeg_options = {
		'options': '-vn'
	}

	ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

	#List that has the sames lenght as the actual connected guilds
	glds = []

	class YTDLSource(discord.PCMVolumeTransformer):
		def __init__(self, source, *, data, volume=0.5):
			super().__init__(source, volume)

			self.data = data
			
			self.title = data.get('title')
			self.url = data.get('url')
		
		#Generates a player
		@classmethod
		async def from_url(cls, url, *, loop=None):
			ytdl.download([url])
			data = ytdl.extract_info(url, download = True)
		
			filename = data['url'] if False else ytdl.prepare_filename(data)

			if not os.path.exists(filename):
				return 10			
				
			return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


	class General(commands.Cog):
		def __init__(self, bot):
			self.bot = bot

		#Sends embed message in the guild chat
		async def send_embed(self, ctx, description: str):
			embed = discord.Embed(description = description
			, colour = discord.Colour.gold())
			msg = await ctx.send(embed=embed)
			await asyncio.sleep(60)
			await msg.delete()

		#Verifies the voice situations of the author/bot
		async def channel_verify(self, ctx):
			author_voice_state = ctx.message.author.voice
			
			if not author_voice_state:
				text = 'You need to be in a channel!'
				await self.send_embed(ctx, text)
				return False

			voice = get(bot.voice_clients, guild = ctx.guild)

			if voice is None:
				text = "I'm not in any channel!"
				await self.send_embed(ctx, text)
				return False			
			
			if voice.channel != ctx.message.author.voice.channel:
				text = "I'm already at another channel in this guild!"
				await self.send_embed(ctx, text)
				return False

			return True

		#Returns the link of a video through his name
		async def get_url(self, ctx):
			entry = ctx.message.content.split()
			entry.pop(0)
			url = ''

			for i in range(len(entry)):
				url = url + entry[i]
				if i != len(entry) - 1:
					url = url + ' '

			if not url.startswith('https://') and not url.startswith('http://'):
				with ctx.typing():
					loop = asyncio.get_event_loop()
					data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download= False))
					if 'entries' in data:
						# take first item from a playlist
						data = data['entries'][0]
					else:
						return

				return data['webpage_url']

			return url

		#Show actual list of the next musics on the queue
		async def show_queue(self, ctx):

			obj = get_object(ctx)		

			if len(obj.queues) == 0:
				text = 'There is nothing in the queue!!'
				await self.send_embed(ctx, text)
				return

			description = ''
			for i in range(len(obj.queues)):
				added = obj.queues[i]['title']
				description = description + f'*{i + 1}°*- **{added}** :notes:'
				if i != len(obj.queues) - 1:
					description = description + '\n'

			queue_list = discord.Embed(
			title = 'List of upcoming songs:',
			description = description,
			colour = discord.Colour.gold())

			msg = await ctx.send(embed=queue_list)
			await asyncio.sleep(60)
			await msg.delete()

		#Plays the music received from an url
		async def play_music(self, ctx, url):
			async with ctx.typing():
				player = await YTDLSource.from_url(url, loop=self.bot.loop)
			if player != 10:		
				ctx.voice_client.play(player, after= lambda e: clear_music())
				text = f'**Playing** :notes: **`{player.title}`**'
				await ctx.send(text)
				print(f'Just played <{player.title}> for <{ctx.author}> at the <{ctx.guild}>')
					
			else:
				text = f'The song you are trying to play is too big!'
				await self.send_embed(ctx, text)
				print(f'<{ctx.author}> tried to play a oversized song at the <{ctx.guild}>: <{url}>')

			obj = get_object(ctx)

			voice = get(bot.voice_clients, guild=ctx.guild)

			p_duration = player.data.get('duration')

			await asyncio.sleep(p_duration)

			if len(obj.queues) != 0 and not voice.is_playing():
				upcoming = obj.queues[0]['webpage_url']
				await obj.to_remove()
				await self.play_music(ctx, upcoming)


		#Join the author's voice channel
		@commands.command()
		async def join(self, ctx):
			author_voice_state = ctx.message.author.voice

			#Checks if the author is in a voice channel
			if not author_voice_state:
				text = 'You need to be in a voice channel!'
				await self.send_embed(ctx, text)
				return

			current_channel = get(bot.voice_clients, guild = ctx.guild)
			author_channel = ctx.message.author.voice.channel
			

			if current_channel == None:
				print(f'Connected to <{author_channel}>', end = '')
				functions.log_ctx(ctx)
				await author_channel.connect()
			elif current_channel.channel != author_channel:
				text = 'I am already in another channel in this server!'
				await self.send_embed(ctx, text)
			else:
				text = 'I am already in your channel'
				await self.send_embed(ctx, text)

		#Command that starts the process of playing a music
		@commands.command()
		async def play(self, ctx):
			'''Plays a Youtube video!'''
			test = ctx.message.content.split()
			if len(test) == 1:
				text = 'You need to type the music name/link on youtube!'
				await self.send_embed(ctx, text)
				return
					
			if not await self.channel_verify(ctx):
				return			

			url = await self.get_url(ctx)
			await self.play_music(ctx, url)

		#Returns all the information of a video through an url
		def from_queue(self, url):
			data = ytdl.extract_info(url, download = True)
			return data

		#Adds a music to the queue/Show the queue
		@commands.command()
		async def queue(self, ctx):
			test = ctx.message.content.split()
			if len(test) == 1:
				await self.show_queue(ctx)
				return

			if not await self.channel_verify(ctx):
				return

			url = await self.get_url(ctx)
			url_data = self.from_queue(url)
			
			#Get the object that represents the actual guild
			obj = get_object(ctx)

			#Checks if the requested song is already in the queue
			for data in obj.queues:
				if data['webpage_url'] == url_data['webpage_url']:
					text = 'This song is already in the queue!'
					await self.send_embed(ctx, text)
					return
			
			#Gets the music name from the data
			music_name = url_data['title']
			
			await obj.to_put(url_data)
			text = f'Now **{music_name}** is in the queue!'
			await self.send_embed(ctx, text)

		#Plays the queue songs
		@commands.command()
		async def qplay(self, ctx):
			obj = get_object(ctx)

			if not await self.channel_verify(ctx):
				return
			
			#Checks if the queue is empty
			elif len(obj.queues) != 0:
				upcoming = obj.queues[0]['webpage_url']
				await obj.to_remove()
				await self.play_music(ctx, upcoming)
			else:
				text = 'There is no more songs in the queue'
				await self.send_embed(ctx, text)

		#Clears the actual queue
		@commands.command()
		async def clear(self, ctx):
			obj = get_object(ctx)
			obj.queues.clear()
			clear_music()
			text = 'Got the queue cleared.'
			await self.send_embed(ctx, text)
		
		#Shuffle the actual queue
		@commands.command()
		async def shuffle(self, ctx):
			obj = get_object(ctx)

			if len(obj.queues) == 0:
				text = 'There is no more songs in the queue'
				await self.send_embed(ctx, text)
				return

			await obj.to_shuffle()
			text = 'Just shuffled the queue!'
			await self.send_embed(ctx, text)		

		#Skip the current song
		@commands.command()
		async def skip(self, ctx):
			obj = get_object(ctx)
			voice = get(bot.voice_clients, guild = ctx.guild)

			if not await self.channel_verify(ctx):
				return

			#Checks if the bot is playing something
			elif not voice.is_playing():
				text = 'I am not playing anything'
				await self.send_embed(ctx, text)
			
			#Checks if the queue is empty
			elif len(obj.queues) == 0:
				ctx.voice_client.stop()
				text = 'Skipped it, but there is nothing more in the queue'
				await self.send_embed(ctx, text)
			
			#Plays the next song
			else:
				ctx.voice_client.stop()
				upcoming = obj.queues[0]['webpage_url']
				await obj.to_remove()
				await self.play_music(ctx, upcoming)

		#Calls the leave function
		@commands.command()
		async def stop(self, ctx):
			obj = get_object(ctx)
			await obj.to_clear()

			channel = ctx.message.author.voice.channel
			voice = get(bot.voice_clients, guild=ctx.guild)
			
			if voice and voice.is_connected():
				print(f'Disconnected from {channel}', end = '')
				functions.log_ctx(ctx)
				await voice.disconnect()
			else:
				text = f'I was not at the {channel}.'
				await self.send_embed(ctx, text)

		#Calls the leave function
		@commands.command()
		async def leave(self, ctx):
			obj = get_object(ctx)
			await obj.to_clear()

			channel = ctx.message.author.voice.channel
			voice = get(bot.voice_clients, guild=ctx.guild)
			
			if voice and voice.is_connected():
				print(f'Disconnected from {channel}', end = '')
				functions.log_ctx(ctx)
				await voice.disconnect()
			else:
				text = f'I was not at the {channel}.'
				await self.send_embed(ctx, text)

		#Prints all the commands/Help
		@commands.command()
		async def command(self, message):
			print('Help message sent', end = '')
			functions.log(message)
			cmd = discord.Embed(title = 'Commands', colour = discord.Colour.blue())

			cmd.add_field(name = 'I am your bot!', value = help_str)
			msg = await message.channel.send(embed = cmd)
			await asyncio.sleep(60)
			await msg.delete()

		#Draw two teams
		@commands.command()
		async def draw(self, ctx):
			C = ctx.message.content.split()
			C = C[1:]
			shuffle(C)

			if len(C) == 6:
				print('Made a 3x3 draw', end = '')
				functions.log_ctx(ctx)

				await ctx.send('So it is a 3x3 draw, wait a second.')
				sleep(2)
				embed1 = discord.Embed(title = 'This is the first team!', colour = discord.Colour.blue())
				embed1.add_field(name = 'Players', value = ' \n- {}\n\n- {}\n\n- {}'.format(C[0], C[1], C[2]))

				embed2 = discord.Embed(title = 'This is the second team!', colour = discord.Colour.red())
				embed2.add_field(name = 'Players', value = ' \n- {}\n\n- {}\n\n- {}'.format(C[3], C[4], C[5]))

				await ctx.send(embed = embed1)
				await ctx.send(embed = embed2)

			elif len(C) == 8:
				print('Made a 4x4 draw', end = '')
				functions.log_ctx(ctx)

				await ctx.send('So it is a 4x4 draw, wait a second.')
				sleep(2)
				embed1 = discord.Embed(title = 'This is the first team!', colour = discord.Colour.blue())
				embed1.add_field(name = 'Players', value = ' \n- {}\n\n- {}\n\n- {}\n\n- {}'.format(C[0], C[1], C[2], C[3]))

				embed2 = discord.Embed(title = 'This is the second team!', colour = discord.Colour.red())
				embed2.add_field(name = 'Players', value = ' \n- {}\n\n- {}\n\n- {}\n\n- {}'.format(C[4], C[5], C[6], C[7]))

				await ctx.send(embed = embed1)
				await ctx.send(embed = embed2)

			elif len(C) == 10:
				print('Made a 5x5 draw', end = '')
				functions.log_ctx(ctx)

				await ctx.send('So it is a 5x5 draw, wait a second.')
				sleep(2)
				embed1 = discord.Embed(title = 'This is the first team!', colour = discord.Colour.blue())
				embed1.add_field(name = 'Players', value = ' \n- {}\n\n- {}\n\n - {}\n\n- {}\n\n- {}'.format(C[0], C[1], C[2], C[3], C[4]))

				embed2 = discord.Embed(title = 'This is the second team!', colour = discord.Colour.red())
				embed2.add_field(name = 'Players', value = ' \n- {}\n\n- {}\n\n- {}\n\n- {}\n\n- {}'.format(C[5], C[6], C[7], C[8], C[9]))

				await ctx.send(embed = embed1)
				await ctx.send(embed = embed2)
			else:
				print('Invalid draw', end = '')
				functions.log_ctx(ctx)
				text = 'Invalid quantity of people'
				await self.send_embed(ctx, text)

		#Plays Heads or Tails
		@commands.command(pass_context=True)
		async def coin(self, ctx):
			'''Jogarei a moeda pra você, fi!'''
			print('Thrown a coin', end = '')
			functions.log_ctx(ctx)
			await ctx.send(choice(cc))

	##########################################################################################
	##########################################################################################
		
		#Makes shure the author is in a channel, and raises a error if he is not
		@play.before_invoke
		async def ensure_voice(self, ctx):
			if ctx.voice_client is None:
				if ctx.author.voice:
					await ctx.author.voice.channel.connect()
				else:				
					text = 'You need to be in a channel'
					await self.send_embed(ctx, text)
					raise commands.CommandError(f'{ctx.author} is not connected to any channel.')
			elif ctx.voice_client.is_playing():
				ctx.voice_client.stop()

	bot = commands.Bot(command_prefix=commands.when_mentioned_or("*&"))

	#Clear the music directory
	def clear_music():
		print(f'Deleting all songs!')
		x = os.listdir('./musics')
		for i in range(len(x)):
			os.remove('./musics/'+x[i])

	#Is activated in each member join
	@bot.event
	async def on_member_join(member):
		print(f'<{member}> entrou no <{member.guild}>!')

		#Boas-vindas ao server
		
		embed = discord.Embed(title = f'Bem-vindo ao {member.guild}!!', colour = discord.Colour.gold())
		boasvindas = f'''
			The {member.mention} just joined our server.\nYou are welcome!\n
		'''

		embed.set_image(url = 'https://media.tenor.com/images/f022eb062fa10d64491efb61c86520fc/tenor.gif')
		embed.add_field(name = 'I am your bot!!', value=f'{boasvindas}\n\n')
		await member.guild.text_channels[0].send(embed = embed)
		

	#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	#Is activated when the bot starts
	@bot.event
	async def on_ready():
		
		print(f'{bot.user} is online in discord!')
		print('=-=-=-=-=-=--=-=-=-=-=-=-=-=-=')
		
		await create_queues()
		await change_status()

		
	#Create a object that will be used to keeps the guild id and a queue list
	async def create_queues():
		for i in range(len(bot.guilds)):
			glds.append('')
			glds[i] = classes.AllGuilds(bot.guilds[i].id)

	#Change the bot status
	async def change_status():
		stts = discord.Activity(name = 'Type =command', type = 3)
		await bot.change_presence(status=discord.Status.idle, activity = stts)

	#Get the object from the server id
	def get_object(ctx):
		return get(glds, id = ctx.guild.id)

	#Heads or Tails list
	cc = functions.cc()

	help_str = functions.help_str()
	
	TOKEN = functions.get_token()
	bot.add_cog(General(bot))
	bot.run(TOKEN)


if __name__ == '__main__':
	run()