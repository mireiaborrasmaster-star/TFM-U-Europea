# -*- coding: utf-8 -*-
"""
fig_color.py · comprobar que los colores de las figuras se distinguen
=====================================================================

QUE PROBLEMA RESUELVE
    Entre el 6 y el 8 % de los hombres tiene alguna forma de daltonismo. Si
    dos series de un grafico se distinguen SOLO por el color y ese par es
    justo uno de los que se confunden, esa persona no puede leer la figura.

    El error habitual es decidirlo a ojo. A ojo no se puede: quien no es
    daltonico ve perfectamente la diferencia que el daltonico no ve. Hay que
    CALCULARLO.

COMO SE CALCULA
    1. Se simula como ve cada color una persona con protanopia (no distingue
       el rojo), deuteranopia (no distingue el verde) y tritanopia (no
       distingue el azul). Se usa el metodo de Vienot, Brettel y Mollon
       (1999), que es el estandar.
    2. Se mide la distancia entre los dos colores simulados en el espacio
       OKLab, que esta construido para que una distancia igual se perciba
       como una diferencia igual (cosa que NO ocurre en RGB).
    3. Se exige una distancia minima. Por debajo, los colores se confunden.

    Umbrales usados:
       >= 15   entre colores con vision normal   (si no, nadie los distingue)
       >=  8   en cada tipo de daltonismo

NOTA IMPORTANTE SOBRE ESTE TRABAJO
    En las figuras de esta memoria el color NUNCA es el unico canal: cada
    barra lleva su valor escrito y cada serie su etiqueta. La comprobacion
    es una salvaguarda adicional, no la unica.

    Ademas la memoria puede imprimirse en blanco y negro, asi que tambien se
    comprueba que los colores tengan luminosidades distintas: es lo que
    decide si se distinguen en una fotocopia.

USO
    python scripts/fig_color.py                 comprueba la paleta del TFM
    from fig_color import comprobar             desde otro script
"""

import itertools

# ---------------------------------------------------------------------------
# sRGB  ->  RGB lineal  ->  OKLab
# ---------------------------------------------------------------------------
def _hex_a_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _a_lineal(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _a_srgb(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _oklab(rgb_lineal):
    r, g, b = rgb_lineal
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = [v ** (1 / 3) if v > 0 else -((-v) ** (1 / 3)) for v in (l, m, s)]
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


# ---------------------------------------------------------------------------
# Simulacion del daltonismo · Vienot, Brettel y Mollon (1999)
# ---------------------------------------------------------------------------
_A_LMS = ((0.31399022, 0.63951294, 0.04649755),
          (0.15537241, 0.75789446, 0.08670142),
          (0.01775239, 0.10944209, 0.87256922))
_A_RGB = ((5.47221206, -4.64196010, 0.16963708),
          (-1.12524190, 2.29317094, -0.16789520),
          (0.02980165, -0.19318073, 1.16364789))


def _mul(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def _simular(rgb_lineal, tipo):
    L, M, S = _mul(_A_LMS, rgb_lineal)
    if tipo == "protanopia":
        L = 1.05118294 * M - 0.05116099 * S
    elif tipo == "deuteranopia":
        M = 0.95130920 * L + 0.04866992 * S
    elif tipo == "tritanopia":
        S = -0.86744736 * L + 1.86727089 * M
    return _mul(_A_RGB, (L, M, S))


def _distancia(hex_a, hex_b, tipo=None):
    """Distancia perceptual entre dos colores, en OKLab x 100."""
    out = []
    for h in (hex_a, hex_b):
        lin = tuple(_a_lineal(c) for c in _hex_a_rgb(h))
        if tipo:
            lin = tuple(_a_lineal(_a_srgb(c)) for c in _simular(lin, tipo))
        out.append(_oklab(lin))
    (l1, a1, b1), (l2, a2, b2) = out
    return 100 * ((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2) ** 0.5


def _luminosidad(h):
    """Claridad OKLab, 0 negro y 1 blanco. Es lo que sobrevive a una fotocopia."""
    return _oklab(tuple(_a_lineal(c) for c in _hex_a_rgb(h)))[0]


# ---------------------------------------------------------------------------
# La comprobacion
# ---------------------------------------------------------------------------
MIN_NORMAL = 15.0
MIN_DALTONISMO = 8.0
MIN_LUMINOSIDAD = 0.10       # separacion minima para el blanco y negro

TIPOS = ("protanopia", "deuteranopia", "tritanopia")


def comprobar(paleta, verboso=True):
    """
    paleta: dict {nombre: '#RRGGBB'}
    Devuelve True si todos los pares pasan. Imprime el detalle.
    """
    nombres = list(paleta)
    fallos = []
    if verboso:
        print(f"   {'par de colores':<34}{'normal':>9}{'protan':>9}"
              f"{'deuter':>9}{'tritan':>9}{'b/n':>8}")
        print("   " + "-" * 78)
    for a, b in itertools.combinations(nombres, 2):
        ha, hb = paleta[a], paleta[b]
        d_norm = _distancia(ha, hb)
        d_cvd = {t: _distancia(ha, hb, t) for t in TIPOS}
        d_lum = abs(_luminosidad(ha) - _luminosidad(hb))

        mal = []
        if d_norm < MIN_NORMAL:
            mal.append("normal")
        for t in TIPOS:
            if d_cvd[t] < MIN_DALTONISMO:
                mal.append(t[:6])
        if d_lum < MIN_LUMINOSIDAD:
            mal.append("b/n")
        if mal:
            fallos.append((a, b, mal))

        if verboso:
            marca = "  <-- " + ", ".join(mal) if mal else ""
            print(f"   {a + ' / ' + b:<34}{d_norm:>9.1f}"
                  f"{d_cvd['protanopia']:>9.1f}{d_cvd['deuteranopia']:>9.1f}"
                  f"{d_cvd['tritanopia']:>9.1f}{d_lum:>8.2f}{marca}")

    if verboso:
        print()
        if fallos:
            print(f"   {len(fallos)} par(es) por debajo del umbral.")
            print("   Recordatorio: en estas figuras el color no es el unico")
            print("   canal (cada barra lleva su valor escrito), asi que un par")
            print("   flojo no invalida la figura, pero conviene separarlo.")
        else:
            print("   Todos los pares se distinguen con vision normal, con los")
            print("   tres tipos de daltonismo y en blanco y negro.")
    return not fallos


# La paleta de datos de las figuras de resultados
PALETA_DATOS = {
    "verde (lo construido)":   "#1F6F6B",
    "verde claro (variante)":  "#5AA39C",
    "azul (referencia)":       "#3D5A80",
    "terracota (problema)":    "#B4543A",
    "gris (suelo o control)":  "#B9C1C2",
}

if __name__ == "__main__":
    print("\nfig_color.py · comprobacion de la paleta de las figuras")
    print("=" * 82)
    comprobar(PALETA_DATOS)
    print()
