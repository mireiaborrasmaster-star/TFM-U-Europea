# -*- coding: utf-8 -*-
"""
fig_comun.py · utilidades compartidas para dibujar las figuras de la memoria
===========================================================================

QUE ES ESTO
    Un modulo de apoyo. No genera ninguna figura por si solo: lo importan
    los tres scripts que si las generan.

        FIG_arquitectura.py      figuras 1-3   (mapa, taxonomias, despliegue)
        FIG_fichas_agentes.py    figuras 4-8   (una ficha por agente)
        FIG_resultados.py        figuras 9-14  (los datos medidos)

POR QUE MILIMETROS Y NO PIXELES
    Todas las coordenadas de estos scripts estan en MILIMETROS del papel.
    La figura se crea con el tamano fisico que va a tener impresa, asi que
    un texto declarado a 8 puntos mide 8 puntos de verdad en la memoria,
    siempre que en Word se inserte al 100 %. Esto evita el problema habitual
    de figuras con letra ilegible o desproporcionada respecto al cuerpo.

    ANCHO = 160 mm es el ancho util de una A4 con los margenes de la
    plantilla de la UEM.

QUE DEVUELVE
    Cada figura se guarda DOS veces en la carpeta figuras/:
        .png  a 300 ppp, para pegar en Word sin complicaciones
        .svg  vectorial, por si hay que retocar algo o imprimir en grande

NORMA DE COLOR
    La memoria puede acabar impresa en blanco y negro. Por eso el estado de
    cada agente no se distingue SOLO por color: cada caja lleva ademas su
    etiqueta escrita ("construido", "solo diseñado"...). El color ayuda, no
    es el unico canal de informacion.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

RAIZ = Path(__file__).resolve().parent.parent
FIGURAS = RAIZ / "figuras"
FIGURAS.mkdir(exist_ok=True)

ANCHO = 160.0          # mm utiles de una A4 con los margenes de la plantilla
MM = 1 / 25.4          # factor milimetro -> pulgada
MARGEN = 5.0           # mm de aire alrededor del dibujo, ver lienzo()

# ---------------------------------------------------------------------------
# LA NUMERACION DE LAS FIGURAS
# ---------------------------------------------------------------------------
# Un unico sitio donde esta escrito que numero lleva cada figura. Los scripts
# no escriben numeros: piden la figura por su NOMBRE y el numero sale de aqui.
#
# Por que asi: si mañana hay que insertar una figura nueva en el capitulo 4,
# cambian todos los numeros posteriores. Con esta tabla es UN cambio; sin ella
# habria que perseguir el numero por tres scripts y por los ficheros de la
# memoria.
#
# El orden es el de aparicion en la memoria.
NUMEROS = {
    # capitulo 2 · antecedentes
    "embudo_sdr":               1,
    "concepto_multiagente":     2,
    # apartado 4.1 · planificacion
    "ciclo_iterativo":          3,
    "gantt":                    4,
    # apartado 4.2 · solucion
    "mapa_fases_agentes":       5,
    "recorrido_operativo":      6,
    "dos_taxonomias":           7,
    # apartado 4.6 · resultados
    "ficha_A2":                 8,
    "comparativa_A2":           9,
    "ficha_A3":                10,
    "deciles_conversion":      11,
    "arboles_vs_redes":        12,
    "ficha_A5":                13,
    "personalizacion":         14,
    "cuarenta_generaciones":   15,
    "ficha_A7":                16,
    # apartado 4.6.4 · el orquestador
    "encadenamiento":          17,
    "embudo_orquestador":      18,
    # apartado 4.6.9 · agentes disenados
    "ficha_A6":                19,
    "ficha_A8":                20,
    "agentes_disenados":       21,
    # capitulo 7 · futuras lineas
    "despliegue_dos_circuitos": 22,
}


def numero(clave):
    if clave not in NUMEROS:
        raise KeyError(f"figura sin numero asignado: {clave!r}. "
                       f"Anadela a NUMEROS en fig_comun.py")
    return NUMEROS[clave]


# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------
TINTA = "#23282B"      # texto principal
SUAVE = "#6B7477"      # texto secundario
LINEA = "#9AA3A6"      # bordes y flechas

VERDE = "#1F6F6B"      # construido y medido
VERDE_CL = "#5AA39C"   # construido en version simple
GRIS_CL = "#ECEFEF"    # solo disenado
BLANCO = "#FFFFFF"     # no se automatiza
ACENTO = "#B4543A"     # para destacar una cifra o un aviso
AZUL = "#3D5A80"       # segundo color de datos

ESTILOS = {
    # nombre        relleno    texto   borde     etiqueta de estado
    "construido":  (VERDE,    "white", VERDE,    "construido y medido"),
    "simple":      (VERDE_CL, "white", VERDE_CL, "construido, versión simple"),
    "disenado":    (GRIS_CL,  TINTA,   LINEA,    "solo diseñado"),
    "manual":      (BLANCO,   TINTA,   LINEA,    "decisión humana"),
    "neutro":      ("#F4F6F6", TINTA,  LINEA,    ""),
    "destacado":   ("#FBEDE8", TINTA,  ACENTO,   ""),
}


# ---------------------------------------------------------------------------
# Lienzo
# ---------------------------------------------------------------------------
def lienzo(alto_mm, ancho_mm=ANCHO, margen_mm=MARGEN):
    """Crea una figura del tamano fisico indicado, con ejes en milimetros.

    EL MARGEN, QUE ANTES NO ESTABA. El dibujo ocupaba el lienzo entero, de
    borde a borde: el titulo nacia en la esquina, las cajas llegaban al
    filo del papel y la leyenda quedaba pegada abajo. Se veia apretado.

    Se arregla agrandando el LIENZO y metiendo el dibujo dentro, no
    encogiendo el dibujo. El sistema de coordenadas sigue yendo de 0 a
    `ancho_mm`, de modo que ningun guion de figuras cambia ni una linea:
    lo unico que cambia es que alrededor queda aire.
    """
    w, h = ancho_mm + 2 * margen_mm, alto_mm + 2 * margen_mm
    fig = plt.figure(figsize=(w * MM, h * MM))
    ax = fig.add_axes([margen_mm / w, margen_mm / h, ancho_mm / w, alto_mm / h])
    ax.set_xlim(0, ancho_mm)
    ax.set_ylim(0, alto_mm)
    ax.invert_yaxis()          # y crece hacia abajo: se dibuja como se lee
    ax.axis("off")
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    return fig, ax


def guardar(fig, clave):
    """Guarda la figura en png (300 ppp) y svg. El nombre lleva su numero."""
    nombre = f"fig{numero(clave):02d}_{clave}"
    for ext in ("png", "svg"):
        fig.savefig(FIGURAS / f"{nombre}.{ext}", dpi=300,
                    facecolor="white", bbox_inches=None)
    plt.close(fig)
    print(f"   [ok] figuras/{nombre}.png  +  .svg")


# ---------------------------------------------------------------------------
# Piezas de dibujo
# ---------------------------------------------------------------------------
def caja(ax, x, y, w, h, estilo="neutro", radio=1.2, lw=0.8, discontinua=False):
    """Rectangulo de esquinas redondeadas. (x, y) es la esquina superior izq."""
    relleno, _, borde, _ = ESTILOS[estilo]
    p = FancyBboxPatch(
        (x + radio, y + radio), w - 2 * radio, h - 2 * radio,
        boxstyle=f"round,pad={radio}", linewidth=lw,
        facecolor=relleno, edgecolor=borde,
        linestyle=(0, (2.5, 1.5)) if discontinua else "solid", zorder=2)
    ax.add_patch(p)
    return p


def texto(ax, x, y, t, tam=7, peso="normal", color=None, ha="left", va="center",
          cursiva=False, familia=None):
    ax.text(x, y, t, fontsize=tam, fontweight=peso,
            color=color if color else TINTA, ha=ha, va=va,
            style="italic" if cursiva else "normal",
            family=familia, zorder=4)


def flecha(ax, x1, y1, x2, y2, color=None, lw=0.9, punta=4.0, discontinua=False):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle=f"-|>,head_width={punta/12:.2f},"
        f"head_length={punta/8:.2f}",
        mutation_scale=10, linewidth=lw,
        linestyle=(0, (2.5, 1.5)) if discontinua else "solid",
        color=color if color else LINEA, zorder=1,
        shrinkA=0, shrinkB=0))


def titulo_figura(ax, clave, titulo, subtitulo=None, y=4.5, ancho_mm=ANCHO):
    """Cabecera dentro del propio dibujo. El pie de figura va en Word.

    El subtitulo SE PARTE SOLO si no cabe. Antes no: al alargar el de la
    figura 5 para explicar lo de los diez agentes, la frase se salia por
    la derecha y se perdia el final. Partirlo aqui evita tener que medir a
    ojo cada vez que se cambia un texto.
    """
    texto(ax, 0, y, f"Figura {numero(clave)}", tam=7.5, peso="bold", color=ACENTO)
    texto(ax, 0, y + 5.4, titulo, tam=9.5, peso="bold")
    if not subtitulo:
        return y + 11.0
    # a tamano 7, un caracter ocupa ~1,52 mm: de ahi salen los caracteres
    # por linea que caben en el ancho disponible
    import textwrap
    lineas = textwrap.wrap(subtitulo, width=max(20, int(ancho_mm / 1.52)))
    for i, l in enumerate(lineas):
        texto(ax, 0, y + 11.0 + i * 4.0, l, tam=7, color=SUAVE)
    return y + 16.5 + (len(lineas) - 1) * 4.0


def leyenda_estados(ax, x, y, estados, ancho_item=None):
    """Fila de cuadraditos con el significado de cada color."""
    ancho_item = ancho_item or (ANCHO / len(estados))
    for i, e in enumerate(estados):
        relleno, _, borde, etiq = ESTILOS[e]
        cx = x + i * ancho_item
        ax.add_patch(Rectangle((cx, y - 1.6), 3.2, 3.2, facecolor=relleno,
                               edgecolor=borde, linewidth=0.8, zorder=3))
        texto(ax, cx + 4.6, y, etiq, tam=6.2, color=SUAVE)


# ---------------------------------------------------------------------------
# La tira de las 11 fases
# ---------------------------------------------------------------------------
FASES = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"]

NOMBRE_FASE = {
    "F0": "definir a quien\nbuscamos",
    "F1": "buscar\nempresas",
    "F2": "enriquecer\ndatos",
    "F3": "puntuar y\npriorizar",
    "F4": "encontrar a\nla persona",
    "F5": "contactar",
    "F6": "atender lo\nque entra",
    "F7": "cualificar",
    "F8": "pasar al\ntecnico",
    "F9": "seguir la\noportunidad",
    "F10": "aprender y\najustar",
}

ESTADO_FASE = {
    "F0": "manual", "F1": "disenado", "F2": "construido", "F3": "construido",
    "F4": "disenado", "F5": "simple", "F6": "disenado", "F7": "disenado",
    "F8": "disenado", "F9": "disenado", "F10": "disenado",
}


def tira_fases(ax, x, y, activa, ancho=ANCHO, alto=11.0, con_nombres=True,
               estilo_activa="construido"):
    """
    Dibuja las 11 fases en una tira horizontal y resalta la fase 'activa'.

    Es la pieza que contextualiza cada ficha de agente: al verla, el lector
    sabe en que punto del proceso comercial actua ese agente sin tener que
    volver al mapa general.
    """
    hueco = 1.4
    w = (ancho - hueco * (len(FASES) - 1)) / len(FASES)
    for i, f in enumerate(FASES):
        cx = x + i * (w + hueco)
        es_activa = (f == activa)
        if es_activa:
            caja(ax, cx, y, w, alto, estilo_activa, radio=0.8, lw=1.2)
            col = ESTILOS[estilo_activa][1]
        else:
            caja(ax, cx, y, w, alto, "neutro", radio=0.8, lw=0.6)
            col = "#A8B0B2"
        texto(ax, cx + w / 2, y + 3.6, f, tam=7 if es_activa else 6.2,
              peso="bold" if es_activa else "normal", color=col, ha="center")
        if con_nombres:
            ax.text(cx + w / 2, y + 7.6, NOMBRE_FASE[f], fontsize=4.6,
                    color=col, ha="center", va="center", linespacing=1.15,
                    zorder=4)
    return y + alto
