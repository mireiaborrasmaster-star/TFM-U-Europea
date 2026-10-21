# -*- coding: utf-8 -*-
"""
F8_A8_tema_protegido.py · entrenar A8 sin usar el texto tal cual
================================================================

LA PREGUNTA
    E25 entreno el enrutado de A8 sobre la columna `Tema` y saco 78,97 %. Pero
    `Tema` es texto libre del equipo comercial y sigue siendo informacion
    restringida de la organizacion. La autora pregunta si hay forma de
    protegerla y no usarla tal cual.

    La hay, y ademas hacia falta, porque hay una fuga que no habiamos mirado.

LA FUGA QUE NADIE HABIA MIRADO
    Guardar el texto en una carpeta privada protege el FICHERO. No protege el
    MODELO.

    Un TF-IDF con un clasificador lineal guarda dentro su vocabulario entero y
    un peso por cada termino y clase. Publicar ese modelo —o una tabla de
    "terminos mas influyentes por area", que es justo lo que uno pone en una
    memoria para explicar el resultado— publica el vocabulario comercial de la
    organizacion, marcas de cliente incluidas.

    Es el mismo tipo de error que X7: la informacion no se filtra por donde se
    esta mirando.

LAS TRES PROTECCIONES QUE SE MIDEN

    A · FILTRAR ENTIDADES
        Se eliminan del texto los terminos que parecen nombres propios —marcas,
        productos de cliente— y se conserva el vocabulario tecnico. El modelo
        sigue siendo legible; lo que desaparece es lo que identifica a nadie.

    B · HUELLA DIGITAL (hashing)
        Cada termino se convierte en un numero mediante una funcion resumen.
        NO SE GUARDA NINGUN VOCABULARIO: el modelo resultante no contiene una
        sola palabra y no hay forma de recuperarlas. Es la proteccion mas
        fuerte disponible sin tocar los datos de origen.
        Coste: el modelo deja de ser inspeccionable.

    C · LAS DOS A LA VEZ

    De cada una se mide lo que cuesta en aciertos. Una proteccion que hunde el
    resultado no es una opcion; una que cuesta un punto, si.

CONFIDENCIALIDAD DE ESTE PROPIO SCRIPT
    No imprime ningun termino del vocabulario, ni ningun tema, ni ningun nombre
    de area. Solo recuentos y porcentajes. Su salida se puede pegar en la
    memoria tal cual.

COMO SE EJECUTA
    python scripts/F8_A8_tema_protegido.py
    python scripts/F8_A8_tema_protegido.py --guardar
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
LIMPIO = RAIZ / "datos" / "01_limpio"
RESULTADOS = RAIZ / "datos" / "03_resultados"
PRIVADO = RAIZ / "datos" / "_mapeo_privado"

TEMAS = PRIVADO / "temas_oportunidades.csv"
OPORTUNIDADES = LIMPIO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56_anon.csv"
SALIDA = RESULTADOS / "f8_tema_protegido.json"

# Lo que E25 midio sin ninguna proteccion. Es el punto de comparacion.
E25 = {"acierto": 78.97, "f1_macro": 69.98, "suelo": 27.12}

# ---------------------------------------------------------------------------
# Vocabulario tecnico que SI puede quedarse
# ---------------------------------------------------------------------------
# Son terminos de dominio publico: normas, ensayos, materiales y propiedades.
# Cualquier instituto de envase los usa. No identifican a ningun cliente.
TECNICO = {
    # normas y reglamentos
    "ista", "astm", "iso", "une", "en", "ppwr", "reach", "efsa", "fda",
    "d4169", "13432", "13430", "13427", "13428", "13429", "11607", "2025",
    # ensayos y propiedades
    "ensayo", "ensayos", "test", "analisis", "estudio", "caracterizacion",
    "vibracion", "compresion", "apilamiento", "caida", "impacto", "bct",
    "ect", "permeabilidad", "barrera", "migracion", "sellado", "resistencia",
    "traccion", "espesor", "gramaje", "humedad", "otr", "wvtr", "dsc", "ftir",
    "sensorial", "vida", "util", "estabilidad", "envejecimiento", "acelerado",
    "compostabilidad", "biodegradacion", "reciclabilidad", "ecodiseno",
    "huella", "carbono", "acv", "transporte", "distribucion", "paletizado",
    # sustancias
    "mosh", "moah", "pfas", "bisfenol", "bpa", "nias", "plomo", "cadmio",
    "mercurio", "cromo", "metales", "pesados", "tintas", "adhesivos",
    # materiales
    "carton", "ondulado", "papel", "plastico", "film", "pelicula", "pet",
    "pe", "pp", "pvc", "eva", "evoh", "aluminio", "vidrio", "madera",
    "bandeja", "botella", "tapon", "caja", "bolsa", "saco", "envase",
    "embalaje", "packaging", "monomaterial", "multicapa", "reciclado",
    # servicio
    "consultoria", "asesoramiento", "formacion", "curso", "proyecto",
    "desarrollo", "prototipo", "escalado", "auditoria", "informe",
    "declaracion", "conformidad", "certificacion", "muestra", "muestras",
    "ref", "refs", "lote",
}


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"{n} · {t}")
    print("=" * 76)


RE_TOKEN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][\wÁÉÍÓÚÜÑáéíóúüñ-]*")


def filtrar_entidades(texto):
    """
    Quita los terminos que parecen nombre propio y no son vocabulario tecnico.
    Criterio: empieza por mayuscula y su forma normalizada no esta en TECNICO.
    Los numeros y las siglas tecnicas se conservan.
    """
    def decidir(m):
        t = m.group(0)
        if sin_acentos(t) in TECNICO:
            return t
        if t[0].isupper() and len(t) > 2:
            return " "
        return t
    return RE_TOKEN.sub(decidir, texto)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("--semilla", type=int, default=42)
    a = ap.parse_args()

    print()
    print("#" * 76)
    print("# F8 · A8 · proteger `Tema` sin perder el resultado")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    tm = pd.read_csv(TEMAS, sep=";")
    op = pd.read_csv(OPORTUNIDADES, sep=";", low_memory=False)
    d = tm.merge(op[["Nº oportunidad", "Área de Empresa"]], on="Nº oportunidad",
                 how="left")
    d = d[d.Tema.notna() & d["Área de Empresa"].notna()].copy()
    d["Tema"] = d.Tema.astype(str)
    d = d[d.Tema.str.len() > 3]
    y = d["Área de Empresa"].astype(str)
    frec = y.value_counts()
    validas = frec[frec >= 20].index
    d = d[y.isin(validas)]
    ys = d["Área de Empresa"].astype(str)
    cifras = {"version": VERSION_SCRIPT, "n": int(len(d)),
              "areas": int(len(validas)), "referencia_E25": E25}

    from sklearn.feature_extraction.text import TfidfVectorizer, HashingVectorizer
    from sklearn.svm import LinearSVC
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.pipeline import make_pipeline
    cv = StratifiedKFold(5, shuffle=True, random_state=a.semilla)

    # ------------------------------------------------------------------ 1
    titulo(1, "LA FUGA · ¿que publicaria el modelo de E25?")
    vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2,
                          strip_accents="unicode", lowercase=True)
    X = vec.fit_transform(d.Tema)
    svc = LinearSVC(C=1.0, class_weight="balanced").fit(X, ys)
    vocab = np.array(vec.get_feature_names_out())
    print(f"   Términos que el modelo guarda dentro : {len(vocab):>7}")
    print(f"   Pesos (términos × áreas)             : {svc.coef_.size:>7}")
    print()

    # cuantos de los terminos mas influyentes NO son vocabulario tecnico
    top_idx = set()
    for fila in svc.coef_:
        top_idx.update(np.argsort(-fila)[:30].tolist())
    top = vocab[sorted(top_idx)]
    def es_tecnico(term):
        return all(sin_acentos(p) in TECNICO or p.isdigit()
                   for p in term.split())
    no_tec = [t for t in top if not es_tecnico(t)]
    # El lexico tecnico de este script es corto a proposito, asi que "no
    # tecnico" es una COTA SUPERIOR. El indicador que de verdad importa es
    # otro: cuantos de esos terminos son RAROS. Un termino que aparece en dos
    # o tres asuntos de entre cuatro mil no es vocabulario de sector: es de un
    # cliente concreto, y es el que reidentifica.
    conteo = np.asarray((X > 0).sum(axis=0)).ravel()
    idx_de = {t: i for i, t in enumerate(vocab)}
    raros = [t for t in no_tec if conteo[idx_de[t]] <= 5]
    print(f"   Términos más influyentes examinados  : {len(top):>7}")
    print(f"   …que NO son vocabulario técnico      : {len(no_tec):>7}   "
          f"{len(no_tec)/len(top)*100:.0f} %   (cota superior)")
    print(f"   …y además aparecen en 5 asuntos o menos: {len(raros):>6}   "
          f"{len(raros)/len(top)*100:.0f} %   <- los que reidentifican")
    print()
    print("   Un término que pesa mucho y sale en tres asuntos de cuatro mil")
    print("   no es vocabulario del sector: es de un cliente concreto.")
    print("   Si la memoria incluye una tabla de «términos más influyentes por")
    print("   área» —que es lo natural para explicar el resultado— los publica.")
    print()
    print("   GUARDAR EL FICHERO EN PRIVADO NO PROTEGE EL MODELO.")
    cifras["vocabulario"] = int(len(vocab))
    cifras["top_no_tecnico_pct"] = float(len(no_tec) / len(top) * 100)
    cifras["top_raros_pct"] = float(len(raros) / len(top) * 100)

    # ------------------------------------------------------------------ 2
    titulo(2, "LAS TRES PROTECCIONES, CON SU COSTE")
    d["filtrado"] = d.Tema.map(filtrar_entidades)
    quitados = (d.Tema.str.split().str.len()
                - d.filtrado.str.split().str.len()).clip(lower=0)
    print(f"   Filtrado de entidades:")
    print(f"      palabras eliminadas de media : {quitados.mean():.1f} "
          f"de {d.Tema.str.split().str.len().mean():.1f}")
    print(f"      asuntos que quedan vacíos    : {(d.filtrado.str.strip()=='').sum()}")
    print()

    def evaluar(textos, vectorizador, etiqueta):
        tubo = make_pipeline(vectorizador,
                             LinearSVC(C=1.0, class_weight="balanced"))
        acc = cross_val_score(tubo, textos, ys, cv=cv, scoring="accuracy")
        f1 = cross_val_score(tubo, textos, ys, cv=cv, scoring="f1_macro")
        return acc.mean() * 100, acc.std() * 100, f1.mean() * 100, etiqueta

    def tfidf():
        return TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2,
                               strip_accents="unicode", lowercase=True)

    def hashing():
        # sin vocabulario: el modelo no contiene ni una palabra
        return HashingVectorizer(n_features=2 ** 18, ngram_range=(1, 2),
                                 strip_accents="unicode", lowercase=True,
                                 alternate_sign=False, norm="l2")

    filas = [
        evaluar(d.Tema, tfidf(), "0 · Sin proteger  (E25)"),
        evaluar(d.filtrado, tfidf(), "A · Entidades filtradas"),
        evaluar(d.Tema, hashing(), "B · Huella digital, sin vocabulario"),
        evaluar(d.filtrado, hashing(), "C · Las dos"),
    ]

    print(f"   {'':<38}{'aciertos':>10}{'±':>7}{'F1-macro':>11}{'coste':>9}")
    print("   " + "-" * 75)
    base = filas[0][0]
    for acc, sd, f1, etq in filas:
        coste = "—" if etq.startswith("0") else f"{acc-base:+.2f}"
        print(f"   {etq:<38}{acc:>9.2f}%{sd:>7.2f}{f1:>11.2f}{coste:>9}")
    print(f"   {'Responder siempre lo más común':<38}{E25['suelo']:>9.2f}%")

    cifras["variantes"] = [{"variante": e, "acierto": a_, "sd": s_, "f1": f_}
                           for a_, s_, f_, e in filas]

    # ------------------------------------------------------------------ 3
    titulo(3, "¿QUEDA ALGO LEGIBLE DESPUES DE PROTEGER?")
    vec2 = tfidf()
    X2 = vec2.fit_transform(d.filtrado)
    svc2 = LinearSVC(C=1.0, class_weight="balanced").fit(X2, ys)
    vocab2 = np.array(vec2.get_feature_names_out())
    top2 = set()
    for fila in svc2.coef_:
        top2.update(np.argsort(-fila)[:30].tolist())
    t2 = vocab2[sorted(top2)]
    no_tec2 = [t for t in t2 if not es_tecnico(t)]
    print(f"   Variante A · entidades filtradas")
    print(f"      vocabulario del modelo            : {len(vocab2):>7}"
          f"   ({len(vocab2)-len(vocab):+d} frente a sin proteger)")
    print(f"      términos influyentes no técnicos  : {len(no_tec2):>7}"
          f"   {len(no_tec2)/len(t2)*100:.0f} %"
          f"   (antes {len(no_tec)/len(top)*100:.0f} %)")
    print()
    print(f"   Variante B · huella digital")
    print(f"      vocabulario del modelo            : {0:>7}")
    print("      No guarda ni una palabra. No hay tabla de términos que")
    print("      publicar, ni por descuido. A cambio, el modelo no se puede")
    print("      explicar término a término.")
    cifras["vocabulario_filtrado"] = int(len(vocab2))
    cifras["top_no_tecnico_filtrado_pct"] = float(len(no_tec2) / len(t2) * 100)

    # ------------------------------------------------------------------ 4
    titulo(4, "RECOMENDACION")
    a_acc = filas[1][0]
    b_acc = filas[2][0]
    c_acc = filas[3][0]
    print(f"   Sin proteger   {base:.2f} %")
    print(f"   A · filtrado   {a_acc:.2f} %   ({a_acc-base:+.2f})")
    print(f"   B · huella     {b_acc:.2f} %   ({b_acc-base:+.2f})")
    print(f"   C · las dos    {c_acc:.2f} %   ({c_acc-base:+.2f})")
    print()
    if c_acc >= base - 2.0:
        print("   RECOMENDACION: la variante C.")
        print()
        print("   Cuesta menos de dos puntos y cierra las dos vias a la vez:")
        print("   el texto pierde los nombres propios ANTES de entrar, y el")
        print("   modelo no guarda vocabulario DESPUES de entrenarse. Aunque")
        print("   alguien publicara el modelo entero por descuido, no habria")
        print("   nada que leer dentro.")
        print()
        print("   Y en la memoria se declara asi: el enrutado se entrena sobre")
        print("   una version del texto sin entidades nombradas y con")
        print("   representacion por huella digital, de modo que ni los datos")
        print("   ni el modelo contienen informacion comercial identificable.")
        print("   Eso es una decision de diseño defendible, no una renuncia.")
    elif b_acc >= base - 2.0:
        print("   RECOMENDACION: la variante B.")
    else:
        print("   RECOMENDACION: la variante A, y declarar la limitacion.")
    print()
    print("   DOS COSAS QUE HAY QUE DECIR CON PRECISION")
    print()
    print("   1. La huella digital es OCULTACION, no cifrado. El modelo no")
    print("      contiene palabras, pero quien tuviera una lista de candidatas")
    print("      podria calcular su huella y mirar el peso. Protege frente a la")
    print("      publicacion descuidada y frente a la lectura casual, que es el")
    print("      riesgo real aqui. No protege frente a alguien decidido.")
    print("      Conviene escribirlo asi en la memoria y no prometer de mas.")
    print()
    print("   2. Ninguna variante sustituye a guardar el origen fuera del")
    print("      proyecto. Las protecciones evitan que el texto salga en el")
    print("      modelo o en la memoria; el fichero sigue existiendo. Las dos")
    print("      medidas hacen falta, y son independientes.")

    titulo(5, "GUARDAR")
    if a.guardar:
        SALIDA.write_text(json.dumps(cifras, indent=2, ensure_ascii=False),
                          encoding="utf-8")
        print(f"   [ok] {SALIDA.relative_to(RAIZ)}")
        print("   Solo recuentos. Ni un termino, ni un tema, ni un area real.")
    else:
        print("   Simulacion. Lanzalo con --guardar para escribir las cifras.")
    print()


if __name__ == "__main__":
    main()
