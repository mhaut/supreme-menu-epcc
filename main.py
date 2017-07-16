# coding=utf-8
import telebot
import tweepy
import os, sys
import glob
import time
from tweepy import OAuthHandler
import json
import copy


class tuiter_manager(object):
	def __init__(self, tokens_tuiter):
		self.platos = {}
		auth = OAuthHandler(tokens_tuiter["consumer_key"], tokens_tuiter["consumer_secret"])
		auth.set_access_token(tokens_tuiter["access_token"], tokens_tuiter["access_secret"])
		self.twitter = tweepy.API(auth)


	def check_update_dishes(self, initial_tuit):
		distance_between_updates = initial_tuit.created_at.day - time.gmtime()[2]
		return distance_between_updates


	def process_dishes(self,lista_tweets):
		offset = 11
		platos = ["Segundos_hoy","Primeros_hoy","Segundos_ayer","Primeros_ayer"]
		for i, id_plato in zip(range(4), platos):
			self.platos[platos[i]] = lista_tweets[i].text[offset:].split(', ')


	def get_dishes(self):
		lista_tweets = list(tweepy.Cursor(self.twitter.user_timeline, id="cafeteriaEPCC").items(4))
		update_dishes = self.check_update_dishes(lista_tweets[0])
		if (update_dishes == 0):
			resultado = "MENÚ ACTUALIZADO HOY"
		elif (update_dishes == -1):
			resultado = "MENÚ ACTUALIZADO AYER, PENDIENTE DE ACTUALIZACIÓN"
		else:
			resultado = "HOY NO HAY MENÚ, O NO ESTA ACTUALIZADO"
		self.process_dishes(lista_tweets)
		return resultado, self.platos



class telegram_manager(object):
	def __init__(self, tokens_telegram, tuiter_manager):
		self.tm  = tuiter_manager
		self.bot = telebot.TeleBot(tokens_telegram["API_TOKEN"])

		@self.bot.message_handler(commands=["menu"])
		def reply(message):
			resultado, platos = self.tm.get_dishes()
			respuesta = self.construir_respuesta(resultado, platos, repetidos=False)
			self.bot.reply_to(message, respuesta)

		@self.bot.message_handler(commands=["calentitos"])
		def reply_juanker(message):
			resultado, platos = self.tm.get_dishes()
			respuesta = self.construir_respuesta(resultado, platos, repetidos=True)
			self.bot.reply_to(message, respuesta)

		@self.bot.message_handler(commands=["nuevo_menu"])
		def reply_juanker(message):
			self.bot.send_message(message, "Dime los primeros separados por comas")
			
			resultado, platos = self.tm.get_dishes()
			respuesta = self.construir_respuesta(resultado, platos, repetidos=True)
			self.bot.reply_to(message, respuesta)


		self.bot.polling()


	def construir_respuesta(self, resultado, platos, repetidos=False):

		for dia_plato in ["Primeros", "Segundos"]:
			resultado += "\n" + dia_plato + "\n"
			for x in (set(platos[dia_plato + "_hoy"])):
				resultado += "  - " + x.encode('UTF-8').title() + "\n"

		if repetidos == True:
			resultado += "\n \n ---------- REPETIDOS --------- \n"
			for x in (set(platos["Primeros_hoy"]) & set(platos["Primeros_ayer"]))\
							| (set(platos["Segundos_hoy"]) & set(platos["Segundos_ayer"])):
				resultado = resultado.replace("  - " + x.encode('UTF-8').title() + "\n", "",1)
				resultado += "  - " + x.encode('UTF-8').title() + "\n"

		resultado += "\n \n  ¡¡¡ BUEN PROVECHO !!!"

		return resultado




if __name__ == "__main__":
	params = copy.deepcopy(sys.argv)
	if len(params) > 1:
		if not params[1].startswith('--Init.Config='):
			params[1] = '--Init.Config=' + params[1]
	elif len(params) == 1:
		params.append('--Init.Config=etc/config.json')

	filepath = params[1].split("=")[1]
	if os.path.isfile(filepath):
		if not ".json" in filepath:
			print("Error: only json format is supported")
		else: # file exist and is json
			with open(filepath) as data_file:
				config_bot = json.load(data_file)
	else:
		print("file " + filepath + " not found!")


	tokens_tuiter   = config_bot["tokens"]["tuiter"]
	tokens_telegram = config_bot["tokens"]["telegram"]

	tm = tuiter_manager(tokens_tuiter)
	tg = telegram_manager(tokens_telegram, tm)
