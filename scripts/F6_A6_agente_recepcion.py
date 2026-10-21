# -*- coding: utf-8 -*-
"""
F6_A6_agente_recepcion.py · A6 · el agente que atiende lo que entra
====================================================================

QUE ES A6
    La fase 6 del proceso: entra un mensaje al buzon general y hay que
    decidir cuatro cosas antes de que lo vea una persona.

       1. ¿De quien es?        -> resolver la identidad contra el CRM
       2. ¿Que pide?           -> detectar la norma citada
       3. ¿A quien le toca?    -> enrutar al area tecnica
       4. ¿Es comercial?       -> o es un proveedor, un curriculum, un evento

    Este script CONSTRUYE las cuatro piezas, las encadena y mide cada una
    por separado. Las dos primeras son reglas y no se entrenan. Las dos
    ultimas son modelos.

LO QUE ESTE SCRIPT APORTA Y NO EXISTIA
    La pieza 3 reutiliza el clasificador de A7, que acierta el 80,51 %
    sobre la poblacion del CRM. El apartado 4.6.6 declara que **no se habia
    medido cuanto se degrada ese 80,51 % sobre texto de cliente**, porque
    solo ocho mensajes traian su area asociada.

    Ya no son ocho. Con 105 correos hay 51 en que la norma citada permite
    deducir el area CON CERTEZA -la correspondencia norma->area no es
    estadistica, es de definicion-, y eso da 51 etiquetas de prueba sobre
    texto de entrada real. Con ellas se mide el desajuste de poblacion que
    estaba declarado y sin cuantificar.

    Es el mismo tipo de hallazgo que dio el orquestador en 4.6.4: un
    componente evaluado en su propia poblacion y medido luego sobre la que
    de verdad le llega.

SOBRE LA PIEZA 4, Y POR QUE EL ACIERTO NO SIRVE AQUI
    De los 105 correos, 13 traen senal de no ser comerciales. O sea que
    decir «todos son comerciales» acierta el 87,6 %. **Un acierto del 87 %
    aqui no significa nada**: lo consigue una regla que no mira el texto.

    Asi que la pieza 4 NO se mide por acierto, sino por si encuentra los
    negativos: AUC y cuantos de los 13 recupera. Y se valida cruzada,
    porque con 13 casos una particion fija depende de la suerte del reparto.

CONFIDENCIALIDAD
    Las areas salen codificadas AR01..AR19. No se imprime ningun correo,
    ningun nombre, ningun dominio concreto ni ningun `Tema`.

COMO SE EJECUTA
    python scripts/F6_A6_agente_recepcion.py
    python scripts/F6_A6_agente_recepcion.py --guardar

NOTA SOBRE LOS NOMBRES DE AGENTE (D24, 07-10-2026)
    Este fichero conserva su nombre antiguo, pero los agentes se
    renumeraron: lo que aqui se llamaba A8 es hoy A7, y lo que se llamaba
    A9 es hoy A8. El texto que imprime usa ya los nombres nuevos. La tabla
    completa esta en 4.6.0 de la memoria y en el ESTADO.
"""

import json
import re
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import LinearSVC

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 04-10-2026"
SEMILLA = 42

RAIZ = Path(__file__).resolve().parent.parent
LIMPIO = RAIZ / "datos" / "01_limpio"
PRIV = RAIZ / "datos" / "_mapeo_privado"
RES = RAIZ / "datos" / "03_resultados"

CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"   # nombre heredado: lleva 105
TEMAS = PRIV / "temas_oportunidades.csv"
OPORT_ANON = LIMPIO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56_anon.csv"
MAPEO = PRIV / "mapeo_areas.json"
DERIVADO = RAIZ / "datos" / "02_derivado"
BRUTO = RAIZ / "datos" / "00_bruto"
CUENTAS_XLSX = BRUTO / "Cuentas activas 25-09-2026 20-36-50.xlsx"

# Dominios de correo que no identifican a ninguna empresa
GENERICOS = {
    "gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.es",
    "live.com", "icloud.com", "aol.com", "protonmail.com", "gmx.com",
    "msn.com", "terra.es", "telefonica.net", "hotmail.es", "outlook.es",
}
# Las etiquetas que puso la autora a mano, casadas con el corpus por
# PREP_casar_etiquetas_correos.py. Sin esto la pieza 4 no se mide.
ETIQUETAS_MANO = LIMPIO / "etiquetas_comercial_A6.csv"

Z95 = 1.959963984540054

# El diccionario norma -> area. Es el mismo de F6_A6_corpus_correos.py; se
# repite aqui a proposito para que este script se pueda leer solo.
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

NO_COMERCIAL = [
    "curriculum", "curriculum vitae", "cv adjunto", "candidatura",
    "oferta de empleo", "practicas", "beca", "tesis", "tfg", "tfm",
    "factura", "remesa", "pago pendiente", "recibo", "domiciliacion",
    "newsletter", "boletin", "darse de baja", "unsubscribe",
    "webinar", "invitacion al evento", "congreso", "feria",
    "proveedor", "presupuesto para ustedes", "les ofrecemos",
    "posicionamiento web", "seo", "marketing digital",
]


def sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def contiene(texto, termino):
    """Busca el termino como palabra, con una salvedad que costo un error.

    Para palabras largas en castellano se tolera un sufijo de hasta tres
    letras, para que «ensayo» encuentre «ensayos» y «caida» encuentre
    «caidas». Eso esta bien.

    Pero para SIGLAS y terminos cortos esa tolerancia es un desastre: con
    ella «reach» —el reglamento— encontraba «reached» y «reaching» en los
    correos en ingles, y el briefing proponia un tema sobre REACH para un
    correo que hablaba de biodegradacion. Tres falsos positivos de 105, dos
    de ellos cambiando el veredicto del correo. Es el error X28.

    Asi que los terminos de seis letras o menos, y los que llevan digitos
    —que son las normas: «en 13432», «2025/40»— se buscan EXACTOS.
    """
    partes = [re.escape(p) for p in termino.split()]
    # Solo se tolera el PLURAL castellano, nada mas. La regla por
    # longitud dejaba fuera «caidas» y la de tres letras cualquiera
    # cazaba «reached». El plural resuelve los dos casos.
    cola = r"(e?s)?"
    return re.search(r"\b" + r"\s+".join(partes) + cola + r"\b",
                     texto) is not None


def dominio_web(url):
    """El dominio de una URL o de un correo, sin www ni rutas.

    Sirve para las dos cosas porque lo que se compara es el
    @dominio del remitente contra el dominio del sitio web de la
    cuenta. Es la via 3 de la decision D18.
    """
    u = str(url).lower().strip()
    if not u or u == "nan":
        return ""
    u = u.split("@")[-1]
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.split("/")[0].split("?")[0].split(":")[0].strip(" .")


def wilson(exitos, n):
    if n == 0:
        return (np.nan, np.nan)
    p = exitos / n
    c = (p + Z95 * Z95 / (2 * n)) / (1 + Z95 * Z95 / n)
    m = Z95 * np.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / (1 + Z95 * Z95 / n)
    return (100 * max(0.0, c - m), 100 * min(1.0, c + m))


def auc(punt, pos):
    p, y = np.asarray(punt, float), np.asarray(pos, bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    orden = np.argsort(p, kind="mergesort")
    r = np.empty(len(p), float)
    r[orden] = np.arange(1, len(p) + 1)
    for v in np.unique(p):
        ig = p == v
        if ig.sum() > 1:
            r[ig] = r[ig].mean()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"PIEZA {n} · {t}")
    print("=" * 76)


# Las cuatro areas que el diccionario de normas cubre, ya en codigo.
#
# Esto permite que el script funcione SIN el mapeo privado, que es lo que
# hace falta para que otra persona pueda ejecutar el sistema sin recibir la
# informacion comercial de la casa. El mapeo solo servia para traducir el
# nombre real al codigo, y aqui el dato ya viene codificado.
#
# No revela nada: AR01..AR05 son etiquetas sin significado para quien no
# tenga el mapeo, y el diccionario de normas usa nombres genericos de
# disciplina —compostabilidad, quimico— que no son informacion reservada.
CODIGOS_NORMA = {
    "caracterizacion y embalajes": "AR01",
    "quimico y procesos": "AR02",
    "envases y economia circular": "AR04",
    "compostabilidad": "AR05",
}


def codigo_area():
    """Devuelve nombre de area -> codigo.

    Si esta el mapeo privado lo usa, porque cubre las diecinueve areas. Si
    no esta, tira de la tabla de arriba, que cubre las cuatro que el
    diccionario de normas necesita. El agente funciona igual en los dos
    casos; sin el mapeo solo pierde la capacidad de nombrar areas que el
    diccionario no toca, y no la usa.
    """
    if not MAPEO.exists():
        print("   [i] Sin el mapeo privado: se usan los codigos de las cuatro")
        print("       areas que el diccionario de normas cubre. El agente")
        print("       funciona igual.")
        return dict(CODIGOS_NORMA), {}
    m = json.loads(MAPEO.read_text(encoding="utf-8"))["campos"]
    bruto = next(v for k, v in m.items() if "rea" in k)
    # el mapeo trae el nombre completo del CRM; aqui se busca por el tramo
    # final, que es como lo nombra el diccionario de normas
    salida = {}
    for nombre, cod in bruto.items():
        corto = sin_tildes(nombre.split(":")[-1]).replace("a. ", "").strip()
        salida[corto] = cod
    return salida, bruto


def cod(nombre, tabla):
    c = tabla.get(sin_tildes(nombre).strip())
    return c or "AR??"


# ===========================================================================
def main():
    guardar = "--guardar" in sys.argv

    print()
    print("#" * 76)
    print("# F6 · A6 · el agente que atiende lo que entra")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    d = pd.read_csv(CORPUS, sep=";")
    d["cuerpo"] = d.cuerpo.fillna("").astype(str)
    d["norm"] = d.cuerpo.map(sin_tildes)
    tabla_cod, bruto = codigo_area()
    salida = {"experimento": "E33", "agente": "A6", "version": VERSION_SCRIPT,
              "n_correos": int(len(d))}

    print()
    print(f"   Correos           : {len(d)}")
    print(f"   Empresas distintas: {d.empresa_seudo.nunique()}")
    print(f"   Idioma            : "
          + " · ".join(f"{k} {v}" for k, v in d.idioma.value_counts().items()))
    print()
    print("   OJO CON EL IDIOMA: una quinta parte entra en ingles. Las reglas")
    print("   de las piezas 1 y 2 funcionan igual, pero cualquier modelo")
    print("   entrenado con texto español lo va a notar. Queda declarado.")

    # ------------------------------------------------------------------ 1
    titulo(1, "¿DE QUIEN ES?  ·  resolver la identidad   (REGLAS)")
    con_dom = d[~d.generico.astype(bool)] if "generico" in d else d
    print(f"   Correos con dominio de empresa: {len(con_dom)} de {len(d)}")
    print()
    print("   Esta pieza ya estaba medida en E22 y no se repite aqui: la")
    print("   resolucion por dominio contra el CRM acierta 32 de 98, un")
    print("   32,7 % [24,2 %, 42,4 %]. Lo que importa para el agente es que")
    print("   el 67 % restante NO se resuelve, y ahi el agente se detiene y")
    print("   avisa, que es la decision D19.")
    salida["pieza1_identidad"] = {"medido_en": "E22", "aciertos": 32,
                                 "de": 98, "pct": 32.7,
                                 "ic": [24.2, 42.4], "tipo": "reglas"}

    # ------------------------------------------------------------------ 2
    titulo(2, "¿QUE PIDE?  ·  detectar la norma citada   (DICCIONARIO)")
    areas_norma = []
    for t in d.norm:
        encontradas = {a for a, terms in NORMAS.items()
                       if any(contiene(t, x) for x in terms)}
        areas_norma.append(encontradas)
    d["areas_norma"] = areas_norma
    d["n_areas"] = d.areas_norma.map(len)
    det = int((d.n_areas > 0).sum())
    lo, hi = wilson(det, len(d))
    print(f"   Correos con alguna norma reconocida: {det} de {len(d)}  "
          f"{100*det/len(d):.1f} %   [{lo:.1f} %, {hi:.1f} %]")
    print()
    print(f"   {'area':<8}{'correos':>9}")
    print("   " + "-" * 18)
    rep = {}
    for a in NORMAS:
        n = int(d.areas_norma.map(lambda s: a in s).sum())
        rep[cod(a, tabla_cod)] = n
        print(f"   {cod(a, tabla_cod):<8}{n:>9}")
    print()
    print(f"   Apuntan a UNA sola area : {(d.n_areas == 1).sum()}")
    print(f"   Apuntan a VARIAS        : {(d.n_areas > 1).sum()}  "
          "<-- aqui el diccionario no decide")
    print(f"   Ninguna norma reconocida: {(d.n_areas == 0).sum()}  "
          "<-- aqui hace falta la pieza 3")
    salida["pieza2_norma"] = {"detectadas": det, "de": int(len(d)),
                              "pct": 100 * det / len(d), "ic": [lo, hi],
                              "una_sola": int((d.n_areas == 1).sum()),
                              "varias": int((d.n_areas > 1).sum()),
                              "ninguna": int((d.n_areas == 0).sum()),
                              "reparto": rep, "tipo": "diccionario"}

    # ------------------------------------------------------------------ 3
    titulo(3, "¿A QUIEN LE TOCA?  ·  A7 sobre texto de cliente real")
    print("   LO QUE SE MIDE AQUI, Y NO ESTABA MEDIDO")
    print("   A7 acierta el 80,51 % sobre `Tema`, que escribe el comercial.")
    print("   En produccion le entra el correo del cliente, que es otra cosa.")
    print("   El 4.6.6 declaraba ese desajuste SIN CUANTIFICAR porque solo")
    n_ded = int((d.n_areas == 1).sum())
    print(f"   ocho mensajes traian area. Ahora hay {n_ded} con area deducible")
    print("   de la norma citada, y la correspondencia norma->area es de")
    print("   definicion, no estadistica.")
    print()

    if not TEMAS.exists() or not OPORT_ANON.exists():
        print("   [!!] No encuentro los datos de entrenamiento de A7.")
        print(f"        {TEMAS.name} / {OPORT_ANON.name}")
        salida["pieza3_enrutado"] = {"estado": "sin datos de entrenamiento"}
    else:
        tm = pd.read_csv(TEMAS, sep=";")
        op = pd.read_csv(OPORT_ANON, sep=";", low_memory=False)
        col_area = next(c for c in op.columns if "rea de Empresa" in c)

        # El fichero anonimizado trae el area YA CODIFICADA (AR01, AR02...),
        # que es el tratamiento de confidencialidad. Asi que todo esto se
        # hace en espacio de codigos, no de nombres.
        codigos_norma = {cod(a, tabla_cod) for a in NORMAS}
        tr = tm.merge(op[["Nº oportunidad", col_area]], on="Nº oportunidad",
                      how="inner").dropna(subset=["Tema", col_area])
        tr = tr[tr[col_area].isin(codigos_norma)]
        print(f"   Areas que el diccionario cubre: "
              f"{', '.join(sorted(codigos_norma))}")
        print(f"   Entrenamiento (del CRM): {len(tr)} oportunidades con `Tema`")
        print(f"   Clases                 : {tr[col_area].nunique()}")

        # la prueba: los correos cuya norma apunta a UNA sola area
        pr = d[d.n_areas == 1].copy()
        pr["area_real"] = pr.areas_norma.map(
            lambda s: cod(next(iter(s)), tabla_cod))
        print(f"   Prueba (correos reales): {len(pr)} con area deducible")

        if len(tr) > 50 and len(pr) > 20:
            # misma receta que A7 en su variante protegida: hashing, que no
            # guarda vocabulario, y clasificador lineal con pesos por clase
            vec = HashingVectorizer(n_features=2 ** 18, ngram_range=(1, 2),
                                    alternate_sign=False, norm="l2")
            Xtr = vec.transform(tr.Tema.astype(str).map(sin_tildes))
            ytr = tr[col_area]
            svc = LinearSVC(C=1.0, class_weight="balanced").fit(Xtr, ytr)

            Xpr = vec.transform(pr.cuerpo.map(sin_tildes))
            pred = svc.predict(Xpr)
            yreal = pr.area_real.values
            acierto = 100 * (pred == yreal).mean()

            # el suelo: la clase mas frecuente del entrenamiento
            may = ytr.value_counts().idxmax()
            suelo = 100 * (yreal == may).mean()
            a_lo, a_hi = wilson(int((pred == yreal).sum()), len(pr))

            print()
            print(f"   {'':<34}{'acierto':>10}{'IC 95 %':>20}")
            print("   " + "-" * 64)
            print(f"   {'A7 en su propia poblacion (4.6.6)':<34}{80.51:>9.1f} %"
                  f"{'—':>20}")
            print(f"   {'A7 sobre correo de cliente real':<34}{acierto:>9.1f} %"
                  f"{f'[{a_lo:.1f}, {a_hi:.1f}]':>20}")
            print(f"   {'Suelo: la clase mas frecuente':<34}{suelo:>9.1f} %"
                  f"{'—':>20}")
            print()
            caida = 80.51 - acierto
            print(f"   CAE {caida:.1f} PUNTOS al cambiar de poblacion.")
            print(f"   Margen que conserva sobre el suelo: {acierto - suelo:+.1f}")
            print()
            if acierto > suelo:
                print("   Sigue por encima del suelo, asi que la senal no se")
                print("   pierde del todo: el enrutado sirve, pero NO con el")
                print("   80,51 % que figuraba. La cifra buena para produccion")
                print(f"   es esta, el {acierto:.1f} %.")
            else:
                print("   NO supera al suelo. Sobre texto de cliente el")
                print("   clasificador no aporta nada, y eso hay que decirlo.")
            print()
            print("   SALVEDADES, que son importantes:")
            print(f"   · Son {len(pr)} casos. El intervalo mide "
                  f"{a_hi-a_lo:.0f} puntos.")
            print("   · La etiqueta de prueba la pone el diccionario de normas,")
            print("     no una persona. Es cierta por definicion, pero solo")
            print("     existe donde se cita una norma, que son los casos mas")
            print(f"     faciles. En los otros {len(d)-len(pr)} no hay con que medir.")
            print("   · Solo entran las cuatro areas que el diccionario cubre,")
            print("     de las diecinueve que existen.")

            salida["pieza3_enrutado"] = {
                "entrenamiento": int(len(tr)), "prueba": int(len(pr)),
                "clases": int(ytr.nunique()),
                "acierto_poblacion_propia": 80.51,
                "acierto_correo_real": acierto, "ic": [a_lo, a_hi],
                "suelo": suelo, "caida_puntos": caida,
                "margen_sobre_suelo": acierto - suelo,
                "etiqueta": "deducida del diccionario de normas",
                "tipo": "modelo reutilizado de A7"}
        else:
            print("   [!!] Datos insuficientes para la prueba")
            salida["pieza3_enrutado"] = {"estado": "insuficiente"}

    # ------------------------------------------------------------------ 4
    titulo(4, "¿ES COMERCIAL?  ·  la unica pieza que estos correos entrenan")

    # --- de donde sale la etiqueta -----------------------------------------
    # La lista de terminos NO SIRVE: al revisar el contexto de los 15 que
    # marcaba, al menos doce eran clientes. Diez decian «proveedor» hablando
    # de SUS proveedores, que es senal comercial, no lo contrario. Es el
    # error X25. Asi que si existe el etiquetado a mano se usa ese, y si no
    # existe NO SE PUBLICA NINGUNA CIFRA.
    etiquetas = ETIQUETAS_MANO if ETIQUETAS_MANO.exists() else None
    if etiquetas is None:
        print("   NO HAY ETIQUETADO A MANO, asi que esta pieza NO SE MIDE.")
        print()
        print("   Se intento con una lista de terminos y salio mal: marcaba 15")
        print("   correos y al mirarlos uno a uno **al menos doce eran")
        print("   clientes**. Diez decian «proveedor» refiriendose a SUS")
        print("   proveedores:")
        print()
        print("      «la caja la fabrica nuestro proveedor, necesitamos saber")
        print("       que ensayos debe superar»")
        print()
        print("   Eso es un cliente pidiendo un ensayo. En este corpus la")
        print("   palabra «proveedor» es senal COMERCIAL, o sea lo contrario")
        print("   de lo que la lista suponia. Un modelo entrenado sobre esa")
        print("   etiqueta aprende justo al reves. Queda como error X25.")
        print()
        print("   PARA CERRARLO:")
        print("      python scripts/PREP_etiquetar_correos_A6.py")
        print("   rellenar la columna, y volver a lanzar esto. Veinte minutos.")
        salida["pieza4_comercial"] = {
            "estado": "SIN MEDIR · la etiqueta automatica resulto erronea",
            "lista_marcaba": 15,
            "falsos_positivos_al_revisar": "al menos 12 de 15",
            "motivo": "«proveedor» aparece en correos de clientes que hablan "
                      "de sus propios proveedores: es senal comercial",
            "como_se_cierra": "PREP_etiquetar_correos_A6.py + 20 minutos"}
        d["no_com"] = 0
        n_neg = 0

    if etiquetas is not None:
        man = pd.read_csv(etiquetas, sep=";")
        man["v"] = man.categoria.astype(str).str.strip().str.upper()
        man["es_no"] = man.v.str.contains("NO")
        print(f"   ETIQUETADO A MANO POR LA AUTORA: {etiquetas.name}")
        print(f"      comercial {int((~man.es_no).sum())}"
              f" · no comercial {int(man.es_no.sum())}")
        d = d.merge(man[["id", "es_no"]], on="id", how="left")
        falta = int(d.es_no.isna().sum())
        if falta:
            print(f"   [!!] {falta} correos sin etiqueta. Vuelve a lanzar")
            print("        PREP_casar_etiquetas_correos.py --guardar")
            raise SystemExit(1)
        d["no_com"] = d.es_no.astype(int)
        n_neg = int(d.no_com.sum())
    suelo4 = 100 * (1 - d.no_com.mean())
    print(f"   Con senal de NO comercial: {n_neg} de {len(d)}  "
          f"({100*n_neg/len(d):.1f} %)")
    print(f"   SUELO: decir «todos comerciales» acierta {suelo4:.1f} %")
    print()
    print("   POR ESO EL ACIERTO NO SE USA AQUI. Se mide si encuentra los")
    print(f"   {n_neg} negativos, con validacion cruzada.")
    print()

    if n_neg >= 8:
        X = d.cuerpo.map(sin_tildes).values
        y = d.no_com.values
        vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=1,
                              max_features=20000)
        clf = LogisticRegression(max_iter=2000, class_weight="balanced")
        # cinco pliegues estratificados: con 13 negativos, una particion fija
        # depende demasiado de donde caigan
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
        punt = np.zeros(len(y), float)
        for itr, ite in cv.split(X, y):
            Xtr = vec.fit_transform(X[itr])
            clf.fit(Xtr, y[itr])
            punt[ite] = clf.predict_proba(vec.transform(X[ite]))[:, 1]
        a = auc(punt, y)
        # Con 14 negativos el AUC solo no dice nada: hace falta el intervalo.
        rng = np.random.default_rng(SEMILLA)
        # OJO: y viene como enteros 0/1 y «~y» seria negacion DE BITS, no
        # logica: ~0 da -1, que no es cero, asi que la condicion se cumplia
        # siempre y se descartaban todas las remuestras. Hay que pasar a
        # booleano antes de negar.
        yb = y.astype(bool)
        ms = []
        for _ in range(2000):
            k = rng.integers(0, len(yb), len(yb))
            if yb[k].all() or (~yb[k]).all():
                continue
            ms.append(auc(punt[k], yb[k]))
        a_lo, a_hi = np.percentile(ms, [2.5, 97.5])
        rec = []
        print(f"   AUC (validacion cruzada): {a:.3f}  "
              f"[{a_lo:.3f}, {a_hi:.3f}]")
        print(f"   El intervalo mide {a_hi-a_lo:.2f}, que es lo que cabe")
        print(f"   esperar con solo {n_neg} casos negativos.")
        print()
        print("   Si el agente manda a revision los N correos mas sospechosos:")
        print(f"   {'N':>5}{'negativos que pilla':>22}{'de':>5}{'%':>8}")
        print("   " + "-" * 42)
        for N in (10, 15, 20, 30):
            top = np.argsort(-punt)[:N]
            pilla = int(y[top].sum())
            rec.append({"n": N, "pilla": pilla, "de": n_neg})
            print(f"   {N:>5}{pilla:>22}{n_neg:>5}{100*pilla/n_neg:>7.0f} %")
        print()
        print("   ASI SE USA: no como clasificador que decide, sino como cola")
        print("   de revision ordenada. Una persona mira los veinte primeros")
        print("   en vez de los ciento cinco.")
        print()
        print("   LO QUE CAMBIO AL USAR LA ETIQUETA DE LA AUTORA")
        print("   Antes la etiqueta la ponia una lista de terminos y el AUC")
        print("   salia 0,700. Al comprobarla contra el juicio de la autora,")
        print("   **la lista acertaba 2 de los 15 que marcaba**: diez decian")
        print("   «proveedor» en correos de clientes que hablaban de SUS")
        print("   proveedores, que es senal comercial, no lo contrario.")
        print(f"   Con la etiqueta buena el AUC es {a:.3f}. Es el error X25.")
        print()
        print("   Y LO QUE SIGUE SIN SOSTENERSE:")
        print(f"   · {n_neg} negativos son pocos, y el intervalo lo dice:")
        print(f"     mide {a_hi-a_lo:.2f} puntos. La cifra orienta, no cierra.")
        print("   · La etiqueta la pone UNA sola persona, que ademas es la")
        print("     autora del sistema. Un segundo etiquetador daria la")
        print("     concordancia entre personas, que es el techo real de")
        print("     esta tarea. No se tiene.")
        print("   · Se mide sobre los correos que llegaron al buzon general")
        print("     y alguien reenvio: no es una muestra aleatoria de todo")
        print("     lo que entra.")
        salida["pieza4_comercial"] = {
            "negativos": n_neg, "de": int(len(d)), "suelo": suelo4,
            "auc_cv": a, "auc_ic": [float(a_lo), float(a_hi)],
            "recuperacion": rec,
            "etiqueta": "ETIQUETADO A MANO por la autora, 105 correos",
            "auc_con_etiqueta_automatica": 0.700,
            "lista_automatica_acertaba": "2 de los 15 que marcaba",
            "limitacion": "un solo etiquetador; sin concordancia entre personas"}
    else:
        print("   [!!] Menos de ocho negativos: no se entrena.")
        salida["pieza4_comercial"] = {"negativos": n_neg, "estado": "insuficiente"}

    # ------------------------------------------------------------------ 5
    titulo(5, "EL AGENTE ENCADENADO  ·  que decide con cada correo")
    # OJO CON LO QUE ESTA FUNCION NO MIRA.
    #
    # No consulta la identidad. Enrutar al area tecnica no necesita saber
    # quien escribe: si alguien pregunta por la EN 13432, va a
    # compostabilidad sea quien sea. Eso es correcto.
    #
    # Pero la decision D19 dice que cuando la identidad NO se resuelve el
    # sistema no da de alta la cuenta: la ve una persona. Asi que «lo
    # resuelve solo» no es lo mismo para una cuenta conocida que para una
    # desconocida, y el paso siguiente lo separa en vez de darlo por igual.
    def decide(fila):
        if fila.no_com:
            return "a revision: puede no ser comercial"
        if fila.n_areas == 1:
            return "enrutado por norma"
        if fila.n_areas > 1:
            return "a revision: la norma apunta a varias areas"
        return "enrutado por el clasificador"
    d["decision"] = d.apply(decide, axis=1)
    print(f"   {'decision':<46}{'correos':>9}{'%':>8}")
    print("   " + "-" * 64)
    reparto = {}
    for k, v in d.decision.value_counts().items():
        reparto[k] = int(v)
        print(f"   {k:<46}{v:>9}{100*v/len(d):>7.1f} %")
    auto = int((~d.decision.str.startswith("a revision")).sum())
    print()
    print(f"   RESUELVE SOLO: {auto} de {len(d)}  ({100*auto/len(d):.1f} %)")
    print(f"   PASA A PERSONA: {len(d)-auto}  "
          f"({100*(len(d)-auto)/len(d):.1f} %)")

    # ----------------------------------------------------------------
    # Y AHORA LO QUE ESA CIFRA ESCONDE.
    #
    # «Resuelve solo» cuenta igual un correo de una cuenta que ya existe
    # que uno de una empresa desconocida. Pero no son lo mismo: por D19,
    # cuando la identidad no se resuelve el sistema NO da de alta la
    # cuenta, asi que ese correo acaba viendolo una persona de todos
    # modos aunque el area este bien enrutada.
    # ----------------------------------------------------------------
    # Se resuelve por las DOS vias, no solo por la web.
    #
    # El export de cuentas trae ahora una columna `Dominio` con la parte de
    # detras de la arroba del correo asociado. Comparar el @dominio del
    # remitente contra ESO es comparar lo mismo con lo mismo; contra el
    # `Sitio web` no lo era, y esa confusion costo el error X19.
    #
    # E35 lo midio: la via Dominio resuelve 51 de 98 frente a 35 de la via
    # web, con p = 0,0004. Y son complementarias, asi que se usan las dos.
    if CUENTAS_XLSX.exists():
        cu = pd.read_excel(CUENTAS_XLSX)
        cu.columns = [c.strip() for c in cu.columns]
        col_w = next((c for c in cu.columns if "Sitio web" in c), None)
        col_d = next((c for c in cu.columns if c.strip().lower() == "dominio"), None)
        dominios_crm = set()
        for col in (col_w, col_d):
            if col is not None:
                dominios_crm |= {x for x in cu[col].map(dominio_web) if x}
        dominios_crm -= GENERICOS
        print()
        print(f"   Identidad resuelta por las dos vias (web + Dominio), "
              f"{len(dominios_crm)} dominios del CRM")
    else:
        cuentas = [DERIVADO / f for f in ("cuentas_train.csv", "cuentas_val.csv",
                                          "cuentas_test.csv")]
        if not all(f.exists() for f in cuentas):
            dominios_crm = set()
        else:
            cu = pd.concat([pd.read_csv(f, usecols=["url"]) for f in cuentas],
                           ignore_index=True)
            dominios_crm = {x for x in cu.url.map(dominio_web) if x}
        print()
        print("   [!!] No encuentro el export de cuentas con la columna")
        print("        Dominio. Se usa solo la via web, que resuelve menos.")

    if dominios_crm:
        d["cuenta_localizada"] = (~d.generico.astype(bool)) & \
            d.dominio.map(lambda x: dominio_web(x) in dominios_crm)
        loc = int(d.cuenta_localizada.sum())

        print()
        print("   PERO «RESUELVE SOLO» NO ES LO MISMO SEGUN LA CUENTA")
        print()
        print(f"   {'':<30}{'cuenta':>10}{'cuenta NO':>12}")
        print(f"   {'':<30}{'localizada':>10}{'localizada':>12}")
        print("   " + "-" * 54)
        a_loc = int((d.cuenta_localizada &
                     ~d.decision.str.startswith("a revision")).sum())
        a_nol = auto - a_loc
        print(f"   {'el agente lo resuelve solo':<30}{a_loc:>10}{a_nol:>12}")
        print(f"   {'pasa a una persona':<30}"
              f"{int(d.cuenta_localizada.sum())-a_loc:>10}"
              f"{len(d)-loc-a_nol:>12}")
        print()
        print(f"   De los {auto} que el agente resuelve, solo {a_loc} son de")
        print(f"   cuentas que estan en el sistema de gestion.")
        print()
        print(f"   LOS OTROS {a_nol} llevan el area bien enrutada, pero por D19")
        print("   necesitan que una persona decida si se da de alta la cuenta.")
        print()
        print(f"   ASI QUE LA CIFRA HONESTA DE AUTOMATIZACION COMPLETA ES")
        print(f"   {a_loc} de {len(d)}  =  {100*a_loc/len(d):.1f} %,")
        print(f"   no el {100*auto/len(d):.1f} %.")
        print()
        print("   El enrutado SI vale para los otros: ahorra a esa persona")
        print("   decidir el area, que es la parte tecnica. Lo que no ahorra")
        print("   es la decision de alta, que es la que D19 reserva.")
        salida["pieza5_cadena_por_identidad"] = {
            "cuenta_localizada": loc,
            "resuelve_solo_y_cuenta_localizada": a_loc,
            "resuelve_solo_sin_cuenta": a_nol,
            "pct_automatizacion_completa": 100 * a_loc / len(d),
            "pct_sin_mirar_identidad": 100 * auto / len(d),
            "nota": "por D19 el sistema no da de alta cuentas por su cuenta, "
                    "asi que un correo bien enrutado de una empresa "
                    "desconocida sigue necesitando a una persona"}
    else:
        print()
        print("   [!!] no encuentro las cuentas: no se puede cruzar con la")
        print("        identidad y la cifra queda sin matizar")
    print()
    print("   Cada correo detenido lleva escrito el motivo, igual que en el")
    print("   orquestador. El agente no adivina cuando no sabe.")
    salida["pieza5_cadena"] = {"reparto": reparto, "resuelve_solo": auto,
                               "a_persona": int(len(d) - auto)}

    # ------------------------------------------------------------------
    titulo(6, "VEREDICTO")
    print(f"   {'pieza':<26}{'como':<14}{'estado'}")
    print("   " + "-" * 70)
    print(f"   {'1 · identidad':<26}{'reglas':<14}CONSTRUIDA y medida (E22)")
    print(f"   {'2 · norma citada':<26}{'diccionario':<14}CONSTRUIDA y medida aqui")
    p3 = salida.get("pieza3_enrutado", {})
    if "acierto_correo_real" in p3:
        print(f"   {'3 · enrutado al area':<26}{'modelo A7':<14}"
              f"CONSTRUIDA · {p3['acierto_correo_real']:.1f} % "
              f"sobre correo real")
    else:
        print(f"   {'3 · enrutado al area':<26}{'modelo A7':<14}sin medir")
    print(f"   {'4 · comercial / no':<26}{'modelo':<14}"
          "CONSTRUIDA, etiqueta automatica")
    print()
    print("   A6 ESTA CONSTRUIDO Y ENCADENADO. Tres de sus cuatro piezas")
    print("   tienen medicion defendible; la cuarta funciona como cola de")
    print("   revision y necesita etiquetado humano para publicarse como")
    print("   rendimiento.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return
    RES.mkdir(parents=True, exist_ok=True)
    f = RES / "a6_agente_recepcion.json"
    f.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=float),
                 encoding="utf-8")
    print()
    print(f"   [ok] {f.name}")
    print()


if __name__ == "__main__":
    main()
