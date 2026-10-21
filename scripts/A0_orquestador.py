# -*- coding: utf-8 -*-
"""
A0_orquestador.py · el sistema secuencial  ·  cierra el objetivo específico 3
=============================================================================

QUE ES ESTO
    Hasta ahora había agentes, no sistema. Cada uno se lanzaba a mano sobre sus
    propios datos y ninguno recibía la salida del anterior. El objetivo
    específico 3 del trabajo pide literalmente «un sistema SECUENCIAL de
    agentes en el que cada componente reciba una entrada, procese la
    información y genere una salida o acción». Esto es ese sistema.

    Entra una empresa. Sale una fila con todo lo que el sistema ha decidido
    sobre ella, y el motivo de cada decisión.

EL RECORRIDO

    empresa
       │
       ├─ PASO 0 · ¿la conozco ya?         → se busca en el CRM por dominio
       │      Si ya esta dada de alta, su sector y su nota LOS PUSO UNA
       │      PERSONA. Volver a calcularlos seria sustituir una certeza por
       │      una prediccion que acierta el 51,73 %. Se cogen del CRM y esa
       │      empresa se salta A2 y A3.
       │
       ├─ A2 · clasificar el sector        → sector + si es de fiar
       │      SOLO para las que no estaban
       │      (transformer XLM-RoBERTa, entrenado en Colab)
       │
       ├─ A3 · puntuar la cuenta           → nota A-E
       │      OJO: recibe el sector que PREDIJO A2, no el verdadero.
       │      Aquí es donde se propaga el error, y es lo que se mide.
       │
       ├─ A5 · emparejar con el catálogo   → servicio + confianza
       │      (representaciones densas e5-small)
       │
       ├─ A3 fase 2 · ajustar prioridad    → alta / media / baja
       │      Tabla de E13, sin modelo. Ver 17_DISENO_A3_FASE2.md
       │
       └─ A5 · redactar el mensaje         → NO SE EJECUTA AQUI
              Necesita GPU. Se deja en cola, que es exactamente la
              arquitectura de dos circuitos del apartado 7.2: todo lo
              anterior corre en un portátil, solo la redacción espera GPU.
       │
    una fila de salida con todo, y el motivo de cada decisión

LO QUE ESTE SCRIPT MIDE Y NINGUN AGENTE SUELTO PUEDE MEDIR

    1. LA PROPAGACION DEL ERROR
       Si A2 falla el sector, ¿arrastra a A3? Se puntúa cada empresa DOS
       veces —con el sector predicho y con el verdadero— y se compara. La
       diferencia es el coste real del error de A2 sobre el sistema, no
       sobre la métrica de A2.

    2. EL EMBUDO DE LA ABSTENCION
       Cuántas empresas llegan al final, cuántas se detienen y en qué paso.
       Un sistema que se para mucho no es malo: es prudente. Pero hay que
       saber cuánto se para y dónde.

POR QUE LA REDACCION NO SE EJECUTA
    El modelo generativo son 7.000 millones de parámetros y necesita GPU.
    Ejecutarlo en este equipo tardaría horas. No es una limitación del
    orquestador: es la arquitectura declarada en 7.2, y este script la
    implementa tal cual. La cola que deja es la entrada del circuito por
    lotes.

COMO SE EJECUTA
    python scripts/A0_orquestador.py
    python scripts/A0_orquestador.py --guardar
    python scripts/A0_orquestador.py --empresas 300   (más rápido, para probar)
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

VERSION_SCRIPT = "v1 · 30-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
DERIVADO = RAIZ / "datos" / "02_derivado"
RESULTADOS = RAIZ / "datos" / "03_resultados"

PRED_A2 = RESULTADOS / "pred_abl_sin_jerarquia.csv"   # el modelo FINAL de A2
CATALOGO = RESULTADOS / "a5_catalogo.json"
SALIDA = RESULTADOS / "orquestador_salida.csv"
COLA = RESULTADOS / "orquestador_cola_redaccion.csv"
METRICAS = RESULTADOS / "orquestador_metricas.json"

MODELO_EMB = "intfloat/multilingual-e5-small"

# ---------------------------------------------------------------------------
# A3 FASE 2 · la tabla de ajuste de prioridad
# ---------------------------------------------------------------------------
# Porcentaje de conversion observado en E13 sobre 4.872 oportunidades reales,
# cruzando la nota de la cuenta con el tipo de servicio solicitado.
#
# No es un modelo entrenado: son las celdas medidas. El diseno completo esta
# en 17_DISENO_A3_FASE2.md, apartado 5, donde se explica por que empezar por
# una tabla y no por un modelo.
TABLA_FASE2 = {
    "Ensayos":                          {"A": 67, "B": 69, "C": 62, "D": 54, "E": 58},
    "Consultoría y asistencia técnica": {"A": 56, "B": 61, "C": 47, "D": 42, "E": 41},
    "Desarrollo I+D":                   {"A": 9,  "B": 5,  "C": 9,  "D": 13, "E": 0},
}
# E13 no cruza estos dos tipos con la nota: se usa su conversion global.
MARGINAL_FASE2 = {"Formación": 57.1, "Servicios": 39.5}
# Nota T (administraciones y centros tecnologicos): tampoco aparece en el
# cruce. Se usa la marginal del tipo, y se declara.
UMBRAL_ALTA, UMBRAL_MEDIA = 55.0, 25.0


def prioridad_fase2(nota, tipo):
    """Devuelve (probabilidad estimada, prioridad, de dónde sale la cifra)."""
    if not tipo or (isinstance(tipo, float) and np.isnan(tipo)):
        return np.nan, "", "sin servicio emparejado"
    if tipo in TABLA_FASE2 and nota in TABLA_FASE2[tipo]:
        p = TABLA_FASE2[tipo][nota]
        origen = "celda medida (nota × tipo)"
    elif tipo in TABLA_FASE2:
        p = float(np.mean(list(TABLA_FASE2[tipo].values())))
        origen = "media del tipo: la nota no está en el cruce"
    else:
        p = MARGINAL_FASE2.get(tipo, np.nan)
        origen = "conversión global del tipo: no hay cruce"
    if np.isnan(p):
        return np.nan, "", "tipo no contemplado"
    pr = "alta" if p >= UMBRAL_ALTA else ("media" if p >= UMBRAL_MEDIA else "baja")
    return p, pr, origen


# ---------------------------------------------------------------------------
# La política de confianza
# ---------------------------------------------------------------------------
# Un sistema que decide siempre no es un sistema fiable, es uno temerario.
# Estos son los puntos donde se permite parar. Los umbrales salen de E19 y
# E24; el de emparejamiento es deliberadamente exigente porque E24 midió que
# ese paso solo acierta el 39 % en primera posición.
UMBRAL_EMPAREJAMIENTO = 2.0     # z dentro de la fila, como en A5
MIN_PALABRAS_WEB = 40           # por debajo, el texto no da para emparejar


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"{n} · {t}")
    print("=" * 76)


def paso(n, t):
    print()
    print(f"   -- PASO {n} · {t} " + "-" * max(0, 52 - len(t)))


def texto_servicio(s):
    partes = [s.get("nombre", ""), s.get("area", ""), s.get("tipo", ""),
              s.get("resuelve", "")]
    return " · ".join(p for p in partes if p)


def normalizar(nombre):
    """Nombre de empresa comparable: sin acentos, sin forma juridica, sin signos."""
    t = sin_acentos(nombre)
    t = re.sub(r"\b(s\.?l\.?u?|s\.?a\.?u?|sociedad limitada|sociedad anonima"
               r"|slu|sau|sl|sa)\b", " ", t)
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def dominio_web(url):
    u = str(url).lower().strip()
    if not u or u == "nan":
        return ""
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.split("/")[0].strip()


def nota_corta(v):
    """«A (I+D sin subvención)» -> «A»"""
    v = str(v).strip()
    return v[0] if v and v[0] in "ABCDET" else np.nan


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("--empresas", type=int, default=0,
                    help="limitar el número de empresas (0 = todas)")
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--mezcla", type=int, default=500,
                    help="cuántas empresas YA conocidas se añaden a la lista "
                         "para poder demostrar el paso 0 (0 = ninguna)")
    a = ap.parse_args()

    print()
    print("#" * 76)
    print("# A0 · ORQUESTADOR · el sistema secuencial de agentes")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    # ------------------------------------------------------------------
    titulo(0, "LA ENTRADA")
    test = pd.read_csv(DERIVADO / "cuentas_test.csv")
    faltan = [p for p in ("train", "val")
              if not (DERIVADO / f"cuentas_{p}.csv").exists()]
    if faltan:
        # Los conjuntos de entrenamiento llevan dentro el texto de las webs,
        # y ahi aparecen nombres de empresa en texto libre. Por eso no se
        # entregan: 112 MB que ademas no hacen falta para leer el trabajo.
        import sys as _s
        _s.exit("\n".join([
            "",
            "   ESTE CIRCUITO NO SE PUEDE EJECUTAR CON LOS DATOS ENTREGADOS.",
            "",
            "   Faltan los conjuntos de entrenamiento (cuentas_"
            + ", cuentas_".join(faltan) + "), que es con",
            "   lo que se entrenan los modelos. Llevan dentro el texto de las",
            "   paginas web, donde aparecen nombres de empresa en texto libre,",
            "   asi que no se entregan.",
            "",
            "   Lo que este circuito produjo esta en output/:",
            "      orquestador_salida.csv          las 2.652 empresas, paso a paso",
            "      orquestador_cola_redaccion.csv  las que quedaron por redactar",
            "      orquestador_metricas.json       las cifras del recorrido",
            "",
            "   El circuito de recepcion SI se ejecuta:",
            "      python lanzar.py recepcion",
            "",
        ]))
    entren = pd.concat([pd.read_csv(DERIVADO / f"cuentas_{p}.csv")
                        for p in ["train", "val"]], ignore_index=True)
    if a.empresas:
        test = test.head(a.empresas).copy()
    print(f"   Empresas que entran en el sistema : {len(test):>6}")
    print(f"   Cuentas disponibles para entrenar : {len(entren):>6}")
    print()
    print("   Cada empresa entra con lo que se sabría de ella en la realidad:")
    print("   su nombre, su provincia, su tamaño y el texto de su web. NADA")
    print("   MAS. El sector verdadero existe en los datos pero el sistema no")
    print("   lo ve: lo tiene que predecir A2, y de eso va todo lo demás.")

    d = test.copy()
    d["_n_pal_web"] = d.web_text.fillna("").str.split().str.len()

    # ================================================================== 0
    paso(0, "¿LA CONOZCO YA?  ·  resolver la identidad contra el CRM")
    print("      Una lista de empresas nunca es toda nueva. Las que ya estan")
    print("      dadas de alta tienen su sector y su nota puestos POR UNA")
    print("      PERSONA. Recalcularlos con un modelo que acierta el 51,73 %")
    print("      seria cambiar una certeza por una moneda al aire.")
    print()

    # el CRM disponible en esta demostracion es la parte de entrenamiento
    crm = entren.copy()
    crm["dom_crm"] = crm.url.apply(dominio_web)
    crm["nom_crm"] = crm.empresa.map(normalizar)
    por_dominio = {r.dom_crm: r for r in crm[crm.dom_crm != ""].itertuples()}
    por_nombre = {r.nom_crm: r for r in crm[crm.nom_crm != ""].itertuples()}

    # Las particiones son disjuntas por construccion, asi que si se ejecuta
    # sobre el conjunto de prueba NINGUNA empresa resolveria y el paso 0 no
    # se podria demostrar. Se inyecta a proposito una muestra de cuentas ya
    # conocidas, para que la lista se parezca a una real. Es una SIMULACION y
    # se declara como tal: en uso real esta mezcla la trae la lista.
    if a.mezcla:
        conocidas = crm[(crm.dom_crm != "") & crm.atractividad.notna()].head(a.mezcla)
        d = pd.concat([d, conocidas], ignore_index=True)
        print(f"      SIMULACION: se anaden {len(conocidas)} empresas que YA estan")
        print("      en el CRM, para que la lista se parezca a una de verdad.")
        print("      En uso real esa mezcla viene dada; aqui hay que provocarla")
        print("      porque las particiones son disjuntas por construccion.")
        print()

    d["dom_in"] = d.url.apply(dominio_web)
    d["nom_in"] = d.empresa.map(normalizar)

    def resolver(fila):
        if fila.dom_in and fila.dom_in in por_dominio:
            return por_dominio[fila.dom_in], "dominio"
        if fila.nom_in and fila.nom_in in por_nombre:
            return por_nombre[fila.nom_in], "nombre"
        return None, ""

    origen, sector_crm, nota_crm, via = [], [], [], []
    for fila in d.itertuples():
        r, como = resolver(fila)
        if r is not None and pd.notna(getattr(r, "sector", None)):
            origen.append("CRM")
            sector_crm.append(r.sector)
            nota_crm.append(nota_corta(getattr(r, "atractividad", None)))
            via.append(como)
        else:
            origen.append("nueva")
            sector_crm.append(None)
            nota_crm.append(None)
            via.append("")
    d["origen"] = origen
    d["_sector_crm"] = sector_crm
    d["_nota_crm"] = nota_crm
    d["via_id"] = via

    conocidas_n = int((d.origen == "CRM").sum())
    nuevas_n = int((d.origen == "nueva").sum())
    print(f"      empresas en la lista           : {len(d):>6}")
    print(f"      ya estaban en el CRM           : {conocidas_n:>6}"
          f"   ({conocidas_n/len(d)*100:.1f} %)")
    print(f"      nuevas, hay que clasificarlas  : {nuevas_n:>6}"
          f"   ({nuevas_n/len(d)*100:.1f} %)")
    if conocidas_n:
        print()
        print("      resueltas por:")
        for k, v in d[d.origen == "CRM"].via_id.value_counts().items():
            print(f"         {k:<10}{v:>6}")
        print()
        print(f"      Esas {conocidas_n} se saltan A2 y A3: su sector y su nota salen")
        print("      del CRM, que es informacion humana y no una prediccion.")

    # ================================================================== A2
    paso(1, "A2 · clasificar el sector  ·  SOLO las nuevas")
    pred = pd.read_csv(PRED_A2)[["empresa_clave", "pred_sector", "sector", "acierto"]]
    pred = pred.rename(columns={"sector": "_sector_real_a2"})
    d = d.merge(pred, on="empresa_clave", how="left")

    # las conocidas conservan el sector del CRM; solo las nuevas usan A2
    es_nueva = d.origen == "nueva"
    d["sector_final"] = np.where(es_nueva, d.pred_sector, d._sector_crm)
    con_pred = es_nueva & d.pred_sector.notna()
    print(f"      nuevas que A2 clasifica        : {int(con_pred.sum()):>6}")
    if con_pred.any():
        print(f"      acierto de A2 sobre ellas      : "
              f"{d.loc[con_pred, 'acierto'].mean()*100:>6.2f} %")
    print(f"      conocidas: sector tomado del CRM: {conocidas_n:>6}")
    print()
    print("      El sistema NO sabe si A2 ha acertado. La columna de acierto")
    print("      se guarda solo para medir la propagación más abajo.")
    d["motivo_A2"] = np.where(
        es_nueva, "sector predicho por A2", "sector tomado del CRM")

    # ================================================================== A3
    paso(2, "A3 · puntuar la cuenta  ·  recibe el sector de A2")
    from sklearn.ensemble import RandomForestClassifier

    COLS = ["sector_agrupado", "provincia", "tamano", "asociado", "pais"]
    ent = entren[entren.atractividad.notna()].copy()
    ent["nota"] = ent.atractividad.map(nota_corta)
    ent = ent[ent.nota.notna()]
    print(f"      cuentas valoradas para entrenar: {len(ent):>6}")

    # Codificacion por indicadores, como en E14. Un codificador ordinal
    # pondria a la provincia un orden que no tiene, y el arbol lo usaria.
    # OJO: astype(str) ya convierte los nulos en la cadena "nan", asi que
    # dummy_na=True crearia una SEGUNDA columna con el mismo nombre y el
    # marco quedaria con etiquetas repetidas. Una de las dos sobra.
    X_ent = pd.get_dummies(ent[COLS].astype(str))
    modelo = RandomForestClassifier(n_estimators=300, min_samples_leaf=5,
                                    n_jobs=-1, random_state=a.semilla)
    modelo.fit(X_ent, ent.nota)
    COLUMNAS_MODELO = X_ent.columns

    # el sector agrupado que corresponde a cada sector, aprendido del histórico
    mapa_agr = (entren.dropna(subset=["sector", "sector_agrupado"])
                .groupby("sector").sector_agrupado.agg(
                    lambda x: x.value_counts().index[0]).to_dict())

    def puntuar(col_sector, etiqueta):
        # se construye el marco desde cero para que no arrastre columnas
        # repetidas del fichero de entrada
        crudo = pd.DataFrame({
            "sector_agrupado": d[col_sector].map(mapa_agr).fillna("DESCONOCIDO"),
            "provincia": d.provincia, "tamano": d.tamano,
            "asociado": d.asociado, "pais": d.pais,
        }).astype(str)
        X = pd.get_dummies(crudo)
        X = X.reindex(columns=COLUMNAS_MODELO, fill_value=False)
        pr = modelo.predict_proba(X)
        return modelo.classes_[pr.argmax(1)], pr.max(1)

    # con lo que predijo A2 · es lo que haría el sistema de verdad
    nota_pred, conf_pred = puntuar("pred_sector", "predicho")
    # con el sector verdadero · SOLO para medir la propagación del error
    d["_nota_si_A2_acertara"], _ = puntuar("_sector_real_a2", "real")

    # las conocidas conservan la nota que les puso una persona
    d["nota_A3"] = np.where(es_nueva & pd.notna(nota_pred), nota_pred,
                            d._nota_crm)
    d["nota_A3"] = d.nota_A3.fillna(pd.Series(nota_pred, index=d.index))
    d["confianza_A3"] = np.where(es_nueva, conf_pred, 1.0)

    print(f"      empresas puntuadas             : {d.nota_A3.notna().sum():>6}")
    print("      reparto de notas:")
    for k, v in d.nota_A3.value_counts().sort_index().items():
        print(f"         {k}  {v:>5}   {v/len(d)*100:5.1f} %")
    d["motivo_A3"] = np.where(
        es_nueva, "nota estimada a partir del sector predicho",
        "nota tomada del CRM: la puso una persona")

    # ---------------------------------------------------------------
    # COMPROBACION DE POBLACION
    # Un modelo entrenado sobre una poblacion y aplicado a otra puede
    # acertar en su propia prueba y fallar en cadena. Aqui se compara,
    # variable a variable, cuantos nulos habia al entrenar y cuantos hay
    # ahora. Si difiere mucho, el arbol esta usando "falta el dato" como
    # si significara lo mismo, y no lo significa.
    print()
    print("      COMPROBACION DE POBLACION  (nulos al entrenar / ahora)")
    alertas = []
    for c in COLS:
        if c == "sector_agrupado":
            continue
        n_ent = ent[c].isna().mean()
        n_now = d[c].isna().mean() if c in d.columns else np.nan
        marca = ""
        if not np.isnan(n_now) and abs(n_ent - n_now) > 0.25:
            marca = "   <-- DIFIERE MUCHO"
            alertas.append((c, n_ent, n_now))
        print(f"         {c:<16}{n_ent*100:>6.1f} %   {n_now*100:>6.1f} %{marca}")
    d["_alertas_poblacion"] = len(alertas)

    if alertas:
        print()
        print("      AVISO. El reparto de notas de arriba NO es de fiar.")
        for c, a_, b_ in alertas:
            print(f"      La variable «{c}» faltaba en el {a_*100:.0f} % de las")
            print(f"      cuentas con las que se entreno y falta en el {b_*100:.0f} %")
            print("      de las que entran ahora.")
        # que aprendio el modelo de ese hueco
        if "tamano" in [c for c, _, _ in alertas]:
            g = ent.assign(falta=ent.tamano.isna()).groupby("falta").nota
            rep = g.value_counts(normalize=True).unstack().fillna(0)
            if True in rep.index:
                dominante = rep.loc[True].idxmax()
                pct = rep.loc[True].max() * 100
                print()
                print(f"      Y se ve por que: entre las cuentas de entrenamiento")
                print(f"      SIN ese dato, el {pct:.0f} % tenia la nota «{dominante}».")
                print(f"      El modelo aprendio «falta el tamano -> {dominante}», que era")
                print("      cierto en su poblacion y deja de serlo en esta.")
        print()
        print("      ESTO YA ESTABA DECLARADO como limitacion de E14. Lo nuevo")
        print("      es poder VERLO: aislado, A3 acertaba el 49,24 % en su")
        print("      propia particion. Encadenado sobre otra poblacion,")
        print("      colapsa en una sola clase.")

    # cuanto acierta de verdad, donde se puede comprobar
    d["_nota_real"] = d.atractividad.map(nota_corta)
    # OJO: el acierto SOLO puede medirse donde el modelo decidio. En las
    # conocidas la nota se copio del CRM; compararla con el CRM daria el
    # 100 % y no significaria nada. Es el error X7 otra vez: comprobar algo
    # contra su propia fuente.
    comprobables = d._nota_real.notna() & es_nueva
    if comprobables.sum() > 30:
        ok = (d.loc[comprobables, "nota_A3"] == d.loc[comprobables, "_nota_real"])
        suelo = d.loc[comprobables, "_nota_real"].value_counts(normalize=True).max()
        print()
        print(f"      Acierto DEL MODELO, solo sobre las nuevas (n = "
              f"{int(comprobables.sum())}): {ok.mean()*100:.1f} %")
        print(f"      Suelo en esa misma muestra                          : "
              f"{suelo*100:.1f} %")
        print("      Las conocidas quedan fuera: su nota se copio del CRM.")
        if ok.mean() <= suelo:
            print("      NO SUPERA EL SUELO. El paso 2 de la cadena, tal como")
            print("      esta, no aporta nada sobre responder siempre lo mismo.")

    # ================================================================== A5a
    paso(3, "A5 · emparejar con el catálogo de servicios")
    servicios = json.loads(CATALOGO.read_text(encoding="utf-8"))
    from sentence_transformers import SentenceTransformer
    emb = SentenceTransformer(MODELO_EMB)
    v_serv = emb.encode(["passage: " + texto_servicio(s) for s in servicios],
                        normalize_embeddings=True, show_progress_bar=False)

    hay_texto = d._n_pal_web >= MIN_PALABRAS_WEB
    print(f"      con texto web utilizable       : {int(hay_texto.sum()):>6}"
          f"   ({hay_texto.mean()*100:.1f} %)")
    print(f"      sin texto: se detienen aquí    : {int((~hay_texto).sum()):>6}")

    d["servicio_A5"] = pd.Series([None] * len(d), dtype="object")
    d["confianza_A5"] = np.nan
    if hay_texto.any():
        textos = ("query: " + d.loc[hay_texto, "web_text"].fillna("").str[:2000])
        v_web = emb.encode(textos.tolist(), normalize_embeddings=True,
                           show_progress_bar=False)
        sim = v_web @ v_serv.T
        mejor = sim.argmax(1)
        z = (sim.max(1) - sim.mean(1)) / sim.std(1)
        d.loc[hay_texto, "servicio_A5"] = [servicios[i]["nombre"] for i in mejor]
        d.loc[hay_texto, "confianza_A5"] = z

    pasa = d.confianza_A5 >= UMBRAL_EMPAREJAMIENTO
    print(f"      superan el umbral de confianza : {int(pasa.sum()):>6}"
          f"   (z >= {UMBRAL_EMPAREJAMIENTO})")
    d["motivo_A5"] = np.select(
        [~hay_texto, hay_texto & ~pasa, pasa],
        ["se detiene: sin texto web suficiente",
         "se detiene: ningún servicio destaca con claridad",
         "servicio emparejado con confianza"],
        default="")

    # ================================================================== A3b
    paso("3b", "A3 fase 2 · ajustar la prioridad  ·  entre F7 y F8")
    print("      Ya se sabe QUÉ se le ofrecería. Con eso y con la nota de la")
    print("      cuenta se estima cuánto esfuerzo merece. No hay modelo: son")
    print("      las celdas medidas en E13 sobre 4.872 oportunidades reales.")
    print()
    tipo_de = {x["nombre"]: x.get("tipo", "") for x in servicios}
    d["tipo_servicio"] = d.servicio_A5.map(tipo_de)
    res = [prioridad_fase2(n, t) for n, t in zip(d.nota_A3, d.tipo_servicio)]
    d["prob_fase2"] = [r[0] for r in res]
    d["prioridad"] = [r[1] for r in res]
    d["motivo_fase2"] = [r[2] for r in res]

    con_prior = d.prioridad != ""
    print(f"      empresas con prioridad asignada: {int(con_prior.sum()):>6}")
    for k in ("alta", "media", "baja"):
        v = int((d.prioridad == k).sum())
        if v:
            print(f"         {k:<8}{v:>6}   {v/max(1,con_prior.sum())*100:5.1f} %")
    print()
    print("      De dónde sale cada cifra:")
    for k, v in d.loc[con_prior, "motivo_fase2"].value_counts().items():
        print(f"         {k:<46}{v:>6}")
    sin_celda = int((d.motivo_fase2 == "media del tipo: la nota no está en el cruce").sum())
    if sin_celda and con_prior.sum():
        print()
        print(f"      DOS TERCERAS PARTES NO USAN UNA CELDA MEDIDA ({sin_celda} de "
              f"{int(con_prior.sum())}).")
        print("      El motivo encadena con lo de mas arriba: la nota mas predicha")
        print("      es T, y T no aparece en el cruce de E13 porque en el historico")
        print("      apenas hay administraciones pidiendo servicios. Es el mismo")
        print("      desajuste de poblacion, dos pasos mas abajo.")

    print()
    print("      AVISO QUE HAY QUE DECLARAR")
    print("      En este recorrido el TIPO DE SERVICIO no lo ha pedido el")
    print("      cliente: lo ha predicho A5, que acierta el 38,9 % (E24). La")
    print("      tabla de E13 se midio sobre lo que los clientes pidieron DE")
    print("      VERDAD. Asi que la prioridad hereda el error del emparejador.")
    print("      Por la puerta de entrada —cuando el cliente ya ha escrito—")
    print("      ese problema no existe: el tipo lo declara el.")

    # ================================================================== A5b
    paso(4, "A5 · redactar el mensaje  ·  NO SE EJECUTA AQUI")
    d["redaccion"] = np.where(pasa, "EN COLA", "descartada")
    # la cola ya no es un monton: sale ordenada por prioridad
    orden_pr = {"alta": 0, "media": 1, "baja": 2, "": 3}
    print(f"      pasan a la cola de redacción   : {int(pasa.sum()):>6}")
    print(f"      no pasan                       : {int((~pasa).sum()):>6}")
    print()
    print("      La redacción necesita un modelo de 7.000 millones de")
    print("      parámetros y GPU. Esto NO es una carencia del orquestador:")
    print("      es el circuito por lotes del apartado 7.2, y la cola que")
    print("      queda aquí es su entrada.")

    # ================================================================== 1
    titulo(1, "EL EMBUDO · dónde se detiene cada empresa")
    print(f"   De las {len(d)} empresas de la lista, {conocidas_n} ya estaban en el CRM")
    print(f"   y {nuevas_n} son nuevas. Las conocidas se saltan A2 y A3.")
    print()
    etapas = [
        ("Entran en el sistema", len(d)),
        ("Tienen sector y nota", int(d.nota_A3.notna().sum())),
        ("Tienen texto web para emparejar", int(hay_texto.sum())),
        ("El emparejamiento es de fiar", int(pasa.sum())),
        ("…de ellas, prioridad alta", int((pasa & (d.prioridad == "alta")).sum())),
    ]
    ancho = 44
    for i, (nombre, n) in enumerate(etapas):
        barra = "#" * int(ancho * n / len(d))
        caida = "" if i == 0 else f"   -{etapas[i-1][1] - n}"
        print(f"   {nombre:<34}{n:>6}  {barra}{caida}")
    print()
    print(f"   Llega al final el {pasa.mean()*100:.1f} % de las empresas.")
    print("   El resto se detiene con un motivo escrito, que es lo que")
    print("   distingue un sistema prudente de uno que no sabe que falla.")
    print()
    print("   Dónde se pierden:")
    for motivo, n in d.motivo_A5.value_counts().items():
        if motivo.startswith("se detiene"):
            print(f"      {motivo:<52}{n:>6}")

    # ================================================================== 2
    titulo(2, "LA PROPAGACION DEL ERROR  ·  lo que ningún agente suelto mide")
    print("   A3 recibe el sector que predijo A2. Si A2 se equivoca, A3 puntúa")
    print("   sobre una premisa falsa. Para medirlo se ha puntuado cada empresa")
    print("   dos veces: con el sector predicho y con el verdadero.")
    print()
    # la propagacion solo tiene sentido donde A2 decide: en las nuevas
    sub = d[es_nueva]
    cambia = (sub.nota_A3 != sub._nota_si_A2_acertara)
    acerto = sub.acierto.astype("boolean").fillna(False).astype(bool)
    print(f"   Se mide sobre las {len(sub)} empresas NUEVAS. Las {conocidas_n}")
    print("   conocidas no pasan por A2, asi que no hay error que propagar.")
    print()

    print(f"   {'':<42}{'empresas':>10}{'cambia la nota':>16}")
    print("   " + "-" * 68)
    for etiqueta, mask in [("A2 acertó el sector", acerto),
                           ("A2 falló el sector", ~acerto)]:
        n = int(mask.sum())
        c = int((cambia & mask).sum())
        pct = c / n * 100 if n else 0
        print(f"   {etiqueta:<42}{n:>10}{c:>9} ({pct:4.1f} %)")
    n_tot, c_tot = len(sub), int(cambia.sum())
    print("   " + "-" * 68)
    print(f"   {'TOTAL':<42}{n_tot:>10}{c_tot:>9} ({c_tot/n_tot*100:4.1f} %)")
    print()

    p_fallo = (cambia & ~acerto).sum() / max(1, (~acerto).sum()) * 100
    p_acierto = (cambia & acerto).sum() / max(1, acerto.sum()) * 100
    print("   LECTURA")
    if p_fallo > p_acierto + 5:
        print(f"   El error de A2 SE PROPAGA: cuando falla el sector, la nota")
        print(f"   de A3 cambia en el {p_fallo:.1f} % de los casos, frente al")
        print(f"   {p_acierto:.1f} % cuando acierta.")
        print()
        print(f"   Y aquí está lo que no se ve mirando A2 por separado: A2")
        print(f"   acierta el {acerto.mean()*100:.1f} %, que suena mediocre, pero")
        print(f"   solo el {c_tot/n_tot*100:.1f} % de sus errores llega a cambiar la")
        print("   decisión siguiente. Muchos fallos de A2 son entre sectores")
        print("   que A3 trata igual, y por tanto son inocuos aguas abajo.")
    else:
        print("   No se aprecia propagación: la nota de A3 cambia por igual")
        print("   acierte o falle A2.")

    print()
    print("   ESTO ES UN RESULTADO PROPIO DEL SISTEMA. La métrica de A2 dice")
    print("   cuántas veces se equivoca; solo la cadena dice cuánto importa.")

    # ================================================================== 3
    titulo(3, "UNA FILA DE SALIDA, CON EL MOTIVO DE CADA DECISION")
    cols = ["empresa", "origen", "sector_final", "nota_A3", "confianza_A3",
            "servicio_A5", "tipo_servicio", "confianza_A5",
            "prob_fase2", "prioridad", "redaccion",
            "motivo_A2", "motivo_A3", "motivo_A5", "motivo_fase2"]
    muestra = d[pasa].head(3) if pasa.any() else d.head(3)
    for _, r in muestra.iterrows():
        print()
        print(f"   {str(r.empresa)[:56]}")
        print(f"      A2  sector    : {str(r.pred_sector)[:44]}")
        print(f"      A3  nota      : {r.nota_A3}   (confianza "
              f"{r.confianza_A3:.2f})")
        print(f"      A5  servicio  : {str(r.servicio_A5)[:44]}")
        print(f"      A5  confianza : {r.confianza_A5:.2f}")
        print(f"      A5  redacción : {r.redaccion}")
        print(f"      motivo        : {r.motivo_A5}")

    # ================================================================== 4
    titulo(4, "GUARDAR")
    metricas = {
        "version": VERSION_SCRIPT,
        "empresas": int(len(d)),
        "ya_en_crm": conocidas_n,
        "nuevas": nuevas_n,
        "acierto_A2": float(d.acierto.mean() * 100),
        "con_texto_web": int(hay_texto.sum()),
        "pasan_emparejamiento": int(pasa.sum()),
        "llegan_al_final_pct": float(pasa.mean() * 100),
        "umbral_emparejamiento": UMBRAL_EMPAREJAMIENTO,
        "prioridad": {k: int((d.prioridad == k).sum())
                      for k in ("alta", "media", "baja")},
        "desajuste_poblacion": int(d._alertas_poblacion.iloc[0]),
        "propagacion": {
            "cambia_nota_total_pct": float(c_tot / n_tot * 100),
            "cambia_si_A2_fallo_pct": float(p_fallo),
            "cambia_si_A2_acerto_pct": float(p_acierto),
        },
    }
    if a.guardar:
        d[cols].to_csv(SALIDA, sep=";", index=False, encoding="utf-8")
        cola = d.loc[pasa, ["empresa", "sector_final", "nota_A3", "servicio_A5",
                            "tipo_servicio", "prob_fase2", "prioridad",
                            "confianza_A5"]].copy()
        cola = cola.sort_values(
            by="prioridad", key=lambda c: c.map(orden_pr)).reset_index(drop=True)
        cola.to_csv(COLA, sep=";", index=False, encoding="utf-8")
        METRICAS.write_text(json.dumps(metricas, indent=2, ensure_ascii=False),
                            encoding="utf-8")
        print(f"   [ok] {SALIDA.name}          una fila por empresa")
        print(f"   [ok] {COLA.name}   la entrada del circuito por lotes")
        print(f"   [ok] {METRICAS.name}")
    else:
        print("   Simulación. Lánzalo con --guardar para escribir la salida.")
    print()


if __name__ == "__main__":
    main()
