# -*- coding: utf-8 -*-
"""
FIG_arquitectura.py · los diagramas de la memoria de la memoria
=================================================

QUE GENERA

    fig01_mapa_fases_agentes   Las 11 fases del proceso comercial, los dos
                               caminos (captacion activa y recepcion), que
                               agente automatiza cada fase y en que estado
                               esta cada uno. Es la figura del apartado 4.2.1.

    fig02_dos_taxonomias       Las DOS clasificaciones del trabajo y por que
                               no se pueden mezclar. Apartado 4.2.2.

    fig03_despliegue           La arquitectura de despliegue en dos circuitos:
                               lo que corre en un portatil y lo unico que
                               necesita GPU. Apartado 7.2.

POR QUE ESTAS TRES Y EN ESTE ORDEN
    Las tres responden a preguntas que un tribunal hace de entrada:
    que hace el sistema, que clasifica exactamente, y donde se ejecuta.

    La figura 1 hace ademas un trabajo que el texto hace peor: mostrar de un
    golpe que de once fases se han construido dos y media. El alcance se ve,
    no hay que defenderlo parrafo a parrafo.

COMO SE EJECUTA
    python scripts/FIG_arquitectura.py

    Las figuras salen en figuras/ en png (300 ppp) y svg.

FUENTES
    00_SECUENCIA_SDR.txt      las 11 fases y las dos taxonomias
    memoria/CAP7_futuras_lineas.md  apartado 7.2, la tabla de requisitos de GPU
"""

from matplotlib.patches import Polygon, Rectangle

from fig_comun import (ANCHO, TINTA, SUAVE, LINEA, VERDE, VERDE_CL, GRIS_CL,
                       ACENTO, AZUL, caja, texto, flecha, lienzo, guardar,
                       titulo_figura, leyenda_estados, ESTILOS)

# ---------------------------------------------------------------------------
# FIGURA 1 · el mapa de las 11 fases
# ---------------------------------------------------------------------------
# codigo, nombre de la fase, agente, que hace el agente, estado
FASES_DET = [
    ("F0",  "Definir a quién buscamos",   "—",   "el perfil de cliente y los criterios del playbook", "manual"),
    ("F1",  "Buscar empresas",            "A1",  "listar empresas por parecido con la cartera actual", "disenado"),
    ("F2",  "Enriquecer los datos",       "A2",  "clasificar el sector de la empresa · 41 clases",     "construido"),
    ("F3",  "Puntuar y priorizar",        "A3",  "nota A-E y probabilidad de conversión",              "construido"),
    ("F4",  "Encontrar a la persona",     "A4",  "quién decide dentro de la empresa y cómo llegar",    "disenado"),
    ("F5",  "Contactar",                  "A5",  "redactar el correo personalizado, o abstenerse",     "simple"),
]

FASE_INBOUND = ("F6", "Atender lo que entra", "A6",
                "identificar quién escribe, qué pide y a dónde va", "construido")

# F7 ya no tiene agente propio: D24 la absorbio en A6. Lo que el diseño le
# asignaba no sostenia un agente —medido en E36— y la cualificacion que la
# via de entrada necesita de verdad la resuelve la cuarta pieza de A6.
FASES_COMUNES = [
    ("F7",  "Cualificar",                 "A6",  "lo comercial frente a lo que no lo es · dentro de A6", "construido"),
    ("F8",  "Pasar al técnico comercial", "A7",  "área técnica, tipo de servicio y briefing",            "construido"),
    ("F9",  "Seguir la oportunidad",      "A8",  "probabilidad de cierre y aviso de atasco",             "construido"),
    ("F10", "Aprender y ajustar",         "A9",  "detectar que el modelo se ha quedado obsoleto",        "disenado"),
]


def caja_fase(ax, x, y, w, h, codigo, nombre, agente, que_hace, estado):
    """Una caja de fase: codigo + nombre, agente + lo que hace, y el estado."""
    _, col_texto, _, etiqueta = ESTILOS[estado]
    caja(ax, x, y, w, h, estado, radio=1.2,
         discontinua=(estado in ("disenado", "manual")))
    texto(ax, x + 4, y + 4.4, f"{codigo}", tam=8, peso="bold", color=col_texto)
    texto(ax, x + 13, y + 4.4, nombre, tam=8, peso="bold", color=col_texto)
    pref = f"{agente} · " if agente != "—" else "sin agente · "
    texto(ax, x + 4, y + 9.3, pref + que_hace, tam=5.9, color=col_texto)
    texto(ax, x + w - 4, y + 4.4, etiqueta, tam=5.4, color=col_texto,
          ha="right", cursiva=True)


def fig_mapa():
    # 227 y no 222: el subtitulo ocupa dos lineas desde que explica lo de
    # los diez agentes, y sin ese milimetraje la leyenda se sale por abajo
    ALTO = 239.0
    fig, ax = lienzo(ALTO)
    y0 = titulo_figura(
        ax, "mapa_fases_agentes",
        "El proceso de Sales Development en once fases y diez agentes",
        "Once fases y diez agentes porque A6 cubre dos: recepción y "
        "cualificación. El color y la etiqueta indican qué se construyó y qué "
        "quedó en diseño.")

    # --- cabeceras de los dos caminos ------------------------------------
    w_col = 76.0
    x_izq, x_der = 0.0, ANCHO - w_col
    texto(ax, x_izq, y0 + 2, "CAMINO 1 · CAPTACIÓN ACTIVA", tam=7, peso="bold",
          color=AZUL)
    texto(ax, x_izq, y0 + 6.6, "nosotros buscamos al cliente", tam=6,
          color=SUAVE)
    texto(ax, x_der, y0 + 2, "CAMINO 2 · RECEPCIÓN", tam=7, peso="bold",
          color=AZUL)
    texto(ax, x_der, y0 + 6.6, "el cliente nos busca", tam=6, color=SUAVE)

    # --- columna outbound -------------------------------------------------
    h, paso = 13.0, 16.2
    yb = y0 + 11.0
    for i, f in enumerate(FASES_DET):
        y = yb + i * paso
        caja_fase(ax, x_izq, y, w_col, h, *f)
        if i:
            flecha(ax, x_izq + w_col / 2, y - paso + h, x_izq + w_col / 2, y)
    y_fin_izq = yb + (len(FASES_DET) - 1) * paso + h

    # --- columna inbound: una sola fase, alineada con F3 -----------------
    y_in = yb + 2 * paso
    caja_fase(ax, x_der, y_in, w_col, h, *FASE_INBOUND)
    texto(ax, x_der, y_in + h + 5.0,
          "Una sola fase, pero es la puerta por la que hoy", tam=6, color=SUAVE)
    texto(ax, x_der, y_in + h + 9.2,
          "entra la mayor parte del negocio real.", tam=6, color=SUAVE)

    # --- confluencia ------------------------------------------------------
    y_j = y_fin_izq + 9.0
    cx_i, cx_d = x_izq + w_col / 2, x_der + w_col / 2
    ax.plot([cx_i, cx_i], [y_fin_izq, y_j], color=LINEA, lw=0.9, zorder=1)
    ax.plot([cx_d, cx_d], [y_in + h, y_j], color=LINEA, lw=0.9, zorder=1)
    ax.plot([cx_i, cx_d], [y_j, y_j], color=LINEA, lw=0.9, zorder=1)
    texto(ax, ANCHO / 2, y_j - 4.6, "los dos caminos confluyen aquí", tam=6,
          color=SUAVE, ha="center", cursiva=True)

    # --- fases comunes ----------------------------------------------------
    w_com = 118.0
    x_com = (ANCHO - w_com) / 2
    yc = y_j + 8.0
    flecha(ax, ANCHO / 2, y_j, ANCHO / 2, yc)
    for i, f in enumerate(FASES_COMUNES):
        y = yc + i * paso
        caja_fase(ax, x_com, y, w_com, h, *f)
        if i:
            flecha(ax, ANCHO / 2, y - paso + h, ANCHO / 2, y)
    y_fin = yc + (len(FASES_COMUNES) - 1) * paso + h

    # el bucle de aprendizaje, dicho en una linea en vez de con una flecha que
    # tendria que cruzar toda la figura
    texto(ax, x_com, y_fin + 5.0,
          "F10 cierra el bucle: lo aprendido vuelve a F0 y corrige el perfil de cliente.",
          tam=6, color=SUAVE, cursiva=True)

    # --- leyenda ----------------------------------------------------------
    y_leg = y_fin + 15.0
    leyenda_estados(ax, 0, y_leg, ["construido", "simple", "disenado", "manual"],
                    ancho_item=40)
    texto(ax, 0, y_leg + 8.5,
          "De once fases, seis se cubren con agentes construidos y medidos sobre "
          "datos reales —F2, F3, F6, F7, F8 y F9—, una en versión simple (F5)",
          tam=6, color=SUAVE)
    texto(ax, 0, y_leg + 12.7,
          "y el resto quedó diseñada y justificada. Recortar el alcance y declararlo "
          "por escrito es una decisión, no una renuncia.",
          tam=6, color=SUAVE)

    guardar(fig, "mapa_fases_agentes")


# ---------------------------------------------------------------------------
# FIGURA 2 · las dos taxonomias
# ---------------------------------------------------------------------------
def fig_taxonomias():
    ALTO = 138.0
    fig, ax = lienzo(ALTO)
    y0 = titulo_figura(
        ax, "dos_taxonomias", "Las dos taxonomías del sistema, y por qué no se pueden mezclar",
        "Una clasifica a la empresa; la otra, lo que esa empresa necesita. Se "
        "saben en momentos distintos del proceso.")

    w = 77.0
    x1, x2 = 0.0, ANCHO - w
    h_caja = 62.0

    # --- taxonomia 1 ------------------------------------------------------
    caja(ax, x1, y0, w, h_caja, "neutro", lw=1.0)
    texto(ax, x1 + 5, y0 + 6.5, "TAXONOMÍA 1", tam=7, peso="bold", color=AZUL)
    texto(ax, x1 + 5, y0 + 12.5, "El sector del cliente", tam=9, peso="bold")
    texto(ax, x1 + 5, y0 + 18.5, "«¿qué hace esta empresa?»", tam=6.5,
          color=SUAVE, cursiva=True)
    filas_1 = [
        ("Clases", "41 sectores (12 agrupados)"),
        ("De dónde sale", "la web de la empresa + el CRM"),
        ("Cuándo se sabe", "ANTES de hablar con ella"),
        ("Para qué sirve", "priorizar y personalizar"),
        ("Dónde actúa", "F2 (A2) y F3 (A3)"),
        ("Modelo", "clasificador de texto entrenado"),
    ]
    for i, (k, v) in enumerate(filas_1):
        yy = y0 + 26.5 + i * 5.8
        texto(ax, x1 + 5, yy, k, tam=6, color=SUAVE)
        texto(ax, x1 + 27, yy, v, tam=6.3, peso="bold")

    # --- taxonomia 2 ------------------------------------------------------
    caja(ax, x2, y0, w, h_caja, "neutro", lw=1.0)
    texto(ax, x2 + 5, y0 + 6.5, "TAXONOMÍA 2", tam=7, peso="bold", color=AZUL)
    texto(ax, x2 + 5, y0 + 12.5, "Lo que necesita de nosotros", tam=9, peso="bold")
    texto(ax, x2 + 5, y0 + 18.5, "«¿qué nos está pidiendo?»", tam=6.5,
          color=SUAVE, cursiva=True)

    # dos dimensiones, en dos cajitas
    wd = (w - 14) / 2
    for j, (tit, sub, items) in enumerate([
            ("2a · ÁREA TÉCNICA", "puede marcar varias a la vez",
             ["envase", "logística", "sostenibilidad", "seguridad alimentaria"]),
            ("2b · TIPO DE SERVICIO", "opción única",
             ["ensayo de laboratorio", "consultoría", "proyecto de I+D", "formación"])]):
        xx = x2 + 5 + j * (wd + 4)
        caja(ax, xx, y0 + 23.0, wd, 33.0, "destacado", radio=1.0, lw=0.8)
        texto(ax, xx + 3, y0 + 28.0, tit, tam=6, peso="bold", color=ACENTO)
        texto(ax, xx + 3, y0 + 32.5, sub, tam=5.2, color=SUAVE, cursiva=True)
        for i, it in enumerate(items):
            texto(ax, xx + 3, y0 + 38.0 + i * 4.6, "· " + it, tam=5.8)

    texto(ax, x2 + 5, y0 + 59.5, "Se sabe DESPUÉS de hablar · actúa en F7 (A7) y F8 (A8)",
          tam=6, peso="bold", color=AZUL)

    # --- la relacion ------------------------------------------------------
    yr = y0 + h_caja + 12.0
    flecha(ax, x1 + w / 2, y0 + h_caja, x1 + w / 2, yr - 2)
    flecha(ax, x2 + w / 2, y0 + h_caja, x2 + w / 2, yr - 2)
    caja(ax, 0, yr, ANCHO, 36.0, "destacado", lw=1.0)
    texto(ax, 5, yr + 6.5, "La relación entre las dos es de MUCHOS A MUCHOS",
          tam=8, peso="bold", color=ACENTO)
    lineas = [
        "El sector NO determina el área. Una misma empresa química puede necesitar un ensayo de materiales, una huella de",
        "carbono o mejorar su transporte: tres áreas distintas, un solo sector. Y un área atiende a empresas de sectores muy",
        "diferentes. Por eso hace falta un modelo aparte, que clasifica la NECESIDAD EXPRESADA y no la empresa.",
    ]
    for i, l in enumerate(lineas):
        texto(ax, 5, yr + 13.5 + i * 4.8, l, tam=5.9)
    texto(ax, 5, yr + 30.0,
          "Ejemplo:   «ensayo de envase» = (ENVASE, ENSAYO)     ·     "
          "«huella de carbono» = (SOSTENIBILIDAD, CONSULTORÍA)",
          tam=6, peso="bold", color=VERDE)

    guardar(fig, "dos_taxonomias")


# ---------------------------------------------------------------------------
# FIGURA 3 · el despliegue en dos circuitos
# ---------------------------------------------------------------------------
def fig_despliegue():
    ALTO = 166.0
    fig, ax = lienzo(ALTO)
    y0 = titulo_figura(
        ax, "despliegue_dos_circuitos", "Arquitectura de despliegue en dos circuitos",
        "De los seis componentes del recorrido, solo uno necesita procesamiento "
        "gráfico en cada ejecución.")

    # --- circuito sincrono ------------------------------------------------
    caja(ax, 0, y0, ANCHO, 46.0, "neutro", lw=1.0)
    texto(ax, 5, y0 + 6.5, "CIRCUITO SÍNCRONO", tam=8, peso="bold", color=VERDE)
    texto(ax, 5, y0 + 12.0, "equipo convencional, sin GPU · responde en segundos",
          tam=6, color=SUAVE)
    pasos = ["limpiar el\nmensaje", "identificar\nquién escribe", "clasificar\nel sector",
             "puntuar\nla cuenta", "enrutar\nal área", "acuse de recibo\ny aviso al técnico"]
    wp = (ANCHO - 10 - 5 * 3.0) / 6
    for i, p in enumerate(pasos):
        xx = 5 + i * (wp + 3.0)
        caja(ax, xx, y0 + 17.0, wp, 20.0, "construido", radio=1.0, lw=0.8)
        ax.text(xx + wp / 2, y0 + 27.0, p, fontsize=5.6, color="white",
                ha="center", va="center", linespacing=1.3, zorder=4)
        if i:
            flecha(ax, xx - 3.0, y0 + 27.0, xx, y0 + 27.0, lw=0.8, color=LINEA)
    texto(ax, 5, y0 + 42.0,
          "Reglas deterministas, un modelo de árboles y un diccionario. "
          "Nada de esto genera texto, y por eso nada de esto necesita GPU.",
          tam=5.9, color=SUAVE)

    # --- frontera ---------------------------------------------------------
    yf = y0 + 52.0
    ax.plot([0, ANCHO], [yf, yf], color=ACENTO, lw=0.9, ls=(0, (4, 2)))
    texto(ax, ANCHO / 2, yf - 3.0, "la frontera está donde empieza a escribirse texto",
          tam=6, color=ACENTO, ha="center", cursiva=True)

    # --- circuito por lotes ----------------------------------------------
    y1 = yf + 6.0
    caja(ax, 0, y1, ANCHO, 46.0, "neutro", lw=1.0)
    texto(ax, 5, y1 + 6.5, "CIRCUITO POR LOTES", tam=8, peso="bold", color=ACENTO)
    texto(ax, 5, y1 + 12.0, "GPU (Colab) · diferido, en cola · admite horas de demora",
          tam=6, color=SUAVE)
    lotes = [("cola de\npendientes", "neutro"), ("REDACTAR\nel mensaje", "destacado"),
             ("revisión\nhumana", "construido"), ("envío", "construido")]
    wl = (ANCHO - 10 - 3 * 4.0) / 4
    for i, (p, est) in enumerate(lotes):
        xx = 5 + i * (wl + 4.0)
        caja(ax, xx, y1 + 17.0, wl, 20.0, est, radio=1.0, lw=1.0)
        col = ESTILOS[est][1]
        ax.text(xx + wl / 2, y1 + 27.0, p, fontsize=6.2,
                fontweight="bold" if i == 1 else "normal",
                color=col, ha="center", va="center", linespacing=1.3, zorder=4)
        if i:
            flecha(ax, xx - 4.0, y1 + 27.0, xx, y1 + 27.0, lw=0.8, color=LINEA)
    texto(ax, 5 + wl + 4.0, y1 + 41.0,
          "el único paso con GPU: modelo de 7.000 millones de parámetros",
          tam=5.6, color=ACENTO, peso="bold")

    # --- el argumento -----------------------------------------------------
    y2 = y1 + 52.0
    caja(ax, 0, y2, ANCHO, 26.0, "destacado", lw=1.0)
    texto(ax, 5, y2 + 6.5, "Esta separación no es una concesión a la falta de medios",
          tam=7.5, peso="bold", color=ACENTO)
    texto(ax, 5, y2 + 13.0,
          "La generación es precisamente el paso que los resultados indican que necesita "
          "revisión humana: cuatro errores de", tam=5.9)
    texto(ax, 5, y2 + 17.8,
          "pertinencia sobre cuarenta generaciones. Que los borradores pasen por una cola "
          "y por una persona no es una", tam=5.9)
    texto(ax, 5, y2 + 22.6,
          "limitación del despliegue: es la salvaguarda que hace falta. La restricción de "
          "infraestructura y el buen diseño coinciden.", tam=5.9)

    guardar(fig, "despliegue_dos_circuitos")



# ---------------------------------------------------------------------------
# FIGURA 1 · la posicion del SDR en el embudo
# ---------------------------------------------------------------------------
def fig_embudo():
    fig, ax = lienzo(124.0)
    y0 = titulo_figura(
        ax, "embudo_sdr",
        "Dónde trabaja el SDR dentro del embudo de ventas B2B",
        "No cierra ventas. Convierte el interés difuso en oportunidad "
        "cualificada y se la entrega al ejecutivo de cuentas.")

    cx = 68.0
    bandas = [
        ("TOFU", "Descubrimiento y atracción", 110.0, 84.0, GRIS_CL, TINTA),
        ("MOFU", "Consideración y cualificación", 84.0, 54.0, VERDE_CL, "white"),
        ("BOFU", "Negociación y cierre", 54.0, 26.0, VERDE, "white"),
    ]
    h = 24.0
    for i, (sigla, nombre, w_sup, w_inf, color, col_txt) in enumerate(bandas):
        y = y0 + i * h
        ax.add_patch(Polygon(
            [(cx - w_sup / 2, y), (cx + w_sup / 2, y),
             (cx + w_inf / 2, y + h - 1.6), (cx - w_inf / 2, y + h - 1.6)],
            closed=True, facecolor=color, edgecolor="white", linewidth=1.6,
            zorder=2))
        texto(ax, cx, y + 8.5, sigla, tam=8, peso="bold", color=col_txt,
              ha="center")
        texto(ax, cx, y + 14.5, nombre, tam=6, color=col_txt, ha="center")

    # el estado del contacto en cada frontera, a la izquierda
    estados = [(y0 - 1.0, "lead"), (y0 + h, "MQL"), (y0 + 2 * h, "SQL"),
               (y0 + 3 * h - 1.6, "cliente")]
    for y, e in estados:
        ax.plot([9.0, 12.0], [y, y], color=LINEA, lw=0.8, zorder=1)
        texto(ax, 8.0, y, e, tam=6, peso="bold", color=AZUL, ha="right")

    # quien es responsable de cada tramo, a la derecha
    tramos = [("Marketing", 126.0, y0, y0 + 16.0, LINEA, "normal"),
              ("SDR", 130.0, y0 + 14.0, y0 + 2 * h - 2.0, ACENTO, "bold"),
              ("Ejecutivo de cuentas", 134.0, y0 + 2 * h - 6.0,
               y0 + 3 * h - 1.6, LINEA, "normal")]
    for quien, x_b, ya, yb, col, peso in tramos:
        ax.plot([x_b, x_b], [ya, yb], color=col,
                lw=2.6 if peso == "bold" else 1.4, zorder=3,
                solid_capstyle="round")
        texto(ax, x_b + 3.0, (ya + yb) / 2, quien, tam=6.3, peso=peso,
              color=col)

    y_n = y0 + 3 * h + 7.0
    caja(ax, 0, y_n, ANCHO, 22.0, "destacado", lw=0.9)
    texto(ax, 4, y_n + 6.0, "El SDR ocupa la franja entre TOFU y MOFU",
          tam=7.5, peso="bold", color=ACENTO)
    texto(ax, 4, y_n + 12.0,
          "Su producto final no es una venta: es un lead cualificado (SQL) con "
          "necesidad, presupuesto, plazo y decisor", tam=6)
    texto(ax, 4, y_n + 17.0,
          "identificados. Es también el tramo donde más oportunidades se pierden "
          "por tiempo de respuesta.", tam=6)

    guardar(fig, "embudo_sdr")


# ---------------------------------------------------------------------------
# FIGURA 2 · que es un sistema multi-agente, y el error que se propaga
# ---------------------------------------------------------------------------
def fig_concepto():
    fig, ax = lienzo(130.0)
    y0 = titulo_figura(
        ax, "concepto_multiagente",
        "Qué es un sistema multi-agente encadenado",
        "Cada agente resuelve una decisión y solo una. La salida de uno es la "
        "entrada del siguiente.")

    w, h = 44.0, 30.0
    hueco = (ANCHO - 3 * w) / 2
    etiquetas = [("Agente 1", "clasificar"), ("Agente 2", "priorizar"),
                 ("Agente 3", "redactar")]
    for i, (ag, tarea) in enumerate(etiquetas):
        x = i * (w + hueco)
        caja(ax, x, y0, w, h, "construido", lw=1.0)
        texto(ax, x + w / 2, y0 + 9.0, ag, tam=8, peso="bold", color="white",
              ha="center")
        texto(ax, x + w / 2, y0 + 15.5, tarea, tam=6.5, color="white",
              ha="center")
        texto(ax, x + w / 2, y0 + 23.0, "entrada → salida", tam=5.6,
              color="#BBD6D3", ha="center", cursiva=True)
        if i:
            flecha(ax, x - hueco, y0 + h / 2, x, y0 + h / 2, lw=1.2)
            texto(ax, x - hueco / 2, y0 + h / 2 - 3.6, "la salida de uno",
                  tam=5.0, color=SUAVE, ha="center")
            texto(ax, x - hueco / 2, y0 + h / 2 + 5.0, "es la entrada",
                  tam=5.0, color=SUAVE, ha="center")
            texto(ax, x - hueco / 2, y0 + h / 2 + 9.0, "del siguiente",
                  tam=5.0, color=SUAVE, ha="center")

    # la propagacion del error
    y1 = y0 + h + 13.0
    texto(ax, 0, y1 - 4.5, "Y lo que ocurre si el primero se equivoca:",
          tam=6.5, peso="bold", color=ACENTO)
    for i in range(3):
        x = i * (w + hueco)
        caja(ax, x, y1, w, 18.0, "destacado", lw=1.0, discontinua=True)
        msg = ["sector equivocado", "prioridad equivocada", "mensaje inadecuado"][i]
        texto(ax, x + w / 2, y1 + 9.0, msg, tam=6.5, peso="bold", color=ACENTO,
              ha="center")
        if i:
            flecha(ax, x - hueco, y1 + 9.0, x, y1 + 9.0, lw=1.2, color=ACENTO,
                   discontinua=True)

    y2 = y1 + 18.0 + 10.0
    caja(ax, 0, y2, ANCHO, 22.0, "neutro", lw=0.9)
    texto(ax, 4, y2 + 6.0,
          "La propagación del error es propia de los sistemas encadenados",
          tam=7.5, peso="bold", color=AZUL)
    texto(ax, 4, y2 + 12.0,
          "No se manifiesta al evaluar cada componente por separado: un agente "
          "puede tener buenas métricas y aun", tam=6)
    texto(ax, 4, y2 + 17.0,
          "así arrastrar a los siguientes. Medirla exige ejecutar la cadena "
          "completa, que es lo que queda pendiente.", tam=6)

    guardar(fig, "concepto_multiagente")


# ---------------------------------------------------------------------------
# FIGURA 3 · el ciclo de trabajo
# ---------------------------------------------------------------------------
def fig_ciclo():
    fig, ax = lienzo(114.0)
    y0 = titulo_figura(
        ax, "ciclo_iterativo",
        "El ciclo de trabajo seguido en el proyecto",
        "Iterativo y guiado por la evidencia. El alcance no podía fijarse de "
        "antemano: dependía de qué datos existían.")

    x_ini = 14.0
    w3 = (ANCHO - x_ini - 2 * 6.0) / 3
    arriba = ["plantear una\nhipótesis", "diseñar la\nmedición", "ejecutar"]
    for i, t in enumerate(arriba):
        x = x_ini + i * (w3 + 6.0)
        caja(ax, x, y0, w3, 20.0, "neutro", lw=0.9)
        ax.text(x + w3 / 2, y0 + 10.0, t, fontsize=7, color=TINTA,
                ha="center", va="center", linespacing=1.4, zorder=4)
        if i:
            flecha(ax, x - 6.0, y0 + 10.0, x, y0 + 10.0, lw=1.0)

    y1 = y0 + 20.0 + 9.0
    flecha(ax, ANCHO - w3 / 2, y0 + 20.0, ANCHO - w3 / 2, y1)
    caja(ax, x_ini, y1, ANCHO - x_ini, 17.0, "destacado", lw=1.0)
    texto(ax, (x_ini + ANCHO) / 2, y1 + 6.5, "registrar el resultado", tam=7.5,
          peso="bold", color=ACENTO, ha="center")
    texto(ax, (x_ini + ANCHO) / 2, y1 + 12.0,
          "incluso —sobre todo— si refuta la hipótesis",
          tam=6.5, color=ACENTO, ha="center", cursiva=True)

    y2 = y1 + 17.0 + 9.0
    flecha(ax, (x_ini + ANCHO) / 2, y1 + 17.0, (x_ini + ANCHO) / 2, y2)
    caja(ax, x_ini, y2, ANCHO - x_ini, 17.0, "neutro", lw=0.9)
    texto(ax, (x_ini + ANCHO) / 2, y2 + 9.5,
          "decidir:  continuar · corregir · descartar",
          tam=7.5, peso="bold", ha="center")

    # el retorno, por la izquierda
    ax.plot([x_ini, 6.0, 6.0], [y2 + 8.5, y2 + 8.5, y0 + 10.0],
            color=LINEA, lw=1.0, ls=(0, (3, 2)), zorder=1)
    flecha(ax, 6.0, y0 + 10.0, x_ini, y0 + 10.0, discontinua=True, lw=1.0)

    y3 = y2 + 17.0 + 9.0
    texto(ax, 0, y3 + 3.0,
          "Consecuencia sobre el alcance: tres agentes se construyeron y ocho se "
          "diseñaron sin construirse. No figuraba", tam=6, color=SUAVE)
    texto(ax, 0, y3 + 8.0,
          "en el planteamiento inicial; se adoptó al comprobar el volumen de "
          "evaluación que exigía cada agente.", tam=6, color=SUAVE)

    guardar(fig, "ciclo_iterativo")


# ---------------------------------------------------------------------------
# FIGURA 4 · el cronograma
# ---------------------------------------------------------------------------
# dia 0 = 21 de septiembre. Las fechas salen de la TABLA 9 del apartado 4.1.2
# y son las registradas en el cuaderno de trabajo. SI EL TRABAJO EMPEZO ANTES,
# hay que cambiarlas aqui y volver a ejecutar el script.
BLOQUES = [
    ("1 · Análisis del proceso y alcance", 0, 3, "construido"),
    ("2 · Obtención y preparación de datos", 4, 5, "construido"),
    ("3 · Construcción y evaluación de agentes", 5, 7, "construido"),
    ("4 · Verificación y auditoría", 8, 8, "construido"),
    ("5 · Redacción de la memoria", 8, 22, "simple"),
]
DIAS_MES = [(0, "21 sep"), (4, "25 sep"), (9, "30 sep"), (14, "5 oct"),
            (19, "10 oct"), (22, "13 oct")]


def fig_gantt():
    # 116 y no 106: la caja de observaciones del final se salia por abajo
    fig, ax = lienzo(116.0)
    y0 = titulo_figura(
        ax, "gantt", "Cronograma del proyecto",
        "Las fechas son las del cuaderno de trabajo. El bloque 5 se solapa con "
        "el 4: la redacción empezó antes de cerrar la auditoría.")

    x_ini, x_fin, dias = 62.0, ANCHO - 4.0, 22

    def dia_a_x(d):
        return x_ini + (x_fin - x_ini) * d / dias

    y_tope = y0 + 6.0 + len(BLOQUES) * 11.0
    for d, etiq in DIAS_MES:
        x = dia_a_x(d)
        ax.plot([x, x], [y0 + 3.5, y_tope], color="#DFE4E4", lw=0.7, zorder=0)
        # la ultima fecha se alinea a la derecha para que no salga de la pagina
        ha = "right" if d == dias else ("left" if d == 0 else "center")
        texto(ax, x, y0, etiq, tam=5.6, color=SUAVE, ha=ha)

    for i, (nombre, d0, d1, estilo) in enumerate(BLOQUES):
        y = y0 + 6.0 + i * 11.0
        texto(ax, 0, y + 4.0, nombre, tam=6.4, peso="bold")
        xa, xb = dia_a_x(d0), min(dia_a_x(d1 + 1), x_fin)
        caja(ax, xa, y, max(xb - xa, 3.2), 8.0, estilo, radio=0.9, lw=0.8)

    y_f = y_tope + 5.0
    caja(ax, 0, y_f, ANCHO, 21.0, "neutro", lw=0.9)
    texto(ax, 4, y_f + 6.0, "Dos observaciones", tam=7, peso="bold", color=AZUL)
    texto(ax, 4, y_f + 11.5,
          "El bloque 4 no estaba previsto: surgió al detectar que varios análisis "
          "se habían ejecutado sin dejar script.", tam=6)
    texto(ax, 4, y_f + 16.5,
          "Y la redacción ocupa dos tercios del calendario, algo que el "
          "planteamiento inicial subestimaba.", tam=6)

    guardar(fig, "gantt")


# ---------------------------------------------------------------------------
# FIGURA 17 · el encadenamiento de los agentes construidos
# ---------------------------------------------------------------------------
def fig_encadenamiento():
    fig, ax = lienzo(170.0)
    y0 = titulo_figura(
        ax, "encadenamiento",
        "Encadenamiento de los agentes construidos",
        "El componente que encadena los agentes construidos. Ejecutado sobre "
        "2.652 empresas; cada una sale con el motivo de cada decisión.")

    pasos = [
        ("A2", "clasificar el sector", "sector + confianza"),
        ("A3", "puntuar la cuenta", "nota A-E + probabilidad de conversión"),
        ("A5", "emparejar servicio o campaña", "servicio + confianza"),
        ("A5", "redactar el mensaje", "EN COLA · necesita GPU"),
    ]
    cx = ANCHO / 2
    caja(ax, 46.0, y0, 68.0, 13.0, "neutro", lw=0.9)
    texto(ax, cx, y0 + 7.0, "una empresa", tam=7.5, peso="bold", ha="center")
    y = y0 + 13.0

    for ag, tarea, salida in pasos:
        y += 6.0
        flecha(ax, cx, y - 6.0, cx, y)
        caja(ax, 4.0, y, ANCHO - 8.0, 13.0, "construido", lw=0.9)
        texto(ax, 9.0, y + 7.0, ag, tam=8, peso="bold", color="white")
        texto(ax, 21.0, y + 7.0, tarea, tam=7.5, peso="bold", color="white")
        texto(ax, ANCHO - 9.0, y + 7.0, "→ " + salida, tam=5.8,
              color="#BBD6D3", ha="right")
        y += 13.0

    y += 6.0
    flecha(ax, cx, y - 6.0, cx, y)
    caja(ax, 4.0, y, ANCHO - 8.0, 17.0, "destacado", lw=1.0)
    texto(ax, cx, y + 6.5, "una fila de salida con todo", tam=8, peso="bold",
          color=ACENTO, ha="center")
    texto(ax, cx, y + 12.5,
          "2.652 filas · el 10,2 % completa el recorrido · el resto se detiene con su motivo",
          tam=6.2, color=ACENTO, ha="center")

    y += 17.0 + 8.0
    caja(ax, 0, y, ANCHO, 22.0, "neutro", lw=0.9)
    texto(ax, 4, y + 6.0, "Lo que solo se puede medir con la cadena montada", tam=7,
          peso="bold", color=AZUL)
    texto(ax, 4, y + 11.5,
          "La propagación del error. A2 acierta el 51,73 %, pero solo el 7,4 % de "
          "sus fallos llega a cambiar", tam=6)
    texto(ax, 4, y + 16.5,
          "la decisión siguiente. La métrica de un agente dice cuántas veces se "
          "equivoca; la cadena, cuánto importa.", tam=6)

    guardar(fig, "encadenamiento")




# ---------------------------------------------------------------------------
# FIGURA 6 · el recorrido operativo completo
# ---------------------------------------------------------------------------
def fig_recorrido():
    """
    El sistema como se usaria de verdad, con sus dos puertas de entrada.

    La figura 5 muestra QUE fases hay. Esta muestra POR DONDE PASA una
    empresa concreta, en que orden, que decide una persona y que decide un
    modelo. Es la que responde a "y esto como se pone en marcha".
    """
    ALTO = 292.0
    fig, ax = lienzo(ALTO)
    y0 = titulo_figura(
        ax, "recorrido_operativo",
        "Cómo recorre el sistema una empresa, de principio a fin",
        "Dos puertas de entrada y un tramo común. El color indica qué está "
        "construido y qué decide una persona.")

    w = 74.0
    x_i, x_d = 0.0, ANCHO - w
    cx_i, cx_d = x_i + w / 2, x_d + w / 2

    # ---- cabeceras --------------------------------------------------------
    texto(ax, x_i, y0 + 2, "PUERTA 1 · CAMPAÑA", tam=7.5, peso="bold", color=AZUL)
    texto(ax, x_i, y0 + 6.8, "yo elijo a quién escribir", tam=6, color=SUAVE)
    texto(ax, x_d, y0 + 2, "PUERTA 2 · CORREO QUE ENTRA", tam=7.5, peso="bold",
          color=AZUL)
    texto(ax, x_d, y0 + 6.8, "responden a la campaña, o escriben por su cuenta",
          tam=6, color=SUAVE)

    y = y0 + 11.0
    h = 15.0
    paso_v = 19.5

    def bloque(x, yy, alto, estilo, lineas, disc=False):
        caja(ax, x, yy, w, alto, estilo, lw=0.9, discontinua=disc)
        col = ESTILOS[estilo][1]
        for i, (t, tam, peso) in enumerate(lineas):
            texto(ax, x + 4, yy + 5.5 + i * 4.6, t, tam=tam, peso=peso, color=col)

    # ---- columna izquierda · campaña -------------------------------------
    bloque(x_i, y, h, "neutro", [
        ("ENTRA: lista de empresas", 7, "bold"),
        ("+ el brief de la campaña", 6, "normal")])
    y_i = y + h

    y_i += 4.5
    flecha(ax, cx_i, y_i - 4.5, cx_i, y_i)
    bloque(x_i, y_i, h, "construido", [
        ("¿Ya la tengo en el CRM?", 7, "bold"),
        ("por el dominio de su web", 6, "normal")])
    y_i += h

    y_i += 4.5
    flecha(ax, cx_i, y_i - 4.5, cx_i, y_i)
    bloque(x_i, y_i, h + 4.0, "construido", [
        ("Si es NUEVA:", 7, "bold"),
        ("A2 · clasificar el sector", 6, "normal"),
        ("A3 fase 1 · nota de encaje", 6, "normal")])
    y_i += h + 4.0
    texto(ax, x_i + 4, y_i + 3.0,
          "si ya la tengo, se salta este paso", tam=5.2, color=SUAVE,
          cursiva=True)

    y_i += 4.5
    flecha(ax, cx_i, y_i - 4.5, cx_i, y_i)
    bloque(x_i, y_i, h, "simple", [
        ("A5 · emparejar servicio", 7, "bold"),
        ("con el texto de su web", 6, "normal")])
    y_i += h

    y_i += 4.5
    flecha(ax, cx_i, y_i - 4.5, cx_i, y_i)
    bloque(x_i, y_i, h, "destacado", [
        ("A5 · redactar el correo", 7, "bold"),
        ("EN COLA · necesita GPU", 6, "normal")])
    y_i += h

    y_i += 4.5
    flecha(ax, cx_i, y_i - 4.5, cx_i, y_i)
    bloque(x_i, y_i, 11.0, "manual", [("Lo reviso y lo envío", 7, "bold")], disc=True)
    y_i += 11.0

    # ---- columna derecha · correo ----------------------------------------
    bloque(x_d, y, h, "neutro", [
        ("ENTRA: un correo", 7, "bold"),
        ("desde el gestor de correo", 6, "normal")])
    y_d = y + h

    y_d += 4.5
    flecha(ax, cx_d, y_d - 4.5, cx_d, y_d)
    bloque(x_d, y_d, 30.0, "disenado", [
        ("¿QUIÉN ME ESCRIBE?  en este orden:", 6.4, "bold"),
        ("1 · ¿la dirección es un contacto mío?", 5.8, "normal"),
        ("2 · ¿el @dominio está en otro contacto?", 5.8, "normal"),
        ("3 · ¿el @dominio es la web de una cuenta?", 5.8, "normal"),
        ("4 · si no, a revisión manual", 5.8, "normal")])
    texto(ax, x_d + 4, y_d + 27.5,
          "1 y 2 no se pueden medir: no salen datos personales del entorno",
          tam=5.0, color=SUAVE, cursiva=True)
    y_d += 30.0

    y_d += 4.5
    flecha(ax, cx_d, y_d - 4.5, cx_d, y_d)
    bloque(x_d, y_d, h + 4.0, "manual", [
        ("¿Es un cliente potencial?", 7, "bold"),
        ("LO DECIDE UNA PERSONA.", 6, "bold"),
        ("El sistema no crea cuentas solo", 5.6, "normal")], disc=True)
    y_d += h + 4.0

    y_d += 4.5
    flecha(ax, cx_d, y_d - 4.5, cx_d, y_d)
    bloque(x_d, y_d, h + 4.0, "construido", [
        ("Si la cuenta es NUEVA:", 7, "bold"),
        ("A2 · clasificar el sector", 6, "normal"),
        ("A3 fase 1 · nota de encaje", 6, "normal")])
    y_d += h + 4.0

    # el envio de la campaña alimenta la puerta 2
    ax.plot([cx_i, cx_i, x_d - 3.0], [y_i, y_i + 5.0, y_i + 5.0],
            color=LINEA, lw=0.9, ls=(0, (3, 2)), zorder=1)
    flecha(ax, x_d - 3.0, y_i + 5.0, x_d - 3.0, y + h / 2, discontinua=True)
    texto(ax, x_i + 4, y_i + 8.5, "si contestan, entran por la puerta 2",
          tam=5.4, color=SUAVE, cursiva=True)

    # ---- confluencia ------------------------------------------------------
    y_c = max(y_i + 12.0, y_d + 6.0)
    ax.plot([cx_d, cx_d], [y_d, y_c], color=LINEA, lw=0.9, zorder=1)
    ax.plot([cx_i, cx_d], [y_c, y_c], color=LINEA, lw=0.9, zorder=1)
    texto(ax, ANCHO / 2, y_c - 3.5, "a partir de aquí el recorrido es el mismo",
          tam=6, color=SUAVE, ha="center", cursiva=True)

    w_c = 118.0
    x_c = (ANCHO - w_c) / 2
    cx_c = ANCHO / 2
    y_c += 7.0
    flecha(ax, cx_c, y_c - 7.0, cx_c, y_c)

    comunes = [
        ("disenado", "F7 · CUALIFICAR", "rellenar los siete criterios con lo que cuenta"),
        ("simple", "A3 fase 2 · AJUSTAR", "tabla de E13 · sin modelo · alta/media/baja"),
        ("construido", "F8 · ENRUTAR  (A8)", "a qué área técnica va · 80,51 %"),
        ("destacado", "OPORTUNIDAD EN EL CRM", "y el técnico comercial la recibe"),
        ("disenado", "F9 · SEGUIR LA OPORTUNIDAD", "cuándo se cerrará y qué lleva parado"),
    ]
    for i, (est, tit, sub) in enumerate(comunes):
        yy = y_c + i * paso_v
        caja(ax, x_c, yy, w_c, h, est, lw=0.9,
             discontinua=(est in ("disenado", "manual")))
        col = ESTILOS[est][1]
        texto(ax, x_c + 4, yy + 5.5, tit, tam=7.5, peso="bold", color=col)
        texto(ax, x_c + 4, yy + 10.5, sub, tam=6, color=col)
        if i:
            flecha(ax, cx_c, yy - (paso_v - h), cx_c, yy)
    y_f = y_c + (len(comunes) - 1) * paso_v + h

    # ---- leyenda ----------------------------------------------------------
    y_l = y_f + 9.0
    leyenda_estados(ax, 0, y_l, ["construido", "simple", "disenado", "manual"],
                    ancho_item=40)
    texto(ax, 0, y_l + 8.5,
          "Lo que está construido y medido cubre el tramo de la izquierda y el "
          "enrutado. Lo que decide una persona no es",
          tam=6, color=SUAVE)
    texto(ax, 0, y_l + 12.7,
          "un hueco pendiente: son los dos puntos donde los datos desaconsejan "
          "automatizar, y están medidos en 4.6.", tam=6, color=SUAVE)

    guardar(fig, "recorrido_operativo")


if __name__ == "__main__":
    print("\nFIG_arquitectura.py · los diagramas de la memoria")
    print("-" * 60)
    fig_embudo()
    fig_concepto()
    fig_ciclo()
    fig_gantt()
    fig_mapa()
    fig_recorrido()
    fig_taxonomias()
    fig_encadenamiento()
    fig_despliegue()
    print("-" * 60)
    print("Listo.\n")
