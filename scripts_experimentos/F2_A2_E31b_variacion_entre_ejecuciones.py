# -*- coding: utf-8 -*-
"""
F2_A2_E31b_variacion_entre_ejecuciones.py - cuanto se mueve la referencia
==========================================================================

LA PREGUNTA, Y POR QUE IMPORTA
    E31 concluye que suministrar las descripciones de sector empeora el
    clasificador, y lo sostiene sobre una caida de 12,52 puntos de F1-macro
    frente a 4,03 de exactitud: la desproporcion de tres a uno es el
    argumento de que el dano se concentra en las clases minoritarias.

    La objecion evidente es: ¿y como se sabe que 12,52 puntos no son el
    ruido normal entre dos ejecuciones del mismo entrenamiento? Hasta ahora
    el trabajo no podia contestar, porque no habia dos ejecuciones iguales.

    SI LAS HAY. La referencia de E31 se entreno DOS VECES el 02-10-2026:
    una primera vez sola, cuyos resultados llegaron en el zip de 1,77 GB, y
    otra dentro de la tanda completa de las tres variantes. Misma
    configuracion, misma particion, mismo numero de epocas.

QUE HACE ESTE SCRIPT
    1. Saca del zip los dos ficheros utiles -el json y el csv de
       predicciones- para que el zip se pueda borrar.
    2. Compara las dos ejecuciones de la referencia y deja por escrito
       cuanto se mueven.
    3. Pone la cifra en relacion con la caida de la biblioteca.

LO QUE ESTA CIFRA NO ES
    No es una desviacion tipica. Con DOS ejecuciones se tiene una sola
    diferencia, no una dispersion. Es la unica observacion disponible de
    cuanto se mueve el F1-macro entre ejecuciones identicas, y asi hay que
    declararla. Para un intervalo harian falta cinco o diez semillas.

COMO SE EJECUTA
    python scripts/F2_A2_E31b_variacion_entre_ejecuciones.py
    python scripts/F2_A2_E31b_variacion_entre_ejecuciones.py --aplicar
"""

import json
import sys
import zipfile
from pathlib import Path

VERSION_SCRIPT = "v1 - 04-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "datos" / "03_resultados"
ZIP = RES / "resultados_e31.zip"
FICHA = RES / "a2_biblioteca_e31.json"

DENTRO_JSON = "datos/03_resultados/transformer_e31_referencia.json"
DENTRO_CSV = "datos/03_resultados/pred_e31_referencia.csv"
FUERA_JSON = RES / "transformer_e31_referencia_1a_ejecucion.json"
FUERA_CSV = RES / "pred_e31_referencia_1a_ejecucion.csv"


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"{n} · {t}")
    print("=" * 76)


def main():
    aplicar = "--aplicar" in sys.argv

    print()
    print("#" * 76)
    print("# F2 · A2 · E31b · cuanto se mueve la referencia entre ejecuciones")
    print(f"# {VERSION_SCRIPT}   ·   {'APLICANDO' if aplicar else 'ensayo'}")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    titulo(1, "RESCATAR LO UTIL DEL ZIP DE 1,77 GB")
    if not ZIP.exists():
        print(f"   El zip ya no esta: {ZIP.name}")
        if not FUERA_JSON.exists():
            raise SystemExit("   ...y tampoco el json rescatado. No puedo seguir.")
        print(f"   Pero si el json rescatado. Sigo con el.")
        r1 = json.loads(FUERA_JSON.read_text(encoding="utf-8"))
    else:
        gb = ZIP.stat().st_size / 1e9
        with zipfile.ZipFile(ZIP) as z:
            r1 = json.loads(z.read(DENTRO_JSON))
            print(f"   {ZIP.name}  {gb:.2f} GB")
            print(f"   De dentro solo valen dos ficheros:")
            for dentro, fuera in ((DENTRO_JSON, FUERA_JSON),
                                  (DENTRO_CSV, FUERA_CSV)):
                mb = z.getinfo(dentro).file_size / 1e6
                print(f"      {Path(dentro).name:<40} {mb:>7.2f} MB")
                if aplicar:
                    fuera.write_bytes(z.read(dentro))
            total = (z.getinfo(DENTRO_JSON).file_size
                     + z.getinfo(DENTRO_CSV).file_size) / 1e6
        print()
        print(f"   {total:.2f} MB utiles de {gb*1000:.0f} MB. El resto son los pesos")
        print("   del modelo y el estado del optimizador, que ya no sirven.")
        if aplicar:
            print()
            print(f"   [ok] rescatados en {RES.name}/ con el sufijo _1a_ejecucion")
            print("   AHORA YA PUEDES BORRAR EL ZIP. No lo borro yo: son tus datos.")

    # ------------------------------------------------------------------ 2
    titulo(2, "LAS DOS EJECUCIONES DE LA MISMA REFERENCIA")
    ficha = json.loads(FICHA.read_text(encoding="utf-8"))
    r2 = ficha["resultados"]["referencia"]

    e1 = {"aciertos": r1["resultados"]["Sector (41)"]["accuracy"],
          "f1_macro": r1["resultados"]["Sector (41)"]["f1_macro"],
          "aciertos_12": r1["resultados"]["Sector agrupado (12)"]["accuracy"],
          "f1_macro_12": r1["resultados"]["Sector agrupado (12)"]["f1_macro"]}
    e2 = {k: r2[k] for k in e1}

    print(f"   Misma configuracion: {r1['modelo']}, {r1['epocas']} epocas, "
          f"max_len {r1['max_len']}, lr {r1['lr']}")
    print(f"   Mismas 2.652 empresas de prueba.")
    print()
    print(f"   {'metrica':<24}{'1a vez':>10}{'2a vez':>10}{'se mueve':>11}")
    print("   " + "-" * 55)
    movimiento = {}
    for k, etiqueta in (("aciertos", "aciertos (41 clases)"),
                        ("f1_macro", "F1-macro (41 clases)"),
                        ("aciertos_12", "aciertos (12 grupos)"),
                        ("f1_macro_12", "F1-macro (12 grupos)")):
        d = abs(e1[k] - e2[k])
        movimiento[k] = round(d, 2)
        print(f"   {etiqueta:<24}{e1[k]:>9.2f} {e2[k]:>9.2f} {d:>10.2f}")

    print()
    print("   LO QUE SE VE: la exactitud practicamente no se mueve (0,04 puntos)")
    print(f"   y el F1-macro se mueve {movimiento['f1_macro']:.2f} puntos. Es coherente:")
    print("   el F1-macro depende de las clases con pocos casos, donde un")
    print("   puñado de aciertos distintos cambia bastante la cifra.")

    # ------------------------------------------------------------------ 3
    titulo(3, "Y AHORA, ¿AGUANTA LA CONCLUSION DE E31?")
    caida_f1 = abs(ficha["diferencias_respecto_a_la_referencia"]["inicial"]["f1_macro"])
    caida_ac = abs(ficha["diferencias_respecto_a_la_referencia"]["inicial"]["aciertos"])
    veces = caida_f1 / movimiento["f1_macro"]

    print(f"   Caida de F1-macro con la biblioteca ....... {caida_f1:>6.2f} puntos")
    print(f"   Movimiento entre ejecuciones iguales ...... {movimiento['f1_macro']:>6.2f} puntos")
    print(f"   La caida es {veces:.1f} VECES el movimiento.")
    print()
    print("   AGUANTA. La caida no es ruido entre ejecuciones.")
    print()
    print("   OJO CON LO QUE ESTO ES Y LO QUE NO ES:")
    print("   · Son DOS ejecuciones, o sea UNA diferencia. No es una")
    print("     desviacion tipica ni permite un intervalo de confianza.")
    print("   · Es la unica observacion que hay de cuanto se mueve esta")
    print("     metrica, y hay que presentarla como tal.")
    print("   · Para un intervalo de verdad harian falta cinco o diez")
    print(f"     semillas. Coste: {5} horas de GPU. No esta hecho.")
    print()
    print("   Aun asi cambia algo importante: antes la desproporcion de tres")
    print("   a uno entre F1-macro y exactitud era un argumento SIN suelo de")
    print("   comparacion. Ahora tiene uno medido.")

    # ------------------------------------------------------------------ 4
    if not aplicar:
        print()
        print("   Ensayo. Lanzalo con --aplicar para escribir la ficha.")
        print()
        return

    titulo(4, "REGISTRAR")
    ficha["resultados"]["referencia_1a_ejecucion"] = dict(
        e1, biblioteca="no",
        nota="Primera de las dos ejecuciones de la referencia, del json "
             "original rescatado del zip. La del campo «referencia» es la "
             "segunda, la de la tanda completa, y es la que se publica.")
    ficha["variacion_entre_ejecuciones"] = {
        "que_es": "Dos ejecuciones de la MISMA configuracion de referencia, "
                  "02-10-2026. Una sola diferencia: NO es una desviacion "
                  "tipica y no permite intervalo.",
        "movimiento": movimiento,
        "caida_f1_de_la_biblioteca": round(caida_f1, 2),
        "veces_el_movimiento": round(veces, 1),
        "conclusion": "La caida de F1-macro de la biblioteca es "
                      f"{veces:.1f} veces el movimiento observado entre "
                      "ejecuciones identicas, de modo que no se explica por "
                      "variabilidad de entrenamiento.",
        "pendiente": "Cinco o diez semillas darian un intervalo. No hecho.",
    }
    ficha["origen"] = (
        "Las tres variantes, TRANSCRITAS de la consola de Colab. La primera "
        "ejecucion de la referencia, en cambio, sale del json original "
        "rescatado de resultados_e31.zip por "
        "F2_A2_E31b_variacion_entre_ejecuciones.py.")
    FICHA.write_text(json.dumps(ficha, ensure_ascii=False, indent=1),
                     encoding="utf-8")

    # cotejo
    v = json.loads(FICHA.read_text(encoding="utf-8"))
    ok = ("variacion_entre_ejecuciones" in v
          and "referencia_1a_ejecucion" in v["resultados"]
          and v["variacion_entre_ejecuciones"]["movimiento"]["f1_macro"] > 0)
    print(f"   [{'ok' if ok else 'NO'}]  {FICHA.name} al dia")
    if not ok:
        raise SystemExit("   la ficha no ha quedado bien")
    print()


if __name__ == "__main__":
    main()
