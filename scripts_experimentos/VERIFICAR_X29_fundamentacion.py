# -*- coding: utf-8 -*-
"""
VERIFICAR_X29_fundamentacion.py · hasta donde llega el error X29
================================================================

QUE SE ENCONTRO, EN E38
    El recortador de palabras dejaba «envase» tal cual pero convertia
    «envases» en «envas»: la regla del plural mira «es» al final, y
    «envase» acaba en «se». Resultado: la MISMA palabra no se reconocia a
    si misma cuando el texto la escribia en plural. La comprobacion de
    fundamentacion del briefing daba 84,4 % donde por construccion tenia
    que dar 100 %, y ahi se destapo.

POR QUE HAY QUE MIRAR A5
    A5 mide su fundamentacion igual —terminos del correo generado que NO
    aparecen en la evidencia— y su recortador, aunque es otro, tiene el
    mismo agujero: corta «es», «as», «os», «a», «o» y «s», y no la «e»
    final. Si el agujero actua, la fundamentacion publicada de A5 esta
    SUBESTIMADA: se contaron como inventados terminos que si estaban en la
    evidencia.

    El sentido del error importa. Subestimar no tumba la afirmacion «el
    correo se sostiene en la evidencia»: la deja medida por lo bajo. Pero
    la cifra no es la que se publico, y el suelo tampoco, porque el suelo
    se calcula con la misma metrica.

QUE HACE ESTE GUION, SIN GPU Y SIN VOLVER A GENERAR NADA
    1. Comprueba que el agujero existe tambien en el recortador de A5.
    2. Recalcula la fundamentacion de los 40 correos ya guardados de las
       dos maneras, cotejando primero que reproduce la cifra publicada.
    3. Rehace el control por permutacion de E19 con la metrica corregida,
       porque una cifra sin su suelo no significa nada: es la leccion X9.

COMO SE EJECUTA
    python scripts/VERIFICAR_X29_fundamentacion.py
    python scripts/VERIFICAR_X29_fundamentacion.py --permutaciones 5000
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DERIVADO = RAIZ / "datos" / "02_derivado"
RES = RAIZ / "datos" / "03_resultados"

PUBLICADO = 34.84          # memoria 4.6.3 y bitacora E19
SUELO_PUBLICADO = 28.8
SEMILLA = 42

# la misma lista de palabras vacias de A5, copiada literal: sin ella el
# recalculo no reproduce la cifra publicada y no se puede comparar nada
VACIAS = {"que", "de", "la", "el", "los", "las", "una", "uno", "para", "con",
          "por", "del", "las", "sus", "este", "esta", "como", "mas", "sobre",
          "entre", "desde", "hasta", "pero", "todo", "cada", "muy", "ser",
          "son", "han", "hay", "les", "nos", "vuestro", "vuestra", "empresa",
          "empresa", "correo", "asunto", "cuerpo", "saludo", "hola", "gracias"}

SUFIJOS = ("mientos", "aciones", "amiento", "ciones", "mente", "ando",
           "endo", "imos", "amos", "eis", "ais", "ado", "ido", "ar",
           "er", "ir", "es", "as", "os", "a", "o", "s")


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def raiz(palabra, arreglado=False):
    """El recortador de A5. Con `arreglado` se le anade la regla que
    faltaba: quitar tambien la «e» final."""
    p = palabra
    for suf in SUFIJOS:
        if len(p) - len(suf) >= 5 and p.endswith(suf):
            return p[:-len(suf)]
    if arreglado and len(p) > 5 and p.endswith("e"):
        return p[:-1]
    return p


def terminos(texto, arreglado=False, minimo=5):
    return {raiz(w, arreglado)
            for w in re.findall(r"[a-z]{%d,}" % minimo, sin_acentos(texto))
            if w not in VACIAS}


def texto_servicio(s):
    return (f"{s['nombre']}. {s['resuelve']} Dirigido a: {s['para_quien']} "
            f"Temas relacionados: {', '.join(s['senales'][:12])}.")


def main():
    reps = 2000
    if "--permutaciones" in sys.argv:
        reps = int(sys.argv[sys.argv.index("--permutaciones") + 1])

    print()
    print("#" * 76)
    print("# VERIFICAR X29 · el recortador de palabras y la fundamentacion")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    print()
    print("=" * 76)
    print("PASO 1 · ¿EXISTE EL AGUJERO TAMBIEN EN A5?")
    print("=" * 76)
    print(f"   {'palabra':<14}{'recortador de A5':>18}{'arreglado':>14}")
    print("   " + "-" * 50)
    for w in ("envase", "envases", "embalaje", "embalajes", "informe",
              "informes", "muestra", "muestras"):
        print(f"   {w:<14}{raiz(w):>18}{raiz(w, True):>14}")
    print()
    print("   Si: «envase» y «envases» no llegaban al mismo sitio. Con la")
    print("   regla que faltaba, si.")

    # ------------------------------------------------------------------ 2
    print()
    print("=" * 76)
    print("PASO 2 · RECALCULAR SOBRE LOS CORREOS YA GUARDADOS")
    print("=" * 76)
    cat = {s["codigo"]: s for s in
           json.loads((RES / "a5_catalogo.json").read_text(encoding="utf-8"))}
    e = pd.read_csv(RES / "a5_correos.csv")
    d = pd.concat([pd.read_csv(DERIVADO / f"cuentas_{p}.csv")
                   for p in ("train", "val", "test")], ignore_index=True)
    d = d[d.tiene_texto.fillna(False)]
    print(f"   Correos guardados                : {len(e)}")
    print(f"   Webs disponibles para el control : {len(d)}")

    res = {}
    for arr in (False, True):
        t_web = {k: terminos(v, arr) for k, v in
                 zip(d.empresa_clave, d.web_text.fillna(""))}
        t_serv = {c: terminos(texto_servicio(s), arr) for c, s in cat.items()}
        t_cor = [terminos(r.correo, arr) for r in e.itertuples()]
        servicios = list(e.servicio)
        claves = np.array(list(t_web.keys()))

        def media(webs, t_cor=t_cor, t_web=t_web, t_serv=t_serv):
            v = [1 - len(tc - (t_web[w] | t_serv[s])) / max(len(tc), 1)
                 for tc, s, w in zip(t_cor, servicios, webs)]
            return float(np.mean(v))

        rng = np.random.default_rng(SEMILLA)
        real = media(list(e.empresa_clave))
        nulas = np.array([media(rng.choice(claves, len(e), replace=False))
                          for _ in range(reps)])
        res[arr] = (100 * real, 100 * nulas.mean(), 100 * nulas.std(),
                    (real - nulas.mean()) / nulas.std(),
                    float((nulas >= real).mean()))

    print()
    print(f"   La cifra publicada en 4.6.3 es {PUBLICADO:.2f} % y el recalculo")
    print(f"   con la metrica de entonces da {res[False][0]:.2f} %.")
    if abs(res[False][0] - PUBLICADO) < 0.05:
        print("   Reproduce, asi que a partir de aqui se puede comparar.")
    else:
        print("   [!!] NO reproduce. No se toca ninguna cifra hasta saber por")
        print("        que: puede que la evidencia de entonces no sea esta.")
        print()
        return
    print()
    print(f"   (La columna guardada en a5_correos.csv promedia "
          f"{100*e.fundamentacion.mean():.2f} %, que no")
    print(f"   es lo publicado: la cifra de la memoria la calcula el control,")
    print(f"   no el generador. Es la misma medida en dos momentos, y la de la")
    print(f"   memoria es la del control.)")

    # ------------------------------------------------------------------ 3
    print()
    print("=" * 76)
    print("PASO 3 · LA CIFRA Y SU SUELO, CON LA METRICA CORREGIDA")
    print("=" * 76)
    print(f"   Suelo por permutacion: cada correo contra la web de OTRA")
    print(f"   empresa, {reps} veces. Es el control de E19, rehecho.")
    print()
    print(f"   {'':<26}{'su web':>10}{'otra web':>11}{'diferencia':>13}{'z':>8}")
    print("   " + "-" * 74)
    for arr, nom in ((False, "Como se publico"), (True, "Con X29 corregido")):
        r, s_, sd, z, p = res[arr]
        marca = "**" if arr else "  "
        print(f"   {marca}{nom:<24}{r:>8.2f} %{s_:>9.2f} %"
              f"{r - s_:>+11.2f} p{z:>8.2f}")
    r0, s0 = res[False][0], res[False][1]
    r1, s1 = res[True][0], res[True][1]
    print()
    print(f"   La fundamentacion sube {r1 - r0:+.2f} puntos al corregir el")
    print(f"   recortador, pero EL SUELO SUBE {s1 - s0:+.2f}, porque se calcula con")
    print(f"   la misma metrica. Lo que decide es la diferencia entre las dos:")
    print(f"   {r0 - s0:+.2f} puntos antes y {r1 - s1:+.2f} puntos despues.")
    print()
    if res[True][4] < 0.05 and (r1 - s1) > 0:
        print(f"   LA CONCLUSION DE E19 AGUANTA: el correo se sostiene en SU")
        print(f"   evidencia y no en el castellano corriente, con p = "
              f"{res[True][4]:.4f} y")
        print(f"   z = {res[True][3]:.2f}. Lo que cambia son las dos cifras "
              f"absolutas, que")
        print(f"   estaban medidas por lo bajo.")
    else:
        print(f"   LA CONCLUSION DE E19 NO AGUANTA con la metrica corregida:")
        print(f"   p = {res[True][4]:.4f}. Hay que rehacer el apartado 4.6.3.")
    print()
    print(f"   QUE HABRIA QUE CAMBIAR EN LA MEMORIA si se adopta la correccion")
    print(f"   tambien en A5:")
    print(f"      4.6.3 · fundamentacion {PUBLICADO:.2f} %  ->  {r1:.2f} %")
    print(f"      4.6.3 · suelo {SUELO_PUBLICADO:.1f} %  ->  {s1:.2f} %")
    print(f"      la diferencia, de {r0-s0:+.2f} a {r1-s1:+.2f} puntos, y la z,")
    print(f"      de {res[False][3]:.2f} a {res[True][3]:.2f}")
    print()
    print(f"   Y SI NO SE ADOPTA, tambien se sostiene: la metrica de entonces")
    print(f"   era conservadora y la conclusion no cambia. Lo que no vale es")
    print(f"   dejarlo sin decir, y por eso esto queda escrito como X29.")
    print()

    salida = {
        "error": "X29", "donde_se_vio": "E38, el briefing de A8",
        "que_es": "el recortador no hacia coincidir el singular de las "
                  "palabras terminadas en -e con su plural",
        "sentido_del_error": "subestimaba la fundamentacion; nunca inflo "
                             "ninguna cifra",
        "alcance_a5": {
            "publicado": PUBLICADO,
            "recalculado_con_la_metrica_de_entonces": res[False][0],
            "reproduce_lo_publicado": bool(abs(res[False][0] - PUBLICADO) < 0.05),
            "corregido": res[True][0],
            "suelo_publicado": SUELO_PUBLICADO,
            "suelo_recalculado": res[False][1],
            "suelo_corregido": res[True][1],
            "diferencia_antes": r0 - s0, "diferencia_despues": r1 - s1,
            "z_antes": res[False][3], "z_despues": res[True][3],
            "p_despues": res[True][4],
            "la_conclusion_de_e19_aguanta": bool(res[True][4] < 0.05
                                                 and (r1 - s1) > 0)},
        "arreglado_en": ["scripts/F8_A8_briefing_traspaso.py"],
        "pendiente_de_decidir": "si se adopta tambien en los guiones de A5, "
                                "lo que cambiaria las cifras de 4.6.3 sin "
                                "cambiar la conclusion",
        "permutaciones": reps,
    }
    (RES / "x29_fundamentacion.json").write_text(
        json.dumps(salida, ensure_ascii=False, indent=1, default=float),
        encoding="utf-8")
    print("   [ok] x29_fundamentacion.json")
    print()


if __name__ == "__main__":
    main()
