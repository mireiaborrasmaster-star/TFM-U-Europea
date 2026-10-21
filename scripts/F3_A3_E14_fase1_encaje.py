"""
A3 · FASE 1 · PUNTUAR UNA CUENTA ANTES DE CONTACTARLA
======================================================
Predice la atractividad comercial de una empresa usando SOLO lo que se sabe de
ella sin haber hablado nunca: sector, tamaño, ubicación y el texto de su web.

PARA QUE SIRVE
--------------
Empresa tiene 24.079 cuentas y solo 3.013 están valoradas. Las 21.066 restantes
nadie las ha mirado, y E12 demostró que ahí hay valor: las cuentas sin valorar
convierten al 7,2 % mientras las marcadas como "no target" convierten al 11,2 %.
Un modelo que puntúe esas 21.066 encontraría cuentas buenas que hoy se ignoran.

POR QUE NO SE USA EL HISTORIAL DE OPORTUNIDADES
-----------------------------------------------
Sería circular: quien asignó las notas conocía ese historial. El modelo
aprendería a reproducir información que en el momento real de decidir no existe.
Ver D12 en la bitácora.

POR QUE CLASIFICACION MULTICLASE Y NO REGRESION ORDINAL
-------------------------------------------------------
Porque la escala no es ordinal. E12 demostró que B supera a A en todos los
indicadores: A es el cliente más valioso por proyecto, B el que vuelve.
Forzar un orden A>B>C>D>E sería imponer una jerarquía que los datos no respaldan.

MODELO
------
Gradient boosting sobre variables tabulares. En datos de tabla los árboles
superan a las redes neuronales de forma sistemática (Grinsztajn et al. 2022;
Shwartz-Ziv y Armon 2022), y además se pueden explicar.

Uso:  python scripts/F3_A3_E14_fase1_encaje.py
"""

import glob
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
LIMPIO = RAIZ / "datos" / "01_limpio"
DERIVADO = RAIZ / "datos" / "02_derivado"
SALIDA = RAIZ / "datos" / "03_resultados"
SALIDA.mkdir(parents=True, exist_ok=True)

SEMILLA = 42
CATEGORICAS = ["sector", "tamano", "provincia", "pais", "asociado", "personalidad",
               "zona", "sector_zona", "sector_tamano"]

# Provincias de la Comunidad Valenciana. Empresa tiene su sede en Valencia, y la
# proximidad resulta ser muy predictiva: estas cuentas convierten al 15,3%
# frente al 7,5% del resto (chi2, p = 3e-62). Ver E15 en la bitacora.
PROV_CV = {"VALENCIA", "CASTELLON", "CASTELLÓN", "ALICANTE",
           "VALENCIA/VALÈNCIA", "CASTELLÓN/CASTELLÓ", "ALICANTE/ALACANT",
           "VALÈNCIA", "CASTELLÓ", "ALACANT"}


def anadir_zona(d):
    """Zona geografica y combinaciones.

    El modelo no puede deducir por si solo que Castellon, Valencia y Alicante
    forman un grupo con sentido: para el son tres categorias sueltas entre 52.
    Esta variable codifica conocimiento de negocio que no esta en los datos.

    Las combinaciones sector x zona capturan interacciones que un modelo de
    arboles encontraria por su cuenta, pero con 2.155 filas de entrenamiento
    conviene darselas hechas.
    """
    prov = d.provincia.astype(str).str.upper().str.strip()
    d["zona"] = np.where(prov.isin(PROV_CV), "COM_VALENCIANA",
                np.where(d.pais.astype(str).str.upper().str.strip()
                         .isin(["ESPAÑA", "ESPANA", "SPAIN"]), "RESTO_ESPANA",
                         "INTERNACIONAL"))
    d["sector_zona"] = d.sector.astype(str) + " | " + d.zona
    d["sector_tamano"] = d.sector.astype(str) + " | " + d.tamano.astype(str)
    return d


def sep(t):
    print("\n" + "-" * 70)
    print(t)
    print("-" * 70)


def cargar():
    f = glob.glob(str(LIMPIO / "Cuentas*_anon.csv"))
    if not f:
        sys.exit("Faltan los datos anonimizados. Ejecuta antes PREP_anonimizar.py")
    cu = pd.read_csv(f[0], sep=";")

    col = lambda *p: next((c for c in cu.columns
                           if any(x.lower() in c.lower() for x in p)), None)
    d = pd.DataFrame({
        "clave": cu[col("Nombre de cuenta")],
        "sector": cu[col("Sector Empresa")],
        "sector_agr": cu[col("Sector agrupado")],
        "tamano": cu[col("Tamaño cuenta")],
        "provincia": cu[col("Provincia")],
        "pais": cu[col("País")],
        "asociado": cu[col("Asociado")],
        "personalidad": cu[col("Personalidad")],
        "es_cliente": cu[col("Número de cuenta")].notna(),
        "atractividad": cu[col("Atractividad")],
    })
    d["nota"] = d.atractividad.astype(str).str[0]
    d.loc[d.atractividad.isna(), "nota"] = np.nan

    # Texto web reaprovechado de A2.
    # El dataset de A2 tiene los nombres REALES normalizados; el de cuentas
    # ya esta anonimizado. Hay que traducir los primeros al mismo codigo,
    # aplicando la misma normalizacion y la misma sal que uso el anonimizador.
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from PREP_anonimizar import normalizar_nombre, cargar_sal
        import hashlib
        sal = cargar_sal()

        def codigo(nombre, prefijo="EMP_"):
            c = normalizar_nombre(nombre)
            if not c:
                return None
            h = hashlib.sha256((sal + c).encode("utf-8")).hexdigest()
            return f"{prefijo}{h[:8].upper()}"

        w = pd.concat([pd.read_csv(DERIVADO / f"cuentas_{p}.csv",
                                   usecols=["empresa", "web_text"])
                       for p in ["train", "val", "test"]], ignore_index=True)
        w["clave"] = w.empresa.map(codigo)      # nombre real -> codigo
        w = w.dropna(subset=["clave"]).drop_duplicates("clave")[["clave", "web_text"]]
        d = d.merge(w, on="clave", how="left")
        n = (d.web_text.fillna("").str.len() > 100).sum()
        print(f"   texto web enlazado desde A2: {n:,}".replace(",", "."))
        if n == 0:
            print("   AVISO: el enlace no ha funcionado. Se continua sin texto.")
    except Exception as e:
        print(f"   (sin texto web: {e})")
        d["web_text"] = ""
    d["web_text"] = d.web_text.fillna("")
    return anadir_zona(d)


def construir_variables(tr, te, usar_texto=True):
    """Codificación de categóricas por frecuencia + TF-IDF del texto.

    La codificación por frecuencia sustituye cada categoría por su número de
    apariciones en train. Es robusta con muchas categorías (52 provincias,
    118 países) y no infla la dimensionalidad como haría one-hot.
    """
    X_tr, X_te = pd.DataFrame(index=tr.index), pd.DataFrame(index=te.index)
    for c in CATEGORICAS:
        frec = tr[c].value_counts()
        X_tr[c + "_frec"] = tr[c].map(frec).fillna(0)
        X_te[c + "_frec"] = te[c].map(frec).fillna(0)
        # tasa de la clase mayoritaria dentro de cada categoría, calculada solo en train
        for n in sorted(tr.nota.dropna().unique()):
            tasa = tr.assign(y=(tr.nota == n)).groupby(c).y.mean()
            X_tr[f"{c}_p{n}"] = tr[c].map(tasa).fillna((tr.nota == n).mean())
            X_te[f"{c}_p{n}"] = te[c].map(tasa).fillna((tr.nota == n).mean())
    X_tr["es_cliente"] = tr.es_cliente.astype(int).values
    X_te["es_cliente"] = te.es_cliente.astype(int).values
    X_tr["tiene_web"] = (tr.web_text.str.len() > 100).astype(int).values
    X_te["tiene_web"] = (te.web_text.str.len() > 100).astype(int).values

    if usar_texto:
        v = TfidfVectorizer(max_features=3000, min_df=5, sublinear_tf=True,
                            strip_accents="unicode", ngram_range=(1, 2))
        A = v.fit_transform(tr.web_text.str.slice(0, 1500))
        Bm = v.transform(te.web_text.str.slice(0, 1500))
        cols = [f"txt_{i}" for i in range(A.shape[1])]
        X_tr = pd.concat([X_tr, pd.DataFrame(A.toarray(), columns=cols, index=tr.index)], axis=1)
        X_te = pd.concat([X_te, pd.DataFrame(Bm.toarray(), columns=cols, index=te.index)], axis=1)
    return X_tr, X_te


def evaluar(nombre, y, p, filas):
    a = accuracy_score(y, p) * 100
    f = f1_score(y, p, average="macro", zero_division=0) * 100
    print(f"   {nombre:<34} acc {a:6.2f}   f1_macro {f:6.2f}")
    filas.append({"modelo": nombre, "accuracy": round(a, 2), "f1_macro": round(f, 2)})


def main():
    print("=" * 70)
    print("A3 · FASE 1 · PUNTUAR CUENTAS ANTES DEL CONTACTO")
    print("=" * 70)
    d = cargar()
    print(f"   cuentas totales: {len(d):,}".replace(",", "."))

    # Solo A-E. La T (administraciones, asociaciones, centros tecnologicos) no
    # es una nota de calidad sino un tipo de entidad: se aparta.
    v = d[d.nota.isin(list("ABCDE"))].copy()
    sinv = d[d.nota.isna()].copy()
    print(f"   valoradas A-E  : {len(v):,}  (se aparta la T: {(d.nota=='T').sum()})"
          .replace(",", "."))
    print(f"   sin valorar    : {len(sinv):,}  <- objetivo del modelo".replace(",", "."))

    sep("1 - REPARTO POR ZONA")
    for z, n in v.zona.value_counts().items():
        sub = v[v.zona == z]
        ab = sub.nota.isin(["A", "B"]).mean() * 100
        print(f"   {z:<16} {n:>5} cuentas valoradas · {ab:4.1f}% con nota A o B")

    sep("2 - REPARTO TRAIN/TEST")
    tr, te = train_test_split(v, test_size=0.25, random_state=SEMILLA, stratify=v.nota)
    print(f"   train {len(tr):,} · test {len(te):,}".replace(",", "."))
    print("\n   distribucion de notas en train:")
    for k, n in tr.nota.value_counts().sort_index().items():
        print(f"      {k}  {n:>4}  ({n/len(tr)*100:4.1f}%)")

    sep("3 - MODELOS")
    filas = []
    dm = DummyClassifier(strategy="most_frequent").fit(tr[["sector"]], tr.nota)
    evaluar("Clase mayoritaria", te.nota, dm.predict(te[["sector"]]), filas)

    Xtr, Xte = construir_variables(tr, te, usar_texto=False)
    for nombre, mod in [
        ("Regresion logistica (sin texto)",
         LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEMILLA)),
        ("Random Forest (sin texto)",
         RandomForestClassifier(n_estimators=400, class_weight="balanced",
                                min_samples_leaf=3, random_state=SEMILLA, n_jobs=-1)),
    ]:
        mod.fit(Xtr, tr.nota)
        evaluar(nombre, te.nota, mod.predict(Xte), filas)

    # ¿aportan las variables de zona y combinaciones?
    BASE = ["sector", "tamano", "provincia", "pais", "asociado", "personalidad"]
    global CATEGORICAS
    completas = CATEGORICAS
    CATEGORICAS = BASE
    Xa, Xb = construir_variables(tr, te, usar_texto=False)
    m = RandomForestClassifier(n_estimators=400, class_weight="balanced",
                               min_samples_leaf=3, random_state=SEMILLA,
                               n_jobs=-1).fit(Xa, tr.nota)
    evaluar("RF sin zona ni combinaciones", te.nota, m.predict(Xb), filas)
    CATEGORICAS = completas

    hay_texto = (tr.web_text.str.len() > 100).sum() >= 50
    if hay_texto:
        Xtr2, Xte2 = construir_variables(tr, te, usar_texto=True)
        rf = RandomForestClassifier(n_estimators=400, class_weight="balanced",
                                    min_samples_leaf=3, random_state=SEMILLA, n_jobs=-1)
        rf.fit(Xtr2, tr.nota)
        pred = rf.predict(Xte2)
        evaluar("Random Forest (+ texto web)", te.nota, pred, filas)
    else:
        print("   (no hay texto web suficiente: se omite ese modelo)")
        Xtr2, Xte2, rf = Xtr, Xte, None
        rf = RandomForestClassifier(n_estimators=400, class_weight="balanced",
                                    min_samples_leaf=3, random_state=SEMILLA,
                                    n_jobs=-1).fit(Xtr, tr.nota)
        pred = rf.predict(Xte)

    sep("4 - DETALLE DEL MEJOR MODELO")
    print(classification_report(te.nota, pred, zero_division=0, digits=3))
    print("   Matriz de confusion (filas=real, columnas=predicho):")
    cm = pd.DataFrame(confusion_matrix(te.nota, pred, labels=list("ABCDE")),
                      index=list("ABCDE"), columns=list("ABCDE"))
    print(cm.to_string())

    sep("5 - VARIABLES MAS INFLUYENTES")
    imp = pd.Series(rf.feature_importances_, index=Xtr2.columns).sort_values(ascending=False)
    noTxt = imp[~imp.index.str.startswith("txt_")]
    print("   (excluyendo las 3.000 del texto)")
    for k, x in noTxt.head(12).items():
        print(f"      {k:<26} {x:.4f}")
    print(f"\n   peso total del texto web: {imp[imp.index.str.startswith('txt_')].sum():.3f}")

    pd.DataFrame(filas).to_csv(SALIDA / "a3_fase1.csv", index=False, encoding="utf-8")
    with open(SALIDA / "a3_fase1.json", "w", encoding="utf-8") as f:
        json.dump({"n_train": len(tr), "n_test": len(te),
                   "n_sin_valorar": len(sinv), "resultados": filas},
                  f, ensure_ascii=False, indent=2)
    print(f"\n   Guardado en {SALIDA.name}/a3_fase1.csv")


if __name__ == "__main__":
    main()
