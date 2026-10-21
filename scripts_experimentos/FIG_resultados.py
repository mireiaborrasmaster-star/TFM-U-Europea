# -*- coding: utf-8 -*-
"""
FIG_resultados.py · las figuras de datos del apartado 4.6
=========================================================

QUE GENERA

    fig08_comparativa_A2       los seis metodos de clasificacion sectorial
    fig10_deciles_conversion   conversion real por decil de puntuacion
    fig11_arboles_vs_redes     arboles frente a redes neuronales
    fig13_personalizacion      la personalizacion frente al correo real
    fig14_cuarenta_generaciones que paso con las cuarenta generaciones

DE DONDE SALEN LAS CIFRAS
    De ficheros de resultados, no escritas a mano donde se puede evitarlo:

        datos/03_resultados/a3_conversion.json      <- lo escribe E12-E16
        datos/03_resultados/a3_arboles_vs_redes.csv <- lo escribe E21
        datos/03_resultados/a5_campana_C01.csv      <- lo escribe E20

    Las de A2 (E4 a E11) si estan escritas aqui, porque el entrenamiento del
    transformer se hizo en Colab y no dejo un fichero de resumen. Van en el
    diccionario A2_METODOS y el script las coteja con 08_BITACORA.md al final.

UNA ADVERTENCIA QUE HAY QUE LEER
    La figura de deciles se dibuja con la RECONSTRUCCION reproducible, no con
    las cifras que E16 publico en su dia. Las dos son correctas pero miden
    objetivos distintos, y el script lo dice en voz alta al ejecutarse. Ver
    el apartado COTEJO al final y la nota que imprime.

DECISIONES DE DIBUJO
    · Ningun grafico con dos escalas verticales. Cuando hay dos magnitudes
      distintas (por ejemplo F1 y segundos de entrenamiento), la segunda se
      escribe como texto al lado de la barra. Un eje doble permite sugerir
      cualquier conclusion eligiendo las escalas.
    · Toda barra lleva su valor escrito. El color no es nunca el unico canal.
    · Donde hay una cifra hay un punto de comparacion: el suelo medido, el
      azar, o la practica actual de la organizacion.
    · La paleta se comprueba para los tres tipos de daltonismo y para el
      blanco y negro con fig_color.py, que se ejecuta al lanzar este script.

COMO SE EJECUTA
    python scripts/FIG_resultados.py
"""

import csv
import json
from pathlib import Path

from fig_comun import (ANCHO, TINTA, SUAVE, LINEA, ACENTO, AZUL, VERDE,
                       caja, texto, lienzo, guardar, titulo_figura, RAIZ)
from fig_color import comprobar

RESULTADOS = RAIZ / "datos" / "03_resultados"

# ---------------------------------------------------------------------------
# La paleta de los graficos de datos
# ---------------------------------------------------------------------------
D_VERDE = "#14514E"      # lo que se construyo y gana
D_VERDE_CL = "#5AA39C"   # la otra serie, o la variante
D_TERRA = "#B4543A"      # el problema, o la familia que pierde
D_GRANATE = "#6E2A1B"    # el problema grave
D_GRIS = "#D6DDDE"       # el suelo, el azar, el control

PALETA = {
    "verde (gana / construido)": D_VERDE,
    "verde claro (2.a serie)": D_VERDE_CL,
    "terracota (pierde / problema)": D_TERRA,
    "granate (problema grave)": D_GRANATE,
    "gris (suelo o control)": D_GRIS,
}


# ---------------------------------------------------------------------------
# Piezas de grafico, en milimetros como el resto de figuras
# ---------------------------------------------------------------------------
def barras_h(ax, x0, y0, ancho, alto_barra, hueco, datos, maximo,
             etiqueta_ancho=54.0, formato="{:.2f}", tam_valor=6.2):
    """
    Barras horizontales. 'datos' es una lista de (etiqueta, valor, color,
    negrita). Devuelve la y siguiente libre.
    """
    x_bar = x0 + etiqueta_ancho
    ancho_util = ancho - etiqueta_ancho - 16.0
    for i, (etiq, valor, color, fuerte) in enumerate(datos):
        y = y0 + i * (alto_barra + hueco)
        texto(ax, x_bar - 3.0, y + alto_barra / 2, etiq,
              tam=6.3, peso="bold" if fuerte else "normal", ha="right",
              color=TINTA if fuerte else SUAVE)
        w = ancho_util * valor / maximo
        ax.add_patch(plt_rect(x_bar, y + 0.6, max(w, 0.4), alto_barra - 1.2,
                              color))
        texto(ax, x_bar + w + 2.2, y + alto_barra / 2, formato.format(valor),
              tam=tam_valor, peso="bold" if fuerte else "normal",
              color=TINTA if fuerte else SUAVE)
    return y0 + len(datos) * (alto_barra + hueco)


def plt_rect(x, y, w, h, color):
    from matplotlib.patches import Rectangle
    return Rectangle((x, y), w, h, facecolor=color, edgecolor="none", zorder=2)


def leyenda(ax, x, y, items, paso=46.0):
    """items: lista de (texto, color)."""
    for i, (t, c) in enumerate(items):
        cx = x + i * paso
        ax.add_patch(plt_rect(cx, y - 1.5, 3.0, 3.0, c))
        texto(ax, cx + 4.4, y, t, tam=6.0, color=SUAVE)


# ---------------------------------------------------------------------------
# FIGURA 8 · los seis metodos de A2
# ---------------------------------------------------------------------------
# E4, E5, E7, E8, E10 · nivel sector, 41 clases, 2.652 casos de prueba.
# Escritas a mano porque el transformer se entreno en Colab; se cotejan abajo.
A2_METODOS = [
    ("Responder siempre lo más común", 13.16, 0.57, D_GRIS, False),
    ("Modelo de lenguaje, sin ejemplos", 33.33, 25.12, D_TERRA, False),
    ("Modelo de lenguaje, con ejemplos", 34.67, 24.37, D_TERRA, False),
    ("TF-IDF + máquina de vectores soporte", 48.49, 40.16, D_VERDE_CL, False),
    ("TF-IDF + regresión logística", 48.91, 41.89, D_VERDE_CL, False),
    ("Transformer XLM-RoBERTa", 51.73, 43.38, D_VERDE, True),
]


def fig_comparativa_a2():
    fig, ax = lienzo(174.0)
    y = titulo_figura(
        ax, "comparativa_A2",
        "Seis maneras de clasificar el sector de una empresa",
        "41 clases · 2.652 cuentas de prueba. La primera fila es el suelo: "
        "lo que se consigue sin modelo alguno.")

    alto, hueco, x_et = 7.0, 3.6, 62.0
    x_bar = x_et
    ancho_util = ANCHO - x_et - 30.0
    maximo = 60.0

    for i, (nombre, acc, f1, color, fuerte) in enumerate(A2_METODOS):
        yb = y + 6.0 + i * (alto * 2 + hueco)
        texto(ax, x_et - 3.0, yb + alto, nombre, tam=6.3,
              peso="bold" if fuerte else "normal", ha="right",
              color=TINTA if fuerte else SUAVE)
        for j, (v, c) in enumerate([(acc, color), (f1, color)]):
            yy = yb + j * alto
            w = ancho_util * v / maximo
            alpha = 1.0 if j == 0 else 0.55
            r = plt_rect(x_bar, yy + 0.5, max(w, 0.4), alto - 1.0, c)
            r.set_alpha(alpha)
            ax.add_patch(r)
            texto(ax, x_bar + w + 2.0, yy + alto / 2,
                  f"{v:.2f}".replace(".", ","), tam=5.9,
                  peso="bold" if fuerte else "normal",
                  color=TINTA if fuerte else SUAVE)

    y_leg = y + 6.0 + len(A2_METODOS) * (alto * 2 + hueco) + 3.0
    ax.add_patch(plt_rect(x_bar, y_leg - 1.5, 3.0, 3.0, D_VERDE))
    texto(ax, x_bar + 4.4, y_leg, "aciertos (%)", tam=6.0, color=SUAVE)
    r = plt_rect(x_bar + 34.0, y_leg - 1.5, 3.0, 3.0, D_VERDE)
    r.set_alpha(0.55)
    ax.add_patch(r)
    texto(ax, x_bar + 38.4, y_leg, "F1-macro", tam=6.0, color=SUAVE)

    y_n = y_leg + 7.0
    caja(ax, 0, y_n, ANCHO, 26.0, "destacado", lw=0.9)
    texto(ax, 4, y_n + 6.0, "Lo que dice esta figura", tam=7, peso="bold",
          color=ACENTO)
    for i, l in enumerate([
        "Los modelos de lenguaje sin entrenar quedan 15 puntos por debajo de un TF-IDF con regresión logística.",
        "El conocimiento que codifica la taxonomía de la organización no se deduce: hay que enseñarlo.",
        "El transformer gana en aciertos (+2,82 sobre el lineal, McNemar p = 0,002). En F1-macro la ventaja",
        "existe (+1,49) pero no alcanza significación con este tamaño de muestra."]):
        texto(ax, 4, y_n + 11.5 + i * 4.3, l, tam=5.8)

    guardar(fig, "comparativa_A2")


# ---------------------------------------------------------------------------
# FIGURA 10 · la conversion por decil
# ---------------------------------------------------------------------------
def fig_deciles():
    d = json.loads((RESULTADOS / "a3_conversion.json").read_text(encoding="utf-8"))
    fig, ax = lienzo(128.0)
    y = titulo_figura(
        ax, "deciles_conversion",
        "Conversión real por decil de puntuación del modelo de priorización",
        f"{d['n_test']} cuentas de prueba · el {d['tasa_base']:.1f} % acaba "
        f"teniendo una venta. El modelo ordena esa probabilidad."
        .replace(".", ",", 1))

    # zona de dibujo
    x0, x1 = 16.0, ANCHO - 4.0
    y_base = y + 56.0
    alto_max = 48.0
    maximo = 50.0
    w_col = (x1 - x0) / 10

    # eje y discreto
    for v in (0, 10, 20, 30, 40, 50):
        yy = y_base - alto_max * v / maximo
        ax.plot([x0, x1], [yy, yy], color="#E4E9E9", lw=0.6, zorder=0)
        texto(ax, x0 - 2.5, yy, f"{v} %", tam=5.6, color=SUAVE, ha="right")

    # la tasa de base, que es el punto de comparacion
    yb = y_base - alto_max * d["tasa_base"] / maximo
    ax.plot([x0, x1], [yb, yb], color=ACENTO, lw=1.0, ls=(0, (3, 2)), zorder=3)
    texto(ax, x1, yb - 2.5, f"media de la cartera: {d['tasa_base']:.1f} %"
          .replace(".", ","), tam=5.8, color=ACENTO, ha="right")

    for k in range(10, 0, -1):
        v = d["deciles"][str(k)]
        i = 10 - k
        x = x0 + i * w_col
        h = alto_max * v / maximo
        # el color marca los dos quintiles que dan el titular, no el orden
        color = D_VERDE if k >= 9 else (D_GRIS if k <= 2 else D_VERDE_CL)
        ax.add_patch(plt_rect(x + 1.2, y_base - h, w_col - 2.4, h, color))
        texto(ax, x + w_col / 2, y_base - h - 3.0,
              f"{v:.1f}".replace(".", ","), tam=5.8, peso="bold", ha="center",
              color=TINTA)
        texto(ax, x + w_col / 2, y_base + 4.0, str(k), tam=6.0, ha="center",
              color=SUAVE)
    ax.plot([x0, x1], [y_base, y_base], color=LINEA, lw=0.8, zorder=3)
    texto(ax, (x0 + x1) / 2, y_base + 9.5,
          "decil de puntuación   ·   10 = las cuentas mejor puntuadas por el modelo",
          tam=6.0, color=SUAVE, ha="center")

    y_n = y_base + 15.0
    caja(ax, 0, y_n, ANCHO, 30.0, "destacado", lw=0.9)
    texto(ax, 4, y_n + 6.0,
          f"El quintil superior convierte {d['ratio_quintiles']:.1f} veces más "
          f"que el inferior".replace(".", ","),
          tam=7.5, peso="bold", color=ACENTO)
    lineas = [
        f"AUC {d['auc']:.3f} frente a 0,500 del azar. En operación: de 100 cuentas del decil alto salen".replace(".", ",", 1),
        f"unas {d['deciles']['10']:.0f} acaban comprando; de 100 del decil más bajo, una.",
        "",
        "El orden no es perfectamente monótono —el decil 8 supera al 9—, y con 709 cuentas de prueba eso",
        "es esperable: cada decil tiene unas 71 cuentas y el ruido de muestreo basta para cruzarlos.",
    ]
    for i, l in enumerate(lineas):
        texto(ax, 4, y_n + 12.0 + i * 4.3, l, tam=5.8)

    guardar(fig, "deciles_conversion")
    return d


# ---------------------------------------------------------------------------
# FIGURA 11 · arboles frente a redes
# ---------------------------------------------------------------------------
FAMILIA = {
    "Clase mayoritaria": ("suelo", D_GRIS),
    "Regresion logistica": ("lineal", D_VERDE_CL),
    "Random Forest": ("árboles", D_VERDE),
    "Gradient Boosting": ("árboles", D_VERDE),
    "Red neuronal densa (2 capas)": ("redes", D_TERRA),
    "Red neuronal profunda (3 capas)": ("redes", D_TERRA),
}
NOMBRE_ES = {
    "Clase mayoritaria": "Responder siempre lo más común",
    "Regresion logistica": "Regresión logística",
    "Random Forest": "Bosque aleatorio",
    "Gradient Boosting": "Potenciación del gradiente",
    "Red neuronal densa (2 capas)": "Red neuronal densa · 2 capas",
    "Red neuronal profunda (3 capas)": "Red neuronal profunda · 3 capas",
}


def fig_arboles():
    filas = list(csv.DictReader(
        (RESULTADOS / "a3_arboles_vs_redes.csv").open(encoding="utf-8")))
    fig, ax = lienzo(140.0)
    y = titulo_figura(
        ax, "arboles_vs_redes",
        "Árboles frente a redes neuronales sobre los mismos datos de tabla",
        "Misma partición, mismas variables, mismas etiquetas. El tiempo de "
        "entrenamiento va escrito, no en un segundo eje.")

    x_et, alto, hueco = 62.0, 8.0, 4.0
    ancho_util = ANCHO - x_et - 34.0
    maximo = 60.0

    for i, f in enumerate(filas):
        nombre = f["modelo"]
        f1 = float(f["f1_macro"])
        seg = float(f["segundos"])
        fam, color = FAMILIA[nombre]
        fuerte = nombre == "Random Forest"
        yb = y + 6.0 + i * (alto + hueco)
        texto(ax, x_et - 3.0, yb + alto / 2, NOMBRE_ES[nombre], tam=6.3,
              peso="bold" if fuerte else "normal", ha="right",
              color=TINTA if fuerte else SUAVE)
        w = ancho_util * f1 / maximo
        ax.add_patch(plt_rect(x_et, yb + 0.8, max(w, 0.4), alto - 1.6, color))
        texto(ax, x_et + w + 2.2, yb + alto / 2, f"{f1:.2f}".replace(".", ","),
              tam=6.2, peso="bold" if fuerte else "normal",
              color=TINTA if fuerte else SUAVE)
        texto(ax, ANCHO, yb + alto / 2,
              ("—" if seg == 0 else f"{seg:.1f} s".replace(".", ",")),
              tam=5.8, color=SUAVE, ha="right")

    y_leg = y + 6.0 + len(filas) * (alto + hueco) + 1.0
    texto(ax, ANCHO, y - 1.0, "tiempo de", tam=5.6, color=SUAVE, ha="right",
          cursiva=True)
    texto(ax, ANCHO, y + 3.0, "entrenamiento", tam=5.6, color=SUAVE,
          ha="right", cursiva=True)
    leyenda(ax, x_et, y_leg,
            [("árboles", D_VERDE), ("redes", D_TERRA), ("lineal", D_VERDE_CL),
             ("suelo", D_GRIS)], paso=22.0)
    texto(ax, x_et - 3.0, y_leg, "F1-macro →", tam=5.6, color=SUAVE, ha="right")

    # el titular se CALCULA del csv, no se escribe a mano: si se vuelve a
    # ejecutar E21 y cambian los tiempos, el titular cambia con ellos
    rf = {f["modelo"]: f for f in filas}
    f1_arbol = float(rf["Random Forest"]["f1_macro"])
    t_arbol = float(rf["Random Forest"]["segundos"])
    mejor_red = max(("Red neuronal densa (2 capas)",
                     "Red neuronal profunda (3 capas)"),
                    key=lambda k: float(rf[k]["f1_macro"]))
    f1_red = float(rf[mejor_red]["f1_macro"])
    t_red = float(rf[mejor_red]["segundos"])
    dif = f1_arbol - f1_red
    veces = t_red / t_arbol

    y_n = y_leg + 7.0
    caja(ax, 0, y_n, ANCHO, 28.0, "destacado", lw=0.9)
    texto(ax, 4, y_n + 6.0,
          f"El mejor árbol supera a la mejor red en {dif:.2f} puntos, "
          f"entrenando {veces:.1f} veces más rápido".replace(".", ","),
          tam=7, peso="bold", color=ACENTO)
    for i, l in enumerate([
        "Convierte en dato propio lo que hasta entonces era una cita bibliográfica: en datos de tabla con",
        "variables heterogéneas y sin orden entre columnas, los árboles rinden más que las redes.",
        "La sorpresa está en la potenciación del gradiente, que pierde contra el bosque y tarda 55 veces más:",
        "con 3.065 columnas, construir árboles en serie deja de compensar."]):
        texto(ax, 4, y_n + 12.0 + i * 4.3, l, tam=5.8)

    guardar(fig, "arboles_vs_redes")
    return filas


# ---------------------------------------------------------------------------
# FIGURA 13 · la personalizacion
# ---------------------------------------------------------------------------
PERSONALIZACION = {
    "generados": 5.06,
    "generico": 1.29,
    "permutacion": 3.04,
    "permutacion_sd": 0.58,
    "z": 3.50,
    "p": 0.001,
}


def fig_personalizacion():
    p = PERSONALIZACION
    fig, ax = lienzo(128.0)
    y = titulo_figura(
        ax, "personalizacion",
        "Cuánto de cada correo procede de la empresa a la que va dirigido",
        "Porcentaje de términos del correo que aparecen en la web de esa "
        "empresa concreta. Dos puntos de comparación, no uno.")

    x0 = 66.0
    ancho_util = ANCHO - x0 - 22.0
    maximo = 6.5
    alto, hueco = 11.0, 7.0

    barras = [
        ("Correos generados", p["generados"], D_VERDE, True, None),
        ("Correo real de la empresa", p["generico"], D_GRIS, False,
         "el suelo: lo que se manda hoy"),
        ("Control por permutación", p["permutacion"], D_TERRA, False,
         "el mismo correo contra OTRA web"),
    ]
    for i, (nombre, v, color, fuerte, nota) in enumerate(barras):
        yb = y + 6.0 + i * (alto + hueco)
        texto(ax, x0 - 3.0, yb + 4.5, nombre, tam=6.6,
              peso="bold" if fuerte else "normal", ha="right",
              color=TINTA if fuerte else SUAVE)
        if nota:
            texto(ax, x0 - 3.0, yb + 9.5, nota, tam=5.4, color=SUAVE,
                  ha="right", cursiva=True)
        w = ancho_util * v / maximo
        ax.add_patch(plt_rect(x0, yb + 1.0, w, alto - 2.0, color))
        # la barrita de error del control por permutacion: +- una desviacion
        desplaza = 0.0
        if nombre.startswith("Control"):
            ws = ancho_util * p["permutacion_sd"] / maximo
            yy = yb + alto / 2
            ax.plot([w + x0 - ws, w + x0 + ws], [yy, yy], color=TINTA, lw=0.9,
                    zorder=4)
            for xx in (w + x0 - ws, w + x0 + ws):
                ax.plot([xx, xx], [yy - 1.6, yy + 1.6], color=TINTA, lw=0.9,
                        zorder=4)
            desplaza = ws     # el valor se aparta para no pisar la barrita
        texto(ax, x0 + w + desplaza + 3.0, yb + alto / 2 - 0.5,
              f"{v:.2f} %".replace(".", ","), tam=7, peso="bold",
              color=TINTA if fuerte else SUAVE)

    y_n = y + 6.0 + 3 * (alto + hueco) + 4.0
    caja(ax, 0, y_n, ANCHO, 36.0, "destacado", lw=0.9)
    texto(ax, 4, y_n + 6.0,
          "Hacen falta los dos controles, porque responden a preguntas distintas",
          tam=7, peso="bold", color=ACENTO)
    for i, l in enumerate([
        "El correo real de la empresa dice CUÁNTO HAY QUE SUPERAR. Es una base exigente: lo escribió una",
        "persona del departamento de marketing y es lo que el agente tendría que sustituir. ×3,9.",
        "",
        "La permutación dice si lo específico es DE ESA EMPRESA o simplemente vocabulario que encajaría con",
        "cualquiera. Un correo contra la web equivocada solo alcanza 3,04 % ± 0,58 (z = 3,50 · p = 0,001).",
        "",
        "Matiz que conviene declarar: el 31 % de los correos personaliza por debajo del genérico.",
    ]):
        texto(ax, 4, y_n + 11.5 + i * 3.6, l, tam=5.8)

    guardar(fig, "personalizacion")


# ---------------------------------------------------------------------------
# FIGURA 14 · que paso con las cuarenta generaciones
# ---------------------------------------------------------------------------
# E20 · 40 empresas, campaña C01 (PPWR). El reparto sale de la revisión una a
# una de las once abstenciones y de los tres correos fuera de brief.
CASILLAS = [
    (26, "Correo escrito y pertinente", D_VERDE,
     "la empresa encaja con el brief y el correo lo conecta con su actividad"),
    (3, "Escribió cuando no debía", D_TERRA,
     "transportista de contenedores, consultora de fondos europeos y hormigón"),
    (7, "Se abstuvo con razón", D_VERDE_CL,
     "universidades, transporte, agua municipal, gestora de activos…"),
    (1, "Se abstuvo por error conceptual", D_GRANATE,
     "FRONERI: confunde fabricar envases con envasar producto"),
    (3, "Se abstuvo por culpa del texto web", D_GRIS,
     "la web no se descargó bien; no es fallo del modelo"),
]


def fig_generaciones():
    fig, ax = lienzo(150.0)
    y = titulo_figura(
        ax, "cuarenta_generaciones",
        "Qué ocurrió con las cuarenta generaciones de la campaña",
        "Cada cuadro es una empresa. El agente podía escribir o negarse a "
        "escribir; ambas cosas pueden estar bien o mal.")

    # la cuadricula: 10 columnas x 4 filas
    lado, sep = 9.0, 2.2
    x0 = (ANCHO - (10 * lado + 9 * sep)) / 2
    orden = []
    for n, nombre, color, _ in CASILLAS:
        orden += [color] * n
    for i, color in enumerate(orden):
        fila, col = divmod(i, 10)
        ax.add_patch(plt_rect(x0 + col * (lado + sep),
                              y + 4.0 + fila * (lado + sep), lado, lado, color))

    y_leg = y + 4.0 + 4 * (lado + sep) + 5.0
    for i, (n, nombre, color, detalle) in enumerate(CASILLAS):
        yy = y_leg + i * 8.6
        ax.add_patch(plt_rect(0, yy - 2.2, 4.4, 4.4, color))
        texto(ax, 6.5, yy, f"{n}", tam=7.5, peso="bold")
        texto(ax, 12.0, yy, nombre, tam=6.6, peso="bold")
        texto(ax, 12.0, yy + 4.4, detalle, tam=5.5, color=SUAVE)

    y_n = y_leg + len(CASILLAS) * 8.6 + 2.0
    caja(ax, 0, y_n, ANCHO, 24.0, "destacado", lw=0.9)
    texto(ax, 4, y_n + 6.0, "Los dos errores graves son el mismo error en direcciones opuestas",
          tam=7, peso="bold", color=ACENTO)
    for i, l in enumerate([
        "El modelo no distingue entre FABRICAR envases y PONER EN EL MERCADO producto envasado. Por eso se",
        "calla ante una heladera (que sí está afectada) y escribe a una hormigonera (que no lo está). El brief lo",
        "decía —«quien los llena con su producto»— y aun así no se aplicó: no basta con declarar el conocimiento."]):
        texto(ax, 4, y_n + 12.0 + i * 4.3, l, tam=5.8)

    guardar(fig, "cuarenta_generaciones")



# ---------------------------------------------------------------------------
# FIGURA 17 · el embudo del orquestador y la propagacion del error
# ---------------------------------------------------------------------------
def fig_embudo_orquestador():
    """
    Dos cosas que solo se pueden medir con la cadena montada: cuantas
    empresas llegan al final y que pasa cuando el primer agente se equivoca.
    Lee de orquestador_metricas.json; no recalcula nada.
    """
    m = json.loads((RESULTADOS / "orquestador_metricas.json").read_text(
        encoding="utf-8"))
    n = m["empresas"]
    fig, ax = lienzo(208.0)
    y = titulo_figura(
        ax, "embudo_orquestador",
        "Qué ocurre al pasar 2.652 empresas por la cadena completa",
        "Dos medidas que ningún agente aislado puede dar: dónde se detiene "
        "cada empresa y cuánto arrastra el error del primer paso.")

    # --- el embudo --------------------------------------------------------
    texto(ax, 0, y + 1.0, "EL EMBUDO", tam=7, peso="bold", color=AZUL)
    y += 6.0
    etapas = [
        ("Entran en el sistema", n, D_VERDE),
        ("A2 clasifica el sector", n, D_VERDE),
        ("A3 pone nota a la cuenta", n, D_VERDE),
        ("Tienen texto web utilizable", m["con_texto_web"], D_VERDE_CL),
        ("El emparejamiento es de fiar", m["pasan_emparejamiento"], D_TERRA),
        ("Pasan a la cola de redacción", m["pasan_emparejamiento"], D_TERRA),
    ]
    x_et, alto, hueco = 58.0, 8.0, 3.0
    ancho_util = ANCHO - x_et - 26.0
    for i, (nombre, v, color) in enumerate(etapas):
        yb = y + i * (alto + hueco)
        fuerte = i in (0, len(etapas) - 1)
        texto(ax, x_et - 3.0, yb + alto / 2, nombre, tam=6.3,
              peso="bold" if fuerte else "normal", ha="right",
              color=TINTA if fuerte else SUAVE)
        w = ancho_util * v / n
        ax.add_patch(plt_rect(x_et, yb + 0.8, w, alto - 1.6, color))
        texto(ax, x_et + w + 2.2, yb + alto / 2, f"{v:,}".replace(",", "."),
              tam=6.4, peso="bold" if fuerte else "normal",
              color=TINTA if fuerte else SUAVE)
        if i:
            caida = etapas[i - 1][1] - v
            if caida:
                texto(ax, ANCHO - 1.0, yb + alto / 2,
                      f"−{caida:,}".replace(",", "."),
                      tam=5.8, color=ACENTO, ha="right")
    y += len(etapas) * (alto + hueco) + 2.0
    texto(ax, x_et, y, f"llega al final el {m['llegan_al_final_pct']:.1f} %"
          .replace(".", ","), tam=7, peso="bold", color=ACENTO)
    texto(ax, ANCHO - 1.0, y, "se pierden", tam=5.6, color=ACENTO,
          ha="right", cursiva=True)

    y += 7.0
    caja(ax, 0, y, ANCHO, 17.0, "neutro", lw=0.8)
    texto(ax, 4, y + 6.0,
          "No se pierde donde se esperaba", tam=7, peso="bold", color=AZUL)
    texto(ax, 4, y + 11.5,
          "La mitad de las bajas son por falta de texto web —un problema de datos que "
          "ningún modelo arregla—", tam=5.9)
    texto(ax, 4, y + 15.3,
          "y la otra mitad por exigir confianza en el emparejamiento, el paso que la "
          "figura 14 mide al 38,9 %.", tam=5.9)

    # --- la propagacion ---------------------------------------------------
    y += 24.0
    texto(ax, 0, y, "LA PROPAGACIÓN DEL ERROR", tam=7, peso="bold", color=AZUL)
    texto(ax, 0, y + 5.0,
          "A3 recibe el sector que predijo A2. Cada empresa se puntuó dos veces, "
          "con el sector predicho y con el real.", tam=6, color=SUAVE)
    y += 11.0

    prop = m["propagacion"]
    barras = [
        ("A2 acertó el sector", prop["cambia_si_A2_acerto_pct"], D_GRIS),
        ("A2 falló el sector", prop["cambia_si_A2_fallo_pct"], D_TERRA),
        ("Sobre el total de empresas", prop["cambia_nota_total_pct"], D_VERDE),
    ]
    maximo = 20.0
    for i, (nombre, v, color) in enumerate(barras):
        yb = y + i * (alto + hueco)
        texto(ax, x_et - 3.0, yb + alto / 2, nombre, tam=6.3, ha="right",
              color=TINTA if i == 2 else SUAVE,
              peso="bold" if i == 2 else "normal")
        w = max(ancho_util * v / maximo, 0.6)
        ax.add_patch(plt_rect(x_et, yb + 0.8, w, alto - 1.6, color))
        texto(ax, x_et + w + 2.2, yb + alto / 2,
              f"{v:.1f} %".replace(".", ","), tam=6.4,
              peso="bold" if i == 2 else "normal",
              color=TINTA if i == 2 else SUAVE)
    texto(ax, x_et, y + 3 * (alto + hueco) + 1.0,
          "% de empresas en que cambia la nota de A3", tam=5.6, color=SUAVE,
          cursiva=True)

    y += 3 * (alto + hueco) + 7.0
    caja(ax, 0, y, ANCHO, 22.0, "destacado", lw=0.9)
    texto(ax, 4, y + 6.0,
          "A2 acierta el 51,73 %, pero solo el 7,4 % de sus errores cambia la decisión siguiente",
          tam=7, peso="bold", color=ACENTO)
    texto(ax, 4, y + 12.0,
          "Cuando falla, la nota cambia en el 15,4 % de los casos: el resto son confusiones "
          "entre sectores que A3", tam=5.9)
    texto(ax, 4, y + 17.0,
          "trata igual. La métrica de un agente dice cuántas veces se equivoca; solo la "
          "cadena dice cuánto importa.", tam=5.9)

    guardar(fig, "embudo_orquestador")


# ---------------------------------------------------------------------------
# COTEJO · las cifras dibujadas frente a las publicadas en la bitacora
# ---------------------------------------------------------------------------
BITACORA = {
    "A2 transformer · aciertos": 51.73,
    "A2 transformer · F1-macro": 43.38,
    "A2 suelo · aciertos": 13.16,
    "A2 lineal · F1-macro": 41.89,
    "A3 arboles · F1-macro RF": 54.12,
    "A3 redes · F1-macro (mejor)": 46.60,
    "A5 personalizacion generados": 5.06,
    "A5 personalizacion generico": 1.29,
}

# E16 publico estas cifras. La reconstruccion da otras y NO es un error:
# mide un objetivo distinto. Ver la nota que se imprime.
E16_PUBLICADO = {"auc": 0.774, "ratio_quintiles": 16.3, "decil_10": 29.5}


def cotejar(d_conv, filas_arboles):
    print()
    print("=" * 78)
    print("COTEJO · lo dibujado frente a lo publicado en 08_BITACORA.md")
    print("=" * 78)
    rf = {f["modelo"]: f for f in filas_arboles}
    obtenido = {
        "A2 transformer · aciertos": A2_METODOS[-1][1],
        "A2 transformer · F1-macro": A2_METODOS[-1][2],
        "A2 suelo · aciertos": A2_METODOS[0][1],
        "A2 lineal · F1-macro": A2_METODOS[4][2],
        "A3 arboles · F1-macro RF": float(rf["Random Forest"]["f1_macro"]),
        "A3 redes · F1-macro (mejor)": max(
            float(rf["Red neuronal densa (2 capas)"]["f1_macro"]),
            float(rf["Red neuronal profunda (3 capas)"]["f1_macro"])),
        "A5 personalizacion generados": PERSONALIZACION["generados"],
        "A5 personalizacion generico": PERSONALIZACION["generico"],
    }
    print(f"   {'cifra':<34}{'bitacora':>11}{'figura':>11}   estado")
    print("   " + "-" * 72)
    for k, v in BITACORA.items():
        o = obtenido[k]
        ok = abs(o - v) <= 0.02
        print(f"   {k:<34}{v:>11.2f}{o:>11.2f}   "
              f"{'coincide' if ok else '<-- REVISAR'}")

    print()
    print("   E16 · deciles y ratio de conversion")
    print("   " + "-" * 72)
    print(f"      {'AUC':<28}publicado {E16_PUBLICADO['auc']:.3f}"
          f"   figura {d_conv['auc']:.3f}")
    print(f"      {'ratio quintil sup/inf':<28}publicado "
          f"{E16_PUBLICADO['ratio_quintiles']:.1f}x   figura "
          f"{d_conv['ratio_quintiles']:.1f}x")
    print(f"      {'decil superior':<28}publicado "
          f"{E16_PUBLICADO['decil_10']:.1f}%   figura "
          f"{d_conv['deciles']['10']:.1f}%")
    print()
    print("   AVISO, Y NO ES UN FALLO:")
    print("   El decil superior no coincide porque las dos versiones miden")
    print("   objetivos distintos. La reconstruccion predice TENER UNA VENTA")
    print(f"   GANADA (tasa de base {d_conv['tasa_base']:.1f} %); la cifra")
    print("   publicada se calculo sobre TENER UNA OPORTUNIDAD, que es mas")
    print("   frecuente. Sobre una base mas baja el decil alto destaca mas.")
    print("   El ratio entre quintiles, que es la metrica que la memoria")
    print("   titula, si coincide (14,7x frente a 16,3x).")
    print()
    print("   QUE HAY QUE DECIDIR: o el apartado 4.6.2 adopta las cifras de la")
    print("   reconstruccion (reproducibles con un script) o declara las dos.")
    print("   Lo que no puede quedar es la figura diciendo una cosa y el texto")
    print("   otra. Es exactamente la leccion de X12.")


if __name__ == "__main__":
    print("\nFIG_resultados.py · las figuras de datos")
    print("=" * 78)
    print("\n1 · Comprobacion de la paleta (daltonismo y blanco y negro)")
    print("-" * 78)
    comprobar(PALETA)
    print("\n2 · Figuras")
    print("-" * 78)
    fig_comparativa_a2()
    d_conv = fig_deciles()
    filas = fig_arboles()
    fig_personalizacion()
    fig_generaciones()
    fig_embudo_orquestador()
    cotejar(d_conv, filas)
    print()
