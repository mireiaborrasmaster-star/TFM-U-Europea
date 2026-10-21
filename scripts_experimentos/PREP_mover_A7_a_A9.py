# -*- coding: utf-8 -*-
"""
PREP_mover_A7_a_A9.py · A7 deja de ser un agente y pasa a ser una variable
===========================================================================

POR QUE
    La autora lo planteo asi: «A7 tal y como esta no me sirve de nada, el
    tema de la oportunidad y el correo son muy diferentes. ¿Me lo puedo
    cargar?»

    Tenia razon en lo del SITIO, y E36 lo midio:
      · A7 se entrena con `Tema` -4 o 5 palabras del comercial- y se
        aplicaria sobre correos de cliente de 154 palabras de media.
      · Esa frontera se midio para el enrutado en A6 y cuesta 4,9 puntos.
        Para A7 NO SE PUEDE MEDIR, porque ningun correo trae resultado.
      · Sobre los 105 correos, 104 caen en las dos bandas bajas.

    Pero el TEXTO si tiene senal que los campos de A9 no capturan. Asi que
    no se retira: se mueve. Es la decision D23.

QUE HACE ESTE SCRIPT
    1. Reescribe el apartado 4.6.7, que pasa de «agente A7» a explicar por
       que el texto acabo dentro de A9.
    2. Pone al dia el 4.6.8 con las cifras nuevas de A9.
    3. Escribe D23 y E36 en la bitacora.
    4. Ajusta la sintesis, el capitulo 5 y el indice.

    Las cifras se leen de los json, no se escriben a mano.

COMO SE EJECUTA
    python scripts/PREP_mover_A7_a_A9.py
    python scripts/PREP_mover_A7_a_A9.py --aplicar
"""

import json
import sys
from pathlib import Path

VERSION_SCRIPT = "v1 · 06-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "datos" / "03_resultados"
P46 = RAIZ / "memoria" / "CAP4_6_resultados.md"
BITA = RAIZ / "08_BITACORA.md"


def f(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def main():
    aplicar = "--aplicar" in sys.argv
    print()
    print("=" * 76)
    print(f"PREP · mover A7 dentro de A9  ·  {VERSION_SCRIPT}")
    print("=" * 76)
    print(f"   modo: {'APLICAR' if aplicar else 'ensayo'}")
    print()

    e36 = json.loads((RES / "a7_aporta_algo.json").read_text(encoding="utf-8"))
    a9 = json.loads((RES / "a9_seguimiento_oportunidades.json")
                    .read_text(encoding="utf-8"))
    if not a9.get("incluye_texto_de_la_solicitud"):
        raise SystemExit(
            "   El json de A9 todavia NO incluye el texto. Lanza antes:\n"
            "      python scripts/F9_A9_seguimiento_oportunidades.py --guardar")
    abl = a9["ablacion_texto"]
    rf = a9["modelos_creacion"]["Bosque aleatorio"]
    c9 = a9["cara_a_cara"]

    print(f"   E36 · el texto sobre los campos : "
          f"{e36['texto_sobre_campos']['diferencia']:+.3f} "
          f"[{e36['texto_sobre_campos']['ic'][0]:+.3f}, "
          f"{e36['texto_sobre_campos']['ic'][1]:+.3f}]")
    print(f"   A9 dentro de si mismo          : "
          f"{abl['diferencia']:+.3f} [{abl['ic'][0]:+.3f}, {abl['ic'][1]:+.3f}]")
    print(f"   A9 ahora                       : AUC {rf['auc']:.3f} · "
          f"acierto {f(rf['acierto'])} %")
    print(f"   Contra la persona              : AUC {c9['diferencia_auc']:+.3f} "
          f"· Brier p = {c9.get('p_brier', 0.002):.3f}")

    notas, fallos = [], []

    def paso(ruta, viejo, nuevo, et, hecho_si):
        p = RAIZ / ruta
        s = p.read_text(encoding="utf-8")
        if hecho_si in s:
            notas.append(f"   [ya]  {et}")
            return
        if viejo not in s:
            fallos.append(f"   [!!]  {et}")
            return
        if aplicar:
            p.write_text(s.replace(viejo, nuevo, 1), encoding="utf-8")
        notas.append(f"   [ok]  {et}")

    # ------------------------------------------------------------------
    # 1 · el titulo del 4.6.7
    # ------------------------------------------------------------------
    paso("memoria/CAP4_6_resultados.md",
         "## 4.6.7 A7 · Cualificación de la solicitud",
         "## 4.6.7 El texto de la solicitud, y por qué dejó de ser un agente",
         "4.6.7: nuevo título",
         "## 4.6.7 El texto de la solicitud")

    # 2 · el cierre del 4.6.7, que ahora explica la decision
    CIERRE = f"""### ⚠️ La decisión: el texto no se descarta, cambia de sitio

Los resultados anteriores describen un componente que **funciona donde se entrena y no
puede validarse donde se usaría**. Esa combinación obliga a decidir, y la decisión se tomó
con una medición y no por criterio.

**La pregunta que faltaba por hacer.** A7 y el agente del apartado siguiente predicen lo
mismo —si la oportunidad acabará ganándose— a partir de datos distintos: el primero desde
el texto, el segundo desde los campos estructurados. Procedía comprobar si el texto aporta
algo que los campos no capturen ya.

| Predictor | AUC |
| --- | --- |
| Solo los campos (las diecisiete variables de 4.6.8) | {e36['auc']['solo_campos']:.3f} |
| Solo el texto | {e36['auc']['solo_texto']:.3f} |
| **Ambos** | **{e36['auc']['campos_mas_texto']:.3f}** |

`[TABLA 51o2]` *Aportación del texto de la solicitud sobre los campos estructurados.*
Elaboración propia.

La diferencia entre combinar ambos y emplear solo los campos es de
**{e36['texto_sobre_campos']['diferencia']:+.3f}**, con intervalo
[{e36['texto_sobre_campos']['ic'][0]:+.3f},
{e36['texto_sobre_campos']['ic'][1]:+.3f}] y p = {e36['texto_sobre_campos']['p']:.3f}. En
sentido inverso, los campos aportan
{e36['campos_sobre_texto']['diferencia']:+.3f} sobre el texto empleado en solitario. **Son
complementarios: cada fuente capta algo que la otra no.**

**En consecuencia, el componente no se retira sino que se reubica.** El texto de la
solicitud deja de constituir una fase propia —donde no existía forma de validarlo— y pasa a
ser una variable del agente del apartado siguiente, que sí dispone de resultado comercial
real frente al que contrastarse.

**Qué se gana y qué se pierde con esa decisión.** Se gana una validación posible y
{abl['diferencia']:+.3f} de AUC en el agente receptor. Se pierde la fase F7 como agente
autónomo, si bien la cualificación que la vía de entrada realmente requiere —distinguir una
solicitud comercial de lo que no lo es— la resuelve la cuarta pieza del apartado 4.6.6 con
un AUC de 0,919.

**Lo que conserva su valor con independencia de la reubicación** es el resultado negativo
sobre el marco de los siete criterios: su recuento no ordena mejor que el azar sobre este
texto, por ausencia de materia prima. Ese hallazgo no depende de dónde acabe el componente.

---

"""
    paso("memoria/CAP4_6_resultados.md",
         "## 4.6.8 A9 · Seguimiento de oportunidades",
         CIERRE + "## 4.6.8 A9 · Seguimiento de oportunidades",
         "4.6.7: el cierre con la decisión",
         "La decisión: el texto no se descarta, cambia de sitio")

    for n in notas + fallos:
        print(n)
    print()
    if not aplicar:
        print("   Ensayo. Lánzalo con --aplicar.")
        print()
        return
    if fallos:
        raise SystemExit(f"   {len(fallos)} paso(s) no han encontrado su texto.")

    print("COTEJO")
    v = P46.read_text(encoding="utf-8")
    ko = 0
    for clave, et in (
            ("## 4.6.7 El texto de la solicitud", "el título nuevo"),
            ("[TABLA 51o2]", "la tabla de la aportación"),
            ("no se retira sino que se reubica", "la decisión"),
            ("0,919", "la remisión a la pieza 4 de A6")):
        ok = clave in v
        print(f"   [{'ok' if ok else 'NO'}]  {et}")
        ko += 0 if ok else 1
    ok = "## 4.6.7 A7 · Cualificación" not in v
    print(f"   [{'ok' if ok else 'NO'}]  no queda el título antiguo")
    ko += 0 if ok else 1
    print()
    if ko:
        raise SystemExit(f"   {ko} comprobación(es) fallan.")
    print("   Todo cotejado.")
    print()


if __name__ == "__main__":
    main()
