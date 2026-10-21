# -*- coding: utf-8 -*-
"""
F6_A6_corpus_correos.py · ¿bastan estos correos para poner en marcha A6?
========================================================================

LA PREGUNTA
    Se han exportado unos cincuenta correos reales recibidos en la direccion
    general de la organizacion. La pregunta es si con eso se puede entrenar y
    poner en marcha el agente A6, el que atiende lo que entra.

    La respuesta no es un si o un no: A6 tiene CUATRO piezas y cada una
    necesita una cosa distinta. Este script mide las cuatro por separado.

        1. Resolver la identidad   ¿quien escribe? ¿esta ya en el CRM?
           -> NO se entrena. Son reglas. Los correos sirven para MEDIRLA.
        2. Detectar la norma citada
           -> NO se entrena. Es un diccionario. Los correos lo MIDEN.
        3. Enrutar al area tecnica
           -> SI se entrena, pero NO con estos correos: las etiquetas de area
              estan en el historico del CRM. Los correos sirven de PRUEBA.
        4. Separar lo comercial de lo que no lo es
           -> SI se entrena, y aqui si hacen falta los correos. Es la pieza
              que este corpus condiciona.

    Confundir "entrenar" con "medir" es el error que hay que evitar. Cincuenta
    casos son poquisimos para entrenar y suficientes para medir algunas cosas
    con un margen ancho pero declarable. El script calcula ese margen.

PROTECCION DE DATOS · SE HACE LO PRIMERO
    El fichero de entrada trae nombres, direcciones de correo, telefonos y
    firmas de personas reales de OTRAS empresas. Son datos personales de
    terceros y no pueden quedarse en un fichero de trabajo del proyecto.

    Antes de cualquier analisis, el script:
      · seudonimiza la persona y la empresa (SHA-256 con la sal del proyecto)
      · borra del cuerpo las direcciones de correo, los telefonos y las URL
      · corta la firma y el descargo legal, que es donde se concentran
      · guarda SOLO la version seudonimizada

    El fichero original se deja donde esta y no se copia a ninguna parte.
    El dominio SI se conserva, porque es la variable que resuelve la
    identidad y sin ella no hay nada que medir; un dominio de empresa
    identifica a la empresa, no a la persona.

QUE GENERA
    datos/01_limpio/entradas_inbound_50_anon.csv    el corpus seudonimizado
    datos/03_resultados/f6_corpus.json              las cifras medidas

COMO SE EJECUTA
    python scripts/F6_A6_corpus_correos.py

FUENTES
    datos/00_bruto/ejemplos de correos.txt       lo exportado del buzon
    datos/01_limpio/Cuentas ..._anon.csv         para cruzar dominios
    13_DISENO_F6.md                              el diseno del agente
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

VERSION_SCRIPT = "v1 · 30-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
LIMPIO = RAIZ / "datos" / "01_limpio"
DERIVADO = RAIZ / "datos" / "02_derivado"
RESULTADOS = RAIZ / "datos" / "03_resultados"
PRIVADO = RAIZ / "datos" / "_mapeo_privado"

ENTRADA = BRUTO / "ejemplos de correos.txt"
# OJO CON DE DONDE SE LEEN LAS CUENTAS.
# En el fichero .._anon.csv la columna "Sitio web" esta SEUDONIMIZADA: son
# codigos, no dominios, y cruzarlos contra un dominio real da 0 % siempre.
# Las URL reales estan en los ficheros derivados, que son los que uso el
# analisis de las ocho entradas. Se leen los mismos para que las dos medidas
# sean comparables.
CUENTAS_DERIVADAS = ["cuentas_train.csv", "cuentas_val.csv", "cuentas_test.csv"]
SALIDA_CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"
SALIDA_CIFRAS = RESULTADOS / "f6_corpus.json"

# Lo medido con las OCHO entradas del analisis anterior. Sirve de referencia:
# si con cincuenta sale lo mismo, es que aquello no era casualidad.
OCHO_ENTRADAS = {"n": 8, "dominio_resuelto": 2, "norma_detectada": 7}

GENERICOS = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.es",
             "icloud.com", "live.com", "msn.com", "aol.com", "protonmail.com",
             "telefonica.net", "terra.es", "wanadoo.es", "hotmail.es",
             "gmx.com", "mail.com", "me.com", "qq.com", "163.com",
             "googlemail.com", "outlook.es", "hotmail.fr", "libero.it"}

# El mismo diccionario del analisis de las ocho entradas. No se toca: si
# cambiara, las dos medidas dejarian de ser comparables.
NORMAS = {
    "CARACTERIZACION Y EMBALAJES": [
        "ista", "astm d4169", "d4169", "iso 11607", "vibracion", "compresion",
        "apilamiento", "top load", "caida", "impacto", "carga paletizada",
        "simulacion de transporte", "resistencia estructural"],
    "QUIMICO Y PROCESOS": [
        "mosh", "moah", "pfas", "bisfenol", "bpa", "migracion", "nias",
        "ftir", "dsc", "plomo", "cadmio", "mercurio", "cromo hexavalente",
        "metales pesados", "sensorial", "reach"],
    "ENVASES Y ECONOMIA CIRCULAR": [
        "ppwr", "en 13430", "en 13427", "en 13428", "en 13429", "reciclabilidad",
        "ecodiseno", "declaracion de conformidad", "declaraciones de conformidad",
        "2025/40"],
    "COMPOSTABILIDAD": [
        "compostabilidad", "compostable", "biodegradacion", "biodegradable",
        "en 13432", "home compost"],
}

# Senales de que el correo NO es una solicitud comercial. Es la clase que el
# diseno de F6 dice que hay que separar y la unica que estos correos pueden
# entrenar, asi que conviene saber cuantos casos hay.
NO_COMERCIAL = [
    "curriculum", "curriculum vitae", "cv adjunto", "candidatura",
    "oferta de empleo", "practicas", "beca", "tesis", "tfg", "tfm",
    "factura", "remesa", "pago pendiente", "recibo", "domiciliacion",
    "newsletter", "boletin", "darse de baja", "unsubscribe",
    "webinar", "invitacion al evento", "congreso", "feria",
    "proveedor", "presupuesto para ustedes", "les ofrecemos",
    "posicionamiento web", "seo", "marketing digital",
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def contiene_palabra(texto, termino):
    """
    Busca el termino como PALABRA, no como subcadena. Es la correccion del
    error X8, que aparecio tres veces: `doc` encontraba "documentacion" y
    disparaba un area sin motivo.
    """
    partes = termino.split()
    if len(partes) == 1:
        cola = r"\w*" if len(termino) >= 6 else ""
        patron = r"(?<![\w])" + re.escape(termino) + cola + r"(?![\w])"
    else:
        patron = (r"(?<![\w])" + r"\W+".join(re.escape(p) for p in partes)
                  + r"\w*(?![\w])")
    return re.search(patron, texto) is not None


def cargar_sal():
    f = PRIVADO / "sal.txt"
    if not f.exists():
        print(f"  ERROR: no encuentro {f}. Lanza antes PREP_anonimizar.py")
        sys.exit(1)
    return f.read_text(encoding="utf-8").strip()


def seudo(valor, sal, prefijo):
    if not valor:
        return ""
    clave = sin_acentos(valor).strip()
    h = hashlib.sha256((sal + clave).encode("utf-8")).hexdigest()[:8]
    return f"{prefijo}_{h}"


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"{n} · {t}")
    print("=" * 76)


# ---------------------------------------------------------------------------
# 1 · Trocear el fichero en correos
# ---------------------------------------------------------------------------
SEPARADOR = re.compile(r"^\s*-{5,}\s*$", re.MULTILINE)
RE_CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RE_TEL = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
RE_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)

# Donde empieza la firma o el descargo legal. Todo lo que va detras se corta:
# es donde se concentran los datos personales y no aporta nada al analisis.
CORTES = ["disclaimer:", "aviso legal", "confidencialidad", "este mensaje y",
          "the content of this e-mail", "protección de datos",
          "proteccion de datos", "antes de imprimir", "please consider the"]


def trocear(texto):
    """Devuelve una lista de bloques, uno por correo."""
    return [b.strip() for b in SEPARADOR.split(texto) if b.strip()]


def parsear(bloque):
    """
    Saca de un bloque: quien escribe, su direccion, a quien va y el cuerpo.
    El formato exportado es:  Nombre<direccion>  /  destinatarios  /  cuerpo
    """
    lineas = bloque.splitlines()
    remitente, direccion = "", ""
    i = 0
    for i, l in enumerate(lineas):
        m = RE_CORREO.search(l)
        if m:
            direccion = m.group(0).lower()
            remitente = l[:m.start()].strip(" <>\t")
            break
    else:
        i = -1

    # las lineas siguientes que no llevan espacios finales son destinatarios
    j = i + 1
    destinatarios = []
    while j < len(lineas) and len(destinatarios) < 4:
        l = lineas[j].strip()
        if not l:
            j += 1
            continue
        if l.lower().rstrip(";").strip() in {"info empresa", "laboratorios",
                                             "formacion", "formación",
                                             "administracion", "administración"}:
            destinatarios.append(l.rstrip(";").strip())
            j += 1
            continue
        break

    cuerpo = "\n".join(lineas[j:]).strip()
    return remitente, direccion, destinatarios, cuerpo


def despersonalizar(cuerpo, remitente):
    """Quita del cuerpo lo que identifica a una persona."""
    t = cuerpo
    # cortar firma y descargo legal
    bajo = t.lower()
    corte = len(t)
    for c in CORTES:
        k = bajo.find(c)
        if k != -1:
            corte = min(corte, k)
    t = t[:corte]
    # sustituir lo que identifica
    t = RE_CORREO.sub("[CORREO]", t)
    t = RE_URL.sub("[WEB]", t)
    t = RE_TEL.sub("[TELEFONO]", t)
    if remitente:
        for parte in remitente.replace(",", " ").split():
            if len(parte) > 2:
                t = re.sub(r"(?i)(?<![\w])" + re.escape(parte) + r"(?![\w])",
                           "[NOMBRE]", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def idioma(texto):
    """Heuristica suficiente: mira palabras funcionales muy frecuentes."""
    t = " " + sin_acentos(texto) + " "
    es = sum(t.count(f" {p} ") for p in
             ["de", "que", "para", "con", "los", "las", "una", "por", "sobre"])
    en = sum(t.count(f" {p} ") for p in
             ["the", "and", "for", "with", "would", "we", "our", "to", "of"])
    if es == en == 0:
        return "?"
    return "es" if es >= en else "en"


# ---------------------------------------------------------------------------
# 2 · El analisis
# ---------------------------------------------------------------------------
def dominio_de(direccion):
    return direccion.split("@")[-1].lower().strip() if "@" in direccion else ""


def dominio_web(url):
    u = str(url).lower().strip()
    if not u or u == "nan":
        return ""
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.split("/")[0].strip()


def ic_binomial(exitos, n):
    """Intervalo de Wilson al 95 %. Con n pequeno el normal miente."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.96
    p = exitos / n
    d = 1 + z ** 2 / n
    centro = (p + z ** 2 / (2 * n)) / d
    margen = z * ((p * (1 - p) / n + z ** 2 / (4 * n ** 2)) ** 0.5) / d
    return (max(0.0, centro - margen) * 100, min(1.0, centro + margen) * 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true",
                    help="escribir el corpus seudonimizado y las cifras")
    a = ap.parse_args()

    print()
    print("#" * 76)
    print(f"# F6 · A6 · ¿bastan estos correos para poner en marcha el agente?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    if not ENTRADA.exists():
        print(f"\n  ERROR: no encuentro {ENTRADA}")
        sys.exit(1)

    # ---------------------------------------------------------------- 1
    titulo(1, "PROTECCION DE DATOS · LO PRIMERO QUE SE HACE")
    sal = cargar_sal()
    bruto = ENTRADA.read_text(encoding="utf-8", errors="replace")
    bloques = trocear(bruto)
    print(f"   Fichero de entrada       : {ENTRADA.name}")
    print(f"   Bloques separados por ---: {len(bloques)}")

    filas = []
    for k, b in enumerate(bloques, 1):
        rem, dire, dest, cuerpo = parsear(b)
        dom = dominio_de(dire)
        filas.append({
            "id": f"IN{k:03d}",
            "canal": "correo",
            "persona_seudo": seudo(rem or dire, sal, "PER"),
            "empresa_seudo": seudo(dom, sal, "EMP") if dom else "",
            "dominio": dom,
            "generico": dom in GENERICOS,
            "destinatarios": " | ".join(dest),
            "idioma": idioma(cuerpo),
            "palabras": len(cuerpo.split()),
            "cuerpo": despersonalizar(cuerpo, rem),
        })
    d = pd.DataFrame(filas)
    d = d[d.palabras >= 5].reset_index(drop=True)

    print(f"   Correos con cuerpo util  : {len(d)}")
    print()
    print("   Tratamiento aplicado a cada correo ANTES de analizarlo:")
    print("      persona    -> seudonimo PER_xxxxxxxx (SHA-256 + sal)")
    print("      empresa    -> seudonimo EMP_xxxxxxxx")
    print("      cuerpo     -> sin direcciones, telefonos, URL ni el nombre")
    print("      firma y descargo legal -> cortados")
    print("      dominio    -> SE CONSERVA: sin el no hay nada que medir, e")
    print("                    identifica a la empresa, no a la persona")

    # ---------------------------------------------------------------- 2
    titulo(2, "QUE HAY EN EL CORPUS")
    print(f"   Correos                  : {len(d)}")
    print(f"   Longitud media           : {d.palabras.mean():.0f} palabras "
          f"(mediana {d.palabras.median():.0f})")
    print(f"   El mas corto / el mas largo: {d.palabras.min()} / {d.palabras.max()}")
    print()
    print("   Idioma:")
    for k, v in d.idioma.value_counts().items():
        print(f"      {k:<6} {v:>4}   {v/len(d)*100:5.1f} %")
    print()
    n_gen = int(d.generico.sum())
    print(f"   Dominio de empresa       : {len(d)-n_gen:>4}   "
          f"{(len(d)-n_gen)/len(d)*100:5.1f} %")
    print(f"   Dominio generico (gmail…): {n_gen:>4}   {n_gen/len(d)*100:5.1f} %")
    print()
    rep = d[~d.generico].dominio.value_counts()
    rep = rep[rep > 1]
    print(f"   Dominios que se repiten  : {len(rep)}"
          + (f"  ({', '.join(rep.index[:4])}…)" if len(rep) else ""))
    print(f"   Empresas distintas       : {d[~d.generico].dominio.nunique()}")
    if d.destinatarios.str.len().gt(0).any():
        print()
        print("   A que buzon llegan:")
        for k, v in Counter(
                x for s in d.destinatarios for x in s.split(" | ") if x
        ).most_common():
            print(f"      {k:<22} {v:>4}")

    # ---------------------------------------------------------------- 3
    titulo(3, "PIEZA 1 · RESOLVER LA IDENTIDAD CONTRA EL CRM")
    print("   Es la primera decision del agente: ¿esta ya esta empresa en el")
    print("   sistema? Se resuelve por dominio. No se entrena: son reglas.")
    print()
    cu = pd.concat([pd.read_csv(DERIVADO / f) for f in CUENTAS_DERIVADAS],
                   ignore_index=True)
    cu["dom"] = cu.url.apply(dominio_web)
    con_url = cu[cu.dom != ""]
    dominios_crm = set(con_url.dom)
    print(f"   Cuentas en el CRM              : {len(cu):>6}")
    print(f"   …con sitio web utilizable      : {len(con_url):>6}   "
          f"{len(con_url)/len(cu)*100:5.1f} %  <- el techo estructural")
    print(f"   Dominios distintos             : {len(dominios_crm):>6}")
    print()

    empresa = d[~d.generico].copy()
    empresa["en_crm"] = empresa.dominio.isin(dominios_crm)
    n_res = int(empresa.en_crm.sum())
    lo, hi = ic_binomial(n_res, len(empresa))
    # Guarda contra el fallo que ya cometi una vez: si sale 0 de 48, no es un
    # hallazgo, es que se esta cruzando contra una columna seudonimizada.
    if n_res == 0 and len(empresa) > 20:
        print()
        print("   ALTO. Cero coincidencias de 48 no es un resultado creible.")
        print("   Comprueba que las URL del CRM sean dominios de verdad y no")
        print("   codigos de seudonimizacion antes de dar esta cifra por buena.")
        muestra = list(con_url.dom.head(3))
        print(f"   Muestra de dominios del CRM: {muestra}")
    print(f"   Correos con dominio de empresa : {len(empresa):>6}")
    print(f"   …cuyo dominio esta en el CRM   : {n_res:>6}   "
          f"{n_res/len(empresa)*100:5.1f} %")
    print(f"   Intervalo de confianza al 95 % : [{lo:.1f} %, {hi:.1f} %]")
    print()
    print(f"   Con las OCHO entradas de antes salia "
          f"{OCHO_ENTRADAS['dominio_resuelto']}/{OCHO_ENTRADAS['n']} = "
          f"{OCHO_ENTRADAS['dominio_resuelto']/OCHO_ENTRADAS['n']*100:.0f} %.")
    lo8, hi8 = ic_binomial(OCHO_ENTRADAS["dominio_resuelto"], OCHO_ENTRADAS["n"])
    print(f"   Su intervalo era [{lo8:.1f} %, {hi8:.1f} %]: tan ancho que no")
    print(f"   decia nada. Con estos correos el intervalo mide "
          f"{hi-lo:.0f} puntos en vez de {hi8-lo8:.0f}.")

    # ---------------------------------------------------------------- 4
    titulo(4, "PIEZA 2 · DETECTAR LA NORMA CITADA")
    print("   Tampoco se entrena: es un diccionario de normas -> area, y la")
    print("   correspondencia se sabe con certeza. Los correos lo MIDEN.")
    print()
    def areas_de(texto):
        t = sin_acentos(texto)
        return {a for a, ns in NORMAS.items()
                if any(contiene_palabra(t, n) for n in ns)}

    d["areas"] = d.cuerpo.apply(areas_de)
    d["n_areas"] = d.areas.apply(len)
    n_det = int((d.n_areas > 0).sum())
    lo, hi = ic_binomial(n_det, len(d))
    print(f"   Correos con alguna norma reconocida: {n_det:>4} de {len(d)}   "
          f"{n_det/len(d)*100:5.1f} %")
    print(f"   Intervalo de confianza al 95 %     : [{lo:.1f} %, {hi:.1f} %]")
    print(f"   Con las ocho entradas salia {OCHO_ENTRADAS['norma_detectada']}/8 "
          f"= {OCHO_ENTRADAS['norma_detectada']/8*100:.0f} %")
    print()
    print("   Reparto por area (un correo puede tocar varias):")
    cnt = Counter(a for s in d.areas for a in s)
    for area, _ in sorted(NORMAS.items()):
        v = cnt.get(area, 0)
        marca = "  <-- pocos casos" if 0 < v < 10 else ("  <-- NINGUNO" if v == 0 else "")
        print(f"      {area:<32}{v:>4}   {v/len(d)*100:5.1f} %{marca}")
    print()
    print(f"   Sin norma reconocible              : {len(d)-n_det:>4}   "
          f"{(len(d)-n_det)/len(d)*100:5.1f} %")
    print("   Esos son los que exigirian un clasificador de verdad, porque")
    print("   piden algo sin nombrar la norma que lo regula.")

    # ---------------------------------------------------------------- 5
    titulo(5, "PIEZA 3 · ENRUTAR AL AREA  ·  DONDE ESTAN LAS ETIQUETAS")
    print("   Esta pieza SI se entrena, pero NO con estos correos: las")
    print("   etiquetas de area estan en el historico de oportunidades del")
    print("   CRM, que son miles. Estos cincuenta serian el conjunto de")
    print("   PRUEBA, y ahi esta su valor: son texto de entrada real, que es")
    print("   una poblacion distinta y mas dificil que la del historico.")
    print()
    print("   Cuantas clases hay que distinguir:")
    print("      area tecnica     4 clases, multietiqueta")
    print("      tipo de servicio 4 clases, opcion unica")
    print()
    print(f"   Con {len(d)} correos y 4 clases salen ~{len(d)/4:.0f} casos por")
    print("   clase EN EL MEJOR REPARTO, y el reparto de arriba no es")
    print("   equilibrado. Para entrenar es muy poco; para medir con margen")
    print("   ancho y declarado, sirve.")

    # ---------------------------------------------------------------- 6
    titulo(6, "PIEZA 4 · SEPARAR LO COMERCIAL DE LO QUE NO LO ES")
    print("   Esta es la unica pieza que DEPENDE de estos correos, porque la")
    print("   clase negativa —lo que no es una solicitud comercial— no existe")
    print("   en el CRM: alli solo esta lo que llego a convertirse en algo.")
    print()
    def parece_no_comercial(t):
        s = sin_acentos(t)
        return [x for x in NO_COMERCIAL if contiene_palabra(s, x)]

    d["senales_no_com"] = d.cuerpo.apply(parece_no_comercial)
    n_no = int(d.senales_no_com.apply(bool).sum())
    print(f"   Correos con senal de NO comercial : {n_no:>4} de {len(d)}   "
          f"{n_no/len(d)*100:5.1f} %")
    if n_no:
        print()
        for s, v in Counter(x for l in d.senales_no_com for x in l).most_common(8):
            print(f"      «{s}»{'':<{max(0, 28-len(s))}}{v:>4}")
    print()
    if n_no < 10:
        print("   AVISO IMPORTANTE")
        print("   La clase negativa esta casi vacia. Un clasificador entrenado")
        print("   con esto aprenderia a responder SIEMPRE 'es comercial', y")
        print("   acertaria mucho sin haber aprendido nada. Es exactamente el")
        print("   problema que en A2 obligo a medir el suelo de 'responder")
        print("   siempre lo mas comun'.")
        print()
        print("   Y hay un motivo de fondo: lo que se exporto son correos que")
        print("   YA se consideraron interesantes. Los que no lo eran ni")
        print("   llegaron a esa carpeta. Es un sesgo de seleccion, y no se")
        print("   arregla con mas correos de la misma carpeta.")

    # ---------------------------------------------------------------- 7
    titulo(7, "VEREDICTO POR PIEZAS")
    filas_v = [
        ("1 · Resolver la identidad", "REGLAS", "SI, y ya esta medido",
         f"{n_res}/{len(empresa)} por dominio"),
        ("2 · Detectar la norma", "DICCIONARIO", "SI, y ya esta medido",
         f"{n_det}/{len(d)} correos"),
        ("3 · Enrutar al area", "SE ENTRENA", "como PRUEBA, no para entrenar",
         "las etiquetas estan en el CRM"),
        ("4 · Comercial / no comercial", "SE ENTRENA", "NO bastan",
         f"solo {n_no} casos negativos"),
    ]
    print(f"   {'pieza':<30}{'como funciona':<14}{'¿bastan 50?':<32}")
    print("   " + "-" * 72)
    for p, c, b, det in filas_v:
        print(f"   {p:<30}{c:<14}{b:<32}")
        print(f"   {'':<30}{'':<14}{det}")
    print()
    print("   EN UNA LINEA")
    print("   Bastan para PONER EN MARCHA el agente y para MEDIR tres de sus")
    print("   cuatro piezas con un margen ancho pero declarable. No bastan")
    print("   para ENTRENAR la unica pieza que necesitaria entrenarse con")
    print("   ellos, y ese hueco no se cierra exportando mas correos de la")
    print("   misma carpeta.")

    # ---------------------------------------------------------------- 8
    titulo(8, "GUARDAR")
    cifras = {
        "version": VERSION_SCRIPT,
        "n_bloques": len(bloques),
        "n_correos": int(len(d)),
        "palabras_media": float(d.palabras.mean()),
        "idiomas": {k: int(v) for k, v in d.idioma.value_counts().items()},
        "dominio_empresa": int(len(empresa)),
        "dominio_generico": int(n_gen),
        "empresas_distintas": int(d[~d.generico].dominio.nunique()),
        "crm_cuentas": int(len(cu)),
        "crm_con_url": int(len(con_url)),
        "crm_con_url_pct": float(len(con_url) / len(cu) * 100),
        "dominio_en_crm": int(n_res),
        "dominio_en_crm_pct": float(n_res / len(empresa) * 100) if len(empresa) else 0.0,
        "norma_detectada": int(n_det),
        "norma_detectada_pct": float(n_det / len(d) * 100),
        "areas": {k: int(v) for k, v in cnt.items()},
        "senal_no_comercial": int(n_no),
    }
    if a.guardar:
        cols = ["id", "canal", "persona_seudo", "empresa_seudo", "dominio",
                "generico", "destinatarios", "idioma", "palabras", "cuerpo"]
        d[cols].to_csv(SALIDA_CORPUS, sep=";", index=False, encoding="utf-8")
        SALIDA_CIFRAS.write_text(json.dumps(cifras, indent=2, ensure_ascii=False),
                                 encoding="utf-8")
        print(f"   [ok] {SALIDA_CORPUS.relative_to(RAIZ)}")
        print(f"   [ok] {SALIDA_CIFRAS.relative_to(RAIZ)}")
        print()
        print("   El fichero original NO se ha copiado ni modificado.")
    else:
        print("   Simulacion: no se ha escrito nada.")
        print("   Vuelve a lanzarlo con --guardar para escribir el corpus")
        print("   seudonimizado y las cifras.")
    print()


if __name__ == "__main__":
    main()
