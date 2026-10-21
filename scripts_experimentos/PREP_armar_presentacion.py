# -*- coding: utf-8 -*-
"""
PREP_armar_presentacion.py · arma la carpeta MASTER PRESENTACION
=================================================================

QUE HACE
    Monta una copia ordenada del proyecto separando lo que el sistema
    NECESITA para funcionar de lo que fue investigacion. Nada se mueve ni se
    borra del original: todo son copias.

LA ESTRUCTURA QUE DEJA

    MASTER PRESENTACION/
      00_LEEME.md                 el mapa de todo
      1_SISTEMA/                  lo que hace falta para que funcione
         scripts/                 la cadena de produccion, en orden
         datos/                   los datos que consume
         NO_ENTREGAR/             la llave de reidentificacion  <-- OJO
         COMO_LANZARLO.md
      2_MEMORIA/                  la memoria, sus figuras y lo que las genera
      3_DOCUMENTACION/            bitacora, disenos y reproducibilidad
      4_EXPERIMENTOS/             la investigacion: comparativas y pruebas

POR QUE LOS DATOS ESTAN UNA SOLA VEZ
    Ocupan 198 MB. Ponerlos tambien en 4_EXPERIMENTOS costaria otros 198 y,
    peor, crearia dos copias que acabarian divergiendo. Los experimentos se
    lanzan copiando el script a 1_SISTEMA/scripts/, y asi queda escrito.

QUE NO SE COPIA, Y POR QUE
    · resultados_e31.zip (1,7 GB): lleva dentro los pesos del modelo y el
      estado del optimizador, que ya no sirven. Lo util se extrajo.
    · los paquete_*.zip de Colab (54 MB): los regenera PREP_paquete_*.py
    · datos/04_recuperado: restos de una recuperacion, ya no hacen falta
    · 90_APARCADO: experimento abandonado

LA CARPETA NO_ENTREGAR
    `_mapeo_privado` contiene `mapeo.json` y `sal.txt`, que juntos vuelven a
    identificar a todas las empresas, y los textos de `Tema`. Va dentro para
    que el sistema arranque, pero con ese nombre y con aviso, porque
    entregarla anularia la seudonimizacion declarada en 4.2.4: bajo RGPD,
    dato seudonimizado mas llave es dato personal otra vez.

    `--limpiar-antes-de-entregar` la borra de la copia de un golpe.

COMO SE EJECUTA
    python scripts/PREP_armar_presentacion.py              # ensayo
    python scripts/PREP_armar_presentacion.py --aplicar
    python scripts/PREP_armar_presentacion.py --limpiar-antes-de-entregar
"""

import shutil
import sys
from pathlib import Path

VERSION_SCRIPT = "v1 · 04-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "MASTER PRESENTACION"

# ---------------------------------------------------------------------------
# El reparto de los scripts. Esta es la decision de fondo del script, asi que
# va explicita y comentada en vez de deducirse de un patron del nombre.
# ---------------------------------------------------------------------------
SISTEMA_PREPARAR = [
    ("PREP_anonimizar.py", "1 · seudonimiza el export del CRM"),
    ("PREP_inspeccionar_cuentas.py", "2 · examina las cuentas, solo agregados"),
    ("PREP_scrapear_webs.py", "3 · descarga el texto de las webs"),
    ("PREP_limpieza_texto.py", "4 · quita cookies y plantillas"),
    ("PREP_preparar_cuentas.py", "5 · arma el conjunto y lo reparte"),
    ("PREP_confidencialidad.py", "6 · protege la informacion comercial"),
    ("F8_A8_preparar_datos.py", "7 · prepara los datos del enrutado"),
    ("F6_A6_corpus_correos.py", "8 · trocea y seudonimiza los correos"),
    ("PREP_casar_etiquetas_correos.py", "9 · pega las etiquetas de A6"),
]
SISTEMA_AGENTES = [
    ("F2_A2_E8_E10_transformer.py", "A2 · clasificar el sector"),
    ("F3_A3_E14_fase1_encaje.py", "A3 fase 1 · puntuar la cuenta"),
    ("F3_A3_E12_E16_conversion.py", "A3 fase 2 · la tabla de conversion"),
    ("F5_A5_E17_emparejar_lexico.py", "A5 · emparejar, parte lexica"),
    ("F5_A5_E18_emparejar_semantico.py", "A5 · emparejar, parte semantica"),
    ("F5_A5_E19_generar_correos.py", "A5 · redactar el correo, version por servicio"),
    # El diseno vigente de A5. La seleccion automatica de servicio se retiro
    # tras medirla, de modo que el correo se escribe sobre un brief de campana
    # que decide una persona. El x3,9 de RQ4 sale de aqui, no de E19.
    ("F5_A5_E20_campana.py", "A5 · redactar el correo de campana (el vigente)"),
    ("F6_A6_agente_recepcion.py", "A6 · atender lo que entra"),
    ("F6_A6_identidad_dos_vias.py", "A6 · la identidad, por las dos vias"),
    ("F8_A8_tema_protegido.py", "A7 · enrutar al area tecnica"),
    ("F8_A8_tema_modelo.py", "A7 · el modelo del tipo de servicio"),
    ("F8_A8_briefing_traspaso.py", "A7 · el briefing de traspaso"),
    ("F9_A9_seguimiento_oportunidades.py", "A8 · seguir la oportunidad"),
    ("A0_orquestador.py", "A0 · encadena la via de salida"),
    ("A0_circuito_recepcion.py", "A0 · encadena la via de entrada y escribe el CRM simulado"),
    ("VERIFICAR_A7_A8_sin_texto.py",
     "comprueba el enrutado y la cualificacion SIN el texto original"),
]
MEMORIA_SCRIPTS = ["fig_comun.py", "fig_color.py", "FIG_arquitectura.py",
                   "FIG_fichas_agentes.py", "FIG_resultados.py",
                   "FIG_numerar_memoria.py", "FIG_cotejar_numeracion.py"]
DOC_SCRIPTS = ["PREP_paquete_sin_texto.py", "PREP_actualizar_cifras.py", "PREP_integrar_orquestador_memoria.py",
               "PREP_registrar_A6_A7_A9.py", "PREP_completar_A6_A7_A9.py",
               "PREP_recuperar_seccion_perdida.py", "PREP_armar_presentacion.py"]

# Documentos de la raiz. Los que describen el sistema van con el sistema.
DOC_RAIZ = ["00_SECUENCIA_SDR.txt", "01_GLOSARIO.txt", "02_arquitectura_y_plan.md",
            "03_playbook_comercial.md", "04_export_crm.md", "05_DATOS_NECESARIOS.md",
            "06_MODELOS_POR_AGENTE.md", "07_HALLAZGOS_CRM.md", "08_BITACORA.md",
            "09_DISENO_A4.md", "10_CATALOGO_SERVICIOS.md",
            "11_METODOLOGIA_ASISTENCIA_IA.md", "12_CAMPANAS.md", "13_DISENO_F6.md",
            "14_REPRODUCIBILIDAD.md", "15_INDICE_MEMORIA.md", "16_GUION_DEFENSA.md",
            "17_DISENO_A3_FASE2.md", "ANEXO_catalogo_servicios.md", "ESTADO.txt"]

# Documentos que los scripts del sistema LEEN AL EJECUTARSE, no solo para
# consultarlos: E17 busca el catalogo y E20 el de campanas en la raiz de su
# propia carpeta. Si solo van en 3_DOCUMENTACION, el sistema no arranca desde
# 1_SISTEMA. Se copian en los dos sitios a proposito.
SISTEMA_DOCS = ["10_CATALOGO_SERVICIOS.md", "12_CAMPANAS.md"]

DATOS_FUERA = {"resultados_e31.zip"}     # 1,7 GB de pesos que ya no sirven
DATOS_CARPETAS_FUERA = {"04_recuperado"}  # restos de una recuperacion


def copiar(origen, destino, n=None):
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origen, destino)
    if n is not None:
        n[0] += 1
        n[1] += origen.stat().st_size


def main():
    aplicar = "--aplicar" in sys.argv
    limpiar = "--limpiar-antes-de-entregar" in sys.argv

    print()
    print("=" * 76)
    print(f"PREP · armar MASTER PRESENTACION  ·  {VERSION_SCRIPT}")
    print("=" * 76)

    # --------------------------------------------------- limpiar y salir
    if limpiar:
        ne = DESTINO / "1_SISTEMA" / "datos" / "_mapeo_privado"
        if not ne.exists():
            print()
            print(f"   No hay nada que limpiar: {ne.name} no existe.")
            print()
            return
        print()
        print(f"   Voy a BORRAR {ne}")
        print(f"   Contiene {sum(1 for _ in ne.rglob('*') if _.is_file())} ficheros.")
        print("   El original en datos/_mapeo_privado NO se toca.")
        if not aplicar:
            print()
            print("   Ensayo. Anade --aplicar para borrarla de verdad.")
            print()
            return
        # Se borran los FICHEROS primero y la carpeta despues.
        #
        # En OneDrive la carpeta vacia a veces no se deja borrar porque el
        # cliente de sincronizacion la tiene abierta, y `rmtree` revienta
        # con un error que NO distingue «no he borrado nada» de «he borrado
        # todo menos el directorio vacio». En un script cuyo trabajo es
        # proteger datos eso no sirve: hay que decir exactamente que paso.
        borrados, fallidos = 0, []
        for f in sorted(ne.rglob("*"), key=lambda x: -len(x.parts)):
            if f.is_file():
                try:
                    f.unlink()
                    borrados += 1
                except OSError as err:
                    fallidos.append((f.name, err))
        for f in sorted(ne.rglob("*"), key=lambda x: -len(x.parts)):
            if f.is_dir():
                try:
                    f.rmdir()
                except OSError:
                    pass

        print()
        if fallidos:
            print(f"   [!!] {len(fallidos)} fichero(s) NO se han podido borrar:")
            for nom, err in fallidos:
                print(f"        {nom}: {err}")
            print()
            print("   LA COPIA TODAVIA NO SE PUEDE ENTREGAR. Cierra lo que los")
            print("   tenga abiertos —OneDrive, Excel, el explorador— y repite.")
            raise SystemExit(1)

        print(f"   [ok] {borrados} fichero(s) borrados. Dentro no queda ninguno.")
        try:
            ne.rmdir()
            print("   [ok] y la carpeta tambien.")
        except OSError:
            print("   [i]  La carpeta VACIA no se deja borrar: OneDrive la")
            print("        tiene abierta. NO IMPORTA, dentro no queda nada;")
            print("        se puede borrar a mano cuando OneDrive la suelte.")
        print()
        print("   LA COPIA YA SE PUEDE ENTREGAR.")
        print("   El original en MASTER/datos/_mapeo_privado no se ha tocado.")
        print()
        return

    print(f"   origen : {RAIZ.name}")
    print(f"   destino: {DESTINO.name}")
    print(f"   modo   : {'COPIANDO' if aplicar else 'ensayo, no escribe nada'}")

    n = [0, 0]
    plan = []

    # ------------------------------------------------------------ 1 SISTEMA
    S = DESTINO / "1_SISTEMA"
    for lista, sub in ((SISTEMA_PREPARAR, "scripts"), (SISTEMA_AGENTES, "scripts")):
        for f, _ in lista:
            o = RAIZ / "scripts" / f
            if not o.exists():
                plan.append(("FALTA", f, 0))
                continue
            plan.append(("1_SISTEMA/scripts", f, o.stat().st_size))
            if aplicar:
                copiar(o, S / sub / f, n)

    # Los dos documentos que los scripts leen al ejecutarse.
    for f in SISTEMA_DOCS:
        o = RAIZ / f
        if not o.exists():
            plan.append(("FALTA", f, 0))
            continue
        plan.append(("1_SISTEMA", f, o.stat().st_size))
        if aplicar:
            copiar(o, S / f, n)

    # requirements.txt, que antes no existia. Sin el, quien reciba la copia
    # tiene que adivinar las librerias y sus versiones.
    req = RAIZ / "requirements.txt"
    if req.exists():
        plan.append(("1_SISTEMA", "requirements.txt", req.stat().st_size))
        if aplicar:
            copiar(req, S / "requirements.txt", n)

    # Lo que sobra en la carpeta de scripts del sistema.
    #
    # PREP solo copiaba encima, nunca retiraba, y asi quedo una copia del
    # 04-10 de un script que el 06-10 ya era otro. Es el riesgo de X11 —leer
    # el fichero equivocado— metido en la propia entrega. Esta carpeta se
    # genera entera desde las listas de arriba, de modo que lo que no este en
    # ellas es un resto: se nombra uno por uno antes de retirarlo.
    previstos = {f for f, _ in SISTEMA_PREPARAR} | {f for f, _ in SISTEMA_AGENTES}
    carpeta = S / "scripts"
    if carpeta.exists():
        sobran = sorted(p for p in carpeta.iterdir()
                        if p.is_file() and p.name not in previstos)
        for p_ in sobran:
            plan.append(("1_SISTEMA/scripts <-- RESTO", p_.name,
                         p_.stat().st_size))
            if aplicar:
                p_.unlink()

    # Los datos, una sola vez.
    #
    # OJO CON _mapeo_privado. La idea era ponerlo en una carpeta NO_ENTREGAR
    # para que no hubiera duda, pero los scripts lo buscan en
    # `datos/_mapeo_privado` y asi el sistema NO ARRANCA. Un enlace de
    # directorio lo resolveria, pero esta carpeta vive en OneDrive y los
    # enlaces ahi dan problemas de sincronizacion.
    #
    # Asi que se queda donde los scripts lo esperan y la advertencia se hace
    # imposible de pasar por alto: un aviso dentro de la propia carpeta y
    # otro, con nombre que salta a la vista, en la raiz de la copia.
    for sub in sorted((RAIZ / "datos").iterdir()):
        if not sub.is_dir() or sub.name in DATOS_CARPETAS_FUERA:
            continue
        privado = sub.name == "_mapeo_privado"
        base = S / "datos" / sub.name
        tam = 0
        for f in sub.rglob("*"):
            if not f.is_file() or f.name in DATOS_FUERA:
                continue
            tam += f.stat().st_size
            if aplicar:
                copiar(f, base / f.relative_to(sub), n)
        plan.append(("1_SISTEMA/datos  <-- NO ENTREGAR" if privado
                     else "1_SISTEMA/datos", sub.name, tam))

    # ------------------------------------------------------------ 2 MEMORIA
    M = DESTINO / "2_MEMORIA"
    for f in sorted((RAIZ / "memoria").glob("*")):
        if f.is_file():
            plan.append(("2_MEMORIA/memoria", f.name, f.stat().st_size))
            if aplicar:
                copiar(f, M / "memoria" / f.name, n)
    for f in sorted((RAIZ / "figuras").glob("*")):
        if f.is_file():
            if aplicar:
                copiar(f, M / "figuras" / f.name, n)
    plan.append(("2_MEMORIA/figuras",
                 f"{len(list((RAIZ/'figuras').glob('*')))} ficheros",
                 sum(x.stat().st_size for x in (RAIZ / "figuras").glob("*")
                     if x.is_file())))

    # Lo que sobre en la carpeta de figuras de la entrega. Es el mismo
    # defecto de X33 en un tercer sitio: al renumerar las figuras tras D24,
    # las de la numeracion anterior se quedaron aqui —entre ellas la ficha
    # de un agente que ya no existe con ese nombre— porque PREP copiaba y
    # no retiraba.
    carpeta_fig = M / "figuras"
    if carpeta_fig.exists():
        nombres_fig = {f.name for f in (RAIZ / "figuras").glob("*")}
        for p_ in sorted(carpeta_fig.iterdir()):
            if p_.is_file() and p_.name not in nombres_fig:
                plan.append(("2_MEMORIA/figuras <-- RESTO", p_.name,
                             p_.stat().st_size))
                if aplicar:
                    p_.unlink()
    for f in MEMORIA_SCRIPTS:
        o = RAIZ / "scripts" / f
        if o.exists():
            if aplicar:
                copiar(o, M / "scripts_de_figuras" / f, n)
    plan.append(("2_MEMORIA/scripts_de_figuras", f"{len(MEMORIA_SCRIPTS)} scripts", 0))

    # ------------------------------------------------------ 3 DOCUMENTACION
    D = DESTINO / "3_DOCUMENTACION"
    for f in DOC_RAIZ:
        o = RAIZ / f
        if not o.exists():
            plan.append(("FALTA", f, 0))
            continue
        plan.append(("3_DOCUMENTACION", f, o.stat().st_size))
        if aplicar:
            copiar(o, D / f, n)
    for f in DOC_SCRIPTS:
        o = RAIZ / "scripts" / f
        if o.exists() and aplicar:
            copiar(o, D / "herramientas" / f, n)
    plan.append(("3_DOCUMENTACION/herramientas", f"{len(DOC_SCRIPTS)} scripts", 0))

    # ------------------------------------------------------- 4 EXPERIMENTOS
    E = DESTINO / "4_EXPERIMENTOS"
    ya = {f for f, _ in SISTEMA_PREPARAR + SISTEMA_AGENTES}
    ya |= set(MEMORIA_SCRIPTS) | set(DOC_SCRIPTS)
    exp = [f for f in sorted((RAIZ / "scripts").glob("*.py"))
           if f.name not in ya and f.name != "renombrar_scripts.py"]
    for f in exp:
        plan.append(("4_EXPERIMENTOS/scripts", f.name, f.stat().st_size))
        if aplicar:
            copiar(f, E / "scripts" / f.name, n)

    # Y lo que sobre aqui, por el mismo motivo: cuando un script pasa de
    # experimento a sistema, su copia antigua se queda en esta carpeta y
    # aparece dos veces en la entrega.
    carpeta_exp = E / "scripts"
    if carpeta_exp.exists():
        nombres_exp = {f.name for f in exp}
        for p_ in sorted(carpeta_exp.iterdir()):
            if p_.is_file() and p_.name not in nombres_exp:
                plan.append(("4_EXPERIMENTOS <-- RESTO", p_.name,
                             p_.stat().st_size))
                if aplicar:
                    p_.unlink()
    # los resultados de los experimentos, que son ligeros
    for f in sorted((RAIZ / "datos" / "03_resultados").glob("*.json")):
        if aplicar:
            copiar(f, E / "resultados" / f.name, n)
    plan.append(("4_EXPERIMENTOS/resultados",
                 f"{len(list((RAIZ/'datos'/'03_resultados').glob('*.json')))} json", 0))
    for f in sorted(RAIZ.glob("*.ipynb")):
        if aplicar:
            copiar(f, E / "cuadernos_colab" / f.name, n)
    plan.append(("4_EXPERIMENTOS/cuadernos_colab",
                 f"{len(list(RAIZ.glob('*.ipynb')))} cuadernos", 0))

    # ------------------------------------------------------------ el informe
    print()
    print(f"   {'destino':<32}{'qué':<42}{'tamaño':>10}")
    print("   " + "-" * 84)
    faltan = 0
    for dest, que, tam in plan:
        if dest == "FALTA":
            print(f"   {'[!!] NO EXISTE':<32}{que:<42}{'':>10}")
            faltan += 1
        else:
            t = f"{tam/1e6:.1f} MB" if tam else ""
            print(f"   {dest:<32}{que[:40]:<42}{t:>10}")

    print()
    print(f"   scripts del sistema  : {len(SISTEMA_PREPARAR)+len(SISTEMA_AGENTES)}")
    print(f"   scripts de experimentos: {len(exp)}")
    print(f"   scripts de figuras   : {len(MEMORIA_SCRIPTS)}")
    print(f"   herramientas de docs : {len(DOC_SCRIPTS)}")
    if faltan:
        print(f"   [!!] {faltan} fichero(s) del plan no existen")

    if not aplicar:
        print()
        print("   Ensayo. Lánzalo con --aplicar para copiar de verdad.")
        print()
        return

    escribir_leemes()

    print()
    print(f"   [ok] {n[0]} ficheros copiados · {n[1]/1e6:.0f} MB")
    print()
    print("   COTEJO")
    ko = 0
    for ruta, etiqueta in (
            ("00_LEEME.md", "el mapa"),
            ("1_SISTEMA/COMO_LANZARLO.md", "las instrucciones"),
            ("1_SISTEMA/scripts/A0_orquestador.py", "el orquestador"),
            ("1_SISTEMA/datos/02_derivado/cuentas_train.csv", "los datos"),
            ("1_SISTEMA/datos/_mapeo_privado/sal.txt", "la carpeta privada"),
            ("1_SISTEMA/datos/_mapeo_privado/NO_ENTREGAR_LEEME.txt", "su aviso"),
            ("AAA_LEEME_ANTES_DE_ENTREGAR.txt", "el aviso de la raíz"),
            ("2_MEMORIA/memoria/CAP4_6_resultados.md", "la memoria"),
            ("3_DOCUMENTACION/08_BITACORA.md", "la bitácora"),
            ("4_EXPERIMENTOS/scripts/F2_A2_E4_baselines.py", "los experimentos")):
        ok = (DESTINO / ruta).exists()
        print(f"   [{'ok' if ok else 'NO'}]  {etiqueta}")
        ko += 0 if ok else 1
    # el zip grande NO debe estar
    grandes = [f for f in DESTINO.rglob("*") if f.is_file()
               and f.stat().st_size > 500e6]
    print(f"   [{'ok' if not grandes else 'NO'}]  ningún fichero de más de 500 MB")
    ko += 0 if not grandes else 1
    print()
    if ko:
        raise SystemExit(f"   {ko} comprobación(es) fallan.")
    print("   Todo cotejado.")
    print()


def escribir_leemes():
    """Los ficheros que explican la carpeta, y los dos avisos."""
    # El numero de scripts del sistema se cuenta, no se escribe a mano:
    # decia 20 cuando eran 25. Se usa replace y no format porque el texto
    # del LEEME lleva llaves por su cuenta.
    (DESTINO / "00_LEEME.md").write_text(
        LEEME.replace("{N_SISTEMA}",
                      str(len(SISTEMA_PREPARAR) + len(SISTEMA_AGENTES))),
        encoding="utf-8")
    (DESTINO / "1_SISTEMA" / "COMO_LANZARLO.md").write_text(COMO, encoding="utf-8")
    (DESTINO / "4_EXPERIMENTOS" / "LEEME.md").write_text(LEEME_EXP, encoding="utf-8")
    (DESTINO / "1_SISTEMA" / "LEEME_PARA_QUIEN_LO_PRUEBE.md").write_text(
        LEEME_TRIBUNAL, encoding="utf-8")
    priv = DESTINO / "1_SISTEMA" / "datos" / "_mapeo_privado"
    if priv.exists():
        # uno dentro de la carpeta y otro donde se ve al abrir la copia
        (priv / "NO_ENTREGAR_LEEME.txt").write_text(AVISO, encoding="utf-8")
        (DESTINO / "AAA_LEEME_ANTES_DE_ENTREGAR.txt").write_text(
            AVISO, encoding="utf-8")


LEEME = """# MASTER PRESENTACIÓN

Copia ordenada del proyecto. **Nada de esto es el original**: el original sigue
en `MASTER/` y no se ha tocado.

La idea es separar **lo que hace falta para que el sistema funcione** de **lo que
fue investigación**, que es mucho más y confunde al mirarlo todo junto.

## Qué hay en cada carpeta

| Carpeta | Qué contiene | Para qué |
| --- | --- | --- |
| **1_SISTEMA** | Los {N_SISTEMA} scripts que ejecutan el sistema, y los datos que consumen | Es lo único que hay que mirar para entender cómo funciona |
| **2_MEMORIA** | La memoria por capítulos, las 23 figuras y los scripts que las generan | Lo que se entrega |
| **3_DOCUMENTACIÓN** | Bitácora, diseños, reproducibilidad, guion de defensa | El respaldo de cada cifra |
| **4_EXPERIMENTOS** | Las comparativas, ablaciones y pruebas que no forman parte del sistema | De dónde salieron las decisiones |

## ⚠️ Antes de entregar nada

`1_SISTEMA/datos/_mapeo_privado/` contiene la llave que vuelve a identificar a
todas las empresas. **Hay que borrarla antes de compartir esta carpeta.** Se hace con:

```
python MASTER/scripts/PREP_armar_presentacion.py --limpiar-antes-de-entregar --aplicar
```

Lee `AAA_LEEME_ANTES_DE_ENTREGAR.txt`, en esta misma carpeta, para el detalle.

## Lo que no se copió, a propósito

- `resultados_e31.zip`, 1,7 GB de pesos de modelo y estado del optimizador que
  ya no sirven de nada. Lo aprovechable se extrajo en su momento.
- Los `paquete_*.zip` de Colab, 54 MB. Los regenera `PREP_paquete_*.py`.
- `datos/04_recuperado/`, restos de una recuperación ya resuelta.
- `90_APARCADO/`, un experimento abandonado.
"""

COMO = """# Cómo se lanza el sistema

Los scripts esperan estar en `scripts/` con `datos/` al lado, que es como están
aquí. Se lanzan **desde esta carpeta** (`1_SISTEMA`), no desde dentro de
`scripts/`.

## El orden

### Preparar los datos — solo la primera vez, o cuando llegue un export nuevo

```bash
python scripts/PREP_anonimizar.py
python scripts/PREP_inspeccionar_cuentas.py
python scripts/PREP_scrapear_webs.py
python scripts/PREP_limpieza_texto.py
python scripts/PREP_preparar_cuentas.py
python scripts/PREP_confidencialidad.py --aplicar
python scripts/F8_A8_preparar_datos.py
python scripts/F6_A6_corpus_correos.py --guardar
python scripts/PREP_casar_etiquetas_correos.py --guardar
```

### Los agentes

```bash
python scripts/F2_A2_E8_E10_transformer.py      # A2 · necesita GPU
python scripts/F3_A3_E14_fase1_encaje.py        # A3 fase 1
python scripts/F3_A3_E12_E16_conversion.py      # A3 fase 2
python scripts/F5_A5_E18_emparejar_semantico.py # A5 · emparejar
python scripts/F5_A5_E19_generar_correos.py     # A5 · redactar, necesita GPU
python scripts/F5_A5_E20_campana.py --campana C01  # A5 · modo campana, el vigente
python scripts/F6_A6_agente_recepcion.py --guardar       # A6 · recepcion
python scripts/F8_A8_tema_protegido.py --guardar         # A7 · enrutado
python scripts/F8_A8_briefing_traspaso.py --guardar      # A7 · briefing
python scripts/F9_A9_seguimiento_oportunidades.py --guardar  # A8 · seguimiento
```

> **Los nombres de fichero conservan la numeracion anterior.** Los agentes se
> renumeraron el 07-10 (decision D24): lo que el fichero llama A8 es hoy A7, y
> lo que llama A9 es hoy A8. El texto que imprimen ya usa los nombres nuevos.
> `F8_A8_briefing_traspaso.py` entrena al arrancar el clasificador del tipo de
> servicio, que vive en `F8_A8_tema_modelo.py`: los dos ficheros tienen que
> estar en la misma carpeta.

### El orquestador, que los encadena

```bash
python scripts/A0_orquestador.py --guardar
```

Deja `datos/03_resultados/orquestador_salida.csv` con una fila por empresa y el
**motivo de cada decisión**, y `orquestador_cola_redaccion.csv` con las que
superan el umbral, ordenadas por prioridad.

## Dos avisos

**No hay ningún modelo guardado.** Cada script reentrena desde cero al
lanzarse. Es deliberado: así cualquiera reproduce las cifras sin tener que
creerse un fichero binario. Para producción habría que guardarlos y cargarlos,
que es lo que describe el capítulo 7 de la memoria.

**Dos cosas necesitan procesamiento gráfico:** el transformer de A2 y la
redacción de A5. Todo lo demás corre en un portátil. Es la arquitectura de dos
circuitos del apartado 7.2.
"""

AVISO = """ATENCION - ESTA CARPETA NO SE ENTREGA
=====================================

QUE HAY AQUI

   mapeo.json        la correspondencia entre cada empresa real y su
                     seudonimo. 4,6 MB.
   sal.txt           la sal criptografica. Con ella se pueden volver a
                     calcular los seudonimos de cualquier empresa.
   temas_oportunidades.csv   el texto libre del campo Tema, que es
                     informacion comercial que Empresa pidio proteger.
   ..._anon_con_tema.bak     lo mismo, en copia de seguridad.

POR QUE IMPORTA

   La memoria declara en el apartado 4.2.4 que los datos estan
   SEUDONIMIZADOS. Esa afirmacion solo se sostiene si la llave se guarda
   aparte.

   Bajo el RGPD, dato seudonimizado MAS la llave vuelve a ser dato
   personal. Entregar esta carpeta junto al resto anularia la proteccion
   que el trabajo declara, y ademas publicaria informacion comercial de
   la empresa.

QUE HACER ANTES DE ENTREGAR

   python MASTER/scripts/PREP_armar_presentacion.py --limpiar-antes-de-entregar --aplicar

   Borra esta carpeta DE LA COPIA. El original en MASTER/datos/_mapeo_privado
   no se toca, asi que el sistema sigue funcionando en MASTER.

QUE DEJA DE FUNCIONAR SI LA BORRAS

   A7 y A8, que leen temas_oportunidades.csv. El resto del sistema no la
   necesita.
"""

LEEME_TRIBUNAL = r"""# Para quien quiera ejecutar el sistema

Esta carpeta se entrega **sin los datos privados**: faltan la tabla que
relaciona cada empresa con su seudónimo y el campo de texto comercial con que
se entrenan dos de los agentes. Aun así **el sistema se puede ejecutar y sus
cifras se pueden comprobar**, y esto explica cómo.

## Lo primero: el entorno

```bash
python -m venv .venv
.venv\Scriptsctivate
pip install -r requirements.txt
```

**Si se quiere usar la tarjeta gráfica**, `torch` se instala aparte y ANTES del
resto, con el índice de la versión de CUDA del equipo:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python -c "import torch; print(torch.cuda.is_available())"
```

## Qué necesita tarjeta gráfica, y qué no

**Solo dos de los nueve componentes la necesitan.** Los demás corren en
cualquier portátil en segundos o pocos minutos.

| Componente | GPU | Descarga de Hugging Face |
| --- | --- | --- |
| A2 · clasificar el sector | **sí** | `xlm-roberta-base`, ~1,1 GB |
| A5 · emparejar servicio | no | `multilingual-e5-small`, ~0,5 GB |
| A0 · circuito de recepcion | no | el mismo `multilingual-e5-small` |
| A5 · redactar el correo | **sí** | `Qwen2.5-7B-Instruct`, ~15 GB |
| A3, A6, A7, A8, A9, A0 | no | — |

Los modelos se descargan solos la primera vez. En total unos 17 GB.

## Qué se puede ejecutar tal cual

```bash
python scripts/F3_A3_E14_fase1_encaje.py        # A3 · priorizar
python scripts/F6_A6_agente_recepcion.py        # A6 · recepción
python scripts/F6_A6_identidad_dos_vias.py      # A6 · identidad
python scripts/F9_A9_seguimiento_oportunidades.py   # A8 · seguimiento
python scripts/A0_orquestador.py                # el orquestador
```

El orquestador tarda unos minutos porque carga ficheros grandes; los demás,
segundos.

## A7 y A8: el caso especial

Estos dos se entrenan con un campo de texto del sistema de gestión que contiene
información comercial de la empresa y que **no se entrega**.

Para que puedan comprobarse igualmente, ese texto viaja **ya convertido a una
matriz mediante una función de troceo**: cada palabra se transforma en una
posición sin que se guarde la correspondencia, de modo que no hay diccionario
que deshacer.

```bash
python scripts/VERIFICAR_A7_A8_sin_texto.py
```

Entrena los dos clasificadores con esa matriz y compara con lo publicado:

| | Con la matriz | En la memoria |
| --- | --- | --- |
| A8 · enrutado al área | 80,16 % | 80,51 % |
| A7 · cualificación | 65,14 % | 66,20 % |

La diferencia de A7 es esperable: su modelo original usa TF-IDF y aquí va
troceado. La de A8 no lo sería, y por eso es menor: ese modelo **ya usaba
troceo**, por la decisión de protección que el apartado 4.2.4 documenta.

**Qué protege esto y qué no.** Protege de *leer* el texto: no viaja ningún
término. **No es cifrado**: quien sospeche que una palabra concreta está en el
corpus puede trocearla y comprobar si esa posición tiene peso. Queda dicho.

## Si algo no arranca

Los scripts que necesitan los datos privados lo dicen y se detienen con el
motivo, en vez de fallar de forma opaca. Si aparece un aviso de que falta
`_mapeo_privado`, es esto y es lo esperado.

## Dónde está cada cifra

`3_DOCUMENTACION/14_REPRODUCIBILIDAD.md` relaciona cada número publicado en la
memoria con el script que lo genera.
"""


LEEME_EXP = """# Experimentos y pruebas

Aquí está la investigación: las comparativas, las ablaciones y las pruebas que
**no forman parte del sistema** pero que justifican cada decisión tomada.

Los resultados de cada uno están en `resultados/`, en formato JSON, y cada cifra
publicada en la memoria se puede rastrear hasta uno de ellos a través de
`3_DOCUMENTACION/14_REPRODUCIBILIDAD.md`.

## Cómo se lanza uno

Los scripts esperan `datos/` al lado de `scripts/`, y aquí no hay datos —están
una sola vez, en `1_SISTEMA/datos/`, para que no existan dos copias que acaben
divergiendo.

Así que para ejecutar un experimento:

```bash
copy "4_EXPERIMENTOS\\scripts\\el_que_sea.py" "1_SISTEMA\\scripts\\"
cd 1_SISTEMA
python scripts/el_que_sea.py
```

## Qué hay aquí dentro

- **Comparativas de método**: los seis clasificadores de A2, árboles frente a
  redes neuronales, el léxico frente a lo semántico en el emparejamiento.
- **Controles**: permutaciones y pruebas de fundamentación, para comprobar que
  un resultado no sale por azar.
- **Diagnósticos**: por qué falla el emparejador, si hace falta el campo `Tema`.
- **Vías que no funcionaron**: la biblioteca de sectores, que perdió dos veces.
  Están aquí porque un resultado negativo medido también es un resultado.
- **Un script retirado**: `F2_A2_E31_biblioteca_entrenamiento.py` se niega a
  arrancar y explica por qué. Es el error X20.
"""


if __name__ == "__main__":
    main()
