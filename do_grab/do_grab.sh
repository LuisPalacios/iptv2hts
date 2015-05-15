#!/bin/bash
#
# Script que ejecuta dos "grabbers" o recolectores de guías de TV. Cada uno
# de ellos genera un fichero XMLTV como salida. Se combinan ambos en un
# único fichero XMLTV final para que sea consumido por Tvheadend desde un
# equipo remoto. El fichero resultado se llama guia.xml y se copia en
# un directorio NFS que a la vez es accedido por dicho servidor tvheadend
#
#  Copyright (C) 2015 Luis Palacios
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#
#  INSTALACION:
#   Instalar movistartv2xmltv
#   Instalar WebGrab+Plus
#   Instalar proyecto xmltv
#   Crear este script
#   Programar su ejecución en crontab
#      0 7 * * * /home/luis/guia/do_grab.sh
#   NOTA: Adaptar TODOS los paths a tu instalación.
#
#
PATH_MOVISTARTV2XMLTV=/home/luis/iptv2hts-master/movistartv2xmltv
PATH_WEBGRABPLUS=/home/luis/wg++
PATH_DESTINATION=/mnt/NAS/moipro

# Preparo PATH
export PATH=/usr/bin:/bin:.

# GRABBER 1
# =========
# Primer grabber: Movistar TV utilizando movistartv2xmltv
# https://github.com/LuisPalacios/iptv2hts
cd ${PATH_MOVISTARTV2XMLTV}
export EPYTHON=python2.7
./tv_grab_es_movistar.py
# Copio el resultado al directorio final de trabajo
cp movistartv-guia.xml ${PATH_DESTINATION}

# GRABBER 2
# =========
# Primer grabber: Múltiples fuentes, utilizando WebGrab+Plus
# http://www.webgrabplus.com/
#
cd ${PATH_WEBGRABPLUS}
./wg++.sh
# Copio el resultado al directorio final de trabajo
cp guide.xml  ${PATH_DESTINATION}/webgrabplus-guia.xml


# COMBINAR
# ========
# Combino los ficheros en uno único final llamado "guia.xml"
# El "combiner" es una herramienta del proyecto XMLTV
# http://sourceforge.net/projects/xmltv/

# Cambio al directorio de trabajo donde dejaré el resultado
cd ${PATH_DESTINATION}

# Genero sobre la marcha dos scripts ejecutables que usará tv_grab_combiner
cat > tv_grab_webgrabplus <<-EOF_WEBGRABPLUS
#!/bin/bash
cat  ${PATH_DESTINATION}/webgrabplus-guia.xml
EOF_WEBGRABPLUS
chmod 755 tv_grab_webgrabplus

# Genero sobre la marcha dos scripts ejecutables que usará tv_grab_combiner
cat > tv_grab_movistartv <<-EOF_WEBGRABMOVISTAR
#!/bin/bash
cat  ${PATH_DESTINATION}/movistartv-guia.xml
EOF_WEBGRABMOVISTAR
chmod 755 tv_grab_movistartv

# Genero sobre la marcha el fichero de configuración de tv_grab_combiner
cat > combina.conf <<-EOF_COMBINA
grabber=tv_grab_webgrabplus;root-url=http://local-file/ignorar.url
grabber=tv_grab_movistartv;root-url=http://local-file/ignorar.url
EOF_COMBINA

# Combino los ficheros, ejecutará los dos grabbers que acabo de 
# crear y combinará sus outputs en un fichero final en formato XMLTV
#
export PATH=.:$PATH
tv_grab_combiner --config-file combina.conf --output guia.xml

