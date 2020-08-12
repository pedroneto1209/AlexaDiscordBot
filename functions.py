import os
import bot_music

def help_str():
    return '''
			• Type **=play** *<song/youtube link>* and i'll play a music at the voice channel.
			• Type **=skip** to skip the music.
			• Type **=join** and i'll join your voice channel.
			• Type **=leave** or **=stop** and i'll leave the voice channel.
			• Type **=queue** *<song/youtube link>* to add a music to the queue.
				***Comandos da queue:***
				- Type **=qplay** to play the queue, if it have not started yet.
				- Type only **=queue** to show the actual situation of the queue.
				- Type **=clear** to clear the queue.
				- Type **=shuffle** to shuffle the queue.\n
			• Type **=coin** and i'll play Heads or Tails for you.
			•  Type **=draw** followed by 6, 8 or 10 names divided by blank space and i'll draw two teams for you.\n
			*- The **=play** skips the actual song, so respect the music that is already playing.*
			'''
		
def cc():
	return ['Tails!!', 'Heads!!']

def log(message):
	print(f' to <{message.author}> at the <{message.guild}>')

def log_ctx(ctx):
	print(f' to <{ctx.author}> at the <{ctx.guild}>')

def get_token():
	folder = os.path.dirname(os.path.abspath(__file__))
	data = os.path.join(f'{folder}', 'token.txt')
	archive = open(data, 'r')
	return archive.readline()