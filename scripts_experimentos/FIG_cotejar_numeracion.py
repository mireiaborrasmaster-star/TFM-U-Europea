# -*- coding: utf-8 -*-
"""
FIG_cotejar_numeracion.py - comprueba que la numeracion de figuras cuadra
==========================================================================

POR QUE EXISTE
    El 03-10-2026 se dio por buena una numeracion que tenia DOS figuras con
    el numero 7 y le faltaban dos. La comprobacion que se uso entonces
    contaba los numeros presentes pero se comia el recuento, asi que un
    numero repetido se veia igual que uno solo. Error X23.

    Una comprobacion que no distingue «una vez» de «dos veces» no comprueba
    nada. Este script existe para no volver a improvisarla.

QUE COMPRUEBA
    1. Cada numero de figura aparece EXACTAMENTE UNA VEZ en toda la memoria.
    2. El numero del marcador coincide con el del nombre del fichero.
    3. La clave del fichero es la que la tabla de pies dice para ese numero.
    4. Estan las 21: ningun numero de la tabla se queda sin marcador.
    5. Cada .png referenciado existe en figuras/, y ningun .png de figuras/
       se queda sin referenciar.
    6. Informa de los numeros de tabla repetidos, que no son error pero
       conviene verlos.

    Devuelve codigo de salida 1 si algo falla, para poder encadenarlo.

COMO SE EJECUTA
    python scripts/FIG_cotejar_numeracion.py
"""

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

VERSION_SCRIPT = "v1 - 03-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
MEMORIA = RAIZ / "memoria"
FIGURAS = RAIZ / "figuras"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from FIG_numerar_memoria import PIES  # noqa: E402

# un pie completo: marcador, titulo y debajo el nombre del fichero
PIE = re.compile(r"`\[FIGURA (\d+)\]`(.*?)`figuras/fig(\d\d)_([a-zA-Z0-9_]+)\.png`",
                 re.S)
# un marcador suelto, para pillar los que se han quedado sin fichero debajo
MARCA = re.compile(r"`?\[FIGURA (\d+)\]`?")
TABLA = re.compile(r"`\[TABLA ([0-9]+[a-z]?)\]`")


def main():
    print()
    print("=" * 74)
    print(f"FIG - cotejo de la numeracion  ·  {VERSION_SCRIPT}")
    print("=" * 74)

    ficheros = sorted(MEMORIA.glob("*.md"))
    if not ficheros:
        raise SystemExit(f"   No hay nada en {MEMORIA}")

    pies = []              # (numero, clave, fichero_memoria)
    marcas = Counter()
    marcas_donde = defaultdict(list)
    tablas = Counter()

    for f in ficheros:
        t = f.read_text(encoding="utf-8")
        # los marcadores de la cabecera explicativa no cuentan
        t = t.replace("`[FIGURA n]`", "")
        for m in PIE.finditer(t):
            pies.append((int(m.group(1)), int(m.group(3)), m.group(4), f.name))
        for m in MARCA.finditer(t):
            marcas[int(m.group(1))] += 1
            marcas_donde[int(m.group(1))].append(f.name)
        for m in TABLA.finditer(t):
            tablas[m.group(1)] += 1

    fallos = []

    # ---------------------------------------------------------------- 1
    print()
    print("1 · ¿aparece cada número una sola vez?")
    repetidos = {n: c for n, c in marcas.items() if c > 1}
    if repetidos:
        for n, c in sorted(repetidos.items()):
            donde = ", ".join(sorted(set(marcas_donde[n])))
            print(f"   [NO]  FIGURA {n} aparece {c} veces  ({donde})")
            fallos.append(f"figura {n} repetida {c} veces")
    else:
        print(f"   [ok]  {len(marcas)} números, ninguno repetido")

    # ---------------------------------------------------------------- 2 y 3
    print()
    print("2 · ¿coincide el marcador con el nombre del fichero, y con la tabla?")
    malos = 0
    for num_marca, num_fich, clave, origen in pies:
        esperada = PIES.get(num_marca, (None, None))[0]
        if num_marca != num_fich:
            print(f"   [NO]  {origen}: marcador {num_marca} sobre "
                  f"fig{num_fich:02d}_{clave}")
            fallos.append(f"marcador {num_marca} con fichero {num_fich}")
            malos += 1
        elif esperada != f"fig{num_fich:02d}_{clave}":
            print(f"   [NO]  {origen}: la figura {num_marca} debería ser "
                  f"«{esperada}» y es «fig{num_fich:02d}_{clave}»")
            fallos.append(f"figura {num_marca} con la clave equivocada")
            malos += 1
    if not malos:
        print(f"   [ok]  los {len(pies)} pies cuadran con la tabla")

    # ---------------------------------------------------------------- 4
    print()
    print("4 · ¿están todas?")
    faltan = sorted(set(PIES) - set(marcas))
    sobran = sorted(set(marcas) - set(PIES))
    if faltan:
        print(f"   [NO]  faltan en la memoria: {faltan}")
        fallos.append(f"faltan las figuras {faltan}")
    if sobran:
        print(f"   [NO]  marcadores que no están en la tabla: {sobran}")
        fallos.append(f"marcadores sin tabla {sobran}")
    if not faltan and not sobran:
        print(f"   [ok]  las {len(PIES)} figuras de la tabla están en la memoria")

    # ---------------------------------------------------------------- 5
    print()
    print("5 · ¿existen los ficheros, y sobra alguno?")
    referenciados = {f"fig{n:02d}_{c}" for _, n, c, _ in pies}
    en_disco = {p.stem for p in FIGURAS.glob("fig*.png")}
    sin_fichero = sorted(referenciados - en_disco)
    sin_referencia = sorted(en_disco - referenciados)
    if sin_fichero:
        print(f"   [NO]  referenciados y no están en figuras/: {sin_fichero}")
        fallos.append(f"faltan los png {sin_fichero}")
    if sin_referencia:
        print(f"   [!!]  en figuras/ y nadie los cita: {sin_referencia}")
    if not sin_fichero and not sin_referencia:
        print(f"   [ok]  {len(referenciados)} png, todos existen y todos se citan")

    # ---------------------------------------------------------------- 6
    print()
    # ------------------------------------------------------------------
    print()
    print("7 · ¿hay dibujo pegado al borde?")
    # Desde que el lienzo lleva margen (fig_comun.MARGEN) ningun pixel
    # deberia caer en los 3 mm exteriores. Si cae, es que el contenido se
    # salio: paso al alargar el subtitulo de la figura 5, y el pie quedaba
    # cortado sin que nadie lo viera.
    try:
        from PIL import Image
        import numpy as np
        malas = []
        for f in sorted(FIGURAS.glob("*.png")):
            a_ = np.array(Image.open(f).convert("L"))
            borde = max(2, int(round(a_.shape[1] / 160 * 3)))   # ~3 mm
            tinta = a_ < 235
            if (tinta[:borde].any() or tinta[-borde:].any()
                    or tinta[:, :borde].any() or tinta[:, -borde:].any()):
                malas.append(f.name)
        if malas:
            for m in malas:
                print(f"   [NO]  {m} tiene dibujo en el margen")
            fallos.append(f"{len(malas)} figuras pegadas al borde")
        else:
            print(f"   [ok]  las {len(list(FIGURAS.glob('*.png')))} figuras "
                  f"respetan el margen")
    except ImportError:
        print("   [i ]  sin Pillow: no se puede comprobar")

    print("6 · tablas repetidas (informativo, no es error)")
    rep_t = {k: c for k, c in tablas.items() if c > 1}
    if rep_t:
        for k, c in sorted(rep_t.items()):
            print(f"   [!!]  TABLA {k} aparece {c} veces")
    else:
        print(f"   [ok]  {len(tablas)} tablas, ninguna repetida")

    # ---------------------------------------------------------------- 7
    # El indice de figuras se desfasaba cada vez que entraba una figura
    # nueva. Se genera desde la tabla de pies y desde el apartado en que
    # cada marcador aparece de verdad, asi que no puede desviarse.
    if "--reescribir-indice" in sys.argv and not fallos:
        print()
        print("7 · reescribiendo el índice de figuras")
        apartado = {}
        for f in ficheros:
            actual = None
            for linea in f.read_text(encoding="utf-8").splitlines():
                m = re.match(r"#{2,3} (\d+(?:\.\d+)*)", linea)
                if m:
                    actual = m.group(1)
                m = re.match(r"`\[FIGURA (\d+)\]`", linea)
                if m:
                    apartado[int(m.group(1))] = actual or f.name
        filas = ["| # | Fichero | Título | Apartado |",
                 "| --- | --- | --- | --- |"]
        for n in sorted(PIES):
            fich, tit = PIES[n]
            tit = " ".join(tit.split())
            if len(tit) > 70:
                tit = tit[:67] + "…"
            filas.append(f"| {n} | `{fich}` | {tit} | "
                         f"{apartado.get(n, '—')} |")
        destino = FIGURAS / "00_INDICE_FIGURAS.md"
        cab = ("# Índice de figuras\n\n"
               "> Generado por `FIG_cotejar_numeracion.py --reescribir-indice`.\n"
               "> **No se edita a mano:** los números salen de la tabla de pies de\n"
               "> `FIG_numerar_memoria.py` y el apartado, de donde el marcador\n"
               "> aparece de verdad en la memoria.\n\n")
        destino.write_text(cab + "\n".join(filas) + "\n", encoding="utf-8")
        print(f"   [ok]  {destino.name}: {len(PIES)} figuras")

    # ----------------------------------------------------------------
    print()
    print("=" * 74)
    if fallos:
        print(f"   {len(fallos)} FALLO(S):")
        for x in fallos:
            print(f"      · {x}")
        print()
        sys.exit(1)
    print("   La numeración cuadra.")
    print()


if __name__ == "__main__":
    main()
