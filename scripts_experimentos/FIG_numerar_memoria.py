# -*- coding: utf-8 -*-
"""
FIG_numerar_memoria.py · pone los marcadores de figura al dia
=============================================================

QUE HACE
    La memoria ya tenia marcadores `[FIGURA n]` escritos a mano cuando solo
    habia previstas nueve figuras. Al generarse dieciocho, los numeros se
    desordenan: hay figuras nuevas que van EN MEDIO de las que ya estaban.

    Este script renumera los marcadores existentes y coloca los nuevos en su
    sitio, de forma que el numero del marcador coincida con el numero que
    lleva dibujado la figura y con el nombre del fichero.

POR QUE UN SCRIPT Y NO A MANO
    Porque hay que hacerlo dos veces: ahora y cuando se anada el orquestador
    (que trae figura propia). Renumerar dieciocho marcadores a mano en cinco
    ficheros es justo el tipo de tarea donde se cuela un error que nadie ve
    hasta la impresion.

COMO SE EJECUTA
    python scripts/FIG_numerar_memoria.py            ver que haria
    python scripts/FIG_numerar_memoria.py --aplicar  escribirlo

    Sin --aplicar no toca nada: solo dice que cambiaria.

ES IDEMPOTENTE
    Ejecutarlo dos veces no hace dano. Si los marcadores ya estan bien, no
    cambia nada y lo dice.
"""

import argparse
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MEMORIA = RAIZ / "memoria"

PIE = "Elaboración propia."

# ---------------------------------------------------------------------------
# Paso 1 · renumerar los marcadores que ya existian
# ---------------------------------------------------------------------------
# fichero -> [(marcador viejo, marcador nuevo)]
RENUMERAR = {
    "CAP4_1_planificacion.md": [("[FIGURA 2b]", "[FIGURA 3]"),
                                ("[FIGURA 2c]", "[FIGURA 4]")],
    "CAP4_2_solucion.md":      [("[FIGURA 3]", "[FIGURA 5]"),
                                ("[FIGURA 4]", "[FIGURA 5bis]")],
    "CAP4_6_resultados.md":    [("[FIGURA 5]", "[FIGURA 8]"),
                                ("[FIGURA 6]", "[FIGURA 10]"),
                                ("[FIGURA 7]", "[FIGURA 13]")],
    "CAP7_futuras_lineas.md":  [("[FIGURA 8]", "[FIGURA 17]"),
                                ("[FIGURA 9]", "[FIGURA 18]")],
}

# ---------------------------------------------------------------------------
# Paso 2 · los pies definitivos, con el fichero de cada figura
# ---------------------------------------------------------------------------
PIES = {
    1:  ("fig01_embudo_sdr",
         "Posición del SDR en el embudo de ventas B2B y transición hacia el "
         "ejecutivo de cuentas."),
    2:  ("fig02_concepto_multiagente",
         "Un sistema multi-agente encadenado: la salida de cada agente es la "
         "entrada del siguiente, y el error se propaga con ella."),
    3:  ("fig03_ciclo_iterativo",
         "Ciclo de trabajo iterativo seguido en el proyecto."),
    4:  ("fig04_gantt", "Cronograma del proyecto."),
    5:  ("fig05_mapa_fases_agentes",
         "Arquitectura del sistema: las once fases del proceso comercial, sus "
         "dos caminos de entrada, el agente que automatiza cada una y el "
         "estado en que quedó cada agente."),
    6:  ("fig06_recorrido_operativo",
         "Recorrido operativo del sistema: las dos puertas de entrada, el tramo "
         "común y el punto en que decide una persona."),
    7:  ("fig07_dos_taxonomias",
         "Las dos taxonomías del sistema y la relación de muchos a muchos entre ellas."),
    8:  ("fig08_ficha_A2",
         "Agente A2: qué recibe, qué hace y qué entrega, situado dentro de las once fases."),
    9:  ("fig09_comparativa_A2",
         "Comparativa de métodos de clasificación sectorial: aciertos y F1-macro."),
    10: ("fig10_ficha_A3",
         "Agente A3: qué recibe, qué hace y qué entrega, situado dentro de las once fases."),
    11: ("fig11_deciles_conversion",
         "Conversión real por decil de puntuación del modelo de priorización."),
    12: ("fig12_arboles_vs_redes",
         "Modelos de árboles frente a redes neuronales sobre los mismos datos de tabla."),
    13: ("fig13_ficha_A5",
         "Agente A5: qué recibe, qué hace y qué entrega, situado dentro de las once fases."),
    14: ("fig14_personalizacion",
         "Personalización de los correos generados frente al correo genérico real y al "
         "control por permutación."),
    15: ("fig15_cuarenta_generaciones",
         "Resultado de las cuarenta generaciones de la campaña: correos escritos y "
         "abstenciones, clasificados uno a uno."),
    16: ("fig16_ficha_A7",
         "Agente A7: qué recibe, qué hace y qué entrega, situado dentro de las once fases."),
    17: ("fig17_encadenamiento",
         "El orquestador: encadenamiento de los agentes construidos y resultado de su "
         "ejecución sobre 2.652 empresas."),
    18: ("fig18_embudo_orquestador",
         "Embudo del recorrido completo y propagación del error de clasificación a lo "
         "largo de la cadena."),
    19: ("fig19_ficha_A6",
         "Agente A6: qué recibe, qué hace y qué entrega, situado dentro de las once fases."),
    20: ("fig20_ficha_A8",
         "Agente A8: qué recibe, qué hace y qué entrega, situado dentro de las once fases."),
    21: ("fig21_agentes_disenados",
         "Los agentes que quedaron en diseño y el motivo concreto de cada renuncia."),
    22: ("fig22_despliegue_dos_circuitos",
         "Arquitectura de despliegue en dos circuitos."),
}


def pie(n):
    fichero, titulo = PIES[n]
    return f"`[FIGURA {n}]` *{titulo}* {PIE}  \n`figuras/{fichero}.png`"


# ---------------------------------------------------------------------------
# Paso 3 · las figuras nuevas y donde se insertan
# ---------------------------------------------------------------------------
# fichero -> [(texto ancla, numero de figura, antes/despues)]
INSERTAR = {
    "CAP4_2_solucion.md": [
        ("### La correspondencia con los agentes", 6, "despues"),
        ("## 4.2.2 Las dos taxonomías, y por qué no se pueden mezclar", 7, "despues"),
    ],
    "CAP4_6_resultados.md": [
        ("## 4.6.1 A2 · Clasificación sectorial de empresas", 8, "despues"),
        ("## 4.6.2 A3 · Priorización de cuentas", 10, "despues"),
        ("### RQ2b · Elección de familia de modelo sobre datos tabulares", 12, "despues"),
        ("## 4.6.3 A5 · Contacto personalizado", 13, "despues"),
        ("### La decisión de abstenerse, y dónde falla", 15, "despues"),
        ("## 4.6.4 A8 · Enrutado al área técnica", 16, "despues"),
        ("## 4.6.5 A0 · El sistema secuencial", [17, 18], "despues"),
        ("## 4.6.8 A9 · Seguimiento de oportunidades", 20, "despues"),
        ("## 4.6.9 Agentes diseñados y no construidos", 21, "despues"),
    ],
    "CAP2_antecedentes.md": [],
    "CAP4_1_planificacion.md": [],
    "CAP7_futuras_lineas.md": [],
}


def renumerar_por_nombre(texto, notas):
    """
    Pone al dia el numero de cada figura BUSCANDOLA POR SU NOMBRE.

    Los pies de la memoria llevan debajo la linea `figuras/figNN_clave.png`.
    La clave no cambia nunca; el numero si, cada vez que se inserta una figura
    en medio. Asi que se busca la clave, se mira que numero le toca ahora y se
    corrigen las dos cosas: el marcador y el nombre del fichero.

    Es inmune al orden: da igual que un numero viejo coincida con uno nuevo.
    """
    clave_a_numero = {f.split("_", 1)[1]: n for n, (f, _) in PIES.items()}
    # se localizan todos los pies existentes y se anota que hay que cambiar
    pendientes = []
    for m in re.finditer(r"`\[FIGURA (\d+)\]`(.*?)`figuras/fig(\d\d)_([a-zA-Z0-9_]+)\.png`",
                         texto, re.S):
        num_marca, medio, num_fich, clave = m.group(1), m.group(2), m.group(3), m.group(4)
        correcto = clave_a_numero.get(clave)
        if correcto is None:
            notas.append(f"AVISO: la figura «{clave}» ya no está en la tabla")
            continue
        if int(num_marca) == correcto and int(num_fich) == correcto:
            continue
        pendientes.append((m.group(0), clave, correcto, medio, int(num_marca)))

    for viejo, clave, correcto, medio, antes in pendientes:
        nuevo = (f"`[FIGURA {correcto}]`{medio}"
                 f"`figuras/fig{correcto:02d}_{clave}.png`")
        texto = texto.replace(viejo, nuevo, 1)
        notas.append(f"figura «{clave}»: {antes} -> {correcto}")
    return texto


def procesar(ruta, aplicar):
    texto = ruta.read_text(encoding="utf-8")
    original = texto
    nombre = ruta.name
    notas = []

    # paso 1 · renumerar, en dos tiempos para que no colisionen entre si
    #
    # OJO: solo la primera vez. Un fichero que ya lleva lineas `figuras/figNN`
    # esta renumerado, y volver a aplicar las reglas convertiria un marcador
    # NUEVO en otro numero. Paso por ahi la primera vez que lo ejecute.
    ya_renumerado = "`figuras/fig" in texto
    if ya_renumerado:
        texto = renumerar_por_nombre(texto, notas)
    for i, (viejo, _) in enumerate([] if ya_renumerado
                                   else RENUMERAR.get(nombre, [])):
        if viejo in texto:
            texto = texto.replace(viejo, f"@@TMP{i}@@")
    for i, (viejo, nuevo) in enumerate([] if ya_renumerado
                                       else RENUMERAR.get(nombre, [])):
        if f"@@TMP{i}@@" in texto:
            texto = texto.replace(f"@@TMP{i}@@", nuevo)
            notas.append(f"renumerado {viejo} -> {nuevo}")

    # el antiguo marcador 4 de 4.2 ya no hace falta: la figura 5 lo cubre
    if nombre == "CAP4_2_solucion.md":
        patron = re.compile(
            r"`\[FIGURA 5bis\]`[^\n]*\n(?:[^\n]*\n)?", re.MULTILINE)
        if patron.search(texto):
            texto = patron.sub(
                "La figura 5 recoge esa correspondencia completa.\n", texto)
            notas.append("el antiguo [FIGURA 4] se sustituye por una remisión "
                         "a la figura 5 (era la misma figura dos veces)")

    # paso 2 · reescribir el pie de cada marcador con su fichero
    for n in PIES:
        marca = f"`[FIGURA {n}]`"
        if marca not in texto:
            continue
        if f"figuras/{PIES[n][0]}.png" in texto:
            continue
        patron = re.compile(re.escape(marca) + r"[^\n]*")
        texto = patron.sub(lambda m: pie(n).replace("\\", "\\\\"), texto, count=1)
        notas.append(f"pie de la figura {n} actualizado con su fichero")

    # paso 2bis · limpiar restos de pies antiguos
    # Algunos pies ocupaban DOS lineas. Al reescribir la primera, la segunda
    # se queda huerfana debajo del nombre del fichero. Se reconoce porque
    # termina en asterisco y empieza en minuscula o con una raya.
    huerfana = re.compile(
        r"(`figuras/fig\d\d_[a-zA-Z0-9_]+\.png`\n)"
        r"([a-zá-úñ—][^\n]*\*)\n")
    while huerfana.search(texto):
        texto = huerfana.sub(r"\1", texto, count=1)
        notas.append("eliminada la segunda línea de un pie de figura antiguo")

    # paso 3 · insertar las figuras nuevas
    for ancla, ns, donde in INSERTAR.get(nombre, []):
        # un ancla puede traer una figura o varias, en orden
        ns = ns if isinstance(ns, list) else [ns]
        ns = [n for n in ns if f"[FIGURA {n}]" not in texto]
        if not ns:
            continue
        if ancla not in texto:
            notas.append(f"AVISO: no encuentro el ancla de la(s) figura(s) "
                         f"{ns}: {ancla[:44]}…")
            continue
        bloque = "".join("\n\n" + pie(n) for n in ns)
        texto = texto.replace(ancla, ancla + bloque, 1)
        notas.append(f"insertada(s) la(s) figura(s) {ns} tras «{ancla[:44]}…»")

    if texto != original and aplicar:
        ruta.write_text(texto, encoding="utf-8")
    return notas, texto != original


def limpiar_huerfanas(aplicar):
    """
    Borra los ficheros de figura que ya no corresponden a ninguna entrada de
    la tabla.

    Al renumerar, `fig18_encadenamiento.png` pasa a llamarse
    `fig16_encadenamiento.png`. El antiguo se queda ahi, con un numero que ya
    es de otra figura, y es exactamente el fichero que uno acaba pegando en
    Word por error. Se van.
    """
    figuras = RAIZ / "figuras"
    if not figuras.exists():
        return
    validos = {f"fig{n:02d}_{f.split('_', 1)[1]}" for n, (f, _) in PIES.items()}
    sobran = [x for x in sorted(figuras.glob("fig*")) if x.stem not in validos]
    if not sobran:
        return
    print()
    print("   Ficheros de figura que ya no corresponden a ninguna figura:")
    for x in sobran:
        print(f"      {'borrado  ' if aplicar else 'sobra    '}{x.name}")
        if aplicar:
            x.unlink()
    if not aplicar:
        print("   (se borran al lanzarlo con --aplicar)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true",
                    help="escribir los cambios; sin esto solo se muestran")
    a = ap.parse_args()

    print()
    print("=" * 74)
    print("FIG_numerar_memoria.py" + ("  ·  APLICANDO" if a.aplicar
                                      else "  ·  simulacion, no escribe nada"))
    print("=" * 74)
    total = 0
    for ruta in sorted(MEMORIA.glob("CAP*.md")):
        notas, cambiado = procesar(ruta, a.aplicar)
        if notas:
            print(f"\n{ruta.name}")
            for n in notas:
                print(f"   · {n}")
            total += len(notas)
    limpiar_huerfanas(a.aplicar)

    print()
    if total == 0:
        print("   Nada que cambiar: los marcadores ya estan al dia.")
    elif not a.aplicar:
        print(f"   {total} cambio(s). Vuelve a lanzarlo con --aplicar.")
    else:
        print(f"   {total} cambio(s) escritos.")
    print()


if __name__ == "__main__":
    main()
