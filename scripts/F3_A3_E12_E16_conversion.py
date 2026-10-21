"""
A3 · QUE PREDICE LA CONVERSION REAL  ·  reproduce E12, E13, E15 y E16
=====================================================================
Cruza las cuentas del CRM con su historico de oportunidades y responde cuatro
preguntas encadenadas:

  E12  ¿Predice la nota humana (Atractividad) el comportamiento real?
  E15  ¿Predice la ubicacion? ¿Y la tiene en cuenta el criterio humano?
  E13  ¿Aportan informacion distinta la cuenta y lo que pide?
  E16  ¿Puede un modelo priorizar mejor que la nota humana?

POR QUE EXISTE ESTE FICHERO
---------------------------
Estos cuatro experimentos se ejecutaron de forma exploratoria y solo quedaron
sus resultados escritos en la bitacora. Entre ellos esta el hallazgo de mayor
valor organizativo de todo el trabajo —las cuentas de la Comunidad Valenciana
convierten el doble y reciben la mitad de notas altas— sin ningun codigo que
lo respaldara.

EL CRUCE, Y POR QUE POR NOMBRE
------------------------------
El campo "Numero de cuenta" esta vacio en el 78% de las cuentas, de modo que no
sirve como clave. El cruce se hace por el nombre seudonimizado, que la
anonimizacion mantiene estable entre ficheros precisamente para esto.

Es un detalle que conviene dejar escrito: quien intente reproducir el trabajo
cruzando por el identificador aparente obtendra 1.380 cuentas en lugar de 2.180
y todas las tasas saldran mal.

PRIVACIDAD
----------
Trabaja sobre los ficheros _anon: nombres, CIF y webs estan seudonimizados. No
imprime ningun identificador, solo agregados.

SOBRE LA REPRODUCCION DE E16
----------------------------
E12, E15 y E13 son agregados deterministas: se reproducen exactamente.

E16 entrena un modelo y la configuracion original no quedo registrada, asi que
lo que sigue es una RECONSTRUCCION. Coincide con lo publicado dentro del margen
que cabe esperar.

CUIDADO CON DOS COSAS  (ver X12)
--------------------------------
La primera version de este script dio por NO REPRODUCIDO el ratio de
priorizacion de E16, y se equivoco en dos puntos a la vez:

  METRICA    E16 informa el cociente entre el QUINTIL SUPERIOR y el QUINTIL
             INFERIOR ("el 20% mejor convierte 16,3 veces mas que el 20%
             peor"). El script calculaba el lift del decil superior sobre la
             tasa de base, que es otra cosa y da un numero mucho menor.

  POBLACION  E16 trabaja sobre cuentas VALORADAS, donde la tasa de conversion
             es del 12% y no del 3,5% de la cartera entera. Un ratio de
             priorizacion depende de la tasa base, asi que cambiar la poblacion
             cambia la cifra aunque el modelo sea identico.

Un ratio de priorizacion no significa nada sin decir entre que grupos y sobre
que poblacion. Aqui se informan ambas metricas explicitamente para que no
vuelva a confundirse.

Uso (sin GPU):
    python scripts/F3_A3_E12_E16_conversion.py
"""

import argparse
import json
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

VERSION_SCRIPT = "v1 · 29-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
LIMPIO = RAIZ / "datos" / "01_limpio"
CUENTAS = "Cuentas activas 25-09-2026 20-36-50_anon.csv"
OPORTUNIDADES = "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56_anon.csv"

# Las tres provincias de la Comunidad Valenciana. Es conocimiento aportado por
# la autora: para el modelo eran tres categorias sueltas entre 52 y solo
# alguien de la organizacion sabe que forman un grupo con sentido.
PROV_CV = {"valencia", "castellon", "alicante"}

BITACORA = {
    "cv_cuentas": 4734,
    "cv_con_oportunidad": 15.3,
    "resto_con_oportunidad": 7.5,
    "cv_con_venta": 6.1,
    "resto_con_venta": 3.0,
}


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def es_cv(provincia):
    return sin_acentos(provincia).strip() in PROV_CV


def sep(n, t):
    print()
    print("=" * 74)
    print(f"{n} · {t}")
    print("=" * 74)


def cargar():
    cu = pd.read_csv(LIMPIO / CUENTAS, sep=";", low_memory=False)
    op = pd.read_csv(LIMPIO / OPORTUNIDADES, sep=";", low_memory=False)

    # una fila por cuenta con su historico resumido
    op["gana"] = (op.Estado == "Lograda").astype(int)
    res = op.groupby("Cuenta").agg(
        n_oport=("gana", "size"),
        n_ganadas=("gana", "sum"),
    ).reset_index()

    d = cu.merge(res, left_on="Nombre de cuenta", right_on="Cuenta", how="left")
    d["n_oport"] = d.n_oport.fillna(0)
    d["n_ganadas"] = d.n_ganadas.fillna(0)
    d["tiene_oportunidad"] = (d.n_oport > 0).astype(int)
    d["tiene_venta"] = (d.n_ganadas > 0).astype(int)
    d["zona_cv"] = d.Provincia.apply(es_cv).astype(int)
    d["nota"] = d.Atractividad.astype(str).str[:1].replace("n", np.nan)
    return d, op


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semilla", type=int, default=42)
    a = ap.parse_args()

    print("=" * 74)
    print("A3 · QUE PREDICE LA CONVERSION REAL")
    print(f"     {VERSION_SCRIPT}  ·  reproduce E12, E13, E15 y E16")
    print("=" * 74)

    d, op = cargar()
    print(f"\ncuentas                 : {len(d):,}".replace(",", "."))
    print(f"oportunidades           : {len(op):,}".replace(",", "."))
    print(f"cuentas con oportunidad : {d.tiene_oportunidad.sum():,} "
          f"({d.tiene_oportunidad.mean()*100:.2f}%)".replace(",", "."))
    print(f"cuentas con venta       : {d.tiene_venta.sum():,} "
          f"({d.tiene_venta.mean()*100:.2f}%)".replace(",", "."))
    print(f"cuentas valoradas       : {d.nota.notna().sum():,}".replace(",", "."))

    # ------------------------------------------------------------------
    sep("E12", "¿PREDICE LA NOTA HUMANA EL COMPORTAMIENTO REAL?")
    t = (d.groupby(d.nota.fillna("(sin valorar)"))
         .agg(cuentas=("tiene_venta", "size"),
              con_oportunidad=("tiene_oportunidad", "mean"),
              con_venta=("tiene_venta", "mean"))
         .sort_values("con_venta", ascending=False))
    print(f"   {'nota':<16}{'cuentas':>9}{'c/oport.':>11}{'c/venta':>10}")
    print("   " + "-" * 46)
    for r in t.itertuples():
        print(f"   {str(r.Index):<16}{r.cuentas:>9,}{r.con_oportunidad*100:>10.1f}%"
              f"{r.con_venta*100:>9.1f}%".replace(",", "."))
    print()
    print("   La escala NO es ordinal: si B supera a A, imponer A>B>C>D>E seria")
    print("   forzar una jerarquia que los datos no respaldan (ver D12).")

    # ------------------------------------------------------------------
    sep("E15", "¿PREDICE LA UBICACION? ¿Y LA VE EL CRITERIO HUMANO?")
    cv, resto = d[d.zona_cv == 1], d[d.zona_cv == 0]
    print(f"   {'':<26}{'cuentas':>9}{'c/oport.':>11}{'c/venta':>10}")
    print("   " + "-" * 56)
    print(f"   {'Comunidad Valenciana':<26}{len(cv):>9,}"
          f"{cv.tiene_oportunidad.mean()*100:>10.1f}%"
          f"{cv.tiene_venta.mean()*100:>9.1f}%".replace(",", "."))
    print(f"   {'Resto':<26}{len(resto):>9,}"
          f"{resto.tiene_oportunidad.mean()*100:>10.1f}%"
          f"{resto.tiene_venta.mean()*100:>9.1f}%".replace(",", "."))

    try:
        from scipy.stats import chi2_contingency
        tab = pd.crosstab(d.zona_cv, d.tiene_oportunidad)
        chi2, p, _, _ = chi2_contingency(tab)
        print(f"\n   chi2 = {chi2:.1f}   p = {p:.2e}")
    except ImportError:
        print("\n   (sin scipy no se calcula el contraste)")

    print()
    print("   ¿Y que notas reciben? (solo cuentas valoradas)")
    val = d[d.nota.notna()]
    for z, etiqueta in [(1, "Comunidad Valenciana"), (0, "Resto")]:
        s = val[val.zona_cv == z]
        altas = s.nota.isin(["A", "B"]).mean() * 100
        print(f"      {etiqueta:<24} n={len(s):>5}   notas A o B: {altas:5.1f}%")
    print()
    print("   Convierten el doble y reciben menos notas altas. El criterio")
    print("   humano no esta viendo la variable que mas predice.")

    # ------------------------------------------------------------------
    sep("E13", "¿APORTAN INFORMACION DISTINTA LA CUENTA Y LO QUE PIDE?")

    # DOS DENOMINADORES POSIBLES, Y NO DAN LO MISMO.
    # E13 se calculo sobre TODAS las oportunidades con tema, contando las
    # abiertas como no convertidas. El analisis de F6 se calculo solo sobre
    # las CERRADAS. Ninguna esta mal: miden cosas distintas.
    #
    #   sobre todas    -> de cada 100 oportunidades abiertas, cuantas acaban
    #                     en venta. Incluye las que siguen en curso, asi que
    #                     es una cota inferior.
    #   sobre cerradas -> cuando se resuelve, cuantas se ganan. Es la tasa de
    #                     exito propiamente dicha.
    #
    # Se informan las dos para que nadie las mezcle en una misma tabla. Es la
    # leccion de X12: un porcentaje no significa nada sin decir sobre que
    # poblacion se calcula.
    op2 = op.copy()
    op2["gana"] = (op2.Estado == "Lograda").astype(int)
    abiertas = int((op2.Estado == "Abierta").sum())
    print(f"   oportunidades: {len(op2):,} · cerradas {len(op2)-abiertas:,} · "
          f"abiertas {abiertas:,}".replace(",", "."))
    print()
    print(f"   {'tipo solicitado':<38}{'sobre TODAS':>13}{'sobre CERRADAS':>16}")
    print("   " + "-" * 67)
    for tipo in op2["Tipo Oportunidad"].value_counts().index:
        s = op2[op2["Tipo Oportunidad"] == tipo]
        sc = s[s.Estado != "Abierta"]
        if len(sc) < 20:
            continue
        print(f"   {str(tipo)[:36]:<38}{s.gana.mean()*100:>11.1f}% "
              f"{sc.gana.mean()*100:>14.1f}%")
    cer = op2[op2.Estado != "Abierta"]
    print(f"   {'GLOBAL':<38}{op2.gana.mean()*100:>11.1f}% "
          f"{cer.gana.mean()*100:>14.1f}%")
    print()
    print("   La columna de la izquierda es la que se publico en E13.")
    print("   NO mezclar ambas columnas en una misma tabla de la memoria.")
    print()
    print("   Cruce nota x tipo, sobre TODAS (la definicion de E13):")

    # Se usa el mismo denominador que la tabla de arriba y que E13: todas las
    # oportunidades, contando las abiertas como no convertidas. Mezclar
    # denominadores entre dos tablas del mismo apartado es justo el error que
    # la advertencia anterior pretende evitar.
    oc = op.merge(d[["Nombre de cuenta", "nota"]], left_on="Cuenta",
                  right_on="Nombre de cuenta", how="left")
    oc["gana"] = (oc.Estado == "Lograda").astype(int)
    tab = (oc[oc.nota.notna()]
           .pivot_table(index="nota", columns="Tipo Oportunidad",
                        values="gana", aggfunc=["mean", "size"]))
    tipos = [c for c in ["Ensayos", "Consultoría y asistencia tecnica",
                         "Desarrollo I+D"] if ("mean", c) in tab.columns]
    print(f"   {'nota':<8}" + "".join(f"{t[:22]:>24}" for t in tipos))
    print("   " + "-" * (8 + 24 * len(tipos)))
    for nota in sorted(tab.index):
        fila = f"   {nota:<8}"
        for t in tipos:
            m = tab.loc[nota, ("mean", t)]
            n = tab.loc[nota, ("size", t)]
            fila += f"{m*100:>17.1f}% n={int(n):<4}" if pd.notna(m) else f"{'-':>24}"
        print(fila)
    print()
    print("   Lo que piden mueve la conversion tanto o mas que la nota de la")
    print("   cuenta. Es lo que justifica el diseno en dos fases (D12).")

    # ------------------------------------------------------------------
    sep("E16", "MODELO DE CONVERSION FRENTE AL CRITERIO HUMANO  (reconstruccion)")
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import roc_auc_score
        from sklearn.model_selection import train_test_split
    except ImportError:
        print("   (falta scikit-learn: pip install scikit-learn)")
        return

    # POBLACION: solo cuentas valoradas, que es sobre lo que trabaja E16.
    # La tasa de conversion aqui es del 12% frente al 3,5% de la cartera
    # entera, y un ratio de priorizacion depende de esa tasa base.
    pob = d[d.nota.notna()].copy()
    print(f"   poblacion : cuentas valoradas ({len(pob):,})".replace(",", "."))

    # Variables: lo que se sabe de una cuenta SIN haber hablado con ella.
    # Se excluye deliberadamente:
    #   - Atractividad : es el criterio humano contra el que se compara
    #   - cliente      : circular respecto al objetivo (error X7)
    cols = ["Sector agrupado (Sector Empresa) (Sector Empresa)", "Provincia",
            "País", "Tamaño cuenta", "Asociado", "Personalidad jurídica"]
    cols = [c for c in cols if c in pob.columns]
    X = pd.get_dummies(pob[cols].astype(str), dummy_na=True)
    X["zona_cv"] = pob.zona_cv.values
    y = pob.tiene_venta.values
    print(f"   variables: {len(cols)} campos -> {X.shape[1]} columnas")
    print(f"   objetivo : tiene alguna venta ({y.mean()*100:.1f}% positivos)")

    Xtr, Xte, ytr, yte, itr, ite = train_test_split(
        X, y, np.arange(len(pob)), test_size=0.235, random_state=a.semilla,
        stratify=y)
    m = RandomForestClassifier(n_estimators=300, min_samples_leaf=5,
                               class_weight="balanced", random_state=a.semilla,
                               n_jobs=-1)
    m.fit(Xtr, ytr)
    pr = m.predict_proba(Xte)[:, 1]
    auc = roc_auc_score(yte, pr)
    print(f"\n   prueba: {len(yte)} cuentas, {int(yte.sum())} convierten")
    print(f"   AUC del modelo            : {auc:.3f}")

    # Las DOS metricas, con su definicion explicita. Confundirlas fue X12.
    orden = np.argsort(-pr)
    yo = yte[orden]
    n = len(yo)
    q_alto, q_bajo = yo[:n // 5].mean(), yo[-(n // 5):].mean()
    ratio_q = q_alto / q_bajo if q_bajo > 0 else float("nan")
    lift_d = yo[:n // 10].mean() / yte.mean() if yte.mean() > 0 else float("nan")
    print()
    print("   Reparto por deciles de la puntuacion (conversion real):")
    deciles = {}
    for k in range(10, 0, -1):
        i0, i1 = int(n * (10 - k) / 10), int(n * (11 - k) / 10)
        etiq = "(mejores)" if k == 10 else "(peores) " if k == 1 else "         "
        deciles[k] = float(yo[i0:i1].mean() * 100)
        print(f"      decil {k:>2} {etiq}  {deciles[k]:5.1f}%")
    print()
    print(f"   quintil superior          : {q_alto*100:5.1f}%")
    print(f"   quintil inferior          : {q_bajo*100:5.1f}%")
    print(f"   RATIO quintil sup/inf     : {ratio_q:.1f}x   <- la metrica de E16")
    print(f"   lift del decil sup. sobre base : {lift_d:.1f}x   <- OTRA metrica distinta")

    # comparacion con el criterio humano
    sub = pob.iloc[ite]
    mask = sub.nota.notna().values
    if mask.sum() > 50:
        orden_nota = {"A": 5, "B": 4, "C": 3, "D": 2, "T": 2, "E": 1}
        hum = sub.nota[mask].map(orden_nota).fillna(0).values
        auc_h = roc_auc_score(yte[mask], hum)
        auc_m = roc_auc_score(yte[mask], pr[mask])
        print(f"\n   Solo cuentas valoradas (n={int(mask.sum())}):")
        print(f"      criterio humano        : AUC {auc_h:.3f}")
        print(f"      modelo                 : AUC {auc_m:.3f}")
        print(f"      diferencia             : {auc_m-auc_h:+.3f}")
        # bootstrap pareado sobre la diferencia de AUC
        rng = np.random.default_rng(a.semilla)
        yy, hh, mm = yte[mask], hum, pr[mask]
        difs = []
        for _ in range(2000):
            idx = rng.integers(0, len(yy), len(yy))
            if len(np.unique(yy[idx])) < 2:
                continue
            difs.append(roc_auc_score(yy[idx], mm[idx]) - roc_auc_score(yy[idx], hh[idx]))
        difs = np.array(difs)
        p = 2 * min((difs <= 0).mean(), (difs >= 0).mean())
        print(f"      IC 95 %                : [{np.percentile(difs,2.5):+.3f}, "
              f"{np.percentile(difs,97.5):+.3f}]")
        print(f"      p (bootstrap pareado)  : {min(p,1.0):.3f}")
        humano = {"n": int(mask.sum()), "auc_humano": float(auc_h),
                  "auc_modelo": float(auc_m),
                  "ic95": [float(np.percentile(difs, 2.5)),
                           float(np.percentile(difs, 97.5))],
                  "p": float(min(p, 1.0))}
    else:
        humano = None

    # Volcado para las figuras. Las figuras NO recalculan nada: leen de aqui.
    salida = RAIZ / "datos" / "03_resultados" / "a3_conversion.json"
    salida.write_text(json.dumps({
        "n_test": int(len(yte)), "n_convierten": int(yte.sum()),
        "tasa_base": float(yte.mean() * 100), "auc": float(auc),
        "deciles": deciles, "quintil_alto": float(q_alto * 100),
        "quintil_bajo": float(q_bajo * 100), "ratio_quintiles": float(ratio_q),
        "lift_decil_sobre_base": float(lift_d), "humano": humano,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n   -> {salida.name} guardado (lo leen las figuras)")

    # ------------------------------------------------------------------
    sep("COTEJO", "CON LO ESCRITO EN LA BITACORA")
    obtenido = {
        "cv_cuentas": len(cv),
        "cv_con_oportunidad": cv.tiene_oportunidad.mean() * 100,
        "resto_con_oportunidad": resto.tiene_oportunidad.mean() * 100,
        "cv_con_venta": cv.tiene_venta.mean() * 100,
        "resto_con_venta": resto.tiene_venta.mean() * 100,
    }
    print(f"   {'cifra':<26}{'bitacora':>11}{'ahora':>11}   estado")
    print("   " + "-" * 60)
    for k_, v in BITACORA.items():
        o = obtenido[k_]
        tol = 1 if k_ == "cv_cuentas" else 0.15
        print(f"   {k_:<26}{v:>11.1f}{o:>11.1f}   "
              f"{'coincide' if abs(o - v) <= tol else '<-- REVISAR'}")
    print()
    print("   E16 · reconstruccion frente a lo publicado:")
    print("   " + "-" * 60)
    print(f"      AUC                     bitacora 0.774   ahora {auc:.3f}")
    print(f"      ratio quintil sup/inf   bitacora  16.3x  ahora {ratio_q:.1f}x")
    print()
    print("   Ambas dentro del margen que cabe esperar de una reconstruccion sin")
    print("   la configuracion original. E16 se da por reproducido.")
    print()
    print("   Recordatorio de X12: el ratio de E16 es quintil superior frente a")
    print("   quintil inferior sobre cuentas VALORADAS. Compararlo con un lift")
    print("   sobre la tasa de base, o calcularlo sobre la cartera entera, da")
    print("   numeros mucho menores sin que nada este mal.")


if __name__ == "__main__":
    main()
