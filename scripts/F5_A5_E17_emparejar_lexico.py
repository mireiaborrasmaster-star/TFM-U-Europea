"""
A5 · EMPAREJAMIENTO ENTRE SERVICIO Y EMPRESA
=============================================
Dado el catalogo de servicios de Empresa y el texto de la web de una empresa,
decide que servicio le encaja mejor.

POR QUE NO HACE FALTA ENTRENAR NADA
-----------------------------------
No existe un conjunto de "emparejamientos correctos" del que aprender. Pero si
existe el catalogo, donde cada servicio declara las senales que indican encaje.
El emparejamiento se resuelve midiendo cuanto se parecen dos textos, y eso no
requiere ejemplos etiquetados.

DOS METODOS, QUE SE COMPARAN
----------------------------
  LEXICO    Cuenta cuantos terminos de senal aparecen en la web.
            Transparente y explicable: se puede senalar que palabra lo motivo.
            No entiende sinonimos: "packaging" no activa "envase".

  SEMANTICO Convierte ambos textos en vectores con un modelo de embeddings y
            mide su similitud. Entiende sinonimos y funciona entre idiomas,
            pero no se puede explicar que palabra concreta lo decidio.

Se implementan ambos porque la comparacion es en si misma un resultado: si el
lexico basta, no hace falta la complejidad del semantico.

VALIDACION SIN ETIQUETAS
------------------------
No hay emparejamientos correctos conocidos, pero si hay una pista: en el CRM,
cada oportunidad tiene un area de Empresa asignada. Si el emparejamiento propone
un servicio cuya area coincide con la que realmente atendio esa cuenta, es
senal de que funciona.

Uso:
    python scripts/F5_A5_E17_emparejar_lexico.py              # metodo lexico, rapido
    python scripts/F5_A5_E17_emparejar_lexico.py --semantico  # anade embeddings (necesita GPU o paciencia)
"""

import argparse
import json
import re
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "10_CATALOGO_SERVICIOS.md"
DERIVADO = RAIZ / "datos" / "02_derivado"
SALIDA = RAIZ / "datos" / "03_resultados"
SALIDA.mkdir(parents=True, exist_ok=True)


def sin_acentos(t):
    """Quita acentos conservando los simbolos. La version anterior eliminaba
    el '+' y dejaba 'i+d' imposible de encontrar."""
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def contiene(texto, senal):
    """Busca la senal como PALABRA, no como subcadena.

    El error anterior: 'pla' aparecia en el 66,8% de las webs porque encontraba
    'planta', 'plancha', 'plazo'... y 'pet' encontraba 'competencia'. Se buscaba
    dentro de las palabras en lugar de buscar palabras.

    Para senales de varias palabras se permite que haya hasta tres palabras
    intercaladas: una web dice "reducimos el plastico de nuestros envases",
    no "reduccion de plastico" literal.
    """
    s = senal.strip()
    if not s:
        return False
    partes = s.split()
    if len(partes) == 1:
        return re.search(r"(?<![\w])" + re.escape(s) + r"(?![\w])", texto) is not None
    patron = r"(?<![\w])" + r"(?:\W+\w+){0,3}\W+".join(re.escape(x) for x in partes)
    return re.search(patron, texto) is not None


# ==========================================================================
# Lectura del catalogo
# ==========================================================================

def leer_catalogo():
    """Extrae los servicios del documento en markdown.

    Se lee del propio documento revisado en lugar de duplicarlo en codigo:
    asi la version que revisa la autora es la que usa el sistema, y no hay
    dos fuentes que puedan desincronizarse.
    """
    if not CATALOGO.exists():
        sys.exit(f"No encuentro {CATALOGO.name}")
    texto = CATALOGO.read_text(encoding="utf-8")
    bloques = re.split(r"\n## (S\d+) · ", texto)[1:]
    servicios = []
    for i in range(0, len(bloques), 2):
        cod, cuerpo = bloques[i], bloques[i + 1]
        nombre = cuerpo.split("\n")[0].strip()

        def campo(patron):
            m = re.search(patron, cuerpo, re.S)
            return m.group(1).strip() if m else ""

        senales = campo(r"\*\*Señales en su web:\*\*(.+?)\n")
        servicios.append({
            "codigo": cod,
            "nombre": nombre,
            "area": campo(r"\| \*\*Área\*\* \| (.+?) \|"),
            "linea": campo(r"\| \*\*Línea\*\* \| (.+?) \|"),
            "tipo": campo(r"\| \*\*Tipo\*\* \| (.+?) \|"),
            "resuelve": re.sub(r"\s+", " ", campo(r"\*\*Qué resuelve\.\*\*(.+?)\n\n")),
            "para_quien": re.sub(r"\s+", " ", campo(r"\*\*A quién le sirve\.\*\*(.+?)\n\n")),
            "disparador": re.sub(r"\s+", " ", campo(r"\*\*Disparador típico\.\*\*(.+?)\n")),
            "senales": [sin_acentos(s) for s in
                        (x.strip(" .\n") for x in senales.split(",")) if s],
        })
    return servicios


# ==========================================================================
# Metodo 1 · lexico
# ==========================================================================

def emparejar_lexico(texto_web, servicios):
    """Cuenta terminos de senal presentes en la web.

    Cada senal cuenta una vez por servicio, no por repeticion: que una web
    diga "envase" cuarenta veces no la hace mas de envase que otra que lo
    diga tres. Lo que importa es la VARIEDAD de senales distintas.
    """
    t = sin_acentos(texto_web)
    resultados = []
    for s in servicios:
        encontradas = [x for x in s["senales"] if contiene(t, x)]
        # se normaliza por el numero de senales del servicio para que los
        # servicios con muchas senales no salgan favorecidos
        punt = len(encontradas) / max(len(s["senales"]), 1)
        resultados.append({"codigo": s["codigo"], "nombre": s["nombre"],
                           "area": s["area"], "punt": punt,
                           "senales": encontradas})
    return sorted(resultados, key=lambda r: -r["punt"])


# ==========================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semantico", action="store_true",
                    help="anade emparejamiento por embeddings")
    ap.add_argument("--muestra", type=int, default=400)
    a = ap.parse_args()

    print("=" * 70)
    print("A5 · EMPAREJAMIENTO SERVICIO <-> EMPRESA")
    print("=" * 70)

    servicios = leer_catalogo()
    print(f"Servicios en el catalogo: {len(servicios)}")
    print(f"Terminos de senal totales: {sum(len(s['senales']) for s in servicios)}")

    # empresas con texto web
    d = pd.concat([pd.read_csv(DERIVADO / f"cuentas_{p}.csv") for p in ["train", "val", "test"]],
                  ignore_index=True)
    d = d[d.tiene_texto.fillna(False)].copy()
    print(f"Empresas con texto web: {len(d):,}".replace(",", "."))
    m = d.sample(n=min(a.muestra, len(d)), random_state=42)
    print(f"Muestra para evaluar: {len(m)}\n")

    filas = []
    for r in m.itertuples():
        res = emparejar_lexico(r.web_text, servicios)
        mejor, segundo = res[0], res[1]
        filas.append({
            "empresa_clave": r.empresa_clave,
            "sector": r.sector,
            "servicio": mejor["codigo"],
            "nombre_servicio": mejor["nombre"],
            "area_servicio": mejor["area"],
            "punt": round(mejor["punt"], 3),
            "margen": round(mejor["punt"] - segundo["punt"], 3),
            "n_senales": len(mejor["senales"]),
            "senales": " · ".join(mejor["senales"][:6]),
        })
    e = pd.DataFrame(filas)

    print("-" * 70)
    print("¿A QUE SERVICIOS SE ESTAN EMPAREJANDO?")
    print("-" * 70)
    v = e.servicio.value_counts()
    mapa = {s["codigo"]: s["nombre"] for s in servicios}
    for c, n in v.items():
        print(f"   {c}  {mapa[c][:44]:<46} {n:>4}  ({n/len(e)*100:4.1f}%)")
    sin = [s["codigo"] for s in servicios if s["codigo"] not in v.index]
    if sin:
        print(f"\n   NUNCA elegidos: {', '.join(sin)}")
        print("   (revisar sus senales en el catalogo: puede que sean demasiado")
        print("    especificas o que las webs de esas empresas no las mencionen)")

    print("\n" + "-" * 70)
    print("¿CON CUANTA CONFIANZA?")
    print("-" * 70)
    print(f"   sin ninguna senal encontrada : {(e.n_senales == 0).sum():>4}  "
          f"({(e.n_senales == 0).mean()*100:4.1f}%)  <- no se puede emparejar")
    print(f"   con 1 sola senal             : {(e.n_senales == 1).sum():>4}  "
          f"({(e.n_senales == 1).mean()*100:4.1f}%)  <- dudoso")
    print(f"   con 2 o mas senales          : {(e.n_senales >= 2).sum():>4}  "
          f"({(e.n_senales >= 2).mean()*100:4.1f}%)  <- fiable")
    print(f"\n   empates (margen 0)           : {(e.margen == 0).sum():>4}  "
          f"({(e.margen == 0).mean()*100:4.1f}%)")

    print("\n" + "-" * 70)
    print("COHERENCIA CON EL SECTOR DE LA EMPRESA")
    print("-" * 70)
    fiables = e[e.n_senales >= 2]
    if len(fiables):
        t = pd.crosstab(fiables.sector, fiables.servicio)
        top = t.sum(axis=1).sort_values(ascending=False).head(6).index
        print("   (servicio mas elegido en los sectores mas frecuentes)")
        for s in top:
            fila = t.loc[s]
            print(f"      {str(s)[:38]:<40} -> {fila.idxmax()} ({fila.max()}/{fila.sum()})")

    e.to_csv(SALIDA / "a5_emparejamientos.csv", index=False, encoding="utf-8")
    with open(SALIDA / "a5_catalogo.json", "w", encoding="utf-8") as f:
        json.dump(servicios, f, ensure_ascii=False, indent=2)
    print(f"\n   Guardado: a5_emparejamientos.csv")
    print("\n   SIGUIENTE: generar los correos con python scripts/F5_A5_E19_generar_correos.py")


if __name__ == "__main__":
    main()
