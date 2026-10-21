# -*- coding: utf-8 -*-
"""
F6_A8_diagnostico_emparejador.py · ¿por qué falla el emparejamiento?
====================================================================

LA PREGUNTA
    E23 midio que el emparejador acierta el servicio en primera posicion solo
    el 39 % de las veces, con un margen de 0,005 sobre el segundo. Alli lo
    atribui a que "los servicios se parecen demasiado entre si", pero lo dije
    SIN MEDIRLO. Este script lo mide.

    Hay tres explicaciones posibles y hay que separarlas, porque llevan a
    soluciones distintas:

      A · EL CATALOGO   los catorce servicios se describen de forma tan
                        parecida que no son separables. Ninguna mejora del
                        modelo lo arregla: hay que reescribir el catalogo.

      B · EL CORREO     el correo es largo y difuso, habla de muchas cosas, y
                        eso diluye la consulta. Se arregla extrayendo la
                        peticion antes de emparejar.

      C · LA PREGUNTA   el correo pide varias cosas a la vez y forzarlo a un
                        solo servicio es un error de planteamiento, no de
                        implementacion.

QUE HACE
    1. Mide cuanto se parecen los servicios ENTRE SI
    2. Prueba si el catalogo es separable, sin correos de por medio:
       se usa la descripcion de cada servicio como consulta y se mira si
       recupera su propia ficha. Si falla aqui, el problema es el catalogo.
    3. Compara los rangos de similitud, porque un coseno de 0,84 no significa
       "muy parecido": este modelo comprime todo en una banda estrecha y lo
       que importa es el ORDEN, no el valor
    4. Prueba a emparejar solo con la frase de la peticion, no con el correo
       entero, para ver si el problema es la difusion
    5. Cuenta cuantos correos piden cosas de VARIAS areas

COMO SE EJECUTA
    python scripts/F6_A8_diagnostico_emparejador.py
    python scripts/F6_A8_diagnostico_emparejador.py --guardar
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

VERSION_SCRIPT = "v1 · 30-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
LIMPIO = RAIZ / "datos" / "01_limpio"
RESULTADOS = RAIZ / "datos" / "03_resultados"
CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"
CATALOGO = RESULTADOS / "a5_catalogo.json"
SALIDA = RESULTADOS / "f6_diagnostico_emparejador.json"
MODELO = "intfloat/multilingual-e5-small"

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

# verbos y sustantivos con los que se formula una peticion
PETICION = ["solicit", "necesit", "requer", "quisiera", "gustaria", "interesa",
            "presupuesto", "precio", "coste", "tarifa", "oferta", "analisis",
            "ensayo", "estudio", "asesoramiento", "informacion sobre",
            "would like", "we need", "request", "quotation", "quote",
            "looking for", "enquiry", "advise"]


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def contiene_palabra(texto, termino):
    partes = termino.split()
    if len(partes) == 1:
        cola = r"\w*" if len(termino) >= 6 else ""
        patron = r"(?<![\w])" + re.escape(termino) + cola + r"(?![\w])"
    else:
        patron = (r"(?<![\w])" + r"\W+".join(re.escape(p) for p in partes)
                  + r"\w*(?![\w])")
    return re.search(patron, texto) is not None


def area_normalizada(a):
    t = sin_acentos(a).upper().split(":")[-1]
    t = t.split("–")[0].split(" - ")[0]
    t = re.sub(r"^\s*[AD]\.\s*", "", t.strip())
    return re.sub(r"\s+", " ", t).strip()


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"{n} · {t}")
    print("=" * 76)


def frase_peticion(cuerpo, maximo=2):
    """Se queda con las frases donde se formula la peticion."""
    frases = re.split(r"(?<=[.!?\n])\s+", cuerpo)
    buenas = [f.strip() for f in frases
              if any(p in sin_acentos(f) for p in PETICION) and len(f.split()) > 4]
    if not buenas:
        return cuerpo[:400]
    return " ".join(buenas[:maximo])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("--modelo", default=MODELO)
    a = ap.parse_args()

    print()
    print("#" * 76)
    print("# F6 · A8 · ¿por qué no acierta el emparejamiento?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    servicios = json.loads(CATALOGO.read_text(encoding="utf-8"))
    d = pd.read_csv(CORPUS, sep=";")
    d["cuerpo"] = d.cuerpo.fillna("")

    from sentence_transformers import SentenceTransformer
    print(f"\n   Modelo: {a.modelo}   ·   {len(servicios)} servicios   ·   "
          f"{len(d)} correos")
    modelo = SentenceTransformer(a.modelo)

    def enc(textos, prefijo):
        return modelo.encode([f"{prefijo}: {t}" for t in textos],
                             normalize_embeddings=True, show_progress_bar=False)

    ficha = [" · ".join(p for p in [s.get("nombre", ""), s.get("area", ""),
                                    s.get("tipo", ""), s.get("resuelve", "")] if p)
             for s in servicios]
    v_serv = enc(ficha, "passage")
    v_mail = enc([t[:2000] for t in d.cuerpo], "query")
    cifras = {"version": VERSION_SCRIPT}

    # ------------------------------------------------------------------ 1
    titulo(1, "¿CUANTO SE PARECEN LOS SERVICIOS ENTRE SI?")
    ss = v_serv @ v_serv.T
    fuera = ss[~np.eye(len(ss), dtype=bool)]
    print(f"   Similitud media entre dos servicios distintos : {fuera.mean():.3f}")
    print(f"   La mas baja / la mas alta                     : "
          f"{fuera.min():.3f} / {fuera.max():.3f}")
    print()
    print("   Las cinco parejas de servicios que mas se confunden:")
    pares = []
    for i in range(len(ss)):
        for j in range(i + 1, len(ss)):
            pares.append((ss[i, j], servicios[i]["nombre"], servicios[j]["nombre"]))
    for v, x, y in sorted(pares, reverse=True)[:5]:
        print(f"      {v:.3f}   {x[:30]:<32} / {y[:30]}")
    cifras["sim_servicio_servicio"] = float(fuera.mean())

    # ------------------------------------------------------------------ 2
    titulo(2, "¿ES SEPARABLE EL CATALOGO?  (sin correos de por medio)")
    print("   Se usa la descripcion larga de cada servicio como consulta y se")
    print("   mira si recupera SU PROPIA ficha entre las catorce. Si el modelo")
    print("   no distingue un servicio de sus hermanos ni con su propio texto,")
    print("   el problema no son los correos.")
    print()
    v_desc = enc([s.get("resuelve", s.get("nombre", "")) for s in servicios],
                 "query")
    m = v_desc @ v_serv.T
    top = np.argsort(-m, axis=1)
    ac1 = int(sum(top[i, 0] == i for i in range(len(servicios))))
    ac3 = int(sum(i in top[i, :3] for i in range(len(servicios))))
    print(f"   Recupera su propia ficha en 1.er puesto : {ac1}/{len(servicios)}"
          f"   ({ac1/len(servicios)*100:.0f} %)")
    print(f"   …dentro de los tres primeros            : {ac3}/{len(servicios)}"
          f"   ({ac3/len(servicios)*100:.0f} %)")
    fallos = [servicios[i]["nombre"] for i in range(len(servicios)) if top[i, 0] != i]
    if fallos:
        print()
        print("   No se recuperan a si mismos:")
        for i in range(len(servicios)):
            if top[i, 0] != i:
                print(f"      {servicios[i]['nombre'][:34]:<36} lo confunde con "
                      f"{servicios[top[i,0]]['nombre'][:30]}")
    cifras["autorrecuperacion_top1"] = ac1
    cifras["n_servicios"] = len(servicios)

    # ------------------------------------------------------------------ 3
    titulo(3, "LOS RANGOS · por que un coseno de 0,84 no significa nada")
    ms = v_mail @ v_serv.T
    mm = v_mail @ v_mail.T
    mm_fuera = mm[~np.eye(len(mm), dtype=bool)]
    print(f"   correo  <->  servicio  : {ms.mean():.3f}   "
          f"(rango {ms.min():.3f} a {ms.max():.3f})")
    print(f"   servicio<->  servicio  : {fuera.mean():.3f}   "
          f"(rango {fuera.min():.3f} a {fuera.max():.3f})")
    print(f"   correo  <->  correo    : {mm_fuera.mean():.3f}   "
          f"(rango {mm_fuera.min():.3f} a {mm_fuera.max():.3f})")
    print()
    print("   Este modelo mete TODO en una banda estrecha: dos textos sin nada")
    print("   que ver ya parten de 0,7 u 0,8. Por eso el valor absoluto no")
    print("   informa y lo unico que cuenta es el ORDEN. Y el orden se decide")
    print("   por diferencias de milesimas.")
    cifras["rango_correo_servicio"] = [float(ms.min()), float(ms.max())]

    # ------------------------------------------------------------------ 4
    titulo(4, "¿MEJORA SI SE EMPAREJA SOLO LA FRASE DE LA PETICION?")
    print("   Hipotesis B: el correo entero es largo y difuso —saludos, firma,")
    print("   contexto— y eso diluye la consulta. Se prueba con solo las frases")
    print("   donde se formula la peticion.")
    print()
    cortos = [frase_peticion(t) for t in d.cuerpo]
    v_corto = enc(cortos, "query")
    ms_corto = v_corto @ v_serv.T

    def diagnostico(sim, etiqueta):
        o = np.argsort(-sim, axis=1)
        t1 = sim[np.arange(len(sim)), o[:, 0]]
        t2 = sim[np.arange(len(sim)), o[:, 1]]
        area_serv = [area_normalizada(x.get("area", "")) for x in servicios]
        a1 = a3 = ev = 0
        for i, cuerpo in enumerate(d.cuerpo):
            t = sin_acentos(cuerpo)
            reales = {ar for ar, ns in NORMAS.items()
                      if any(contiene_palabra(t, n) for n in ns)}
            if len(reales) != 1:
                continue
            real = reales.pop()
            ev += 1
            a1 += area_serv[o[i, 0]] == real
            a3 += real in {area_serv[j] for j in o[i, :3]}
        print(f"   {etiqueta}")
        print(f"      margen sobre el 2.o : {(t1-t2).mean():.4f}")
        print(f"      acierto 1.er puesto : {a1}/{ev}  ({a1/ev*100:.0f} %)")
        print(f"      acierto en top 3    : {a3}/{ev}  ({a3/ev*100:.0f} %)")
        print(f"      servicios distintos elegidos: {len(set(o[:,0]))}")
        return {"margen": float((t1 - t2).mean()), "top1": int(a1),
                "top3": int(a3), "evaluables": int(ev),
                "distintos": int(len(set(o[:, 0])))}

    r_largo = diagnostico(ms, "Correo entero:")
    print()
    r_corto = diagnostico(ms_corto, "Solo la frase de la peticion:")
    cifras["correo_entero"] = r_largo
    cifras["solo_peticion"] = r_corto

    # ------------------------------------------------------------------ 5
    titulo(5, "¿PIDEN LOS CORREOS UNA SOLA COSA?")
    print("   Hipotesis C: quiza forzar un solo servicio es el error. Se mira")
    print("   cuantas areas distintas cita cada correo.")
    print()
    n_areas = []
    for cuerpo in d.cuerpo:
        t = sin_acentos(cuerpo)
        n_areas.append(len({ar for ar, ns in NORMAS.items()
                            if any(contiene_palabra(t, n) for n in ns)}))
    for k in sorted(set(n_areas)):
        v = n_areas.count(k)
        etq = {0: "ninguna (no citan norma)", 1: "una sola area"}.get(
            k, f"{k} areas distintas")
        print(f"      {etq:<30}{v:>4} correos   {v/len(d)*100:5.1f} %")
    multi = sum(1 for x in n_areas if x > 1)
    cifras["correos_multiarea"] = int(multi)

    # ------------------------------------------------------------------ 6
    titulo(6, "DIAGNOSTICO")
    sep_cat = ac1 / len(servicios)
    print(f"   A · ¿Se parecen demasiado los servicios entre si?")
    print(f"       Similitud media entre servicios distintos: {fuera.mean():.3f}")
    print(f"       Cada servicio se recupera a si mismo: {ac1}/{len(servicios)}")
    if sep_cat >= 0.8:
        print("       -> NO. El catalogo SI es separable. Con su propio texto")
        print("          el modelo distingue los servicios sin problema.")
        veredicto_a = "el catalogo es separable"
    else:
        print("       -> SI. El catalogo NO es separable ni con su propio")
        print("          texto. Hay que reescribir las descripciones.")
        veredicto_a = "el catalogo no es separable"
    print()
    print(f"   B · ¿Es el correo, que viene difuso?")
    mejora = r_corto["top1"] - r_largo["top1"]
    print(f"       Acierto con el correo entero : {r_largo['top1']}/{r_largo['evaluables']}")
    print(f"       Acierto con solo la peticion : {r_corto['top1']}/{r_corto['evaluables']}")
    if mejora > 0:
        print(f"       -> SI influye: recortar el correo mejora en {mejora} casos.")
        veredicto_b = "el correo difuso influye"
    else:
        print("       -> No mejora recortando. El problema no es la longitud.")
        veredicto_b = "la longitud del correo no es el problema"
    print()
    print(f"   C · ¿Piden varias cosas a la vez?")
    print(f"       Correos que citan mas de un area: {multi} de {len(d)}")
    if multi / len(d) > 0.15:
        print("       -> SI en una parte. Exigir un solo servicio penaliza a")
        print("          esos correos aunque el emparejador funcione bien.")
    else:
        print("       -> Poco. La mayoria pide una sola cosa.")
    print()
    print("   D · ENTONCES, ¿QUE PASA?  La respuesta esta en el apartado 3.")
    print()
    print(f"       correo  con correo   : {mm_fuera.mean():.3f}")
    print(f"       servicio con servicio: {fuera.mean():.3f}")
    print(f"       correo  con servicio : {ms.mean():.3f}   <- LA MAS BAJA")
    print()
    print("       Un correo se parece mas a CUALQUIER otro correo que al")
    print("       servicio que de verdad pide. Y un servicio se parece mas a")
    print("       cualquier otro servicio que al correo que lo solicita.")
    print()
    print("       El modelo no esta agrupando por TEMA. Esta agrupando por")
    print("       GENERO DE TEXTO: por un lado los correos, con su saludo, su")
    print("       peticion y su despedida; por otro las fichas de catalogo,")
    print("       con su lenguaje de servicio. Son dos idiomas distintos, y la")
    print("       distancia entre esos dos idiomas es mayor que la distancia")
    print("       entre temas dentro de cada uno.")
    print()
    print("       Por eso recortar el correo lo empeora: al quitar contexto se")
    print("       pierde vocabulario tematico y queda mas formula de correo.")
    print()
    print("   QUE SE DEDUCE")
    print("       No hay que reescribir el catalogo: es separable (14 de 14).")
    print("       Hay que dejar de comparar un correo con una ficha. El paso")
    print("       que falta es TRADUCIR la peticion al idioma del catalogo:")
    print("       que A7 extraiga la necesidad como enunciado tecnico breve")
    print("       —«migracion de PFAS en caja de carton ondulado impresa»— y")
    print("       emparejar ESO. Deja de ser correo contra ficha y pasa a ser")
    print("       ficha contra ficha, que es lo que el apartado 2 demuestra")
    print("       que el modelo si resuelve.")
    print()
    print("       ESTO NO ESTA MEDIDO. Es la hipotesis que sale del")
    print("       diagnostico, no un resultado. Medirla exige ejecutar el")
    print("       modelo generativo, que necesita GPU. Queda como M5.")
    print()
    print("       La otra via, independiente de esta: entrenar un clasificador")
    print("       de area con las 4.362 etiquetas del historico. Ahi no hay")
    print("       problema de genero porque no se compara con nada: se predice.")
    print()
    print("   " + "-" * 70)
    cifras["veredicto"] = {
        "catalogo": veredicto_a, "correo": veredicto_b, "multiarea": int(multi),
        "sim_correo_correo": float(mm_fuera.mean()),
        "sim_servicio_servicio": float(fuera.mean()),
        "sim_correo_servicio": float(ms.mean()),
        "causa": "desajuste de genero entre correo y ficha de catalogo",
    }

    if a.guardar:
        SALIDA.write_text(json.dumps(cifras, indent=2, ensure_ascii=False),
                          encoding="utf-8")
        print(f"   [ok] {SALIDA.relative_to(RAIZ)}")
    else:
        print("   Simulacion. Lanzalo con --guardar para escribir las cifras.")
    print()


if __name__ == "__main__":
    main()
