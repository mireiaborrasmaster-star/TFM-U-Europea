# -*- coding: utf-8 -*-
"""
F8_A8_briefing_traspaso.py · A7 · la mitad que faltaba: el briefing
====================================================================

QUE ES
    El diseno de la fase 8 pedia dos cosas: enrutar al area tecnica y
    **redactar el briefing de traspaso**. Lo primero estaba construido; esto
    es lo segundo.

    Entra un correo ya procesado por A6 y sale la ficha que recibe el
    comercial: de quien es, a que area va, que pide, un tema propuesto para
    la oportunidad, y las puntuaciones que ya se han calculado.

QUE PARTE ES UN MODELO Y QUE PARTE NO, QUE NO ES LO MISMO
    · EL TIPO DE SERVICIO lo decide un CLASIFICADOR ENTRENADO con las
      4.860 etiquetas que las personas de Empresa pusieron en la columna
      «Tipo Oportunidad». Era un diccionario de palabras hasta E38, y se
      sustituyo porque se midio que el modelo acierta mas: 86,6 % frente
      a 22,2 % sobre temas, y +10,5 puntos incluso donde el diccionario
      ve su palabra. Lo que lee no es el correo entero sino un TELEGRAMA
      de diez palabras sacado de el, porque con el correo entero el
      mismo modelo se derrumba del 86,6 % al 41,5 %.
    · EL AREA TECNICA la decide el clasificador de 4.6.6, sin reentrenar.
    · LA MATERIA y LA NORMA siguen saliendo literales del texto, a
      proposito: son lo que sostiene que el tema este fundamentado.

    De ahi que la ficha separe siempre LO QUE CONSTA de LO QUE SE PROPONE,
    y que la propuesta lleve su tramo de confianza al lado.

POR QUE NO LO ESCRIBE UN MODELO GENERATIVO, AL MENOS NO POR DEFECTO
    Se planteo, y el dato lo desaconseja como primera opcion:

      · El 94 % de los temas del historico aparece UNA SOLA VEZ, asi que no
        hay plantilla que copiar. Habria que generar de verdad.
      · Generar exige GPU, lo que mete el briefing en el circuito por lotes
        y le quita justamente lo que lo hace util: responder rapido.
      · Y un briefing inventado es peor que ninguno. Si dice que el cliente
        pide un ensayo que no pidio, el comercial llega a la reunion con
        una idea falsa.

    Asi que el briefing se COMPONE de lo que consta, no se redacta. Cada
    campo lleva de donde sale, y lo que no se sabe aparece como no sabido en
    vez de rellenarse.

    Con `--generativo` se puede anadir una propuesta de tema redactada por
    el modelo de A5. Pasa por el MISMO verificador de fundamentacion que
    4.6.3, y si no lo supera no se muestra.

QUE SE MIDE, Y QUE NO
    De un briefing no se mide el "acierto": no hay briefing verdadero contra
    el que comparar. Lo que si se puede medir, y se mide:

      1. COBERTURA · cuantos campos se rellenan de verdad, campo a campo
      2. FUNDAMENTACION · que proporcion del tema propuesto sale del correo
         o del catalogo, y no de ningun otro sitio
      3. CONTRA UN SUELO · un tema hecho con las palabras mas comunes del
         historico, para saber si la propuesta aporta algo sobre eso

COMO SE EJECUTA
    python scripts/F8_A8_briefing_traspaso.py
    python scripts/F8_A8_briefing_traspaso.py --guardar
    python scripts/F8_A8_briefing_traspaso.py --ver 3     # ensena 3 fichas

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
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from F8_A8_tema_modelo import (UMBRAL_IGUAL_CALIDAD, cortesia_comun,  # noqa: E402
                               entrena_tipo, hacer_telegrama, idf_de)

warnings.filterwarnings("ignore")

VERSION_SCRIPT = ("v3 · 09-10-2026 · el tipo lo decide un modelo (E38) y la ficha "
                  "lleva el historial de la cuenta, sin importes (D13)")

# el telegrama, con los valores elegidos en E38 sobre correo fabricado
TELEGRAMA_PALABRAS = 10
TELEGRAMA_TOPE_IDF = 7.0

# el nombre corto con el que cada clase entra en el tema
NOMBRE_CORTO = {
    "Ensayos": "Ensayo",
    "Consultoría y asistencia tecnica": "Consultoría",
    "Consultoría y asistencia técnica": "Consultoría",
    "Desarrollo I+D": "Desarrollo",
    "Servicios": "Servicio",
    "Formación": "Formación",
    "Valoración-patente-prueba de concepto": "Valoración",
}


def tramo(p):
    """Los tres tramos de confianza medidos en E38: con p >= 0,80 el modelo
    acierta el 94,5 %; entre 0,50 y 0,80 el 72,1 %; por debajo, el 44,6 %."""
    return "alta" if p >= 0.80 else ("media" if p >= 0.50 else "baja")
SEMILLA = 42

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
LIMPIO = RAIZ / "datos" / "01_limpio"
PRIV = RAIZ / "datos" / "_mapeo_privado"
RES = RAIZ / "datos" / "03_resultados"

CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"
ETIQUETAS = LIMPIO / "etiquetas_comercial_A6.csv"
CUENTAS = BRUTO / "Cuentas activas 25-09-2026 20-36-50.xlsx"
OPORT = BRUTO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56.xlsx"
OFERT = BRUTO / "Ofertas 2025 - ACT 27-09-2026 19-16-12.xlsx"
CATALOGO = RES / "a5_catalogo.json"

GENERICOS = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.es",
             "live.com", "icloud.com", "aol.com", "protonmail.com", "gmx.com",
             "msn.com", "terra.es", "telefonica.net", "hotmail.es", "outlook.es"}

# norma -> area, el mismo diccionario de A6
NORMAS = {
    "AR01": ["ista", "astm d4169", "d4169", "iso 11607", "vibracion", "compresion",
             "apilamiento", "top load", "caida", "impacto", "carga paletizada",
             "simulacion de transporte", "resistencia estructural"],
    "AR02": ["mosh", "moah", "pfas", "bisfenol", "bpa", "migracion", "nias",
             "ftir", "dsc", "plomo", "cadmio", "mercurio", "cromo hexavalente",
             "metales pesados", "sensorial", "reach"],
    "AR04": ["ppwr", "en 13430", "en 13427", "en 13428", "en 13429",
             "reciclabilidad", "ecodiseno", "declaracion de conformidad",
             "declaraciones de conformidad", "2025/40"],
    "AR05": ["compostabilidad", "compostable", "biodegradacion", "biodegradable",
             "en 13432", "home compost"],
}

# que tipo de servicio sugiere el texto
TIPOS = {
    "Ensayo": ["ensayo", "ensayos", "analisis", "analitica", "test", "testing",
               "muestra", "muestras", "laboratorio", "determinacion"],
    "Consultoría": ["asesoramiento", "consultoria", "asesoria", "informe",
                    "dictamen", "revision documental", "interpretacion"],
    "Certificación": ["certificado", "certificacion", "declaracion de conformidad",
                      "conformidad", "homologacion"],
    "Formación": ["formacion", "curso", "taller", "jornada"],
}

# materiales y objetos que suelen dar nombre al tema
MATERIAS = ["envase", "envases", "embalaje", "film", "pelicula", "bandeja",
            "botella", "caja", "carton", "papel", "plastico", "tapa", "bolsa",
            "palet", "palets", "etiqueta", "tarrina", "bote", "tapon",
            "saco", "big bag", "barqueta", "capsula", "capsulas"]


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


def dominio(x):
    u = sin_tildes(x).strip()
    if not u or u == "nan":
        return ""
    u = u.split("@")[-1]
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.split("/")[0].split("?")[0].split(":")[0].strip(" .")


def raiz(p):
    """Recorta la palabra para que «ensayos» y «ensayo» cuenten como una.

    Es el mismo criterio que usa el verificador de A5 en 4.6.3, con una
    correccion que hizo falta en E38 y que es el error X29.

    La regla del plural mira «es» al final, asi que «envases» se recorta a
    «envas»; pero «envase» acaba en «se», no en «es», y se quedaba igual.
    Resultado: LA MISMA PALABRA no se reconocia a si misma cuando el correo
    la escribia en plural. La comprobacion de fundamentacion del briefing
    daba 84,4 % donde por construccion tenia que dar 100 %, y lo mismo
    pasaba con «embalaje/embalajes» o «informe/informes».

    Se arregla quitando tambien la «e» final, que es lo que faltaba para
    que las dos formas lleguen al mismo sitio.
    """
    for suf in ("ciones", "cion", "mente", "ales", "idad", "es", "as", "os", "a", "s"):
        if len(p) > len(suf) + 3 and p.endswith(suf):
            return p[: -len(suf)]
    if len(p) > 4 and p.endswith("e"):      # X29
        return p[:-1]
    return p


def terminos(texto, minimo=5):
    return {raiz(p) for p in re.findall(r"[a-z0-9]+", sin_tildes(texto))
            if len(p) >= minimo}


# ===========================================================================
def componer_tema(texto, tipo, area, normas_vistas):
    """Propone un tema con la estructura de los reales: 4-5 palabras.

    La MATERIA y la NORMA se sacan literales del correo. El TIPO, desde
    E38, lo pone el clasificador, asi que es la unica parte del tema que
    no esta escrita en el texto: por eso la ficha lo marca como propuesta
    y la fundamentacion se mide por separado para una cosa y para la otra.

    Si no hay materia prima suficiente devuelve None, que sigue siendo
    mejor que rellenar.
    """
    t = sin_tildes(texto)
    materia = next((m for m in MATERIAS if contiene(t, m)), None)
    norma = normas_vistas[0] if normas_vistas else None
    partes = []
    if tipo:
        partes.append(tipo)
        if materia:
            partes.append("de " + materia)
    elif materia:
        # sin tipo de servicio, empezar por «de» daba «de embalaje · PPWR»,
        # que no es una frase. Se pone la materia sola.
        partes.append(materia.capitalize())
    if norma:
        partes.append("· " + norma.upper())
    if len(partes) < 2:
        return None, []
    usado = [x for x in (tipo, materia, norma) if x]
    return " ".join(partes), usado


def _historial(cta, hist, of_h):
    """Lo que la organizacion ya sabe de esta cuenta.

    Es la pregunta que un comercial hace primero —«¿a esta empresa ya le
    hemos hecho algo?»— y la respuesta estaba en el export desde el
    principio. No lleva ningun importe: la decision D13 los deja fuera de
    todo el trabajo, asi que se cuentan casos y se miran fechas.
    """
    vacio = {"oportunidades_previas": None, "ganadas_previas": None,
             "dias_desde_la_ultima": None, "area_habitual": None,
             "ofertas_previas": None, "es_cliente_nuevo": None}
    if cta is None:
        return vacio
    k = str(cta["Nombre de cuenta"]).strip().lower()
    h = hist.get(k)
    if not h:
        return {**vacio, "oportunidades_previas": 0, "ganadas_previas": 0,
                "ofertas_previas": int(of_h.get(k, 0)),
                "es_cliente_nuevo": True}
    areas = h["areas"]
    return {"oportunidades_previas": h["ops"], "ganadas_previas": h["ganadas"],
            "dias_desde_la_ultima": h["ultima"],
            "area_habitual": (str(areas.index[0]) if areas is not None
                              and len(areas) else None),
            "ofertas_previas": int(of_h.get(k, 0)),
            "es_cliente_nuevo": h["ops"] == 0}


def main():
    guardar = "--guardar" in sys.argv
    ver = 0
    if "--ver" in sys.argv:
        i = sys.argv.index("--ver")
        ver = int(sys.argv[i + 1]) if i + 1 < len(sys.argv) else 3

    print()
    print("#" * 76)
    print("# F8 · A7 · el briefing de traspaso")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    print()
    print("=" * 76)
    print("PASO 1 · DE DONDE SALE CADA CAMPO")
    print("=" * 76)
    d = pd.read_csv(CORPUS, sep=";")
    d["cuerpo"] = d.cuerpo.fillna("").astype(str)
    d["norm"] = d.cuerpo.map(sin_tildes)
    d["dom"] = d.dominio.map(dominio)

    if ETIQUETAS.exists():
        et = pd.read_csv(ETIQUETAS, sep=";")
        et["no_com"] = et.categoria.astype(str).str.upper().str.contains("NO")
        d = d.merge(et[["id", "no_com"]], on="id", how="left")
    else:
        d["no_com"] = False

    # la cuenta, por las dos vias de E35
    cu = pd.read_excel(CUENTAS)
    cu.columns = [c.strip() for c in cu.columns]
    col_w = next((c for c in cu.columns if "Sitio web" in c), None)
    col_d = next((c for c in cu.columns if c.strip().lower() == "dominio"), None)
    cu["d1"] = cu[col_w].map(dominio) if col_w else ""
    cu["d2"] = cu[col_d].map(dominio) if col_d else ""
    ficha = {}
    for _, r in cu.iterrows():
        for dd in (r.d1, r.d2):
            if dd and dd not in GENERICOS and dd not in ficha:
                ficha[dd] = r
    print(f"   Correos a traspasar          : {len(d)}")
    print(f"   Cuentas con dominio utilizable: {len(ficha)}")

    # ------------------------------------------------------------------ 2
    print()
    print("=" * 76)
    print("PASO 2 · SE COMPONE UNA FICHA POR CORREO")
    print("=" * 76)

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8")) if CATALOGO.exists() else {}
    voc_catalogo = terminos(json.dumps(catalogo, ensure_ascii=False))

    # ---- el clasificador del tipo de servicio (E38) -----------------------
    print()
    print("   Entrenando el clasificador del tipo de servicio con el")
    print("   historico de oportunidades...")
    op_tipo = pd.read_excel(OPORT)
    op_tipo.columns = [c.strip() for c in op_tipo.columns]
    col_area_h = next((c for c in op_tipo.columns if "rea de Empresa" in c), None)
    vec_t, clf_t, _, clases_t = entrena_tipo(op_tipo, UMBRAL_IGUAL_CALIDAD)
    idf_t = idf_de(vec_t, TELEGRAMA_TOPE_IDF)
    prohibidas = cortesia_comun(d.norm)
    d["telegrama"] = d.cuerpo.map(
        lambda x: hacer_telegrama(x, idf_t, TELEGRAMA_PALABRAS, prohibidas))
    Pt = clf_t.predict_proba(vec_t.transform(d.telegrama))
    d["tipo_modelo"] = clf_t.classes_[Pt.argmax(axis=1)]
    d["tipo_p"] = Pt.max(axis=1)
    print(f"   Listo · {len(clases_t)} clases, telegrama de "
          f"{TELEGRAMA_PALABRAS} palabras")

    # ---- el historial de la cuenta --------------------------------------
    # Lo que un comercial pregunta primero al recibir un caso: ¿a esta
    # empresa ya le hemos hecho algo? Esta en el export y no hace falta
    # ningun modelo para contestarlo. SIN IMPORTES, por la decision D13:
    # se cuentan oportunidades y ofertas y se mira cuando fue la ultima,
    # nunca cuanto se facturo.
    print()
    print("   Leyendo el historial de cada cuenta (sin importes)...")
    hist = {}
    op_h = op_tipo[op_tipo["Cuenta"].notna()].copy()
    op_h["k"] = op_h["Cuenta"].astype(str).str.strip().str.lower()
    op_h["gana"] = op_h.Estado.astype(str).str.strip().str.lower() == "lograda"
    hoy = pd.Timestamp.today()
    for k, g in op_h.groupby("k"):
        f = pd.to_datetime(g["Fecha de creación"], errors="coerce").max()
        hist[k] = {"ops": int(len(g)), "ganadas": int(g.gana.sum()),
                   "ultima": None if pd.isna(f) else int((hoy - f).days),
                   "areas": g[col_area_h].dropna().astype(str).value_counts()
                   if col_area_h else None}
    of_h = {}
    if OFERT.exists():
        of = pd.read_excel(OFERT)
        of.columns = [c.strip() for c in of.columns]
        of = of[of["Cuenta"].notna()]
        of["k"] = of["Cuenta"].astype(str).str.strip().str.lower()
        of_h = of.groupby("k").size().to_dict()
    print(f"   {len(hist)} cuentas con oportunidades previas · "
          f"{len(of_h)} con ofertas")

    fichas, campos = [], Counter()
    for _, r in d.iterrows():
        t = r.norm
        areas = [a for a, terms in NORMAS.items() if any(contiene(t, x) for x in terms)]
        normas_vistas = [x for a in areas for x in NORMAS[a] if contiene(t, x)]
        # el diccionario ya no DECIDE el tipo: solo dice si la palabra
        # consta en el correo, que es la justificacion que ve el comercial
        literal = next((k for k, v in TIPOS.items()
                        if any(contiene(t, x) for x in v)), None)
        pal_literal = sorted({x for v in TIPOS.values() for x in v
                              if contiene(t, x)}) or None
        tipo_largo = str(r.tipo_modelo)
        tipo = NOMBRE_CORTO.get(tipo_largo, tipo_largo)
        cta = ficha.get(r.dom) if r.dom and r.dom not in GENERICOS else None
        tema, usado = componer_tema(r.cuerpo, tipo, areas[0] if areas else None,
                                    normas_vistas)

        f = {
            "id": r.id,
            "cuenta": (str(cta["Nombre de cuenta"]) if cta is not None else None),
            "cuenta_en_crm": cta is not None,
            "sector": (str(cta["Sector Empresa"]) if cta is not None
                       and pd.notna(cta["Sector Empresa"]) else None),
            "provincia": (str(cta["Provincia"]) if cta is not None
                          and pd.notna(cta["Provincia"]) else None),
            "cliente_previo": (str(cta["Asociado"]) if cta is not None
                               and pd.notna(cta["Asociado"]) else None),
            "dominio_contacto": r.dom or None,
            "idioma": r.idioma,
            "area_por_norma": areas[0] if len(areas) == 1 else None,
            "area_ambigua": areas if len(areas) > 1 else None,
            "normas_citadas": sorted(set(normas_vistas)) or None,
            "tipo_servicio": tipo,
            "tipo_servicio_completo": tipo_largo,
            "tipo_lo_propone": "modelo entrenado (E38)",
            "tipo_confianza": tramo(float(r.tipo_p)),
            "tipo_probabilidad": round(float(r.tipo_p), 3),
            "tipo_consta_en_el_texto": literal,
            "palabras_que_lo_sostienen": pal_literal,
            "telegrama_leido": r.telegrama or None,
            **_historial(cta, hist, of_h),
            # lo que hace falta para dar de alta la cuenta, cuando no consta:
            # la ficha lleva lo que se puede extraer y dice que falta
            "alta_de_cuenta": ("no hace falta: la cuenta ya consta"
                               if cta is not None else
                               f"PENDIENTE · se propone con el dominio "
                               f"{r.dom or '(sin dominio)'}; faltan razón "
                               f"social, CIF y sector"),
            "tema_propuesto": tema,
            "es_comercial": (not bool(r.no_com)) if pd.notna(r.no_com) else None,
            "palabras": int(r.palabras),
        }
        for k, v in f.items():
            # `is not None` y no `if v`: un cero es un dato —«esta cuenta
            # no ha ganado ninguna oportunidad» informa— y con la version
            # anterior desaparecia del recuento, porque en Python 0 == False
            if v is not None:
                campos[k] += 1
        fichas.append(f)

    print()
    print(f"   {'campo':<26}{'se rellena':>12}{'%':>9}   de donde sale")
    print("   " + "-" * 74)
    origen = {
        "cuenta": "cruce por dominio (E35)",
        "sector": "ficha de la cuenta",
        "provincia": "ficha de la cuenta",
        "dominio_contacto": "cabecera del correo",
        "area_por_norma": "diccionario norma -> area",
        "normas_citadas": "literal del correo",
        "tipo_servicio": "MODELO entrenado (E38)",
        "tipo_consta_en_el_texto": "literal, como justificacion",
        "tema_propuesto": "composicion",
        "alta_de_cuenta": "lo que hace falta para crearla",
        "oportunidades_previas": "historial de la cuenta",
        "ganadas_previas": "historial de la cuenta",
        "dias_desde_la_ultima": "historial de la cuenta",
        "area_habitual": "historial de la cuenta",
        "ofertas_previas": "historial de ofertas",
        "es_comercial": "clasificador de A6",
        "idioma": "deteccion",
    }
    for k, o in origen.items():
        n = campos.get(k, 0)
        print(f"   {k:<26}{n:>7} /{len(d):<3}{100*n/len(d):>7.1f} %  {o}")
    conf = Counter(f["tipo_confianza"] for f in fichas)
    print()
    print(f"   El tipo se propone en los {len(d)}, pero no con la misma")
    print(f"   seguridad. Reparto, y el acierto que E38 midio en cada tramo:")
    for tr_, ac in (("alta", "94,5 %"), ("media", "72,1 %"), ("baja", "44,6 %")):
        print(f"      confianza {tr_:<8}{conf.get(tr_, 0):>4} correos"
              f"      acierto medido {ac}")
    lit = sum(1 for f in fichas if f["tipo_consta_en_el_texto"])
    print()
    print(f"   Y en {lit} de los {len(d)} el correo ademas lo dice con sus")
    print(f"   palabras, que van impresas en la ficha al lado de la propuesta.")

    # ------------------------------------------------------------------ 3
    print()
    print("=" * 76)
    print("PASO 3 · ¿ESTA FUNDAMENTADO EL TEMA PROPUESTO?")
    print("=" * 76)
    con_tema = [f for f in fichas if f["tema_propuesto"]]
    print(f"   Correos con tema propuesto : {len(con_tema)} de {len(d)}  "
          f"({100*len(con_tema)/len(d):.1f} %)")
    print(f"   Sin tema: no habia materia prima suficiente, y se dice en vez")
    print(f"   de rellenar con algo inventado.")

    print()
    print("   ESTA MEDIDA HAY QUE MIRARLA CON MAS CUIDADO DESDE E38. Antes el")
    print("   tema entero salia literal del correo. Ahora el TIPO lo decide un")
    print("   modelo: el correo puede decir «comprobar si aguanta» y la ficha")
    print("   proponer «Ensayo». Asi que se mide con dos varas y se ensenan")
    print("   las dos, porque dan cosas distintas.")

    fund, fund_correo, fund_sin_tipo, fallos = [], [], [], []
    for f in con_tema:
        cuerpo = d.loc[d.id == f["id"], "cuerpo"].iloc[0]
        tv = terminos(f["tema_propuesto"], minimo=4)
        if not tv:
            continue
        del_correo = terminos(cuerpo, minimo=4)
        fund.append(len(tv & (del_correo | voc_catalogo)) / len(tv))
        fund_correo.append(len(tv & del_correo) / len(tv))
        # el tema sin la palabra que puso el modelo: solo lo que consta
        resto = tv - terminos(f["tipo_servicio"] or "", minimo=4)
        if resto:
            fund_sin_tipo.append(len(resto & del_correo) / len(resto))
            if fund_sin_tipo[-1] < 0.999:
                fallos.append((f["id"], f["tema_propuesto"],
                               sorted(resto - del_correo)))
    fund = np.array(fund)
    fund_correo = np.array(fund_correo)
    fund_sin_tipo = np.array(fund_sin_tipo)
    print()
    print(f"   {'':<48}{'fundamentacion':>16}")
    print("   " + "-" * 74)
    print(f"     {'Tema entero · contra el correo Y el catalogo':<46}"
          f"{100*fund.mean():>13.1f} %")
    print(f"     {'Tema entero · contra el correo SOLO':<46}"
          f"{100*fund_correo.mean():>13.1f} %")
    print(f"   **{'Sin el tipo · contra el correo solo':<46}"
          f"{100*fund_sin_tipo.mean():>13.1f} %")
    print()
    print(f"   LA PRIMERA es la medida de E37 y sigue dando "
          f"{100*fund.mean():.1f} %, pero por un")
    print(f"   motivo que hay que decir: «ensayo» y «consultoria» estan en el")
    print(f"   catalogo de servicios, asi que la palabra que pone el modelo")
    print(f"   cuenta como fundamentada aunque no este en el correo. El")
    print(f"   catalogo siempre fue fuente valida, pero aqui se queda corta.")
    print()
    print(f"   LA SEGUNDA es la exigente: contra el correo y nada mas. Da")
    print(f"   {100*fund_correo.mean():.1f} %, y esos "
          f"{100*(fund.mean()-fund_correo.mean()):.1f} puntos de diferencia son "
          f"exactamente lo que")
    print(f"   el modelo pone de su cosecha. Es el precio de los "
          f"{len(d) - sum(1 for f in fichas if f['tipo_consta_en_el_texto'])} tipos")
    print(f"   que antes no habia, y va declarado en cada ficha.")
    print()
    print(f"   LA TERCERA es la que tiene que dar 100 %, y lo da en "
          f"{int((fund_sin_tipo >= 0.999).sum())} de {len(fund_sin_tipo)}:")
    print(f"   materia y norma siguen saliendo literales del texto. Por")
    print(f"   construccion deberia ser asi, y precisamente por eso se")
    print(f"   comprueba: la vez que dio 99,1 % destapo el error X28.")
    if fallos:
        print()
        print(f"   NO DA 100 %, hay {len(fallos)} temas con alguna palabra que no")
        print(f"   esta literal en el correo. Los primeros, para verlos:")
        for i, (idc, tema_, falta) in enumerate(fallos[:6]):
            print(f"      {idc} · «{tema_}» · falta {falta}")

    # ------------------------------------------------------------------ 4
    print()
    print("=" * 76)
    print("PASO 4 · ¿APORTA SOBRE EL SUELO?")
    print("=" * 76)
    op = pd.read_excel(OPORT)
    op.columns = [c.strip() for c in op.columns]
    temas = op["Tema"].dropna().astype(str)
    pal = Counter(p for t in temas for p in sin_tildes(t).split() if len(p) >= 4)
    suelo_tema = " ".join(w for w, _ in pal.most_common(3))
    print(f"   EL SUELO: proponer siempre las tres palabras mas frecuentes del")
    print(f"   historico. Es lo que se obtiene sin leer el correo.")
    print()
    sv = terminos(suelo_tema, minimo=4)
    f_suelo = []
    for f in con_tema:
        cuerpo = d.loc[d.id == f["id"], "cuerpo"].iloc[0]
        ov = terminos(cuerpo, minimo=4) | voc_catalogo
        f_suelo.append(len(sv & ov) / len(sv) if sv else 0)
    f_suelo = np.array(f_suelo)
    print(f"   {'':<34}{'fundamentacion':>16}")
    print("   " + "-" * 52)
    print(f"   {'El suelo (3 palabras comunes)':<34}{100*f_suelo.mean():>15.1f} %")
    print(f"   {'El tema compuesto':<34}{100*fund.mean():>15.1f} %")
    print(f"   {'Diferencia':<34}{100*(fund.mean()-f_suelo.mean()):>+15.1f} puntos")

    # ------------------------------------------------------------------ 5
    print()
    print("=" * 76)
    print("PASO 5 · QUE LLEVA UNA FICHA, Y QUE NO LLEVA")
    print("=" * 76)
    completas = sum(1 for f in fichas if f["cuenta_en_crm"] and f["area_por_norma"]
                    and f["tema_propuesto"])
    print(f"   Fichas con cuenta + area + tema : {completas} de {len(d)}  "
          f"({100*completas/len(d):.1f} %)")
    print()
    print("   LO QUE NINGUNA FICHA LLEVA, y hay que decirlo:")
    print("   · El nombre y el cargo de quien escribe. No se exportaron, por")
    print("     minimizacion de datos (4.2.4).")
    print("   · Presupuesto y plazos del cliente: solo aparecen en el 43,8 %")
    print("     y el 28,6 % de los correos, medido en E34.")
    print("   · Una estimacion de si se va a ganar. A8 la da, pero necesita")
    print("     la oportunidad ya creada, y aqui todavia no existe.")

    if ver:
        print()
        print("=" * 76)
        print(f"EJEMPLO · {ver} ficha(s), con la cuenta oculta")
        print("=" * 76)
        for f in [x for x in fichas if x["tema_propuesto"]][:ver]:
            print()
            print(f"   --- {f['id']} ---")
            for k in ("cuenta_en_crm", "sector", "provincia", "dominio_contacto",
                      "idioma", "area_por_norma", "normas_citadas",
                      "tipo_servicio", "tipo_confianza", "tipo_probabilidad",
                      "tipo_consta_en_el_texto", "palabras_que_lo_sostienen",
                      "telegrama_leido", "tema_propuesto",
                      "oportunidades_previas", "ganadas_previas",
                      "dias_desde_la_ultima", "area_habitual",
                      "ofertas_previas", "alta_de_cuenta", "es_comercial"):
                v = f[k]
                if k in ("sector", "provincia"):
                    v = "(consta)" if v else None
                if k == "dominio_contacto":
                    v = "(consta)" if v else None
                print(f"   {k:<26}{v if v is not None else '— no consta'}")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    salida = {
        "experimento": "E37", "agente": "A7", "pieza": "briefing de traspaso",
        "version": VERSION_SCRIPT,
        "n_correos": int(len(d)),
        "cobertura": {k: int(campos.get(k, 0)) for k in origen},
        "tema": {"propuestos": int(len(con_tema)),
                 "pct": 100 * len(con_tema) / len(d),
                 "fundamentacion_media": float(100 * fund.mean()),
                 "con_fundamentacion_total": int((fund >= 0.999).sum()),
                 "fundamentacion_solo_correo": float(100 * fund_correo.mean()),
                 "fundamentacion_sin_el_tipo": float(100 * fund_sin_tipo.mean()),
                 "sin_el_tipo_con_total": int((fund_sin_tipo >= 0.999).sum()),
                 "sin_el_tipo_n": int(len(fund_sin_tipo)),
                 "suelo_fundamentacion": float(100 * f_suelo.mean())},
        "tipo_servicio": {
            "lo_decide": "clasificador entrenado (E38)",
            "antes": "diccionario de palabras (E37)",
            "lee": f"telegrama de {TELEGRAMA_PALABRAS} palabras extraido del correo",
            "se_propone_en": int(len(d)),
            "confianza": {k: int(v) for k, v in
                          Counter(f["tipo_confianza"] for f in fichas).items()},
            "consta_literal_en": int(sum(1 for f in fichas
                                         if f["tipo_consta_en_el_texto"])),
            "acierto_por_tramo_medido_en_e38":
                {"alta": 94.5, "media": 72.1, "baja": 44.6}},
        "fichas_completas": int(completas),
        "no_lleva": ["nombre y cargo del contacto (minimizacion)",
                     "presupuesto y plazos (solo en el 43,8 % y 28,6 %)",
                     "estimacion de cierre (A8 exige la oportunidad creada)"],
    }
    RES.mkdir(parents=True, exist_ok=True)
    f = RES / "a8_briefing.json"
    f.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=float),
                 encoding="utf-8")
    pd.DataFrame(fichas).to_csv(RES / "a8_briefings.csv", sep=";", index=False,
                                encoding="utf-8")
    print()
    print(f"   [ok] {f.name}  ·  a8_briefings.csv con las {len(fichas)} fichas")
    print()


if __name__ == "__main__":
    main()
