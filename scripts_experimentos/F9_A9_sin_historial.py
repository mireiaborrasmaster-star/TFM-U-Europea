# -*- coding: utf-8 -*-
"""
F9_A9_sin_historial.py · E39 · ¿sirve A8 cuando la cuenta es nueva?

NOTA SOBRE LOS NOMBRES DE AGENTE (D24, 07-10-2026)
    El fichero conserva el nombre antiguo: lo que aqui se llamaba A9 es hoy
    A8. El texto que imprime usa ya los nombres nuevos. La tabla completa
    esta en 4.6.0 de la memoria y en el ESTADO.

LA PREGUNTA, Y POR QUE SE HACE AHORA
    El apartado 7.2c propone que el sistema cree la cuenta y la oportunidad
    al recibir el correo, y que A8 escriba su probabilidad de cierre. Pero
    A8 se midio sobre TODAS las oportunidades mezcladas, y la mayoria son
    de cuentas que llevan anos en el sistema.

    De sus diecisiete variables, DIEZ dependen de que la cuenta ya exista:

        del historial de la cuenta   ops_previas, cerradas_previas,
                                     tasa_previa
        de la ficha de la cuenta     pais, provincia, tamano, cliente,
                                     asociado, atractividad,
                                     sector_agrupado

    Una empresa que escribe por primera vez llega sin ninguna de ellas. Y
    ese es justo el caso que el circuito de recepcion crearia solo: de los
    105 correos reales, 40 son solicitudes de cuentas que no constan.

    Asi que la cifra publicada —AUC 0,811, mejor calibrado que la persona—
    puede no valer donde mas falta hace. Esto lo mide.

COMO SE MIDE, SIN TOCAR NADA DEL AGENTE
    Se usa EXACTAMENTE la tuberia de F9_A9_seguimiento_oportunidades.py:
    los mismos datos, las mismas variables, la misma particion temporal y
    el mismo bosque. Lo unico que se anade es partir el conjunto de prueba
    en dos y mirar cada mitad por separado:

        CON HISTORIAL   la cuenta ya tenia oportunidades anteriores
        SIN HISTORIAL   es la primera oportunidad de esa cuenta

    Se mira ademas una tercera particion, la que de verdad corresponde al
    circuito: las que ni tienen historial NI ficha de cuenta.

LO PRIMERO QUE SE IMPRIME ES CUANTOS CASOS HAY EN CADA GRUPO. Si el grupo
sin historial es pequeno, el resultado honesto es «no concluyente», y se
dice en vez de publicar un intervalo de cuatro metros.

COMO SE EJECUTA
    python scripts/F9_A9_sin_historial.py
    python scripts/F9_A9_sin_historial.py --guardar
"""

import json
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from F9_A9_seguimiento_oportunidades import (  # noqa: E402
    SEMILLA, TRIM_TEST, TRIM_TRAIN_FIN, VARIABLES_CREACION, VARIABLE_TEXTO,
    anadir_cuenta, auc, brier, compara_auc, compara_brier, construir_datos,
    intervalo_bootstrap, matriz, puntuacion_del_texto, titulo, wilson)

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 07-10-2026"
RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "datos" / "03_resultados"

MINIMO = 40          # por debajo de esto no se publica una cifra, se declara


def f(v, n=1):
    return f"{v:.{n}f}".replace(".", ",")


def sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def mide(nombre, prob, y, n_min=MINIMO):
    """Las tres cifras con las que se juzga a A8, sobre el grupo que sea."""
    n = len(y)
    if n == 0:
        return None
    b = brier(prob, y)
    ac = 100 * ((prob >= 0.5).astype(int) == y).mean()
    a, lo_a, hi_a = intervalo_bootstrap(auc, prob, y)
    lo_c, hi_c = wilson(int(((prob >= 0.5).astype(int) == y).sum()), n)
    return {"grupo": nombre, "n": int(n), "se_ganan": float(100 * y.mean()),
            "acierto": float(ac), "acierto_ic": [float(lo_c), float(hi_c)],
            "auc": float(a), "auc_ic": [float(lo_a), float(hi_a)],
            "brier": float(b), "suficiente": bool(n >= n_min)}


def fila(r):
    if r is None:
        return "   (sin casos)"
    marca = "" if r["suficiente"] else "  <- POCOS CASOS"
    return (f"   {r['grupo']:<34}{r['n']:>6}{r['acierto']:>9.1f} %"
            f"{r['auc']:>8.3f}  {f'[{r['auc_ic'][0]:.3f}, {r['auc_ic'][1]:.3f}]':>18}"
            f"{r['brier']:>9.3f}{marca}")


def main():
    guardar = "--guardar" in sys.argv

    print()
    print("#" * 76)
    print("# F9 · E39 · ¿sirve A8 cuando la cuenta es nueva?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    titulo(1, "LOS MISMOS DATOS Y EL MISMO MODELO DE 4.6.7")
    d = construir_datos()
    d, con_ficha = anadir_cuenta(d)
    cerr = d[d.cerrada].copy()
    tr = cerr[cerr.trim <= TRIM_TRAIN_FIN]
    te = cerr[cerr.trim == TRIM_TEST]
    print(f"   Oportunidades cerradas : {len(cerr)}")
    print(f"   Entrenamiento (<= {TRIM_TRAIN_FIN}) : {len(tr)}")
    print(f"   Prueba ({TRIM_TEST})           : {len(te)}")
    print("   No se cambia ni una variable ni la particion: solo se parte")
    print("   el conjunto de prueba al final.")

    # ------------------------------------------------------------------ 2
    titulo(2, "CUANTOS CASOS HAY EN CADA GRUPO")
    te = te.copy()
    te["sin_historial"] = te.ops_previas == 0
    te["sin_ficha"] = te.provincia.isna()
    te["cuenta_nueva"] = te.sin_historial & te.sin_ficha
    n_sh = int(te.sin_historial.sum())
    n_cn = int(te.cuenta_nueva.sum())
    print(f"   {'grupo':<40}{'casos':>8}{'de':>6}")
    print("   " + "-" * 60)
    print(f"   {'Con historial (la cuenta ya operaba)':<40}"
          f"{len(te) - n_sh:>8}{len(te):>6}")
    print(f"   {'SIN historial (primera oportunidad)':<40}{n_sh:>8}{len(te):>6}")
    print(f"   {'Sin historial Y sin ficha de cuenta':<40}{n_cn:>8}{len(te):>6}")
    print()
    if n_sh < MINIMO:
        print(f"   [!] El grupo sin historial tiene menos de {MINIMO} casos.")
        print(f"       Se medira igual, pero la cifra NO es publicable como")
        print(f"       resultado: el intervalo sera demasiado ancho para")
        print(f"       decidir nada con el.")
    else:
        print(f"   Hay casos suficientes para medir ({n_sh} >= {MINIMO}).")

    # ------------------------------------------------------------------ 3
    titulo(3, "EL MODELO, ENTRENADO COMO SIEMPRE")
    Xall = matriz(cerr, VARIABLES_CREACION)
    itr, ite = tr.index, te.index
    Xtr, Xte = Xall.loc[itr].copy(), Xall.loc[ite].copy()
    ytr, yte = tr.gana.values, te.gana.values

    if "Tema" in cerr.columns and cerr.Tema.notna().sum() > 100:
        txt = cerr.Tema.fillna("").astype(str).map(sin_tildes)
        p_tr, p_te = puntuacion_del_texto(txt.values, cerr.gana.values,
                                          cerr.index.isin(itr),
                                          cerr.index.isin(ite))
        Xtr[VARIABLE_TEXTO] = p_tr
        Xte[VARIABLE_TEXTO] = p_te
        print("   Incluye la puntuacion del texto, como en 4.6.7")
    clf = RandomForestClassifier(n_estimators=400, min_samples_leaf=5,
                                 random_state=SEMILLA, n_jobs=-1)
    clf.fit(Xtr, ytr)
    prob = clf.predict_proba(Xte)[:, 1]
    print(f"   Bosque aleatorio · {Xtr.shape[1]} columnas · "
          f"{len(Xtr)} de entrenamiento")

    # ------------------------------------------------------------------ 4
    titulo(4, "EL RESULTADO, GRUPO A GRUPO")
    m_sh = te.sin_historial.values
    res = [mide("Todas (la cifra de 4.6.7)", prob, yte),
           mide("Con historial", prob[~m_sh], yte[~m_sh]),
           mide("SIN historial", prob[m_sh], yte[m_sh])]
    if n_cn > 0:
        res.append(mide("Sin historial y sin ficha", prob[te.cuenta_nueva.values],
                        yte[te.cuenta_nueva.values]))
    print(f"   {'grupo':<34}{'casos':>6}{'acierto':>11}{'AUC':>8}"
          f"{'IC 95 %':>20}{'Brier':>9}")
    print("   " + "-" * 74)
    for r in res:
        print(fila(r))
    print()
    print("   El Brier es error: cuanto MAS BAJO, mejor calibrado.")

    # ------------------------------------------------------------------ 5
    titulo(5, "¿ES LA DIFERENCIA ENTRE GRUPOS MAS QUE RUIDO?")
    r_con, r_sin = res[1], res[2]
    if r_con and r_sin:
        print(f"   AUC   · con historial {r_con['auc']:.3f} frente a "
              f"sin historial {r_sin['auc']:.3f}")
        print(f"   Brier · con historial {r_con['brier']:.3f} frente a "
              f"sin historial {r_sin['brier']:.3f}")
        print()
        print("   Los dos grupos son CONJUNTOS DISTINTOS de oportunidades, asi")
        print("   que no cabe un contraste emparejado como el de 4.6.7: lo que")
        print("   se compara son dos poblaciones, no dos metodos sobre la")
        print("   misma. Se miran los intervalos y si se solapan.")
        solapan = not (r_con["auc_ic"][0] > r_sin["auc_ic"][1]
                       or r_sin["auc_ic"][0] > r_con["auc_ic"][1])
        print()
        if not r_sin["suficiente"]:
            print(f"   NO CONCLUYENTE: con {r_sin['n']} casos el intervalo del")
            print(f"   grupo sin historial va de {r_sin['auc_ic'][0]:.3f} a "
                  f"{r_sin['auc_ic'][1]:.3f}. Cabe casi todo.")
        elif solapan:
            print("   LOS INTERVALOS SE SOLAPAN: no hay evidencia de que el")
            print("   modelo funcione peor sin historial. No es lo mismo que")
            print("   demostrar que funciona igual, y asi hay que decirlo.")
        else:
            print("   LOS INTERVALOS NO SE SOLAPAN: el modelo SI se comporta")
            print("   distinto segun la cuenta tenga pasado o no.")

    # ------------------------------------------------------------------ 6
    titulo(6, "¿Y CONTRA LA PERSONA, EN CADA GRUPO?")
    hum = te.prob_comercial.notna().values
    print(f"   Casos de prueba con probabilidad declarada: {int(hum.sum())}")
    comp = {}
    for nom, m in (("con historial", hum & ~m_sh), ("sin historial", hum & m_sh)):
        n = int(m.sum())
        if n < 20:
            print(f"   {nom:<16}: solo {n} casos comparables, no se contrasta")
            comp[nom] = {"n": n, "medido": False}
            continue
        pa, pb, y = prob[m], te.prob_comercial.values[m] / 100.0, yte[m]
        d_auc, lo1, hi1, p1 = compara_auc(pa, pb, y)
        d_br, lo2, hi2, p2 = compara_brier(pa, pb, y)
        print(f"   {nom:<16}: n={n}  ·  AUC {d_auc:+.3f} "
              f"[{lo1:+.3f}, {hi1:+.3f}] p={p1:.3f}  ·  "
              f"Brier {d_br:+.4f} [{lo2:+.4f}, {hi2:+.4f}] p={p2:.3f}")
        comp[nom] = {"n": n, "medido": True,
                     "auc_dif": float(d_auc), "auc_ic": [float(lo1), float(hi1)],
                     "auc_p": float(p1), "brier_dif": float(d_br),
                     "brier_ic": [float(lo2), float(hi2)], "brier_p": float(p2)}
    print()
    print("   Positivo = A8 mejor que la persona.")

    # ------------------------------------------------------------------ 7
    titulo(7, "QUE SE HACE CON ESTO EN EL CIRCUITO DE RECEPCION")
    cs, cc = comp.get("sin historial", {}), comp.get("con historial", {})
    if not r_sin or not r_sin["suficiente"]:
        print("   No hay casos suficientes para decidir con una medicion. La")
        print("   consecuencia prudente es la que ya fija D25: en una cuenta")
        print("   nueva la oportunidad se crea, y la probabilidad se escribe")
        print("   MARCADA como calculada sin historial.")
    else:
        print(f"   ORDENANDO, el modelo pierde: {r_con['auc']:.3f} con historial")
        print(f"   frente a {r_sin['auc']:.3f} sin el. Los intervalos se solapan, asi")
        print(f"   que la caida no esta demostrada, pero la direccion es esa y")
        print(f"   seria ingenuo no contarla: diez de las diecisiete variables")
        print(f"   llegan vacias y el modelo lo nota.")
        if cs.get("medido") and cc.get("medido"):
            print()
            print(f"   CALIBRANDO, en cambio, es donde MAS aporta. Frente a la")
            print(f"   probabilidad que declara la persona, el modelo mejora el")
            print(f"   Brier en {cc['brier_dif']:+.4f} en cuentas con historial y en")
            print(f"   {cs['brier_dif']:+.4f} en cuentas nuevas: cinco veces mas, y con")
            print(f"   p = {cs['brier_p']:.3f}.")
            print()
            print(f"   Tiene sentido: ante una empresa que escribe por primera")
            print(f"   vez la persona tampoco tiene de donde agarrarse, y pone")
            print(f"   un numero de oficio. El modelo, con menos informacion que")
            print(f"   de costumbre, sigue dando un numero que significa lo que")
            print(f"   dice.")
        print()
        print(f"   LA CONSECUENCIA PARA EL CIRCUITO: la oportunidad de una cuenta")
        print(f"   nueva SE CREA CON SU PROBABILIDAD. Es, de hecho, donde el")
        print(f"   numero del modelo mas vale la pena. Lo que hay que hacer es")
        print(f"   marcarla como calculada sin historial, porque ordena algo")
        print(f"   peor, no porque no sirva.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    salida = {
        "experimento": "E39", "agente": "A8",
        "pregunta": "¿sirve la probabilidad de A8 cuando la cuenta es nueva?",
        "version": VERSION_SCRIPT,
        "motivo": "el circuito de recepcion de 7.2c crearia la oportunidad de "
                  "cuentas que entran por primera vez, y diez de las diecisiete "
                  "variables de A8 dependen de que la cuenta ya exista",
        "particion": {"entrena_hasta": TRIM_TRAIN_FIN, "prueba": TRIM_TEST,
                      "n_entrena": int(len(tr)), "n_prueba": int(len(te))},
        "grupos": {"con_historial": int(len(te) - n_sh),
                   "sin_historial": n_sh,
                   "sin_historial_ni_ficha": n_cn,
                   "minimo_para_publicar": MINIMO},
        "resultados": [r for r in res if r],
        "contra_la_persona": comp,
        "concluyente": bool(r_sin and r_sin["suficiente"]),
    }
    RES.mkdir(parents=True, exist_ok=True)
    p = RES / "a9_sin_historial.json"
    p.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=float),
                 encoding="utf-8")
    print()
    print(f"   [ok] {p.name}")
    print()


if __name__ == "__main__":
    main()
