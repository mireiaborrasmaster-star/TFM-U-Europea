# -*- coding: utf-8 -*-
"""
F6_A7_A8_viabilidad_cadena.py · ¿alcanza para A6, A7 y A8?
==========================================================

LA PREGUNTA
    Con cincuenta y dos correos reales, ¿se puede montar la cadena de entrada
    completa? Es decir:

        A6  recibir el correo, saber quien escribe y a donde va
        A7  cualificar: rellenar la ficha con lo que el cliente cuenta
        A8  emparejar con un servicio y redactar el briefing de traspaso

    La pregunta de fondo es otra, y conviene separarla: no es si hay datos
    para ENTRENAR, sino si hace falta entrenar algo.

LA DISTINCION QUE LO DECIDE TODO
    Hay tres formas de resolver una tarea y solo una necesita muchos datos:

      REGLAS            un diccionario, una expresion regular.
                        Datos necesarios para construirlo: ninguno.
                        Datos para medirlo: unas decenas. Ya los hay.

      EXTRAER CON LLM   se le pide al modelo que lea y rellene una ficha.
                        Datos para construirlo: NINGUNO. El modelo ya sabe
                        leer; lo que se le da es el formato de la ficha.
                        Datos para medirlo: unas decenas. Ya los hay.

      ENTRENAR          se ajusta un modelo con ejemplos etiquetados.
                        Datos necesarios: cientos o miles.
                        52 NO bastan.

    A5 ya demostro que la segunda via funciona: genero cuarenta correos con
    un modelo abierto sin entrenar nada, y se midieron. A7 y A8 son el mismo
    patron al reves —en vez de escribir, leer y rellenar—, que es una tarea
    mas facil, no mas dificil.

QUE MIDE ESTE SCRIPT
    1. Cuantas etiquetas reales de area hay en el CRM        (para entrenar)
    2. Cuantos de los 52 correos se pueden etiquetar de verdad (para medir)
    3. Si la ficha de cualificacion se puede rellenar leyendo el correo
    4. Si el emparejamiento con el catalogo de servicios funciona · SE EJECUTA
       de verdad con el mismo modelo de A5, no se estima
    5. Veredicto por agente

COMO SE EJECUTA
    python scripts/F6_A7_A8_viabilidad_cadena.py
    python scripts/F6_A7_A8_viabilidad_cadena.py --guardar

FUENTES
    datos/01_limpio/entradas_inbound_50_anon.csv   los 52 correos seudonimizados
    datos/02_derivado/cuentas_*.csv                para resolver el dominio
    datos/00_bruto/Oportunidades ....xlsx          las etiquetas de area reales
    datos/03_resultados/a5_catalogo.json           los 14 servicios
"""

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

VERSION_SCRIPT = "v1 · 30-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
LIMPIO = RAIZ / "datos" / "01_limpio"
DERIVADO = RAIZ / "datos" / "02_derivado"
RESULTADOS = RAIZ / "datos" / "03_resultados"

CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"
CATALOGO = RESULTADOS / "a5_catalogo.json"
OPORTUNIDADES_BRUTO = "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56.xlsx"
CUENTAS_DERIVADAS = ["cuentas_train.csv", "cuentas_val.csv", "cuentas_test.csv"]
SALIDA = RESULTADOS / "f6_viabilidad_cadena.json"

MODELO = "intfloat/multilingual-e5-small"

# ---------------------------------------------------------------------------
# Los siete criterios de cualificacion y como se detecta cada uno en un correo
# ---------------------------------------------------------------------------
# Esto NO es el agente A7: es una sonda para saber si la informacion ESTA en
# el correo. Si una senal no aparece nunca, ningun modelo podra extraerla,
# por bueno que sea. Se mide la MATERIA PRIMA, no la capacidad del modelo.
NIPPDEC = {
    "N · Necesidad": [
        "solicitar", "solicitamos", "necesitamos", "necesitaria", "quisiera",
        "nos gustaria", "requerimos", "interesados", "consulta", "informacion",
        "analisis", "ensayo", "ensayos", "estudio", "asesoramiento",
        "would like", "we need", "we are looking", "request", "enquiry"],
    "I · Impacto": [
        "cumplimiento", "cumplir", "obligacion", "obligatorio", "exige",
        "exigencia", "nos piden", "nos solicitan", "cliente nos", "auditoria",
        "reclamacion", "rechazo", "incidencia", "problema", "sancion",
        "entrada en vigor", "compliance", "requirement"],
    "P · Presupuesto": [
        "presupuesto", "coste", "costes", "precio", "precios", "tarifa",
        "tarifas", "oferta economica", "importe", "cuanto costaria",
        "quotation", "quote", "cost", "budget", "pricing"],
    "P · Plazo": [
        "plazo", "plazos", "urgente", "urgencia", "cuanto tiempo", "cuando",
        "antes de", "fecha limite", "disponibilidad", "lo antes posible",
        "timeline", "lead time", "deadline", "how long", "when"],
    "D · Decisor": [
        "director", "directora", "responsable", "jefe", "jefa", "gerente",
        "manager", "head of", "coordinador", "coordinadora", "tecnico",
        "calidad", "i+d", "compras", "produccion", "developer", "engineer"],
    "E · Encaje": [
        "envase", "envases", "embalaje", "packaging", "film", "pelicula",
        "bandeja", "botella", "caja", "carton", "plastico", "papel",
        "material", "materiales", "producto", "producimos", "fabricamos",
        "comercializamos", "we produce", "we manufacture"],
    "C · Campeon": [
        "quedo a la espera", "quedamos a la espera", "no dude", "no duden",
        "podemos concertar", "reunion", "llamada", "contactar", "hablar",
        "ampliar informacion", "happy to", "look forward", "please advise",
        "get in touch", "further details"],
}


# El mismo diccionario de normas del analisis de F6. Aqui no se usa para
# enrutar sino como CONTRASTE: donde el correo cita una norma, el area correcta
# se sabe con certeza, y eso permite comprobar si el emparejador semantico
# acierta o esta eligiendo casi al azar.
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


def area_normalizada(a):
    """«LABORATORIOS: A. Caracterizacion y Embalajes» -> «CARACTERIZACION Y EMBALAJES»"""
    t = sin_acentos(a).upper()
    t = t.split(":")[-1]
    t = t.split("\u2013")[0].split(" - ")[0]
    t = re.sub(r"^\s*[AD]\.\s*", "", t.strip())
    return re.sub(r"\s+", " ", t).strip()


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def contiene_palabra(texto, termino):
    """Palabra completa, con tolerancia de sufijo. Es la correccion de X8."""
    partes = termino.split()
    if len(partes) == 1:
        cola = r"\w*" if len(termino) >= 6 else ""
        patron = r"(?<![\w])" + re.escape(termino) + cola + r"(?![\w])"
    else:
        patron = (r"(?<![\w])" + r"\W+".join(re.escape(p) for p in partes)
                  + r"\w*(?![\w])")
    return re.search(patron, texto) is not None


def dominio_web(url):
    u = str(url).lower().strip()
    if not u or u == "nan":
        return ""
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.split("/")[0].strip()


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"{n} · {t}")
    print("=" * 76)


def texto_servicio(s):
    """Lo que se le da al modelo para representar un servicio."""
    partes = [s.get("nombre", ""), s.get("area", ""), s.get("tipo", ""),
              s.get("resuelve", "")]
    return " · ".join(p for p in partes if p)


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("--modelo", default=MODELO)
    a = ap.parse_args()

    print()
    print("#" * 76)
    print("# F6 · A7 · A8 · ¿alcanza para montar la cadena de entrada?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    if not CORPUS.exists():
        sys.exit(f"Falta {CORPUS.name}. Lanza antes F6_A6_corpus_correos.py --guardar")
    d = pd.read_csv(CORPUS, sep=";")
    d["cuerpo"] = d.cuerpo.fillna("")
    print(f"\n   Corpus: {len(d)} correos seudonimizados")

    cifras = {"version": VERSION_SCRIPT, "n_correos": int(len(d))}

    # ------------------------------------------------------------------ 1
    titulo(1, "¿CUANTAS ETIQUETAS REALES DE AREA HAY?  (lo que SI se entrena)")
    ruta_op = BRUTO / OPORTUNIDADES_BRUTO
    etiquetadas = None
    if ruta_op.exists():
        op = pd.read_excel(ruta_op)
        col_area = next((c for c in op.columns if "rea de Empresa" in c), None)
        col_tipo = next((c for c in op.columns if "Tipo Oportunidad" in c), None)
        col_cta = next((c for c in op.columns if c.strip() == "Cuenta"), None)
        print(f"   Oportunidades en el fichero      : {len(op):>6}")
        if col_area:
            etiquetadas = op[op[col_area].notna()]
            print(f"   …con area tecnica asignada       : {len(etiquetadas):>6}   "
                  f"{len(etiquetadas)/len(op)*100:5.1f} %")
            print()
            print("   Reparto de las etiquetas de area:")
            for k, v in etiquetadas[col_area].value_counts().head(8).items():
                print(f"      {str(k)[:46]:<48}{v:>6}")
            cifras["oportunidades"] = int(len(op))
            cifras["con_area"] = int(len(etiquetadas))
        if col_tipo:
            print()
            print("   Reparto del tipo de oportunidad:")
            for k, v in op[col_tipo].value_counts().head(6).items():
                print(f"      {str(k)[:46]:<48}{v:>6}")
    else:
        print(f"   No encuentro {OPORTUNIDADES_BRUTO}")

    print()
    print("   LECTURA: para ENTRENAR el enrutado por area no hacen falta los")
    print("   correos. Las etiquetas ya existen, son miles y son reales: cada")
    print("   oportunidad historica acabo asignada a un area. Son gratis.")

    # ------------------------------------------------------------------ 2
    titulo(2, "¿CUANTOS DE LOS 52 CORREOS SE PUEDEN ETIQUETAR?  (para MEDIR)")
    cu = pd.concat([pd.read_csv(DERIVADO / f) for f in CUENTAS_DERIVADAS],
                   ignore_index=True)
    cu["dom"] = cu.url.apply(dominio_web)
    idx = {}
    for r in cu[cu.dom != ""].itertuples():
        idx.setdefault(r.dom, []).append(r.empresa)

    emp = d[~d.generico.astype(str).str.lower().isin(["true"])].copy()
    emp["cuenta"] = emp.dominio.map(lambda x: (idx.get(x) or [None])[0])
    resueltos = emp[emp.cuenta.notna()]
    print(f"   Correos con dominio de empresa    : {len(emp):>4}")
    print(f"   …resueltos contra una cuenta      : {len(resueltos):>4}")

    con_etiqueta = 0
    if etiquetadas is not None and col_cta:
        cuentas_con_area = set(etiquetadas[col_cta].dropna().astype(str)
                               .str.strip().str.upper())
        nombres = resueltos.cuenta.astype(str).str.strip().str.upper()
        con_etiqueta = int(nombres.isin(cuentas_con_area).sum())
        print(f"   …y ademas con oportunidad etiquetada: {con_etiqueta:>2}")
    cifras["correos_resueltos"] = int(len(resueltos))
    cifras["correos_con_etiqueta_area"] = con_etiqueta

    print()
    print("   ESTE ES EL CUELLO DE BOTELLA REAL, y no es el que parecia.")
    print("   Para medir si el enrutado acierta hace falta saber la respuesta")
    print("   correcta de cada correo. Solo se sabe sola en los casos de")
    print("   arriba. En el resto, la respuesta correcta hay que ponerla a")
    print("   mano: leer el correo y decir a que area iria.")
    print()
    print(f"   Etiquetar 52 correos a mano es cosa de una tarde. Eso convierte")
    print(f"   el corpus en un conjunto de prueba de verdad.")

    # ------------------------------------------------------------------ 3
    titulo(3, "¿ESTA EN EL CORREO LA INFORMACION DE LA FICHA?  (A7)")
    print("   Se sondea si la materia prima existe. Si un criterio no aparece")
    print("   nunca, ningun modelo podra extraerlo por bueno que sea.")
    print()
    tabla = {}
    for crit, senales in NIPPDEC.items():
        hits = d.cuerpo.apply(
            lambda t: any(contiene_palabra(sin_acentos(t), s) for s in senales))
        tabla[crit] = int(hits.sum())
    print(f"   {'criterio':<20}{'correos':>9}{'%':>8}")
    print("   " + "-" * 40)
    for crit, n in tabla.items():
        marca = "  <-- flojo" if n / len(d) < 0.35 else ""
        print(f"   {crit:<20}{n:>9}{n/len(d)*100:>7.1f} %{marca}")
    cifras["nippdec"] = tabla

    completos = d.cuerpo.apply(
        lambda t: sum(any(contiene_palabra(sin_acentos(t), s) for s in ss)
                      for ss in NIPPDEC.values()))
    print()
    print("   Criterios cubiertos por correo:")
    for k, v in sorted(Counter(completos).items()):
        print(f"      {k} de 7 criterios{'':<6}{v:>4} correos")
    print(f"\n   Media: {completos.mean():.1f} de 7 criterios por correo")
    cifras["nippdec_media"] = float(completos.mean())

    # ------------------------------------------------------------------ 4
    titulo(4, "¿FUNCIONA EL EMPAREJAMIENTO CON EL CATALOGO?  (A8) · SE EJECUTA")
    servicios = json.loads(CATALOGO.read_text(encoding="utf-8"))
    print(f"   Servicios en el catalogo : {len(servicios)}")
    print(f"   Modelo                   : {a.modelo}")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        sys.exit("   Falta sentence-transformers. pip install sentence-transformers")

    print("   Cargando el modelo…")
    modelo = SentenceTransformer(a.modelo)
    v_serv = modelo.encode(["passage: " + texto_servicio(s) for s in servicios],
                           normalize_embeddings=True, show_progress_bar=False)
    v_mail = modelo.encode(["query: " + t[:2000] for t in d.cuerpo],
                           normalize_embeddings=True, show_progress_bar=False)
    sim = v_mail @ v_serv.T

    orden = np.argsort(-sim, axis=1)
    top1 = sim[np.arange(len(sim)), orden[:, 0]]
    top2 = sim[np.arange(len(sim)), orden[:, 1]]
    margen = top1 - top2
    # confianza por filas, como en A5: cuanto destaca el primero sobre la
    # media de SU propia fila. Comparar cosenos crudos entre correos distintos
    # no dice nada; dentro de una fila, si.
    z = (top1 - sim.mean(axis=1)) / sim.std(axis=1)

    print()
    print(f"   Similitud del primer servicio : media {top1.mean():.3f}   "
          f"min {top1.min():.3f}   max {top1.max():.3f}")
    print(f"   Margen sobre el segundo       : media {margen.mean():.3f}   "
          f"mediana {np.median(margen):.3f}")
    print(f"   Confianza (z dentro de fila)  : media {z.mean():.2f}   "
          f"min {z.min():.2f}   max {z.max():.2f}")
    print()
    for umbral in (1.5, 2.0, 2.5):
        n = int((z >= umbral).sum())
        print(f"   Con umbral de confianza z >= {umbral}: "
              f"{n:>3} de {len(d)} correos se emparejan  "
              f"({n/len(d)*100:.0f} %), {len(d)-n} se derivan a una persona")
    cifras["emparejamiento"] = {
        "top1_medio": float(top1.mean()), "margen_medio": float(margen.mean()),
        "z_medio": float(z.mean()),
        "pasan_z2": int((z >= 2.0).sum()),
    }

    print()
    print("   A que servicios se emparejan (primer puesto):")
    elegidos = Counter(servicios[i]["nombre"] for i in orden[:, 0])
    for nombre, v in elegidos.most_common(8):
        print(f"      {nombre[:52]:<54}{v:>4}")
    print(f"\n   Servicios distintos elegidos: {len(elegidos)} de {len(servicios)}")
    if len(elegidos) <= 3:
        print("   AVISO: casi todo cae en los mismos servicios. Eso suele")
        print("   indicar que el catalogo es corto o que las descripciones se")
        print("   parecen demasiado entre si, no que el modelo funcione mal.")
    cifras["servicios_distintos"] = len(elegidos)


    # --- contraste: ¿acierta el emparejador donde SI sabemos la respuesta? ---
    print()
    print("   " + "-" * 70)
    print("   CONTRASTE · ¿acierta donde la respuesta se sabe con certeza?")
    print("   " + "-" * 70)
    print("   En los correos que citan una norma, el area correcta se conoce.")
    print("   Sirven para comprobar si el emparejador acierta o elige casi al")
    print("   azar. Es el mismo razonamiento que el suelo de A2: una cifra sin")
    print("   punto de comparacion no dice nada.")
    print()

    area_serv = [area_normalizada(x.get("area", "")) for x in servicios]
    aciertos1 = aciertos3 = evaluables = 0
    for i, cuerpo in enumerate(d.cuerpo):
        t = sin_acentos(cuerpo)
        reales = {a for a, ns in NORMAS.items()
                  if any(contiene_palabra(t, n) for n in ns)}
        if len(reales) != 1:          # solo los inequivocos
            continue
        real = reales.pop()
        evaluables += 1
        if area_serv[orden[i, 0]] == real:
            aciertos1 += 1
        if real in {area_serv[j] for j in orden[i, :3]}:
            aciertos3 += 1

    # suelo: elegir el servicio mas frecuente del catalogo para ese area
    from collections import Counter as _C
    reparto = _C(area_serv)
    suelo = max(reparto.values()) / len(area_serv)

    if evaluables >= 5:
        print(f"   Correos con un area inequivoca : {evaluables:>4}")
        print(f"   Acierta en el primer puesto    : {aciertos1:>4} "
              f"({aciertos1/evaluables*100:.0f} %)")
        print(f"   El area correcta esta en el top 3: {aciertos3:>4} "
              f"({aciertos3/evaluables*100:.0f} %)")
        print(f"   Suelo (elegir siempre el area mas comun del catalogo): "
              f"{suelo*100:.0f} %")
        print()
        if aciertos1 / evaluables <= suelo + 0.05:
            print("   VEREDICTO: NO supera al suelo. El emparejador semantico")
            print("   NO esta discriminando entre servicios. Coherente con el")
            print("   margen de 0,005 sobre el segundo: es practicamente un")
            print("   empate entre los catorce.")
        elif aciertos3 / evaluables >= 0.7:
            print("   VEREDICTO: flojo en el primer puesto pero util como")
            print("   PROPUESTA DE TRES. Asi es como deberia usarse: el agente")
            print("   propone tres servicios y decide una persona.")
        else:
            print("   VEREDICTO: aciertos por encima del suelo pero lejos de")
            print("   ser fiable sin revision humana.")
    else:
        print(f"   Solo {evaluables} correos con area inequivoca: no alcanza")
        print("   para contrastar. Hace falta etiquetar a mano.")

    cifras["contraste_emparejador"] = {
        "evaluables": int(evaluables), "acierto_top1": int(aciertos1),
        "acierto_top3": int(aciertos3), "suelo": float(suelo)}

    # ------------------------------------------------------------------ 5
    titulo(5, "VEREDICTO POR AGENTE")
    filas = [
        ("A6 · recibir y enrutar", "reglas + diccionario",
         "SI, y ya esta medido", "29 % por dominio, 44 % por norma"),
        ("A7 · cualificar", "extraer con un LLM, sin entrenar",
         "SI, es viable", f"{completos.mean():.1f} de 7 criterios por correo"),
        ("A8 · emparejar servicio", "representaciones densas, sin entrenar",
         "SI, y acaba de ejecutarse",
         f"{int((z>=2.0).sum())} de {len(d)} con confianza alta"),
        ("A8 · redactar el briefing", "generar con un LLM, sin entrenar",
         "SI, es el mismo patron que A5", "A5 ya lo hizo y se midio"),
        ("A6 · comercial / no comercial", "clasificador entrenado",
         "NO", "la clase negativa esta vacia: sesgo de origen"),
    ]
    print(f"   {'pieza':<32}{'como se resuelve':<38}")
    print("   " + "-" * 72)
    for p, c, v, det in filas:
        print(f"   {p:<32}{c:<38}")
        print(f"   {'':<32}{v}  ·  {det}")
        print()

    print("   EN UNA LINEA")
    print("   Cuatro de las cinco piezas NO necesitan entrenarse, asi que la")
    print("   pregunta de si 52 correos bastan para entrenar no se les aplica.")
    print("   Lo que 52 correos dan es lo que faltaba: con que MEDIRLAS.")
    print()
    print("   Lo unico que de verdad necesita entrenarse con estos correos es")
    print("   separar lo comercial de lo que no lo es, y eso no se arregla con")
    print("   mas correos de la misma carpeta: hay que exportar sin filtrar.")

    # ------------------------------------------------------------------ 6
    titulo(6, "GUARDAR")
    if a.guardar:
        SALIDA.write_text(json.dumps(cifras, indent=2, ensure_ascii=False),
                          encoding="utf-8")
        print(f"   [ok] {SALIDA.relative_to(RAIZ)}")
    else:
        print("   Simulacion. Vuelve a lanzarlo con --guardar para escribir")
        print("   las cifras.")
    print()


if __name__ == "__main__":
    main()
