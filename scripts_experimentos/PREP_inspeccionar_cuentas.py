"""
INSPECCION DEL EXPORT DE CUENTAS  ·  SOLO AGREGADOS
====================================================
Decide si el export completo de cuentas mejora el dataset de 4.009 activas.

PROTOCOLO DE PRIVACIDAD
  Este script imprime UNICAMENTE recuentos, porcentajes y distribuciones de
  etiquetas (sector, subsector, pais, tamaño). NUNCA imprime nombres de
  empresa, CIF, webs ni contactos. Comprueba la lista COLUMNAS_PROHIBIDAS
  al final si quieres verificarlo.

Uso:  python scripts/PREP_inspeccionar_cuentas.py
"""

import re
import sys
import unicodedata
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "INPUT"
REFERENCIA = RAIZ / "90_APARCADO_experimento_clasificacion" / "data"

# Columnas cuyo CONTENIDO no se imprime jamas
COLUMNAS_PROHIBIDAS = re.compile(
    r"nombre|cuenta|alias|raz[oó]n|cif|nif|web|url|sitio|email|correo|"
    r"tel[eé]fono|contacto|direcci|domicilio|propietario",
    re.IGNORECASE,
)


def norm(v):
    if pd.isna(v):
        return None
    t = str(v).strip().upper()
    t = re.sub(r"\s+", " ", t)
    return t or None


def clave_empresa(v):
    if pd.isna(v):
        return None
    t = str(v).strip().upper()
    t = "".join(c for c in unicodedata.normalize("NFD", t)
                if unicodedata.category(c) != "Mn")
    t = re.sub(r"\b(S\.?L\.?U?|S\.?A\.?U?|SCCL|SLL|COOP|C\.?B\.?)\b", " ", t)
    t = re.sub(r"[^A-Z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip() or None


def localizar(df, *patrones):
    """Encuentra una columna por patron, sin imprimir su contenido."""
    for p in patrones:
        for c in df.columns:
            if re.search(p, str(c), re.IGNORECASE):
                return c
    return None


def barra(pct, ancho=28):
    return "#" * int(pct / 100 * ancho)


def main():
    ficheros = sorted(ENTRADA.glob("*.xlsx"))
    if not ficheros:
        sys.exit(f"No hay ningun .xlsx en {ENTRADA}")
    f = ficheros[-1]

    print("=" * 74)
    print("INSPECCION DEL EXPORT DE CUENTAS")
    print("=" * 74)
    print(f"Fichero: {f.name}\n")

    df = pd.read_excel(f)
    print(f"[1] VOLUMEN")
    print(f"      filas    : {len(df):,}".replace(",", "."))
    print(f"      columnas : {len(df.columns)}")

    # ---- estructura (solo nombres de columna y % de relleno) ----------
    print(f"\n[2] COLUMNAS Y RELLENO")
    for i, c in enumerate(df.columns, 1):
        n = df[c].notna().sum()
        marca = "  (contenido no mostrado)" if COLUMNAS_PROHIBIDAS.search(str(c)) else ""
        print(f"      {i:2}. {str(c)[:44]:<44} {n/len(df)*100:5.1f}%{marca}")

    col_sector = localizar(df, r"^sector", r"sector.*empresa")
    col_sub = localizar(df, r"subsector")
    col_web = localizar(df, r"sitio web", r"^web", r"url")
    col_pais = localizar(df, r"^pa[ií]s")
    col_tam = localizar(df, r"tama[nñ]o")
    col_nombre = localizar(df, r"nombre de cuenta", r"^cuenta$", r"raz[oó]n social", r"^nombre$")

    if not col_sector:
        sys.exit("\nERROR: no encuentro la columna de sector. Dime como se llama.")

    df["_sector"] = df[col_sector].map(norm)
    df["_sub"] = df[col_sub].map(norm) if col_sub else None

    # ---- etiquetado ---------------------------------------------------
    print(f"\n[3] ETIQUETADO  (lo que decide si sirve para entrenar)")
    ns, nb = df["_sector"].notna().sum(), (df["_sub"].notna().sum() if col_sub else 0)
    print(f"      con sector    : {ns:,} de {len(df):,}  ({ns/len(df)*100:.1f}%)".replace(",", "."))
    if col_sub:
        print(f"      con subsector : {nb:,} de {len(df):,}  ({nb/len(df)*100:.1f}%)".replace(",", "."))
    print(f"      sectores distintos    : {df['_sector'].nunique()}")
    if col_sub:
        print(f"      subsectores distintos : {df['_sub'].nunique()}")

    # ---- scrapeabilidad -----------------------------------------------
    if col_web:
        tiene = df[col_web].astype(str).str.contains(r"\.", na=False) & df[col_web].notna()
        print(f"\n[4] SCRAPEABILIDAD")
        print(f"      con web        : {tiene.sum():,} ({tiene.mean()*100:.1f}%)".replace(",", "."))
        print(f"      con web Y sector: {(tiene & df['_sector'].notna()).sum():,}".replace(",", "."))
        print(f"      (son las utiles para entrenar A2)")

    # ---- comparacion con el dataset actual ----------------------------
    ref = REFERENCIA / "train.csv"
    if ref.exists() and col_nombre:
        print(f"\n[5] SOLAPE CON LAS 4.009 ACTIVAS")
        act = pd.concat([pd.read_csv(REFERENCIA / f"{p}.csv")
                         for p in ["train", "val", "test"]], ignore_index=True)
        claves_act = set(act["empresa_clave"].dropna())
        claves_new = set(df[col_nombre].map(clave_empresa).dropna())
        comun = claves_act & claves_new
        print(f"      cuentas en el export nuevo : {len(claves_new):,}".replace(",", "."))
        print(f"      ya estaban en las activas  : {len(comun):,}".replace(",", "."))
        print(f"      NUEVAS                     : {len(claves_new - claves_act):,}".replace(",", "."))

    # ---- LA PREGUNTA CLAVE: la cola larga -----------------------------
    print(f"\n[6] ¿ARREGLA LA COLA LARGA?  (el problema principal de A2)")
    for nivel, col in [("SECTOR", "_sector")] + ([("SUBSECTOR", "_sub")] if col_sub else []):
        vc = df[col].value_counts()
        if len(vc) == 0:
            continue
        print(f"\n      --- {nivel}: {len(vc)} clases ---")
        print(f"      mediana de ejemplos por clase : {vc.median():.0f}")
        print(f"      clases con <10 ejemplos       : {(vc < 10).sum()}  ({(vc < 10).sum()/len(vc)*100:.0f}%)")
        print(f"      clases con <50 ejemplos       : {(vc < 50).sum()}")
        print(f"      mayor / menor                 : {vc.iloc[0]} / {vc.iloc[-1]}")

        if ref.exists():
            actv = act[nivel.lower() if nivel == "SECTOR" else "subsector"].value_counts()
            print(f"      >> antes (4.009): {len(actv)} clases, "
                  f"mediana {actv.median():.0f}, {(actv < 10).sum()} clases con <10")
            print(f"      >> ahora        : {len(vc)} clases, "
                  f"mediana {vc.median():.0f}, {(vc < 10).sum()} clases con <10")

    # ---- distribucion de sectores (etiquetas, no empresas) ------------
    print(f"\n[7] DISTRIBUCION DE SECTORES")
    vc = df["_sector"].value_counts()
    for s, n in vc.head(20).items():
        print(f"      {str(s)[:40]:<40} {n:>6}  {barra(n/vc.iloc[0]*100)}")
    if len(vc) > 20:
        print(f"      ... y {len(vc)-20} sectores mas")

    for nombre, col in [("PAIS", col_pais), ("TAMAÑO", col_tam)]:
        if col:
            print(f"\n[8] {nombre}")
            v = df[col].fillna("(sin dato)").map(norm).value_counts()
            for k, n in v.head(8).items():
                print(f"      {str(k)[:36]:<36} {n:>6}  ({n/len(df)*100:4.1f}%)")

    # ---- veredicto -----------------------------------------------------
    print("\n" + "=" * 74)
    print("VEREDICTO")
    print("=" * 74)
    utiles = ((df[col_web].notna() if col_web else True) & df["_sector"].notna()).sum()
    print(f"  Cuentas con sector Y web (entrenables) : {utiles:,}".replace(",", "."))
    print(f"  Frente a las 1.496 utiles de ahora     : x{utiles/1496:.1f}")
    print("\n  Criterio de decision:")
    print("    - Si el % de etiquetado es alto (>80%) y la cola mejora -> USAR ESTE")
    print("    - Si el etiquetado es pobre o las clases se disparan    -> revisar")


if __name__ == "__main__":
    main()
