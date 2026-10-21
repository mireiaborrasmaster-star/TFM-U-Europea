# -*- coding: utf-8 -*-
"""
COTEJAR_desfases.py · busca en la memoria lo que ya no es verdad
=================================================================

PARA QUE SIRVE
    Un documento largo que se escribe durante tres semanas acumula frases
    que eran ciertas cuando se escribieron y dejaron de serlo despues. No
    dan error, no las detecta ningun corrector, y son lo peor que puede
    encontrar un tribunal: el trabajo contradiciendose a si mismo.

    Ya ha pasado tres veces en este proyecto:
      · el capitulo 5 dijo durante tres dias que el orquestador no se
        habia construido (error X22)
      · el 4.6.9 decia «A6 produjo resultados pese a no construirse» y
        «A9 no se construyo por alcance» cuando los dos estaban hechos
      · la ficha de A6 publicaba un 75,6 % que X28 habia corregido a 79,5

    Este guion busca esas frases. No adivina: comprueba una lista de
    afirmaciones que HOY son falsas, y contrasta las cifras publicadas
    contra los ficheros de resultados que las generan.

COMO SE LEE LA SALIDA
    [!!] es una frase que no deberia aparecer. Hay que ir a verla.
    [ok] es que no esta.
    Las cifras se comprueban una a una contra su JSON.

HAY QUE AMPLIARLO
    Cada vez que una cifra cambie o un agente cambie de estado, se anade
    aqui la frase vieja. Cuesta treinta segundos y evita el proximo X22.

COMO SE EJECUTA
    python scripts/COTEJAR_desfases.py
"""

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MEM = RAIZ / "memoria"
RES = RAIZ / "datos" / "03_resultados"

# ---------------------------------------------------------------------------
# 1 · Frases que HOY son falsas. Cada una con el motivo, para que quien lea
#     el aviso sepa por que lo es sin tener que preguntar.
# ---------------------------------------------------------------------------
PROHIBIDAS = [
    ("A6 produjo resultados pese a no construirse",
     "A6 se construyo el 04-10 (E33)"),
    ("No se construyó por alcance, no por falta de datos",
     "era la nota de A9/A8, que se construyo el 04-10 (E32)"),
    ("el sistema secuencial no se construyó",
     "el orquestador se construyo el 30-09 (E28), error X22"),
    ("A7 es el caso más instructivo de los seis",
     "A7 ya no es un agente: D23 lo convirtio en variable y D24 renumero"),
    ("Construir A7 habría exigido generar conversaciones",
     "redactado con la numeracion anterior a D24"),
    ("75,6 %", "X28 corrigio el enrutado sobre correo real a 79,5 %"),
    ("de los once agentes", "son diez desde D24: A6 cubre dos fases"),
    ("siete se construyeron", "son seis: A2, A3, A5, A6, A7 y A8"),
    ("cuatro agentes construidos —A2, A3, A5 y A8—",
     "numeracion anterior a D24"),
    ("A9 y A10", "desde D24 son A8 y A9"),
    # «| A10 |» aparece legitimamente en la tabla de correspondencia de
    # 4.6.0, que es justo la que traduce la numeracion vieja a la nueva.
    # Se busca solo fuera de esa tabla.
    ("| A10 · ", "desde D24 el aprendizaje continuo es A9"),
    ("ampliación a cincuenta y dos correos\nconvirtió", "el corpus son 105"),
    ("52 mensajes reales", "el corpus son 105 desde el 04-10"),
    ("no se ha medido en este trabajo, y el apartado 7.4",
     "E39 lo midio el 07-10"),
    ("el briefing no existe", "se construyo el 06-10 (E37)"),
    ("de los que solo se diseñaron", "revisar: pudo quedar obsoleto"),
]

# ---------------------------------------------------------------------------
# 2 · Cifras publicadas que deben coincidir con su fichero de resultados.
#     (fichero json, ruta dentro del json, como se escribe, donde debe estar)
# ---------------------------------------------------------------------------
def coma(v, n=1):
    return f"{v:.{n}f}".replace(".", ",")


def cifras():
    def j(n):
        p = RES / n
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    b, m, sh, ci = (j("a8_briefing.json"), j("a8_tema_modelo.json"),
                    j("a9_sin_historial.json"), j("a0_circuito_recepcion.json"))
    out = []
    if b:
        out += [("cobertura del tipo de servicio",
                 f"{b['cobertura']['tipo_servicio']} de 105", "CAP4_6"),
                ("asunto propuesto",
                 f"{b['cobertura']['tema_propuesto']} de 105", "CAP4_6")]
    if m:
        out += [("acierto del clasificador de tipo",
                 coma(m["modelo"]["acierto_global"]) + " %", "CAP4_6"),
                ("el diccionario al que sustituye",
                 coma(m["diccionario"]["acierto_global"]) + " %", "CAP4_6"),
                ("caida con el correo entero",
                 coma(m["correo_fabricado"]["modelo_sobre_el_correo_entero"]) + " %",
                 "CAP4_6")]
    if sh:
        por = {r["grupo"]: r for r in sh["resultados"]}
        out += [("AUC sin historial",
                 f"{por['SIN historial']['auc']:.3f}".replace(".", ","), "CAP4_6")]
    if ci:
        out += [("oportunidades creadas por el circuito",
                 f"{ci['destinos']['oportunidad creada']} de 105", "CAP4_6"),
                ("area sobre el telegrama",
                 coma(ci["area"]["acierto_telegrama"]) + " %", "CAP4_6"),
                ("AUC de la pieza de solicitud",
                 f"{ci['clasificador_no_comercial']['auc']:.3f}".replace(".", ","),
                 "CAP4_6")]
    # X31 y X32: el suelo del enrutado es de SU poblacion (41 mensajes reales),
    # no el de la poblacion de entrenamiento. Se vigila para que no se vuelva
    # a mezclar ni a transcribir mal.
    ar = j("a6_agente_recepcion.json")
    if ar:
        e3 = ar["pieza3_enrutado"]
        out += [("enrutado sobre correo real", coma(e3["acierto_correo_real"]) + " %",
                 "CAP4_6"),
                ("su suelo, el de esa misma poblacion", coma(e3["suelo"]) + " %",
                 "CAP4_6"),
                ("margen sobre el suelo", coma(e3["margen_sobre_suelo"]), "CAP4_6")]
    return out


def main():
    print()
    print("#" * 76)
    print("# COTEJAR · lo que ya no es verdad y sigue escrito")
    print("#" * 76)

    ficheros = sorted(MEM.glob("CAP*.md"))
    textos = {f: f.read_text(encoding="utf-8") for f in ficheros}
    fallos = 0

    print()
    print("=" * 76)
    print("1 · FRASES QUE HOY SON FALSAS")
    print("=" * 76)
    for frase, motivo in PROHIBIDAS:
        donde = []
        for f, s in textos.items():
            for i, l in enumerate(s.split("\n"), 1):
                if frase in l:
                    donde.append(f"{f.name}:{i}")
        if donde:
            print(f"   [!!]  «{frase[:52]}»")
            print(f"         {motivo}")
            for d in donde[:4]:
                print(f"         -> {d}")
            fallos += len(donde)
        else:
            print(f"   [ok]  «{frase[:52]}»")

    print()
    print("=" * 76)
    print("2 · CIFRAS PUBLICADAS FRENTE A SU FICHERO DE RESULTADOS")
    print("=" * 76)
    todo = "\n".join(textos.values())
    for et, valor, _ in cifras():
        ok = valor in todo
        print(f"   [{'ok' if ok else '!!'}]  {et:<42}{valor}")
        fallos += 0 if ok else 1

    print()
    print("=" * 76)
    print("3 · REFERENCIAS RELATIVAS, QUE EL REORDENADO ROMPE")
    print("=" * 76)
    rel = 0
    for f, s in textos.items():
        for i, l in enumerate(s.split("\n"), 1):
            if re.search(r"apartado (siguiente|anterior)", l):
                print(f"   [i ]  {f.name}:{i}  {l.strip()[:62]}")
                rel += 1
    if not rel:
        print("   [ok]  ninguna")
    else:
        print()
        print("   No son errores: hay que mirarlas a mano cada vez que se")
        print("   reordenan apartados.")

    print()
    print("=" * 76)
    print(f"   {'TODO CUADRA' if not fallos else f'{fallos} COSAS QUE MIRAR'}")
    print("=" * 76)
    print()
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
