# -*- coding: utf-8 -*-
"""
TAB_numerar_memoria.py · pone las tablas en orden, de 1 a N
============================================================

EL PROBLEMA QUE RESUELVE
    Las tablas se fueron numerando capitulo a capitulo, segun se escribian,
    y el resultado tenia dos averias:

      1. NUMEROS REPETIDOS. La numeracion continua se hizo suponiendo el
         orden CAP2 -> CAP4_2 -> CAP4_6 -> CAP5 -> CAP7, y despues se
         escribieron CAP3_3 y CAP4_1 con su propia cuenta desde el 4. Hay
         dieciseis marcadores duplicados: dos tablas distintas con el
         mismo numero, cuatro de ellas DENTRO del mismo capitulo.

      2. SUFIJOS DE LETRA. Cada tabla insertada despues llevaba una letra
         para no mover las siguientes: 51b, 51i, y de ahi a 51i1 ... 51i8.
         Funciono como andamio, pero no es numeracion.

    Este guion recorre los capitulos EN EL ORDEN DE LECTURA, numera cada
    tabla segun aparece y arregla tambien las referencias en prosa.

POR QUE ES UN GUION Y NO UN ARREGLO A MANO
    Porque hay que repetirlo. Faltan por escribir los capitulos 1, 3.1,
    3.2, 4.3, 4.4, 4.5, 6, 8 y 9; en cuanto alguno traiga una tabla, la
    numeracion se desplaza. Volver a lanzarlo es un comando.

QUE NO HACE
    No toca las FIGURAS: de eso se encarga FIG_numerar_memoria.py, y su
    numeracion esta cotejada aparte.

COMO SE EJECUTA
    python scripts/TAB_numerar_memoria.py              # solo enseña el plan
    python scripts/TAB_numerar_memoria.py --aplicar
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MEM = RAIZ / "memoria"

# El orden de lectura de la memoria, segun 15_INDICE_MEMORIA.md. Lo que no
# existe todavia se ignora sin ruido: asi el guion sigue valiendo cuando se
# escriban los capitulos que faltan.
ORDEN = [
    "CAP1_resumen.md",
    "CAP2_antecedentes.md",
    "CAP3_1_objetivos.md", "CAP3_2_objetivos.md", "CAP3_3_beneficios.md",
    "CAP4_1_planificacion.md", "CAP4_2_solucion.md",
    "CAP4_3_recursos.md", "CAP4_4_costes.md", "CAP4_5_viabilidad.md",
    "CAP4_6_resultados.md",
    "CAP5_discusion.md",
    "CAP6_conclusiones.md",
    "CAP7_futuras_lineas.md",
    "CAP8_referencias.md", "CAP9_anexos.md",
]

MARCADOR = re.compile(r"\[TABLA ([0-9]+[a-z0-9]*)\]")
EN_PROSA = re.compile(r"\b([Tt]abla) ([0-9]+[a-z0-9]*)\b")


def main():
    aplicar = "--aplicar" in sys.argv

    print()
    print("#" * 76)
    print("# TAB · numerar las tablas de la memoria en orden de lectura")
    print("#" * 76)

    ficheros = [MEM / n for n in ORDEN if (MEM / n).exists()]
    faltan = [n for n in ORDEN if not (MEM / n).exists()]
    print()
    print(f"   Capitulos encontrados: {len(ficheros)} de {len(ORDEN)}")
    if faltan:
        print(f"   Sin escribir todavia : {', '.join(x[:7] for x in faltan)}")

    # ---- 1 · el plan, sin tocar nada -------------------------------------
    print()
    print("=" * 76)
    print("PASO 1 · QUE HAY AHORA")
    print("=" * 76)
    textos = {f: f.read_text(encoding="utf-8") for f in ficheros}
    # Se numera POR APARICION, no por etiqueta. Es la diferencia que
    # importa: cuando una etiqueta sale dos veces en el mismo capitulo
    # —51m, 51n, 51o y 51p lo hacian— un diccionario etiqueta -> numero
    # asigna el mismo numero a las dos y el problema sobrevive al arreglo.
    plan = {}          # fichero -> [numero nuevo de cada aparicion, en orden]
    n = 0
    vistos = {}
    for f in ficheros:
        etiquetas = MARCADOR.findall(textos[f])
        plan[f.name] = list(range(n + 1, n + 1 + len(etiquetas)))
        for e in etiquetas:
            n += 1
            vistos.setdefault(e, []).append(f.name)
        print(f"   {f.name:<28}{len(etiquetas):>4} tablas")
    print(f"   {'TOTAL':<28}{n:>4}")
    # para la prosa hace falta etiqueta -> numero, y eso SOLO es fiable
    # cuando la etiqueta aparece una vez en ese capitulo
    mapa, ambiguas = {}, set()
    for f in ficheros:
        ets = MARCADOR.findall(textos[f])
        for e, nuevo in zip(ets, plan[f.name]):
            if ets.count(e) > 1:
                ambiguas.add((f.name, e))
            else:
                mapa[(f.name, e)] = nuevo

    dup = {e: v for e, v in vistos.items() if len(v) > 1}
    print()
    print(f"   Marcadores repetidos: {len(dup)}")
    for e, donde in sorted(dup.items()):
        mismo = " · ¡DOS VECES EN EL MISMO CAPITULO!" if len(set(donde)) == 1 else ""
        print(f"      {e:<6} en {', '.join(x[:8] for x in donde)}{mismo}")
    letras = sorted({e for e in vistos if not e.isdigit()})
    print()
    print(f"   Marcadores con sufijo de letra: {len(letras)}")
    print(f"      {', '.join(letras[:18])}{' …' if len(letras) > 18 else ''}")

    # ---- 2 · las referencias en prosa ------------------------------------
    print()
    print("=" * 76)
    print("PASO 2 · LAS REFERENCIAS EN PROSA")
    print("=" * 76)
    print("   Una referencia «tabla 8» se resuelve DENTRO de su capitulo: es")
    print("   lo unico que la desambigua cuando el 8 esta repetido.")
    refs, huerfanas = [], []
    for f in ficheros:
        for m in EN_PROSA.finditer(textos[f]):
            et = m.group(2)
            if (f.name, et) in mapa:
                refs.append((f.name, m.group(0), mapa[(f.name, et)]))
            elif (f.name, et) in ambiguas:
                huerfanas.append((f.name, m.group(0) + " · la etiqueta sale "
                                  "DOS VECES en ese capitulo"))
            else:
                huerfanas.append((f.name, m.group(0)))
    for fn, txt, nuevo in refs:
        print(f"   [ok]  {fn[:22]:<24}«{txt}»  ->  tabla {nuevo}")
    for fn, txt in huerfanas:
        print(f"   [!!]  {fn[:22]:<24}«{txt}» no corresponde a ninguna tabla")
        print(f"         de ese capitulo. HAY QUE MIRARLA A MANO.")

    # ---- 3 · aplicar ------------------------------------------------------
    print()
    print("=" * 76)
    print("PASO 3 · EL RESULTADO")
    print("=" * 76)
    cambios = sum(1 for f in ficheros
                  for e, nu in zip(MARCADOR.findall(textos[f]), plan[f.name])
                  if e != str(nu))
    print(f"   Tablas que cambian de numero : {cambios} de {n}")
    print(f"   Referencias en prosa que cambian: "
          f"{sum(1 for _, t, nu in refs if t.split()[-1] != str(nu))}")

    if not aplicar:
        print()
        print("   Ensayo: no se ha escrito nada. Usa --aplicar.")
        print()
        return 0

    for f in ficheros:
        s = textos[f]
        pendientes = iter(plan[f.name])

        def rep_marcador(m, it=pendientes):
            return f"[TABLA {next(it)}]"

        def rep_prosa(m, fn=f.name):
            et = m.group(2)
            if (fn, et) in mapa:
                return f"{m.group(1)} {mapa[(fn, et)]}"
            return m.group(0)

        # primero la prosa, que lee las etiquetas VIEJAS, y despues los
        # marcadores: al reves, la prosa buscaria numeros ya cambiados
        s = EN_PROSA.sub(rep_prosa, s)
        s = MARCADOR.sub(rep_marcador, s)
        f.write_text(s, encoding="utf-8")
        print(f"   [ok]  {f.name}")

    # ---- 4 · cotejo -------------------------------------------------------
    print()
    print("=" * 76)
    print("COTEJO")
    print("=" * 76)
    ko = 0
    todas = []
    for f in ficheros:
        todas += MARCADOR.findall(f.read_text(encoding="utf-8"))
    esperado = [str(i) for i in range(1, n + 1)]
    if todas == esperado:
        print(f"   [ok]  las {n} tablas van de 1 a {n}, en orden y sin repetir")
    else:
        print(f"   [NO]  la secuencia no cuadra")
        rep = {x for x in todas if todas.count(x) > 1}
        if rep:
            print(f"         repetidos: {sorted(rep)[:10]}")
        ko += 1
    letras = [x for x in todas if not x.isdigit()]
    print(f"   [{'ok' if not letras else 'NO'}]  no queda ningun sufijo de letra")
    ko += 0 if not letras else 1
    if huerfanas:
        print(f"   [!!]  {len(huerfanas)} referencias en prosa sin resolver, "
              f"mirar a mano")
    print()
    return ko


if __name__ == "__main__":
    sys.exit(main())
