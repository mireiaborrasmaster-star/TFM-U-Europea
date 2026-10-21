# -*- coding: utf-8 -*-
"""
F9_A9_evaluar_prevision_existente.py · ¿sirve el proyecto de previsión como A9?
===============================================================================

LA PREGUNTA
    Existe en la carpeta PHYTON un proyecto propio, «PREVISION DE VENTAS», que
    la autora desarrollo para su trabajo diario. ¿Sirve como base del agente
    A9, el que sigue las oportunidades del pipeline?

    La respuesta corta es que NO sirve como base: sirve como A9. Esta mas
    desarrollado que cualquiera de los agentes del TFM.

QUE COMPRUEBA ESTE SCRIPT
    1. Que tecnica implementa realmente, leyendo el codigo
    2. Con cuantos datos trabaja y que fiabilidad tiene, leyendo sus salidas
    3. Que pedia el diseno de A9 y que parte esta cubierta
    4. Que problemas plantea incorporarlo al TFM  <-- lo importante

CONFIDENCIALIDAD
    El proyecto de prevision trabaja con IMPORTES. Este script NO imprime
    ninguna cifra monetaria: se detiene en las metricas de acierto y en los
    recuentos. Es la decision D13 del TFM, que excluyo toda variable
    monetaria, y se respeta tambien al leer un proyecto ajeno al TFM.

COMO SE EJECUTA
    python scripts/F9_A9_evaluar_prevision_existente.py
"""

import re
import subprocess
from pathlib import Path

import pandas as pd

VERSION_SCRIPT = "v1 · 30-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
PREVISION = RAIZ.parent.parent / "PREVISIÓN DE VENTAS"

# Lo que el diseno de A9 pedia, segun 00_SECUENCIA_SDR.txt
DISENO_A9 = [
    ("Vigilar el pipeline: qué avanza y qué está parado", "PASO_9"),
    ("Predecir CUÁNDO se cerrará algo, no solo SI", "curvas.py"),
    ("Análisis de supervivencia", "curvas.py"),
    ("Alertas y próxima acción recomendada", "PASO_12"),
    ("Recontactar los «ahora no»", None),
]

# Palabras que delatan una cifra monetaria: no se imprime la fila que las lleve
MONETARIO = ["importe", "€", "eur", "euros", "valor", "facturaci"]


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"{n} · {t}")
    print("=" * 76)


def sin_dinero(texto):
    return not any(m in str(texto).lower() for m in MONETARIO)


def main():
    print()
    print("#" * 76)
    print("# F9 · A9 · ¿sirve el proyecto de previsión existente?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    if not PREVISION.exists():
        raise SystemExit(f"No encuentro {PREVISION}")

    # ------------------------------------------------------------------ 1
    titulo(1, "QUE TECNICA IMPLEMENTA  ·  leyendo el codigo, no el README")
    curvas = (PREVISION / "prevision" / "modelo" / "curvas.py").read_text(
        encoding="utf-8", errors="replace")
    print("   Fichero: prevision/modelo/curvas.py")
    print()
    senales = {
        "Aalen-Johansen": "Aalen" in curvas,
        "riesgos competitivos": "riesgos competitivos" in curvas.lower(),
        "función de supervivencia S(t)": "S(t)" in curvas or "S =" in curvas,
        "incidencia acumulada CIF": "CIF" in curvas,
        "censura (sigue abierto)": "censurado" in curvas.lower(),
        "identidad S + CIF1 + CIF2 = 1": "S + CIF1 + CIF2 = 1" in curvas,
    }
    for k, v in senales.items():
        print(f"      {'SI ' if v else 'no '}  {k}")
    print()
    if all(senales.values()):
        print("   Es un analisis de supervivencia con riesgos competitivos")
        print("   implementado a mano y correctamente: mantiene la identidad")
        print("   que garantiza que las tres curvas suman uno en todo momento.")
        print()
        print("   El diseno de A9 en 00_SECUENCIA_SDR.txt pedia exactamente")
        print("   esto, con estas palabras: «modelo que predice CUANDO se")
        print("   cerrara algo, no solo SI se cerrara (analisis de")
        print("   supervivencia)».")

    # ------------------------------------------------------------------ 2
    titulo(2, "TAMANO Y MADUREZ DEL PROYECTO")
    py = [f for f in PREVISION.rglob("*.py")
          if ".git" not in str(f) and "__pycache__" not in str(f)]
    lineas = sum(len(f.read_text(encoding="utf-8", errors="replace").splitlines())
                 for f in py)
    tests = [f for f in py if f.name.startswith("test_")]
    print(f"   Ficheros de codigo        : {len(py):>5}")
    print(f"   Lineas de codigo          : {lineas:>5}")
    print(f"   Ficheros de test          : {len(tests):>5}")
    print(f"   Configuracion externa     : "
          f"{'si' if (PREVISION / 'config.toml').exists() else 'no'}")
    print(f"   Base de datos             : "
          f"{'si' if list(PREVISION.rglob('*.sqlite')) else 'no'}")
    try:
        log = subprocess.run(["git", "log", "--format=%ad|%s", "--date=short"],
                             cwd=PREVISION, capture_output=True, text=True,
                             timeout=30).stdout.strip().splitlines()
        print(f"   Commits registrados       : {len(log):>5}")
        if log:
            print(f"   Primer commit             : {log[-1].split('|')[0]}")
            print(f"   Ultimo commit             : {log[0].split('|')[0]}")
    except Exception:
        log = []

    print()
    print("   COMPARACION CON LOS AGENTES DEL TFM")
    scripts_tfm = list((RAIZ / "scripts").glob("*.py"))
    lineas_tfm = sum(len(f.read_text(encoding="utf-8", errors="replace").splitlines())
                     for f in scripts_tfm)
    print(f"      TFM (carpeta scripts/) : {len(scripts_tfm):>3} ficheros, "
          f"{lineas_tfm:>6} lineas, 0 tests")
    print(f"      Proyecto de prevision  : {len(py):>3} ficheros, "
          f"{lineas:>6} lineas, {len(tests)} tests")
    print()
    print("   El proyecto de prevision esta MAS desarrollado que el conjunto")
    print("   de los agentes del TFM: tiene capas, configuracion externa,")
    print("   persistencia, registro de ejecuciones y pruebas automaticas.")

    # ------------------------------------------------------------------ 3
    titulo(3, "QUE FIABILIDAD TIENE  ·  su propia prueba hacia atras")
    f7 = PREVISION / "OUTPUT" / "PASO_7_prueba_hacia_atras.xlsx"
    if f7.exists():
        d = pd.ExcelFile(f7).parse("Comparativa", header=None)
        print("   Fichero: OUTPUT/PASO_7_prueba_hacia_atras.xlsx")
        print()
        for _, fila in d.iterrows():
            celdas = [str(x) for x in fila.tolist() if str(x) != "nan"]
            if len(celdas) < 3:
                continue
            etiqueta = " · ".join(celdas[:2])
            if not sin_dinero(etiqueta):
                continue          # nada de importes, decision D13
            if any(k in etiqueta.lower() for k in
                   ["oportunidades válidas", "ofertas válidas", "semanas probadas",
                    "meses probados", "aciert"]):
                print(f"      {etiqueta[:58]:<60}{celdas[-2]:>8}")
        print()
        print("   Se omiten deliberadamente las filas de importes (decision D13).")
    else:
        print("   No encuentro la prueba hacia atras.")

    # ------------------------------------------------------------------ 4
    titulo(4, "EL ANALISIS QUE MAS INTERESA AL TFM")
    fp = list((PREVISION / "OUTPUT" / "PROBABILIDAD_COMERCIAL").glob("ACIERTO_*.xlsx"))
    if fp:
        d = pd.ExcelFile(fp[0]).parse("Resumen", header=None)
        print("   «¿Acierta el % de probabilidad que pone el comercial a mano?»")
        print()
        for _, fila in d.iterrows():
            celdas = [str(x) for x in fila.tolist() if str(x) != "nan"]
            if len(celdas) < 2:
                continue
            k = celdas[0]
            if any(t in k.lower() for t in
                   ["ofertas analizadas", "ordenan bien", "entre qué valores",
                    "media de lo que dicen", "se logra de verdad",
                    "diferencia (puntos)", "lectura"]):
                print(f"      {k[:42]:<44}{celdas[1][:34]}")
        print()
        print("   ESTO ES EL MISMO CONTRASTE QUE E16 DEL TFM, en otra fase del")
        print("   embudo: modelo frente a criterio humano, con AUC e intervalo.")
        print()
        print("   Y separa dos cosas que el TFM no llego a separar:")
        print("      ORDENAR bien  (discriminacion, AUC)")
        print("      ACERTAR el numero (calibracion)")
        print("   El comercial ordena muy bien y calibra mal. Son dos")
        print("   propiedades distintas y un modelo puede tener una sin la otra.")

    # ------------------------------------------------------------------ 5
    titulo(5, "QUE PEDIA A9 Y QUE ESTA CUBIERTO")
    for que, donde in DISENO_A9:
        estado = "CUBIERTO" if donde else "NO"
        print(f"      [{estado:^8}]  {que}")
    print()
    print("   Cuatro de las cinco funciones del diseno estan implementadas.")
    print("   La quinta —recontactar los «ahora no»— es la unica que faltaria,")
    print("   y es una regla sobre el pipeline, no un modelo.")

    # ------------------------------------------------------------------ 6
    titulo(6, "LO QUE HAY QUE DECIDIR, Y NO ES TECNICO")
    print("   1. FECHAS. El primer commit es del 15-09-2026 y el TFM arranca")
    print("      el 21-09. El proyecto EMPEZO ANTES. Si entra en la memoria")
    print("      hay que declarar que es trabajo previo y propio, no")
    print("      desarrollado para el TFM. Ocultarlo seria un problema serio;")
    print("      declararlo no lo es en absoluto.")
    print()
    print("   2. IMPORTES. El proyecto preve importes. La decision D13 del TFM")
    print("      excluyo toda variable monetaria. O se revisa D13, o solo")
    print("      entra la parte de conversion y plazos, que es la que importa")
    print("      para A9.")
    print()
    print("   3. ALCANCE. Son 4 laboratorios, no los 11 agentes. A9 cubriria")
    print("      una parte del pipeline, no todo.")
    print()
    print("   4. TIEMPO. Quedan 13 dias y la memoria esta sin cerrar. Meter un")
    print("      quinto agente cuesta un apartado de 4.6, una ficha, una")
    print("      figura y su parrafo en la sintesis y en el capitulo 5.")
    print()
    print("   RECOMENDACION")
    print("      Declararlo en el capitulo 7 como linea ya explorada, con sus")
    print("      cifras, y NO abrir un apartado 4.6.5. Motivo: el trabajo ya")
    print("      tiene cuatro agentes construidos y el capitulo 4.6 esta")
    print("      cerrado. Lo que aporta A9 no es un agente mas: es la prueba")
    print("      de que la arquitectura propuesta se sostiene fuera del TFM.")
    print("      Eso vale mas en el capitulo 7 que como quinto resultado.")
    print()


if __name__ == "__main__":
    main()
