"""
A5 · EMPAREJAMIENTO SEMANTICO CON EMBEDDINGS
=============================================
Empareja servicios y empresas comparando SIGNIFICADO en lugar de palabras.

POR QUE HACE FALTA
------------------
El metodo lexico fracasa, y esta medido: buscando correctamente las senales del
catalogo, el 41,8% de las webs no contiene NINGUNA de las 74 senales, y el 48,2%
de los emparejamientos son empates a cero.

El motivo es un desajuste de registro. Una empresa se describe diciendo
"fabricamos envases para la industria alimentaria"; Empresa describe su servicio
como "declaracion de conformidad y ensayos de migracion". Hablan del mismo
asunto con vocabularios distintos.

COMO FUNCIONA
-------------
Un modelo de embeddings convierte cada texto en un vector de numeros que captura
su significado. Textos que hablan de lo mismo quedan cerca aunque no compartan
ni una palabra. Se calcula la similitud entre el vector del servicio y el de la
empresa, y se elige el mas cercano.

MODELO
------
intfloat/multilingual-e5-small por defecto: abierto, multilingue (el 25% de las
cuentas son internacionales) y lo bastante ligero para correr sin GPU.

El modelo e5 espera prefijos "query:" y "passage:" en los textos. Se respeta
esa convencion porque fue entrenado asi y omitirla degrada el resultado.

Uso:
    python scripts/F5_A5_E18_emparejar_semantico.py                 # muestra de 400
    python scripts/F5_A5_E18_emparejar_semantico.py --muestra 1000
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
DERIVADO = RAIZ / "datos" / "02_derivado"
SALIDA = RAIZ / "datos" / "03_resultados"
SALIDA.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).parent))
from F5_A5_E17_emparejar_lexico import leer_catalogo, emparejar_lexico  # noqa: E402

MAX_CARACTERES = 1200


def texto_servicio(s):
    """Descripcion del servicio en lenguaje natural, tal como lo diria una
    persona. Se evita el formato de ficha: el modelo de embeddings funciona
    mejor con prosa que con listas de palabras clave."""
    return (f"{s['nombre']}. {s['resuelve']} Dirigido a: {s['para_quien']} "
            f"Temas relacionados: {', '.join(s['senales'][:12])}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="intfloat/multilingual-e5-small")
    ap.add_argument("--muestra", type=int, default=400)
    ap.add_argument("--lote", type=int, default=32)
    a = ap.parse_args()

    print("=" * 72)
    print("A5 · EMPAREJAMIENTO SEMANTICO")
    print("=" * 72)

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("\nFalta la libreria. Instala con:")
        print("   pip install sentence-transformers")
        sys.exit(1)

    servicios = leer_catalogo()
    print(f"Servicios: {len(servicios)}")

    d = pd.concat([pd.read_csv(DERIVADO / f"cuentas_{p}.csv")
                   for p in ["train", "val", "test"]], ignore_index=True)
    d = d[d.tiene_texto.fillna(False)].copy()
    m = d.sample(n=min(a.muestra, len(d)), random_state=42).reset_index(drop=True)
    print(f"Empresas en la muestra: {len(m)}")

    print(f"\nCargando {a.modelo}...")
    modelo = SentenceTransformer(a.modelo)

    # el modelo e5 requiere estos prefijos
    v_serv = modelo.encode(["passage: " + texto_servicio(s) for s in servicios],
                           normalize_embeddings=True, batch_size=a.lote)
    print("Servicios vectorizados. Procesando webs...")
    v_web = modelo.encode(["query: " + t[:MAX_CARACTERES]
                           for t in m.web_text.fillna("")],
                          normalize_embeddings=True, batch_size=a.lote,
                          show_progress_bar=True)

    sim = v_web @ v_serv.T                      # similitud coseno
    orden = np.argsort(-sim, axis=1)
    mejor, segundo = orden[:, 0], orden[:, 1]

    e = pd.DataFrame({
        "empresa_clave": m.empresa_clave,
        "sector": m.sector,
        "servicio": [servicios[i]["codigo"] for i in mejor],
        "nombre_servicio": [servicios[i]["nombre"] for i in mejor],
        "area_servicio": [servicios[i]["area"] for i in mejor],
        "similitud": sim[np.arange(len(m)), mejor].round(4),
        "margen": (sim[np.arange(len(m)), mejor] - sim[np.arange(len(m)), segundo]).round(4),
        "segunda_opcion": [servicios[i]["codigo"] for i in segundo],
    })

    print("\n" + "-" * 72)
    print("REPARTO DE SERVICIOS")
    print("-" * 72)
    v = e.servicio.value_counts()
    mapa = {s["codigo"]: s["nombre"] for s in servicios}
    for c, n in v.items():
        print(f"   {c}  {mapa[c][:42]:<44} {n:>4}  ({n/len(e)*100:4.1f}%)")
    sin = [s["codigo"] for s in servicios if s["codigo"] not in v.index]
    print(f"\n   servicios nunca elegidos: {len(sin)}  {' '.join(sin) if sin else ''}")
    print(f"   concentracion en los 3 primeros: {v.head(3).sum()/len(e)*100:.1f}%")

    print("\n" + "-" * 72)
    print("CONFIANZA DEL EMPAREJAMIENTO")
    print("-" * 72)
    print(f"   similitud media : {e.similitud.mean():.3f}")
    print(f"   margen medio    : {e.margen.mean():.4f}")
    print(f"   margen > 0,01   : {(e.margen > 0.01).mean()*100:.1f}%  <- decision clara")
    print(f"   margen < 0,003  : {(e.margen < 0.003).mean()*100:.1f}%  <- practicamente empate")

    print("\n" + "-" * 72)
    print("COMPARATIVA CON EL METODO LEXICO")
    print("-" * 72)
    lex = []
    for t in m.web_text.fillna(""):
        r = emparejar_lexico(t, servicios)
        lex.append(r[0]["codigo"] if r[0]["senales"] else None)
    e["lexico"] = lex
    coinc = (e.servicio == e.lexico).mean() * 100
    print(f"   el lexico no pudo decidir en : {e.lexico.isna().mean()*100:.1f}% de los casos")
    print(f"   coinciden ambos metodos      : {coinc:.1f}%")
    print(f"   concentracion lexico (top 3) : "
          f"{e.lexico.value_counts().head(3).sum()/len(e)*100:.1f}%")

    print("\n" + "-" * 72)
    print("COHERENCIA CON EL SECTOR (prueba de sentido comun)")
    print("-" * 72)
    t = pd.crosstab(e.sector, e.servicio)
    for s in t.sum(axis=1).sort_values(ascending=False).head(8).index:
        fila = t.loc[s]
        print(f"   {str(s)[:36]:<38} -> {fila.idxmax()} "
              f"{mapa[fila.idxmax()][:30]:<32} ({fila.max()}/{fila.sum()})")

    e.to_csv(SALIDA / "a5_emparejamiento_semantico.csv", index=False, encoding="utf-8")
    print(f"\n   Guardado: a5_emparejamiento_semantico.csv")


if __name__ == "__main__":
    main()
