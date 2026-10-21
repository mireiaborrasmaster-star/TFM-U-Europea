"""
SCRAPING DE LAS WEBS PENDIENTES
================================
Descarga el texto de las webs de las cuentas que aun no lo tienen.

POR QUE IMPORTA
---------------
Ya esta medido sobre el dataset anterior:

    empresas CON texto web ...... 60% de acierto
    empresas SIN texto web ...... 35% de acierto

El texto es la variable que mas pesa. Ahora mismo solo el 7% del conjunto de
entrenamiento lo tiene, asi que esto es el cuello de botella del agente A2.

COMO FUNCIONA
-------------
1. ORDEN DE PRIORIDAD. Primero test y val, porque sin ellos no se puede MEDIR
   nada por muy bueno que sea el entrenamiento. Despues los sectores con poco
   texto. Al final los que ya van sobrados.
   Asi, si paras el proceso a media ejecucion, lo hecho es lo que mas vale.

2. GUARDADO INCREMENTAL. Cada bloque se escribe en disco. Si se corta la luz o
   lo paras con Ctrl+C, al volver a lanzarlo sigue donde estaba.

3. LIMPIEZA AL VUELO. Se aplica PREP_limpieza_texto.py segun se descarga, para no
   guardar banners de cookies.

QUE ESPERAR
-----------
De cada 100 URLs, unas 60-75 daran texto util. El resto son dominios caducados,
webs caidas, sitios que bloquean robots o paginas que son solo un logo.
Eso es normal y no es un fallo del script.

Uso:
    python scripts/PREP_scrapear_webs.py                 # todo, en orden de prioridad
    python scripts/PREP_scrapear_webs.py --limite 200    # prueba corta
    python scripts/PREP_scrapear_webs.py --hilos 12      # mas agresivo
    python scripts/PREP_scrapear_webs.py --solo-medicion # solo test y val

PRIVACIDAD: solo imprime recuentos y porcentajes. Ni una URL, ni un nombre.
"""

import argparse
import csv
import random
import re
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, str(Path(__file__).parent))
from PREP_limpieza_texto import limpiar  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DERIVADO = RAIZ / "datos" / "02_derivado"
SALIDA = RAIZ / "datos" / "01_limpio"
SALIDA.mkdir(parents=True, exist_ok=True)
RESULTADO = SALIDA / "web_text_scrapeado.csv"

TIMEOUT = 10
MAX_CARACTERES = 10000
MIN_UTIL = 100
GUARDAR_CADA = 100

NAVEGADORES = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
]

ETIQUETAS_FUERA = ["script", "style", "nav", "footer", "header", "noscript",
                   "svg", "form", "aside", "iframe"]


# ==========================================================================

def normalizar_url(u):
    if not u or pd.isna(u):
        return None
    u = str(u).strip()
    if not u or "." not in u:
        return None
    if not u.startswith(("http://", "https://")):
        u = "https://" + u.lstrip("/")
    return u


def extraer_texto(html):
    sopa = BeautifulSoup(html, "html.parser")
    for e in sopa(ETIQUETAS_FUERA):
        e.decompose()
    texto = sopa.get_text(separator=" ")
    return re.sub(r"\s+", " ", texto).strip()


def descargar(clave, url):
    """Devuelve (clave, texto_limpio, estado). Nunca lanza excepcion."""
    u = normalizar_url(url)
    if not u:
        return clave, "", "url_invalida"

    cabeceras = {
        "User-Agent": random.choice(NAVEGADORES),
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }
    for intento in (1, 2):
        try:
            r = requests.get(u, headers=cabeceras, timeout=TIMEOUT,
                             verify=False, allow_redirects=True)
            if r.status_code >= 400:
                return clave, "", f"http_{r.status_code}"
            if "html" not in r.headers.get("Content-Type", "").lower():
                return clave, "", "no_html"
            texto = limpiar(extraer_texto(r.text))[:MAX_CARACTERES]
            if len(texto) < MIN_UTIL:
                return clave, texto, "texto_corto"
            return clave, texto, "ok"
        except requests.exceptions.SSLError:
            if intento == 1:
                u = u.replace("https://", "http://")
                continue
            return clave, "", "error_ssl"
        except requests.exceptions.Timeout:
            return clave, "", "timeout"
        except requests.exceptions.ConnectionError:
            return clave, "", "sin_conexion"
        except Exception:
            return clave, "", "error"
    return clave, "", "error"


# ==========================================================================

def construir_lista(solo_medicion=False):
    """Lista de trabajo ordenada por prioridad."""
    partes = []
    for p in ["train", "val", "test"]:
        f = DERIVADO / f"cuentas_{p}.csv"
        if not f.exists():
            sys.exit(f"Falta {f.name}. Ejecuta antes PREP_preparar_cuentas.py")
        partes.append(pd.read_csv(f))
    d = pd.concat(partes, ignore_index=True)

    d["url_ok"] = d.url.map(normalizar_url)
    pendientes = d[(~d.tiene_texto.fillna(False)) & d.url_ok.notna()].copy()

    # prioridad 1: lo que permite MEDIR
    pendientes["prioridad"] = 3
    pendientes.loc[pendientes.particion.isin(["test", "val"]), "prioridad"] = 1

    # prioridad 2: sectores con poco texto ya disponible
    cobertura = d[d.tiene_texto.fillna(False)].sector.value_counts()
    flojos = {s for s in d.sector.dropna().unique() if cobertura.get(s, 0) < 60}
    pendientes.loc[(pendientes.prioridad == 3) &
                   (pendientes.sector.isin(flojos)), "prioridad"] = 2

    if solo_medicion:
        pendientes = pendientes[pendientes.prioridad == 1]

    # dentro de cada prioridad, barajar para no machacar un dominio seguido
    pendientes = (pendientes.sample(frac=1, random_state=42)
                            .sort_values("prioridad", kind="stable"))
    return pendientes[["empresa_clave", "url_ok", "prioridad", "particion", "sector"]]


def ya_hechas():
    if not RESULTADO.exists():
        return set()
    try:
        return set(pd.read_csv(RESULTADO, usecols=["empresa_clave"]).empresa_clave.dropna())
    except Exception:
        return set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hilos", type=int, default=8)
    ap.add_argument("--limite", type=int, default=None, help="para probar")
    ap.add_argument("--solo-medicion", action="store_true",
                    help="solo test y val")
    a = ap.parse_args()

    print("=" * 70)
    print("SCRAPING DE WEBS PENDIENTES")
    print("=" * 70)

    trabajo = construir_lista(a.solo_medicion)
    hechas = ya_hechas()
    if hechas:
        antes = len(trabajo)
        trabajo = trabajo[~trabajo.empresa_clave.isin(hechas)]
        print(f"Ya procesadas en ejecuciones anteriores: {antes - len(trabajo):,}"
              .replace(",", "."))
    if a.limite:
        trabajo = trabajo.head(a.limite)

    total = len(trabajo)
    if total == 0:
        print("\nNo queda nada pendiente.")
        return

    print(f"\nPendientes en esta ejecucion: {total:,}".replace(",", "."))
    for pr, etiqueta in [(1, "test y val (permiten medir)"),
                         (2, "sectores con poco texto"),
                         (3, "resto")]:
        n = (trabajo.prioridad == pr).sum()
        if n:
            print(f"   prioridad {pr} - {etiqueta:<30} {n:>6,}".replace(",", "."))
    print(f"\nHilos: {a.hilos}   ·   Tiempo estimado: {total*2.5/a.hilos/60:.0f}-"
          f"{total*6/a.hilos/60:.0f} min")
    print("\nSe guarda cada bloque. Puedes cortar con Ctrl+C y retomar luego.\n")

    nuevo = not RESULTADO.exists()
    fichero = open(RESULTADO, "a", newline="", encoding="utf-8")
    escritor = csv.writer(fichero)
    if nuevo:
        escritor.writerow(["empresa_clave", "texto", "estado", "fecha"])

    estados = {}
    hecho = con_texto = 0
    inicio = time.time()
    fecha = datetime.now().strftime("%Y-%m-%d")

    try:
        with ThreadPoolExecutor(max_workers=a.hilos) as pool:
            futuros = {pool.submit(descargar, r.empresa_clave, r.url_ok): r.empresa_clave
                       for r in trabajo.itertuples()}
            for f in as_completed(futuros):
                clave, texto, estado = f.result()
                escritor.writerow([clave, texto, estado, fecha])
                estados[estado] = estados.get(estado, 0) + 1
                hecho += 1
                if estado == "ok":
                    con_texto += 1
                if hecho % GUARDAR_CADA == 0:
                    fichero.flush()
                    trans = time.time() - inicio
                    resto = (total - hecho) * trans / hecho / 60
                    print(f"   {hecho:>6,}/{total:,}  ({hecho/total*100:4.1f}%)   "
                          f"con texto: {con_texto/hecho*100:4.1f}%   "
                          f"quedan ~{resto:.0f} min".replace(",", "."))
    except KeyboardInterrupt:
        print("\n\n   Interrumpido. Lo procesado queda guardado.")
        print("   Vuelve a lanzar el script para continuar donde lo dejaste.")
    finally:
        fichero.close()

    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print(f"   procesadas          : {hecho:,}".replace(",", "."))
    print(f"   con texto util      : {con_texto:,} ({con_texto/max(hecho,1)*100:.1f}%)"
          .replace(",", "."))
    print(f"   tiempo              : {(time.time()-inicio)/60:.1f} min")
    print("\n   Desglose de los fallos:")
    for e, n in sorted(estados.items(), key=lambda x: -x[1]):
        print(f"      {e:<16} {n:>6,}  ({n/max(hecho,1)*100:4.1f}%)".replace(",", "."))

    print(f"\n   Guardado en: {RESULTADO.name}")
    print("\n   SIGUIENTE PASO: python scripts/PREP_preparar_cuentas.py")
    print("   (incorporara el texto nuevo al dataset)")


if __name__ == "__main__":
    main()
