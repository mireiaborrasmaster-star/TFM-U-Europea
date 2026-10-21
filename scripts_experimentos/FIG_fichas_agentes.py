# -*- coding: utf-8 -*-
"""
FIG_fichas_agentes.py · figuras 4 a 8 · una ficha por agente
============================================================

QUE GENERA

    fig04_ficha_A2   clasificar el sector de la empresa      (fase F2)
    fig05_ficha_A3   puntuar y priorizar la cuenta           (fase F3)
    fig06_ficha_A5   redactar el correo, o abstenerse        (fase F5)
    fig07_ficha_A6   atender lo que entra                    (fase F6)
    fig08_agentes_disenados   A1, A4 y A9, los que quedaron en diseño

POR QUE TIENEN TODAS LA MISMA FORMA
    Cada ficha se lee de arriba abajo en cuatro tiempos:

        1. LA TIRA DE LAS 11 FASES, con la fase de ese agente resaltada.
           Esto es lo que contextualiza el agente: el lector ve de un vistazo
           en que punto del proceso comercial actua y que va antes y despues,
           sin tener que volver al mapa general de la figura 1.

        2. ENTRA -> PROCESA -> SALE. Un agente es exactamente esto, y decirlo
           asi obliga a que las salidas encajen con las entradas del siguiente.

        3. COMO FUNCIONA. Modelo, datos y las decisiones de diseño que hubo
           que tomar.

        4. QUE SE MIDIO. Las cifras, con su punto de comparacion al lado.
           Una cifra sin referencia no dice nada: por eso donde hay un 51,73 %
           aparece tambien el 13,16 % de responder siempre lo mas comun.

    Repetir la misma estructura en las cinco fichas es deliberado: permite
    comparar agentes entre si y deja a la vista que los agentes disenados
    tienen la casilla de mediciones vacia.

QUE FIGURA ACOMPANA A QUE APARTADO
    fig04 -> 4.6.1      fig05 -> 4.6.2      fig06 -> 4.6.3
    fig07 -> 4.6.6 y capitulo 7        fig08 -> 4.6.6

COMO SE EJECUTA
    python scripts/FIG_fichas_agentes.py

FUENTE DE LAS CIFRAS
    08_BITACORA.md, experimentos E4 a E21. Las cifras estan escritas aqui a
    mano y el script las coteja con la bitacora al final (ver COTEJO).
"""

from fig_comun import (ANCHO, TINTA, SUAVE, LINEA, VERDE, ACENTO, AZUL,
                       caja, texto, flecha, lienzo, guardar, titulo_figura,
                       tira_fases, ESTILOS, NOMBRE_FASE)

# ---------------------------------------------------------------------------
# Las cinco fichas, como datos
# ---------------------------------------------------------------------------
FICHAS = [
    dict(
        agente="A2", fase="F2", estado="construido",
        titulo="Agente A2 · clasificar el sector de la empresa",
        subtitulo="Actúa en F2, sobre la lista bruta de empresas. Todo lo que "
                  "viene después depende de que acierte aquí.",
        entra="el nombre de la empresa\ny el texto de su web",
        procesa="XLM-RoBERTa ajustado\ncon el histórico del CRM",
        sale="uno de 41 sectores\ny la confianza de la predicción",
        como=[
            ("Modelo", "XLM-RoBERTa base · 270 millones de parámetros"),
            ("Datos", "histórico del CRM · 2.652 cuentas de prueba"),
            ("Entrenamiento", "4 épocas con GPU, una sola vez"),
            ("Decisión de diseño", "ponderar por clase sí; cabeza jerárquica no"),
        ],
        medido=[
            ("Acierto", "51,73 %"),
            ("F1-macro", "43,38"),
            ("Suelo medido", "13,16 % · responder siempre lo más común"),
            ("Contraste", "+2,82 sobre el modelo lineal · McNemar p = 0,002"),
        ],
        limite="La ventaja en F1-macro (+1,49) no alcanza significación. No es que "
               "no exista: es que 2.652 casos de prueba no bastan para demostrarla.",
    ),
    dict(
        agente="A3", fase="F3", estado="construido",
        titulo="Agente A3 · puntuar y priorizar la cuenta",
        subtitulo="Actúa en F3, con lo que se sabe de una empresa ANTES de haber "
                  "hablado con ella. Decide a quién se llama primero.",
        entra="la ficha de la empresa\ny el histórico del CRM",
        procesa="bosque aleatorio\nsobre datos de tabla",
        sale="nota A-E y probabilidad\nde conversión",
        como=[
            ("Modelo", "bosque aleatorio · 300 árboles"),
            ("Datos", "cartera completa de cuentas · 709 de prueba"),
            ("Variables", "sector, provincia, tamaño, forma jurídica, zona"),
            ("Excluido a propósito", "«es cliente»: circular respecto al objetivo"),
        ],
        medido=[
            ("AUC", "0,788   (el azar es 0,500)"),
            ("Quintil superior frente al inferior", "14,7 veces más conversión"),
            ("Frente al criterio humano", "el modelo discrimina mejor · p = 0,016"),
            ("Árboles frente a redes", "+7,52 puntos de F1-macro y 8,5× más rápido"),
        ],
        limite="El texto de la web apenas aporta aquí (+1,4 puntos): dice qué hace "
               "una empresa, no cuánto vale como cliente. En A2 valía 22 puntos.",
    ),
    dict(
        agente="A5", fase="F5", estado="simple",
        titulo="Agente A5 · redactar el correo de contacto, o abstenerse",
        subtitulo="Actúa en F5. Recibe un brief de campaña y lo conecta con la "
                  "actividad concreta de cada empresa.",
        entra="el brief de la campaña\ny la web de la empresa",
        procesa="Qwen2.5-7B-Instruct\ncuantizado a 4 bits",
        sale="un borrador de correo\nO una abstención motivada",
        como=[
            ("Modelo", "Qwen2.5-7B-Instruct · 4 bits, ejecutado en Colab"),
            ("Emparejamiento", "representaciones densas · E5-small, 118 M"),
            ("Campaña de prueba", "C01 · Reglamento PPWR de envases"),
            ("Salvaguarda", "puede negarse a escribir si no ve encaje"),
        ],
        medido=[
            ("Personalización", "5,06 %"),
            ("Suelo medido", "1,29 % · el correo real que hoy envía la empresa"),
            ("Contraste", "×3,9 · permutación z = 3,50 · p = 0,001"),
            ("Redundancia entre correos", "0,486 frente a 1,000 del genérico"),
        ],
        limite="Se abstuvo en el 27,5 % de los casos (11 de 40): siete abstenciones "
               "correctas, un error conceptual y tres por texto web defectuoso.",
    ),
    dict(
        agente="A7", fase="F8", estado="construido",
        titulo="Agente A7 · preparar la ficha con la que se traspasa el caso",
        subtitulo="Actúa en F8. El área llega decidida desde A6; aquí se compone "
                  "la ficha que recibe el comercial.",
        entra="la necesidad expresada\npor el cliente",
        procesa="clasificador de tipo\n+ composición del asunto",
        sale="la ficha de traspaso,\ncon su área ya decidida",
        como=[
            ("Tipo de servicio", "entrenado con 4.860 etiquetas humanas"),
            ("El área", "no la decide: llega de A6 · se construyó en 4.6.5"),
            ("Qué lee del correo", "un extracto de 10 términos, no el correo entero"),
            ("Qué NO decide un modelo", "materia y norma, que salen literales del texto"),
        ],
        medido=[
            ("Tipo · acierto", "86,6 % · el diccionario al que sustituye, 22,2 %"),
            ("Tipo · sobre correo largo", "41,5 %; con el extracto, 69,4 %"),
            ("Asunto propuesto", "78 de 105 · fundamentado al 100 % en lo literal"),
            ("Ficha completa", "cuenta + área + asunto en 23 de 105"),
        ],
        limite="Del briefing no se mide acierto: no hay briefing verdadero contra "
               "el que comparar. Se mide que el asunto propuesto salga del texto, "
               "y da el 100 % en la parte literal. Queda pendiente anotar a mano "
               "el tipo de servicio de los 105 mensajes.",
    ),
    dict(
        agente="A6", fase="F6", estado="construido",
        titulo="Agente A6 · atender, cualificar y enrutar lo que entra",
        subtitulo="Actúa en F6 y F7, la puerta del camino de recepción. Cuatro "
                  "piezas sobre 105 mensajes reales.",
        entra="un correo o un formulario\nrecibido por la empresa",
        procesa="identidad + norma citada\n+ enrutado + ¿es comercial?",
        sale="enrutado al área técnica,\no a revisión con el motivo",
        como=[
            ("1 · identidad", "el @dominio contra DOS campos de la cuenta"),
            ("2 · norma", "diccionario norma → área, cierto por definición"),
            ("3 · enrutado", "clasificador de área, medido sobre correo real"),
            ("4 · comercial", "clasificador sobre etiquetado a mano de la autora"),
        ],
        medido=[
            ("Identidad resuelta", "53 de 98 · 54,1 % · gana el dominio de correo"),
            ("Enrutado sobre correo real", "79,5 % · frente al 80,51 % sobre el asunto"),
            ("Comercial / no comercial", "AUC 0,919 · [0,828, 0,980]"),
            ("Resuelve sin persona", "45 de 105 · 42,9 %"),
        ],
        limite="Enruta bien 79 de 105, pero solo 45 son de cuentas "
               "que ya existen: por D19 el resto necesita que una persona decida "
               "el alta. Y el 12 % de las cuentas no tiene ninguno de "
               "los dos campos de dominio, así que no hay forma de encontrarlas.",
    ),
    dict(
        agente="A8", fase="F9", estado="construido",
        titulo="Agente A8 · estimar si la oportunidad se va a ganar",
        subtitulo="Actúa en F9, con la oportunidad ya registrada. Compite "
                  "contra la probabilidad que declara la persona.",
        entra="la oportunidad registrada\ny el historial de la cuenta",
        procesa="bosque aleatorio\nsin ninguna variable monetaria",
        sale="probabilidad de cierre\ny aviso de atasco",
        como=[
            ("Modelo", "bosque aleatorio · 400 árboles · 17 variables"),
            ("Datos", "3.833 oportunidades cerradas · sin importes"),
            ("Partición", "temporal · se aparta el trimestre censurado"),
            ("Historial", "calculado hacia atrás: nunca ve su propio futuro"),
        ],
        medido=[
            ("Acierto al registrar", "73,9 % · suelo 56,7 %"),
            ("AUC", "0,811 · [0,777, 0,840]"),
            ("Ordenando, contra la persona", "+0,034 · p = 0,22 · empata"),
            ("Calibrando, contra la persona", "+0,0258 · p = 0,002 · gana"),
        ],
        limite="Ordena igual que la persona; donde gana es en que su número "
               "significa lo que dice. El contraste es de un solo trimestre, "
               "y no mide si usarlo aumenta las ventas: mide si ordena.",
    ),
]


# ---------------------------------------------------------------------------
# El dibujo de una ficha
# ---------------------------------------------------------------------------
def ficha(d):
    ALTO = 152.0
    fig, ax = lienzo(ALTO)
    clave = f"ficha_{d['agente']}"
    y = titulo_figura(ax, clave, d["titulo"], d["subtitulo"])

    # --- 1. la tira de las once fases ------------------------------------
    texto(ax, 0, y + 1.5, "DÓNDE ACTÚA DENTRO DEL PROCESO", tam=6, peso="bold",
          color=AZUL)
    y += 5.0
    y = tira_fases(ax, 0, y, d["fase"], estilo_activa=d["estado"]) + 3.0
    _, _, _, etiq = ESTILOS[d["estado"]]
    texto(ax, 0, y + 1.0,
          f"{d['fase']} · {NOMBRE_FASE[d['fase']].replace(chr(10), ' ')} — {etiq}",
          tam=6, color=SUAVE, cursiva=True)
    y += 8.0

    # --- 2. entra -> procesa -> sale --------------------------------------
    w = (ANCHO - 2 * 9.0) / 3
    h = 24.0
    for i, (rot, txt, est) in enumerate([
            ("ENTRA", d["entra"], "neutro"),
            ("PROCESA", d["procesa"], d["estado"]),
            ("SALE", d["sale"], "neutro")]):
        x = i * (w + 9.0)
        caja(ax, x, y, w, h, est, radio=1.2,
             discontinua=(est == "disenado"))
        col = ESTILOS[est][1]
        texto(ax, x + 4, y + 5.5, rot, tam=6, peso="bold",
              color=col if est != "neutro" else AZUL)
        ax.text(x + w / 2, y + 15.0, txt, fontsize=6.6, color=col,
                ha="center", va="center", linespacing=1.5, zorder=4)
        if i:
            flecha(ax, x - 9.0, y + h / 2, x, y + h / 2, lw=1.0)
    y += h + 10.0

    # --- 3 y 4. como funciona / que se midio ------------------------------
    wc = (ANCHO - 8.0) / 2
    h_bloque = 42.0
    for j, (tit, filas, color_tit) in enumerate([
            ("CÓMO FUNCIONA", d["como"], AZUL),
            ("QUÉ SE MIDIÓ", d["medido"], VERDE)]):
        x = j * (wc + 8.0)
        caja(ax, x, y, wc, h_bloque, "neutro", lw=0.8)
        texto(ax, x + 4, y + 6.0, tit, tam=6.5, peso="bold", color=color_tit)
        for i, (k, v) in enumerate(filas):
            yy = y + 13.5 + i * 7.2
            texto(ax, x + 4, yy, k, tam=5.5, color=SUAVE)
            texto(ax, x + 4, yy + 3.8, v, tam=6.2, peso="bold")
    y += h_bloque + 7.0

    # --- el limite, siempre declarado ------------------------------------
    caja(ax, 0, y, ANCHO, 17.0, "destacado", lw=0.9)
    texto(ax, 4, y + 5.5, "LO QUE ESTA FICHA NO DICE", tam=6, peso="bold",
          color=ACENTO)
    # el limite se parte en dos lineas por la mitad, buscando un espacio
    t = d["limite"]
    corte = t.rfind(" ", 0, int(len(t) * 0.52))
    texto(ax, 4, y + 10.5, t[:corte], tam=6)
    texto(ax, 4, y + 14.5, t[corte + 1:], tam=6)

    guardar(fig, clave)


# ---------------------------------------------------------------------------
# FIGURA 8 · los agentes que quedaron en diseño
# ---------------------------------------------------------------------------
DISENADOS = [
    ("A1", "F1", "Buscar empresas",
     "Proponer empresas nuevas por parecido con la cartera actual, usando "
     "representaciones densas.",
     "No hay fuente de empresas fuera del CRM con la que probarlo."),
    ("A4", "F4", "Encontrar a la persona",
     "Extraer nombres y cargos de texto y clasificar el papel de cada uno en "
     "la decisión de compra.",
     "Trata datos personales de terceros: exige una base legal que el trabajo "
     "no podía resolver."),
    ("A9", "F10", "Aprender y ajustar",
     "Detectar que un modelo se ha quedado obsoleto y avisar de que hay que "
     "reentrenarlo.",
     "Requiere el sistema en producción durante meses. No hay nada que "
     "vigilar todavía."),
]


def figura_8():
    ALTO = 194.0
    fig, ax = lienzo(ALTO)
    y = titulo_figura(
        ax, "agentes_disenados", "Los agentes que quedaron en diseño, y por qué",
        "Cada renuncia tiene un motivo concreto. A6 se construyó después y "
        "tiene ficha propia, en la figura 19.")

    h = 25.0
    for i, (ag, fase, nombre, hace, por_que) in enumerate(DISENADOS):
        yy = y + i * (h + 5.0)
        caja(ax, 0, yy, ANCHO, h, "disenado", lw=0.9, discontinua=True)
        texto(ax, 5, yy + 6.5, f"{ag}", tam=8.5, peso="bold", color=AZUL)
        texto(ax, 26, yy + 6.5, f"{nombre}", tam=8.5, peso="bold")
        texto(ax, ANCHO - 5, yy + 6.5, f"fase {fase}", tam=6, color=SUAVE,
              ha="right", cursiva=True)
        texto(ax, 5, yy + 13.5, "Qué haría", tam=5.5, color=SUAVE)
        texto(ax, 26, yy + 13.5, hace, tam=6.2)
        texto(ax, 5, yy + 19.5, "Por qué no", tam=5.5, color=ACENTO)
        # el motivo puede ocupar dos lineas
        corte = por_que.rfind(" ", 0, 95) if len(por_que) > 95 else len(por_que)
        texto(ax, 26, yy + 19.5, por_que[:corte], tam=6.2, color=ACENTO)
        if corte < len(por_que):
            texto(ax, 26, yy + 23.8, por_que[corte + 1:], tam=6.2, color=ACENTO)

    y_fin = y + len(DISENADOS) * (h + 5.0) + 2.0
    caja(ax, 0, y_fin, ANCHO, 17.0, "destacado", lw=0.9)
    texto(ax, 4, y_fin + 6.0,
          "Ninguno se dejó por falta de tiempo: a cada uno le falta algo concreto.",
          tam=7, peso="bold", color=ACENTO)
    texto(ax, 4, y_fin + 12.5,
          "Es una distinción que conviene sostener en la defensa: son líneas de trabajo "
          "abiertas, no tareas pendientes.", tam=6)

    guardar(fig, "agentes_disenados")


if __name__ == "__main__":
    print("\nFIG_fichas_agentes.py · figuras 4 a 8")
    print("-" * 60)
    for d in FICHAS:
        ficha(d)
    figura_8()
    print("-" * 60)
    print("Listo.\n")
