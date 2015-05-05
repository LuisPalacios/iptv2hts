
NOTA: Este proyecto todavía está Work in Progress y vinculado a este apunte técnico: [http://www.luispa.com/?p=2647](http://www.luispa.com/?p=2647)


## iptv2hts
===


Genera **Muxes** y **Canales** en Tvheadend 3.x partiendo de un fichero playlist .M3U. He creado este programa partiendo de uno ya existente (ver Licencia) con el objetivo de personalizarlo para poder insertar los canales de Movistar TV en una instalación con Tvheadend. En principio vale para cualquier fichero IPTV (en formato .m3u) pero todas las pruebas las he realizado con dicho proveedor. 


## Fichero .M3U
===

Junto con este script encontrarás el fichero **movistartv-canales.m3u** pero también una copia del proyecto **movistartv2xmltv**, que es el script con el que he creado dicho fichero movistartv-canales.m3u.


### Uso
---


#### movistartv2xmltv

Si quieres crear tu mismo el fichero **movistartv-canales.m3u** sigue los pasos siguientes: 


<PENDIENTE>



#### iptv2hts

Para ejecutar el programa tienes que usar la sintaxis siguiente: ``m3u2hts.py [opciones] inputfile`` o bien ``m3u2hts.py -h`` para conseguir ayuda sobre los parámetros. 

Puedes ejecutar el script dentro del directorio raiz de Tvheadend o en un directorio vacío y transferir el resultado al servidor donde se ejectua Tvheadend. En cualquier caso, recomiendo que pares Tvheadend antes de ejecutar o copiar. 

    # service tvheadend stop  (o systemctl stop tvheadend)
    :
    __(ejecutar el programa  ... o ... transferir los archivos)__
    :
    # service tvheadend start   (o systemctl start tvheadend)
    

Ejemplo de ejecución, primero enviamos el script y el fichero .M3U al equipo donde se ejecuta Tvheadend

	obelix:iptv2hts luis$ scp iptv2hts.py root@moipro.parchis.org:.
	obelix:iptv2hts luis$ scp movistartv-canales.m3u root@moipro.parchis.org:.

A continuación nos conectamos mediante SSH

    obelix:~ luis$ ssh -l root moipro.parchis.org

En mi caso se trata de un MOI Pro, así que voy al directorio donde está tvheadend instalado

	[root@MOIPro ~]# cd /\(null\)/.hts/tvheadend
	[root@MOIPro /(null)/.hts/tvheadend]# mv $HOME/iptv2hts.py .
	[root@MOIPro /(null)/.hts/tvheadend]# mv $HOME/movistartv-canales.m3u .

Ejecuto el Script

    [root@MOIPro /(null)/.hts/tvheadend]# systemctl stop tvheadend
    [root@MOIPro /(null)/.hts/tvheadend]# ./iptv2hts.py -x 192.168.1.1:4022 -o canales -n 2 -r -c utf-8 movistartv-canales.m3u
	OK
    [root@MOIPro /(null)/.hts/tvheadend]# systemctl start tvheadend

Conectar con el Interfaz Web de Tvheadend ***Configuration->DVB Inputs->Networks***, selecciono "IPTV Movistar" y hago click en ***Force Scan***. El proceso tardará un buen rato, termina cuando ves que ha activado todos los ***Services***.

A continuación vamos a  ***Configuration->DVB Inputs->Services***, seleccionamos todos los servicios de ""Movistar TV" y ***Map Services***, marcamos las cuatro opciones y pulsamos en ***MAP***. 



### Entrada
---

Como fichero de entrada (por ejemplo canales_movistar_tv.m3u) se espera un fichero con formato M3U, que suele tener definiciones opcionales y URL's para cada canal: 

    #EXTINF:duración, número de canal - nombre del canal
    #EXTTV:tag[,tag,tag...];lenguaje;XMLTV id[;URL al icono]
    udp://@ip:port

Las líneas #EXTTV y su contenido son opcionales. 

Veamos un ejemplo de fichero canales_movistar_tv.m3u:

    <PDTE LUIS PONER AQUI EL FICHERO>
    


### Salida Tvheadend 3.9+
---

El script va a crear una configuración compatible con Tvheadend 3.9+, por lo tanto creará (si no existen) los directorios pertinentes y creará los ficheros ***MUX*** y ***SERVICE*** y ***CHANNEL***. La estructura de directorios y ficheros es la siguinente: 

    input/iptv/config
    input/iptv/networks/UUID/config                      - Creará "IPTV network"
    input/iptv/networks/UUID/muxes/UUID/config           - Un mux por canal
    input/iptv/networks/UUID/muxes/UUID/services/UUID    - Un service (falso) por canal (opción -o service)
    channel/tag/UUID                                     - Tags de los canales
    channel/config/UUID                                  - Canales (asociados a los servicios y tags, opción -o channel)
    epggrab/xmltv/channels/UUID                          - Información EPG (asociada al canal), opción -o channel
    

Los ficheros M3U estándar no tienen la información necesaria que necesita Tvheadend para formar la asociación ***mux -> servicio -> canal***, en concreto le falta el ***service id***. 


### Movistar TV
---

Para crear los canales de Movistar TV en Tvheadend recomiendo crear solo los Mux y los Canales, es decir, usar solo la opción **-o canales**. Tras ejecutar el script tendrás que pedirle a Tvheadend que haga un ***scan*** de los ***mux*** para que sea él quien cree los ***services*** (y lo haga con el ***id*** adecuado). Una vez creados, podrás seleccionarlos y pedir que haga un ***Map de los Services*** a los ***Canales existentes***: 

 * Abre las propiedades de la Network "IPTV Movistar"
 * Habilita "Idle scan muxes" y limita "Max input streams" (a algo que tu red pueda gestionar, por ejemplo 4)
 * Cuando termine el scan (puede tardar mucho), podrás pedir que se haga el Map
  cada canal a su servicio desde la ventana de Servicios o desde la de Canales. 
 

Licencia y referencias
--------

iptv2hts está basado en el trabajo de Gregor Rudolf: [GitHub grudolf/m3u2hts](https://github.com/grudolf/m3u2hts). 

movistartv2xmltv está basado en el trabajo de "ese": [GitHub ese/movistartv2xmltv](https://github.com/ese/movistartv2xmltv). 

Este código se licencia bajo MIT: http://www.opensource.org/licenses/mit-license.php
