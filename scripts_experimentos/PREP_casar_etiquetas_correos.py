# -*- coding: utf-8 -*-
"""
PREP_casar_etiquetas_correos.py · pega las etiquetas de la autora al corpus
============================================================================

QUE HACE
    La autora clasifico a mano los 105 correos en COMERCIAL / NO COMERCIAL,
    escribiendo «CATEGORIA:» al final de cada uno en
    `ejemplos_de_correos_clasificados.txt`.

    Ese fichero lleva nombres y direcciones reales; el corpus con el que se
    trabaja esta seudonimizado. Asi que no se pueden casar por texto exacto
    ni por orden —los separadores no coinciden: 93 bloques para 105 correos—.

COMO SE CASAN
    Por SOLAPAMIENTO DE CONTENIDO. De cada correo se toma el conjunto de
    palabras largas (>=5 letras, sin tildes) y se busca en el corpus el que
    mas comparte, medido con el indice de Jaccard.

    Y SE COMPRUEBA, que es lo que importa:
      · que cada correo del corpus reciba UNA sola etiqueta
      · que el parecido del mejor candidato sea alto
      · que haya DISTANCIA con el segundo mejor, porque si dos correos
        empatan la asignacion es una moneda al aire

    Si algo de eso falla, el script lo dice y no escribe nada.

PARA QUE SIRVE DESPUES
    Con esto la cuarta pieza de A6 pasa de no tener etiqueta fiable a
    tenerla. Y de paso se puede medir cuanto se equivocaba la lista de
    terminos que se uso antes, que es el error X25.

CONFIDENCIALIDAD
    No imprime el texto de ningun correo ni ningun nombre. Solo
    identificadores y cifras.

COMO SE EJECUTA
    python scripts/PREP_casar_etiquetas_correos.py
    python scripts/PREP_casar_etiquetas_correos.py --guardar
"""

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

VERSION_SCRIPT = "v1 · 04-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
CLASIF = RAIZ / "datos" / "00_bruto" / "ejemplos_de_correos_clasificados.txt"
CORPUS = RAIZ / "datos" / "01_limpio" / "entradas_inbound_50_anon.csv"
SALIDA = RAIZ / "datos" / "01_limpio" / "etiquetas_comercial_A6.csv"

MIN_PARECIDO = 0.20      # por debajo, la asignacion no es de fiar
MIN_DISTANCIA = 1.30     # el mejor tiene que superar al segundo en esta razon

NO_COMERCIAL_LISTA = [
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


def huella(texto):
    """Palabras largas del texto. Las cortas son ruido comun a todo correo."""
    return {p for p in re.findall(r"[a-z0-9]{5,}", sin_tildes(texto))}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def leer_clasificados():
    t = CLASIF.read_text(encoding="utf-8", errors="replace")
    trozos = re.split(r"(CATEGOR[IÍ]A\s*:\s*[^\n\r]+)", t, flags=re.I)
    fuera = []
    for i in range(0, len(trozos) - 1, 2):
        cuerpo = trozos[i].strip()
        cat = re.sub(r"CATEGOR[IÍ]A\s*:\s*", "", trozos[i + 1],
                     flags=re.I).strip().upper()
        if cuerpo:
            fuera.append((cuerpo, cat))
    return fuera


def main():
    guardar = "--guardar" in sys.argv

    print()
    print("=" * 76)
    print(f"PREP · casar las etiquetas con el corpus  ·  {VERSION_SCRIPT}")
    print("=" * 76)
    print()

    if not CLASIF.exists():
        raise SystemExit(f"   No encuentro {CLASIF.name}")
    cl = leer_clasificados()
    co = pd.read_csv(CORPUS, sep=";")
    co["cuerpo"] = co.cuerpo.fillna("").astype(str)

    print(f"   Correos clasificados a mano : {len(cl)}")
    print(f"   Correos en el corpus        : {len(co)}")
    reparto = pd.Series([c for _, c in cl]).value_counts()
    for k, v in reparto.items():
        print(f"      {k:<16}{v:>4}   {100*v/len(cl):>5.1f} %")

    if len(cl) != len(co):
        print()
        print(f"   [!!] No son el mismo numero. Se casara lo que se pueda.")

    # ------------------------------------------------------------------
    print()
    print("   Casando por solapamiento de contenido...")
    hc = [huella(c) for c, _ in cl]
    ho = [huella(x) for x in co.cuerpo]

    # Asignacion UNO A UNO, no el mejor de cada uno por separado.
    #
    # Hace falta porque el fichero clasificado trae DOS CORREOS IDENTICOS
    # —el 48 y el 50, parecido 1,000— y eligiendo el mejor de cada uno los
    # dos se llevaban la misma entrada del corpus, dejando otra sin
    # etiqueta. Resolviendo la asignacion en conjunto cada correo recibe
    # una y solo una.
    import numpy as np
    M = np.array([[jaccard(hc[i], ho[j]) for j in range(len(co))]
                  for i in range(len(cl))])
    try:
        from scipy.optimize import linear_sum_assignment
        fil, col = linear_sum_assignment(-M)
        metodo = "asignacion optima (Hungaro)"
    except ImportError:
        # sin scipy: voraz por parecido descendente, que aqui basta porque
        # la matriz esta muy separada salvo en el par identico
        orden = np.dstack(np.unravel_index(np.argsort(-M, axis=None), M.shape))[0]
        usados_i, usados_j, fil, col = set(), set(), [], []
        for i, j in orden:
            if i in usados_i or j in usados_j:
                continue
            usados_i.add(i); usados_j.add(j); fil.append(i); col.append(j)
        fil, col = np.array(fil), np.array(col)
        metodo = "voraz por parecido descendente"
    print(f"   metodo: {metodo}")

    filas, flojos, ambiguos, inocuos = [], [], [], []
    for i, j in zip(fil, col):
        cat = cl[i][1]
        mejor = M[i, j]
        # el segundo mejor de ESE correo, para saber si estaba disputado
        otros = np.sort(M[i])[::-1]
        segundo = otros[1] if len(otros) > 1 else 0.0
        razon = mejor / segundo if segundo > 0 else 999.0
        filas.append({"id": co.id.iloc[j], "categoria": cat,
                      "parecido": round(float(mejor), 3),
                      "razon": round(float(razon), 2),
                      "orden_clasificado": int(i) + 1})
        if mejor < MIN_PARECIDO:
            flojos.append((int(i) + 1, co.id.iloc[j], mejor))
        elif razon < MIN_DISTANCIA:
            # Que este disputado solo importa si el otro candidato traeria
            # OTRA etiqueta. Si los que se lo disputan dicen lo mismo, la
            # etiqueta sale igual se asigne como se asigne, y entonces la
            # ambiguedad es inocua. Hay que comprobarlo, no suponerlo.
            rivales = [k for k in range(len(cl))
                       if k != i and M[k, j] >= mejor * 0.95]
            cats = {cl[k][1] for k in rivales} | {cat}
            if len(cats) > 1:
                ambiguos.append((int(i) + 1, co.id.iloc[j], mejor, segundo))
            else:
                inocuos.append((int(i) + 1, co.id.iloc[j], mejor, cat))

    r = pd.DataFrame(filas)
    dup = r.id.duplicated(keep=False)

    print()
    print("   COMPROBACIONES")
    ko = 0
    for ok, etiqueta in (
            (not dup.any(),
             f"cada correo recibe una sola etiqueta "
             f"({int(r.id.duplicated().sum())} repetidos)"),
            (len(r) == len(co), f"se casan los {len(co)} del corpus"),
            (not flojos, f"ninguno por debajo de {MIN_PARECIDO} de parecido "
                         f"({len(flojos)} flojos)"),
            (not ambiguos, f"ningun empate cambia la etiqueta "
                           f"({len(ambiguos)} que si la cambiarian)")):
        print(f"   [{'ok' if ok else 'NO'}]  {etiqueta}")
        ko += 0 if ok else 1

    print()
    print(f"   Parecido: mediana {r.parecido.median():.3f} · "
          f"minimo {r.parecido.min():.3f} · maximo {r.parecido.max():.3f}")

    if dup.any():
        print()
        print("   CORREOS DEL CORPUS CON MAS DE UNA ETIQUETA:")
        for i, f in r[dup].sort_values("id").iterrows():
            print(f"      {f.id}  orden {f.orden_clasificado:>3}  "
                  f"parecido {f.parecido}")
    for n, cid, p in flojos[:10]:
        print(f"      flojo: clasificado {n} -> {cid} con {p:.3f}")
    for n, cid, pp, ss in ambiguos[:10]:
        print(f"      ambiguo: clasificado {n} -> {cid}  "
              f"{pp:.3f} frente a {ss:.3f}")
    if inocuos:
        print()
        print(f"   {len(inocuos)} empate(s) INOCUO(S): los correos que se")
        print("   disputan la entrada traen la MISMA etiqueta, asi que da")
        print("   igual como se reparta. Vienen de que el fichero")
        print("   clasificado trae algun correo repetido:")
        for n, cid, pp, c in inocuos:
            print(f"      clasificado {n} -> {cid}  {pp:.3f}  ambos «{c}»")

    if ko:
        print()
        print("   NO SE ESCRIBE NADA: el casado no es de fiar.")
        print()
        sys.exit(1)

    # ------------------------------------------------------------------
    print()
    print("=" * 76)
    print("CUANTO SE EQUIVOCABA LA LISTA DE TERMINOS  ·  el error X25")
    print("=" * 76)
    co2 = co.merge(r[["id", "categoria"]], on="id", how="left")
    co2["norm"] = co2.cuerpo.map(sin_tildes)
    co2["lista_dice_no"] = co2.norm.map(
        lambda t: any(contiene(t, x) for x in NO_COMERCIAL_LISTA)).astype(int)
    co2["autora_dice_no"] = (co2.categoria.str.contains("NO")).astype(int)

    vp = int(((co2.lista_dice_no == 1) & (co2.autora_dice_no == 1)).sum())
    fp = int(((co2.lista_dice_no == 1) & (co2.autora_dice_no == 0)).sum())
    fn = int(((co2.lista_dice_no == 0) & (co2.autora_dice_no == 1)).sum())
    vn = int(((co2.lista_dice_no == 0) & (co2.autora_dice_no == 0)).sum())

    print()
    print(f"   {'':<26}{'la autora: NO':>16}{'la autora: SI':>16}")
    print("   " + "-" * 58)
    print(f"   {'la lista dice NO':<26}{vp:>16}{fp:>16}")
    print(f"   {'la lista dice SI':<26}{fn:>16}{vn:>16}")
    print()
    marcados = vp + fp
    print(f"   La lista marcaba {marcados} correos como no comerciales.")
    print(f"   De esos, acertaba {vp} y SE EQUIVOCABA EN {fp}.")
    if marcados:
        print(f"   Precision: {100*vp/marcados:.1f} %")
    reales = vp + fn
    if reales:
        print(f"   Y se dejaba sin marcar {fn} de los {reales} que si lo eran.")
        print(f"   Cobertura: {100*vp/reales:.1f} %")
    print()
    print("   Por eso la etiqueta automatica no servia, y por eso la cifra")
    print("   que se habia publicado para esta pieza queda retirada.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    r[["id", "categoria", "parecido"]].sort_values("id").to_csv(
        SALIDA, sep=";", index=False, encoding="utf-8")
    print()
    print(f"   [ok] {SALIDA.name}  ·  {len(r)} etiquetas")
    print()
    print("   Ahora:  python scripts/F6_A6_agente_recepcion.py --guardar")
    print()


if __name__ == "__main__":
    main()
