# BachScraper
# This Python file uses the following encoding: utf-8

import urllib2
import csv
import lxml.html
from lxml import etree
import cssselect
import logging



# CONSTANTES

# Parte constante de las URL que se quieren recuperar
parteURL = "https://www.bach-digital.de/receive/BachDigitalWork_work_000"
# Hay que añadirle 5 digitos más; empezando con 00001 y terminando en 99999
# Muchas de estas páginas no existen
parteIdioma = "?lang=en"

limiteInfURL = 1                # Primera página que se quiere recuperar
limiteSupURL = 11500            # Última página que se quiere recuperar
longResto = 5                   # Longitud del sufijo que se va a añadir

fichSalidaCSV = "bach.csv"      # Nombre del fichero CSV donde se almacenará el dataset
fichLog = "bach.log"            # Nombre del fichero de log
CODIFICACION = "utf_8"



# Información sobre los campos que se quieran recuperar
# Para cada campo que se quiera recuperar de la página se debe incluir una tupla con 4 elementos:
# 1. La cadena de búsqueda para lxml o CSS selector
# 2. El nombre del campo (para la primera línea del fichero CSV)
# 3. Tipo de análisis que se realizará:
#       - "xpath": con xpath
#       - "cssselect-text": con cssselect, con resultado en la parte text del elemento recuperado
#       - "cssselect-tail": con cssselect, con resultado en la parte tail del elemento recuperado
#       - "cssselect-conjunto": con cssselect, donde se recupera un conjunto de elentos donde hay que buscar un texto específico
# 4. Si el análisis es de tipo "cssselect-conjunto", el texto que hay que buscar
listaCampos =  [
                    ('html body main div br',"Autor","cssselect-tail", ""),
                    ('//*[@id="innercontent"]/div[1]/h3/span',"Título","xpath", ""),
                    ('//*[@id="innercontent"]/div[1]/h3/abbr',"Catálogo","xpath", ""),
                    ('//*[@id="innercontent"]/div[1]/h4',"Descripción","xpath", ""),
                    ('dl[id=perfMedium]', "Instrumentación", "cssselect-conjunto", "Scoring"),
                    ('dl[class=dl-horizontal]', "Fecha", "cssselect-conjunto", "Date of origin"),
                    ('dl[class=dl-horizontal]', "Letras", "cssselect-conjunto", "Lyrics"),
                    ('dl[class=dl-horizontal]', "Comentarios", "cssselect-conjunto", "Comment"),
                    ('dl[class=dl-horizontal]', "Edición", "cssselect-conjunto", "Edition"),
                    ('dl[class=dl-horizontal]', "Editor", "cssselect-conjunto", "Editor"),
                    ('dl[class=dl-horizontal]', "Estreno", "cssselect-conjunto", "Early performances"),
                    ]


# Descarga una página a partir de la url
# Código del libro Web Scraping with Python de Lawson
def download (url):
    try:
        html = urllib2.urlopen(url).read()
    except urllib2.URLError as e:
        html = None
    return html

# Devuelve una tupla con toda la información que se extrae de la página web
# Parámetros:
# - árbol obtenido a partir de la página Web
# - información sobre el campo que se quiere recuperar (ontenida de listaCampos)
def extraerCampo (arbol, exp, nombre, tipo, texto):
    if tipo == "xpath":
        informacion = arbol.xpath(exp)
    else:
        if tipo == "cssselect-text" or tipo == "cssselect-tail":
            informacion = arbol.cssselect(exp)
        else:
            if tipo == "cssselect-conjunto":
                informacion = None
                for link in arbol.cssselect(exp):
                        cont = 0
                        parar = False
                        # Se busca en el conjunto recuperado el texto requerido
                        # y se devuelve el siguiente elemento, que es donde está la información buscada
                        for c in iter(link):
                            cont = cont+1
                            if (isinstance(c.text,str) and c.text.find(texto)!= -1):
                                parar = True
                            else:
                                if parar == True:
                                    informacion = c
                                    parar = False
            else:
                print "ERROR: tipo no definido"
                logging.error("Tipo de extracción del campo no definido")

    # En informacion está el código html recuperado según la expresión de búsqueda
    # Ahora se extraerá la información según el tipo de información esperado
    if informacion is None or informacion == []:
        resultado = ""
    else:
        if len(informacion) == 0:
            resultado = informacion.text
        else:
            if isinstance(informacion[0], str) or isinstance(informacion[0], unicode):
                #No tiene subelementos
                resultado = informacion[0]
            else:
                if tipo == "xpath":
                    resultado = (informacion[0].text)
                else:
                    if tipo == "cssselect-text":
                        # Se recupera el text y, además, más información si existe
                        resultado = (informacion[0].text)
                        for c in iter(informacion[0]):
                            if isinstance(c.text, str) or isinstance(c.text, unicode):
                                resultado += c.text + ", "
                        # Se elimina la última coma
                        if len(resultado)>2 and resultado[-2:] == ", ":
                            resultado = resultado[0:len(resultado)-2]
                        # Se añade más información si hay en la cola
                        if informacion[0].tail != None:
                            resultado = resultado+informacion[0].tail
                    else:
                        if tipo == "cssselect-tail":
                            resultado = (informacion[0].tail)
                        else:
                            if tipo == "cssselect-conjunto":
                                # Se recupera el text y, además, más información si existe
                                if informacion[0].text is None:
                                    resultado = ""
                                else:
                                    resultado = (informacion[0].text)
                                for c in iter(informacion):
                                    if isinstance(c.text, str) or isinstance(c.text, unicode):
                                            resultado += c.text + ", "
                                # Se elimina la última coma
                                if len(resultado)>2 and resultado[-2:] ==", ":
                                    resultado = resultado[0:len(resultado)-2]
                                # Se añade más información si hay en la cola
                                if informacion[0].tail != None:
                                    resultado = resultado+informacion[0].tail
                            else:
                                resultado = ""
    return resultado.encode(CODIFICACION).strip()

# Dada una dirección y la página recuperada de esa dirección
# Devuelve una lista con la información encontrada para cada uno de los campos
def extraerInformacion (url, html):
    tree = etree.HTML(html)
    resultado = []
    for (exp, nombreCampo, tipo, texto) in listaCampos:
       resultado.append(extraerCampo(tree, exp, nombreCampo, tipo, texto))
    resultado.append(url)
    return resultado

# Devuelve una lista con los nombres de todos los campos obtenidos de listaCampos
def obtenerCabecera ():
    cab = []
    for (_, c, _, _) in listaCampos:
        cab.append(c)
    cab.append("URL")
    return cab

# Dado el nombre de un fichero CSV
# va generando la URL de las páginas,
# obtiene la página correspondiente
# extrae la información para cada campos
# y la escribe en el fichero CSV
# También escribe en pantalla y en el log la URL que está procesando

def crearCSVconPaginas (nomFicheroCSV):
  with open(nomFicheroCSV, 'w') as fcsv:
    writer = csv.writer(fcsv, delimiter=';', )

    noDescargadas = 0
    paginasProcesadas = 0
    writer.writerow(obtenerCabecera())
    # se generan las URL
    for i in range(limiteInfURL,limiteSupURL+1, 1):
        url = parteURL+str(i).zfill(longResto)+parteIdioma
        # Se intenta descargar la página correspondiente
        html = download(url)
        if html is None:
            print "No existe la página ", url
            logging.info("No existe la página "+url)
            noDescargadas = noDescargadas + 1
        else:
            print "Procesando ", url
            logging.info("Procesando "+url)
            # Se intenta mejorar el HTML de la página obtenida
            tree = lxml.html.fromstring(html)
            fixed_html = lxml.html.tostring(tree, pretty_print = True)
            # Se extrae la información y se guarda en el fichero CSV
            writer.writerow(extraerInformacion(url, fixed_html))
            paginasProcesadas = paginasProcesadas + 1
    # Resumen de páginas procesadas y no descargadas
    logging.info("Páginas procesadas: "+ str(paginasProcesadas))
    print "Páginas procesadas: ", paginasProcesadas
    logging.info("Páginas que no existen o que no se han podido descargar: " + str(noDescargadas))
    print "Páginas que no existen o que no se han podido descargar: ", noDescargadas
  fcsv.close()

# Programa principal
def main():
    logging.basicConfig(level = logging.DEBUG,
                        format = "%(asctime)s : %(levelname)s : %(message)s",
                        filename = fichLog,
                        filemode = 'w')
    print("Se inicia el proceso de scraping de la web www.bach-digital.de")
    logging.info("Se inicia el proceso de scraping de la web www.bach-digital.de")
    print("Se está generado el data set "+fichSalidaCSV)
    logging.info("Se está generado el data set "+fichSalidaCSV)

    crearCSVconPaginas(fichSalidaCSV)

    print("Fin del proceso de scraping")
    logging.info("Fin del proceso de scraping")





if __name__ == "__main__":
    main()
