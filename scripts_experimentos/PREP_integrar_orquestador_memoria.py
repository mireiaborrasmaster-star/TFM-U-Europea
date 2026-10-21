# -*- coding: utf-8 -*-
"""
PREP_integrar_orquestador_memoria.py - mete el orquestador en la memoria
=========================================================================

POR QUE EXISTE
    El orquestador se construyo y se midio el 30-09-2026 (E28) y se amplio
    con la segunda fase de A3 el 01-10-2026 (E29). Quedo registrado en la
    bitacora, en 14_REPRODUCIBILIDAD y en el capitulo 7, y se dibujaron sus
    dos figuras. Pero NO llego ni al capitulo de resultados ni al de
    discusion: el capitulo 5 seguia afirmando que el objetivo 3 no se habia
    cumplido, y el 4.6 no tenia apartado del orquestador, mientras el
    capitulo 5 remitia a un 4.6.5 que hablaba de otra cosa.

    Queda registrado como error X22. La causa: los cambios se aplicaron con
    ficheros _patch.py desechables cuyo resultado no se cotejo despues.

QUE HACE
    1. CAP4_6: corre 4.6.5 y 4.6.6 un numero, abre el apartado 4.6.5 del
       orquestador y corrige el parrafo que daba A0 por no construido.
    2. CAP5: pone el objetivo 3 como cumplido, en la tabla y en su apartado.

    NO toca los marcadores de figura: eso lo hace FIG_numerar_memoria.py,
    que los coloca por nombre. Este script solo deja el ancla puesta.

    Es idempotente: si ya esta hecho, lo dice y no cambia nada. Y COTEJA
    cada paso releyendo el fichero, que es justo lo que falto la vez pasada.

DE DONDE SALE CADA CIFRA
    E28 (2.652 empresas, la particion de prueba) y E29 (3.152 empresas, la
    tirada que incorpora la fase 2 de A3). Son poblaciones distintas y el
    texto lo dice en cada caso. Cotejadas contra 08_BITACORA.md y
    14_REPRODUCIBILIDAD.md, que coinciden.

COMO SE EJECUTA
    python scripts/PREP_integrar_orquestador_memoria.py           # ensayo
    python scripts/PREP_integrar_orquestador_memoria.py --aplicar
"""

import sys
from pathlib import Path

VERSION_SCRIPT = "v1 - 03-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
MEMORIA = RAIZ / "memoria"

# ---------------------------------------------------------------------------
# El apartado 4.6.5
# ---------------------------------------------------------------------------
APARTADO_A0 = """## 4.6.5 A0 · El sistema secuencial

Los apartados anteriores evalúan cada agente por separado, cada uno sobre su propia
partición y ninguno recibiendo la salida del anterior. El orquestador los encadena: entra
una empresa y sale una fila con todo lo decidido sobre ella y el motivo de cada decisión.

```
empresa
   |- A2 · clasificar el sector   -> sector predicho
   |- A3 · puntuar la cuenta      -> nota A-E     <- recibe el sector que predijo A2
   |- A5 · emparejar servicio     -> servicio + confianza
   |- A3 fase 2 · ajustar         -> prioridad alta / media / baja
   |- A5 · redactar               -> EN COLA
```

La redacción no se ejecuta en línea: el modelo generativo exige procesamiento gráfico. No
es una carencia sino el **circuito por lotes** del apartado 7.2, y la cola que deja el
orquestador es precisamente su entrada. El resto del recorrido se ejecuta completo en un
ordenador portátil, como esa arquitectura preveía.

**Lo que aporta encadenar.** La integración no requirió modelado nuevo: los cuatro pasos
existían y sus interfaces resultaron compatibles sin adaptación. Produjo, en cambio, dos
resultados que la evaluación por componentes no podía dar, y apuntan en direcciones
opuestas: uno corrige a la baja la gravedad del peor resultado del trabajo, y el otro
corrige al alza una limitación que estaba declarada como nota al pie.

### Resultado 1 · La mayoría de los errores de clasificación son inocuos

A3 recibe el sector que predijo A2, no el verdadero. Para medir el arrastre se puntuó cada
empresa dos veces, una con el sector predicho y otra con el real, y se comparó la nota:

| Clasificación sectorial | Empresas | Cambia la nota de A3 |
| --- | --- | --- |
| A2 acertó el sector | 1.372 | 0 · **0,0 %** |
| A2 falló el sector | 1.280 | 197 · **15,4 %** |
| **Total** | **2.652** | 197 · **7,4 %** |

`[TABLA 51e]` *Propagación del error de clasificación sectorial a la puntuación de
cuentas.* Elaboración propia.

A2 acierta el 51,73 %, cifra modesta tomada en sí misma. Pero solo el 7,4 % del total de
casos acusa ese error en la decisión siguiente: cuando A2 falla, la nota cambia en el 15,4 %
de las veces, y el 84,6 % restante son confusiones entre sectores que el modelo de
puntuación trata de igual manera.

**Es un resultado que ningún agente aislado puede producir.** La métrica de A2 informa de
cuántas veces se equivoca; solo la cadena informa de cuánto importa equivocarse.

### Resultado 2 · El encadenamiento revela un desajuste de población

El orquestador compara, variable a variable, cuántos valores faltaban en los datos con que
se entrenó A3 y cuántos faltan en las empresas que efectivamente le entran:

| Variable | Nulos al entrenar | Nulos en la población de entrada |
| --- | --- | --- |
| Tamaño de la empresa | 6,0 % | **62,0 %** |
| Asociado | 71,7 % | 25,3 % |
| Provincia | 11,8 % | 36,6 % |

`[TABLA 51f]` *Distancia entre la población de entrenamiento de A3 y la que le entrega el
agente anterior.* Elaboración propia.

La consecuencia es trazable. Entre las cuentas de entrenamiento **sin** tamaño registrado,
el 61 % tenía la nota T; el modelo aprendió que la ausencia de tamaño predice esa nota, lo
cual era cierto en su población y es falso en esta. Al aplicarse sobre la población
entrante, predice la nota T para el 61,7 % de los casos.

| Evaluación | Acierto | Suelo | Margen |
| --- | --- | --- | --- |
| A3 aislada, en su propia partición (apartado 4.6.2) | 49,24 % | 37,13 % | **+12,1** |
| A3 encadenada, sobre la población de entrada | 44,1 % | 37,9 % | **+6,2** |

`[TABLA 51g]` *Margen del modelo de puntuación sobre su clase mayoritaria, evaluado
aisladamente y encadenado.* Elaboración propia.

**Encadenar reduce a la mitad el margen sobre el suelo.** La limitación estaba declarada
desde la evaluación aislada, pero como nota al pie; el orquestador la convierte en una
cifra. Y la lección excede el caso: **evaluar los agentes por separado oculta fallos que
solo se manifiestan cuando cada uno recibe la entrada real del anterior.**

### Resultado 3 · El embudo, y dónde se pierden los casos

| Etapa | Empresas | Se pierden |
| --- | --- | --- |
| Entran | 2.652 | — |
| A2 las clasifica | 2.652 | 0 |
| A3 les pone nota | 2.652 | 0 |
| Tienen texto de página web utilizable | 1.573 | −1.079 |
| El emparejamiento de servicio es fiable (z ≥ 2,0) | 270 | −1.303 |
| **Llegan a la cola de redacción** | **270** | |

`[TABLA 51h]` *Embudo del recorrido completo sobre la partición de prueba.* Elaboración
propia.

Completa el recorrido el **10,2 %** de las empresas. Y no se pierden donde cabía esperar:
aproximadamente la mitad de las bajas se deben a **falta de texto de la página web**, un
problema de disponibilidad de datos que ningún modelo resuelve, y la otra mitad a la
exigencia de confianza en el emparejamiento, coherente con el 38,9 % de acierto que se midió
para ese paso en el apartado 4.6.3.

Cada empresa detenida lleva registrado su motivo. Un sistema que se detiene con razón
escrita no es un sistema que falla, sino uno que delimita lo que no sabe.

### La segunda fase de A3, incorporada al recorrido

La segunda fase de la priorización —ajustar la nota una vez se conoce el servicio de
interés— se incorporó al orquestador **en su versión de tabla**, sin entrenar modelo
alguno: emparejado el servicio se conoce su tipo, y el cruce de la nota con el tipo devuelve
la conversión ya medida en el apartado 4.6.2. Sobre la tirada que la incluye, de 3.152
empresas, el reparto de las 1.573 que disponen de texto web es el siguiente:

| Prioridad | Empresas | % |
| --- | --- | --- |
| Alta | 1.035 | 65,8 % |
| Media | 417 | 26,5 % |
| Baja | 121 | 7,7 % |

`[TABLA 51i]` *Reparto de prioridad tras la segunda fase de A3.* Elaboración propia.

La cola de redacción sale ordenada: de las 270 empresas que superan el umbral de
emparejamiento, 198 son de prioridad alta.

**Dos salvedades, y las dos son de encadenamiento.** La primera es que el tipo de servicio
lo **predice A5**, no lo solicita el cliente: la conversión de referencia se midió sobre
peticiones reales, mientras aquí el tipo procede de un emparejamiento que acierta el 38,9 %,
de modo que la prioridad hereda ese error. Por la vía de entrada el problema no se plantea,
porque allí el cliente declara lo que quiere. La segunda es que solo 668 de los casos caen
en una celda del cruce con conversión medida; 828 se resuelven con la media de su tipo y 77
con la conversión global. **La mayoría de las prioridades, por tanto, no descansa en una
cifra propia sino en una agregación**, y así debe interpretarse.

### Lo que este apartado no demuestra

El orquestador acredita que el sistema **funciona encadenado** y permite medir la
propagación del error. No acredita que mejore la conversión comercial: para eso haría falta
contrastar el recorrido completo contra la práctica vigente sobre empresas reales y a lo
largo del tiempo, lo que excede el alcance de este trabajo y se plantea en el capítulo 7.
Las cifras de este apartado son **de proceso, no de resultado comercial**.

Tampoco debe leerse el 10,2 % como una tasa de éxito. Es la proporción de empresas sobre
las que el sistema se considera en condiciones de redactar; las 2.382 restantes no están mal
resueltas, están **explícitamente no resueltas**, que es una situación distinta y
preferible.

---

"""

# ---------------------------------------------------------------------------
# El parrafo del 4.6.6 que daba A0 por no construido
# ---------------------------------------------------------------------------
PARRAFO_VIEJO = """A ellos se añade el **orquestador (A0)**, que no es un agente sino el componente que
encadenaría a los demás. Su ausencia es el único objetivo específico no cumplido y se
trata por separado en el capítulo 5 y en el apartado 7.1."""

PARRAFO_NUEVO = """El **orquestador (A0)** no figura en esta relación porque **sí se construyó**: no es un
agente sino el componente que encadena a los demás, y el apartado anterior recoge su
ejecución y los dos resultados que produjo."""

# ---------------------------------------------------------------------------
# CAP5 · el objetivo 3
# ---------------------------------------------------------------------------
FILA_VIEJA = ("| 3 · Diseñar un sistema**secuencial** de agentes        "
              "| 🔴**No cumplido**   | Ver más abajo                   "
              "                                 |")
FILA_NUEVA = ("| 3 · Diseñar un sistema**secuencial** de agentes        "
              "| ✅**Cumplido**      | Orquestador ejecutado sobre 2.652 "
              "empresas · 4.6.5               |")

OBJ3_NUEVO = """### Objetivo 3 · El sistema secuencial, y lo que su construcción reveló

El objetivo pedía un sistema secuencial en el que cada componente reciba una entrada, la
procese y genere una salida. Durante la mayor parte del desarrollo **no se cumplió**:
existían agentes construidos y evaluados de forma independiente, cada uno sobre sus propios
datos y ninguno recibiendo la salida del anterior. El cotejo sistemático de los objetivos
declarados contra lo construido, ya en fase de redacción, lo puso de manifiesto, y el
componente se construyó a continuación.

La integración no requirió modelado nuevo: los cuatro pasos existían y sus interfaces
resultaron compatibles sin adaptación. Conviene señalar, no obstante, que esa facilidad es
**retrospectiva**. La asignación de esfuerzo había priorizado la evaluación rigurosa de cada
agente sobre su integración y, aunque la decisión era razonable en su momento, estuvo cerca
de dejar sin cumplir el objetivo que da título al trabajo.

**Lo que la integración aportó, y no estaba previsto.** El apartado 4.6.5 lo desarrolla; su
resumen es que el sistema encadenado produjo dos resultados inaccesibles a la evaluación por
componentes, y que apuntan en direcciones opuestas.

*La propagación del error resultó menor de lo temido.* De las 1.280 empresas en que la
clasificación sectorial fue incorrecta, solo en 197 —un 15,4 %— se alteró la puntuación
posterior; sobre el total de 2.652 casos, el 7,4 %. El clasificador acierta el 51,73 %,
cifra modesta en términos absolutos, pero el encadenamiento muestra que la mayor parte de
sus errores son confusiones entre sectores que el componente siguiente trata de igual
manera. **La métrica de un agente informa de cuántas veces se equivoca; solo la cadena
informa de cuánto importa equivocarse.**

*El desajuste de población resultó mayor de lo declarado.* El modelo de puntuación se
entrenó sobre cuentas en que el tamaño de la empresa constaba en el 94 % de los casos y se
aplica sobre una población en que falta en el 62 %. Había aprendido que la ausencia de ese
dato predice una nota concreta —cierto en su población, falso en esta— y su margen sobre la
clase mayoritaria **cae de 12,1 a 6,2 puntos** al evaluarse sobre la población que le
entrega el agente anterior. La limitación estaba declarada desde la evaluación aislada, pero
como nota al pie; la cadena la convierte en una cifra.

**La lección metodológica excede el caso y es, probablemente, la aportación más
transferible del trabajo:** un conjunto de componentes correctamente evaluados no
constituye un sistema correctamente evaluado. Evaluar agentes por separado oculta fallos
que solo se manifiestan cuando cada uno recibe la entrada real del anterior, y el único
modo de encontrarlos es construir la cadena.

**Qué sigue sin estar medido.** El orquestador acredita que el sistema funciona encadenado,
no que mejore la conversión comercial. Esa comparación exige un contraste contra la práctica
vigente a lo largo del tiempo y queda planteada en el capítulo 7.
"""

OBJ3_ANCLA_FIN = "### Objetivo 6 · La utilidad se evaluó, pero con un solo evaluador"

# ---------------------------------------------------------------------------
# CAP5 · 5.3.2 · la limitacion ya no es la que era
#
# La nota interna decia «se elimina de limitaciones». No se elimina: se
# SUSTITUYE, porque queda una limitacion real y distinta. El sistema si se
# encadena, pero el paso generativo no corre en linea, de modo que el
# recorrido no es automatico de extremo a extremo.
# ---------------------------------------------------------------------------
LIMITACION_VIEJA = """**Un sistema multi-agente sin orquestador.** El sistema descompone el problema en módulos
especializados y encadenables, pero **cada agente se ejecuta de forma independiente**. No
se construyó el componente que encadena las salidas, lo que impide medir un fenómeno propio
de estas arquitecturas: la propagación del error a lo largo de la cadena. Se trata en 5.4."""

LIMITACION_NUEVA = """**La cadena se interrumpe en el paso generativo.** El orquestador encadena los agentes
construidos y recorre el sistema completo sobre un ordenador portátil, pero **la redacción
no se ejecuta en línea**: el modelo generativo exige procesamiento gráfico y el recorrido
termina dejando una cola de empresas pendientes de redactar. Es la arquitectura de dos
circuitos del apartado 7.2 y responde a una restricción de recursos deliberada, no a un
fallo de diseño; pero implica que el sistema **no es automático de extremo a extremo** y
que el tiempo de respuesta de la vía de salida depende de cuándo se procese el lote.

**El encadenamiento se midió una sola vez y sobre una sola población.** Los dos resultados
del apartado 4.6.5 —la propagación del error y el desajuste de población— se obtuvieron de
una ejecución sobre la partición de prueba. No se dispone de ejecuciones sucesivas que
permitan estimar su variabilidad, de modo que deben leerse como **órdenes de magnitud
medidos, no como estimaciones con intervalo**."""

# ---------------------------------------------------------------------------
# CAP5 · la nota interna que era la lista de tareas de todo esto
# ---------------------------------------------------------------------------
NOTA_INI = "**1 · El apartado 5.4 declara que el objetivo 3 no se cumplió.**"
NOTA_FIN = "**2 · El 5.6 es el capítulo más singular del trabajo.**"

NOTA_NUEVA = """**1 · El objetivo 3 ya consta cumplido, y la nota anterior queda cerrada.** El orquestador
se construyó el 30-09-2026 y se amplió con la segunda fase de A3 el 01-10-2026. Los tres
cambios que esta nota pedía están hechos: la fila del objetivo 3 en la tabla 56, el
apartado del objetivo 3 y el punto de limitaciones de 5.3.2, que no se eliminó sino que se
sustituyó por la limitación que de verdad queda —que la redacción no corre en línea—.

> 🔧 **PENDIENTE, y es opcional.** El cuarto punto de la nota anterior no se ha aplicado:
> la tabla 54 del apartado 5.1 puede reforzarse con el dato de cuántas empresas completan
> el recorrido (10,2 %) y dónde se detienen las demás. Es un añadido que mejora el
> argumento de la asimetría ejecutar / decidir, no una corrección necesaria. Decídelo tú.

"""


# ---------------------------------------------------------------------------
def paso(texto, viejo, nuevo, etiqueta, notas, hecho_si):
    """Sustituye una vez. Si ya esta hecho lo anota y sigue."""
    if hecho_si in texto:
        notas.append(f"   [ya]  {etiqueta}")
        return texto
    if viejo not in texto:
        notas.append(f"   [!!]  {etiqueta}  <- NO ENCUENTRO EL TEXTO VIEJO")
        return texto
    notas.append(f"   [ok]  {etiqueta}")
    return texto.replace(viejo, nuevo, 1)


def main():
    aplicar = "--aplicar" in sys.argv

    print()
    print("=" * 74)
    print(f"PREP - integrar el orquestador en la memoria  ·  {VERSION_SCRIPT}")
    print("=" * 74)
    print(f"   modo: {'APLICAR' if aplicar else 'ensayo (sin escribir)'}")
    print()

    cambios = {}

    # --------------------------------------------------- CAP4_6
    p46 = MEMORIA / "CAP4_6_resultados.md"
    t = p46.read_text(encoding="utf-8")
    notas = []
    print("CAP4_6_resultados.md")

    t = paso(t, "## 4.6.6 Síntesis de resultados",
             "## 4.6.7 Síntesis de resultados",
             "síntesis: 4.6.6 -> 4.6.7", notas,
             hecho_si="## 4.6.7 Síntesis de resultados")
    t = paso(t, "## 4.6.5 Agentes diseñados y no construidos",
             "## 4.6.6 Agentes diseñados y no construidos",
             "agentes diseñados: 4.6.5 -> 4.6.6", notas,
             hecho_si="## 4.6.6 Agentes diseñados y no construidos")
    t = paso(t, "## 4.6.6 Agentes diseñados y no construidos",
             APARTADO_A0 + "## 4.6.6 Agentes diseñados y no construidos",
             "abierto el apartado 4.6.5 del orquestador", notas,
             hecho_si="## 4.6.5 A0 · El sistema secuencial")
    t = paso(t, PARRAFO_VIEJO, PARRAFO_NUEVO,
             "corregido el párrafo que daba A0 por no construido", notas,
             hecho_si="no figura en esta relación porque **sí se construyó**")

    # El apartado nuevo trae cinco tablas, 51e a 51i, y la 51e ya estaba
    # cogida por la cobertura de criterios de A7. Como el apartado nuevo va
    # ANTES, la que se mueve es la vieja: pasa a 51j y asi el orden de los
    # numeros sigue siendo el orden del documento.
    t = paso(t,
             "`[TABLA 51e]` *Cobertura de los criterios de cualificación en el "
             "mensaje entrante.*",
             "`[TABLA 51j]` *Cobertura de los criterios de cualificación en el "
             "mensaje entrante.*",
             "la tabla 51e de A7 pasa a 51j (colisión con las nuevas)", notas,
             hecho_si="[TABLA 51j]")

    # El bloque de A7 remitia a «el apartado 4.6.5» para los 52 correos, que
    # estan en su MISMO apartado. Al correr la numeracion, ese 4.6.5 pasaba a
    # apuntar al orquestador. Se cambia por una remision sin numero, que no
    # se puede volver a desfasar.
    t = paso(t,
             "Los cincuenta y dos mensajes reales del apartado 4.6.5 permiten",
             "Los cincuenta y dos mensajes reales de este mismo apartado permiten",
             "remisión de A7 a los 52 correos, sin número", notas,
             hecho_si="mensajes reales de este mismo apartado")
    for n in notas:
        print(n)
    cambios[p46] = t

    # --------------------------------------------------- CAP5
    p5 = MEMORIA / "CAP5_discusion.md"
    t = p5.read_text(encoding="utf-8")
    notas = []
    print()
    print("CAP5_discusion.md")

    t = paso(t, FILA_VIEJA, FILA_NUEVA,
             "tabla de objetivos: el 3 pasa a cumplido", notas,
             hecho_si="Orquestador ejecutado sobre 2.652 empresas")

    # el apartado entero, de su titulo al titulo siguiente
    ini = t.find("### Objetivo 3 · El sistema secuencial no se construyó")
    if "### Objetivo 3 · El sistema secuencial, y lo que su construcción reveló" in t:
        notas.append("   [ya]  apartado del objetivo 3 reescrito")
    elif ini == -1:
        notas.append("   [!!]  apartado del objetivo 3  <- NO ENCUENTRO EL TÍTULO")
    else:
        fin = t.find(OBJ3_ANCLA_FIN, ini)
        if fin == -1:
            notas.append("   [!!]  no encuentro dónde acaba el apartado")
        else:
            t = t[:ini] + OBJ3_NUEVO + "\n" + t[fin:]
            notas.append("   [ok]  apartado del objetivo 3 reescrito")

    t = paso(t, LIMITACION_VIEJA, LIMITACION_NUEVA,
             "5.3.2: la limitación «sin orquestador» se sustituye por la real",
             notas, hecho_si="La cadena se interrumpe en el paso generativo")

    # la nota interna, del marcador 1 al marcador 2
    ini = t.find(NOTA_INI)
    if "la nota anterior queda cerrada" in t:
        notas.append("   [ya]  nota interna cerrada")
    elif ini == -1:
        notas.append("   [!!]  nota interna  <- NO ENCUENTRO EL MARCADOR 1")
    else:
        fin = t.find(NOTA_FIN, ini)
        if fin == -1:
            notas.append("   [!!]  no encuentro dónde acaba la nota 1")
        else:
            t = t[:ini] + NOTA_NUEVA + t[fin:]
            notas.append("   [ok]  nota interna cerrada")

    for n in notas:
        print(n)
    cambios[p5] = t

    # --------------------------------------------------- escribir y cotejar
    print()
    if not aplicar:
        print("   Ensayo. Vuelve a lanzarlo con --aplicar para escribir.")
        print()
        return

    for ruta, texto in cambios.items():
        ruta.write_text(texto, encoding="utf-8")

    print("=" * 74)
    print("COTEJO · releyendo los ficheros ya escritos")
    print("=" * 74)
    comprobaciones = [
        (p46, "## 4.6.5 A0 · El sistema secuencial", "existe el apartado 4.6.5"),
        (p46, "## 4.6.6 Agentes diseñados", "agentes diseñados es el 4.6.6"),
        (p46, "## 4.6.7 Síntesis", "la síntesis es el 4.6.7"),
        (p46, "porque **sí se construyó**", "A0 ya no consta como no construido"),
        (p5, "✅**Cumplido**", "el objetivo 3 consta cumplido en la tabla"),
        (p5, "y lo que su construcción reveló", "el apartado del objetivo 3 está reescrito"),
        (p5, "La cadena se interrumpe en el paso generativo",
         "5.3.2 declara la limitación que de verdad queda"),
        (p5, "la nota anterior queda cerrada", "la nota interna está cerrada"),
    ]
    fallos = 0
    for ruta, buscado, etiqueta in comprobaciones:
        ok = buscado in ruta.read_text(encoding="utf-8")
        print(f"   [{'ok' if ok else 'NO'}]  {etiqueta}")
        fallos += 0 if ok else 1

    # lo que NO debe quedar
    for ruta, buscado, etiqueta in [
            (p5, "El sistema secuencial no se construyó",
             "no queda el título antiguo del objetivo 3"),
            (p5, "🔴**No cumplido**   | Ver más abajo",
             "no queda la fila antigua de la tabla"),
            (p5, "Un sistema multi-agente sin orquestador",
             "no queda la limitación antigua de 5.3.2"),
            (p5, "el sistema secuencial SÍ se va a construir",
             "no queda la lista de tareas ya ejecutada")]:
        ok = buscado not in ruta.read_text(encoding="utf-8")
        print(f"   [{'ok' if ok else 'NO'}]  {etiqueta}")
        fallos += 0 if ok else 1

    print()
    if fallos:
        raise SystemExit(f"   {fallos} comprobacion(es) fallan. NO des esto por hecho.")
    print("   Todo cotejado. Ahora toca:")
    print("      python scripts/FIG_numerar_memoria.py --aplicar")
    print()


if __name__ == "__main__":
    main()
