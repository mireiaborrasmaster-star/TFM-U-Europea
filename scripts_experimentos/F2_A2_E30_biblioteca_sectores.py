# -*- coding: utf-8 -*-
"""
F2_A2_E30_biblioteca_sectores.py · ¿mejoraría A2 con una biblioteca de sectores?
================================================================================

LA PREGUNTA
    El clasificador sectorial acierta el 51,73 %. La autora pregunta si daría
    mejor resultado entregarle una "biblioteca": una descripcion de que es
    cada sector y por que una empresa pertenece a el.

    La idea tiene nombre en la literatura —descripciones de etiqueta— y
    encaja de lleno con la tesis del trabajo: si el conocimiento de la casa
    no se deduce, hay que aportarlo.

LO QUE RESULTA AL COMPROBARLO
    1. LA BIBLIOTECA YA EXISTE. `taxanomia.json`, en el proyecto original,
       describe 183 subsectores con criterios de inclusion y de EXCLUSION.
    2. YA SE PROBO, con el modelo cerrado y la biblioteca en el prompt.
    3. PERDIO contra el supervisado. Esta medido desde entonces.
    4. Pero hay una señal a favor de la idea que nadie habia mirado, y un
       camino que nadie ha probado.

QUE HACE ESTE SCRIPT
    Lee la biblioteca y los resultados de aquella evaluacion, los compara con
    las cifras publicadas de A2 y deja por escrito las cuatro conclusiones.
    No entrena nada ni recalcula nada: pone en relacion dos medidas que
    estaban en carpetas distintas.

AVISO DE COMPARABILIDAD
    Las dos evaluaciones NO usan la misma particion. La del modelo cerrado es
    de marzo de 2026 sobre 602 casos de prueba; la de A2 es de septiembre
    sobre 2.652. Las cifras indican un orden de magnitud, no una diferencia
    exacta, y asi se declara.

COMO SE EJECUTA
    python scripts/F2_A2_E30_biblioteca_sectores.py
"""

import json
from pathlib import Path

import pandas as pd

VERSION_SCRIPT = "v1 · 01-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
PRUEBA1 = RAIZ.parent / "PRUEBA 1 - Agente cualificador"
TAXONOMIA = PRUEBA1 / "taxanomia.json"
EVAL = PRUEBA1 / "OUTPUT" / "evaluacion_openai_resumen.xlsx"

# Lo publicado en 4.6.1, sobre 2.652 casos de prueba
A2_PUBLICADO = {
    "Responder siempre lo más común": 13.16,
    "Modelo de lenguaje abierto, sin ejemplos": 33.33,
    "Modelo de lenguaje abierto, con ejemplos": 34.67,
    "TF-IDF + regresión logística": 48.91,
    "Transformer XLM-RoBERTa": 51.73,
}


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"{n} · {t}")
    print("=" * 76)


def main():
    print()
    print("#" * 76)
    print("# F2 · A2 · ¿mejoraría con una biblioteca de sectores?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    titulo(1, "LA BIBLIOTECA YA EXISTE")
    if not TAXONOMIA.exists():
        raise SystemExit(f"No encuentro {TAXONOMIA}")
    tax = json.loads(TAXONOMIA.read_text(encoding="utf-8"))
    sectores = len(tax)
    con_desc_sector = sum(1 for v in tax.values()
                          if isinstance(v, dict) and v.get("descripcion"))
    subsectores = sum(len(v.get("subsectores", {})) for v in tax.values()
                      if isinstance(v, dict))
    largos = [len(d) for v in tax.values() if isinstance(v, dict)
              for d in v.get("subsectores", {}).values() if isinstance(d, str)]

    print(f"   Fichero                        : taxanomia.json")
    print(f"   Sectores de primer nivel       : {sectores:>5}")
    print(f"   …CON descripción propia        : {con_desc_sector:>5}   <-- NINGUNO")
    print(f"   Subsectores descritos          : {subsectores:>5}")
    print(f"   Longitud media de la descripción: {sum(largos)/len(largos):>4.0f} caracteres")
    print()
    print("   Las descripciones no son etiquetas: llevan criterio de")
    print("   inclusión Y DE EXCLUSIÓN. Por ejemplo, para aceites:")
    print("   «...aceites vegetales comestibles. NO APLICA a aceites")
    print("   técnicos o cosméticos.»")
    print()
    print("   Eso es exactamente conocimiento de la casa, del tipo que RQ1")
    print("   demuestra que un modelo general no deduce. Ya está escrito.")

    # ------------------------------------------------------------------ 2
    titulo(2, "Y YA SE PROBÓ  ·  con el modelo cerrado y la biblioteca en el prompt")
    if not EVAL.exists():
        raise SystemExit(f"No encuentro {EVAL}")
    ev = pd.read_excel(EVAL)
    print(f"   {'conjunto':<14}{'casos':>7}{'sector':>10}{'subsector':>12}")
    print("   " + "-" * 44)
    for _, r in ev.iterrows():
        print(f"   {r.dataset:<14}{int(r.total):>7}"
              f"{r.precision_sector:>9.2f}%{r.precision_subsector:>11.2f}%")
    test = ev[ev.dataset == "TEST"].iloc[0]

    print()
    print("   FRENTE A LO PUBLICADO EN 4.6.1  (2.652 casos, otra partición)")
    print("   " + "-" * 60)
    for k, v in sorted(A2_PUBLICADO.items(), key=lambda x: x[1]):
        marca = "   <-- el modelo final" if v == 51.73 else ""
        print(f"   {k:<44}{v:>7.2f}%{marca}")
    print(f"   {'Modelo cerrado CON la biblioteca':<44}"
          f"{test.precision_sector:>7.2f}%   <-- lo que se pregunta")
    print()
    print("   LA BIBLIOTECA EN EL PROMPT NO SUPERÓ AL SUPERVISADO.")
    print(f"   {test.precision_sector:.2f} % frente a 51,73 %: unos "
          f"{51.73 - test.precision_sector:.0f} puntos por debajo.")
    print()
    print("   (Particiones distintas: la cifra indica orden de magnitud, no")
    print("    una diferencia exacta. Coincide con el 40,47 % que la bitácora")
    print("    ya registraba para este mismo experimento.)")

    # ------------------------------------------------------------------ 3
    titulo(3, "PERO HAY UNA SEÑAL A FAVOR QUE NADIE HABÍA MIRADO")
    print(f"   Acierto de SECTOR     : {test.precision_sector:>6.2f} %   "
          f"({sectores} clases, SIN descripción)")
    print(f"   Acierto de SUBSECTOR  : {test.precision_subsector:>6.2f} %   "
          f"({subsectores} clases, CON descripción)")
    print()
    dif = test.precision_subsector - test.precision_sector
    print(f"   Acierta MÁS con {subsectores} clases que con {sectores}: "
          f"+{dif:.2f} puntos.")
    print()
    print("   Eso no es lo normal: a más clases, menos acierto. La explicación")
    print("   más plausible es que el subsector SÍ tiene descripción y el")
    print("   sector NO la tiene.")
    print()
    print("   NO ESTÁ DEMOSTRADO: son dos espacios de etiquetas distintos y la")
    print("   comparación está confundida por ese factor. Pero es la única")
    print("   evidencia disponible sobre la pregunta, y apunta a favor.")

    # ------------------------------------------------------------------ 4
    titulo(4, "LO QUE NADIE HA PROBADO")
    print("   La biblioteca se usó SOLO para el prompt de un modelo cerrado.")
    print("   El transformer, que es el modelo final, nunca la ha visto: se")
    print("   entrenó con pares (texto -> etiqueta) y nada más.")
    print()
    print("   Quedan dos cosas sin hacer, y son baratas:")
    print()
    print("   A · ESCRIBIR LAS 39 DESCRIPCIONES DE SECTOR que faltan.")
    print("       Los 183 subsectores están descritos; los sectores, no. Y el")
    print("       sector es justo lo que A2 predice. Es trabajo de la autora,")
    print("       no mío: el valor está en lo que solo sabe quien trabaja ahí.")
    print()
    print("   B · AÑADIR LA DESCRIPCIÓN AL ENTRENAMIENTO del transformer,")
    print("       no al prompt. Es otra cosa distinta de lo que se probó.")
    print("       Necesita GPU y una tarde de Colab.")

    # ------------------------------------------------------------------ 5
    titulo(5, "ANTES QUE NADA, SIN EMBARGO")
    print("   No se sabe cuánto del 48 % de error es error del modelo y")
    print("   cuánto es desacuerdo con la etiqueta del CRM. Es la medición")
    print("   M3, y hay 263 filas esperando en un Excel.")
    print()
    print("   Si dos personas de la organización coinciden en el 75 % de los")
    print("   casos, el 51,73 % está a 23 puntos del techo humano, no a 48")
    print("   del ideal. Es la misma cifra leída de otra forma, y decide si")
    print("   merece la pena invertir en mejorar el modelo.")
    print()
    print("   Coste: dos horas. Rendimiento: reinterpreta todo el apartado.")
    print()


if __name__ == "__main__":
    main()
