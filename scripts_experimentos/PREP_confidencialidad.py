# -*- coding: utf-8 -*-
"""
PREP_confidencialidad.py · proteger la informacion comercial de la organizacion
===============================================================================

DE DONDE SALE ESTO
    La autora advierte que su organizacion no quiere que se conozcan con
    exactitud los servicios que presta, y supone que las fichas de servicio
    se extrajeron de la columna `Tema` del export de oportunidades.

    ESA SUPOSICION ES FALSA, y conviene dejarlo escrito porque cambia la
    solucion. El catalogo `10_CATALOGO_SERVICIOS.md` dice en su cabecera que
    se elaboro "a partir de las lineas tecnologicas y areas reales del CRM,
    del playbook y de conocimiento publico del sector" y que "NO es el
    catalogo oficial de Empresa". Es una reconstruccion, no un volcado.

    Pero al comprobarlo aparecieron TRES exposiciones reales que nadie habia
    señalado, y una de ellas es seria.

LAS TRES EXPOSICIONES

    1. `Tema` ESTA EN EL FICHERO LIMPIO SIN TRATAR.  <-- la grave
       La configuracion de anonimizacion le aplica LIMPIAR, que solo normaliza
       espacios y acentos. No es anonimizar. Es texto libre escrito por el
       equipo comercial y contiene, comprobado, nombres de producto de cliente
       y marcas de terceros. Son 4.878 filas.

    2. `Area de Empresa` y `Linea Tecnologica` estan en CONSERVAR.
       Es la estructura interna real de la organizacion, y al publicar su
       reparto se publica DONDE SE CONCENTRA EL NEGOCIO. Eso es justo lo que
       una competidora querria saber.

    3. El catalogo del anexo arrastra esos mismos nombres de area.

QUE HACE ESTE SCRIPT

    A. AUDITA  ·  dice donde aparece cada cosa, sin tocar nada
    B. CODIFICA ·  crea AR01..ARnn para las areas y guarda la equivalencia
                   real en datos/_mapeo_privado/, junto a la sal
    C. RETIRA  ·  saca `Tema` del fichero limpio y lo deja solo en la carpeta
                  privada. Es la misma decision que ya se tomo con los datos
                  de contacto de A4: minimizacion, no imposibilidad
    D. PUBLICA ·  genera ANEXO_catalogo_servicios.md, la version del catalogo
                  que SI puede ir en la memoria

UNA COSA QUE NO SE TOCA, Y POR QUE
    Los NOMBRES de los servicios («ensayos de transporte y distribucion»,
    «ensayos de compostabilidad») son denominaciones genericas del sector que
    ofrece cualquier instituto de envase, y ademas son texto generado, no
    extraido. Si se sustituyen por codigos, el anexo deja de permitir
    reproducir E18 y E24, que dependen de esos textos concretos.

    Lo confidencial no es QUE servicios existen: es la estructura interna que
    los agrupa y el volumen de negocio de cada una. Eso es lo que se codifica.

    Si la organizacion decide que tambien los nombres sobran, se ejecuta con
    --ocultar-nombres y el anexo sale solo con codigos. Se pierde
    reproducibilidad y hay que declararlo en la memoria.

COMO SE EJECUTA
    python scripts/PREP_confidencialidad.py              solo audita
    python scripts/PREP_confidencialidad.py --aplicar    codifica y publica
"""

import argparse
import json
import re
import shutil
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

VERSION_SCRIPT = "v1 · 30-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
LIMPIO = RAIZ / "datos" / "01_limpio"
RESULTADOS = RAIZ / "datos" / "03_resultados"
PRIVADO = RAIZ / "datos" / "_mapeo_privado"

OPORTUNIDADES = "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56_anon.csv"
CATALOGO = RESULTADOS / "a5_catalogo.json"
ANEXO = RAIZ / "ANEXO_catalogo_servicios.md"
MAPEO_AREAS = PRIVADO / "mapeo_areas.json"
TEMA_PRIVADO = PRIVADO / "temas_oportunidades.csv"

# Documentos que pueden acabar en manos del tribunal o publicarse
PUBLICABLES = ["memoria", "08_BITACORA.md", "10_CATALOGO_SERVICIOS.md",
               "07_HALLAZGOS_CRM.md", "13_DISENO_F6.md", "15_INDICE_MEMORIA.md",
               "16_GUION_DEFENSA.md", "ESTADO.txt"]

# Rastros de la estructura interna
RASTROS = ["LABORATORIOS:", "D. PROYECTOS:", "TÉCNICO:", "TECNICO:",
           "TRANSFERENCIA TECNOLÓGICA", "Línea Tecnológica", "Sublínea"]


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"{n} · {t}")
    print("=" * 76)


def codigo_area(nombre, indice):
    return f"AR{indice:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true",
                    help="escribir los cambios; sin esto solo audita")
    ap.add_argument("--ocultar-nombres", action="store_true",
                    help="el anexo sale solo con códigos, sin nombres de servicio")
    a = ap.parse_args()

    print()
    print("#" * 76)
    print("# PREP · proteccion de la informacion comercial")
    print(f"# {VERSION_SCRIPT}" + ("   ·   APLICANDO" if a.aplicar
                                   else "   ·   solo auditoria"))
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    titulo(1, "DE DONDE SALIO EL CATALOGO  ·  se comprueba, no se supone")
    cab = (RAIZ / "10_CATALOGO_SERVICIOS.md").read_text(encoding="utf-8")[:1200]
    generado = "No es el catálogo oficial" in cab or "BORRADOR GENERADO" in cab
    print(f"   ¿Dice el catalogo que es una reconstruccion? "
          f"{'SI' if generado else 'NO'}")
    print()
    if generado:
        print("   El catalogo NO se extrajo de la columna `Tema`. Su cabecera")
        print("   declara que se elaboro a partir de las lineas tecnologicas y")
        print("   areas del CRM, del playbook y de conocimiento publico del")
        print("   sector, y que no es el catalogo oficial de la organizacion.")
        print()
        print("   CONSECUENCIA: publicar las fichas NO publica la oferta real.")
        print("   El riesgo esta en otro sitio, y es el de los apartados 2 y 3.")

    # ------------------------------------------------------------------ 2
    titulo(2, "EXPOSICION 1 · la columna `Tema`  <-- la grave")
    # Si ya se aplico una vez, el original esta en la copia privada. Leer de
    # ahi hace que el script se pueda repetir sin codificar codigos ya
    # codificados, que daria AR01 -> AR01 y perderia la equivalencia.
    copia_previa = PRIVADO / (OPORTUNIDADES.replace(".csv", "_con_tema.bak"))
    fuente = copia_previa if copia_previa.exists() else (LIMPIO / OPORTUNIDADES)
    if copia_previa.exists():
        print(f"   (se lee del original guardado en {copia_previa.name})")
    op = pd.read_csv(fuente, sep=";", low_memory=False)
    tema = op["Tema"].dropna().astype(str)
    print(f"   Filas con tema            : {len(tema):>6}")
    print(f"   Longitud media            : {tema.str.len().mean():>6.0f} caracteres")
    print()
    print("   Tratamiento que tiene hoy : LIMPIAR")
    print("   Lo que hace LIMPIAR       : normalizar espacios y acentos")
    print("   Lo que NO hace            : anonimizar nada")
    print()
    # senales de que hay nombres propios de terceros dentro
    con_mayus = tema[tema.str.contains(r"\b[A-Z][a-z]{3,}", regex=True, na=False)]
    print(f"   Temas con alguna palabra capitalizada (posible marca o producto"
          f" de cliente): {len(con_mayus)}   {len(con_mayus)/len(tema)*100:.0f} %")
    print()
    print("   Es texto libre escrito por el equipo comercial. Describe QUE se")
    print("   le hizo A QUIEN. Aunque el nombre de la cuenta este seudonimizado")
    print("   en la fila de al lado, el tema puede identificar al cliente por")
    print("   si solo si menciona su producto o su marca.")
    print()
    print("   DECISION PROPUESTA: sacarlo del fichero limpio y conservarlo solo")
    print("   en la carpeta privada. Es la misma decision de minimizacion que")
    print("   ya se tomo con los datos de contacto en A4.")
    print("   Coste: ninguno hoy. A8 nunca se construyo, y su script de")
    print("   preparacion lee del fichero BRUTO, no de este.")

    # ------------------------------------------------------------------ 3
    titulo(3, "EXPOSICION 2 · la estructura interna y el reparto del negocio")
    areas = op["Área de Empresa"].dropna().astype(str).str.strip()
    reparto = Counter(areas)
    print(f"   Areas distintas en el CRM : {len(reparto)}")
    print(f"   Oportunidades con area    : {len(areas)}")
    print()
    print("   El REPARTO por area dice donde se concentra el negocio. Publicar")
    print("   los recuentos absolutos es publicar el tamaño de cada unidad.")
    print()
    print("   Ya esta publicado en:")
    encontrados = []
    for doc in PUBLICABLES:
        ruta = RAIZ / doc
        if ruta.is_dir():
            ficheros = list(ruta.glob("*.md"))
        elif ruta.exists():
            ficheros = [ruta]
        else:
            continue
        for f in ficheros:
            try:
                t = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if any(r in t for r in RASTROS):
                encontrados.append(f.relative_to(RAIZ))
    if encontrados:
        for f in encontrados:
            print(f"      · {f}")
    else:
        print("      (ninguno)")
    print()
    print("   DECISION PROPUESTA: codificar las areas como AR01..ARnn y")
    print("   guardar la equivalencia real en la carpeta privada. En la memoria")
    print("   se habla de «area tecnica AR03», y el reparto se da en")
    print("   PORCENTAJES, no en numero de oportunidades.")

    # ------------------------------------------------------------------ 4
    titulo(4, "CODIFICACION DE AREAS")
    orden = [k for k, _ in reparto.most_common()]
    mapa = {nombre: codigo_area(nombre, i + 1) for i, nombre in enumerate(orden)}
    print(f"   {'codigo':<9}{'% de oportunidades':>20}   (el nombre real va a la"
          f" carpeta privada)")
    print("   " + "-" * 62)
    for nombre in orden:
        print(f"   {mapa[nombre]:<9}{reparto[nombre]/len(areas)*100:>19.1f} %")

    # ------------------------------------------------------------------ 5
    titulo(5, "EL ANEXO DEL CATALOGO")
    servicios = json.loads(CATALOGO.read_text(encoding="utf-8"))
    print(f"   Servicios en el catalogo  : {len(servicios)}")
    print(f"   Nombres de servicio       : "
          f"{'CODIGOS' if a.ocultar_nombres else 'se conservan'}")
    if not a.ocultar_nombres:
        print()
        print("   Se conservan porque son denominaciones genericas del sector")
        print("   —cualquier instituto de envase ofrece «ensayos de transporte»—")
        print("   y porque E18 y E24 dependen de esos textos concretos: sin")
        print("   ellos el anexo no permite reproducir los experimentos.")
        print()
        print("   Si la organizacion decide que tambien sobran, se relanza con")
        print("   --ocultar-nombres y se declara la perdida de reproducibilidad.")

    # ------------------------------------------------------------------ 6
    titulo(6, "APLICAR")
    if not a.aplicar:
        print("   Auditoria. No se ha escrito nada.")
        print("   Vuelve a lanzarlo con --aplicar cuando estes conforme.")
        print()
        return

    PRIVADO.mkdir(exist_ok=True)

    # 6a · la equivalencia real, a la carpeta privada
    # 6b · el tema, fuera del fichero limpio
    op[["Nº oportunidad", "Tema"]].to_csv(TEMA_PRIVADO, sep=";", index=False,
                                          encoding="utf-8")
    print(f"   [ok] {TEMA_PRIVADO.relative_to(RAIZ)}   (privado)")

    # La copia de seguridad va a la carpeta PRIVADA, no a 01_limpio: dejarla
    # al lado del fichero limpio no protegeria nada, el texto seguiria ahi.
    copia = PRIVADO / (OPORTUNIDADES.replace(".csv", "_con_tema.bak"))
    if not copia.exists():
        shutil.copy2(LIMPIO / OPORTUNIDADES, copia)
    op2 = op.drop(columns=["Tema"])
    # Area, linea y sublinea describen la misma estructura interna a tres
    # niveles de detalle. Codificar solo el area dejaria la puerta abierta:
    # la linea permite reconstruirla.
    mapas = {"Área de Empresa": mapa}
    for col, prefijo in [("Línea Tecnológica", "LT"),
                         ("Sublínea Tecnológica", "SL")]:
        if col not in op2.columns:
            continue
        vals = [v for v, _ in Counter(
            op2[col].dropna().astype(str).str.strip()).most_common()]
        mapas[col] = {v: f"{prefijo}{i+1:02d}" for i, v in enumerate(vals)}
    for col, m in mapas.items():
        if col in op2.columns:
            op2[col] = op2[col].map(lambda x: m.get(str(x).strip(), x))
    MAPEO_AREAS.write_text(json.dumps(
        {"campos": {c: m for c, m in mapas.items()},
         "nota": "Equivalencia entre los codigos publicados y la estructura "
                 "real del CRM. NO se comparte ni se sube a ningun sitio."},
        indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"   [ok] {MAPEO_AREAS.relative_to(RAIZ)}   "
          f"({sum(len(m) for m in mapas.values())} equivalencias)")
    op2.to_csv(LIMPIO / OPORTUNIDADES, sep=";", index=False, encoding="utf-8")
    print(f"   [ok] {OPORTUNIDADES}   sin `Tema` y con areas codificadas")
    print(f"        copia previa en {copia.name} · borrala cuando compruebes")

    # 6c · el anexo publicable
    lineas = [
        "# Anexo · Catálogo de servicios empleado por el agente A5",
        "",
        "> **Naturaleza de este catálogo.** No es el catálogo comercial de la",
        "> organización. Es una **reconstrucción** elaborada a partir de las",
        "> líneas de trabajo del sistema de gestión, del playbook y de",
        "> conocimiento público del sector, y validada por la autora. Se emplea",
        "> como entrada de los experimentos E17, E18, E20 y E24.",
        ">",
        "> **Confidencialidad.** La estructura interna de áreas de la",
        "> organización no se publica: cada servicio se adscribe a un código",
        "> `ARnn` cuya equivalencia con la unidad real no forma parte de esta",
        "> memoria. Tampoco se publican precios, tarifas ni importes, por",
        "> decisión declarada en el apartado 4.2.4.",
        "",
        f"Servicios: **{len(servicios)}** · áreas codificadas: **{len(mapa)}**",
        "",
        "---",
        "",
    ]
    # codigo de area para cada servicio, por su nombre normalizado
    def cod_serv(s):
        real = str(s.get("area", "")).strip()
        for nombre, c in mapa.items():
            if sin_acentos(nombre)[:18] in sin_acentos(real) or \
               sin_acentos(real)[:18] in sin_acentos(nombre):
                return c
        return "AR—"

    for i, s in enumerate(servicios, 1):
        cod = s.get("codigo", f"S{i:02d}")
        nombre = "(nombre no publicado)" if a.ocultar_nombres else s.get("nombre", "")
        lineas += [
            f"## {cod} · {nombre}",
            "",
            "| | |",
            "|---|---|",
            f"| **Área técnica** | `{cod_serv(s)}` |",
            f"| **Tipo de servicio** | {s.get('tipo', '')} |",
            "",
        ]
        if s.get("resuelve") and not a.ocultar_nombres:
            lineas += [f"**Qué resuelve.** {s['resuelve']}", ""]
        if s.get("senales"):
            lineas += ["**Señales en la web del cliente.** "
                       + ", ".join(s["senales"][:12]) + ".", ""]
        lineas += ["---", ""]

    lineas += [
        "## Reparto del histórico por área codificada",
        "",
        "Se expresa en porcentaje. Los recuentos absolutos identificarían el",
        "tamaño de cada unidad de la organización y no se publican.",
        "",
        "| Área | % de oportunidades |",
        "|---|---|",
    ]
    for nombre in orden:
        lineas.append(f"| `{mapa[nombre]}` | {reparto[nombre]/len(areas)*100:.1f} % |")
    lineas += ["", f"Base: {len(areas)} oportunidades con área asignada.", ""]

    ANEXO.write_text("\n".join(lineas), encoding="utf-8")
    print(f"   [ok] {ANEXO.name}   <- el anexo para la memoria")
    print()
    print("   LO QUE TIENES QUE REVISAR TU")
    print("   1. Abre el anexo y comprueba que ninguna ficha describe algo que")
    print("      la organizacion considere reservado.")
    print("   2. Decide si los NOMBRES de servicio pueden publicarse. Si no,")
    print("      relanza con --ocultar-nombres.")
    print("   3. La carpeta datos/_mapeo_privado/ no puede salir de tu equipo")
    print("      ni subirse a ningun sitio. Contiene la sal, el mapeo de")
    print("      empresas, el de areas y ahora los temas.")
    print()


if __name__ == "__main__":
    main()
