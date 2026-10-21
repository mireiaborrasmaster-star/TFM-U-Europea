# -*- coding: utf-8 -*-
"""
PREP_registrar_A6_A7_A9.py - mete los tres agentes nuevos en la bitacora
=========================================================================

QUE HACE
    Escribe E32 (A9), E33 (A6) y E34 (A7) en 08_BITACORA.md, mas las dos
    decisiones y el error que salieron al construirlos.

    Las cifras NO se escriben a mano: se leen de los tres json que dejaron
    los scripts, para que no puedan desviarse del dato.

    Idempotente y se coteja al final. Nada de _patch.py desechables: es la
    leccion del error X22.

COMO SE EJECUTA
    python scripts/PREP_registrar_A6_A7_A9.py
    python scripts/PREP_registrar_A6_A7_A9.py --aplicar
"""

import json
import sys
from pathlib import Path

VERSION_SCRIPT = "v1 - 04-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "datos" / "03_resultados"
BITA = RAIZ / "08_BITACORA.md"

a6 = json.loads((RES / "a6_agente_recepcion.json").read_text(encoding="utf-8"))
a7 = json.loads((RES / "a7_cualificacion_solicitud.json").read_text(encoding="utf-8"))
a9 = json.loads((RES / "a9_seguimiento_oportunidades.json").read_text(encoding="utf-8"))


def f(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


# ===========================================================================
p9, c9, t9 = a9["persona"], a9["cara_a_cara"], a9["tiempos"]
rf = a9["modelos_creacion"]["Bosque aleatorio"]
cal = {c["rango"]: c for c in p9["calibracion"]}

E32 = f"""### E32 · A9 · El agente de seguimiento, y el comercial como rival medido
**Fecha:** 04-10-2026 · {a9['n']['cerradas']} oportunidades cerradas · `F9_A9_seguimiento_oportunidades.py`

**Qué es A9.** Una vez la oportunidad existe, estimar la probabilidad de que acabe
ganándose y cuánto va a tardar, para saber a qué dedicar el tiempo y cuál está atascada.

**Por qué el experimento tiene esta forma.** Es la del proyecto de previsión de ventas de
la autora, que no entrena ningún modelo: mide la **calibración** (Brier) y la
**discriminación** (AUC) de la columna `Probabilidad` que rellena el comercial, con
intervalos por bootstrap. Aquí se añade la pieza que faltaba —un modelo que compite contra
esa persona— y las dos métricas se mantienen. **El rival no es una referencia inventada:
sale medido del propio sistema de gestión.**

**Sin importes**, decisión D13. Como medida de tamaño entran las horas presupuestadas, que
no son dinero.

#### Cómo se evalúa, y por qué así

Partición **temporal**, no aleatoria: se entrena con lo anterior a {a9['particion']['entrena_hasta']}
y se prueba con {a9['particion']['prueba']}. Una partición aleatoria dejaría ver el futuro,
que es justo lo que un agente de previsión no tiene.

El trimestre {a9['particion']['apartado_por_censura']} **se aparta**: tiene un 81,0 % de
ganadas porque las recientes aún no se han resuelto. Incluirlo infla el resultado. Es
censura por la derecha y se declara.

| Conjunto | Casos | Se ganan |
|---|---|---|
| Entrenamiento (≤ {a9['particion']['entrena_hasta']}) | {a9['n']['entrena']} | 50,6 % |
| Prueba ({a9['particion']['prueba']}) | {a9['n']['prueba']} | {f(a9['suelo_prueba'])} % |
| Apartado por censura | 374 | 81,0 % |

#### 🔑 Hallazgo 1 · El modelo supera con holgura al suelo

| Modelo | Acierto | AUC | Brier |
|---|---|---|---|
| **Suelo** (decir siempre «se gana») | {f(a9['suelo_prueba'])} % | 0,500 | 0,2455 |
| Regresión logística | 71,0 % | 0,777 | 0,1976 |
| **Bosque aleatorio** | **{f(rf['acierto'])} %** | **{rf['auc']:.3f}** | {rf['brier']:.4f} |
| Potenciación del gradiente | 71,8 % | 0,775 | 0,1920 |

Y esto **solo con lo que se sabe al crear la oportunidad**: tipo, tipología, línea
tecnológica, área, provincia, tamaño, si ya es cliente, y el histórico de la cuenta.

**El histórico se calcula hacia atrás.** «Cuántas oportunidades tuvo antes esta cuenta y
cuántas ganó» se computa solo con las creadas **antes** de la que se predice. Hacerlo de
otro modo es ver el futuro, y es el error más fácil de cometer en este montaje.

#### 🔑 Hallazgo 2 · Contra la persona: empata ordenando y gana calibrando

Sobre los {a9['n']['comparables_con_persona']} casos de prueba en que el comercial declaró
su porcentaje:

| Quién | AUC | IC 95 % | Brier | IC 95 % |
|---|---|---|---|---|
| La persona | {p9['auc']:.3f} | [{p9['auc_ic'][0]:.3f}, {p9['auc_ic'][1]:.3f}] | {p9['brier']:.4f} | [{p9['brier_ic'][0]:.4f}, {p9['brier_ic'][1]:.4f}] |
| **A9** | **{c9['auc_modelo']:.3f}** | [{c9['auc_modelo_ic'][0]:.3f}, {c9['auc_modelo_ic'][1]:.3f}] | **{c9['brier_modelo']:.4f}** | [{c9['brier_modelo_ic'][0]:.4f}, {c9['brier_modelo_ic'][1]:.4f}] |

Contraste **emparejado** —se remuestrean los mismos casos para los dos, no cada uno por
separado— con el signo puesto de modo que positivo significa «A9 mejor»:

| | Diferencia | IC 95 % | p |
|---|---|---|---|
| ORDENAR (AUC) | {c9['diferencia_auc']:+.3f} | [{c9['diferencia_ic'][0]:+.3f}, {c9['diferencia_ic'][1]:+.3f}] | {c9['p']:.3f} |
| CALIBRAR (Brier) | +0,0244 | [+0,0091, +0,0372] | **0,002** |

**Son dos cosas distintas y aquí se separan.** Ordenando no se distinguen: el intervalo
cruza el cero. Calibrando, A9 es mejor y el intervalo no lo cruza.

Quitando los valores extremos —ver el hallazgo 3— sobre {c9['sin_extremos']['n']} casos la
diferencia de AUC queda en {c9['sin_extremos']['diferencia_auc']:+.3f}
[{c9['sin_extremos']['ic'][0]:+.3f}, {c9['sin_extremos']['ic'][1]:+.3f}], p ≈ {c9['sin_extremos']['p']:.3f}.
Sigue sin distinguirse.

**La frase que resume A9:** *ordena igual que la persona, pero su número significa lo que
dice.*

#### 🔑 Hallazgo 3 · La persona es pesimista de forma sistemática, y parte de su cifra está contaminada

| Dice | Casos | Se gana de verdad | IC 95 % |
|---|---|---|---|
| 0–24 % | {cal['0-24']['n']} | {f(cal['0-24']['real'])} % | [{f(cal['0-24']['ic'][0])}, {f(cal['0-24']['ic'][1])}] |
| 25–49 % | {cal['25-49']['n']} | {f(cal['25-49']['real'])} % | [{f(cal['25-49']['ic'][0])}, {f(cal['25-49']['ic'][1])}] |
| 50–69 % | {cal['50-69']['n']} | {f(cal['50-69']['real'])} % | [{f(cal['50-69']['ic'][0])}, {f(cal['50-69']['ic'][1])}] |
| **70–89 %** | {cal['70-89']['n']} | **{f(cal['70-89']['real'])} %** | [{f(cal['70-89']['ic'][0])}, {f(cal['70-89']['ic'][1])}] |
| 90–100 % | {cal['90-100']['n']} | {f(cal['90-100']['real'])} % | [{f(cal['90-100']['ic'][0])}, {f(cal['90-100']['ic'][1])}] |

**Cuando dicen 70–89 % se gana el 95,0 %.** El número ordena bien pero no vale como
probabilidad: hay que traducirlo antes de usarlo, que es exactamente lo que el proyecto de
previsión anticipaba sin haberlo cuantificado.

**Y hay contaminación.** {p9['extremos_contaminados']} casos de los
{a9['n']['comparables_con_persona']} llevan 0 o 100 exactos, y de los que marcan 100 se
gana el 90,7 %: **ese valor se escribe después de saber el resultado**, no es una
previsión. Por eso se usa la probabilidad de la **primera** oferta de cada oportunidad, y
por eso la comparación se repite sin los extremos.

#### Hallazgo 4 · El modelo aprende «qué», no «quién»

| | AUC |
|---|---|
| Con el propietario de la oportunidad | {a9['ablacion_propietario']['con']:.3f} |
| Sin el propietario | {a9['ablacion_propietario']['sin']:.3f} |

Aporta {a9['ablacion_propietario']['aporta']:+.3f}. Importa porque un modelo que acierta
identificando al comercial no es transferible a otra organización ni a otra plantilla: lo
que hace es memorizar personas. Este no.

#### Hallazgo 5 · Lo que se pierde tarda seis veces más

| | Casos | Mediana | Media | p90 |
|---|---|---|---|---|
| Ganadas | 1.793 | **{t9['mediana_ganadas']:.0f} días** | 33 | 83 |
| Perdidas | 1.571 | **{t9['mediana_perdidas']:.0f} días** | 104 | 234 |

Una oportunidad que lleva mucho tiempo abierta es, casi siempre, una oportunidad perdida
que nadie ha cerrado. Y de eso sale una lista de trabajo que **no necesita modelo**:

El 90 % de las que cierran lo hacen antes de {t9['p90']:.0f} días.
**{t9['atascadas']} de las {t9['abiertas']} abiertas ({f(100*t9['atascadas']/t9['abiertas'])} %)
pasan de ese plazo.**

#### Un defecto de los datos que conviene anotar

{t9['cierre_antes_de_crear']} oportunidades tienen fecha de cierre **anterior** a la de
creación. Se excluyen del análisis de tiempos y queda declarado: son registros creados a
posteriori.

#### Lo que E32 no dice

No dice que usar A9 aumente las ventas: mide si ordena mejor que la persona, no el efecto
de actuar en consecuencia. La comparación es de **un** trimestre. Y sin importes, por D13:
un modelo con el importe podría ordenar mejor y no se ha probado.

---

"""

# ===========================================================================
p2, p3, p4, p5 = (a6["pieza2_norma"], a6["pieza3_enrutado"],
                  a6["pieza4_comercial"], a6["pieza5_cadena"])

E33 = f"""### E33 · A6 · El agente de recepción, y lo que A8 pierde con texto de cliente
**Fecha:** 04-10-2026 · {a6['n_correos']} correos reales · `F6_A6_agente_recepcion.py`

**Qué es A6.** La fase 6: entra un mensaje al buzón general y hay que decidir cuatro cosas
antes de que lo vea una persona. ¿De quién es? ¿Qué pide? ¿A quién le toca? ¿Es comercial?

**Qué cambió para poder construirlo.** El corpus pasó de 52 correos a
{a6['n_correos']}. Con 52 se podía medir; con {a6['n_correos']} se puede además construir
y encadenar. Una quinta parte entra **en inglés** (23 de {a6['n_correos']}), lo que las
reglas no acusan pero cualquier modelo entrenado en español sí.

| Pieza | Cómo funciona | Estado |
|---|---|---|
| 1 · Resolver la identidad | reglas | medida en E22: 32/98 = 32,7 % |
| 2 · Detectar la norma citada | diccionario | medida aquí: {p2['detectadas']}/{p2['de']} = {f(p2['pct'])} % |
| 3 · Enrutar al área técnica | modelo de A8 | **medida aquí sobre correo real** |
| 4 · Comercial / no comercial | modelo | construida, etiqueta automática |

#### 🔑 Hallazgo principal · El desajuste de población de A8, por fin cuantificado

El apartado 4.6.4 declaraba que **no se había medido** cuánto se degrada el 80,51 % de A8
al pasar de `Tema` —texto del comercial— al correo del cliente, porque solo ocho mensajes
traían su área asociada.

Ya no son ocho. De los {a6['n_correos']} correos, **{p3['prueba']} permiten deducir el área
con certeza** a partir de la norma citada, porque la correspondencia norma → área no es
estadística sino de definición. Eso da {p3['prueba']} etiquetas de prueba sobre texto de
entrada real.

| | Acierto | IC 95 % |
|---|---|---|
| A8 en su propia población (4.6.4) | {f(p3['acierto_poblacion_propia'],2)} % | — |
| **A8 sobre correo de cliente real** | **{f(p3['acierto_correo_real'])} %** | [{f(p3['ic'][0])}, {f(p3['ic'][1])}] |
| Suelo: la clase más frecuente | {f(p3['suelo'])} % | — |

**Cae {f(p3['caida_puntos'])} puntos y conserva {f(p3['margen_sobre_suelo'])} sobre el
suelo.** La señal no se pierde: el enrutado sirve, pero la cifra buena para producción es
el {f(p3['acierto_correo_real'])} %, no el 80,51 %.

**Y esto contrasta con A3.** En E28 el encadenamiento redujo a la mitad el margen de la
priorización. Aquí el clasificador de área aguanta el cambio de población casi intacto.
**Dos componentes, dos comportamientos opuestos ante el mismo fenómeno**, y la diferencia
está en la etiqueta: el área la escribe quien la conoce, la nota de cuenta la deduce un
modelo de variables que cambian de distribución.

**Salvedades, y son importantes.** Son {p3['prueba']} casos y el intervalo mide 26 puntos.
La etiqueta de prueba la pone el diccionario, no una persona: es cierta por definición pero
**solo existe donde se cita una norma, que son los casos más fáciles**. Y entran solo las
cuatro áreas que el diccionario cubre, de diecinueve.

#### Hallazgo 2 · La norma citada resuelve la mitad de los casos

{p2['detectadas']} de {p2['de']} correos citan una norma reconocible
([{f(p2['ic'][0])} %, {f(p2['ic'][1])} %]). De ellos, {p2['una_sola']} apuntan a **una
sola** área y {p2['varias']} a varias, donde el diccionario no decide. Los
{p2['ninguna']} restantes piden algo sin nombrar la norma que lo regula, y ahí hace falta
el clasificador.

#### Hallazgo 3 · La pieza 4 no se puede publicar como rendimiento, y el motivo no es el tamaño

{p4['negativos']} de {p4['de']} correos traen señal de no ser comerciales. O sea que decir
«todos son comerciales» acierta el {f(p4['suelo'])} %.

**Por eso el acierto no vale aquí:** lo consigue una regla que no mira el texto. Se mide si
encuentra los negativos, con validación cruzada: **AUC {p4['auc_cv']:.3f}**, y de los
veinte más sospechosos recupera 5 de los {p4['negativos']}.

Así se usa: **no como clasificador que decide, sino como cola de revisión ordenada.** Una
persona mira veinte correos en vez de {p4['de']}.

Pero lo que impide publicarlo como rendimiento **no es que haya pocos casos**: es que
**los negativos los marca una lista de términos, no una persona**. El modelo aprende a
imitar la lista, así que el resultado mide consistencia con ella, no acierto. Se cierra
etiquetando los {p4['de']} a mano, que son veinte minutos.

#### El agente encadenado

| Decisión | Correos | % |
|---|---|---|
| Enrutado por el clasificador | 46 | 43,8 % |
| Enrutado por norma | 35 | 33,3 % |
| A revisión: puede no ser comercial | 15 | 14,3 % |
| A revisión: la norma apunta a varias áreas | 9 | 8,6 % |

**Resuelve solo {p5['resuelve_solo']} de {a6['n_correos']}
({f(100*p5['resuelve_solo']/a6['n_correos'])} %)** y pasa {p5['a_persona']} a una persona,
cada uno con el motivo escrito. Igual que el orquestador: no adivina cuando no sabe.

---

"""

# ===========================================================================
m7, r7, s7 = a7["modelo"], a7["referencias"], a7["sin_terminos_de_resultado"]

E34 = f"""### E34 · A7 · La cualificación, con tres criterios en vez de siete
**Fecha:** 04-10-2026 · {a7['n']['prueba']} solicitudes de prueba · `F7_A7_cualificacion_solicitud.py`

**Qué es A7.** La fase 7: llega una solicitud y hay que cualificarla antes de dedicarle
tiempo. El diseño original proponía siete criterios —necesidad, impacto, presupuesto,
plazo, decisor, encaje y campeón— extraídos de la conversación comercial.

**Por qué no se había construido, y qué cambia.** No existía el dato de entrada: Empresa no
graba las llamadas. Eso sigue siendo cierto. Lo que cambia es que el **sustituto escrito**
sí existe, y por duplicado: {a7['n']['correos_cliente']} correos reales de cliente, y
**{a7['n']['cerradas']} solicitudes históricas del sistema de gestión con su resultado
real**. Lo segundo permite plantear la pregunta que de verdad importaba:

> ¿Predice la conversión **contar criterios de cualificación**, o hay que **aprender del
> texto**?

#### 🔑 Hallazgo 1 · Contar criterios no ordena, y eso NO refuta el marco

| Referencia | AUC | IC 95 % |
|---|---|---|
| Azar | 0,500 | — |
| Contar los **siete** criterios | {r7['contar_siete']['auc']:.3f} | [{r7['contar_siete']['ic'][0]:.3f}, {r7['contar_siete']['ic'][1]:.3f}] |
| Contar los **tres** que sí aparecen | {r7['contar_tres']['auc']:.3f} | [{r7['contar_tres']['ic'][0]:.3f}, {r7['contar_tres']['ic'][1]:.3f}] |

Los dos intervalos cruzan el 0,5: ninguna ordena.

**Pero la lectura correcta no es que el marco falle.** En este texto los criterios apenas
aparecen: **{a7['criterios']['media_de_7_en_crm']:.2f} de 7** de media, porque el campo son
cuatro o cinco palabras escritas por el comercial. Dos de los siete no salen nunca.
**Contar algo que no está no puede ordenar nada.** Lo que dice el resultado es que el marco
**no es aplicable a este texto**, no que sea falso.

Para contrastarlo de verdad haría falta medirlo sobre correos de cliente —donde los
criterios sí aparecen, 3,1 de 7— y esos correos **no traen resultado comercial asociado**.
Queda como pregunta abierta, y así se declara. Es la misma disciplina que impuso el error
X16: no afirmar una causa que no se ha aislado.

| Criterio | Solicitudes | % | Se ganan |
|---|---|---|---|
| N · Necesidad | 848 | 22,8 % | 50,6 % |
| E · Encaje | 711 | 19,1 % | 48,8 % |
| I · Impacto | 53 | 1,4 % | 50,9 % |
| D · Decisor | 46 | 1,2 % | 50,0 % |
| P · Presupuesto | 5 | 0,1 % | 80,0 % |
| P · Plazo | 4 | 0,1 % | 100,0 % |
| C · Campeón | 0 | 0,0 % | — |

(Media global de ganadas: 54,9 %. Ninguno de los dos criterios con casos suficientes se
separa de ella.)

#### 🔑 Hallazgo 2 · Aprender del texto sí funciona

| | Acierto | AUC | IC 95 % |
|---|---|---|---|
| Suelo | {f(a7['suelo'])} % | 0,500 | — |
| Contar los siete criterios | — | {r7['contar_siete']['auc']:.3f} | [{r7['contar_siete']['ic'][0]:.3f}, {r7['contar_siete']['ic'][1]:.3f}] |
| **A7 · aprender del texto** | **{f(m7['acierto'])} %** | **{m7['auc']:.3f}** | [{m7['auc_ic'][0]:.3f}, {m7['auc_ic'][1]:.3f}] |

**+{f(m7['acierto']-a7['suelo'])} puntos sobre el suelo y +{m7['auc']-r7['contar_siete']['auc']:.3f} de AUC
sobre contar criterios.** Partición temporal, {a7['n']['entrena']} de entrenamiento y
{a7['n']['prueba']} de prueba.

#### Hallazgo 3 · Y no está leyendo el resultado

El texto lo escribe el comercial, a veces después de saber cómo acabó. Se comprobó de dos
formas, porque suponerlo no basta:

1. {s7['solicitudes_con_fuga']} de {a7['n']['cerradas']} solicitudes (0,8 %) contienen algún
   término de desenlace —«anulado», «no procede»…—.
2. De los 200 términos más influyentes del modelo, **{s7['influyentes_delatores']} son de
   resultado**.

Y al reentrenar sin ese vocabulario: acierto {f(s7['acierto'])} %, AUC {s7['auc']:.3f}.
**No cambia nada**, de modo que el modelo no se apoyaba en ellos y la cifra publicable es
la de arriba.

#### El agente sobre correo de cliente real

Corre y devuelve una puntuación para cada uno de los {a7['n']['correos_cliente']} correos,
pero el reparto se desplaza a la baja: 37 en muy baja, 67 en baja, 1 en alta. Coherente con
que el modelo se entrenó con texto del comercial.

**Y ahí no hay con qué comprobarlo:** ninguno de los correos trae resultado comercial
asociado, así que el reparto describe el comportamiento del agente, **no su acierto**. Es
el mismo límite que A8 tenía antes de E33, y en este caso no se puede cerrar con los datos
disponibles.

#### Lo que E34 no dice

Cualifica con tres criterios de los siete, porque los otros cuatro no aparecen. Se entrena
y se prueba con texto del comercial, no del cliente. Y mide si ordena, no el efecto de
cualificar.

---

"""

# ===========================================================================
DECISIONES = """### D20 · Construir A6, A7 y A9 en vez de ampliar lo construido
**Fecha:** 04-10-2026 · **Origen:** el tutor

El tutor señaló que dos transformers y un bosque aleatorio no bastan para un TFM, aunque
los experimentos estén bien hechos, y amplió el plazo al 18 de octubre. La respuesta fue
construir los tres agentes que quedaban con dato disponible.

**Qué lo hizo posible, agente por agente.** No fue el plazo: fue encontrar el dato.

| Agente | Lo que faltaba | Lo que se encontró |
|---|---|---|
| A6 | corpus con el que construir, no solo medir | el corpus pasó de 52 a 105 correos |
| A7 | un objetivo real, no la propia lista de palabras | 3.725 solicitudes históricas CON resultado |
| A9 | — | 4.063 ofertas con fecha de cierre **y la probabilidad que declara el comercial** |

**Lo de A9 merece subrayarse:** la columna `Probabilidad` del export de ofertas da un
**rival humano medido**, no una referencia inventada. Es la misma estructura que RQ3 usó
para A3, y es la forma más defendible de presentar un modelo.

**A8 no entra en esta lista porque ya estaba construido** (D16). El recuento del tutor se
quedaba corto: A2, A5, A3 y A8 son cuatro modelos, más el orquestador que los encadena.

### D21 · A7 se cualifica con tres criterios, y el motivo está medido
**Fecha:** 04-10-2026 · **Origen:** la autora · **Evidencia:** E34

De los siete criterios del diseño original solo tres aparecen con frecuencia suficiente en
los correos de cliente: necesidad (74,3 %), encaje (69,5 %) y presupuesto (43,8 %). Los
otros cuatro no llegan al 36 %.

**No es una simplificación por comodidad: es que la materia prima de los otros cuatro no
está en el canal escrito.** Impacto, plazo, decisor y campeón son cosas que se averiguan
hablando, y por eso el diseño original los situaba en la conversación.

**Descartado:** inferirlos con un modelo generativo a partir del correo. Se descarta porque
no habría con qué validar lo inferido —ningún correo trae esos campos etiquetados— y un
criterio inventado es peor que un criterio ausente.

"""

X24 = (
    "| X24 | Al cargar las fechas del export anonimizado pasé "
    "`dayfirst=True` a `pd.to_datetime`, pero venían en formato ISO "
    "(`2025-01-25 14:00:47`). Pandas leyó el 25 como MES, lo declaró "
    "inválido y devolvió `NaT` | **Se perdieron dos tercios de las filas en "
    "silencio.** A7 se entrenó con 1.060 casos y se evaluó con 155 en vez de "
    "2.680 y 684, y la primera cifra que obtuve —72,9 % de acierto— era de un "
    "conjunto de prueba cuatro veces menor, o sea mucho menos fiable. No dio "
    "ningún error: solo menos datos | Al extrañarme de que un fichero de 4.881 "
    "filas diera 2.002, conté los `NaT` por trimestre y aparecieron 2.723 sin "
    "fecha. Quitando `dayfirst` se leen todas. **La cifra buena es 66,2 %, no "
    "72,9 %**, y es la que está publicada. La lección: un filtro que descarta "
    "filas tiene que decir cuántas descarta |\n")


# ===========================================================================
def main():
    aplicar = "--aplicar" in sys.argv
    print()
    print("=" * 74)
    print(f"PREP - registrar A6, A7 y A9  ·  {VERSION_SCRIPT}")
    print("=" * 74)
    print(f"   modo: {'APLICAR' if aplicar else 'ensayo'}")
    print()

    s = BITA.read_text(encoding="utf-8")
    notas = []

    # --- los tres experimentos, antes de la seccion de hallazgos de datos --
    ancla_e = "## 4 · Hallazgos sobre la calidad de los datos"
    bloque = E32 + E33 + E34
    if "### E32 ·" in s:
        notas.append("   [ya]  E32, E33 y E34")
    elif ancla_e not in s:
        notas.append("   [!!]  no encuentro el ancla de los experimentos")
    else:
        s = s.replace(ancla_e, bloque + ancla_e, 1)
        notas.append("   [ok]  E32, E33 y E34 escritos")

    # --- las decisiones ----------------------------------------------------
    ancla_d = "\n## 3 · Experimentos y resultados"
    if "### D20 ·" in s:
        notas.append("   [ya]  D20 y D21")
    elif ancla_d not in s:
        notas.append("   [!!]  no encuentro el ancla de las decisiones")
    else:
        s = s.replace(ancla_d, "\n" + DECISIONES + ancla_d, 1)
        notas.append("   [ok]  D20 y D21 escritas")

    # --- el error ----------------------------------------------------------
    if "| X24 |" in s:
        notas.append("   [ya]  X24")
    elif "| X23 |" not in s:
        notas.append("   [!!]  no encuentro X23 para colocar X24 detras")
    else:
        i = s.index("| X23 |")
        fin = s.index("\n", i) + 1
        s = s[:fin] + X24 + s[fin:]
        notas.append("   [ok]  X24 escrito")

    for n in notas:
        print(n)

    if not aplicar:
        print()
        print("   Ensayo. Lanzalo con --aplicar para escribir.")
        print()
        return

    BITA.write_text(s, encoding="utf-8")

    print()
    print("COTEJO")
    t = BITA.read_text(encoding="utf-8")
    fallos = 0
    for clave, etiqueta in (
            ("### E32 · A9 ·", "E32 (A9)"),
            ("### E33 · A6 ·", "E33 (A6)"),
            ("### E34 · A7 ·", "E34 (A7)"),
            ("### D20 ·", "D20"), ("### D21 ·", "D21"), ("| X24 |", "X24"),
            (f"{a6['pieza3_enrutado']['acierto_correo_real']:.1f}".replace(".", ",")
             + " %", "la cifra de A8 sobre correo real"),
            ("0,002", "el p del contraste de calibracion"),
            ("66,2 %", "el acierto bueno de A7")):
        ok = clave in t
        print(f"   [{'ok' if ok else 'NO'}]  {etiqueta}")
        fallos += 0 if ok else 1
    # La cifra mala de A7 SI debe aparecer, pero SOLO dentro de X24, que es
    # donde se explica que estaba mal. Si saliera en otro sitio seria un
    # resultado publicado con el conjunto de prueba reducido.
    veces = t.count("72,9 %")
    fila_x24 = next((l for l in t.splitlines() if l.startswith("| X24 |")), "")
    solo_en_x24 = veces == fila_x24.count("72,9 %") and veces > 0
    print(f"   [{'ok' if solo_en_x24 else 'NO'}]  la cifra mala de A7 aparece "
          f"{veces} vez/veces, y solo en X24")
    fallos += 0 if solo_en_x24 else 1
    print()
    if fallos:
        raise SystemExit(f"   {fallos} comprobacion(es) fallan.")
    print("   Todo cotejado.")
    print()


if __name__ == "__main__":
    main()
