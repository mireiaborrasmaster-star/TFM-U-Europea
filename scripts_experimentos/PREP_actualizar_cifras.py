# -*- coding: utf-8 -*-
"""
PREP_actualizar_cifras.py · que los recuentos del cuaderno cuadren en todas partes
==================================================================================

EL PROBLEMA
    La memoria dice en once sitios distintos cuantos experimentos, hipotesis,
    decisiones y errores tiene el cuaderno de trabajo. Unas veces en cifra
    ("21 experimentos") y otras en letra ("veintiun experimentos").

    Cada vez que se añade un experimento, esos once sitios quedan mal. Y un
    tribunal que encuentre "trece errores" en la pagina 40 y dieciocho en el
    anexo tiene motivos para dudar del resto.

    Contarlos a mano once veces es justo el tipo de tarea donde se cuela el
    fallo que nadie ve hasta la impresion.

QUE HACE
    1. CUENTA de verdad, leyendo 08_BITACORA.md
    2. BUSCA esos recuentos en todos los documentos, en cifra y en letra
    3. LOS CORRIGE

COMO SE EJECUTA
    python scripts/PREP_actualizar_cifras.py             ver que cambiaria
    python scripts/PREP_actualizar_cifras.py --aplicar   escribirlo

    Es idempotente: si ya cuadran, no toca nada y lo dice.
"""

import argparse
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BITACORA = RAIZ / "08_BITACORA.md"

# Documentos donde puede aparecer un recuento
DOCUMENTOS = (sorted((RAIZ / "memoria").glob("*.md"))
              + sorted(RAIZ.glob("*.md"))
              + [RAIZ / "ESTADO.txt"])

LETRAS = {
    10: "diez", 11: "once", 12: "doce", 13: "trece", 14: "catorce",
    15: "quince", 16: "dieciséis", 17: "diecisiete", 18: "dieciocho",
    19: "diecinueve", 20: "veinte", 21: "veintiún", 22: "veintidós",
    23: "veintitrés", 24: "veinticuatro", 25: "veinticinco",
    26: "veintiséis", 27: "veintisiete", 28: "veintiocho",
    29: "veintinueve", 30: "treinta", 31: "treinta y un",
    32: "treinta y dos", 33: "treinta y tres", 34: "treinta y cuatro",
}
# «veintiun» aparece con y sin tilde, y «veintiuna» en femenino
ALIAS = {21: ["veintiún", "veintiun", "veintiuna"]}


def contar():
    t = BITACORA.read_text(encoding="utf-8")
    return {
        "experimentos": len(re.findall(r"^### E\d+ ·", t, re.M)),
        "hipótesis": len(re.findall(r"^\| \*\*H\d+\*\*", t, re.M)),
        "decisiones": len(re.findall(r"^### D\d+ ·", t, re.M)),
        "errores": len(re.findall(r"^\| X\d+ \|", t, re.M)),
        "mediciones": len(re.findall(r"^### M\d+ ·", t, re.M)),
    }


# sustantivo -> las palabras que pueden acompañarlo en el texto
SINONIMOS = {
    "experimentos": ["experimentos"],
    "hipótesis": ["hipótesis"],
    "decisiones": ["decisiones"],
    "errores": ["errores"],
}


def formas(n, palabra):
    """Todas las maneras de escribir «n palabra» que hay que reconocer."""
    out = [str(n)]
    if n in LETRAS:
        out.append(LETRAS[n])
    out += ALIAS.get(n, [])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()

    cuenta = contar()
    print()
    print("=" * 74)
    print("PREP · recuentos del cuaderno" + ("  ·  APLICANDO" if a.aplicar
                                             else "  ·  simulación"))
    print("=" * 74)
    print()
    for k, v in cuenta.items():
        letra = LETRAS.get(v, "")
        print(f"   {k:<16}{v:>4}   {letra}")
    print()

    # Se buscan numeros VIEJOS plausibles (de 10 a 40) seguidos del sustantivo
    # y se sustituyen por el correcto, respetando si estaba en cifra o en letra.
    cambios_total = 0
    for doc in DOCUMENTOS:
        if not doc.exists() or doc.name == "08_BITACORA.md":
            continue
        try:
            texto = doc.read_text(encoding="utf-8")
        except Exception:
            continue
        original = texto
        detalle = []

        for clave, palabras in SINONIMOS.items():
            correcto = cuenta[clave]
            for palabra in palabras:
                # en cifra
                def rep_cifra(m):
                    viejo = int(m.group(1))
                    if viejo == correcto or not (5 <= viejo <= 60):
                        return m.group(0)
                    detalle.append(f"{viejo} {palabra} -> {correcto}")
                    return f"{correcto} {m.group(2)}"
                texto = re.sub(r"\b(\d{1,2})\s+(" + palabra + r")\b",
                               rep_cifra, texto)
                # en letra
                for n, l in LETRAS.items():
                    if n == correcto:
                        continue
                    for forma in [l] + ALIAS.get(n, []):
                        patron = r"\b(" + re.escape(forma) + r")\s+(" + palabra + r")\b"
                        if re.search(patron, texto, re.I):
                            nuevo = LETRAS.get(correcto, str(correcto))
                            texto = re.sub(
                                patron, lambda m: f"{nuevo} {m.group(2)}",
                                texto, flags=re.I)
                            detalle.append(f"{forma} {palabra} -> {nuevo}")

        if texto != original:
            cambios_total += len(detalle)
            print(f"   {doc.relative_to(RAIZ)}")
            for d in sorted(set(detalle)):
                print(f"      · {d}")
            if a.aplicar:
                doc.write_text(texto, encoding="utf-8")

    print()
    if cambios_total == 0:
        print("   Todos los recuentos cuadran.")
    elif a.aplicar:
        print(f"   {cambios_total} corrección(es) escritas.")
    else:
        print(f"   {cambios_total} corrección(es). Relánzalo con --aplicar.")
    print()


if __name__ == "__main__":
    main()
