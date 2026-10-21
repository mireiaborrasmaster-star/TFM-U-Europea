"""
F6 · ANALISIS DE LAS ENTRADAS Y DE LA RESOLUCION DE IDENTIDAD
=============================================================
Reproduce TODAS las cifras del documento 13_DISENO_F6.md.

POR QUE EXISTE ESTE FICHERO
---------------------------
El analisis de F6 se hizo primero de forma exploratoria, ejecutando codigo
suelto en la terminal. Las cifras resultantes se escribieron en el documento
de diseno, pero el codigo que las producia no quedaba en ninguna parte.

Eso invalida la reproducibilidad: una cifra sin el codigo que la genera no es
un resultado, es una afirmacion. Este script recupera cada numero del
documento y lo vuelve a calcular, de modo que cualquiera pueda comprobarlo.

Es la misma exigencia que el trabajo aplica a los experimentos de A2, A3 y A5,
y no hay razon para relajarla aqui.

QUE COMPRUEBA
-------------
  1. Cobertura del campo Sitio web en el CRM   (el techo del paso 2)
  2. Resolucion por dominio sobre las 8 entradas reales
  3. Ruido de la busqueda por nombre           (por que va despues)
  4. Conversion segun el tipo de lo que piden  (F3 fase 2)
  5. Conversion por area de Empresa
  6. Cobertura del diccionario de normas       (el enrutado por regla)

Uso (no necesita GPU ni internet):
    python scripts/F6_A6_analisis_entradas.py
"""

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

VERSION_SCRIPT = "v1 · 29-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
LIMPIO = RAIZ / "datos" / "01_limpio"
DERIVADO = RAIZ / "datos" / "02_derivado"
ENTRADAS = LIMPIO / "entradas_inbound_anon.csv"
OPORTUNIDADES = "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56_anon.csv"

# Dominios de proveedores de correo: agrupar por ellos uniria empresas sin
# ninguna relacion. El paso 2 debe desactivarse cuando aparece uno.
GENERICOS = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.es",
             "icloud.com", "live.com", "msn.com", "aol.com", "protonmail.com",
             "telefonica.net", "terra.es", "wanadoo.es", "hotmail.es",
             "gmx.com", "mail.com", "me.com", "qq.com", "163.com"}

# Diccionario norma -> area. Es conocimiento organizacional aportado, no
# aprendido: la correspondencia entre una norma citada y el area que la
# ejecuta se sabe con certeza y no hay que estimarla de los datos.
NORMAS = {
    "CARACTERIZACION Y EMBALAJES": [
        "ista", "astm d4169", "d4169", "iso 11607", "vibracion", "compresion",
        "apilamiento", "top load", "caida", "impacto", "carga paletizada",
        "simulacion de transporte", "resistencia estructural"],
    "QUIMICO Y PROCESOS": [
        "mosh", "moah", "pfas", "bisfenol", "bpa", "migracion", "nias",
        "ftir", "dsc", "plomo", "cadmio", "mercurio", "cromo hexavalente",
        "metales pesados", "sensorial"],
    # "doc" estaba aqui y encontraba "documentacion" y "documento" dentro de
    # las palabras, disparando esta area en IN02 e IN05 sin ningun motivo.
    # Es el error X8 por tercera vez: buscar subcadenas en lugar de palabras.
    # Se elimina la sigla suelta y se deja la expresion completa.
    "ENVASES Y ECONOMIA CIRCULAR": [
        "ppwr", "en 13430", "en 13427", "en 13428", "en 13429", "reciclabilidad",
        "ecodiseno", "declaracion de conformidad", "declaraciones de conformidad",
        "2025/40"],
    "COMPOSTABILIDAD": [
        "compostabilidad", "compostable", "biodegradacion", "biodegradable",
        "en 13432", "home compost"],
}


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def dominio(url):
    """Extrae el dominio de una URL del CRM, que llega en formatos variados."""
    u = str(url).strip().lower()
    if not u or u == "nan":
        return ""
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.split("/")[0].split("?")[0].strip()


def contiene_palabra(texto, termino):
    """Busca por palabra completa, no por subcadena.

    Es el error X8: buscar 'IDEA' dentro de las palabras encuentra BOMBAS
    IDEAL y CARCHIDEA. Aqui importa especialmente porque una coincidencia
    falsa asignaria una entrada a la cuenta equivocada.

    Para terminos de varias palabras ('astm d4169', 'carga paletizada') se
    permite separacion variable, porque el texto real no respeta el espaciado
    del catalogo.
    """
    partes = termino.split()
    if len(partes) == 1:
        # Los terminos tecnicos largos se admiten como raiz: 'migracion'
        # tiene que encontrar 'migraciones'. Es el mismo problema morfologico
        # de E17, resuelto igual. Solo a partir de 6 caracteres, para que una
        # sigla corta no vuelva a encontrar palabras que la contengan.
        cola = r"\w*" if len(termino) >= 6 else ""
        patron = r"(?<![\w])" + re.escape(termino) + cola + r"(?![\w])"
    else:
        patron = (r"(?<![\w])" + r"\W+".join(re.escape(p) for p in partes)
                  + r"\w*(?![\w])")
    return re.search(patron, texto) is not None


def titulo(n, t):
    print()
    print("=" * 74)
    print(f"{n} · {t}")
    print("=" * 74)


def main():
    print("=" * 74)
    print("F6 · ANALISIS DE ENTRADAS Y RESOLUCION DE IDENTIDAD")
    print(f"     {VERSION_SCRIPT}")
    print("     reproduce las cifras de 13_DISENO_F6.md")
    print("=" * 74)

    if not ENTRADAS.exists():
        sys.exit(f"Falta {ENTRADAS.name}")
    ent = pd.read_csv(ENTRADAS, sep=";")
    cuentas = pd.concat([pd.read_csv(DERIVADO / f"cuentas_{p}.csv")
                         for p in ["train", "val", "test"]], ignore_index=True)
    print(f"\nEntradas reales : {len(ent)}  "
          f"({(ent.canal == 'correo').sum()} correos, "
          f"{(ent.canal == 'formulario').sum()} formularios)")
    print(f"Cuentas del CRM : {len(cuentas):,}".replace(",", "."))

    # ---------------------------------------------------------------- 1
    titulo(1, "COBERTURA DEL CAMPO SITIO WEB  (el techo del paso 2)")
    cuentas["dom"] = cuentas.url.apply(dominio)
    con = (cuentas.dom != "").sum()
    print(f"   cuentas con URL utilizable : {con:,} de {len(cuentas):,}"
          .replace(",", "."))
    print(f"   cobertura                  : {con/len(cuentas)*100:.1f}%")
    print(f"   dominios distintos         : {cuentas[cuentas.dom != ''].dom.nunique():,}"
          .replace(",", "."))
    print()
    print("   El paso 2 no puede reconocer mas alla de esta cobertura, sea cual")
    print("   sea el algoritmo. El limite lo pone el CRM, no el metodo.")

    indice = {}
    for r in cuentas[cuentas.dom != ""].itertuples():
        indice.setdefault(r.dom, []).append(r)

    # ---------------------------------------------------------------- 2
    titulo(2, "RESOLUCION POR DOMINIO sobre las 8 entradas reales")
    encontradas = 0
    for r in ent.itertuples():
        if r.dominio in GENERICOS:
            print(f"   {r.id}  {r.dominio:<22} GENERICO: no se agrupa por dominio")
            continue
        hit = indice.get(r.dominio)
        if hit:
            encontradas += 1
            x = hit[0]
            print(f"   {r.id}  {r.dominio:<22} -> {x.empresa_clave[:36]}")
            print(f"         sector {x.sector} · {x.provincia} · "
                  f"atractividad {str(x.atractividad)[:1]}")
        else:
            print(f"   {r.id}  {r.dominio:<22} no esta -> cuenta nueva")
    print(f"\n   resueltas por dominio exacto: {encontradas}/{len(ent)}")

    # ---------------------------------------------------------------- 3
    titulo(3, "RUIDO DE LA BUSQUEDA POR NOMBRE  (por que va DESPUES)")
    nombres = cuentas.empresa_clave.astype(str).apply(sin_acentos)
    print(f"   {'entrada':<8}{'termino':<14}{'subcadena':>11}{'palabra':>10}")
    print("   " + "-" * 45)
    for r in ent.itertuples():
        tok = [t for t in re.sub(r"[^A-Za-z ]", " ", str(r.empresa_declarada)).split()
               if len(t) > 3]
        if not tok:
            continue
        t = sin_acentos(tok[0])
        n_sub = int(nombres.str.contains(t, regex=False).sum())
        n_pal = int(nombres.apply(lambda x: contiene_palabra(x, t)).sum())
        print(f"   {r.id:<8}{t[:13]:<14}{n_sub:>11}{n_pal:>10}")
    print()
    print("   La columna 'subcadena' es lo que devolveria una busqueda ingenua.")
    print("   Buscar por palabra completa reduce el ruido, pero no lo elimina:")
    print("   la salida de este paso son CANDIDATAS a revisar, nunca una")
    print("   asignacion automatica.")

    # ---------------------------------------------------------------- 4
    ruta = LIMPIO / OPORTUNIDADES
    if not ruta.exists():
        print(f"\n   (falta {OPORTUNIDADES}: no se calculan 4, 5 y 6)")
        return
    o = pd.read_csv(ruta, sep=";", low_memory=False)
    cerradas = o[o.Estado.isin(["Lograda", "Perdida"])].copy()
    cerradas["gana"] = (cerradas.Estado == "Lograda").astype(int)

    titulo(4, "F3 FASE 2 · CONVERSION SEGUN EL TIPO DE LO QUE PIDEN")
    print(f"   oportunidades cerradas: {len(cerradas):,}".replace(",", "."))
    print()
    t = (cerradas.groupby("Tipo Oportunidad")
         .agg(n=("gana", "size"), tasa=("gana", "mean"))
         .sort_values("tasa", ascending=False))
    for r in t.itertuples():
        print(f"   {str(r.Index)[:42]:<44} n={r.n:>5}   gana {r.tasa*100:5.1f}%")
    print(f"   {'GLOBAL':<44} n={len(cerradas):>5}   gana "
          f"{cerradas.gana.mean()*100:5.1f}%")

    try:
        from scipy.stats import chi2_contingency
        tab = pd.crosstab(cerradas["Tipo Oportunidad"], cerradas.gana)
        chi2, p, gl, _ = chi2_contingency(tab)
        print(f"\n   chi2 = {chi2:.1f}   gl = {gl}   p = {p:.2e}")
        if "Ensayos" in t.index and "Desarrollo I+D" in t.index:
            razon = t.loc["Ensayos", "tasa"] / t.loc["Desarrollo I+D", "tasa"]
            print(f"   un ensayo se gana {razon:.1f} veces mas que un I+D")
    except ImportError:
        print("\n   (sin scipy no se calcula el contraste)")

    # ---------------------------------------------------------------- 5
    titulo(5, "CONVERSION POR AREA DE Empresa  (areas con 50+ casos)")
    a = (cerradas.groupby("Área de Empresa")
         .agg(n=("gana", "size"), tasa=("gana", "mean")))
    a = a[a.n >= 50].sort_values("tasa", ascending=False)
    for r in a.itertuples():
        print(f"   {str(r.Index)[:54]:<56} n={r.n:>5}   gana {r.tasa*100:5.1f}%")

    # ---------------------------------------------------------------- 6
    titulo(6, "COBERTURA DEL DICCIONARIO DE NORMAS")
    print("   Si la entrada cita una norma reconocida, el area se decide por")
    print("   regla y no hace falta clasificador. Se mide cuanto cubre.")
    print()
    cubiertas = 0
    for r in ent.itertuples():
        txt = sin_acentos(r.cuerpo)
        halladas = {area: [n for n in ns if contiene_palabra(txt, n)]
                    for area, ns in NORMAS.items()}
        halladas = {k: v for k, v in halladas.items() if v}
        if halladas:
            cubiertas += 1
            area = max(halladas, key=lambda k: len(halladas[k]))
            todas = sum(len(v) for v in halladas.values())
            print(f"   {r.id}  -> {area:<30} ({todas} terminos)")
            for k, v in halladas.items():
                print(f"          {k[:26]:<28} {', '.join(v[:5])}")
        else:
            print(f"   {r.id}  -> sin norma citada: decide el clasificador")
    print(f"\n   cobertura del diccionario: {cubiertas}/{len(ent)} "
          f"({cubiertas/len(ent)*100:.0f}%)")
    print()
    print("   OJO: esto mide COBERTURA, no acierto. Que el diccionario dispare")
    print("   no demuestra que el area propuesta sea la correcta; para eso")
    print("   hacen falta las etiquetas reales del CRM (A8).")


if __name__ == "__main__":
    main()
