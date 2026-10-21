"""
CONSTRUCCION DE LOS PAQUETES PARA COLAB
=======================================
Genera los ficheros .zip que se suben a Google Colab, con los scripts, el
catalogo, los briefs y los datos que cada cuaderno necesita.

POR QUE EXISTE
--------------
Los paquetes se construian a mano cada vez, lo que tiene dos problemas: se
olvida algun fichero, y cuando cambia un nombre de script el paquete queda
desincronizado con la carpeta de trabajo. Ocurrio al renombrar los scripts el
29-09-2026: los .zip seguian llevando los nombres viejos dentro.

QUE INCLUYE Y QUE NO
--------------------
De los datos de cuentas se incluyen SOLO las filas con texto web y SOLO las
columnas que A5 usa. Las columnas input_nombre, input_texto e input_completo
son copias del texto preparadas para el clasificador de A2 y triplicarian el
tamano del paquete sin aportar nada aqui.

El texto web se incluye COMPLETO, sin truncar. Es deliberado: el control por
permutacion calcula el suelo de la metrica sobre el texto entero, y truncarlo
daria un suelo distinto al que se obtiene en local. Los numeros dejarian de ser
comparables.

Uso:
    python scripts/PREP_paquete_colab.py
    python scripts/PREP_paquete_colab.py --paquete campana
"""

import argparse
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

VERSION_SCRIPT = "v1 · 29-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
DERIVADO = RAIZ / "datos" / "02_derivado"

# Solo lo que A5 necesita. Ver la nota de la cabecera sobre las columnas input_*.
COLUMNAS = ["empresa", "empresa_clave", "url", "provincia", "sector",
            "sector_agr", "subsector", "web_text", "tiene_texto"]

PAQUETES = {
    "a5": {
        "zip": "paquete_a5_v2.zip",
        "cuaderno": "A5_generar_correos.ipynb",
        "lanza": "scripts/F5_A5_E19_generar_correos.py",
        "ficheros": [
            "scripts/F5_A5_E19_generar_correos.py",
            "scripts/F5_A5_E19_control_fundamentacion.py",
            "scripts/F5_A5_E17_emparejar_lexico.py",
            "scripts/F5_A5_E18_emparejar_semantico.py",
            "10_CATALOGO_SERVICIOS.md",
            "datos/03_resultados/a5_correos_v1.csv",
        ],
        "orden": [
            "python scripts/F5_A5_E19_generar_correos.py --muestra 40 "
            "--salida a5_correos_v2.csv",
            "python scripts/F5_A5_E19_control_fundamentacion.py "
            "--fichero a5_correos_v2.csv",
        ],
    },
    "campana": {
        "zip": "paquete_a5_campana.zip",
        "cuaderno": "A5_correos_campana.ipynb",
        "lanza": "scripts/F5_A5_E20_campana.py",
        "ficheros": [
            "scripts/F5_A5_E20_campana.py",
            "scripts/F5_A5_E20_control_campana.py",
            "scripts/F5_A5_E19_generar_correos.py",
            "scripts/F5_A5_E17_emparejar_lexico.py",
            "scripts/F5_A5_E18_emparejar_semantico.py",
            "12_CAMPANAS.md",
            "10_CATALOGO_SERVICIOS.md",
            "datos/00_bruto/correo_generico_C01.txt",
            "datos/03_resultados/a5_correos_v1.csv",
        ],
        "orden": [
            "python scripts/F5_A5_E20_campana.py --campana C01 --muestra 40",
            "python scripts/F5_A5_E20_control_campana.py",
        ],
    },
}


def leeme(nombre, cfg):
    libs = "\n".join(f"    {i+1}.  {o}" for i, o in enumerate(cfg["orden"]))
    return f"""PAQUETE {nombre.upper()}  ·  generado por PREP_paquete_colab.py {VERSION_SCRIPT}
{'=' * 72}

CUADERNO QUE LO USA
    {cfg['cuaderno']}

QUE SE EJECUTA
    Solo {cfg['lanza']}
    Los demas scripts son librerias que ese importa, o utilidades posteriores.

ORDEN
{libs}

NOMBRES DE LOS SCRIPTS
    F<fase>_A<agente>_<experimento>_<nombre>.py

    Asi el nombre dice a que fase pertenece y en que experimento de la
    bitacora (08_BITACORA.md) estan sus resultados.

    Ejemplo: F5_A5_E20_campana.py
             fase F5 (contactar) · agente A5 · experimento E20

NECESITA GPU (Colab T4) para la generacion.
Los scripts de control NO necesitan GPU.
"""


def construir(nombre, cfg, tmp):
    z = RAIZ / cfg["zip"]
    faltan = [f for f in cfg["ficheros"] if not (RAIZ / f).exists()]
    if faltan:
        print(f"   FALTAN ficheros, no se construye: {', '.join(faltan)}")
        return None

    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for r in cfg["ficheros"]:
            f.write(RAIZ / r, r)
        for p in ["train", "val", "test"]:
            f.write(tmp / f"cuentas_{p}.csv", f"datos/02_derivado/cuentas_{p}.csv")
        f.writestr("LEEME.txt", leeme(nombre, cfg))
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paquete", choices=list(PAQUETES) + ["todos"], default="todos")
    a = ap.parse_args()

    print("=" * 72)
    print("PAQUETES PARA COLAB")
    print(f"     {VERSION_SCRIPT}")
    print("=" * 72)

    tmp = Path(tempfile.mkdtemp())
    print("\nPreparando los datos de cuentas...")
    for p in ["train", "val", "test"]:
        d = pd.read_csv(DERIVADO / f"cuentas_{p}.csv")
        d = d[d.tiene_texto.fillna(False)][COLUMNAS]
        d.to_csv(tmp / f"cuentas_{p}.csv", index=False, encoding="utf-8")
        print(f"   cuentas_{p}: {len(d):,} filas".replace(",", "."))

    objetivo = PAQUETES if a.paquete == "todos" else {a.paquete: PAQUETES[a.paquete]}
    for nombre, cfg in objetivo.items():
        print(f"\n{cfg['zip']}")
        z = construir(nombre, cfg, tmp)
        if z:
            print(f"   {len(cfg['ficheros'])} ficheros + 3 de datos + LEEME")
            print(f"   {z.stat().st_size/1024/1024:.2f} MB")

    print("\nListo. Sube el .zip en el paso 1 del cuaderno correspondiente.")


if __name__ == "__main__":
    main()
