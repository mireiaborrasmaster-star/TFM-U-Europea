"""
PREPARACION DEL DATASET DE ENRUTADO  (agente A8, fase F8)
==========================================================
Convierte el export de oportunidades en un dataset para predecir a que area
tecnica de Empresa corresponde una necesidad.

EL PROBLEMA
-----------
Llega una oportunidad con un tema como "Ensayos compostabilidad" o "Vida util
- 3 salsas". Hay que decidir que tecnico comercial la atiende. Hoy lo decide
una persona; si se equivoca, el lead llega a quien no toca, se devuelve y el
cliente espera.

DOS DIMENSIONES, COMO EN EL PLAYBOOK
------------------------------------
  AREA TECNICA    ¿de que trata?   -> 13 clases utiles (18 menos las residuales)
  DIVISION        el nivel grueso  -> 4 clases (el prefijo antes de los dos puntos)
  TIPO SERVICIO   ¿como se atiende? -> 6 clases (Ensayos, Consultoria, I+D...)

Se predicen por separado porque son preguntas distintas. La division se deriva
del area, igual que en A2 el sector agrupado se derivaba del sector.

DIFERENCIA CLAVE CON A2: EL REPARTO ES TEMPORAL
-----------------------------------------------
En A2 el reparto era aleatorio porque clasificar una empresa no depende del
tiempo. Aqui SI: el modelo va a enrutar oportunidades FUTURAS, asi que debe
entrenarse con las antiguas y evaluarse con las recientes.

Un reparto aleatorio dejaria que el modelo viera oportunidades de junio para
predecir las de marzo, e inflaria el resultado de forma enganosa.

PRIVACIDAD
----------
No se usan nombres de cuenta. Del texto del tema se eliminan correos,
telefonos y codigos largos. Solo se imprimen recuentos y etiquetas.

Uso:  python scripts/F8_A8_preparar_datos.py
"""

import glob
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "datos" / "02_derivado"
SALIDA.mkdir(parents=True, exist_ok=True)

# Donde buscar el export. Primero en MASTER, si no en el proyecto de prevision.
RUTAS = [RAIZ / "datos" / "00_bruto", RAIZ / "INPUT",
         RAIZ.parent.parent / "PREVISIÓN DE VENTAS" / "INPUT" / "TODAS"]

MIN_EJEMPLOS_AREA = 30     # por debajo, el area se pliega a "OTRAS"
REPARTO = (0.70, 0.15, 0.15)

RE_EMAIL = re.compile(r"[\w\.\-\+]+@[\w\-]+\.[\w\.\-]+")
RE_TEL = re.compile(r"(?:\+\d{1,3}[\s\.\-]?)?(?:\d[\s\.\-]?){9,}")
RE_URL = re.compile(r"https?://\S+|www\.\S+")


def limpiar_tema(v):
    """Limpieza minima. El tema es texto tecnico util: se conserva casi todo.
    Solo se quitan datos de contacto y codigos muy largos."""
    if pd.isna(v):
        return ""
    t = str(v)
    t = RE_URL.sub(" ", t)
    t = RE_EMAIL.sub(" ", t)
    t = RE_TEL.sub(" ", t)
    t = re.sub(r"\b\d{8,}\b", " ", t)      # codigos internos largos
    return re.sub(r"\s+", " ", t).strip()


def localizar_export():
    for r in RUTAS:
        f = sorted(glob.glob(str(r / "Oportunidades*.xlsx")))
        if f:
            return f[-1]
    sys.exit("No encuentro ningun 'Oportunidades*.xlsx'. Deja el export en "
             "MASTER/datos/00_bruto/")


def sep(t):
    print("\n" + "-" * 68)
    print(t)
    print("-" * 68)


def main():
    fichero = localizar_export()
    print("=" * 68)
    print("PREPARACION DEL DATASET DE ENRUTADO (A8)")
    print("=" * 68)
    print(f"Fichero: {Path(fichero).name}")

    op = pd.read_excel(fichero)
    print(f"Filas leidas: {len(op):,}".replace(",", "."))

    d = pd.DataFrame({
        "id_oportunidad": op["Nº oportunidad"],
        "tema": op["Tema"].map(limpiar_tema),
        "area": op["Área de Empresa"].astype(str).str.strip(),
        "tipo_servicio": op["Tipo Oportunidad"].astype(str).str.strip(),
        "linea": op.get("Línea Tecnológica", pd.Series(dtype=str)),
        "fecha": pd.to_datetime(op["Fecha de creación"], errors="coerce"),
        "estado": op["Estado"],
    })
    d.loc[d.area.isin(["nan", "None", ""]), "area"] = np.nan
    d.loc[d.tipo_servicio.isin(["nan", "None", ""]), "tipo_servicio"] = np.nan

    sep("1 - FILAS UTILIZABLES")
    antes = len(d)
    d = d[(d.tema.str.len() > 3) & d.area.notna() & d.fecha.notna()].copy()
    print(f"   sin tema, sin area o sin fecha, eliminadas: {antes - len(d):,}"
          .replace(",", "."))
    print(f"   filas utiles                              : {len(d):,}".replace(",", "."))
    print(f"   longitud media del tema                   : {d.tema.str.len().mean():.0f} car.")

    # ---- division (el prefijo) -----------------------------------------
    sep("2 - NIVELES DE ETIQUETA")
    d["division"] = d.area.str.split(":").str[0].str.strip()
    vc_div = d.division.value_counts()
    residuales = vc_div[vc_div < MIN_EJEMPLOS_AREA].index
    d["division"] = np.where(d.division.isin(residuales), "OTRAS DIVISIONES", d.division)
    print(f"   division      : {d.division.nunique()} clases")
    for k, n in d.division.value_counts().items():
        print(f"      {str(k)[:46]:<48} {n:>5}")

    vc = d.area.value_counts()
    raras = vc[vc < MIN_EJEMPLOS_AREA].index
    d["area_agr"] = np.where(d.area.isin(raras),
                             "OTRAS - " + d.division, d.area)
    print(f"\n   area          : {d.area.nunique()} clases -> {d.area_agr.nunique()} "
          f"tras plegar las de <{MIN_EJEMPLOS_AREA} ejemplos "
          f"({len(raras)} clases, {vc[raras].sum()} filas)")
    print(f"   tipo_servicio : {d.tipo_servicio.nunique()} clases "
          f"({d.tipo_servicio.notna().mean()*100:.1f}% relleno)")

    # ---- reparto TEMPORAL ----------------------------------------------
    sep("3 - REPARTO TEMPORAL (no aleatorio)")
    d = d.sort_values("fecha").reset_index(drop=True)
    n = len(d)
    c1, c2 = int(n * REPARTO[0]), int(n * (REPARTO[0] + REPARTO[1]))
    d["particion"] = "test"
    d.loc[:c1, "particion"] = "train"
    d.loc[c1:c2, "particion"] = "val"
    print("   Se entrena con las oportunidades ANTIGUAS y se evalua con las")
    print("   RECIENTES, que es como funcionara en produccion.")
    for p in ["train", "val", "test"]:
        s = d[d.particion == p]
        print(f"\n   {p:<6} {len(s):>5} filas | {s.fecha.min():%Y-%m-%d} a "
              f"{s.fecha.max():%Y-%m-%d} | {s.area_agr.nunique():>2} areas")

    # clases que aparecen en test pero no en train: no son evaluables
    en_train = set(d[d.particion == "train"].area_agr)
    fuera = d[(d.particion != "train") & (~d.area_agr.isin(en_train))]
    if len(fuera):
        print(f"\n   AVISO: {len(fuera)} filas de val/test con un area que no aparece")
        print("   en train (efecto del reparto temporal). Se marcan, no se eliminan.")
    d["area_vista_en_train"] = d.area_agr.isin(en_train)

    # ---- entrada del modelo ---------------------------------------------
    d["input_tema"] = d.tema
    d["input_completo"] = d.tema + d.linea.fillna("").astype(str).apply(
        lambda x: f" | Linea: {x}" if x and x != "nan" else "")

    sep("4 - FICHEROS GENERADOS")
    cols = ["id_oportunidad", "tema", "area", "area_agr", "division",
            "tipo_servicio", "linea", "fecha", "estado", "particion",
            "area_vista_en_train", "input_tema", "input_completo"]
    for p in ["train", "val", "test"]:
        ruta = SALIDA / f"enrutado_{p}.csv"
        d[d.particion == p][cols].to_csv(ruta, index=False, encoding="utf-8")
        print(f"   {ruta.name}")

    print("\n" + "=" * 68)
    print("SIGUIENTE PASO: python scripts/baselines_a8.py")


if __name__ == "__main__":
    main()
