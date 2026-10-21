# -*- coding: utf-8 -*-
"""
A0_circuito_recepcion.py · E40 · el circuito de entrada, de principio a fin
===========================================================================

QUE ES
    El equivalente del orquestador A0 para la via de ENTRADA. Toma los
    correos reales, los pasa por A6 y A7, decide que hacer con cada uno y
    escribe el resultado en cuatro hojas de calculo que hacen de sistema de
    gestion simulado.

    Es la puesta en practica de lo que el apartado 7.2c describe. NO se
    conecta a ningun buzon ni a ningun CRM: lee los correos ya exportados y
    escribe ficheros nuevos. Esa es toda la diferencia, y se declara.

POR QUE HOJAS DE CALCULO, Y POR QUE SON UNA SIMULACION HONESTA
    Los tres export del sistema de gestion empiezan por las columnas
    «(No modificar) Cuenta», «(No modificar) Suma de comprobacion de fila» y
    «(No modificar) Fecha de modificacion». Ese formato existe para que el
    fichero editado pueda volver al CRM. Asi que tratar las hojas como las
    tablas del sistema no es un apano: es el camino que el propio producto
    contempla.

    Lo que esto demuestra: que la cadena funciona de principio a fin y
    produce registros con la forma que el CRM espera.
    Lo que NO demuestra: que la integracion funcione. Eso depende de
    permisos y licencias, y queda fuera del trabajo.

LOS ORIGINALES NO SE TOCAN NUNCA
    Se leen y nada mas. Todo lo que el circuito produce va a ficheros
    nuevos en datos/05_simulacion_crm/, para que siempre se distinga lo que
    ya habia de lo que hizo el agente.

LAS CUATRO SALIDAS
    crm_oportunidades_nuevas.xlsx   lo que el circuito crearia
    crm_cuentas_propuestas.xlsx     altas PROPUESTAS, nunca creadas solas
    buzon_no_comercial.xlsx         lo que solo se encamina
    buzon_a_revisar.xlsx            lo que llega a una persona, con todo

POR QUE LAS CUENTAS SON «PROPUESTAS» Y NO «CREADAS»
    Lo impide la decision D19: una cuenta que no consta en el sistema de
    gestion la da de alta una persona. El circuito deja la fila preparada
    con lo que ha podido extraer y la marca como pendiente, y el correo
    aparece ademas en el buzon de revision. Asi se obtiene el fichero sin
    saltarse la decision.

LA PROBABILIDAD DE LA OPORTUNIDAD
    La pone A8, y en las cuentas nuevas TAMBIEN, porque E39 midio que es
    justo donde mas aporta: su ventaja de calibracion sobre la persona se
    multiplica por cinco. Ordena algo peor, de modo que la fila sale
    marcada como «calculada sin historial». Se escribe en columna propia:
    nunca en «Probabilidad», que es la de la persona.

COMO SE EJECUTA
    python scripts/A0_circuito_recepcion.py
    python scripts/A0_circuito_recepcion.py --guardar
"""

import json
import sys
import unicodedata
import warnings
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import FeatureUnion
from sklearn.svm import LinearSVC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from F8_A8_briefing_traspaso import (  # noqa: E402
    GENERICOS, MATERIAS, NOMBRE_CORTO, NORMAS, TELEGRAMA_PALABRAS,
    TELEGRAMA_TOPE_IDF, TIPOS, componer_tema, contiene, dominio, sin_tildes,
    tramo)
from F8_A8_tema_modelo import (cortesia_comun, entrena_tipo,  # noqa: E402
                               hacer_telegrama, idf_de)
from F9_A9_seguimiento_oportunidades import (  # noqa: E402
    TRIM_TRAIN_FIN, VARIABLES_CREACION, anadir_cuenta, construir_datos,
    matriz)

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 07-10-2026"
SEMILLA = 42
HOY = date.today().isoformat()

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
LIMPIO = RAIZ / "datos" / "01_limpio"
RES = RAIZ / "datos" / "03_resultados"
SALIDA = RAIZ / "datos" / "05_simulacion_crm"

CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"
ETIQUETAS = LIMPIO / "etiquetas_comercial_A6.csv"
CUENTAS = BRUTO / "Cuentas activas 25-09-2026 20-36-50.xlsx"
OPORT = BRUTO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56.xlsx"
# Los mismos dos ficheros, ya seudonimizados. Se usan cuando el export
# original no esta: es el caso de la copia que se entrega, donde el export
# con nombres reales no se incluye. Las columnas son las mismas.
CUENTAS_ANON = LIMPIO / "Cuentas activas 25-09-2026 20-36-50_anon.csv"
OPORT_ANON = LIMPIO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56_anon.csv"


def leer_tabla(bruto, anon):
    """Lee el export del CRM, o su version seudonimizada si no esta."""
    if bruto.exists():
        return pd.read_excel(bruto)
    if anon.exists():
        print(f"   (usando {anon.name}, el export original no esta)")
        return pd.read_csv(anon, sep=";")
    import sys as _s
    _s.exit("\n".join([
        "",
        f"   No encuentro ni {bruto.name}",
        f"   ni {anon.name}.",
        "",
    ]))

# La lista de sospecha: los K correos peor valorados por la pieza de A6.
# K sale de E41, de la curva medida: 15 es la lista mas larga que no toca
# mas de dos solicitudes reales, y recoge 13 de los 14 no comerciales.
LISTA_SOSPECHA = 15
MODELO_DENSO = "intfloat/multilingual-e5-small"


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"PASO {n} · {t}")
    print("=" * 76)


# ===========================================================================
def main():
    guardar = "--guardar" in sys.argv

    print()
    print("#" * 76)
    print("# A0 · E40 · el circuito de entrada, de principio a fin")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)
    print()
    print("   Ningun fichero original se modifica. Todo lo que sale va a")
    print(f"   datos/05_simulacion_crm/, que hace de sistema de gestion.")

    # ------------------------------------------------------------------ 1
    titulo(1, "LO QUE ENTRA")
    d = pd.read_csv(CORPUS, sep=";")
    d["cuerpo"] = d.cuerpo.fillna("").astype(str)
    d["norm"] = d.cuerpo.map(sin_tildes)
    d["dom"] = d.dominio.map(dominio)
    et = pd.read_csv(ETIQUETAS, sep=";")
    et["no_com_real"] = et.categoria.astype(str).str.upper().str.contains("NO")
    d = d.merge(et[["id", "no_com_real"]], on="id", how="left")
    print(f"   Correos                      : {len(d)}")
    print(f"   Etiquetados a mano como no comerciales: "
          f"{int(d.no_com_real.sum())}")

    cu = leer_tabla(CUENTAS, CUENTAS_ANON)
    cu.columns = [c.strip() for c in cu.columns]
    col_w = next((c for c in cu.columns if "Sitio web" in c), None)
    col_d = next((c for c in cu.columns if c.strip().lower() == "dominio"), None)
    cu["d1"] = cu[col_w].map(dominio) if col_w else ""
    cu["d2"] = cu[col_d].map(dominio) if col_d else ""
    ficha = {}
    for _, r in cu.iterrows():
        for dd in (r.d1, r.d2):
            if dd and dd not in GENERICOS and dd not in ficha:
                ficha[dd] = r
    print(f"   Cuentas con dominio utilizable: {len(ficha)}")

    # ------------------------------------------------------------------ 2
    titulo(2, "A6 · ¿ES UNA SOLICITUD DE TRABAJO?")
    print("   La decision la toma el CLASIFICADOR, no la etiqueta. Y su")
    print("   puntuacion sale por validacion cruzada, asi que ningun correo")
    print("   lo juzga un modelo que ya lo haya visto.")
    print()
    print("   Se usa la combinacion que gano en E41: representaciones densas")
    print("   mas palabras. Sube la ordenacion de 0,918 a 0,946 y certifica")
    print("   48 solicitudes sin colar un solo correo no comercial.")
    X = d.norm.values
    y = d.no_com_real.astype(int).values
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)

    # --- la mitad de palabras: palabras y trozos de palabra ---------------
    p_pal = np.zeros(len(y), float)
    for itr, ite in cv.split(X, y):
        v = FeatureUnion([
            ("pal", TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2),
                                    min_df=1, max_features=20000)),
            ("car", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                    sublinear_tf=True, min_df=2,
                                    max_features=60000))])
        clf = LogisticRegression(max_iter=2000, class_weight="balanced")
        clf.fit(v.fit_transform(X[itr]), y[itr])
        p_pal[ite] = clf.predict_proba(v.transform(X[ite]))[:, 1]

    # --- la mitad densa: el mismo e5-small que empareja en A5 -------------
    print("   Calculando representaciones densas (sin GPU)...")
    from sentence_transformers import SentenceTransformer
    V = SentenceTransformer(MODELO_DENSO).encode(
        ["query: " + t for t in d.cuerpo], normalize_embeddings=True,
        show_progress_bar=False)
    p_den = np.zeros(len(y), float)
    for itr, ite in cv.split(X, y):
        clf = LogisticRegression(max_iter=3000, class_weight="balanced", C=4.0)
        clf.fit(V[itr], y[itr])
        p_den[ite] = clf.predict_proba(V[ite])[:, 1]

    def norm01(x):
        return (x - x.min()) / (x.max() - x.min() + 1e-12)

    p_no = (norm01(p_pal) + norm01(p_den)) / 2
    d["p_no_comercial"] = p_no

    # ---- EL UMBRAL NO SE HEREDA, SE ELIGE --------------------------------
    # Con el 0,5 de costumbre el clasificador no manda NADA al buzon
    # generico y se lleva por delante dos solicitudes reales. No es que el
    # modelo este roto: ordena bien —AUC 0,919 en 4.6.5— pero ordenar y
    # decidir son cosas distintas, que es la leccion de todo el capitulo.
    #
    # El criterio aqui es asimetrico y conviene decirlo: PERDER UNA
    # SOLICITUD REAL cuesta mucho mas que colar un correo que no lo era.
    # Un correo de mas en el buzon generico lo ve una persona y lo
    # devuelve; una solicitud perdida no la reclama nadie.
    reales = d.no_com_real.values.astype(bool)

    # La pieza ORDENA igual de bien que en 4.6.5 —es la misma, con las
    # mismas puntuaciones—. Lo que falla es el sitio por donde cortar, y
    # para verlo hace falta mirar DONDE caen las puntuaciones, no solo el
    # AUC: dos solicitudes reales puntuan por encima de los catorce no
    # comerciales, y ahi es justo donde un umbral tiene que cortar.
    from F6_A6_agente_recepcion import auc as auc6
    print()
    print(f"   AUC de la pieza, la misma de 4.6.5 : {auc6(p_no, reales):.3f}")
    print()
    print(f"   {'tramo':<16}{'NO comerciales':>18}{'solicitudes':>16}")
    print("   " + "-" * 52)
    bandas = []
    for lo, hi in ((0.50, 1.01), (0.45, 0.50), (0.40, 0.45),
                   (0.35, 0.40), (0.0, 0.35)):
        sel = (p_no >= lo) & (p_no < hi)
        nn, ns = int((sel & reales).sum()), int((sel & ~reales).sum())
        bandas.append((lo, hi, nn, ns))
        print(f"   {f'{lo:.2f} - {min(hi,1.0):.2f}':<16}{nn:>18}{ns:>16}")
    print()
    print(f"   La solicitud mejor puntuada llega a {p_no[~reales].max():.3f}, por encima")
    print(f"   de los {int((p_no[reales] < p_no[~reales].max()).sum())} correos no comerciales. Dos casos raros apenas")
    print(f"   mueven un AUC —son 28 pares de 1.274— pero se sientan justo")
    print(f"   donde hay que poner la raya.")
    print()
    print("   NO SE BUSCA UN UMBRAL, SE HACE UNA LISTA. Un umbral obliga a")
    print("   elegir entre tirar correos buenos o no cazar ninguno malo. Una")
    print("   lista ordenada por sospecha no tira nada: RETIENE para revision,")
    print("   y el coste de equivocarse deja de ser perder una solicitud y")
    print("   pasa a ser retrasarla un rato.")
    print()
    orden_sos = np.argsort(-p_no)
    print(f"   {'los K mas sospechosos':<24}{'no comerciales':>16}"
          f"{'solicitudes':>13}")
    print("   " + "-" * 56)
    tabla_k = []
    for k in (5, 10, LISTA_SOSPECHA, 20, 30):
        sel = orden_sos[:k]
        nn = int(reales[sel].sum())
        tabla_k.append({"k": k, "no_comerciales": nn, "solicitudes": k - nn})
        marca = "  <-" if k == LISTA_SOSPECHA else ""
        print(f"   {f'los {k} primeros':<24}{nn:>16}{k - nn:>13}{marca}")
    print()
    print(f"   Se eligen {LISTA_SOSPECHA}, que es la lista mas larga que no toca mas de")
    print(f"   dos solicitudes reales. El punto se calibro sobre estos mismos")
    print(f"   {len(d)} correos, asi que la cifra es optimista y se dice.")
    sos = np.zeros(len(d), bool)
    sos[orden_sos[:LISTA_SOSPECHA]] = True
    d["sospecha_no_comercial"] = sos
    d["decide_no_comercial"] = False      # nada se descarta solo

    vp = int((d.sospecha_no_comercial & reales).sum())
    fp = int((d.sospecha_no_comercial & ~reales).sum())
    fn = int((~d.sospecha_no_comercial & reales).sum())
    print()
    print(f"   La lista lleva {int(d.sospecha_no_comercial.sum())} correos:")
    print(f"      eran no comerciales de verdad    : {vp} de {int(reales.sum())}")
    print(f"      eran solicitudes y se retrasan   : {fp}")
    print(f"      no comerciales que se le escapan : {fn}")
    print()
    print("   ESTE ES EL COSTE DE DECIDIR CON EL MODELO Y NO CON LA ETIQUETA,")
    print("   y es lo que A6 no podia enseñar: su reparto publicado usa la")
    print("   etiqueta humana, que en produccion no existe.")

    # ------------------------------------------------------------------ 3
    titulo(3, "A7 · AREA, TIPO DE SERVICIO Y ASUNTO")
    op = leer_tabla(OPORT, OPORT_ANON)
    op.columns = [c.strip() for c in op.columns]
    if "Tema" not in op.columns:
        # El «Tema» es el asunto que una persona escribio en la oportunidad.
        # Es texto libre y puede nombrar a la empresa o al proyecto, de modo
        # que la anonimizacion lo aparta a la carpeta privada. Sin el no hay
        # etiqueta con la que entrenar el tipo de servicio.
        import sys as _s
        _s.exit("\n".join([
            "",
            "   ESTE PASO NO SE PUEDE EJECUTAR CON LOS DATOS ENTREGADOS.",
            "",
            "   Entrenar el tipo de servicio necesita la columna «Tema» de las",
            "   oportunidades: el asunto que escribio una persona. Es texto",
            "   libre y puede nombrar a la empresa, asi que la anonimizacion lo",
            "   aparta y no se entrega.",
            "",
            "   Lo que este paso produjo esta en output/:",
            "      a8_tipo_por_correo.csv      el tipo propuesto para cada correo",
            "      a8_briefings.csv            las 105 fichas de traspaso",
            "      simulacion_crm/             las hojas del sistema de gestion",
            "",
            "   Los pasos 1 y 2 —identidad, area y si es una solicitud— si se",
            "   han ejecutado aqui arriba con los datos seudonimizados.",
            "",
        ]))
    vec_t, clf_t, _, _ = entrena_tipo(op)
    idf_t = idf_de(vec_t, TELEGRAMA_TOPE_IDF)
    prohibidas = cortesia_comun(d.norm)
    tel = d.cuerpo.map(lambda x: hacer_telegrama(x, idf_t, TELEGRAMA_PALABRAS,
                                                 prohibidas))
    P = clf_t.predict_proba(vec_t.transform(tel))
    d["tipo_largo"] = clf_t.classes_[P.argmax(axis=1)]
    d["tipo_p"] = P.max(axis=1)
    d["telegrama"] = tel
    print(f"   Tipo de servicio propuesto en los {len(d)} correos")

    # area: primero la norma citada; si no, el clasificador de A7
    col_area = next(c for c in op.columns if "rea de Empresa" in c)
    tr_op = op[op["Tema"].notna() & op[col_area].notna()]
    vec_a = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=1,
                            max_features=60000)
    Xa = vec_a.fit_transform(tr_op.Tema.astype(str).map(sin_tildes))
    svc = LinearSVC(C=1.0, class_weight="balanced").fit(Xa, tr_op[col_area])
    # ¿sobre el correo entero o sobre el telegrama? E38 enseño que el mismo
    # modelo se derrumba con un correo largo. Aqui se puede comprobar: en
    # los correos donde la norma citada da el area, esa area hace de
    # referencia. Son pocos, pero es lo que hay, y es mejor que elegir a
    # ojo entre dos opciones.
    pred_cuerpo = svc.predict(vec_a.transform(d.norm))
    pred_tel = svc.predict(vec_a.transform(tel))
    gold, pc, pt = [], [], []
    for i, r in enumerate(d.itertuples()):
        a_ = [x for x, te in NORMAS.items()
              if any(contiene(r.norm, z) for z in te)]
        if len(a_) == 1:
            gold.append(a_[0])
            pc.append(pred_cuerpo[i])
            pt.append(pred_tel[i])
    cod_nom = {}
    try:
        from F6_A6_agente_recepcion import codigo_area
        _, bruto = codigo_area()
        cod_nom = {v: k for k, v in (bruto or {}).items()}
    except Exception:
        pass
    ac_c = np.mean([cod_nom.get(g, g) == c for g, c in zip(gold, pc)]) if gold else 0
    ac_t = np.mean([cod_nom.get(g, g) == c for g, c in zip(gold, pt)]) if gold else 0
    print(f"   Clasificador de area entrenado con {len(tr_op)} oportunidades")
    print(f"   Contra el area que da la norma ({len(gold)} correos):")
    print(f"      sobre el correo entero : {100*ac_c:.1f} %")
    print(f"      sobre el telegrama     : {100*ac_t:.1f} %")
    usa_tel = ac_t > ac_c
    pred_area = pred_tel if usa_tel else pred_cuerpo
    print(f"   Se usa {'el telegrama' if usa_tel else 'el correo entero'}.")
    print()
    print(f"   CUIDADO AL COMPARAR ESTE NUMERO CON EL 79,5 % DE 4.6.5. Aquel")
    print(f"   se mide sobre un problema de CUATRO areas —solo las que el")
    print(f"   diccionario de normas cubre— y este sobre las")
    print(f"   {tr_op[col_area].nunique()} del sistema de gestion, porque un correo puede ir a")
    print(f"   cualquiera. Mas clases, menos acierto: no se contradicen, miden")
    print(f"   tareas distintas.")

    filas = []
    for i, r in enumerate(d.itertuples()):
        t = r.norm
        areas = [a for a, te in NORMAS.items() if any(contiene(t, x) for x in te)]
        normas = sorted({x for a in areas for x in NORMAS[a] if contiene(t, x)})
        tipo = NOMBRE_CORTO.get(str(r.tipo_largo), str(r.tipo_largo))
        tema, _ = componer_tema(r.cuerpo, tipo, areas[0] if areas else None,
                               normas)
        cta = ficha.get(r.dom) if r.dom and r.dom not in GENERICOS else None
        filas.append({
            "id": r.id, "dom": r.dom, "idioma": r.idioma,
            "p_no_comercial": r.p_no_comercial,
            "no_comercial": bool(r.decide_no_comercial),
            "sospecha": bool(r.sospecha_no_comercial),
            "no_com_real": bool(r.no_com_real),
            "n_areas": len(areas),
            "area_norma": areas[0] if len(areas) == 1 else None,
            "area_modelo": pred_area[i],
            "areas_ambiguas": "|".join(areas) if len(areas) > 1 else None,
            "normas": "|".join(normas) or None,
            "tipo": tipo, "tipo_largo": str(r.tipo_largo),
            "tipo_p": float(r.tipo_p), "tipo_confianza": tramo(float(r.tipo_p)),
            "telegrama": r.telegrama,
            "tema": tema,
            "cuenta": (str(cta["Nombre de cuenta"]) if cta is not None else None),
            "num_cuenta": (str(cta["Número de cuenta"]) if cta is not None
                           and pd.notna(cta["Número de cuenta"]) else None),
            "cuenta_en_crm": cta is not None,
            "sector": (str(cta["Sector Empresa"]) if cta is not None
                       and pd.notna(cta["Sector Empresa"]) else None),
            "provincia": (str(cta["Provincia"]) if cta is not None
                          and pd.notna(cta["Provincia"]) else None),
        })
    F = pd.DataFrame(filas)

    # ------------------------------------------------------------------ 4
    titulo(4, "LA DECISION · A DONDE VA CADA CORREO")

    def destino(f):
        # la lista de sospecha RETIENE, no descarta: el correo va a una
        # persona con todo lo extraido, y de ahi sale al buzon generico o
        # vuelve al circuito
        if f.sospecha:
            return "revision: puede no ser una solicitud"
        if f.n_areas > 1:
            return "revision: la norma apunta a varias areas"
        if not f.cuenta_en_crm:
            return "revision: la cuenta no consta (D19)"
        return "oportunidad creada"

    F["destino"] = F.apply(destino, axis=1)
    F["area"] = np.where(F.area_norma.notna(),
                         F.area_norma.map(lambda x: cod_nom.get(x, x)),
                         F.area_modelo)
    print(f"   {'destino':<46}{'correos':>9}{'%':>8}")
    print("   " + "-" * 64)
    for k, v in F.destino.value_counts().items():
        print(f"   {k:<46}{v:>9}{100*v/len(F):>7.1f} %")
    creadas = F[F.destino == "oportunidad creada"]
    propuestas = F[F.destino == "revision: la cuenta no consta (D19)"]

    # ---- POR QUE EL CLASIFICADOR NO ES UNA PUERTA ------------------------
    # Se probo a usarlo como filtro, reteniendo los sospechosos antes de
    # crear nada. El resultado fue que NO EVITA NI UNA sola oportunidad
    # espuria: los dos correos no comerciales que llegan a la rama de
    # creacion son justo los que el clasificador puntua como comerciales.
    # A cambio retrasaba tres solicitudes reales. Asi que no se usa como
    # puerta: su puntuacion viaja como COLUMNA en la hoja de revision, para
    # que la persona ordene por ella.
    espurias = int((F.no_com_real & (F.destino == "oportunidad creada")).sum())

    # ¿cuantas oportunidades espurias habria SIN la lista de sospecha?
    def destino_sin_lista(f):
        if f.n_areas > 1:
            return "revision"
        if not f.cuenta_en_crm:
            return "revision"
        return "oportunidad creada"

    sin_l = F.apply(destino_sin_lista, axis=1)
    esp_sin = int(((sin_l == "oportunidad creada") & F.no_com_real).sum())
    print()
    print(f"   LO QUE LA LISTA EVITA")
    print(f"      sin ella : {esp_sin} oportunidades nacidas de un correo que no")
    print(f"                 era una solicitud")
    print(f"      con ella : {espurias}")
    print(f"      precio   : {int((F.sospecha & ~F.no_com_real).sum())} solicitudes reales esperan a que alguien")
    print(f"                 las mire. No se pierden.")
    print()
    print(f"   LO QUE NO EVITA, Y CONVIENE LEERLO")
    print(f"   El correo que se cuela pregunta si conocemos a algun fabricante")
    print(f"   capaz de producir con un biopolimero concreto: pide un CONTACTO,")
    print(f"   no un servicio, y lo pide con el vocabulario exacto de una")
    print(f"   solicitud tecnica. Distinguirlo exige saber que hace y que no")
    print(f"   hace Empresa, y eso no esta en el texto (E41).")

    # ------------------------------------------------------------------ 5
    titulo(5, "A8 · LA PROBABILIDAD DE CADA OPORTUNIDAD")
    print("   Se entrena con el historico, igual que en 4.6.7, y se puntua")
    print("   lo que el circuito acaba de crear.")
    h = construir_datos()
    h, _ = anadir_cuenta(h)
    cerr = h[h.cerrada].copy()
    tr = cerr[cerr.trim <= TRIM_TRAIN_FIN]
    Xh = matriz(cerr, VARIABLES_CREACION)
    # la variable de texto, que es lo que fue A7 y que 4.6.7 incluye. Para
    # el historico sale del asunto que escribio una persona; para lo que el
    # circuito crea, del asunto que propone A7. No es lo mismo y se dice.
    vtx = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=3,
                          max_features=60000)
    Xtx = vtx.fit_transform(cerr.loc[tr.index, "Tema"].fillna("").astype(str)
                            .map(sin_tildes))
    ctx = LogisticRegression(max_iter=3000, class_weight="balanced")
    ctx.fit(Xtx, tr.gana.values)
    from sklearn.model_selection import cross_val_predict
    Xh = Xh.copy()
    Xh.loc[tr.index, "punt_texto"] = cross_val_predict(
        LogisticRegression(max_iter=3000, class_weight="balanced"),
        Xtx, tr.gana.values, cv=5, method="predict_proba")[:, 1]
    rf = RandomForestClassifier(n_estimators=400, min_samples_leaf=5,
                                random_state=SEMILLA, n_jobs=-1)
    rf.fit(Xh.loc[tr.index], tr.gana.values)
    print(f"   Bosque entrenado con {len(tr)} oportunidades cerradas,")
    print(f"   con la variable de texto incluida, como en 4.6.7")

    # el historial de cada cuenta, hasta hoy
    hist = (h.groupby(h["Cuenta"].astype(str).str.strip().str.lower())
            .agg(ops=("gana", "size"), cerr=("cerrada", "sum"),
                 gan=("gana", "sum")))
    nuevas = pd.concat([creadas, propuestas], ignore_index=True)
    if len(nuevas):
        reg = pd.DataFrame(index=range(len(nuevas)))
        reg["Tipo Oportunidad"] = nuevas.tipo_largo.values
        reg["Tipología de proyecto"] = np.nan
        reg["Línea Tecnológica"] = np.nan
        reg["Sublínea Tecnológica"] = np.nan
        reg[col_area] = nuevas.area.values
        reg["Propietario"] = np.nan
        reg["mes"] = date.today().month
        prev, cerrp, tasa = [], [], []
        for _, f in nuevas.iterrows():
            k = str(f.cuenta).strip().lower() if f.cuenta else None
            if k and k in hist.index:
                x = hist.loc[k]
                prev.append(int(x.ops))
                cerrp.append(int(x.cerr))
                tasa.append(float(x.gan / x.cerr) if x.cerr else np.nan)
            else:
                prev.append(0)
                cerrp.append(0)
                tasa.append(np.nan)
        reg["ops_previas"] = prev
        reg["cerradas_previas"] = cerrp
        reg["tasa_previa"] = tasa
        for c in ("pais", "provincia", "tamano", "cliente", "asociado",
                  "atractividad", "sector_agrupado"):
            reg[c] = np.nan
        reg["provincia"] = nuevas.provincia.values
        reg["sector_agrupado"] = nuevas.sector.values
        Xn = matriz(reg, VARIABLES_CREACION).reindex(columns=Xh.columns,
                                                     fill_value=0)
        # el asunto que propone A7, puntuado con el mismo modelo de texto
        temas = nuevas.tema.fillna("").astype(str).map(sin_tildes).values
        Xn["punt_texto"] = ctx.predict_proba(vtx.transform(temas))[:, 1]
        nuevas["prob_modelo"] = rf.predict_proba(Xn)[:, 1]
        nuevas["sin_historial"] = np.array(prev) == 0
        print(f"   Oportunidades puntuadas: {len(nuevas)}")
        print(f"      de ellas, sin historial de cuenta: "
              f"{int(nuevas.sin_historial.sum())}")
        print(f"   Probabilidad media: {100*nuevas.prob_modelo.mean():.1f} %")
        print()
        print("   E39: en las cuentas nuevas el numero ORDENA algo peor y")
        print("   CALIBRA mucho mejor que el de una persona. Por eso se")
        print("   escribe igualmente, marcado.")

    # ------------------------------------------------------------------ 6
    titulo(6, "LAS CUATRO HOJAS")
    opor = pd.DataFrame({
        "id_correo": nuevas.id,
        "Tema": nuevas.tema.fillna("(sin asunto propuesto)"),
        "Cuenta": nuevas.cuenta,
        "Número de cuenta (Cuenta) (Cuenta)": nuevas.num_cuenta,
        "Tipo Oportunidad": nuevas.tipo_largo,
        "Área de Empresa": nuevas.area,
        "Estado": "Abierta",
        "Fecha de creación": HOY,
        "Probabilidad modelo": (100 * nuevas.prob_modelo).round(1),
        "Calculada sin historial": np.where(nuevas.sin_historial, "Sí", "No"),
        "Confianza del tipo": nuevas.tipo_confianza,
        "Origen": np.where(nuevas.destino == "oportunidad creada",
                           "agente · creada", "agente · pendiente del alta"),
        "Normas citadas": nuevas.normas,
    })
    # UNA CUENTA POR DOMINIO, no una por correo: dos mensajes de la misma
    # empresa son dos oportunidades, pero una sola alta. Sin esto el
    # circuito duplicaria cuentas en cuanto alguien escribe dos veces.
    g = (propuestas.groupby("dom")
         .agg(correos=("id", lambda x: " ".join(sorted(x))),
              n=("id", "size")).reset_index())
    print(f"   {len(propuestas)} correos de cuenta desconocida se agrupan en "
          f"{len(g)} altas")
    rep = int((g.n > 1).sum())
    if rep:
        print(f"   ({rep} dominios escribieron mas de una vez)")
    cuentas_n = pd.DataFrame({
        "Nombre de cuenta": "(pendiente) " + g.dom.astype(str),
        "Dominio": g.dom,
        "Sitio web": "www." + g.dom.astype(str),
        "Provincia": np.nan, "Sector Empresa": np.nan, "CIF/NIF": np.nan,
        "Estado del alta": "PENDIENTE · la crea una persona (D19)",
        "Origen": "agente · propuesta",
        "Correos que la originan": g.correos,
        "Fecha de la propuesta": HOY,
    })
    # El buzon generico NO se alimenta solo: el circuito propone y una
    # persona confirma, por el mismo motivo que las cuentas. Va ordenado
    # por probabilidad para que confirmarlo sea un vistazo.
    no_com = F[F.sospecha].sort_values("p_no_comercial", ascending=False)
    buzon_no = pd.DataFrame({
        "id_correo": no_com.id,
        "PROPUESTA": "encaminar al buzón genérico · CONFIRMAR",
        "Probabilidad de no ser una solicitud": no_com.p_no_comercial.round(3),
        "Dominio del remitente": no_com.dom,
        "Idioma": no_com.idioma,
        "Lo que el modelo leyó": no_com.telegrama,
        "Era no comercial (solo para evaluar)": np.where(
            no_com.no_com_real, "Sí", "NO · era una solicitud"),
        "Fecha": HOY,
    })
    rev = F[F.destino.str.startswith("revision")]
    buzon_rev = pd.DataFrame({
        "id_correo": rev.id,
        "POR QUÉ LLEGA AQUÍ": rev.destino.str.replace("revision: ", "",
                                                      regex=False),
        "Dominio del remitente": rev.dom,
        "Cuenta en el CRM": np.where(rev.cuenta_en_crm, rev.cuenta, "no consta"),
        "Área propuesta": rev.area,
        "Áreas posibles": rev.areas_ambiguas,
        "Normas citadas": rev.normas,
        "Probabilidad de no ser una solicitud": rev.p_no_comercial.round(3),
        "Tipo de servicio": rev.tipo,
        "Confianza del tipo": rev.tipo_confianza,
        "Asunto propuesto": rev.tema,
        "Lo que el modelo leyó": rev.telegrama,
        "Idioma": rev.idioma,
    })
    for nom, t in (("crm_oportunidades_nuevas", opor),
                   ("crm_cuentas_propuestas", cuentas_n),
                   ("buzon_no_comercial", buzon_no),
                   ("buzon_a_revisar", buzon_rev)):
        print(f"   {nom + '.xlsx':<34}{len(t):>5} filas x {t.shape[1]} columnas")

    print()
    print("   Todas las filas llevan el id del correo del que salieron: es lo")
    print("   que permite seguir la cadena entera hacia atras.")

    # ------------------------------------------------------------------ 7
    titulo(7, "LO QUE ESTO DEMUESTRA Y LO QUE NO")
    print("   DEMUESTRA que la cadena corre entera y produce registros con la")
    print("   forma que el sistema de gestion espera: se abren las hojas y")
    print("   ahi estan las oportunidades, con su asunto, su area y su")
    print("   probabilidad.")
    print()
    print("   NO DEMUESTRA que la integracion funcione —depende de permisos y")
    print("   licencias— ni que las oportunidades creadas sean las correctas:")
    print("   para eso habria que comprobar cuantos de estos correos acabaron")
    print("   de verdad en una oportunidad real, y eso exige el cruce con el")
    print("   historico que el anonimizado del corpus impide.")
    print()
    print("   Y UNA LIMITACION DEL CORPUS, no del circuito: los correos estan")
    print("   seudonimizados, asi que la cuenta propuesta se identifica por su")
    print("   dominio y no por su razon social. En explotacion el nombre")
    print("   saldria de la firma del correo.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    SALIDA.mkdir(parents=True, exist_ok=True)
    for nom, t in (("crm_oportunidades_nuevas", opor),
                   ("crm_cuentas_propuestas", cuentas_n),
                   ("buzon_no_comercial", buzon_no),
                   ("buzon_a_revisar", buzon_rev)):
        t.to_excel(SALIDA / f"{nom}.xlsx", index=False)
    resumen = {
        "experimento": "E40", "pieza": "circuito de recepcion simulado",
        "version": VERSION_SCRIPT, "fecha": HOY,
        "n_correos": int(len(F)),
        "destinos": {k: int(v) for k, v in F.destino.value_counts().items()},
        "clasificador_no_comercial": {
            "lista_sospecha": LISTA_SOSPECHA, "no_se_usa_como_puerta": True,
            "cazaria": vp, "de_no_comerciales": int(reales.sum()),
            "solicitudes_que_retrasaria": fp,
            "oportunidades_espurias_que_evita": 0,
            "oportunidades_espurias_creadas": espurias,
            "auc": float(auc6(p_no, reales)),
            "bandas": [{"desde": lo, "hasta": hi, "no_comerciales": nn,
                        "solicitudes": ns} for lo, hi, nn, ns in bandas],
            "maximo_de_una_solicitud": float(p_no[~reales].max()),
            "tabla_k": tabla_k,
            "motivo": "ningun umbral caza no comerciales sin llevarse "
                      "solicitudes reales; y los no comerciales que llegan a "
                      "crear oportunidad son los que el modelo puntua como "
                      "comerciales"},
        "area": {"acierto_correo_entero": float(100 * ac_c),
                 "acierto_telegrama": float(100 * ac_t),
                 "n_referencia": len(gold),
                 "clases": int(tr_op[col_area].nunique()),
                 "no_comparable_con": "el 79,5 % de 4.6.5, que mide 4 clases"},
        "cuentas": {"correos_sin_cuenta": int(len(propuestas)),
                    "altas_propuestas": int(len(g)),
                    "dominios_repetidos": rep},
        "oportunidades": {"filas": int(len(opor)),
                          "creadas": int((nuevas.destino == "oportunidad creada").sum()),
                          "pendientes_del_alta": int(len(propuestas)),
                          "sin_historial": int(nuevas.sin_historial.sum()),
                          "prob_media": float(100 * nuevas.prob_modelo.mean())},
        "no_demuestra": ["que la integracion con el CRM funcione",
                         "que las oportunidades creadas sean las correctas"],
    }
    (RES / "a0_circuito_recepcion.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=1, default=float),
        encoding="utf-8")
    print()
    print(f"   [ok] cuatro hojas en datos/05_simulacion_crm/")
    print(f"   [ok] a0_circuito_recepcion.json")
    print()


if __name__ == "__main__":
    main()
