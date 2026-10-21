"""
LIMPIEZA DEL TEXTO SCRAPEADO DE LAS WEBS
=========================================
Quita el ruido que contamina las variables del modelo de clasificacion.

EL PROBLEMA QUE RESUELVE
------------------------
Al inspeccionar el dataset anterior, las palabras con mas peso en algunas
empresas eran:

    cookielawinfo - checkbox - gdpr - consent - plugin - registrar

Es decir, el banner de cookies, no la empresa. En webs con poco contenido real
ese ruido domina el vector entero y el modelo aprende a distinguir plantillas
de WordPress en lugar de sectores industriales.

DOS ESTRATEGIAS, Y LA SEGUNDA ES LA BUENA
-----------------------------------------
1. LISTA NEGRA: patrones conocidos (cookies, menus, avisos legales).
   Rapida, pero siempre se queda corta y hay que mantenerla a mano.

2. FILTRO POR FRECUENCIA EN EL CORPUS: si una frase aparece en mas del X% de
   las webs, es plantilla, no contenido. Se detecta sola, sin listas.
   Es la que se defiende bien en la memoria: criterio objetivo y reproducible,
   no una lista escrita a ojo.

Se aplican las dos: la lista negra para lo evidente y el filtro de frecuencia
para lo que se escape.
"""

import re
from collections import Counter

# ==========================================================================
# 1 - Lista negra de patrones conocidos
# ==========================================================================

TERMINOS_BASURA = {
    # cookies / consentimiento
    "cookielawinfo", "cookieyes", "cookiebot", "gdpr", "rgpd", "consent",
    "checkbox", "necessary", "analytics", "preferences", "functional",
    "advertisement", "performance", "uncategorized", "viewport",
    # plataformas y plugins
    "wordpress", "woocommerce", "elementor", "wpml", "plugin", "widget",
    "shortcode", "prestashop", "joomla", "drupal", "shopify", "wixsite",
    # navegacion
    "breadcrumb", "sitemap", "newsletter", "javascript", "iframe",
    "lorem", "ipsum", "placeholder", "untitled",
}

PATRONES_FRASE = [
    r"(?i)\b(aceptar|rechazar|configurar|gestionar)\s+(todas\s+)?(las\s+)?cookies\b",
    r"(?i)\bpol[ií]tica\s+de\s+(cookies|privacidad|calidad)\b",
    r"(?i)\baviso\s+legal\b",
    r"(?i)\bt[eé]rminos\s+y\s+condiciones\b",
    r"(?i)\bderechos\s+reservados\b",
    r"(?i)\bseleccionar\s+p[aá]gina\b",
    r"(?i)\b(ir|saltar)\s+al\s+contenido\b",
    r"(?i)\b(accept|reject|manage)\s+(all\s+)?cookies\b",
    r"(?i)\b(privacy|cookie)\s+policy\b",
    r"(?i)\ball\s+rights\s+reserved\b",
    r"(?i)\bskip\s+to\s+(main\s+)?content\b",
    r"(?i)\bthis\s+website\s+uses\s+cookies\b",
    r"(?i)\bwir\s+verwenden\s+cookies\b",
    r"(?i)\bce\s+site\s+utilise\s+des\s+cookies\b",
    r"(?i)\bquesto\s+sito\s+utilizza\s+i\s+cookie\b",
    r"(?i)\bleer\s+m[aá]s\b|\bread\s+more\b|\bver\s+m[aá]s\b",
]

RE_URL = re.compile(r"https?://\S+|www\.\S+|\S+\.(com|es|net|org|eu)/\S*")
RE_EMAIL = re.compile(r"[\w\.\-\+]+@[\w\-]+\.[\w\.\-]+")
RE_TELEFONO = re.compile(r"(?:\+\d{1,3}[\s\.\-]?)?(?:\d[\s\.\-]?){9,}")
RE_NO_LATINO = re.compile(r"[^\x00-\x7FÀ-ɏ\s]")
RE_SEPARADOR = re.compile(r"[^\wÀ-ɏ]+")
RE_FRASE = re.compile(r"[.!?\n·|]+")


def _token_es_basura(t):
    """Decide si un token no aporta nada al modelo."""
    if len(t) < 3:
        return True
    if t in TERMINOS_BASURA:
        return True
    if t.isdigit():                                 # numeros sueltos: 0000, 03202
        return True
    if not any(c.isalpha() for c in t):             # simbolos
        return True
    if sum(c.isdigit() for c in t) > len(t) / 2:    # codigos tipo a1b2c3
        return True
    if len(t) > 28:                                 # cadenas pegadas sin espacios
        return True
    return False


def limpiar(texto):
    """Limpieza de un texto individual. Conserva el contenido con significado."""
    if not texto or not isinstance(texto, str):
        return ""
    t = texto
    if t.strip().lower() in {"nan", "none", "null", "-"}:
        return ""

    t = RE_URL.sub(" ", t)
    t = RE_EMAIL.sub(" ", t)
    t = RE_TELEFONO.sub(" ", t)
    t = RE_NO_LATINO.sub(" ", t)
    for p in PATRONES_FRASE:
        t = re.sub(p, " ", t)

    tokens = [w for w in RE_SEPARADOR.split(t) if not _token_es_basura(w.lower())]
    return re.sub(r"\s+", " ", " ".join(tokens)).strip()


# ==========================================================================
# 2 - Filtro por frecuencia en el corpus  (la estrategia principal)
# ==========================================================================

def detectar_plantillas(textos, umbral=0.15, min_palabras=4, top=400):
    """Encuentra frases que se repiten en muchas webs distintas.

    Si una frase aparece en mas del `umbral` de las webs, no describe a ninguna
    empresa concreta: es plantilla. Se detecta sola, sin listas escritas a mano.
    """
    n = len(textos)
    if n < 50:
        return set()

    conteo = Counter()
    for t in textos:
        if not t:
            continue
        frases = {f.strip().lower() for f in RE_FRASE.split(str(t))
                  if len(f.split()) >= min_palabras}
        conteo.update(frases)

    limite = umbral * n
    return {f for f, c in conteo.most_common(top * 4) if c >= limite}


def aplicar_plantillas(texto, plantillas):
    """Quita del texto las frases marcadas como plantilla."""
    if not texto or not plantillas:
        return texto
    partes = RE_FRASE.split(str(texto))
    fuera = [p for p in partes if p.strip().lower() not in plantillas]
    return re.sub(r"\s+", " ", " ".join(fuera)).strip()


def limpiar_corpus(textos, umbral_plantilla=0.15, verbose=True):
    """Limpieza completa de una coleccion de textos.

    EL ORDEN IMPORTA:
      1. Detectar plantillas sobre el texto ORIGINAL, que aun conserva la
         puntuacion. Sin puntuacion no hay frases que comparar y el detector
         no encuentra nada.
      2. Quitar esas plantillas.
      3. Solo entonces, limpieza de tokens, urls y basura.

    Devuelve (textos_limpios, informe). El informe son solo numeros.
    """
    originales = [str(t) if t else "" for t in textos]

    # 1 y 2 - plantillas, sobre el texto con puntuacion intacta
    plantillas = detectar_plantillas(originales, umbral=umbral_plantilla)
    sin_plantillas = [aplicar_plantillas(t, plantillas) for t in originales]

    # 3 - limpieza de tokens
    paso1 = sin_plantillas
    paso2 = [limpiar(t) for t in sin_plantillas]

    def media_long(lista):
        v = [len(x) for x in lista if x]
        return sum(v) / len(v) if v else 0

    informe = {
        "textos": len(originales),
        "no_vacios_antes": sum(1 for t in originales if len(t) > 100),
        "no_vacios_despues": sum(1 for t in paso2 if len(t) > 100),
        "long_media_antes": round(media_long(originales)),
        "long_media_tras_listanegra": round(media_long(paso1)),
        "long_media_final": round(media_long(paso2)),
        "plantillas_detectadas": len(plantillas),
    }
    if informe["long_media_antes"]:
        informe["reduccion_pct"] = round(
            (1 - informe["long_media_final"] / informe["long_media_antes"]) * 100, 1)

    if verbose:
        print("\n   LIMPIEZA DE TEXTO")
        print("     textos procesados        : {}".format(informe["textos"]))
        print("     longitud media antes     : {} car.".format(informe["long_media_antes"]))
        print("     tras quitar basura       : {} car.".format(informe["long_media_tras_listanegra"]))
        print("     plantillas detectadas    : {}".format(informe["plantillas_detectadas"]))
        print("     longitud media final     : {} car.".format(informe["long_media_final"]))
        if "reduccion_pct" in informe:
            print("     reduccion total          : {}%".format(informe["reduccion_pct"]))
        print("     con texto util (>100car) : {} (antes {})".format(
            informe["no_vacios_despues"], informe["no_vacios_antes"]))

    return paso2, informe


if __name__ == "__main__":
    ejemplo = (
        "Aceptar todas las cookies Politica de privacidad cookielawinfo-checkbox-necessary "
        "gdpr consent 11 months Seleccionar pagina Fabrica de Muebles Torres S.L. es una "
        "compania especializada en mobiliario de hogar en melamina, dormitorios de "
        "matrimonio y comedores. www.ejemplo.es info@ejemplo.es 963 123 456 0000 03202"
    )
    print("ANTES:\n ", ejemplo)
    print("\nDESPUES:\n ", limpiar(ejemplo))
