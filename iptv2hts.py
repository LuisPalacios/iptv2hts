#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ==========================================================================================
#
# iptv2hts.py - Generar configuración Tvheadend 3.9+ desde playlist IPTV M3U
#
# (c) 2015 Luis Palacios
#
# Fork del trabajo de Gregor Rudolf (https://github.com/grudolf/m3u2hts): 
#  - traducido al castellano,
#  - añadida documentación, 
#  - eliminado el soporte a versiones de tvheadend anteriores a 3.9+
#  - corregidos algunos bugs
#  - añadida la opción udpxy
#  - asegurado que inserta los canales de Movistar TV correctamente. 
#
# Licenciado bajo la licencia MIT:
# http://www.opensource.org/licenses/mit-license.php
#
# ==========================================================================================

# ==========================================================================================
#
# Importaciones
#
# ==========================================================================================
#
#
from optparse import OptionParser	# facilita la gestión de los argumentos de llamada
import codecs						# co/decodificar ficheros al leerlos/escribirlos
import re							# trabajar con Expresiones Regulares
import os							# acceso a funciones del sistema operativo
try:
	import json              		# Soporte al trabajo con ficheros JSON (lo usa Tvheadend)
except ImportError: 				# Si tienes una instalación de python antigua entonces
	import simplejson as json		# necesitarás hacer "easy_install simplejson"


# ==========================================================================================
#
# Atributos
#
# ==========================================================================================
#

# Expresión regular PROGNUM: Extraer el número del programa de #EXTINF. 
#
#	Si tenemos: 
# 		#EXTINF:-1,456 - TVE
#
#	Nos quedamos tras la coma y aplicamos expresión regular a "456 - TVE":
#		#1 = 456
#		#2 = TVE
#
PROGNUM = re.compile(r"(\d+) - (.*)")  

# Expresión regular URLPART: <definición>
#
#	Si tenemos: rtp://@x.x.x.x:yyy
#
#	Resultado: Divide en tres el resultado, dejando: 
#		#1 = rtp
#		#2 = x.x.x.x
#		#3 = yyy
#
URLPART = re.compile(r"^((?P<scheme>.+?)://@?)?(?P<host>.*?)(:(?P<port>\d+?))?$")

# De dónde coger el número del canal
#
CHAN_NUMBERING_GENERATE = 0			# Generar números de canal nuevos
CHAN_NUMBERING_DURATION = 1			# Utilizar el campo duración como número de canal
CHAN_NUMBERING_NAMES = 2			# Utilizar la parte izda. de núm - nombre como número de canal

# Diccionarios donde iré guardando los canales y los tags
#
canales = dict()
tags = dict()


# ==========================================================================================
#
# Muestra el contenido de una Lista, lo utilizo para debug
#
# ==========================================================================================
#
def printList(lista):
	print "--"
	for idx, val in enumerate(lista):
		print "["+str(idx)+"]", val
    

# ==========================================================================================
#
# Genera un número único
#
# ==========================================================================================
#
def uuid():
	import uuid
	return uuid.uuid4().hex

# ==========================================================================================
#
# Leer los canales IPTV desde el fichero .M3U
#
# ==========================================================================================
#
def readm3u(infile, removenum, channumbering, inputcodec):
	"""
	Leer los canales IPTV de un fichero .M3U
	@param infile: Fichero de entrada
	@param removenum: Quitar los números de los canales del nombre del canal
	@param channumbering: De dónde coger el número del canal
	@param inputcodec: Tipo de codificación del fichero fuente: cp1250, utf-8, ...
	"""

	# Leo el fichero .M3U
	#
	instream = codecs.open(infile, "Ur", encoding=inputcodec)
	
	#
	# Limpio todas las variables antes de empezar a parsear el fichero .M3U
	#
	chancnt = 0
	tagcnt = 0
	chname = ''
	chtags = None
	chlanguage = None
	chnumber = None
	chxmltv = None
	chicon = None
	for line in instream.readlines():

		# Elimino espacios al principio de la línea y quito el C/R al final
		line = line.strip()

		# Línea EXTINF
		#
		#	EXTINF:duración, número de canal - nombre del canal
		#
		if line.startswith("#EXTINF:"):

			#
			# buff[0]: duración
			# buff[1]: número de canal - nombre del canal
			#
			buff = line[8:].split(',')
			
			# Debug
			# printList(buff)
			
			# Expr. Regular, para dejar en chname el nombre del canal
			# Nota: Ejecutar con -r para quitar el número del nombre del canal
			# 
			# m.group(1): número del canal
			# m.group(2): nombre del canal
			#
			m = PROGNUM.search(buff[1])
			if removenum and m:
				chname = m.group(2)
			else:
				chname = buff[1]

			# Debug
			# print "Nombre del canal: " + chname

			if m and channumbering == CHAN_NUMBERING_NAMES:
				chnumber = m.group(1)
			elif channumbering == CHAN_NUMBERING_DURATION:
				chnumber = buff[0]
				
			# Debug
			# print "Número del canal: " + str(chnumber)


		# Línea EXTTV
		#
		#	EXTTV:tag[,tag,tag...];lenguaje;XMLTV id[;URL al icono]
		#   #EXTTV:POLICIACAS;es;FOXHD;http://172.26.22.23:2001/appclient/incoming/epg/MAY_1/imSer/1607.jpg
		#
		elif line.startswith('#EXTTV:'):

			#
			# buff[0]: tag[,tag,tag...]
			# buff[1]: lenguaje
			# buff[2]: XMLTV id
			# buff[3]: URL al icono
			#
			buff = line[7:].split(';')

			# Construyo el Diccionario de TAGS
			# :
			# u'ANIMACIÓN': {'num': 6, 'name': u'ANIMACIÓN'},
			# u'POLICIACAS': {'num': 7, 'name': u'POLICIACAS'},
			# :
			#
			chtags = buff[0].split(',')
			for t in chtags:
				if not t in tags:
					tagcnt += 1
					tags[t] = {'num': tagcnt, 'name': t}
					
			# Añado el lenguaje al Diccionario de TAGS
			# :
			# u'es': {'num': 3, 'name': u'es'}}
			# :
			#
			chlanguage = buff[1]
			if chlanguage:
				if not chlanguage in tags:
					tagcnt += 1
					tags[chlanguage] = {'num': tagcnt, 'name': chlanguage}
				chtags.append(chlanguage)
				
			# Me guardo el XMLTV ID (Es el id que se usa para identificar el EPG)
			# 
			#
			chxmltv = buff[2]

			# Me guardo el URL del icono
			# 
			#
			chicon = buff[3] if len(buff) > 3 else None
			
		# Línea Canal 
		#
		#	Será una URL con el formato rtp://... o http://
		#
		#
		else:
			# Analizo las líneas con formato rtp://@X.X.X.X:port
			#
			chgroup = re.search(URLPART, line).groupdict()
			if not chgroup or not chgroup["scheme"]:
				continue
			chancnt += 1
			if channumbering == CHAN_NUMBERING_GENERATE: chnumber = chancnt
			if chname in canales:
				print "%s already exists" % chname
				chname += '.'
			#
			# chgroup["scheme"] : rtp, http, ... 
			# chgroup["host"]   : dirección IP
			# chgroup["port"]   : puerto
			#
			canales[chname] = {'num': chancnt, 'number': chnumber, 'name': chname, 'tags': chtags, 'lang': chlanguage,
								'scheme': chgroup["scheme"], 'ip': chgroup["host"], 'port': chgroup["port"],
								'xmltv': chxmltv, 'icon': chicon}			
			#
			# Limpio variables para la siguiente iteracción
			#
			chname = ''
			chtags = None
			chlanguage = None
			chnumber = None
			chxmltv = None
			chicon = None


# ==========================================================================================
#
# Escribir toda la información dentro de Tvheadend
#
# ==========================================================================================
#
def writechannels(networkname, udpxy, iface, output):

	#
	# Estructura de directorios: 
	#
	#	input/iptv/config
	#	input/iptv/networks/UUID/config                      - Creará "IPTV network"
	#	input/iptv/networks/UUID/muxes/UUID/config           - Un mux por canal
	#	input/iptv/networks/UUID/muxes/UUID/services/UUID    - Un service (falso) por canal (opción -o service)
	#	channel/tag/UUID                                     - Tags de los canales
	#	channel/config/UUID                                  - Canales (asociados a los servicios y tags, opción -o channel)
	#	epggrab/xmltv/channels/UUID                          - Información EPG (asociada al canal), opción -o channel
	#
	
	#
	#   Información EPG (asociada al canal), opción -o channel
	#
	xmltvpath = "epggrab/xmltv/channels"
	if not os.path.exists(xmltvpath):
		os.makedirs(xmltvpath)

	tagpath = 'channel/tag'
	if not os.path.exists(tagpath):
		os.makedirs(tagpath)

	chnpath = 'channel/config'
	if not os.path.exists(chnpath):
		os.makedirs(chnpath)

	#channel/tag/UUID
	for tag in tags.values():
		tag['id'] = uuid()
		jstag = {'enabled': 1,
				 'internal': 0,
				 'titledIcon': 0,
				 'name': tag['name'],
				 'comment': '',
				 'icon': ''}
		writejson(os.path.join(tagpath, tag['id']), jstag)



	#input/iptv
	path = os.path.join('input', 'iptv')
	if not os.path.exists(path):
		os.makedirs(path)
	#input/iptv/config
	writejson(os.path.join(path, 'config'), {
		'uuid': uuid(),
		'skipinitscan': 1,
		'autodiscovery': 0
	})

	# Network
	#	input/iptv/networks/uuid()
	#
	path = os.path.join(path, 'networks', uuid())
	if not os.path.exists(path):
		os.makedirs(path)
	writejson(os.path.join(path, 'config'), {
		"priority": 1,
		"spriority": 1,
		"max_streams": 2,				# Max input streams (afterwards change to 0)
		"max_bandwidth": 0,				# Max bandwidth (Kbps)
		"max_timeout": 10,				# Max timeout (seconds)
		"networkname": networkname,		# Network name
		"nid": 0,
		"autodiscovery": "true",		# Network discovery
		"skipinitscan": "true",			# Skip initial scan
		"idlescan": "true",				# Idle scan (after sacnning change to 0)
		"sid_chnum": "false",
		"ignore_chnum": "false",
		"localtime": "false"
	})
	

	#input/iptv/networks/uuid()/muxes
	path = os.path.join(path, 'muxes')
	if not os.path.exists(path):
		os.mkdir(path)
	#one mux and service for each channel
	for channel in canales.values():
		muxid = uuid()
		muxpath = os.path.join(path, muxid)
		if not os.path.exists(muxpath):
			os.mkdir(muxpath)
		if channel['port']:
			if udpxy is not None:
				# http://192.168.1.1:4022/udp/C.C.C.C:PPPP
				#  "iptv_url": "http://['192.168.1.1:4022']/udp/239.0.5.74:8208"
				url = "http://%s/udp/%s:%s" % (udpxy, channel['ip'], channel['port'])
			else:
				url = "%s://@%s:%s" % (channel['scheme'], channel['ip'], channel['port'])
		else:
			if udpxy is not None:
				# http://192.168.1.1:4022/udp/C.C.C.C
				url = "http://%s/udp/%s" % (udpxy, channel['ip'])
			else:
				url = "%s://@%s" % (channel['scheme'], channel['ip'])
		jsmux = {
			'iptv_url': url,
			'iptv_interface': iface,
			'iptv_atsc': 0,
			'iptv_svcname': channel['name'],
			'iptv_muxname': channel['name'],
			'iptv_sname': channel['name'],
			'enabled': 1,
			'scan_result': 2  # mark scan result (1 - ok, 2 - failed)
		}
		#input/iptv/networks/uuid()/muxes/uuid()/config file
		writejson(os.path.join(muxpath, 'config'), jsmux)
		#input/iptv/networks/uuid()/muxes/uuid()/services/uuid()
		svcpath = os.path.join(muxpath, 'services')
		if not os.path.exists(svcpath):
			os.mkdir(svcpath)

		#create empty service with id 0
		svcid = None
		if output is not None:
			if 'servicios' in output:
				svcid = uuid()
				jssvc = {
					'sid': 0,	# guess service id
					'svcname': channel['name'],
					'name': channel['name'],
					'dvb_servicetype': 1,
					'enabled': 1
				}
				writejson(os.path.join(svcpath, svcid), jssvc)
			else:
				svcid = None

			#channel/config
			if 'canales' in output:
				chanid = uuid()
				jschan = {
					'name': channel['name'],
					'dvr_pre_time': 0,
					'dvr_pst_time': 0,
					'services': [svcid]
				}
				if channel['number'] is not None:
					jschan['number'] = int(channel['number'])
				if channel['tags'] is not None:
					jschan['tags'] = list(tags[x]['id'] for x in channel['tags'])
				if channel['icon'] is not None:
					jschan['icon'] = channel['icon']
				writejson(os.path.join(chnpath, chanid), jschan)

				#epg
				#epggrab/xmltv/channels/#
				if channel['xmltv'] is not None:
					xmlid = channel['xmltv']
				else:
					xmlid = channel['name']
				jsepg = {
					'name': xmlid,
					'channels': [chanid]
				}
				writejson(os.path.join(xmltvpath, chanid), jsepg)


# ==========================================================================================
#
# Guardar el contenido del objeto 'obj' en un fichero y hacerlo en formato JSON
#
# ==========================================================================================
#
def writejson(filename, obj):
	"""
	Export obj to filename in JSON format
	@param filename: output file
	@param obj: object to export
	"""
	outstream = codecs.open(filename, "w", encoding='utf-8')
	json.dump(obj, outstream, indent=4, ensure_ascii=False)
	outstream.close()


# ==========================================================================================
#
# Entrada principal al programa
#
# ==========================================================================================
#
def main():

	# Parser para facilitar la interpretación de los argumentos
	#
	#
	par = OptionParser(	usage="%prog [opciones] fichero_m3u", 
						add_help_option=False,
						description="Generar configuración Tvheadend 3.9+ desde playlist IPTV M3U".decode('utf8'))

	# -h
	# --help:		Versión traducida 
	#
	par.add_option("-h", "--help",
					action="help",
					help=("Mostrar este mensaje de ayuda y salir"))

	# -r
	# --removenum:	Eliminar el número del canal de su nombre, de modo que el nombre del 
	#				canal no tenga ningún número delante. 
	#
	#				Valor por defecto: Se deja el número junto con el nombre
	#
	par.add_option('-r', '--removenum', action='store_true', help='Elimina el número del programa de su nombre'.decode('utf8'))

	# -n
	# --numbering:	Indicar qué tipo de numeración queremos pre-establecer a los canales. 
	#				Si pasamos 0 significa que dejamos a este script crear una numeración
	#				incremental según analiza los canales. Si por otro lado indicamos
	#				la opción '1' estamos pidiendo que saque el número de canal desde el 
	#				valos "duración" en el EXTINF. Por último si empleamos la opción '2' que
	#				es la de por defecto, estamos indicando que use el "número de canal"
	#				de la línea EXTINF (EXTINF:duración, número de canal - nombre del canal)
	#
	#				Valor por defecto: 2  (Extraer el número antes del "- nombre del canal")
	#
	par.add_option('-n', '--numbering', type='int', default=2,
					help='0=generar, 1=duración, 2=nombre [def.: %default]'.decode('utf8'))

	# -c
	# --codec:		Identificar que tipo de codificación tiene el fichero .M3U. Lo normal
	#				hoy en día es que sea UTF-8, pero podría ser ascii o cualquier otra...
	#
	#				Valor por defecto: utf-8
	#
	par.add_option('-c', '--codec', action='store', dest='codec', default='utf-8',
				   help='Codificacion del fichero [def.: %default]'.decode('utf8'))

	# -i
	# --iface:		Identificar el nombre del interfaz linux por el cual se buscarán
	#				las fuentes multicast. Por defecto se utilizará 'eth0'. Si empleas
	#				la opción --udpxy puedes dejar cualquier nombre de interfaz porque
	#				Tvheadend no lo empleará (con udpxy se usa http)
	#
	#				Valor por defecto: eth0
	#
	par.add_option('-i', '--iface', action='store', dest='iface', default='eth0',
				   help='Nombre de la interfaz IPTV [def.: %default]'.decode('utf8'))
	# -x
	# --udpxy:		Utilizar esta opción para definir la dirección o el nombre DNS de
	# 				un servidor "udpxy". Si tienes dicho servicio en tu casa te permite
	#				hacer relay del tráfico multicast UDP hacia clientes TCP (HTTP). En 
	#				ese caso te puede interesar que Tvheadend lo utilice, en vez de RTP. 
	#
	#				Valor por defecto: NONE
	#
	par.add_option('-x', '--udpxy', action='store', type='string', dest='udpxy',
				   help='Dirección o nombre DNS de tu servidor udpxy'.decode('utf8'))

	# -n
	# --networkname:Utilizar esta opción para definir la dirección o el nombre DNS de
	# 				un servidor "udpxy". Si tienes dicho servicio en tu casa te permite
	#				hacer relay del tráfico multicast UDP hacia clientes TCP (HTTP). En 
	#				ese caso te puede interesar que Tvheadend lo utilice, en vez de RTP. 
	#
	#				Valor por defecto: NONE
	#
	par.add_option('-k', '--networkname', action='append', type='string', dest='networkname', default='IPTV Movistar',
				   help='Nombre de la IPTV Network [def.: %default]'.decode('utf8'))

	# -o
	# --output:		Indica qué tipo de información generar además de los muxes. Podemos
	#				elegir entre 'servicio' para que se generen servicios fake o bien
	#				podemos poner 'canal', o bien podemos poner ambos para que se 
	#				combinen.
	#
	#				Valor por defecto: none
	#
	par.add_option('-o', '--output', action='append', type='string', dest='output',
				   help='Qué tipo de extras, además de los muxes, queremos generar, '
				   		'pudiendo optar entre "servicios" y "canales" o ambos para combinarlos'.decode('utf8'))
	
	# Realizo el parsing de los Argumentos
	#
	opt, args = par.parse_args()
	if len(args) == 1:
		#
		# Ejecuto la lectura y parsing del fichero .M3U
		#
		readm3u(args[0], opt.removenum, opt.numbering, opt.codec)
		
		#
		# Escribo la estructura de directorios y ficheros
		#
		writechannels(opt.networkname, opt.udpxy, opt.iface, opt.output) 
		
		#
		# Mensaje final
		#
		print("OK")
	else:
		par.print_help()


# ==========================================================================================
#
# Entrada al programa cuando se ejecuta desde la línea de comandos
#
# ==========================================================================================
#
if __name__ == '__main__':
	main()#

