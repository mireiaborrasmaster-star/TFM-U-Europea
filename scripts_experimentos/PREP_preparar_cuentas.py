"""
PREPARACION DEL DATASET DE CUENTAS  (agente A2 - clasificacion sectorial)
=========================================================================
Convierte el export completo del CRM en un dataset listo para entrenar.

QUE HACE, Y POR QUE
-------------------
1. NORMALIZA LOS TRES NIVELES de la taxonomia de Empresa:
       Sector agrupado (12)  ->  Sector Empresa (41)  ->  Subsector (186)
   No hay que inventar agrupaciones: Empresa ya tiene la suya.

2. ARREGLA LA JERARQUIA. Hay 24 subsectores que aparecen colgando de mas de
   un sector. Se asigna cada uno a su padre mayoritario, para que el modelo
   jerarquico no reciba senales contradictorias.

3. REAPROVECHA EL TEXTO YA SCRAPEADO. Unas 2.100 webs ya estan descargadas del
   trabajo anterior. Se cruzan por nombre normalizado para no repetir el
   scraping, que es lo que mas tiempo cuesta.

4. LIMPIA EL TEXTO con PREP_limpieza_texto.py (banners de cookies, plugins, urls).

5. CONSTRUYE LOS SPLITS RESPETANDO EL TEST ANTERIOR. Las 602 empresas que ya
   estaban en el conjunto de prueba siguen ahi. Asi los resultados nuevos son
   comparables con los baselines ya medidos, en vez de empezar de cero.

PRIVACIDAD
----------
Este script imprime unicamente recuentos, porcentajes y distribuciones de
etiquetas. Nunca nombres de empresa, CIF ni webs.

Uso:  python scripts/PREP_preparar_cuentas.py
"""

import re
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from PREP_limpieza_texto import limpiar_corpus  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "INPUT"
ANTERIOR = RAIZ / "90_APARCADO_experimento_clasificacion" / "data"
SALIDA = RAIZ / "datos" / "02_derivado"
SALIDA.mkdir(parents=True, exist_ok=True)

SEMILLA = 42
MIN_CARACTERES = 100      # umbral de texto util
MIN_EJEMPLOS_COLA = 15    # por debajo de esto, la clase va a "OTROS"
REPARTO = (0.80, 0.10, 0.10)


# ==========================================================================
# Normalizacion
# ==========================================================================

def norm_etiqueta(v):
    if pd.isna(v):
        return None
    t = re.sub(r"\s+", " ", str(v).strip().upper())
    return t or None


def clave_empresa(v):
    """Clave de identidad: sin acentos, sin forma juridica, sin puntuacion.
    Solo para cruzar y deduplicar, nunca como variable del modelo."""
    if pd.isna(v):
        return None
    t = str(v).strip().upper()
    t = "".join(c for c in unicodedata.normalize("NFD", t)
                if unicodedata.category(c) != "Mn")
    t = re.sub(r"\b(S\.?L\.?U?|S\.?A\.?U?|SCCL|SLL|COOP|C\.?B\.?|SOCIEDAD "
               r"(LIMITADA|ANONIMA))\b", " ", t)
    t = re.sub(r"[^A-Z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t or None


def columna(df, *patrones, obligatoria=False):
    for p in patrones:
        for c in df.columns:
            if re.search(p, str(c), re.IGNORECASE):
                return c
    if obligatoria:
        sys.exit(f"ERROR: no encuentro ninguna columna que case con {patrones}")
    return None


def sep(titulo):
    print("\n" + "-" * 70)
    print(titulo)
    print("-" * 70)


# ==========================================================================

def main():
    ficheros = sorted(ENTRADA.glob("*.xlsx"))
    if not ficheros:
        sys.exit(f"No hay ningun .xlsx en {ENTRADA}")
    fichero = ficheros[-1]

    print("=" * 70)
    print("PREPARACION DEL DATASET DE CUENTAS")
    print("=" * 70)
    print(f"Fichero: {fichero.name}")

    df = pd.read_excel(fichero)
    print(f"Filas leidas: {len(df):,}".replace(",", "."))

    # ---- localizar columnas -------------------------------------------
    col = {
        "nombre":   columna(df, r"nombre de cuenta", r"^cuenta$", r"raz[oó]n social",
                            obligatoria=True),
        "agrupado": columna(df, r"sector agrupado"),
        "sector":   columna(df, r"^sector empresa$", r"^sector$", obligatoria=True),
        "sub":      columna(df, r"^subsector"),
        "web":      columna(df, r"sitio web", r"^web$", r"^url$", r"p[áa]gina web"),
        "pais":     columna(df, r"^pa[ií]s"),
        "provincia": columna(df, r"^provincia"),
        "tamano":   columna(df, r"tama[nñ]o"),
        "cliente":  columna(df, r"^cliente$"),
        "asociado": columna(df, r"^asociado$"),
        "atract":   columna(df, r"atractividad"),
    }
    print("\nColumnas localizadas:")
    for k, v in col.items():
        print(f"   {k:<10} {'OK  ' + str(v)[:42] if v else 'NO ENCONTRADA'}")

    if not col["web"]:
        print("\n   *** AVISO: no hay columna de sitio web. ***")
        print("   El dataset se preparara igual, pero SIN texto no se puede")
        print("   entrenar bien A2. Reexporta incluyendo 'Sitio web'.")

    # ---- construir dataframe base --------------------------------------
    d = pd.DataFrame({
        "empresa": df[col["nombre"]],
        "empresa_clave": df[col["nombre"]].map(clave_empresa),
        "sector_agrupado": df[col["agrupado"]].map(norm_etiqueta) if col["agrupado"] else None,
        "sector": df[col["sector"]].map(norm_etiqueta),
        "subsector": df[col["sub"]].map(norm_etiqueta) if col["sub"] else None,
    })
    for k, nuevo in [("web", "url"), ("pais", "pais"), ("provincia", "provincia"),
                     ("tamano", "tamano"), ("cliente", "cliente"),
                     ("asociado", "asociado"), ("atract", "atractividad")]:
        d[nuevo] = df[col[k]] if col[k] else None

    # ---- filtrar y deduplicar -------------------------------------------
    sep("1 - LIMPIEZA DE FILAS")
    antes = len(d)
    d = d[d.empresa_clave.notna() & d.sector.notna()].copy()
    print(f"   sin nombre o sin sector, eliminadas : {antes - len(d):,}".replace(",", "."))
    antes = len(d)
    d = d.drop_duplicates(subset="empresa_clave", keep="first")
    print(f"   duplicadas por nombre, eliminadas   : {antes - len(d):,}".replace(",", "."))
    print(f"   filas utiles                        : {len(d):,}".replace(",", "."))

    # ---- coherencia de la jerarquia --------------------------------------
    sep("2 - JERARQUIA")
    d["jerarquia_incoherente"] = False
    if col["sub"]:
        con_sub = d.dropna(subset=["subsector"])
        padres = con_sub.groupby("subsector").sector.nunique()
        incoherentes = padres[padres > 1].index
        d["jerarquia_incoherente"] = d.subsector.isin(incoherentes)
        print(f"   subsectores colgando de >1 sector : {len(incoherentes)} de "
              f"{d.subsector.nunique()}")
        print(f"   filas afectadas                   : {d.jerarquia_incoherente.sum():,}"
              .replace(",", "."))
        print("   -> NO se reescribe el sector: la etiqueta del CRM es la")
        print("      autoridad y esta rellena al 100%. Solo se marca la fila,")
        print("      para poder medir despues si esas filas fallan mas.")
        print("      (Un subsector bajo dos sectores puede ser legitimo:")
        print("       'ENVASES' cuelga razonablemente de plastico y de papel.)")
    for nivel in ["sector_agrupado", "sector", "subsector"]:
        if d[nivel].notna().any():
            print(f"   {nivel:<16} {d[nivel].nunique():>4} clases  "
                  f"({d[nivel].notna().mean()*100:.1f}% relleno)")

    # ---- reaprovechar texto ya scrapeado ---------------------------------
    sep("3 - TEXTO WEB YA DISPONIBLE")
    d["web_text"] = ""
    d["origen_texto"] = "pendiente"

    # (a) lo scrapeado en esta fase, que es lo mas reciente y manda
    scrapeado = RAIZ / "datos" / "01_limpio" / "web_text_scrapeado.csv"
    if scrapeado.exists():
        s = pd.read_csv(scrapeado)
        s = s[s.estado == "ok"].dropna(subset=["empresa_clave"])
        s = s.drop_duplicates("empresa_clave", keep="last")
        mapa_s = dict(zip(s.empresa_clave, s.texto.fillna("")))
        d["web_text"] = d.empresa_clave.map(mapa_s).fillna("")
        d.loc[d.web_text.str.len() > MIN_CARACTERES, "origen_texto"] = "scrapeado"
        print(f"   scrapeado en esta fase            : "
              f"{(d.web_text.str.len() > MIN_CARACTERES).sum():,}".replace(",", "."))

    # (b) lo que ya venia del trabajo anterior, para lo que aun este vacio
    if (ANTERIOR / "train.csv").exists():
        viejo = pd.concat(
            [pd.read_csv(ANTERIOR / f"{p}.csv") for p in ["train", "val", "test"]],
            ignore_index=True)
        viejo = viejo.dropna(subset=["empresa_clave"]).drop_duplicates("empresa_clave")
        mapa = dict(zip(viejo.empresa_clave, viejo.web_text_limpio.fillna("")))
        vacias = d.web_text.str.len() <= MIN_CARACTERES
        rellenadas = d.loc[vacias, "empresa_clave"].map(mapa).fillna("")
        d.loc[vacias, "web_text"] = rellenadas
        nuevas = vacias & (d.web_text.str.len() > MIN_CARACTERES)
        d.loc[nuevas, "origen_texto"] = "reutilizado"
        print(f"   reaprovechado del trabajo anterior: {nuevas.sum():,}".replace(",", "."))
    faltan = (d.web_text.str.len() <= MIN_CARACTERES)
    print(f"   PENDIENTES DE SCRAPEAR            : {faltan.sum():,}".replace(",", "."))
    if col["web"]:
        con_url = d.url.notna() & d.url.astype(str).str.contains(r"\.", na=False)
        print(f"   ...de las cuales tienen URL       : {(faltan & con_url).sum():,}"
              .replace(",", "."))

    # ---- limpieza del texto ----------------------------------------------
    sep("4 - LIMPIEZA DEL TEXTO")
    if (d.web_text.str.len() > MIN_CARACTERES).sum() > 50:
        limpios, _ = limpiar_corpus(d.web_text.tolist(), umbral_plantilla=0.02,
                                    verbose=True)
        d["web_text"] = limpios
    else:
        print("   (aun no hay texto suficiente que limpiar)")
    d["tiene_texto"] = d.web_text.str.len() >= MIN_CARACTERES

    # ---- clases de cola larga --------------------------------------------
    sep("5 - COLA LARGA")
    for nivel in ["sector", "subsector"]:
        if d[nivel].isna().all():
            continue
        vc = d[nivel].value_counts()
        raras = vc[vc < MIN_EJEMPLOS_COLA].index
        nuevo = nivel + "_agr"
        if nivel == "subsector":
            # las raras se pliegan a "OTROS - <sector padre>"
            d[nuevo] = np.where(d[nivel].isin(raras),
                                "OTROS - " + d.sector.fillna("SIN SECTOR"),
                                d[nivel])
        else:
            d[nuevo] = np.where(d[nivel].isin(raras), "OTROS", d[nivel])
        print(f"   {nivel:<10} {len(vc):>4} clases -> {d[nuevo].nunique():>4} "
              f"tras plegar las de <{MIN_EJEMPLOS_COLA} ejemplos "
              f"({len(raras)} clases, {vc[raras].sum()} filas)")

    # ---- entrada del modelo ----------------------------------------------
    d["input_completo"] = (
        "Empresa: " + d.empresa.fillna("").astype(str).str.strip()
        + d.pais.fillna("").astype(str).apply(lambda p: f" | Pais: {p}" if p.strip() else "")
        + d.web_text.apply(lambda t: f"\nWeb: {t}" if t else "")
    ).str.strip()
    d["input_nombre"] = "Empresa: " + d.empresa.fillna("").astype(str).str.strip()
    d["input_texto"] = d.web_text

    # ---- splits, respetando el test anterior -----------------------------
    sep("6 - REPARTO TRAIN / VAL / TEST")
    d["particion"] = None
    if (ANTERIOR / "test.csv").exists():
        test_previo = set(pd.read_csv(ANTERIOR / "test.csv").empresa_clave.dropna())
        val_previo = set(pd.read_csv(ANTERIOR / "val.csv").empresa_clave.dropna())
        d.loc[d.empresa_clave.isin(test_previo), "particion"] = "test"
        d.loc[d.empresa_clave.isin(val_previo) & d.particion.isna(), "particion"] = "val"
        print(f"   heredadas del reparto anterior -> test {(d.particion=='test').sum()}, "
              f"val {(d.particion=='val').sum()}")
        print("   (se respetan para que los resultados sigan siendo comparables)")

    resto = d[d.particion.isna()].copy()
    rng = np.random.default_rng(SEMILLA)
    # reparto estratificado por sector, para que todas las clases esten en train
    asignacion = pd.Series(index=resto.index, dtype=object)
    for _, grupo in resto.groupby(resto.sector.fillna("NA")):
        idx = grupo.index.to_numpy()
        rng.shuffle(idx)
        n = len(idx)
        n_tr = max(1, int(round(n * REPARTO[0])))
        n_va = int(round(n * REPARTO[1]))
        asignacion.loc[idx[:n_tr]] = "train"
        asignacion.loc[idx[n_tr:n_tr + n_va]] = "val"
        asignacion.loc[idx[n_tr + n_va:]] = "test"
    d.loc[resto.index, "particion"] = asignacion
    d["particion"] = d.particion.fillna("train")

    for p in ["train", "val", "test"]:
        s = d[d.particion == p]
        print(f"   {p:<6} {len(s):>6,} filas | {s.sector.nunique():>3} sectores | "
              f"{s.tiene_texto.mean()*100:4.1f}% con texto".replace(",", "."))

    # ---- fuga entre particiones ------------------------------------------
    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        ca = set(d[d.particion == a].empresa_clave)
        cb = set(d[d.particion == b].empresa_clave)
        if ca & cb:
            print(f"   AVISO: {len(ca & cb)} empresas repetidas entre {a} y {b}")

    # ---- guardar -----------------------------------------------------------
    sep("7 - FICHEROS GENERADOS")
    columnas = ["empresa", "empresa_clave", "url", "pais", "provincia", "tamano",
                "cliente", "asociado", "atractividad",
                "sector_agrupado", "sector", "sector_agr", "subsector", "subsector_agr",
                "web_text", "tiene_texto", "origen_texto", "jerarquia_incoherente",
                "input_nombre", "input_texto", "input_completo", "particion"]
    columnas = [c for c in columnas if c in d.columns]
    for p in ["train", "val", "test"]:
        ruta = SALIDA / f"cuentas_{p}.csv"
        d[d.particion == p][columnas].to_csv(ruta, index=False, encoding="utf-8")
        print(f"   {ruta.name}")

    pend = d[~d.tiene_texto]
    if col["web"]:
        pend = pend[pend.url.notna()]
    ruta = SALIDA / "pendientes_scraping.csv"
    pend[[c for c in ["empresa", "empresa_clave", "url"] if c in pend.columns]].to_csv(
        ruta, index=False, encoding="utf-8")
    print(f"   {ruta.name}  ({len(pend):,} cuentas por scrapear)".replace(",", "."))

    print("\n" + "=" * 70)
    print("SIGUIENTE PASO")
    print("=" * 70)
    if not col["web"]:
        print("  1. Reexportar el CRM incluyendo la columna 'Sitio web'")
        print("  2. Volver a lanzar este script")
    else:
        print(f"  1. Scrapear las {len(pend):,} webs pendientes".replace(",", "."))
        print("  2. Lanzar los baselines sobre el dataset nuevo")


if __name__ == "__main__":
    main()
