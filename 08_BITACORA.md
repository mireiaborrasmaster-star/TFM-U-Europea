# Bitácora del TFM

> Cuaderno de laboratorio. Cada **hipótesis**, cada **resultado** y cada **decisión**,
> con su fecha y su razón. Se añade al final, no se reescribe: si algo resulta estar
> mal, se anota la corrección debajo en lugar de borrar lo anterior.
>
> Sirve para tres cosas: no repetir trabajo, poder justificar cualquier elección meses
> después, y ser el material en bruto de los capítulos 6 a 8 de la memoria.

**Última actualización:** 27-09-2026 (E10 · ablaciones · A2 cerrado)

---

> **Confidencialidad de la información comercial.** La estructura interna de
> áreas y líneas de la organización no se nombra en este cuaderno: se emplean
> los códigos `ARnn`, `LTnn` y `SLnn`, cuya equivalencia se guarda fuera del
> proyecto. Los volúmenes de negocio por unidad se expresan en porcentaje y no
> en número de oportunidades. El campo de texto libre `Tema` se retiró de los
> ficheros de trabajo. Ver `PREP_confidencialidad.py`.


## Índice

1. [Hipótesis y su estado](#1--hipótesis-y-su-estado)
2. [Decisiones tomadas](#2--decisiones-tomadas)
3. [Experimentos y resultados](#3--experimentos-y-resultados)
4. [Hallazgos sobre la calidad de los datos](#4--hallazgos-sobre-la-calidad-de-los-datos)
5. [Errores cometidos y corregidos](#5--errores-cometidos-y-corregidos)
6. [Preguntas abiertas](#6--preguntas-abiertas)
7. [Mediciones pendientes y prompts para retomarlas](#7--mediciones-pendientes-y-prompts-para-retomarlas)

---

## 1 · Hipótesis y su estado

| # | Hipótesis | Estado | Evidencia |
|---|---|---|---|
| **H1** | La taxonomía sectorial de Empresa codifica conocimiento organizacional tácito, no inferible del lenguaje general | ✅ **Confirmada** | E1, E5, E6 |
| **H1b** | La ventaja del modelo supervisado se concentra en los sectores cuyo nombre no es semánticamente transparente | ✅ **Confirmada** | E2 |
| **H2** | Multiplicar los datos mejora sobre todo la cola larga (clases con pocos ejemplos), no el acierto global | ✅ **Confirmada** | E4 |
| **H3** | El texto de la web es la variable dominante | ✅ **Confirmada** | E1, E4, E5 |
| **H4** | La convención de Empresa puede transmitirse a un LLM mediante ejemplos en el prompt | ❌ **Refutada** | E6 |
| **H8** | El resultado de H1 es independiente del LLM concreto que se use | ✅ **Confirmada** | E5, E7 |
| **H5** | Un transformer entrenado supera al modelo lineal, sobre todo en F1-macro | ⚠️ **Parcialmente confirmada**: la ventaja en exactitud es significativa (+2,83, p = 0,002); la de F1-macro **no** (+1,50, p = 0,241). La parte "sobre todo en F1-macro" de la hipótesis no se sostiene | E8, E10, E11 |
| **H11** | La cabeza jerárquica auxiliar mejora el rendimiento | ⚠️ **Indicio no concluyente**: parece empeorar (F1-macro +1,95 al quitarla) pero no alcanza significación (p = 0,070). Sí mejora la robustez a etiquetas ambiguas | E10, E11 |
| **H9** | Existe un techo de rendimiento impuesto por el ruido de etiqueta del CRM | ⏳ Pendiente, con **dos** indicios fuertes | E8, E8b → M3 |
| **H15** | El modelo de fit rinde en las cuentas sin valorar lo mismo que en test | ❌ **Refutada**: desajuste de población en `tamaño`; la estimación realista baja de 48,3 % a 43,4 % | E14 |
| **H16** | Las cuentas de la Comunidad Valenciana convierten más | ✅ **Confirmada**: 15,3 % frente a 7,5 % (p = 3·10⁻⁶²) | E15 |
| **H17** | La valoración humana de atractividad es coherente con el rendimiento geográfico | ❌ **Refutada**: las cuentas que más convierten reciben las notas más bajas | E15 |
| **H18** | Un modelo entrenado sobre conversión real prioriza mejor que la valoración humana | ✅ **Confirmada**: AUC 0,707 frente a 0,638, p = 0,016 | E16 |
| **H19** | El tamaño de la empresa predice el comportamiento comercial | ❌ **Refutada**: predice la *opinión* del comercial (−4,9 al quitarlo) pero no la conversión (0,0) | E14, E16 |
| **H20** | El emparejamiento por términos del catálogo basta para asociar servicios a empresas | ❌ **Refutada**: el 41,8 % de las webs no contiene ninguna señal y el 48,2 % son empates | E17 |
| **H21** | El emparejamiento semántico resuelve lo que el léxico no puede | ✅ **Confirmada**: 0 % de indecisos frente a 41,8 %, y coherencia con el criterio experto | E18 |
| **H22** | La confianza declarada por el sistema predice su acierto | ✅ **Confirmada**: 100 % de acierto en confianza alta frente a 66,7 % en baja | E18 |
| **H23** | Un LLM abierto, con la evidencia acotada y la prohibición explícita de inventar, produce correos anclados en esa evidencia | ✅ **Confirmada, con matiz** | E19: +6,07 puntos sobre el control por permutación (p < 0,0005), pero el margen es modesto |
| **H24** | La generación personalizada sobre un brief de campaña supera al correo genérico que la organización envía hoy | ✅ **Confirmada** | E20: personalización ×3,9 sobre el genérico real (p = 0,001); redundancia 0,486 frente a 1,000 |
| **H25** | Aportar el conocimiento de negocio en un brief escrito basta para que el modelo lo aplique | ⚠️ **Parcialmente refutada** | E20: el brief declaraba «quien los llena con su producto» y aun así el modelo se abstuvo con un envasador de alimentación |
| **H26** | En los datos tabulares de este trabajo los modelos de árboles superan a las redes neuronales | ✅ **Confirmada** | E21: +7,52 puntos de F1-macro y 8,5× menos coste de entrenamiento |
| **H14** | La valoración de la cuenta y el tipo de necesidad aportan información independiente | ✅ **Confirmada**: una cuenta E con ensayo convierte al 61,5 %, una A con I+D al 6,2 % | E13 |
| **H12** | La valoración humana de atractividad predice el comportamiento comercial real | ✅ **Confirmada**, con el matiz de que B supera a A | E12 |
| **H13** | Existe valor comercial sin identificar en las cuentas no valoradas | ✅ **Confirmada**: las E convierten al 11,2 % y las sin nota al 7,2 % | E12 |
| **H10** | Los errores del modelo se concentran en pares de categorías genuinamente ambiguos, no son aleatorios | ✅ **Confirmada** | E8b |
| **H6** | Las filas con jerarquía incoherente en el CRM son más difíciles de clasificar | ✅ **Confirmada** | E4 |
| **H7** | Los modelos de árboles superan a las redes neuronales en los componentes tabulares | ✅ **Confirmada** *(es la misma hipótesis que H26; se formularon por separado por error y se unifican aquí)* | E21 |
| **H27** | El área técnica que atenderá una necesidad es aprendible del histórico de oportunidades | ✅ **Confirmada con holgura**: 78,97 % de acierto y F1-macro 69,98 sobre 13 áreas, frente a un suelo de 27,12 % | E25 |
| **H28** | Proteger el texto comercial obliga a sacrificar rendimiento | ❌ **Refutada**: la representación por huella digital elimina el vocabulario del modelo sin coste medible (80,51 % frente a 78,97 %). Sí lo sacrifica el filtrado de entidades (−11,08) | E26 |

| **H29** | Entregar al modelo la descripción de cada sector mejora la clasificación, sobre todo en las clases con pocos ejemplos | ❌ **Refutada, y en sentido contrario**: −4,03 puntos de acierto y −12,52 de F1-macro. El deterioro se concentra justamente en las clases minoritarias | E30, E31 |
| **H30** | Un modelo estima la probabilidad de cierre de una oportunidad mejor que la persona que hoy la declara | 🟡 **Parcialmente confirmada**: ordenando no se distinguen (+0,034 de AUC, p = 0,22); calibrando el modelo es mejor (+0,0258 de Brier, p = 0,002) | E32 |
| **H31** | Contar los criterios de cualificación del marco de siete predice si la solicitud se convierte | ⬜ **Sin resolver**: no ordena (AUC 0,492) pero en ese texto los criterios apenas aparecen —0,45 de 7—, así que no es una refutación sino una medición imposible | E34 |
| **H32** | El clasificador de área aguanta el paso del texto del comercial al del cliente | ✅ **Confirmada, con un coste pequeño**: 79,5 % frente al 80,51 % de su propia población, conservando 66,7 puntos sobre el suelo | E33 |
| **H33** | Una etiqueta construida con una lista de términos aproxima el juicio humano lo bastante para evaluar con ella | ❌ **Refutada**: de los quince correos que la lista marcaba como no comerciales solo dos lo eran; precisión del 13,3 % | E33, X25 |
| **H34** | Comparar el dominio del remitente con un campo de dominio de correo resuelve la identidad mejor que compararlo con el de la página web | ✅ **Confirmada**: 52,0 % frente a 35,7 %, con 18 casos que solo resuelve la vía nueva frente a 2 (p = 0.0004) | E35 |


---

## 2 · Decisiones tomadas

### D1 · Usar el export completo de 24.079 cuentas, no las 4.009 activas
**Fecha:** 25-09-2026
**Por qué:** el problema principal era la cola larga — 57 subsectores con menos de 10
ejemplos. Con el dataset completo bajan a 29 y la mediana de ejemplos por subsector
pasa de 9 a 37.
**Descartado:** quedarse con las 4.009 por comodidad.

### D2 · No inventar agrupaciones de sectores: usar los tres niveles oficiales de Empresa
**Fecha:** 25-09-2026
**Por qué:** el export reveló que Empresa ya tiene su propia jerarquía de tres niveles
(12 / 41 / 186 clases), y la parte alta es limpia — ninguno de los 39 sectores
detallados cuelga de más de un agrupado. Agrupar a mano habría introducido un criterio
arbitrario imposible de justificar ante un tribunal.
**Principio general:** entrenar fino y agregar después siempre se puede; al revés, no.

### D3 · No reescribir las 5.154 filas con jerarquía incoherente
**Fecha:** 25-09-2026
**Por qué:** la primera versión del script las reasignaba automáticamente al sector
mayoritario, sobrescribiendo silenciosamente el 24 % de las etiquetas. El sector del
CRM está relleno al 100 % y es la etiqueta oficial. Además, un subsector bajo dos
sectores puede ser legítimo ("ENVASES" cuelga con sentido de plástico y de papel).
**Qué se hizo en su lugar:** marcar la fila con una bandera, para poder medir después
si falla más (ver H6).

### D4 · Conservar el conjunto de prueba anterior dentro del nuevo
**Fecha:** 25-09-2026
**Por qué:** las 601 empresas que ya estaban en el test siguen en el test. Así los
resultados nuevos son comparables con los baselines ya medidos en lugar de empezar
de cero.

### D5 · Scrapear todas las webs pendientes, pero en orden de prioridad
**Fecha:** 26-09-2026
**Por qué:** se estudió recortar el trabajo scrapeando solo lo esencial, pero 30 de
los 41 sectores tenían poca cobertura, así que el 87 % entraba igualmente en
"prioridad". El orden (test y validación primero) no sirve para recortar sino para
que, si el proceso se interrumpe, lo hecho sea lo más valioso.

### D6 · Solo modelos abiertos, sin APIs comerciales
**Fecha:** 22-09-2026 · **Origen:** requisito del máster
**Consecuencia:** hay que rehacer la parte que usaba la API de ChatGPT. Los resultados
antiguos se conservan como referencia histórica pero la comparación oficial se hace
contra un LLM abierto.
**Ventaja añadida:** reproducible por el tribunal, sin coste por uso, y sin enviar
datos de clientes a un tercero.

### D7 · Descartar el campo `Probabilidad` del CRM como referencia humana
**Fecha:** 25-09-2026 · **Decisión de la autora**
**Por qué:** los comerciales pueden modificar ese porcentaje **después** de que la
oportunidad se cierre. El campo contiene por tanto información del desenlace: es una
fuga de información del futuro (*target leakage*). Un modelo entrenado con él
parecería excelente y sería inútil en producción.
**Se comprobó:** solo hay 4 fotos semanales archivadas (10 días), insuficiente para
reconstruir el valor previo al cierre.
**Uso alternativo:** en la memoria sirve como argumento — la única estimación existente
no es auditable, lo que justifica construir una trazable.

### D8 · Configuración del vectorizador elegida midiendo, no a ojo
**Fecha:** 26-09-2026
**Por qué:** la configuración inicial tardaba más de 10 minutos por modelo. Se
compararon cinco alternativas (ver E3). Elegida: palabras (1-2 gramas, 150.000
variables) + caracteres (4-5 gramas, 40.000), texto cortado a 2.000 caracteres.

### D9 · El sistema PREVISIÓN DE VENTAS se declara como punto de partida, no como aportación
**Fecha:** 25-09-2026
**Por qué:** ese proyecto ya existía antes del TFM y ya hace análisis de supervivencia
con riesgos competitivos. Presentarlo como aportación propia no sería honesto.
**Cómo se posiciona:** baseline. La aportación del TFM es la capa de aprendizaje
automático encima — predicción por oportunidad individual en lugar de curvas agregadas,
usando el texto, el sector y variables no monetarias.
**Pendiente:** comentarlo con el tutor.

### D10 · Alcance recortado a 5 agentes construidos de 11
**Fecha:** 21-09-2026
**Por qué:** diez agentes no caben en un TFM. Se construyen A2, A3, A6, A7, A8, A9;
se implementan en versión simple A5; se diseñan y justifican A1, A4, A10.

### D11 · Modelo elegido para F2 / A2: distinto según el uso
**Fecha:** 27-09-2026 · **Evidencia:** E4, E8

**La diferencia es pequeña pero ESTADÍSTICAMENTE SIGNIFICATIVA** (confirmado 27-09-2026,
ver E9). La redacción inicial de esta decisión decía "puede no ser significativa"; el test
lo desmintió y se corrige aquí.

| | Aciertos (41 clases) | F1-macro | Aciertos (12 clases) | F1-macro (12) |
|---|---|---|---|---|
| Regresión logística | 48,91 | **41,89** | 56,73 | 53,79 |
| Transformer | **50,98** | 41,43 | **59,41** | **56,46** |

**Resultado del test (E9):** sector p = 0,026 · agrupado p = 0,005. La ventaja del
transformer es real en ambos niveles.

**Esto NO cambia la decisión de producción, pero sí su justificación.** Ya no se argumenta
que la diferencia podría ser ruido, sino que **su magnitud no compensa el coste operativo**
en el nivel de 41 clases. En el nivel agrupado, donde la ventaja es mayor y más clara
(p = 0,005), el transformer sí compensa.

**DECISIÓN — en la memoria:** se reportan **los dos**. La comparación es la aportación, no
el ganador. El transformer se presenta como modelo final del capítulo por ser el mejor en
exactitud y por ganar con claridad en el nivel agrupado (+2,7 en ambas métricas).

**DECISIÓN — en producción:**

| Nivel | Modelo | Por qué |
|---|---|---|
| Sector (41 clases) | **Regresión logística** | 2 puntos de exactitud no compensan depender de una GPU para cada reentrenamiento |
| Sector agrupado (12) | **Transformer** | Gana en las dos métricas (+2,7 / +2,7) y es el único nivel fiable de verdad (59 %) |

**Criterios de la decisión de producción, más allá de la exactitud:**

| Criterio | Lineal | Transformer |
|---|---|---|
| Entrenar | 2 min en CPU | 20 min con GPU |
| Ejecutar | Cualquier equipo | Requiere hardware |
| Reentrenar al entrar cuentas nuevas | Trivial | Requiere GPU |
| Explicabilidad | Se ven las palabras que pesan | Caja negra |
| Robustez a etiquetas ambiguas | −6,93 puntos | **−1,26 puntos** |

**Alternativa descartada:** quedarse solo con el transformer por ser el mejor número. Se
descarta porque el coste de mantenimiento recae sobre Empresa y la ganancia es marginal en
el nivel de 41 clases.

**Matiz a favor del transformer:** su robustez ante etiquetas ambiguas (pierde 1,3 puntos
donde el lineal pierde 7) es una ventaja operativa real. En producción, las cuentas nuevas
y atípicas son justamente las difíciles, y ahí el promedio engaña.


### D12 · A3 se divide en dos fases encadenadas
**Fecha:** 27-09-2026 · **Origen:** propuesta de la autora · **Evidencia:** E12, E13

**Diseño inicial descartado:** un único modelo que predijera la atractividad usando todo
lo disponible, incluido el historial de oportunidades. Se descarta por **circularidad**:
quien asignó las notas conocía ese historial, así que el modelo aprendería a reproducir
información que en el momento real de decidir no existe.

**Diseño adoptado — dos fases, dos momentos, dos conjuntos de información:**

| | Cuándo | Qué se conoce | Para qué | Datos |
|---|---|---|---|---|
| **Fase 1 · Fit** | Antes de cualquier contacto | Sector, tamaño, provincia, país, asociado, texto web | Priorizar a quién dirigirse | Entrenar con 3.013 valoradas · aplicar a **21.066 sin valorar** |
| **Fase 2 · Ajuste** | Cuando el cliente pide algo | + tipo de servicio y texto del `Tema` | Decidir cuánto esfuerzo invertir | Entrenar con 2.096 · aplicar a 2.776 |

**Por qué no hay circularidad en la fase 2:** el `Tema` está disponible en el momento real
de la decisión, porque el cliente ya ha escrito. Es información que llega después, no
información del futuro.

**Encadenamiento:** la salida de la fase 1 es una variable de entrada de la fase 2. Esto
materializa el objetivo específico 3 (sistema secuencial donde cada componente recibe una
entrada, procesa y genera una salida) dentro del propio agente A3.

**Correspondencia con el mapa:** fase 1 es F3; fase 2 opera entre F7 y F8.

**Decisión adicional sobre la variable objetivo:** se modela como **clasificación
multiclase**, no como regresión ordinal, porque E12 demostró que la escala no es
estrictamente ordinal (B supera a A en todos los indicadores).


### D13 · Exclusión de toda variable monetaria del trabajo
**Fecha:** 27-09-2026 · **Decisión de la autora**

**Qué se excluye:** importes de ofertas y oportunidades, ingresos medios por segmento,
tarifas y cualquier cifra económica, tanto en los análisis como en la documentación.

**Motivo:** son información comercial sensible de Empresa. Los márgenes, tarifas e ingresos
por segmento constituyen inteligencia competitiva cuya difusión podría perjudicar a la
organización.

**Alcance de la decisión:**

| | |
|---|---|
| Eliminado de la documentación | Tablas de ingreso medio por nota de atractividad |
| Excluido de los modelos | La variable `Importe detallado total` no se usa como objetivo ni como predictor |
| Sustituido por | **Tasas de conversión** (porcentajes), que miden lo mismo sin revelar magnitudes |

**Impacto en los resultados: ninguno.** Se verificó que las conclusiones de E12, E13 y E16
se sostienen íntegramente sobre tasas de conversión:

- E12 (la atractividad predice el comportamiento) se demuestra con el % de cuentas que
  generan oportunidad, sin necesidad de importes
- E13 (lo que se pide pesa más que quién lo pide) se mide sobre tasas de conversión
- E16 (el modelo prioriza mejor que el criterio humano) usa como objetivo *"¿generará
  oportunidad?"*, variable binaria sin componente monetario

**Consecuencia para trabajo futuro:** queda fuera del alcance cualquier modelo de
predicción de importe o de valor esperado de cartera. Si se retomara, requeriría una
decisión expresa de la organización sobre el tratamiento de esa información.


---

### D14 · A5 pasa a modo campaña: el agente deja de elegir el servicio

**Fecha:** 28-09-2026
**Documentos:** `12_CAMPANAS.md` · `scripts/F5_A5_E20_campana.py`

**Qué se decide.** El agente A5 deja de elegir qué servicio proponer. El tema, el
disparador, los datos técnicos y lo que se ofrece vienen fijados en un **brief de
campaña** que escribe una persona. El modelo solo conecta ese mensaje con la actividad
de cada empresa.

**Por qué. Tres razones, y las tres tienen respaldo.**

*1 · La parte que se elimina es la que falla.* E19 mostró que el eslabón débil no es la
redacción sino el emparejamiento: a un fabricante de aisladores cerámicos se le propuso
caracterización de materiales de envase. Ningún modelo de generación compensa eso.

*2 · Esa decisión no necesita automatizarse.* En la práctica comercial de Empresa una
campaña la decide una persona. Lo que no escala no es elegir el tema, sino escribir
cientos de correos que lo conecten con cada empresa. Automatizar la parte equivocada es
un error de diseño, no de implementación.

*3 · Resuelve de raíz el problema de las afirmaciones inventadas.* En la versión
anterior el propio ejemplo del prompt contenía una afirmación de mercado que no estaba
en ninguna evidencia, y el modelo aprendía de ahí que inventar contexto es aceptable. Con
el brief, los datos técnicos y las fechas los pone una persona, y lo único que el modelo
aporta —el enlace con la actividad— sí se verifica contra la web.

**Origen de la decisión.** La autora aportó un correo real de campaña lanzado por el
departamento de marketing de Empresa (PPWR, septiembre de 2026) y planteó que lo útil para
su organización es generar el correo de un servicio concreto contextualizado a la
actividad de la empresa, no que el sistema elija el servicio.

El análisis de ese correo identificó cuatro elementos que ningún modelo puede deducir
leyendo una web, y que pasan a ser campos obligatorios del brief:

| Elemento | Por qué no es inferible |
|---|---|
| El disparador | Un hecho del mundo (la guía de la Comisión Europea) |
| Los hitos | Fechas exigibles concretas |
| Los puntos técnicos con nombre | PFAS, DoC, EN 13430 |
| Qué se entrega | Un informe, un dosier: decisión de la casa |

**Es el mismo principio que el trabajo defiende desde A2:** el conocimiento
organizacional no se infiere de los datos, se aporta. Aquí se aplica al diseño del
agente y no solo a sus etiquetas.

**Qué se conserva.** A5 en modo selección de servicio (`F5_A5_E19_generar_correos.py`) se mantiene como
variante evaluada: sus resultados son E19 y no se descartan. El emparejamiento semántico
de E18 conserva su función, pero cambia de papel: ya no elige el servicio, sino que sirve
para decidir **qué empresas entran en una campaña**. Pasa de selector a filtro de
pertinencia.

**Qué añade en cuanto a evaluación.** El correo genérico que Empresa envía hoy —el mismo
texto para todas las empresas— pasa a ser la **línea base**, y es exigente porque lo ha
escrito una persona. La pregunta del experimento deja de ser «¿escribe bien el modelo?» y
pasa a ser la que le importa al negocio:

> ¿Personalizar automáticamente aporta algo frente a mandar el mismo correo a todos?

Con dos métricas que no miden lo mismo:

| Métrica | Qué mide | Referencia |
|---|---|---|
| **Personalización** | Qué parte del correo viene de la web de *esa* empresa y no del brief | El correo genérico real: **1,1 %** (medido, no supuesto) |
| **Redundancia** | Cuánto se parecen los correos entre sí | El genérico: 1,000 por definición |

**Abstención.** El brief declara a quién *no* le aplica la campaña. Si la empresa no
encaja, el agente responde `NO APLICA` en lugar de forzar el encaje. Es la traslación de
la política de confianza de E18: reconocer cuándo no se debe actuar forma parte del
trabajo del agente. Y tiene coste asimétrico —una abstención equivocada es un cliente
perdido—, así que se evalúa a mano.

---


### D15 · Proteger la información comercial en tres capas, no en una
**Fecha:** 30-09-2026
**Por qué:** la organización no quiere que se conozca con exactitud su cartera de
servicios ni dónde se concentra su negocio. Sacar el texto de la carpeta de trabajo
no bastaba: el modelo entrenado guarda el vocabulario dentro (X18), y la memoria
publicaría ese vocabulario en cuanto explicara el modelo. Se adoptan tres medidas
independientes:

1. El texto de origen (`Tema`) vive fuera del proyecto, en la carpeta privada
2. La estructura interna —área, línea y sublínea— se publica codificada `ARnn`,
   `LTnn`, `SLnn`, y los volúmenes en porcentaje, nunca en recuento absoluto
3. El modelo se entrena con representación por huella digital, sin vocabulario, y
   la memoria no incluye ninguna tabla de términos influyentes

**Descartado:** filtrar las entidades nombradas del texto, que cuesta 11,08 puntos
de acierto (E26); y confiar solo en la carpeta privada, que no protege el modelo.

**Límite declarado:** la huella digital es ocultación, no cifrado.

### D16 · Incorporar A8 a los agentes construidos
**Fecha:** 30-09-2026
**Por qué:** el enrutado por área se midió al responder una pregunta sobre
confidencialidad y resultó ser la tarea más aprendible del trabajo (E25). Estaba
previsto como agente solo diseñado, y dejarlo fuera del capítulo de resultados
habría ocultado el contraste con mayor margen sobre el suelo de toda la memoria.
**Descartado:** dejarlo en el cuaderno y citarlo como línea abierta. Se descarta
porque el resultado existe, está validado y su limitación está declarada.
**Consecuencia:** el apartado 4.6 pasa de tres agentes construidos a cuatro.



### D17 · Construir el orquestador y cerrar el objetivo 3
**Fecha:** 30-09-2026
**Por qué:** el objetivo específico 3 pedía un sistema secuencial y era el único sin
cumplir; además da título al trabajo. No requería modelado nuevo: los cuatro pasos
existían y sus interfaces encajaban.
**Descartado:** dejarlo como línea futura y declarar el objetivo incumplido. Se descarta
porque el coste era medio día y el hueco era el que un tribunal iría a buscar primero.
**Lo que no se esperaba:** el orquestador no solo cerró el objetivo, sino que produjo dos
resultados propios (E28) y destapó que la evaluación aislada de A3 era optimista.



### D18 · La resolución de identidad va por tres vías ordenadas, no por una
**Fecha:** 01-10-2026 · **Origen:** corrección de la autora

Durante todo el desarrollo se había usado la palabra «dominio» para dos cosas distintas, y
eso ocultaba que hay **dos búsquedas diferentes**, no una:

| Vía | Qué compara | ¿Necesita que la cuenta tenga web? |
|---|---|---|
| 1 · dirección exacta | el correo completo con los contactos | no |
| 2 · dominio en contactos | el `@dominio` con el `@dominio` de otros contactos | **no** |
| 3 · dominio en cuentas | el `@dominio` con el campo *Sitio web* de las cuentas | **sí** |

**Consecuencia sobre una cifra publicada.** El «techo estructural del 70 %» que se venía
reportando es el techo de la **vía 3**, no el del sistema. La vía 2 opera sobre la tabla de
contactos, donde la dirección de correo existe por definición, y no está sujeta a ese
límite. Ver X19.

**Por qué se conserva la vía 3 pese a ser la más débil.** Resuelve un caso que las otras no
cubren: las empresas registradas **de las que nunca ha escrito nadie**. Ahí no existe
ningún contacto con ese dominio, y la única señal disponible es la web de la cuenta. Es
típicamente el caso de una empresa incorporada en una campaña de salida que no respondió.
Cuesta una comparación de cadenas y recupera el 29,2 % de esos casos.

**Qué se puede medir y qué no.** Las vías 1 y 2 operan sobre datos de contacto personales
que no se exportaron (minimización, ver 4.2.4). Se diseñan y se especifican, pero **no se
pueden cuantificar**, y así se declara. Solo la vía 3 tiene cifra.

### D19 · El sistema no crea cuentas por su cuenta
**Fecha:** 01-10-2026 · **Origen:** propuesta de la autora · **Evidencia:** E22

Cuando la resolución de identidad falla en las tres vías, el mensaje **no genera una cuenta
nueva**: queda en revisión manual. Una persona decide si es un cliente potencial y, solo
tras ese visto bueno, se enriquece la cuenta con A2 y A3 fase 1.

**Por qué, y está medido.** E22 estableció que la clase «esto no es una solicitud
comercial» está prácticamente vacía en el corpus disponible —nueve casos de cincuenta y
dos, y seis de ellos por un término ambiguo— y que la causa no es el tamaño de la muestra
sino su procedencia. Un sistema que no distingue un cliente potencial de un proveedor, un
currículum o una invitación a un congreso no puede dar de alta cuentas sin supervisión:
degradaría el sistema de gestión, que es el activo sobre el que se sostiene todo lo demás.

**Descartado:** crear la cuenta automáticamente y marcarla para revisión posterior. Se
descarta porque el coste de un registro erróneo es persistente y el de esperar a una
persona es de horas.

**Cuándo se revisaría:** cuando pueda entrenarse esa clase, lo que exige exportar del buzón
**sin filtrar previamente**.


### D20 · Construir A6, A7 y A9 en vez de ampliar lo construido
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


### D22 · El sistema se entrega ejecutable sin los datos reservados
**Fecha:** 06-10-2026 · **Origen:** el tutor pide probarlo en su equipo

El tutor solicitó ejecutar el sistema en su ordenador. Eso obliga a resolver una tensión
que hasta ahora no se había planteado: **la copia que se entrega no puede llevar ni la
llave de reidentificación ni el texto comercial**, pero sin ellos dos agentes no arrancan.

**Qué se comprobó, quitando la carpeta privada de verdad y ejecutando:**

| Componente | Sin los datos reservados |
|---|---|
| A2, A3, A5, A9, A0 | funcionan: no la tocan |
| A6 | **no funcionaba**; corregido, ver abajo |
| A7, A8 y la pieza 3 de A6 | no funcionan: se entrenan con el campo `Tema` |

**A6 se arregló quitándole la dependencia.** Solo usaba el mapeo privado para traducir el
nombre del área a su código, y el dato ya viene codificado. Se sustituyó por los cuatro
códigos que el diccionario de normas necesita, que no significan nada para quien no tenga
el mapeo.

#### 🔑 Para A7 y A8 se entrega la matriz troceada, no el texto

La salida sale de **E26**: la representación por huella digital rinde igual que TF-IDF y
**no almacena ningún término**. Así que se entrega el texto ya convertido a matriz, con sus
etiquetas en código, y quien lo reciba entrena los dos clasificadores sin ver una sola
palabra.

| | Con la matriz troceada | Publicado |
|---|---|---|
| A8 · enrutado al área | 80,16 % | 80,51 % |
| A7 · cualificación | 65,14 % | 66,20 % |

Reproducen. La diferencia de A7 es esperable —su modelo original usa TF-IDF y aquí va
troceado—; la de A8 es menor porque **ese modelo ya usaba troceo**, por la decisión de
protección que E26 justificó.

**Qué protege y qué no, dicho con precisión.** Protege de **leer** el texto: no viaja
ningún término ni hay diccionario que deshacer. **No es cifrado:** quien sospeche que una
palabra concreta está en el corpus puede trocearla y comprobar si esa posición tiene peso.
Protege frente a la lectura, no frente a la confirmación de una sospecha. Para que un
tribunal ejecute el sistema es proporcionado; para publicarlo en abierto habría que
pensarlo más.

#### Comprobado ejecutando, no suponiendo

Se borró la carpeta privada de la copia y se lanzó todo:

| | |
|---|---|
| A3 · priorizar | ✅ |
| A6 · recepción | ✅ |
| A6 · identidad por dos vías | ✅ |
| A9 · seguimiento | ✅ |
| **A0 · orquestador** | ✅ **código 0, recorre la cadena entera** |
| `VERIFICAR_A7_A8_sin_texto` | ✅ las dos cifras reproducen |

**El sistema completo se ejecuta sin la llave de reidentificación ni el texto comercial.**

**Descartado:** entregar el texto con los nombres sustituidos. Se descarta porque lo que
Empresa pide proteger no son los nombres sino **el contenido**: qué servicios se piden y cómo
se describen.

#### Lo que faltaba y nadie había echado en falta

**No existía `requirements.txt`.** Quien recibiera la copia tendría que adivinar las
bibliotecas y sus versiones. Se añade, con el aviso de que `torch` con tarjeta gráfica se
instala aparte y antes del resto.

Y se documenta lo que el equipo receptor necesita: unos **17 GB** de descarga de modelos
—`xlm-roberta-base`, `multilingual-e5-small` y `Qwen2.5-7B-Instruct`— de los cuales solo
**dos componentes de nueve exigen tarjeta gráfica**. Los otros siete corren en cualquier
portátil.


### D23 · A7 deja de ser un agente y pasa a ser una variable de A9
**Fecha:** 06-10-2026 · **Origen:** la autora · **Evidencia:** E36

**Qué se decide.** El texto de la solicitud deja de constituir la fase F7 y pasa a ser una
variable del agente de seguimiento. No se retira: se reubica.

**Por qué.** Donde estaba no podía validarse —ningún correo de cliente trae su resultado
comercial— y sobre ese texto el modelo no discrimina. Donde se le pone sí hay resultado
real, y el texto aporta
**+0.023** [+0.007, +0.039], p = 0.006.

| A9 | AUC | Acierto |
|---|---|---|
| Sin el texto | 0,788 | 72,4 % |
| **Con el texto** | **0,811** | **73,9 %** |

**Qué se gana y qué se pierde.** Se gana una validación posible y +0.023 de
AUC. Se pierde la fase F7 como agente autónomo —de siete construidos se pasa a seis—, pero
la cualificación que la vía de entrada necesita de verdad, distinguir lo comercial de lo que
no lo es, ya la resuelve la cuarta pieza de A6 con AUC 0,919.

**Cómo defenderlo.** «Se construyó, se evaluó, se midió que no aportaba donde estaba y se
reubicó donde sí aporta» es mejor trabajo que mantener un agente que no se usa. El
resultado negativo sobre el marco de los siete criterios conserva su valor con
independencia de dónde acabe el componente.

**Descartado:** borrarlo sin más, como la autora planteaba inicialmente. Se descarta porque
E36 midió que el texto tiene señal propia, y tirarla habría sido perder rendimiento sin
motivo.


### D24 · Los agentes se renumeran: A6 absorbe la cualificación, A8 pasa a A7 y A9 a A8
**Fecha:** 07-10-2026 · **Origen:** la autora · **Consecuencia de:** D23

**Qué se decide.** D23 retiró la cualificación como agente. Hasta hoy la numeración
conservaba el hueco: había un A6, un A7 que ya no existía, un A8 y un A9. Se renumera para
que los agentes salgan en orden y la cuenta cuadre.

| Antes | Ahora | Función |
|---|---|---|
| A6 | **A6** | Recepción y cualificación de entradas |
| A7 | *(absorbido en A6)* | Cualificación de la solicitud |
| A8 | **A7** | Enrutado al área técnica y briefing de traspaso |
| A9 | **A8** | Seguimiento de oportunidades |
| A10 | **A9** | Aprendizaje continuo (en diseño) |

**Por qué cuadra ahora y antes no.** El capítulo de resultados decía «de los once agentes,
seis construidos, uno sin automatizar y tres sin construir»: eso suma diez, no once. El
sobrante era precisamente el agente que D23 había retirado. Ahora son **once fases del
proceso y diez agentes**, porque A6 cubre dos fases.

**Qué NO se renumera, y por qué.**
- **Las once fases del proceso.** El proceso comercial sigue teniendo once fases; lo que
  cambia es que una de ellas no tiene agente propio. Renumerar las fases habría obligado a
  tocar el capítulo 2, el 3.3 y la figura de arquitectura, con ganancia cero.
- **Los nombres de los ficheros de código.** `F8_A8_briefing_traspaso.py` implementa lo que
  la memoria llama A7, y `F9_A9_seguimiento_oportunidades.py` lo que llama A8. Renombrar
  sesenta ficheros a once días de la entrega es más riesgo que beneficio. La
  correspondencia está en 4.6.0, en el ESTADO y en el LEEME de la entrega.
- **Esta bitácora.** Es un registro cronológico: las entradas anteriores al 07-10 usan los
  nombres vigentes en su fecha, y cambiarlas sería falsificar el registro. Esta tabla es la
  clave de lectura.

**Qué se reordena en la memoria.** Los apartados de 4.6 pasan a seguir el orden de los
agentes: 4.6.4 el orquestador, 4.6.5 A6, 4.6.6 A7, 4.6.7 A8 y 4.6.8 el texto de la
solicitud. Al reordenar hubo que corregir tres referencias relativas —«el apartado
siguiente» pasó a ser «el anterior»— y el 4.6.9 apareció con texto de cuando A6 y el
seguimiento no estaban construidos: decía «A6 produjo resultados pese a no construirse» y
«A9 no se construyó por alcance». Las dos afirmaciones eran falsas desde el 5 y el 6 de
octubre. **Reordenar un documento sirve también para encontrar lo que se quedó atrás.**

**Descartado:** dejar el hueco en A7 y explicarlo con una nota. Se descarta porque un
tribunal que lea el índice de 4.6 ve primero la numeración y después la nota.


### D25 · Qué hace el sistema con un correo que no sabe resolver
**Fecha:** 07-10-2026 · **Origen:** la autora · **Alcance:** diseño de explotación, no construido

**Qué se decide.** Tres destinos para un mensaje entrante, y ninguno es «intentarlo igual»:

| Destino | Cuándo | Observado sobre 105 |
|---|---|---|
| Buzón genérico, sin gestionar | no es una solicitud de trabajo | 14 |
| Circuito completo: ficha + alta de cuenta y oportunidad + probabilidad de cierre | solicitud, cuenta conocida, área inequívoca | 45 |
| Reenvío a la responsable con todo lo extraído | cualquier otro caso | el resto |

**Por qué.** Lo que no es una solicitud no hay que gestionarlo, solo encaminarlo. Y cuando
el sistema no puede decidir, lo útil no es que adivine sino que **entregue el caso con el
trabajo ya hecho**: dominio, cuenta si consta, normas citadas, tipo propuesto con su tramo
de confianza, y el motivo por el que se detuvo. Es el mismo principio de A5 al abstenerse y
de A6 al derivar a revisión.

**Lo que esto corrige.** Durante la conversación se afirmó que A8 no puede intervenir al
llegar el correo porque exige la oportunidad creada. **Es incorrecto si el sistema la crea
él mismo**: A8 se evaluó justamente sobre lo que se conoce al registrar. La restricción real
es otra, y no está medida: una cuenta nueva llega sin historial, y varias variables de A8
resumen ese historial. Anotado como medición pendiente en 7.4.

**Qué queda fuera, y se dice.** El sistema de gestión es un producto de Microsoft y la
escritura automática de cuentas y oportunidades depende de permisos y licencias del
departamento de sistemas. No se implementa ni se simula. Lo que sí se fija son dos
condiciones: la probabilidad del modelo va en **campo propio etiquetado**, sin sobrescribir
la de nadie, y **cada registro creado por el sistema debe poder identificarse**, o la
evaluación posterior del efecto real es imposible.

**Descartado:** que el sistema diera de alta cuentas nuevas por su cuenta. Lo impide D19, y
es el motivo de que la automatización completa alcance a
45 de 105 y no a los
80 que el agente sabría enrutar.

**No se construye.** Decisión de la autora: esta parte es línea futura, se documenta en
7.2c y no se implementa dentro del plazo del trabajo.


### D26 · El clasificador de área se construye y se documenta en A6, no en A7
**Fecha:** 09-10-2026 · **Origen:** la autora · **Alcance:** orden del capítulo 4.6; ninguna medición

**La pregunta que lo provoca.** «Si en A6 ya se establece el área, ¿para qué lo repite A7?»
Leída sobre la memoria, la pregunta estaba bien hecha: el capítulo daba la impresión de que
dos agentes hacían el mismo trabajo.

**Qué se comprobó antes de decidir.** No hay trabajo repetido. **El área se decide una sola
vez**, en el triaje de A6, y viaja con el mensaje hasta la ficha. Lo que estaba repetido era
la **explicación**: el lector encontraba primero el uso —en A6— y después la construcción
—en A7—, y de ahí la impresión de duplicidad.

**Por qué estaba así.** El clasificador se construyó antes que A6, al responder una pregunta
sobre confidencialidad de los datos comerciales, y A6 llegó después y lo reutilizó. La
memoria había heredado **el orden en que se hicieron las cosas en lugar del orden en que se
entienden**.

**Qué se mueve.** Los cuatro apartados que construyen y miden el clasificador —los datos ya
etiquetados, el 80,51 % sobre su suelo, la protección por huella digital y el techo
declarado— pasan de 4.6.6 a 4.6.5, justo **antes** de la medición del desajuste de
población, que es donde cobran sentido: el modelo se entrena sobre el asunto que escribe un
comercial y acto seguido se mide sobre el correo que escribe un cliente.

**Qué NO se mueve, y por qué.** Los bloques de «Instrucción de construcción». Llevan fecha y
son el registro de cómo se dirigió cada agente: moverlos falsearía ese registro. El de A7 se
queda en A7 con una nota de dónde está ahora su resultado.

**Qué no cambia.** **Ni una cifra.** El 80,51 %, el 79,5 % sobre correo real y los 53,4
puntos de margen son los mismos; cambia dónde están escritos, y ninguna figura se rehízo. Sí
se corrigieron seis referencias internas de 4.6 y tres de los capítulos 4.2 y 5 que
apuntaban a «el apartado 4.6.6» y ahora apuntan a 4.6.5 o al propio apartado.

**Descartado:** dejarlo donde estaba y añadir una nota que aclarase que no hay duplicación.
Se descarta porque el lector que concluye que hay trabajo repetido **lo concluye antes de
llegar a la nota**.


### D27 · La ficha de traspaso es un documento para leer, y lleva lo que la organización ya sabe de la empresa
**Fecha:** 09-10-2026 · **Origen:** la autora · **Consecuencia de:** D13 y D19

**Qué se decide.** Tres cosas sobre la misma pieza:

| | Qué se fija |
|---|---|
| 1 | La ficha se redacta **para que una persona la lea**, no solo para alimentar el sistema de gestión |
| 2 | Lleva el **historial de la cuenta**: oportunidades previas, ganadas, cuánto hace de la última, área habitual y ofertas previas |
| 3 | El **alta de la cuenta** es precondición de la oportunidad, y la decide una persona |

**Por qué el historial.** «¿A esta empresa ya le hemos hecho algo?» es la primera pregunta
que se hace quien recibe un caso, y la respuesta **estaba en el sistema de gestión desde el
principio, sin necesidad de ningún modelo**. No incorporarla era dejar fuera de la ficha lo
único que no hay que inferir.

**Sin un solo importe**, en aplicación de D13: se cuentan casos y se miran fechas, nunca
cuánto se facturó. Esto excluye deliberadamente la variable que un sistema comercial usaría
en primer lugar.

**Por qué el alta es precondición.** Una oportunidad cuelga siempre de una cuenta. Si la
empresa consta, el registro puede crearse solo; si no consta, **el sistema propone el alta y
no la ejecuta**, porque D19 reserva a una persona la creación de cuentas. Crear cuentas a
partir de un correo introduciría duplicados en el activo que este trabajo trata de ordenar.

**Cómo debería llegarle al responsable comercial, que es diseño y no construcción.** Un
correo al responsable del área con **la ficha dentro** y **el enlace a la oportunidad ya
creada**, de modo que la decisión se tome sin abrir nada más. Queda recogido en 7.5 y no se
implementa: exige permisos de escritura en el sistema de gestión y envío desde el buzón
corporativo, que dependen del departamento de sistemas.

**Qué se plantea y no se hace.** Un resumen de la empresa a partir de su página web. El
material existe —el apartado 4.6.1 lo usa para clasificar sectores— pero resumir no es
clasificar, y verificar que el resumen no inventa exigiría una medición propia. Línea futura
declarada, no resultado.

**Qué NO lleva la ficha, y se dice en la memoria.** El nombre y el cargo de quien escribe
—minimización de datos—, el presupuesto y los plazos que el cliente menciona —constan solo en
el 43,8 % y el 28,6 % de los correos— y la estimación de cierre, que exige la oportunidad ya
creada.


## 3 · Experimentos y resultados

### E1 · Baseline con el dataset antiguo (4.000 empresas, 38 sectores)
**Fecha:** 21-09-2026 · **Datos:** 2.799 train / 602 test

| Modelo | Aciertos | F1-macro |
|---|---|---|
| Clase mayoritaria | 16,78 | 0,85 |
| Keywords + RandomForest *(el modelo que ya existía)* | 25,75 | 14,30 |
| TF-IDF + SVM, solo nombre | 33,06 | 20,75 |
| TF-IDF + SVM, solo texto web | 32,06 | 24,07 |
| **GPT zero-shot** | **40,47** | 31,40 |
| **TF-IDF + SVM, nombre + texto** | **48,50** | 31,40 |

**Conclusiones:**
- El modelo que ya existía (keywords + RF) era el peor de los modelos reales, 15 puntos
  por debajo de GPT.
- Un modelo lineal simple supera a GPT-4 por 8 puntos.
- Segmentado: con texto web 59,5 % frente a 45,9 % de GPT; sin texto, empate (34,9 vs 33,8).

---

### E2 · Análisis de transparencia semántica *(el resultado que define la tesis)*
**Fecha:** 21-09-2026 · **Datos:** los del E1

Agrupando los sectores según lo bien que los entiende GPT (corte en la mediana, 37,5 %):

| Grupo | Sectores | Empresas | GPT | Supervisado | **Ganancia** |
|---|---|---|---|---|---|
| **Idiosincráticos** | 10 | 208 | 22,8 % | 47,8 % | **+25,0** |
| **Transparentes** | 11 | 362 | 52,1 % | 52,8 % | **+0,7** |

**Diferencia de 35× en la ganancia.** Donde GPT ya entiende la categoría, el modelo
supervisado no aporta nada; donde no la entiende, gana 25 puntos.

**Casos extremos:** NANOTECNOLOGÍA +60,0 · MERCHANDISING +37,5 · MENAJE MONOUSO +33,3
frente a CERÁMICA −6,2 · UNIVERSIDAD +13,2.

**Ejemplo ilustrativo para la memoria:** *FÁBRICA DE MUEBLES (ejemplo)* — su web
habla de mobiliario de melamina y dormitorios; Empresa la clasifica como **CONSTRUCCIÓN /
INSTALACIONES Y ACABADOS**. Ningún modelo de lenguaje general deduce eso. Y en los pesos
del SVM se ve la convención aprendida: entre las palabras que más indican CONSTRUCCIÓN
aparecen "mobiliario" y "mesas".

---

### E3 · Elección del vectorizador
**Fecha:** 26-09-2026 · **Nivel:** sector (41 clases)

| Configuración | Tiempo | Aciertos | F1-macro |
|---|---|---|---|
| Original (char 3-5, 200k variables, texto completo) | >600 s | — | — |
| Solo palabras, texto a 1.500 | 44 s | 44,08 | 36,07 |
| Solo palabras, texto a 3.000 | 77 s | 45,14 | 37,50 |
| **Palabras + caracteres 4-5, texto a 1.500** | **135 s** | **48,45** | **39,93** |
| Palabras + caracteres, con SGD | 88 s | 44,00 | 34,59 |

**Conclusiones:** los n-gramas de caracteres valen +4,4 puntos y se mantienen. SGD es
más rápido pero pierde 4,5 puntos y se descarta. La longitud media real del texto es
1.968 caracteres, así que cortar en 2.000 apenas pierde información.

---

### E4 · Baselines con el dataset nuevo (21.707 empresas)
**Fecha:** 26-09-2026 · **Datos:** 16.408 train / 2.652 test · 55,1 % y 60,6 % con texto

**Por nivel de la taxonomía:**

| Nivel | Clases | Mejor modelo | Aciertos | F1-macro |
|---|---|---|---|---|
| Sector agrupado | 12 | LogReg | **56,73** | **53,79** |
| Sector | 41 | LogReg | **48,91** | **41,89** |
| Subsector (cola plegada) | 169 | SVM | **38,39** | 25,59 |

**Ablación de entrada, nivel sector:**

| Entrada | Aciertos |
|---|---|
| Solo el nombre | 32,92 |
| Solo el texto web | 34,39 |
| **Ambos** | **48,49** |

→ Juntas rinden 14 puntos más que la mejor por separado: **el nombre y la web aportan
información distinta, no redundante**.

**Por disponibilidad de texto (nivel sector):**

| | n | Aciertos |
|---|---|---|
| Sin texto web | 1.045 | 34,93 |
| **Con texto web** | 1.607 | **57,31** |

→ **El texto web vale 22 puntos.**

**Comparación con el dataset antiguo:**

| | Antes (4.000) | Ahora (21.707) |
|---|---|---|
| Clases | 38 | 41 |
| Aciertos | 48,50 | 48,91 |
| **F1-macro** | **31,40** | **41,89** |

→ El acierto apenas se mueve; el F1-macro sube **10,5 puntos** con más clases que antes.
**Confirma H2:** más datos no mejoran lo fácil, mejoran la cola larga.

**Jerarquía incoherente (H6):**

| | n | Aciertos |
|---|---|---|
| Filas coherentes | 2.056 | 50,05 |
| Filas incoherentes | 596 | **43,12** |

→ 7 puntos peor. Confirmada H6.

---

### E5 · LLM abierto, zero-shot
**Fecha:** 26-09-2026 · **Modelo:** Qwen2.5-7B-Instruct, cuantizado a 4 bits
**Muestra:** 300 empresas del test · **Hardware:** Colab, Tesla T4 · **Tiempo:** 4,6 min

| | Resultado |
|---|---|
| Aciertos | **33,33 %** |
| F1-macro | 25,12 |

**Por disponibilidad de texto:** sin texto 27,91 % · con texto 37,43 %

**Cumplimiento del formato:** exacta 97,3 % · aproximada 1,3 % · contenida 0,7 % ·
inválida 0,7 %

**Control clave:** el 97,3 % de respuestas con formato exacto **descarta la explicación
alternativa** de que el modelo no entendiera las instrucciones. Lo que falla no es el
formato, es saber cuál es la categoría correcta.

**Comparación cruzada con el supervisado:**

| | LLM | Supervisado | Distancia |
|---|---|---|---|
| Sin texto web | 27,9 % | 34,9 % | 7 puntos |
| **Con texto web** | 37,4 % | 57,3 % | **20 puntos** |

→ **La distancia se dispara cuando hay más información.** El LLM lee la web y entiende
qué hace la empresa, pero no puede mapearlo a la convención de Empresa. El cuello de
botella no es la información: es el conocimiento organizacional. **Confirma H1.**

---

### E6 · LLM abierto, few-shot (20 ejemplos)
**Fecha:** 26-09-2026 · **Mismas 300 empresas que E5** (misma semilla → comparación pareada)
**Tiempo:** 20,3 min

| | Zero-shot | Few-shot | Diferencia |
|---|---|---|---|
| Aciertos | 33,33 % | **34,67 %** | **+1,34** |
| F1-macro | 25,12 | 24,37 | **−0,75** |
| Formato exacto | 97,3 % | **99,7 %** | **+2,4** |

**Por disponibilidad de texto:** sin texto 25,58 % · con texto 41,52 %

**Conclusión — H4 refutada.** Los 1,34 puntos equivalen a 4 empresas de 300: ruido.
El F1-macro incluso baja.

**El hallazgo fino:** los ejemplos **sí** enseñaron algo — el formato subió del 97,3 %
al 99,7 %. Veinte ejemplos bastan para transmitir *la forma* de la respuesta y no bastan
en absoluto para transmitir *el criterio* de clasificación. Es una disociación limpia
entre forma y fondo.

**Pendiente:** test de McNemar sobre los datos pareados para confirmar que la diferencia
no es significativa.

---

### E7 · LLM abierto, segundo modelo: Salamandra-7B
**Fecha:** 26-09-2026 · **Modelo:** BSC-LT/salamandra-7b-instruct, cuantizado a 4 bits
**Mismas 300 empresas** · **Tiempo:** 4,7 min

| | Salamandra | Qwen2.5 |
|---|---|---|
| Aciertos | **16,00 %** | 33,33 % |
| F1-macro | 11,81 | 25,12 |
| **Respuestas con formato válido** | **65,3 %** | **99,3 %** |

**⚠️ ESTE RESULTADO NO ES COMPARABLE CON EL DE QWEN.**

Salamandra no respondió en el formato pedido en 104 de las 300 empresas (34,7 %). Esas
respuestas cuentan como fallo automáticamente, aunque el modelo pudiera tener razón.

**Acierto solo entre las 196 respuestas interpretables: 24,5 %.**

**Señal adicional de que el problema es de formato y no de comprensión:**

| | Aciertos |
|---|---|
| Sin texto web | 21,71 % |
| Con texto web | **11,70 %** |

Acierta **menos** cuando tiene más información, al revés que todos los demás modelos.
La explicación más probable es que con prompts largos el modelo se dispersa y deja de
responder con una categoría.

**REDACCIÓN OFICIAL PARA LA MEMORIA** *(texto acordado, usar literal)*

> Salamandra-7B alcanzó un 16,0 % de acierto, si bien el 34,7 % de sus respuestas no se
> ajustaron al formato solicitado frente al 0,7 % de Qwen2.5. Restringiendo la métrica a
> las respuestas interpretables, el acierto asciende al 24,5 %. La comparación directa
> entre ambos modelos no es por tanto concluyente en cuanto a comprensión de la taxonomía,
> ya que la diferencia se explica en buena medida por la capacidad de seguimiento de
> instrucciones.

**⛔ LO QUE NO SE PUEDE ESCRIBIR**

> ~~"Salamandra entiende peor la taxonomía de Empresa"~~

No se ha medido eso. Se ha medido que **obedece peor el formato**. Son cosas distintas y
confundirlas invalidaría la conclusión. Ver la medición pendiente M1 al final del documento.

**Lo que sí aporta:** dos modelos abiertos distintos, de arquitecturas y orígenes
distintos, quedan los dos muy por debajo del 48,9 % del modelo supervisado, se mida como
se mida. **Refuerza H1 y confirma H8.**

**Lección metodológica:** nunca comparar modelos generativos sin controlar la tasa de
cumplimiento de formato. Un modelo puede parecer peor clasificando cuando en realidad
solo es peor obedeciendo.

---

### E8 · Transformer XLM-RoBERTa (paso 6, cierre de A2)
**Fecha:** 27-09-2026 · **Modelo:** xlm-roberta-base, cabeza jerárquica
**Datos:** 16.408 train / 2.647 val / 2.652 test · **Hardware:** Colab T4 · **Tiempo:** 19,9 min
**Configuración:** 4 épocas, lote 16, max_len 256, lr 2e-5, pesos por clase, alfa 0,3 · beta 0,1

#### Resultado principal

| Nivel | Aciertos | F1-macro |
|---|---|---|
| Sector agrupado (12 clases) | **59,41** | **56,46** |
| Sector (41 clases) | **50,98** | 41,43 |

#### Comparativa completa · nivel sector, 41 clases

| Método | Aciertos | F1-macro |
|---|---|---|
| Responder siempre lo más común | 13,16 | 0,57 |
| LLM abierto zero-shot | 33,33 | 25,12 |
| LLM abierto few-shot | 34,67 | 24,37 |
| Supervisado · TF-IDF + SVM | 48,49 | 40,16 |
| Supervisado · regresión logística | 48,91 | **41,89** |
| **Transformer XLM-RoBERTa** | **50,98** | 41,43 |

#### ⚠️ H5 parcialmente refutada

La hipótesis era: *"un transformer entrenado supera al modelo lineal, **sobre todo en
F1-macro**"*. El razonamiento era que la comprensión semántica ayudaría en los sectores
con pocos ejemplos.

**Resultado:** gana en aciertos (+2,07) pero **NO en F1-macro** (−0,46). La predicción
sobre dónde estaría la mejora era incorrecta y así debe reportarse.

#### El hallazgo que sí aparece: robustez al ruido de etiqueta

| | Modelo lineal | Transformer |
|---|---|---|
| Filas con jerarquía coherente | 50,05 | 51,26 |
| Filas con jerarquía incoherente | 43,12 | **50,00** |
| **Penalización** | **−6,93** | **−1,26** |

**El transformer es cinco veces más robusto a las etiquetas ambiguas.** Es una ventaja
real de la comprensión semántica, pero se manifiesta en la tolerancia al ruido, no en la
cola larga como se había predicho. Conecta con C5 y H6.

#### Convergencia

| Época | Aciertos (val) | F1-macro (val) |
|---|---|---|
| 1 | 43,07 | 28,98 |
| 2 | 48,55 | 38,76 |
| 3 | 48,05 | **40,16** ← mejor |
| 4 | 48,21 | 39,56 |

Se estanca en la época 2-3 mientras la pérdida de entrenamiento sigue bajando
(3,40 → 2,72): comienza el sobreajuste. **Entrenar más no mejora.**

#### 🔑 Indicio fuerte de techo impuesto por los datos

Dos familias de modelos radicalmente distintas —un lineal sobre conteos de palabras y una
red neuronal profunda multilingüe— convergen ambas en el rango 49-51 %.

Cuando modelos tan distintos coinciden, lo más probable es que el límite no lo pongan los
modelos sino **la calidad de las etiquetas**. Parte del 49 % restante puede ser ruido del
propio CRM, no error del modelo.

**Consecuencia:** la medición **M3** (ruido de etiqueta) pasa a ser la más importante de
las pendientes. Sin ella no se puede afirmar si un 51 % está lejos o cerca del máximo
alcanzable, y por tanto no se puede valorar el sistema.

#### Redacción para la memoria

> El ajuste fino de XLM-RoBERTa alcanzó un 50,98 % de acierto y un F1-macro de 41,43 en
> la clasificación a nivel de sector (41 clases), frente al 48,91 % y 41,89 del mejor
> modelo lineal. La mejora se concentra en la exactitud global y en el nivel agrupado de
> la taxonomía (59,41 % frente a 56,73 %), mientras que el F1-macro permanece
> estadísticamente equivalente. El resultado no confirma la hipótesis de partida, que
> anticipaba una mejora concentrada en las clases minoritarias. Sí se observa, en cambio,
> una robustez notablemente superior ante registros con jerarquía inconsistente
> (penalización de 1,26 puntos frente a 6,93 del modelo lineal). La convergencia de dos
> familias de modelos muy distintas en un rango estrecho de rendimiento sugiere la
> existencia de un techo impuesto por la calidad del etiquetado más que por la capacidad
> de los modelos.

---

### E8b · Análisis de errores del transformer
**Fecha:** 27-09-2026 · **Datos:** `pred_principal.csv`, 2.652 empresas

#### Sectores peor y mejor clasificados

| Peor | n | Acierto | Ejemplos train | | Mejor | n | Acierto | Ejemplos train |
|---|---|---|---|---|---|---|---|---|
| MENAJE MONOUSO | 13 | **0,0 %** | 42 | | UNIVERSIDAD E INVESTIGACIÓN | 115 | 85,2 % | 578 |
| **OTROS** | 30 | **0,0 %** | 239 | | DEFENSA | 27 | 81,5 % | 208 |
| DISTRIBUCIÓN MINORISTA/MAYORISTA | 56 | 10,7 % | 436 | | DROGUERÍA Y PERFUMERÍA | 64 | 79,7 % | 499 |
| LABORATORIOS | 29 | 13,8 % | 112 | | CERÁMICA | 25 | 76,0 % | 67 |
| NANOTECNOLOGÍA | 17 | 17,6 % | 91 | | LOGÍSTICA Y TRANSPORTE | 163 | 74,8 % | 1.286 |

**Caso llamativo: "OTROS" acierta un 0 % pese a tener 239 ejemplos de entrenamiento.**
Es una categoría residual, un cajón de sastre sin contenido semántico propio: no hay
ningún rasgo compartido que el modelo pueda aprender. **No es un fallo del modelo, es un
problema de diseño de la taxonomía.** Conviene excluirla del cálculo o tratarla aparte, y
declararlo.

#### ¿Cuánto influye el número de ejemplos?

| Ejemplos en train | Sectores | Acierto medio |
|---|---|---|
| < 100 | 7 | 34,8 % |
| 100 – 300 | 18 | 42,8 % |
| 300 – 800 | 6 | 48,0 % |
| > 800 | 6 | **59,0 %** |

Correlación entre volumen de ejemplos y acierto: **r = 0,286**. Positiva pero **modesta**.
Hay 24 puntos de diferencia entre los extremos, pero la cantidad de datos explica solo una
parte: CERÁMICA acierta un 76 % con 67 ejemplos, mientras DISTRIBUCIÓN acierta un 10,7 %
con 436. **La dificultad de la categoría pesa más que el volumen de datos.**

#### 🔑 Las confusiones son simétricas y semánticamente coherentes

| Confusión | n | Sentido inverso | n |
|---|---|---|---|
| ALIMENTACIÓN NO PERECEDERA → PERECEDERA | 22 | PERECEDERA → NO PERECEDERA | **21** |
| MATERIAS PRIMAS → INDUSTRIA QUÍMICA | 19 | INDUSTRIA QUÍMICA → MATERIAS PRIMAS | **27** |
| ENVASE Y EMBALAJE → FABRICANTE ART. PLÁSTICO | 26 | | |
| ENVASE Y EMBALAJE → INDUSTRIA QUÍMICA | 21 | | |
| RECICLADORES → GESTIÓN DE RESIDUOS | 14 | | |

**Esto es lo más relevante del análisis.** Los errores no son aleatorios: se concentran en
pares de categorías que una persona también confundiría. Y son **casi perfectamente
simétricos** (22 contra 21; 19 contra 27).

Una confusión asimétrica indicaría un sesgo del modelo hacia la clase mayoritaria. Una
confusión **simétrica** indica que **la frontera entre ambas categorías es genuinamente
difusa**: una empresa alimentaria puede fabricar producto perecedero y no perecedero; un
fabricante de envases de plástico es a la vez envase y artículo de plástico.

**Refuerza H9** (techo impuesto por los datos): parte del error no es corregible con mejor
modelado porque la etiqueta correcta es discutible.

#### Distancia del error

Solo el **15,8 %** de los errores cae dentro del mismo sector agrupado. Es decir, el 84 %
de los fallos cruzan la frontera de familia.

Esto explica aritméticamente la diferencia entre niveles:
`50,98 + (49,02 × 0,158) ≈ 58,7`, muy cerca del 59,41 % medido en el nivel agrupado. Los
dos números son coherentes entre sí.

#### Implicaciones

1. **Excluir o aislar la categoría OTROS** en los análisis: contamina las métricas y no es
   aprendible por construcción.
2. **Documentar los pares ambiguos** (alimentación perecedera/no perecedera, materias
   primas/química, envase/plástico) como limitación inherente de la taxonomía.
3. **Preguntar a negocio** si esos pares deben seguir separados: si dos categorías llevan
   siempre al mismo técnico comercial y se confunden sistemáticamente, quizá sobra una.
   Es la pregunta P3.

---

### E9 · Test de McNemar: transformer frente a modelo lineal

> **Ampliación del 29-09-2026** (`scripts/F2_A2_E9_E11_contrastes.py`). Al segmentar
> el contraste por disponibilidad de texto web aparece un resultado que no estaba
> medido:
>
> | | n | Transformer | Lineal | p |
> |---|---|---|---|---|
> | Con texto | 1.607 | 60,92 % | 57,93 % | **0,013** |
> | Sin texto | 1.045 | 37,61 % | 35,02 % | 0,073 |
>
> La ventaja del transformer **se concentra donde hay texto que leer**. Sin texto la
> diferencia no alcanza significación. Es coherente con el resto del trabajo pero no
> se había contrastado.

**Fecha:** 27-09-2026 · **Datos:** 2.652 empresas, comparación pareada
**Método:** McNemar exacto (binomial sobre las discordancias)

#### Nivel sector (41 clases)

| | Acierto |
|---|---|
| Regresión logística | 48,91 % |
| Transformer | **50,98 %** |
| Diferencia | **+2,07 puntos** |

**Tabla de discordancias:**

| | n |
|---|---|
| Ambos aciertan o ambos fallan | 2.063 |
| Solo acierta el lineal | 267 |
| Solo acierta el transformer | **322** |

**p = 0,026 → diferencia significativa al 5 %**

#### Nivel sector agrupado (12 clases)

| | Acierto |
|---|---|
| Regresión logística | 57,44 % |
| Transformer | **60,09 %** |
| Diferencia | **+2,66 puntos** |

Discordancias: 252 solo lineal · 320 solo transformer · **p = 0,005**

*(Nota: el nivel agrupado del modelo lineal se deriva mapeando su predicción de sector.
Por eso estas cifras difieren ligeramente de las de E4/E8, calculadas sobre subconjuntos
algo distintos.)*

#### Interpretación

El test ignora las 2.063 empresas en que ambos modelos coinciden y examina solo las 589
discordantes. Bajo la hipótesis de equivalencia se repartirían ~294/295; se observan
267/322. Esa desviación tiene un 2,6 % de probabilidad bajo el azar.

**Corrige una afirmación previa:** se había anticipado que 2 puntos podrían ser ruido. Con
2.652 observaciones pareadas, son detectables. La ventaja del transformer es real.

**Matiz necesario:** significativo estadísticamente no equivale a relevante en la práctica.
La diferencia es real pero pequeña frente al coste operativo. Ver D11.

#### Redacción para la memoria

> La diferencia de 2,07 puntos entre el transformer (50,98 %) y la regresión logística
> (48,91 %) resulta estadísticamente significativa (test de McNemar exacto sobre 2.652
> observaciones pareadas, b = 267, c = 322, p = 0,026). En el nivel agrupado de la
> taxonomía la ventaja asciende a 2,66 puntos con mayor significación (p = 0,005). No
> obstante, la magnitud del efecto es modesta en relación con el coste computacional y de
> mantenimiento asociado al modelo neuronal.

---

### E10 · Ablaciones del transformer
**Fecha:** 27-09-2026 · Mismas condiciones que E8, variando un elemento cada vez

| Configuración | Aciertos | F1-macro |
|---|---|---|
| Solo el nombre de la empresa | 36,24 | 26,80 |
| Sin ponderación por clase | 50,79 | 34,39 |
| **Principal** (jerarquía + pesos) | 50,98 | 41,43 |
| **Sin cabeza jerárquica** | **51,73** | **43,38** |

#### 🔑 Hallazgo principal: la cabeza jerárquica PERJUDICA

Quitarla mejora **ambas** métricas: **+0,75** en aciertos y **+1,95** en F1-macro.

**Por qué el diseño original era erróneo.** La cabeza jerárquica pedía al modelo predecir
el subsector como tarea auxiliar, más un término que penalizaba la incoherencia entre
niveles. El razonamiento era que daría señal adicional y regularizaría. Pero:

- El subsector solo está relleno en el **74 %** de los casos
- **24 subsectores cuelgan de más de un sector** (ver C5): la jerarquía con la que se le
  obligaba a ser coherente es ella misma incoherente
- Son **169 clases**, una tarea auxiliar muy difícil

Resultado: capacidad del modelo desviada hacia una tarea ruidosa, en detrimento de la
principal. **El modelo más simple gana.**

#### Esto rehabilita H5

| | Aciertos | F1-macro |
|---|---|---|
| Regresión logística | 48,91 | 41,89 |
| **Transformer sin jerarquía** | **51,73** | **43,38** |
| Diferencia | **+2,82** | **+1,49** |

H5 postulaba que el transformer superaría al lineal **sobre todo en F1-macro**. Con la
configuración principal no lo hacía (E8) y se marcó como parcialmente refutada. **Con la
configuración correcta sí lo hace.** Lo que fallaba no era la hipótesis sino la
implementación de la cabeza jerárquica.

#### La ponderación por clase sí era necesaria

| | Aciertos | F1-macro |
|---|---|---|
| Con pesos | 50,98 | **41,43** |
| Sin pesos | 50,79 | **34,39** |

Mismo acierto, **7 puntos menos de F1-macro**. Comportamiento de manual: sin ponderar, el
modelo ignora las clases minoritarias y lo compensa acertando las mayoritarias. La
exactitud no lo refleja; el F1-macro sí. **Decisión de diseño validada.**

#### Aportación del texto web, comparada entre familias

| | Solo nombre | Completo | Ganancia |
|---|---|---|---|
| Transformer | 36,24 | 50,98 | +14,7 |
| Lineal | 32,92 | 48,49 | +15,6 |

Ambas familias extraen un valor equivalente del texto. El transformer es algo mejor
partiendo solo del nombre (+3,3 puntos), coherente con su mayor capacidad para
interpretar razones sociales.

#### ⚖️ Compromiso: la jerarquía aportaba robustez

| | Coherentes | Incoherentes | Penalización |
|---|---|---|---|
| Con jerarquía | 51,26 | 50,00 | **−1,26** |
| Sin jerarquía | 52,58 | 48,83 | −3,75 |

**La cabeza jerárquica sí mejoraba la robustez ante etiquetas ambiguas**, pero el coste en
rendimiento global superaba el beneficio. No es "la jerarquía no sirve", sino que el
compromiso no compensa con esta calidad de etiquetado. Si las etiquetas de subsector
mejorasen, la conclusión podría invertirse.

#### Redacción para la memoria

> El estudio de ablación reveló que la cabeza jerárquica auxiliar, incorporada para
> aprovechar la estructura de la taxonomía, degradaba el rendimiento en ambas métricas
> (51,73 % y 43,38 de F1-macro sin ella, frente a 50,98 % y 41,43 con ella). Se atribuye a
> la baja cobertura del segundo nivel (74 %) y a la inconsistencia de la propia jerarquía,
> que hace que el término de coherencia introduzca una restricción parcialmente errónea.
> La ponderación por clase, en cambio, resultó determinante: su eliminación reduce el
> F1-macro en 7 puntos sin afectar apreciablemente a la exactitud, confirmando su papel en
> el tratamiento del desbalanceo.

**MODELO FINAL DE A2: transformer sin cabeza jerárquica · 51,73 % · F1-macro 43,38**

---

### E11 · Contrastes estadísticos completos (McNemar + bootstrap)
**Fecha:** 27-09-2026 · 2.652 empresas, comparaciones pareadas

| Comparación | Métrica | Diferencia | Método | p | ¿Significativa? |
|---|---|---|---|---|---|
| Transformer final vs regresión logística | Aciertos | **+2,83** | McNemar exacto | **0,0020** | ✅ **Sí** |
| Transformer final vs regresión logística | F1-macro | +1,50 | Bootstrap (2.000) | 0,241 | ❌ No |
| Sin jerarquía vs con jerarquía | Aciertos | +0,75 | McNemar exacto | 0,244 | ❌ No |
| Sin jerarquía vs con jerarquía | F1-macro | +1,95 | Bootstrap (2.000) | 0,070 | ❌ No |
| Nombre + texto vs solo nombre | Aciertos | +14,74 | McNemar exacto | 10⁻⁴⁷ | ✅ **Sí** |

Intervalos de confianza al 95 % del F1-macro (bootstrap):
- Sin jerarquía vs con jerarquía: **[−0,20, +3,65]** → incluye el cero
- Transformer vs lineal: **[−1,14, +4,14]** → incluye el cero

#### ⚠️ Correcciones a afirmaciones anteriores

**H5 vuelve a "parcialmente confirmada".** En E10 se dio por confirmada porque el
transformer ganaba en ambas métricas. La ventaja en F1-macro **no es estadísticamente
demostrable**. Lo que sí queda demostrado es la ventaja en exactitud.

**H11 no puede darse por refutada.** El perjuicio de la cabeza jerárquica apunta en esa
dirección (F1-macro p = 0,070) pero no alcanza significación. Se marca como *indicio no
concluyente*.

#### 🔑 Hallazgo metodológico: el F1-macro es difícil de contrastar

El F1-macro promedia las 41 clases dando el mismo peso a cada una. Varios sectores tienen
10-17 empresas en el test; en un remuestreo, dos empresas de más o de menos en una clase
de 13 mueven su F1 varios puntos, y eso arrastra la media.

**Consecuencia:** el F1-macro tiene una varianza muy alta y con 2.652 observaciones no
permite detectar diferencias de 1,5-2 puntos. La exactitud, calculada sobre observaciones
independientes, es mucho más estable — por eso una diferencia menor (2,83) resulta
significativa mientras otra mayor (1,95 en F1-macro) no lo es.

**Para la memoria:** conviene declarar esta limitación. No es que los modelos no difieran
en F1-macro; es que el conjunto de prueba disponible no permite demostrarlo.

#### Redacción para la memoria

> El modelo final supera a la regresión logística en exactitud de forma estadísticamente
> significativa (51,73 % frente a 48,91 %; McNemar exacto sobre 2.652 observaciones
> pareadas, b = 249, c = 324, p = 0,002). Las diferencias observadas en F1-macro, aunque
> favorables al modelo neuronal (+1,50 puntos), no alcanzan significación estadística
> (bootstrap con 2.000 remuestreos, IC 95 % [−1,14, +4,14]). Esta limitación se atribuye a
> la elevada varianza del F1-macro en presencia de clases con escasa representación en el
> conjunto de prueba, y no permite concluir diferencias entre modelos en dicha métrica.

**MODELO FINAL DE A2: transformer sin cabeza jerárquica · 51,73 % de acierto · F1-macro 43,38**
*(la elección se sostiene sobre la exactitud, única métrica con diferencia demostrada)*

---

### E12 · ¿Predice la atractividad el comportamiento real? (validación previa de A3)
**Fecha:** 27-09-2026 · **Datos:** 24.079 cuentas × 4.881 oportunidades × 4.063 ofertas
**Cruce:** por ID de cuenta (100 % de cobertura) y por nombre para las no clientes (100 %)

| Nota | Cuentas | Con oportunidad | Con venta cerrada |
|---|---|---|---|
| **B** · Asistencia e innovación recurrente | 311 | **36,7 %** | 25,1 % |
| **A** · I+D sin subvención | 332 | 25,9 % | 17,2 % |
| **C** · I+D con subvención | 879 | 26,4 % | 13,1 % |
| **D** · Asistencia esporádica | 1.067 | 16,1 % | 8,7 % |
| **E** · No target de Empresa | 285 | 11,2 % | 5,6 % |
| *Sin clasificar* | **21.066** | **7,2 %** | — |

> **Nota metodológica:** el análisis se realiza sobre **tasas de conversión**, no sobre
> importes facturados. Se decidió excluir toda variable monetaria del trabajo (ver D13).
> Las conclusiones no se ven afectadas: la señal que se mide es la propensión a generar
> negocio, no su magnitud.

**Contrastes:** Kruskal-Wallis H = 81,4, p = 9·10⁻¹⁷ · Spearman ρ = −0,148, p = 1,6·10⁻¹⁵

#### Conclusión 1: la escala funciona

El criterio comercial de Empresa captura señal real. De E a B hay más del triple de
probabilidad de generar oportunidad y más del cuádruple de cerrar venta. **Entrenar un modelo
para replicar esta valoración tiene sentido**: no se estaría automatizando un criterio
arbitrario.

#### Conclusión 2: la escala NO es ordinal pura

**B supera a A** en todos los indicadores. No es un error: A identifica al cliente más
valioso *por proyecto* (I+D sin subvención) y B al que *vuelve* (recurrente). En volumen
anual, la recurrencia gana.

**Consecuencia para el modelo:** tratar la escala como un orden A>B>C>D>E forzaría una
jerarquía que los datos no respaldan. Conviene modelarla como clasificación multiclase,
no como regresión ordinal.

#### 🔑 Conclusión 3: hay valor sin descubrir en las 21.000 sin clasificar

Las cuentas **sin nota** convierten al 7,2 %. Las marcadas **E ("no target")** convierten
al **11,2 %**.

Las cuentas que alguien descartó explícitamente rinden **más** que las que nadie ha mirado.
No es que la E esté mal asignada: es que el 87 % de la base de datos está sin valorar y
contiene cuentas de calidad A o B que nadie ha identificado.

**Esto es la justificación de negocio de A3**, y es un argumento cuantificado, no una
suposición.

#### Decisión de modelado

Se modela *"¿generará oportunidad?"* como variable binaria. Es la formulación adecuada
por dos motivos: está bien repartida (9,1 % de casos positivos) y **evita el tratamiento
de variables monetarias**, excluidas del trabajo por la decisión D13.

---

### E13 · ¿Aportan información distinta la cuenta y lo que pide? (justifica D12)

> ✅ **Verificado el 30-09-2026** (`scripts/F3_A3_E12_E16_conversion.py`).
>
> **Atención al denominador.** E13 calcula la conversión sobre **todas** las oportunidades,
> contando las abiertas como no convertidas. El análisis de F6, en cambio, la calculó solo
> sobre las **cerradas**. Las dos son correctas y miden cosas distintas:
>
> | Tipo solicitado | Sobre TODAS *(E13)* | Sobre CERRADAS |
> |---|---|---|
> | Ensayos | 57,0 % | 61,8 % |
> | Consultoría y asistencia técnica | 42,0 % | 50,8 % |
> | Desarrollo I+D | 8,5 % | 18,2 % |
> | **Global** | **43,0 %** | **54,7 %** |
>
> La primera es una cota inferior —incluye 1.048 oportunidades aún en curso—; la segunda es
> la tasa de éxito cuando el asunto se resuelve. **No deben aparecer en la misma tabla.** La
> memoria emplea la definición de E13 de forma consistente en todo el apartado 4.6.2.
>
> **Cifras reproducidas del cruce nota × tipo** (sobre todas, misma definición):
> A/ensayos 66,9 % · B/ensayos 66,9 % · E/ensayos **61,5 %** · A/I+D **6,2 %**.
> Difieren en décimas de las publicadas originalmente (67 / 69 / 58 / 9) por el filtrado de
> filas sin tema. **La conclusión es idéntica y se refuerza**: la distancia entre una cuenta
> E pidiendo un ensayo y una cuenta A pidiendo I+D es aún mayor de lo reportado (61,5 %
> frente a 6,2 %, casi diez veces).
>
> Se adoptan como oficiales las cifras reproducibles por el script.
**Fecha:** 27-09-2026 · **Datos:** 4.872 oportunidades con tema · 43,4 % acaban en oferta ganada

#### Conversión según el tipo de servicio solicitado

| Tipo de servicio | n | Conversión |
|---|---|---|
| Ensayos | 2.236 | **57,2 %** |
| Formación | 84 | 57,1 % |
| Consultoría y asistencia técnica | 1.406 | 42,4 % |
| Servicios | 304 | 39,5 % |
| **Desarrollo I+D** | 798 | **8,8 %** |

**Lo que se pide pesa más que quién lo pide.** Un ensayo convierte seis veces más que un
proyecto de I+D, con independencia del tipo de cuenta.

#### Cruce: nota de la cuenta × tipo de servicio (% de conversión)

| Nota | Consultoría | I+D | Ensayos |
|---|---|---|---|
| A | 56 | 9 | 67 |
| B | 61 | 5 | 69 |
| C | 47 | 9 | 62 |
| D | 42 | 13 | 54 |
| **E** | 41 | **0** | **58** |

#### 🔑 Conclusión

**Una cuenta E pidiendo un ensayo convierte al 58 %. Una cuenta A pidiendo I+D, al 9 %.**

Las dos fuentes de información varían de forma prácticamente independiente: la nota
ordena dentro de cada columna, el tipo de servicio ordena dentro de cada fila, y la
segunda tiene un rango mucho mayor.

**Priorizar solo por la valoración de la cuenta llevaría a atender la A y descartar la E,
cuando la E tiene seis veces más probabilidad de cerrar.** Esto justifica el diseño en dos
fases de D12 y descarta un modelo único basado solo en atributos de empresa.

---

### E14 · A3 fase 1 · Puntuar cuentas antes del contacto
**Fecha:** 27-09-2026 · 2.874 cuentas valoradas A-E · 2.155 train / 719 test

| Modelo | Aciertos | F1-macro |
|---|---|---|
| Clase mayoritaria | 37,13 | 10,83 |
| Regresión logística | 45,20 | 43,29 |
| RF sin zona ni combinaciones | 47,43 | 45,58 |
| RF con zona y combinaciones | 47,84 | 46,77 |
| **RF completo + texto web** | **49,24** | **47,35** |

El texto web aporta poco (+1,4): dice **qué hace** una empresa, no **cuánto vale como
cliente**. Muy distinto de A2, donde valía 22 puntos.

#### ⚠️ LIMITACION: desajuste de población en `tamaño`

Detectada a raíz de una pregunta de la autora sobre el significado de las variables.

| | Con `tamaño` informado |
|---|---|
| Cuentas valoradas (entrenamiento y test) | **93,8 %** |
| Cuentas sin valorar (población objetivo) | **27,9 %** |

Dentro del entrenamiento la variable es señal genuina (A: 85,5 % grandes empresas;
D: 85,7 % PYMEs; χ², p = 1,7·10⁻¹⁹⁹) y la proporción de "sin dato" apenas varía entre
notas, lo que descarta que el modelo aprenda "alguien se molestó en mirarla".

**No es fuga sino desajuste de población.** Reentrenando sin la variable: **43,39 %**
frente a 48,26 %. **Coste: 4,9 puntos.**

> **Para la memoria:** la cifra a reportar para la población objetivo es **43,4 %**, no
> 48-49 %. El conjunto de prueba se compone de cuentas ya valoradas, donde el tamaño está
> informado en el 93,8 % de los casos frente al 27,9 % de las no valoradas.

*(Sobre las 22 cuentas de test sin tamaño el acierto es del 63,6 %, pero con n = 22 el
margen ronda los ±20 puntos: no es interpretable y no debe citarse.)*

---

### E15 · La proximidad geográfica predice, y el criterio humano la penaliza
**Fecha:** 27-09-2026 · **Origen:** hipótesis planteada por la autora
**Datos:** 24.079 cuentas cruzadas con 4.881 oportunidades

#### Las cuentas de la Comunidad Valenciana convierten el doble

| | Cuentas | Con oportunidad | Con venta |
|---|---|---|---|
| **Comunidad Valenciana** | 4.734 | **15,3 %** | **6,1 %** |
| Resto | 19.345 | 7,5 % | 3,0 % |

χ², p = 3,1·10⁻⁶². La proximidad a la sede de Empresa es un predictor de primer orden.

#### 🔑 Pero reciben peores notas

| Zona | Cuentas valoradas | % con nota A o B |
|---|---|---|
| **Internacional** | 318 | **54,7 %** |
| Resto de España | 1.633 | 21,0 % |
| **Comunidad Valenciana** | 923 | **13,7 %** |

**El criterio de valoración está prácticamente invertido respecto al rendimiento real.**
Las cuentas que más convierten reciben las notas más bajas; las internacionales, que
convierten menos, reciben nota alta cuatro veces más a menudo.

Posible explicación: las cuentas internacionales pueden ser estratégicas por motivos no
visibles en la facturación (proyectos europeos, financiación, prestigio). **No se afirma
que la valoración sea errónea**, sino que existe una discrepancia sistemática entre el
criterio declarado y el comportamiento observado, y que esa discrepancia no está
documentada en ningún sitio de la organización.

#### Combinaciones sector × zona con mayor conversión

*(media global: 9,1 %)*

| Sector | Zona | n | Conversión |
|---|---|---|---|
| Droguería, cosmética y farmacia | **CV** | 170 | **32,9 %** |
| Envase y embalaje | **CV** | 447 | **32,0 %** |
| Recicladores y gestores de residuos | **CV** | 158 | 26,6 % |
| Materias primas e industria química | **CV** | 332 | 25,6 % |
| Envase y embalaje | Resto | 3.057 | 12,5 % |

El mismo sector triplica su conversión según la zona. **La combinación de variables
predice mejor que cualquiera por separado**, lo que justifica introducir las interacciones
`sector × zona` y `sector × tamaño` como variables explícitas.

#### Efecto de incorporarlas al modelo

| | Aciertos | F1-macro |
|---|---|---|
| Sin zona ni combinaciones | 47,43 | 45,58 |
| **Con zona y combinaciones** | **47,84** | **46,77** |

**+1,19 de F1-macro.** Y `sector_tamano` pasa a ser la variable más influyente, por delante
del tamaño aislado. La clase E es la que más mejora (recall 0,394 → 0,451), coherente con
que `sector_zona_pE` figure entre las variables de mayor peso: hay combinaciones de sector
y zona sistemáticamente fuera del target.

> **Nota metodológica:** esta variable codifica conocimiento de negocio que el modelo no
> puede inferir. Para el algoritmo, Castellón, Valencia y Alicante son tres categorías
> sueltas entre 52 provincias, sin relación entre sí. Que formen un grupo con sentido por
> la proximidad a la sede solo lo sabe alguien de la organización. Es un buen ejemplo de
> por qué el conocimiento de dominio sigue siendo necesario.

---

### E16 · A3 · Modelo de conversión real y comparación con el criterio humano

> ✅ **Verificado el 29-09-2026** (`scripts/F3_A3_E12_E16_conversion.py`).
> La reconstrucción independiente del experimento da **AUC 0,788** frente al 0,774
> publicado y un **ratio quintil superior/inferior de 14,7×** frente al 16,3×. Ambas
> dentro del margen esperable sin la configuración original. **Las cifras de E16 se dan
> por reproducidas.**
>
> Durante la auditoría este experimento se marcó primero como no reproducible. Era un
> error del propio cotejo, no de E16: se comparaba un lift sobre la tasa de base con un
> cociente entre quintiles, y sobre la cartera entera en lugar de sobre las cuentas
> valoradas. Queda documentado en X12 porque ilustra un riesgo real de la fase de
> revisión. Ver `14_REPRODUCIBILIDAD.md`.

**Fecha:** 27-09-2026 · **Datos:** 24.079 cuentas · 2.185 convierten (9,1 %)
**Objetivo:** ¿generará alguna oportunidad? (binario) · **Modelo:** Random Forest

#### ⚠️ Circularidad detectada y corregida

La primera versión incluía `es_cliente` como variable. **Ser cliente implica haber tenido
oportunidades**, que es justo lo que se quiere predecir.

| Modelo | AUC | AUC-PR | top 20 % / bottom 20 % |
|---|---|---|---|
| Con `es_cliente` *(contaminado)* | 0,829 | 0,393 | 24,9× |
| **Sin `es_cliente` (válido)** | **0,774** | **0,302** | **16,3×** |
| Sin `es_cliente` ni `tamaño` | 0,774 | 0,298 | 15,6× |

*(azar: AUC 0,500 · AUC-PR 0,091)*

**Las cifras a reportar son las de la segunda fila.** El 24,9× inicial estaba inflado.

#### Capacidad de priorización (modelo válido)

| Decil | Conversión real |
|---|---|
| 10 (mejores) | **29,5 %** |
| 9 | 16,4 % |
| 8 | 13,9 % |
| … | … |
| 2 | 1,7 % |
| 1 (peores) | **1,2 %** |

**El 20 % mejor convierte 16,3 veces más que el 20 % peor.** Traducido a operación: de
100 cuentas del decil alto salen unas 30 oportunidades; de 100 del decil bajo, una.

#### 🔑 Comparación con el criterio humano

Sobre las mismas 708 cuentas valoradas del conjunto de prueba (163 convierten):

| Criterio | AUC |
|---|---|
| **Modelo de conversión** | **0,707** |
| Nota humana de atractividad (A=5 … E=1) | 0,638 |
| Diferencia | **+0,069** |

**Bootstrap, 2.000 remuestreos: IC 95 % [+0,011, +0,130], p = 0,016 → significativa.**

El modelo discrimina mejor que la valoración manual, con ventaja **modesta pero
estadísticamente demostrada**. La nota humana no es inútil (0,638 está claramente por
encima del azar), pero el modelo captura más señal.

#### Hallazgo secundario: `tamaño` predice la opinión, no el comportamiento

| | Coste de quitar `tamaño` |
|---|---|
| Modelo de **atractividad** (E14) | **−4,9 puntos** |
| Modelo de **conversión** (este) | **0,000** |

El tamaño de la empresa es la variable más influyente para predecir **lo que un comercial
opinará**, y es irrelevante para predecir **lo que la cuenta hará**. Refuerza E15: el
criterio de valoración vigente se apoya en señales que no anticipan el negocio real.

#### Redacción para la memoria

> El modelo de conversión alcanza un AUC de 0,774 y permite ordenar la cartera de forma
> que el primer quintil convierte 16,3 veces más que el último. Restringiendo la
> comparación a las cuentas con valoración humana disponible, el modelo discrimina mejor
> que dicha valoración (AUC 0,707 frente a 0,638; diferencia +0,069, IC 95 % [+0,011,
> +0,130] por bootstrap, p = 0,016). Se descartó una versión inicial del modelo que
> incluía la condición de cliente entre sus variables, al constituir ésta una forma de
> circularidad respecto a la variable objetivo.

---

### E17 · A5 · El emparejamiento léxico no funciona (resultado negativo)
**Fecha:** 27-09-2026 · **Datos:** catálogo de 14 servicios con 74 términos de señal ·
muestra de 400 empresas con texto web

#### Qué se probó

Emparejar cada empresa con el servicio de Empresa que mejor le encaja, buscando en su web
los términos que el catálogo declara como indicadores de encaje. Sin entrenamiento: solo
presencia de términos.

#### Tres versiones, en orden

| Versión | Sin ninguna señal | Empates | Fiables (2+ señales) | Servicio dominante |
|---|---|---|---|---|
| 1 · Conteo simple *(con bug)* | 10,2 % | 22,5 % | 33,0 % | S05 · 22,8 % |
| 2 · Ponderado por especificidad | — | 10,2 % | — | S01 · 22,0 % |
| **3 · Búsqueda corregida** | **41,8 %** | **48,2 %** | **17,5 %** | S01 · 53,8 % |

#### ⚠️ El bug que inflaba los resultados

Las versiones 1 y 2 buscaban las señales como **subcadena** en lugar de como palabra:

| Señal | Aparecía en | Qué encontraba realmente |
|---|---|---|
| `pla` | **66,8 %** de las webs | "**pla**nta", "**pla**ncha", "**pla**zo" |
| `pet` | 33,0 % | "com**pet**encia", "re**pet**ir" |
| `pha` | 7,3 % | "al**fa**bético" y similares |

Y en el extremo contrario, `i+d` aparecía en el **0,00 %** de las webs, lo cual es
imposible: la función de normalización eliminaba el símbolo `+` y dejaba el término
inbuscable.

**Corregidos ambos, el rendimiento se desploma.** Ese desplome es el dato correcto: el 33 %
de emparejamientos "fiables" de la versión 1 se apoyaba en coincidencias falsas.

#### 🔑 Conclusión: desajuste de registro

Con la búsqueda correcta, **en el 41,8 % de las webs no aparece ninguno de los 74 términos
del catálogo**, y el 48,2 % de los emparejamientos son empates a cero.

El motivo no es que las señales estén mal elegidas, sino que **empresa e instituto hablan
del mismo asunto con vocabularios distintos**:

| Cómo se describe la empresa | Cómo describe Empresa el servicio |
|---|---|
| *"fabricamos envases para la industria alimentaria"* | *"declaración de conformidad y ensayos de migración"* |
| *"reducimos el plástico de nuestros envases"* | *"reducción de plástico"* |

Ni siquiera las variantes morfológicas coinciden: "reducción" no encuentra "reducimos".

**Esto no se arregla afinando el catálogo.** Requiere comparar significados en lugar de
cadenas de texto, que es lo que hacen los *embeddings*.

#### Valor del resultado negativo

Documenta por qué se recurre a un método más complejo, en lugar de afirmarlo. La
progresión —léxico simple, léxico ponderado, léxico corregido, semántico— convierte una
elección de diseño en una conclusión medida.

**Además ilustra un riesgo metodológico general:** un error de implementación puede
producir resultados *aparentemente mejores* que la versión correcta. Si no se hubiera
revisado la búsqueda por subcadena, el método léxico habría parecido razonable y se habría
descartado el semántico por innecesario.

---

### E18 · A5 · Emparejamiento semántico y política de confianza
**Fecha:** 27-09-2026 · **Modelo:** intfloat/multilingual-e5-small (abierto, multilingüe)
**Datos:** 14 servicios × 400 empresas con texto web

#### Comparativa con el método léxico

| | Léxico corregido | **Semántico** |
|---|---|---|
| No puede decidir | 41,8 % | **0 %** |
| Servicios nunca elegidos | 1 | **0** |
| Coincidencia entre ambos métodos | — | **9,8 %** |

Los dos métodos **no son variantes de lo mismo**: coinciden en menos del 10 % de los casos.

#### Prueba de sentido común: coherencia con el sector

| Sector | Servicio propuesto | |
|---|---|---|
| **Alimentación perecedera** | Vida útil y estabilidad | **26 / 30** |
| Alimentación no perecedera | Vida útil y estabilidad | 12 / 17 |
| Logística y transporte | Optimización logística | 11 / 28 |
| Droguería y perfumería | Vida útil y estabilidad | 7 / 16 |
| Envase y embalaje | Caracterización de materiales | 20 / 79 |

Los emparejamientos coinciden con lo que elegiría una persona. El método léxico no
acertaba ninguno de estos.

#### Problema detectado: las similitudes no separan

| | |
|---|---|
| Similitud media | 0,798 |
| Desviación típica | 0,023 |
| Rango completo | 0,717 – 0,861 |

Todas las parejas puntúan en una franja de 0,14 puntos. El modelo ordena bien, pero con
diferencias tan pequeñas que **no permite saber cuándo fiarse**. Es un efecto conocido:
cuando todos los textos pertenecen al mismo dominio, los vectores se concentran en una
región estrecha del espacio y las similitudes se comprimen.

#### Solución: normalización por fila

En lugar de la similitud absoluta se mide **cuánto destaca cada servicio frente a los otros
trece para esa misma empresa** (puntuación z por fila).

| | Antes | Después |
|---|---|---|
| Rango del margen | 0,000 – 0,010 | **0,00 – 2,30** (desviaciones típicas) |
| Decisiones claras | 15,8 % | **26,8 %** |

**No se cambió el modelo, se cambió cómo se lee su salida.**

#### 🔑 Validación: la confianza declarada predice el acierto

Sobre alimentación perecedera, donde el servicio correcto es conocido (vida útil):

| Confianza declarada | n | Acierto |
|---|---|---|
| **ALTA** | 12 | **100,0 %** |
| MEDIA | 12 | 83,3 % |
| **BAJA** | 6 | **66,7 %** |

**El sistema sabe cuándo no sabe.** Es el requisito para poder automatizar con garantías.

#### Política de actuación derivada

| Confianza | Casos | Acción |
|---|---|---|
| ALTA | 26,8 % | Correo generado automáticamente |
| MEDIA | 37,2 % | Proponer dos servicios alternativos |
| BAJA | 36,0 % | Derivar a una persona |

Esto materializa el diseño *human-in-the-loop* anunciado en la arquitectura: no como
principio declarativo sino como **umbral cuantificado** que determina cuándo el sistema
actúa por su cuenta y cuándo solicita intervención humana.

Conecta además con la advertencia de De Keyser et al. (2025) recogida en el marco teórico
sobre el deterioro de la relación comercial derivado de interacciones automatizadas de
baja calidad: el sistema automatiza el 27 % de los casos más claros y deriva el tercio que
requiere criterio.

#### Redacción para la memoria

> El emparejamiento entre servicios y empresas se resolvió mediante representaciones
> vectoriales multilingües, tras constatar la insuficiencia del método léxico (E17). El
> modelo asigna el servicio adecuado de forma coherente con el criterio experto —26 de 30
> empresas de alimentación perecedera se emparejan con el servicio de vida útil— si bien
> las similitudes absolutas presentan escasa dispersión (0,717–0,861). La normalización por
> fila permite derivar una medida de confianza cuya validez se verifica empíricamente: en
> los casos de confianza alta el acierto es del 100 %, frente al 66,7 % en los de confianza
> baja. Dicha medida fundamenta la política de intervención humana del agente.

---

### E19 · A5 · Generación de correos y control de la métrica de fundamentación

**Fecha:** 28-09-2026
**Script:** `scripts/F5_A5_E19_generar_correos.py` (Colab, GPU T4) · `A5_generar_correos.ipynb`
**Modelo:** Qwen2.5-7B-Instruct, cuantizado a 4 bits, temperatura 0,7
**Muestra:** 40 empresas con texto web, emparejadas por el método semántico de E18
**Salida:** `datos/03_resultados/a5_correos.csv`

#### Pregunta

Un LLM abierto al que se le entrega como única evidencia el texto de la web de una
empresa y la ficha de un servicio, ¿escribe un correo de contacto que se sostenga sobre
esa evidencia, o rellena con afirmaciones inventadas?

#### Resultado · cumplimiento de restricciones

| Restricción | Cumplimiento |
|---|---|
| Longitud máxima 140 palabras | 100 % (media 76, rango 37–101) |
| Termina con una pregunta | 100 % |
| Formato `Asunto:` / `Cuerpo:` | 100 % |
| **No menciona servicios que Empresa no ofrece** | **100 % (0 casos)** |

El indicador que mide el riesgo comercial real —ofrecer algo que el instituto no hace—
sale limpio en las 40 generaciones.

#### El problema de la métrica de fundamentación, y su control

La fundamentación media fue del **34,8 %**. Leída en bruto, sugeriría que dos tercios de
cada correo es invención. **Es una lectura falsa**, y conviene explicar por qué porque
afecta a cómo debe presentarse esta métrica en la memoria.

La métrica cuenta qué proporción del vocabulario del correo aparece en la evidencia. Pero
un correo en castellano contiene inevitablemente léxico que ninguna web de empresa
contiene: *ayudar*, *actual*, *durante*, *garantizar*, *explorar*, *interesaría*. Esas
palabras se contabilizan como «no respaldadas» sin ser afirmaciones sobre nada.

**La métrica carece de punto de referencia.** Un porcentaje solo significa algo comparado
con otro. El control adecuado es evaluar cada correo contra la web de **otra empresa
elegida al azar**: si la puntuación no baja, la métrica no mide fundamentación sino
solape de castellano corriente.

| Evaluación | Fundamentación |
|---|---|
| Correo contra **su** web | **34,84 %** |
| Correo contra la web de **otra** empresa (2.000 permutaciones) | 28,77 % ± 1,27 |
| Diferencia | **+6,07 puntos** (z = 4,76; p < 0,0005) |

**Interpretación.** El suelo de la métrica para prosa comercial en castellano es ≈29 %.
La diferencia de 6 puntos es la señal real de anclaje, y es estadísticamente
inequívoca: en 2.000 permutaciones ninguna alcanzó el valor observado. Pero es una
diferencia **modesta**: el correo se apoya en la web más de lo que lo haría por azar, y
no mucho más.

> **Para la memoria.** Una métrica sin control es un número sin significado. El mismo
> 34,8 % admite la lectura «dos tercios inventados» y la lectura «significativamente por
> encima del azar», y solo la permutación distingue cuál es correcta. El procedimiento
> —permutar el emparejamiento y volver a medir— es aplicable a cualquier métrica de
> fundamentación y debería acompañarla siempre.

#### Defectos de redacción detectados

La verificación automática no los captura, porque no son invenciones sino fallos de
oficio. Se detectan leyendo:

| Defecto | Frecuencia | Ejemplo |
|---|---|---|
| Marcador de plantilla sin rellenar | 7,5 % | «[Tu Nombre]», «[Su Nombre]» |
| Firma inventada | 12,5 % | El modelo se despide como si fuera una persona concreta |
| **Se delata leyendo la web** | **15,0 %** | «Leer su descripción, me llamó la atención…» |
| Inversión de papeles | casos aislados | A un fabricante de cintas aislantes: «*nuestras* cintas vinílicas» |
| Calcos y palabras inexistentes | casos aislados | «characterización», «soluciones insulatorias» |

El más dañino comercialmente es el tercero: el correo revela que quien escribe ha leído
la web en lugar de conocer a la empresa, que es exactamente la impresión que un primer
contacto debe evitar.

La inversión de papeles es cualitativamente distinta de las demás: el modelo atribuye a
Empresa los productos del cliente. No es un error de estilo sino de comprensión de quién
habla, y la verificación por solape de vocabulario **no puede detectarlo** —las palabras
están todas respaldadas, solo que asignadas al sujeto equivocado.

#### Un caso que revela el límite del emparejamiento

A EMPRESA DE PORCELANA INDUSTRIAL (ejemplo) (fabricante de aisladores cerámicos) se le propuso
caracterización de materiales de envase. El correo intenta resolver el desajuste por
escrito —«cómo nuestras soluciones podrían complementar sus aisladores»— pero la
propuesta no encaja. El emparejamiento se clasificó como confianza MEDIA.

Esto confirma la política de confianza de E18 desde el otro extremo: **un emparejamiento
flojo no se arregla escribiendo mejor**. La calidad del correo está acotada por la del
emparejamiento que lo precede, y ningún modelo de generación compensa esa cadena.

#### La fundamentación no varía con la confianza del emparejamiento

| Confianza | n | Fundamentación |
|---|---|---|
| ALTA | 6 | 30,9 % |
| MEDIA | 17 | 36,6 % |
| BAJA | 17 | 31,0 % |

No hay relación monótona. Era esperable: la fundamentación mide si el correo se apoya en
la web, no si el servicio propuesto es el adecuado. **Son dos fallos independientes** y
necesitan dos verificaciones distintas. Un correo perfectamente anclado en la web de la
empresa puede ofrecer el servicio equivocado con total coherencia interna.

#### Conclusión

El agente cumple las restricciones duras —longitud, formato, y sobre todo no ofrecer
servicios inexistentes— y se ancla en la evidencia por encima del azar de forma
estadísticamente inequívoca, aunque con margen modesto. Los defectos que quedan son de
redacción y de comprensión de papeles, no de invención de hechos.

**Valoración de alcance:** suficiente para la versión simple que el TFM declara para A5
(ver alcance en `00_SECUENCIA_SDR.txt`). No es un sistema desplegable sin revisión
humana, y el trabajo no lo afirma.

> **Redacción sugerida.** «La generación con un LLM abierto cumple el 100 % de las
> restricciones duras, incluida la de no ofrecer servicios ajenos al catálogo. El anclaje
> en la evidencia se verifica mediante un control por permutación: los correos puntúan
> 34,8 % frente a un suelo de 28,8 % al evaluarlos contra webs ajenas (z = 4,76;
> p < 0,0005). Los defectos residuales son de redacción —marcadores sin rellenar,
> referencias explícitas a la lectura de la web— y no de fabricación de hechos.»

---

### E20 · A5 · Correos de campaña: personalización frente al correo genérico real

**Fecha:** 28-09-2026
**Script:** `scripts/F5_A5_E20_campana.py` · `A5_correos_campana.ipynb` (Colab, GPU T4)
**Modelo:** Qwen2.5-7B-Instruct, 4 bits, temperatura 0,6, un ejemplo resuelto
**Campaña:** C01 · PPWR (`12_CAMPANAS.md`)
**Muestra:** las mismas 40 empresas de E19
**Salida:** `datos/03_resultados/a5_campana_C01.csv`

#### Pregunta

No «¿escribe bien el modelo?», que es blanda, sino la que importa al negocio:

> ¿Personalizar automáticamente aporta algo frente a mandar el mismo correo a todos?

La línea base no es un modelo tonto: es **el correo real que el departamento de marketing
de Empresa lanzó en septiembre de 2026**, escrito por una persona y enviado idéntico a
todas las empresas. Es una base exigente, y es la práctica que el agente tendría que
sustituir.

#### Resultado 1 · La estructura queda resuelta

El defecto que motivó el rediseño —correos sin saludo ni despedida, que ninguna persona
escribiría— desaparece:

| | v1 (E19) | Campaña |
|---|---|---|
| Tiene saludo | 7,5 % | **100 %** |
| Tiene despedida | 12,5 % | **100 %** |
| Agradece la atención | 5,0 % | 86,2 % |
| Tutea (tono de la casa) | — | **100 %** |
| Marcador «[Tu Nombre]» sin rellenar | 7,5 % | **0 %** |
| **Se delata leyendo la web** | **15,0 %** | **0 %** |
| Longitud media | 76 palabras | 209 palabras |

Los dos tics que más dañaban el correo desaparecen por completo. La causa era el prompt y
no la capacidad del modelo: bastó dar la estructura por partes, un ejemplo resuelto y la
prohibición explícita de cada tic.

#### Resultado 2 · La personalización supera al genérico, con dos controles

| Medida | Valor |
|---|---|
| Personalización de los correos generados | **5,06 %** |
| Personalización del correo genérico de Empresa | 1,29 % ← suelo real, medido |
| Diferencia | **+3,77 puntos (×3,9)** |
| Control por permutación (correo contra otra web, n = 2.000) | 3,04 % ± 0,58 |
| z / p | **3,50 / p = 0,001** |

Los dos controles responden a preguntas distintas y hacen falta los dos. El genérico dice
**cuánto hay que superar**; la permutación dice **si lo específico es de esa empresa** o
simplemente vocabulario que encajaría con cualquiera.

**Redundancia entre correos** (Jaccard sobre términos de contenido):

| | Parecido medio entre pares |
|---|---|
| Correo genérico actual | **1,000** (es literalmente el mismo) |
| Correos generados | **0,486** |

La mitad del contenido de cada correo es distinta de la de los demás, y esa diferencia
está anclada en la web de cada empresa (p = 0,001). El agente no está reescribiendo el
brief con otras palabras.

**Matiz que conviene declarar:** el 31 % de los correos personaliza *por debajo* del
genérico. La media favorable esconde una tercera parte de correos que no aportan nada
sobre lo que ya se manda hoy.

#### Resultado 3 · La abstención funciona, y falla de una forma muy concreta

El agente se abstuvo en el **27,5 %** de los casos (11 de 40). Revisadas una a una:

| Categoría | n | Casos |
|---|---|---|
| Abstención correcta | 7 | Universidades (2), transporte, agua municipal, gestora de activos, microfluídica, regeneración de suelos |
| **Error conceptual** | 1 | **EMPRESA DE HELADOS (ejemplo)** (helados) |
| Fallo del texto web, no del modelo | 3 | EMPRESA DE PANADERÍA (ejemplo), EMPRESA VINÍCOLA (ejemplo), EMPRESA DE PRODUCTO SANITARIO (ejemplo) |

Y en sentido contrario, escribió a tres empresas que el brief excluye: un transportista de
contenedores, una consultora de proyectos europeos y una empresa de hormigón.

#### El hallazgo: confunde el producto con su envase

Los dos errores más graves son **el mismo error en direcciones opuestas**:

| Caso | Qué razonó | Por qué está mal |
|---|---|---|
| **EMPRESA DE HELADOS (ejemplo)** (helados, marca conocida) | «no fabrica envases, no le afecta» → se abstiene | Llena envases alimentarios. Es el perfil exacto de PFAS y contacto con alimentos. La abstención más cara de las once |
| **EMPRESA DE HORMIGÓN (ejemplo)** (hormigón) | Aplica la reciclabilidad EN 13430 «a los betones y hormigones» → escribe | El PPWR regula el **envase**, no el producto. Inventa un requisito que no existe |

El modelo no distingue entre *fabricar envases* y *poner producto envasado en el mercado*.
Es una distinción central del reglamento, y es exactamente el tipo de conocimiento que el
trabajo viene sosteniendo que hay que **aportar** en lugar de esperar que se infiera (H1).

El brief sí lo decía —«quien los fabrica, quien los transforma y **quien los llena con su
producto**»— pero el modelo se quedó con el primer verbo. **El conocimiento estaba escrito
y aun así no se aplicó**, lo que acota el alcance de la solución «ponlo en el brief»: no
basta con declararlo, hay que declararlo de forma que resista la lectura del modelo.

Como contraste, EMPRESA DE CEMENTO (ejemplo) sí lo razonó bien: «puede afectar indirectamente a través
de los envases utilizados en la distribución». El saco de cemento es un envase. La
capacidad existe; lo que falta es consistencia.

#### El hallazgo secundario: tres de cada once abstenciones son fallos de datos

| Empresa | Qué se descargó de su web |
|---|---|
| EMPRESA DE PANADERÍA (ejemplo) | Un muro anti-bot: «Protección Anti-DDoS, verificación del dispositivo» |
| EMPRESA VINÍCOLA (ejemplo) | Un menú de Joomla sin contenido |
| EMPRESA DE PRODUCTO SANITARIO (ejemplo) | La web de otra empresa distinta (cargadores y mandrilado) |

En los tres casos **el modelo razonó correctamente sobre lo que se le dio**. El fallo está
aguas arriba: en el scraping (C2, C3) y en las URL del CRM.

> **Para la memoria.** Al evaluar un agente conviene separar los fallos de razonamiento de
> los fallos de la evidencia que se le entrega. De once abstenciones, siete son correctas,
> tres son achacables a los datos y solo una es un error del modelo. Atribuir las once al
> agente daría una tasa de error del 27 % cuando la real es del 9 %, y llevaría a intentar
> arreglar el componente equivocado.

#### Conclusión

Personalizar automáticamente **supera de forma medible** al correo genérico: casi cuatro
veces más contenido específico de cada empresa (p = 0,001) y la mitad del texto distinto
entre correos, con la estructura y el tono de la casa resueltos al 100 %.

La decisión de a quién escribir **no está resuelta**: 4 errores de decisión sobre 40, con
coste asimétrico —una abstención equivocada es un cliente perdido, y EMPRESA DE HELADOS (ejemplo) es
precisamente eso—. El agente no es desplegable sin revisión sobre esa decisión, y el
trabajo no lo afirma.

> **Redacción sugerida.** «La generación personalizada mediante un LLM abierto supera al
> correo genérico de la organización en contenido específico por empresa (5,06 % frente a
> 1,29 %; ×3,9), con anclaje verificado por permutación (z = 3,50; p = 0,001) y una
> redundancia entre correos de 0,486 frente a 1,000 del genérico. La decisión de
> pertinencia presenta en cambio 4 errores sobre 40, concentrados en una confusión
> sistemática entre el producto de la empresa y su envase.»

---

### E21 · A3 · Árboles frente a redes neuronales en datos tabulares (RQ2b)

**Fecha:** 29-09-2026
**Script:** `scripts/F3_A3_E21_arboles_vs_redes.py`
**Datos:** 3.013 cuentas valoradas · 2.259 entrenamiento / 754 prueba · 3.065 variables
**Cierra:** la medición pendiente **M4**, anotada el 27-09-2026

#### Por qué se hizo

El documento `06_MODELOS_POR_AGENTE.md` contenía un párrafo redactado para la memoria que
afirmaba que la elección de modelos de árboles estaba *«verificada experimentalmente […]
donde una red neuronal densa equivalente obtuvo un rendimiento inferior»*.

**Esa verificación no se había realizado.** El párrafo se escribió anticipando un
experimento que quedó pendiente, y de haberse trasladado a la memoria habría afirmado una
medición inexistente. Se detectó al redactar el apartado 4.2.5.

#### Diseño

Seis familias de modelos sobre **exactamente las mismas variables** y la misma partición
estratificada, de modo que la única diferencia entre ellas sea el modelo. A las redes se les
aplicó normalización de escala —que requieren y los árboles no— para no perjudicarlas.

#### Resultado

| Modelo | Aciertos | F1-macro | Segundos | Tamaño |
|---|---|---|---|---|
| Clase mayoritaria | 35,41 | 8,72 | 0,0 | — |
| Regresión logística | 40,05 | 43,37 | 8,2 | 18.390 coeficientes |
| **Random Forest** | **51,33** | **54,12** | **2,4** | 400 árboles |
| Potenciación del gradiente | 49,20 | 50,80 | 133,5 | 1.200 árboles |
| Red neuronal densa (2 capas) | 45,23 | 46,43 | 11,1 | 400.896 pesos |
| Red neuronal profunda (3 capas) | 44,96 | 46,60 | 20,4 | 825.984 pesos |

**El mejor árbol supera a la mejor red en 7,52 puntos de F1-macro, entrenando 8,5 veces más
rápido y con un modelo inspeccionable.**

#### Interpretación

El resultado respalda la elección de modelos de árboles para A3 y convierte una
justificación bibliográfica en un dato propio. Las razones estructurales que aduce la
literatura —variables heterogéneas, ausencia de orden o vecindad entre columnas, relaciones
escalonadas, robustez a variables poco informativas— se manifiestan aquí con claridad.

Merece atención que la **potenciación del gradiente quede por debajo del bosque aleatorio** y
tarde 55 veces más. Con 3.065 variables, la mayoría procedentes del TF-IDF del texto web, el
bosque aleatorio se beneficia de muestrear variables en cada división, mientras que la
potenciación secuencial sufre la dimensionalidad. No se había anticipado.

#### Dos salvedades que hay que declarar

**1 · No es comparable con E14 en cifras absolutas.** Esta ejecución incluye la nota T
(administraciones, asociaciones y centros tecnológicos), que E14 excluyó: 6 clases frente a
5, y 3.013 cuentas frente a 2.874. Por eso el bosque aleatorio obtiene aquí 54,12 de
F1-macro y en E14 obtenía 47,35. **La comparación entre familias, que es el objeto del
experimento, sí es válida**: todas ven exactamente los mismos datos.

**2 · No demuestra una tesis general.** El resultado vale para este conjunto de variables y
este volumen (unos 3.000 casos). No demuestra que las redes neuronales sean peores en datos
tabulares en general, solo que aquí no compensan. La afirmación general corresponde a la
literatura citada, no a este experimento.

> **Redacción sugerida.** «La elección de modelos de árboles para los componentes tabulares
> no se justifica únicamente por la literatura, sino que se verificó sobre los propios datos:
> entrenadas seis familias de modelos sobre variables y particiones idénticas, el bosque
> aleatorio superó a la mejor arquitectura neuronal en 7,52 puntos de F1-macro (54,12 frente
> a 46,60) con un coste de entrenamiento 8,5 veces menor.»

#### Nota metodológica

El experimento se diseñó admitiendo ambos desenlaces, y el script lo declara en su salida: si
la red hubiese resultado superior, habría que revisar la elección de modelo de A3 y corregir
`06_MODELOS_POR_AGENTE.md`. Un experimento cuyo resultado solo puede confirmar la hipótesis
previa no aporta información.

---

### Cuadro resumen · nivel sector, 41 clases

| Método | Aciertos | F1-macro |
|---|---|---|
| Responder siempre lo más común | 13,16 | 0,57 |
| LLM abierto zero-shot (Qwen2.5-7B) | 33,33 | 25,12 |
| LLM abierto few-shot (20 ejemplos) | 34,67 | 24,37 |
| LLM abierto Salamandra-7B zero-shot ⚠️ | 16,00 | 11,81 |
| Supervisado · TF-IDF + SVM | 48,49 | 40,16 |
| **Supervisado · regresión logística** | **48,91** | **41,89** |
| Transformer · solo nombre | 36,24 | 26,80 |
| Transformer · sin ponderación por clase | 50,79 | 34,39 |
| Transformer · con cabeza jerárquica | 50,98 | 41,43 |
| **Transformer sin jerarquía (MODELO FINAL)** | **51,73** | **43,38** |

---

---

### E22 · F6 · ¿Bastan cincuenta correos reales para poner en marcha A6?
**Fecha:** 30-09-2026 · 52 correos exportados del buzón general · script
`F6_A6_corpus_correos.py`

**Pregunta.** La autora exportó unos cincuenta correos reales. ¿Sirven para
entrenar y poner en marcha el agente de recepción?

**Planteamiento.** La pregunta no admite un sí o un no, porque A6 tiene cuatro
piezas y cada una necesita una cosa distinta. Dos son reglas y no se entrenan;
una se entrena con etiquetas que ya existen en el CRM; solo la cuarta depende
de estos correos.

#### Qué hay en el corpus

| | |
|---|---|
| Correos con cuerpo útil | **52** |
| Longitud media | 169 palabras (mediana 150) |
| Idioma | 41 español (79 %) · 11 inglés (21 %) |
| Dominio de empresa | 48 (92 %) |
| Dominio genérico (gmail y similares) | 4 (8 %) |
| Empresas distintas | 45 |

#### Resultado 1 · La resolución por dominio se confirma

| | 8 entradas | **52 correos** |
|---|---|---|
| Resueltas por dominio exacto | 2/8 · 25 % | **14/48 · 29,2 %** |
| Intervalo de confianza al 95 % | [7,1 %, 59,1 %] | **[18,2 %, 43,2 %]** |

El intervalo pasa de 52 puntos de ancho a 25. La estimación anterior no estaba
equivocada, simplemente no decía nada. La cobertura del campo Sitio web en el
CRM se reproduce exacta: **70,0 %**, el techo estructural declarado.

#### 🔑 Resultado 2 · El diccionario de normas cubre la MITAD de lo que parecía

| | 8 entradas | **52 correos** |
|---|---|---|
| Correos con norma reconocida | 7/8 · **88 %** | **23/52 · 44,2 %** |
| Intervalo de confianza al 95 % | [53 %, 98 %] | **[31,6 %, 57,7 %]** |

**Es el hallazgo del experimento y obliga a corregir una cifra publicada.** Con
ocho ejemplos el diccionario parecía resolver casi todo; con cincuenta y dos
resuelve menos de la mitad. El 88 % estaba dentro del intervalo del 44 %, así
que no hubo error de cálculo: hubo una muestra pequeña y optimista.

El 56 % restante son correos que piden algo **sin nombrar la norma que lo
regula**. Ese es exactamente el trabajo que un diccionario no puede hacer y que
justifica un clasificador.

Reparto por área entre los que sí citan norma: químico y procesos 11,
envases y economía circular 9, caracterización y embalajes 4, compostabilidad 4.

#### Resultado 3 · La clase negativa está casi vacía, y por una razón de fondo

Solo **9 de 52** llevan alguna señal de no ser una solicitud comercial, y seis
de las nueve vienen de la palabra «proveedor», que también aparece en correos
perfectamente comerciales. El recuento real de negativos es menor.

**El motivo no es el tamaño de la muestra, es de dónde sale.** Lo exportado son
correos que ya se habían considerado interesantes; los que no lo eran nunca
llegaron a esa carpeta. Es un sesgo de selección y no se corrige exportando más
correos del mismo sitio: hay que exportar del buzón sin filtrar.

#### Conclusión

| Pieza de A6 | Cómo funciona | ¿Bastan 52 correos? |
|---|---|---|
| Resolver la identidad | reglas | **Sí**, y queda medida |
| Detectar la norma citada | diccionario | **Sí**, y queda medida (a la baja) |
| Enrutar al área técnica | se entrena | Como conjunto de **prueba**, no de entrenamiento |
| Separar lo comercial de lo que no | se entrena | **No**, y no por el tamaño sino por el sesgo |

**Bastan para poner el agente en marcha y para medir tres de sus cuatro piezas.**

#### Redacción sugerida para la memoria

> La ampliación del corpus de entradas de ocho a cincuenta y dos casos reales
> permitió estrechar los intervalos de confianza y corrigió a la baja una de las
> cifras reportadas: la cobertura del diccionario de normas pasó del 88 %
> estimado sobre ocho casos al 44,2 % medido sobre cincuenta y dos (IC 95 %
> [31,6 %, 57,7 %]). La primera estimación no era errónea —el valor posterior
> queda dentro de su intervalo— sino que procedía de una muestra insuficiente
> para sostenerla. La resolución de identidad por dominio, en cambio, se
> confirmó: 29,2 % frente al 25 % estimado inicialmente.


---

### E23 · F6-F7-F8 · ¿Alcanzan 52 correos para montar la cadena de entrada?
**Fecha:** 30-09-2026 · script `F6_A7_A8_viabilidad_cadena.py`

**Pregunta.** ¿Se puede construir A6 (recibir), A7 (cualificar) y A8 (emparejar
servicio y redactar el briefing) con los cincuenta y dos correos reales?

**Reformulación.** La pregunta «¿bastan para entrenar?» solo se aplica a las
piezas que se entrenan, y son la minoría. Cuatro de las cinco piezas de la
cadena se resuelven con reglas, con extracción mediante un modelo de lenguaje
sin ajustar, o con representaciones densas: ninguna necesita ejemplos
etiquetados para *existir*, solo para *medirse*. Es el mismo patrón que A5, que
generó cuarenta correos sin entrenar nada.

#### Resultado 1 · Las etiquetas para entrenar el enrutado ya existen

| | |
|---|---|
| Oportunidades en el histórico | **4.881** |
| …con área técnica asignada | **4.362 · 89,4 %** |
| Reparto por área (codificada) | `AR01` 27,1 % · `AR02` 18,0 % · `AR03` 12,7 % · `AR04` 11,8 % · resto por debajo del 8 % |
| Tipos de oportunidad | Ensayos 46 % · Consultoría 29 % · I+D 16 % · resto 9 % |

Para entrenar el enrutado no hacen falta los correos. Lo que falta no es
volumen de entrenamiento: es **texto de entrada real con su respuesta**.

#### 🔑 Resultado 2 · El cuello de botella son las etiquetas de los correos, no los correos

| | |
|---|---|
| Correos con dominio de empresa | 48 |
| …resueltos contra una cuenta del CRM | 14 |
| …**y además con oportunidad etiquetada** | **8** |

Solo ocho correos traen su respuesta correcta puesta. Los otros cuarenta y
cuatro exigen etiquetado manual: leer y decir a qué área irían. **Es trabajo de
una tarde y convierte el corpus en conjunto de prueba de verdad.**

#### Resultado 3 · El correo no trae la ficha completa, y eso es un hallazgo de diseño

Cobertura de los siete criterios de cualificación sobre los 52 correos:

| Criterio | Correos | % |
|---|---|---|
| N · Necesidad | 38 | **73,1 %** |
| E · Encaje | 37 | **71,2 %** |
| P · Presupuesto | 25 | 48,1 % |
| D · Decisor | 19 | 36,5 % |
| C · Campeón | 19 | 36,5 % |
| P · Plazo | 15 | **28,8 %** |
| I · Impacto | 13 | **25,0 %** |

**Media: 3,2 de 7 criterios por correo.** Solo dos correos traen los siete;
cuatro no traen ninguno.

Lo relevante es *cuáles* faltan: impacto, plazo y presupuesto son precisamente
los que un comercial obtiene **preguntando**, no leyendo. La consecuencia de
diseño es que A7 no puede rellenar la ficha desde el primer mensaje, y no por
limitación del modelo sino porque la información no está. Lo que sí puede hacer
es rellenar la mitad que está y **generar las preguntas que faltan**, que es
exactamente lo que hace un SDR en la primera respuesta.

#### ⚠️ Resultado 4 · El emparejamiento con el catálogo no es fiable · resultado negativo

Ejecutado de verdad con `multilingual-e5-small`, el mismo modelo de E18, sobre
los 52 correos contra los 14 servicios del catálogo:

| | |
|---|---|
| Similitud del primer servicio | 0,843 de media |
| **Margen sobre el segundo** | **0,005** |
| Servicios distintos elegidos | 10 de 14, pero 24 de 52 caen en el mismo |

Un margen de 0,005 es un empate. Contraste sobre los 18 correos cuya área se
conoce con certeza porque citan una norma:

| | |
|---|---|
| Acierta en el primer puesto | 7/18 · **38,9 %** |
| El área correcta está en el top 3 | 10/18 · **55,6 %** |
| Suelo (elegir siempre el área más común del catálogo) | **14,3 %** |

**Supera al suelo casi tres veces, y aun así no es utilizable sin revisión.**
La conclusión operativa es que A8 no debe elegir un servicio: debe **proponer
tres y que decida una persona**, y aun así acierta poco más de la mitad de las
veces.

Causa probable, no medida: catorce servicios descritos en un dominio muy
homogéneo —casi todo es envase— dan descripciones que se parecen demasiado
entre sí. Es el mismo problema de fondo que E17 encontró con el emparejamiento
léxico, ahora confirmado también con representaciones densas.

#### Conclusión

| Pieza | Cómo se resuelve | ¿Alcanza? |
|---|---|---|
| A6 · recibir y enrutar | reglas + diccionario | **Sí**, medido: 29 % por dominio, 44 % por norma |
| A7 · cualificar | extraer con un LLM, sin entrenar | **Sí, parcialmente**: 3,2 de 7 criterios |
| A8 · emparejar servicio | representaciones densas | **No de forma fiable**: 39 % top-1 |
| A8 · redactar el briefing | generar con un LLM, sin entrenar | **Sí**, mismo patrón que A5 |
| A6 · comercial / no comercial | clasificador entrenado | **No**: clase negativa vacía |

**Se puede montar la cadena entera y medirla. Lo que no se puede es dejarla sin
una persona al final**, y los datos dicen exactamente en qué paso: el
emparejamiento con el servicio.

#### Redacción sugerida para la memoria

> La viabilidad de la cadena de entrada se evaluó componente a componente,
> distinguiendo los que requieren entrenamiento supervisado de los que se
> resuelven mediante reglas o mediante modelos preentrenados sin ajuste. De las
> cinco piezas identificadas, cuatro pertenecen al segundo grupo y no dependen,
> por tanto, del volumen del corpus. El análisis situó dos limitaciones
> concretas: los mensajes entrantes contienen de media 3,2 de los siete
> criterios de cualificación, faltando sistemáticamente los relativos a impacto,
> plazo y presupuesto —los que se obtienen preguntando—; y el emparejamiento
> semántico con el catálogo de servicios alcanza un 38,9 % de acierto en primera
> posición frente a un suelo del 14,3 %, insuficiente para operar sin revisión
> humana pese a superar claramente el azar.


---

### E24 · F8 · Por qué falla el emparejamiento con el catálogo
**Fecha:** 30-09-2026 · script `F6_A8_diagnostico_emparejador.py`

**Motivo del experimento.** En E23 atribuí el fallo del emparejador a que «los
servicios se describen de forma demasiado parecida entre sí», y lo escribí
declarando que no lo había medido. La autora preguntó exactamente por eso. Se
midió, y **la explicación era falsa**.

Se plantearon tres hipótesis y se contrastaron las tres.

#### A · ¿Se parecen demasiado los servicios entre sí? → **NO**

| | |
|---|---|
| Similitud media entre dos servicios distintos | 0,866 |
| Pareja más confundible | dos servicios del mismo ámbito · 0,929 |
| **Cada servicio recupera su propia ficha usando su descripción** | **14 de 14 · 100 %** |

El catálogo **sí** es separable. Dada la descripción de un servicio, el modelo
lo distingue de sus trece hermanos sin un solo fallo. La hipótesis que yo había
dado por buena queda refutada.

#### B · ¿Es que el correo viene difuso? → **NO, y va en contra**

| | Correo entero | Solo la frase de la petición |
|---|---|---|
| Acierto en 1.ª posición | 7/18 · 39 % | **2/18 · 11 %** |
| Acierto en top 3 | 10/18 · 56 % | 7/18 · 39 % |

Recortar el correo a la petición **empeora** el resultado a la mitad.

#### C · ¿Piden varias cosas a la vez? → **Poco**

Solo 5 de 52 correos citan más de un área. No explica el fallo.

#### 🔑 La causa real: un desajuste de género, no de tema

| Comparación | Similitud media |
|---|---|
| correo ↔ correo | **0,872** |
| servicio ↔ servicio | 0,866 |
| **correo ↔ servicio** | **0,823** ← la más baja |

**Un correo se parece más a cualquier otro correo que al servicio que
literalmente está pidiendo.** El modelo no agrupa por tema: agrupa por **género
de texto**. Por un lado los correos, con su saludo, su petición y su despedida;
por otro las fichas de catálogo, con lenguaje de servicio. La distancia entre
esos dos registros es mayor que la distancia entre temas dentro de cada uno.

Eso explica también por qué recortar el correo lo empeora: al quitar contexto se
pierde vocabulario temático y queda proporcionalmente más fórmula epistolar.

**Nota metodológica sobre los cosenos.** Ninguno de estos valores absolutos
significa «muy parecido». Este modelo comprime todo en la banda 0,75–0,93, de
modo que dos textos sin relación parten ya de 0,8. Lo único que informa es el
orden, y el orden se decide por milésimas: el margen entre el primer servicio y
el segundo es de 0,005.

#### Qué se deduce

No hay que reescribir el catálogo. Hay que **dejar de comparar un correo con una
ficha**. El paso que falta es traducir la petición al registro del catálogo: que
A7 extraiga la necesidad como enunciado técnico breve —«migración de PFAS en
caja de cartón ondulado impresa»— y emparejar *eso*. Deja de ser correo contra
ficha y pasa a ser ficha contra ficha, que es justo lo que el contraste A
demuestra que el modelo resuelve sin fallos.

> **Esto no está medido.** Es la hipótesis que sale del diagnóstico, no un
> resultado, y comprobarla exige el modelo generativo, que necesita GPU. Queda
> registrada como **M5**. Se declara así para no repetir el error que originó
> este mismo experimento.

Vía alternativa e independiente: entrenar un clasificador de área con las 4.362
etiquetas del histórico. Ahí no existe el problema de género, porque no se
compara con nada: se predice.

#### Redacción sugerida para la memoria

> El análisis de las causas del bajo rendimiento del emparejamiento semántico
> descartó las dos explicaciones más inmediatas. El catálogo resultó plenamente
> separable —cada servicio recupera su propia ficha en primera posición, 14 de
> 14— y la reducción del mensaje a su frase de petición degradó el acierto del
> 39 % al 11 %. La comparación de las similitudes intragrupo e intergrupo situó
> la causa en otro lugar: los mensajes entrantes se asemejan más entre sí
> (0,872) y las fichas de servicio entre ellas (0,866) de lo que un mensaje se
> asemeja al servicio que solicita (0,823). La representación densa agrupa por
> género textual antes que por contenido temático, de modo que el emparejamiento
> directo entre dos registros distintos parte de una desventaja estructural que
> no procede del catálogo ni de la longitud del mensaje.


---

### E25 · F8 · ¿Hace falta `Tema` para A8? ¿Y sirve para lo que A8 tiene que hacer?
**Fecha:** 30-09-2026 · 4.351 oportunidades · script `F8_A8_utilidad_tema.py`

**Origen.** Al retirar la columna `Tema` de los ficheros de trabajo por
confidencialidad (X17) afirmé que no costaba nada «porque A8 nunca se
construyó». La autora preguntó lo evidente: entonces, ¿hace falta `Tema` para
construirlo? Se comprobó, y de paso se respondió una pregunta mayor que nadie
había hecho.

#### Respuesta 1 · Sí, es imprescindible, y no se ha perdido

El histórico de oportunidades no contiene **ningún otro campo de texto**: todo
lo demás son identificadores, fechas o las propias etiquetas que hay que
predecir. Sin `Tema`, el conjunto de entrenamiento de A8 está vacío.

Por eso no se borró. Está íntegro en la carpeta privada y el script de
preparación de A8 lee del fichero bruto. **Retirarlo de `01_limpio` no impide
construir A8: impide publicarlo**, que era justamente el objetivo.

#### 🔑 Respuesta 2 · El enrutado por área funciona, y con holgura

Clasificador sobre `Tema` → área técnica. Validación cruzada de 5 particiones,
13 áreas con 20 o más casos, 4.351 oportunidades:

| Método | Aciertos | F1-macro |
|---|---|---|
| Responder siempre lo más común | 27,12 % | — |
| **TF-IDF + máquina de vectores soporte** | **78,97 %** | **69,98** |

Desviación entre particiones: ±1,11. **Mejora sobre el suelo: +51,9 puntos.**

Un modelo lineal sin ajuste alguno separa las trece áreas. Es, con diferencia,
el resultado más limpio de todo el trabajo: la tarea que parecía la más difícil
—decidir qué unidad técnica atiende una necesidad— resulta ser la más
aprendible, porque las etiquetas existen, son abundantes y las escribió quien
sabía la respuesta.

#### ⚠️ Respuesta 3 · Pero ese 79 % es un techo optimista, no un rendimiento esperable

A8 se entrenaría con `Tema` —jerga interna del comercial, escrita **después** de
que exista la oportunidad— y se ejecutaría sobre lo que escribe **un cliente**,
en prosa, **antes** de que exista nada.

| Comparación | Similitud media |
|---|---|
| tema ↔ tema | 0,833 |
| correo ↔ correo | 0,872 |
| **tema ↔ correo** | **0,821** ← la más baja |

| | `Tema` | Correo de cliente |
|---|---|---|
| Longitud media | 34 caracteres | 1.099 caracteres |

**Un correo es 32 veces más largo y pertenece a otro registro.** Es el mismo
patrón que E24 encontró en el emparejador, aquí más leve pero presente.

**Lo que no se sabe:** cuánto cae ese 79 % al aplicarlo a texto de cliente. No
se puede medir porque solo ocho correos traen su área verdadera. Queda como
**M6**.

#### Consecuencia para la memoria

Si se reporta el 78,97 %, hay que declararlo como **rendimiento sobre la
población de entrenamiento, no sobre la de uso**. Es exactamente el mismo aviso
que ya llevan E14 (desajuste de población en `tamaño`) y E24. Sin esa
salvedad, la cifra promete algo que no está demostrado.

#### Redacción sugerida para la memoria

> El enrutado por área técnica resultó ser la tarea más aprendible del conjunto:
> un clasificador lineal sobre el asunto de la oportunidad alcanzó un 78,97 % de
> acierto y un F1-macro de 69,98 sobre trece áreas, frente a un 27,12 % de la
> clase mayoritaria, en validación cruzada de cinco particiones (±1,11). El
> resultado se explica por la naturaleza de las etiquetas: son abundantes,
> reales y las asignó quien conocía la respuesta. Debe reportarse, no obstante,
> con una salvedad de alcance: el texto de entrenamiento es el asunto redactado
> internamente tras crearse la oportunidad, mientras que el sistema operaría
> sobre el mensaje del cliente, un registro distinto y treinta veces más
> extenso. La cifra constituye por tanto un techo, no una estimación del
> rendimiento en explotación.


---

### E26 · F8 · Entrenar A8 sin usar el texto comercial tal cual
**Fecha:** 30-09-2026 · 4.351 oportunidades · script `F8_A8_tema_protegido.py`

**Origen.** Tras E25 la autora objetó que `Tema` sigue siendo información
restringida de la organización y preguntó si hay forma de protegerla y no
usarla tal cual. La objeción era correcta, y al comprobarla apareció una fuga
que no estaba contemplada.

#### 🔑 La fuga: guardar el fichero en privado no protege el modelo

Un TF-IDF con clasificador lineal **guarda su vocabulario entero dentro**:

| | |
|---|---|
| Términos almacenados en el modelo | **3.382** |
| Pesos (términos × áreas) | 43.966 |
| De los 386 términos más influyentes, no técnicos | 331 · **86 %** *(cota superior)* |
| …y que además aparecen en **5 asuntos o menos** de 4.351 | 183 · **47 %** |

Ese 47 % es el indicador que importa. Un término que pesa mucho en la decisión
y aparece en tres asuntos de entre cuatro mil no es vocabulario del sector: es
de un cliente concreto, y reidentifica.

**Y la forma natural de explicar un modelo lineal en una memoria es
precisamente una tabla de «términos más influyentes por área».** Publicarla
habría publicado el vocabulario comercial de la organización, marcas de
terceros incluidas, con el fichero de datos perfectamente guardado en privado.

Es el mismo tipo de error que X7: la información no se escapa por donde se está
mirando.

#### Las tres protecciones, con su coste medido

Validación cruzada de 5 particiones, mismas condiciones que E25:

| Variante | Aciertos | ± | F1-macro | Coste |
|---|---|---|---|---|
| 0 · Sin proteger (E25) | 78,97 % | 1,11 | 69,98 | — |
| A · Entidades nombradas filtradas | 67,89 % | 1,20 | 55,48 | **−11,08** |
| **B · Huella digital, sin vocabulario** | **80,51 %** | 1,28 | **72,84** | **+1,54** |
| C · Las dos | 69,18 % | 1,24 | 56,78 | −9,79 |
| *Responder siempre lo más común* | *27,12 %* | | | |

**Filtrar los nombres propios cuesta once puntos.** Elimina 1,3 de cada 5
palabras y deja 130 asuntos vacíos: se lleva por delante demasiada señal.

**La huella digital no cuesta nada.** El modelo pasa a tener **cero términos
almacenados** —no hay tabla de vocabulario que publicar, ni por descuido— y el
acierto no baja; la diferencia de +1,54 queda dentro del margen entre
particiones y se atribuye a que el vectorizador por huella no descarta términos
poco frecuentes, no a una mejora real del método.

#### Decisión

**Variante B**, combinada con las dos medidas ya tomadas:

1. El texto de origen vive fuera del proyecto *(X17)*
2. El modelo se entrena con representación por huella digital, sin vocabulario
3. La memoria **no incluye ninguna tabla de términos influyentes**

#### Dos precisiones que hay que escribir sin adornos

**La huella digital es ocultación, no cifrado.** El modelo no contiene
palabras, pero quien dispusiera de una lista de candidatas podría calcular su
huella y consultar el peso. Protege frente a la publicación descuidada y la
lectura casual —que es el riesgo real en un TFM— y no frente a un atacante
decidido. Declararlo así es parte de hacerlo bien.

**Ninguna variante sustituye a sacar el origen del proyecto.** Son medidas
independientes y hacen falta las dos.

#### Redacción sugerida para la memoria

> El asunto de la oportunidad constituye información comercial de la
> organización, por lo que el clasificador de enrutado no se entrenó sobre el
> texto en claro. Se evaluaron tres tratamientos: el filtrado de entidades
> nombradas, la representación mediante huella digital sin vocabulario
> almacenado, y su combinación. El filtrado resultó inviable —una caída de
> 11,08 puntos de acierto, al eliminar una de cada cuatro palabras—, mientras
> que la representación por huella digital no supuso coste alguno (80,51 %
> frente a 78,97 %, diferencia comprendida en la variación entre particiones) y
> eliminó por completo el vocabulario del modelo. Se adoptó esta última. La
> medida es de ocultación y no de cifrado, y se combina con la conservación del
> texto de origen fuera del entorno del proyecto y con la omisión deliberada de
> cualquier tabla de términos influyentes en esta memoria.


---

### E27 · F9 · El agente A9 ya existe, y no se había mirado
**Fecha:** 30-09-2026 · script `F9_A9_evaluar_prevision_existente.py`

**Origen.** La autora señaló que en su carpeta de trabajo hay un proyecto propio,
«Previsión de ventas», y preguntó si serviría de base para A9. La respuesta es que no
sirve *de base*: **es A9**, y está más desarrollado que cualquier agente del TFM.

#### Qué implementa realmente

Verificado leyendo el código, no la documentación. `prevision/modelo/curvas.py` implementa
**análisis de supervivencia con riesgos competitivos por el estimador de Aalen-Johansen**,
escrito a mano: función de supervivencia, dos funciones de incidencia acumulada, censura
por oportunidades aún abiertas, y la identidad S + CIF₁ + CIF₂ = 1 mantenida en todo
momento.

El diseño de A9 pedía literalmente *«un modelo que predice CUÁNDO se cerrará algo, no solo
SI se cerrará (análisis de supervivencia)»*. Es exactamente eso.

#### Madurez, comparada con el propio TFM

| | TFM (`scripts/`) | Proyecto de previsión |
|---|---|---|
| Ficheros de código | 36 | 43 |
| Líneas | 11.019 | **12.947** |
| Ficheros de test | **0** | 6 |
| Configuración externa | no | sí (`config.toml`) |
| Persistencia | ficheros sueltos | SQLite |
| Control de versiones | no | 8 commits |

**El proyecto está mejor construido que el conjunto de los agentes del TFM.** Conviene
decirlo sin rodeos: tiene capas, configuración externa, persistencia, registro de
ejecuciones y pruebas automáticas, y ninguno de los agentes del trabajo las tiene.

#### Fiabilidad, medida por su propia prueba hacia atrás

2.092 oportunidades, 1.754 ofertas, 64 semanas y 14 meses probados:

| Horizonte | Acierto |
|---|---|
| Mes completo · ofertas logradas | **83,3 %** |
| Próximas 4 semanas · ofertas logradas | 73,2 % |
| Próximas 4 semanas · oportunidad → oferta | 66,1 % |
| Semana 1 · ofertas logradas | 66,6 % |
| Semana 4 · ofertas logradas | 62,2 % |

*(Se omiten las filas de importes: decisión D13.)*

El deterioro al alejarse el horizonte es el esperable y está medido semana a semana, que es
más de lo que hace ningún agente del TFM.

#### 🔑 El análisis que más le interesa a este trabajo

El proyecto incluye un análisis aparte: **¿acierta el porcentaje de probabilidad que el
comercial escribe a mano en cada oferta?** Sobre 852 ofertas ya resueltas:

| | |
|---|---|
| **¿Ordenan bien?** AUC | **0,802** (IC 95 % [0,762, 0,841]) |
| Media de lo que declaran | 69,1 % |
| Lo que se logra de verdad | 84,3 % |
| **Error de calibración** | **15,2 puntos · pesimistas** |

Es el mismo contraste que E16 —criterio humano frente a métrica objetiva, con AUC e
intervalo— en otra fase del embudo. **Y separa dos propiedades que el TFM no llegó a
separar:**

- **Discriminación**: ordenar bien los casos. El comercial lo hace muy bien, AUC 0,802.
- **Calibración**: acertar el número. Lo hace mal, se queda 15 puntos corto.

Un modelo puede tener una sin la otra. En E16 solo se midió la primera. Es una carencia del
protocolo de evaluación del trabajo que este proyecto deja a la vista.

Nota de contraste: en E16 el criterio humano obtuvo AUC 0,638 y aquí 0,802. No se
contradicen —son tareas distintas: allí se valora una **cuenta** antes de cualquier
contacto, aquí una **oferta** ya en curso, con mucha más información disponible— pero la
comparación es en sí misma informativa.

#### Cobertura del diseño de A9

| Función pedida en el diseño | Estado |
|---|---|
| Vigilar el pipeline: qué avanza, qué está parado | ✅ |
| Predecir cuándo se cerrará, no solo si | ✅ |
| Análisis de supervivencia | ✅ |
| Alertas y próxima acción recomendada | ✅ |
| Recontactar los «ahora no» | ❌ |

Cuatro de cinco. La que falta es una regla sobre el pipeline, no un modelo.

#### ⚠️ Lo que hay que decidir, y no es técnico

**1 · Fechas.** El primer commit es del **15-09-2026** y el cuaderno del TFM arranca el
**21-09**. El proyecto es anterior. Si entra en la memoria hay que declararlo como trabajo
propio previo, no desarrollado para el trabajo. Ocultarlo sería un problema serio;
declararlo no lo es en absoluto.

**2 · Importes.** El proyecto prevé importes, y D13 excluyó toda variable monetaria del
TFM. O se revisa D13, o entra solo la parte de conversión y plazos.

**3 · Alcance.** Cubre cuatro laboratorios, no los once agentes.

**4 · Tiempo.** Quedan trece días y la memoria no está cerrada.

#### Recomendación

**Declararlo en el capítulo 7, con sus cifras, y no abrir un apartado 4.6.5 para A9.**

El motivo no es de esfuerzo. Es que lo que aporta este proyecto no es un quinto agente:
es **la prueba de que la arquitectura propuesta se sostiene fuera del marco del trabajo**.
Una fase diseñada sobre el papel en septiembre resultó estar ya implementada, en
producción y validada contra catorce meses de histórico, por la propia autora y sin
relación con el TFM. Eso vale más en las conclusiones y en las futuras líneas que como un
resultado más entre otros.


---

### E28 · A0 · El orquestador: el sistema secuencial, y lo que revela
**Fecha:** 30-09-2026 · 2.652 empresas · script `A0_orquestador.py`

**Qué es.** El componente que encadena los agentes construidos. Entra una empresa y sale
una fila con todo lo decidido sobre ella y el motivo de cada decisión. **Cierra el objetivo
específico 3**, el único que quedaba sin cumplir.

```
empresa
   ├─ A2 · clasificar el sector      → sector predicho
   ├─ A3 · puntuar la cuenta         → nota A-E   ← recibe el sector de A2
   ├─ A5 · emparejar servicio        → servicio + confianza
   └─ A5 · redactar                  → EN COLA (necesita GPU)
```

La redacción no se ejecuta: el modelo generativo exige GPU. No es una carencia, es el
**circuito por lotes** del apartado 7.2, y la cola que deja el orquestador es su entrada.
El resto corre entero en un portátil, como preveía esa arquitectura.

#### 🔑 Hallazgo 1 · La mayoría de los errores de A2 son inocuos

A3 recibe el sector que predijo A2, no el verdadero. Para medir el arrastre se puntuó cada
empresa dos veces, con el predicho y con el real:

| | Empresas | Cambia la nota de A3 |
|---|---|---|
| A2 acertó el sector | 1.372 | 0 · **0,0 %** |
| A2 falló el sector | 1.280 | 197 · **15,4 %** |
| **Total** | 2.652 | 197 · **7,4 %** |

**A2 acierta el 51,73 %, que suena mediocre, pero solo el 7,4 % de sus errores llega a
cambiar la decisión siguiente.** Cuando falla, la nota cambia en el 15,4 % de los casos: el
otro 84,6 % son confusiones entre sectores que A3 trata igual.

Es un resultado que **ningún agente aislado puede dar**. La métrica de A2 dice cuántas
veces se equivoca; solo la cadena dice cuánto importa equivocarse. Y matiza a la baja la
gravedad del resultado más flojo del trabajo.

#### 🔑 Hallazgo 2 · Encadenar destapa un desajuste de población que la evaluación aislada ocultaba

El orquestador compara, variable a variable, cuántos valores faltaban al entrenar A3 y
cuántos faltan en las empresas que entran:

| Variable | Nulos al entrenar | Nulos ahora |
|---|---|---|
| `tamaño` | 6,0 % | **62,0 %** |
| `asociado` | 71,7 % | **25,3 %** |
| `provincia` | 11,8 % | 36,6 % |

Y se ve la consecuencia: entre las cuentas de entrenamiento **sin** tamaño, el 61 % tenía
la nota T. El modelo aprendió «falta el tamaño → T», cierto en su población y falso en
esta. Resultado: predice T para el 61,7 % de las empresas entrantes.

| | Acierto | Suelo | Margen |
|---|---|---|---|
| A3 aislada, en su propia partición (E14) | 49,24 % | 37,13 % | **+12,1** |
| A3 encadenada, sobre la población de entrada | 44,1 % | 37,9 % | **+6,2** |

**Encadenar reduce a la mitad el margen sobre el suelo.** La limitación estaba declarada
desde E14, pero era una nota al pie; el orquestador la convierte en una cifra.

**La lección excede el caso: evaluar agentes por separado oculta fallos que solo aparecen
cuando reciben la entrada real del anterior.** Es el argumento más fuerte a favor de
construir el sistema y no quedarse en los componentes.

#### Hallazgo 3 · El embudo de la abstención

| Etapa | Empresas | Se pierden |
|---|---|---|
| Entran | 2.652 | — |
| A2 las clasifica | 2.652 | 0 |
| A3 les pone nota | 2.652 | 0 |
| Tienen texto web utilizable | 1.573 | −1.079 |
| El emparejamiento es de fiar (z ≥ 2,0) | 270 | −1.303 |
| **Llegan a la cola de redacción** | **270** | |

**Llega al final el 10,2 %.** Y no se pierde donde se esperaba: la mitad de las bajas son
por **falta de texto web**, un problema de datos que ningún modelo arregla, y la otra mitad
por la exigencia de confianza en el emparejamiento, coherente con el 38,9 % de acierto que
E24 midió para ese paso.

Cada empresa detenida lleva escrito su motivo. Un sistema que se detiene con razón escrita
no es un sistema que falla: es uno que sabe lo que no sabe.

#### Un error de implementación que conviene anotar

Al construirlo, `astype(str)` combinado con `dummy_na=True` generaba **dos columnas con el
mismo nombre** —una por el texto «nan» y otra por el indicador de nulo—, lo que hacía
imposible alinear las variables entre entrenamiento y uso. Falla de forma ruidosa, que es
lo mejor que puede pasar; si hubiera fallado en silencio habría desalineado las columnas y
el modelo habría predicho sobre variables equivocadas sin avisar.

#### Redacción sugerida para la memoria

> La integración de los agentes en un recorrido secuencial permitió medir dos propiedades
> inaccesibles a la evaluación por componentes. La primera es la propagación del error: de
> las 1.280 empresas en que la clasificación sectorial resultó incorrecta, solo en un
> 15,4 % se alteró la puntuación posterior, de modo que el 7,4 % del total de casos acusa
> el error del primer componente. La segunda es un desajuste de población que la evaluación
> aislada no revelaba: el margen del modelo de puntuación sobre su clase mayoritaria cae de
> 12,1 a 6,2 puntos al aplicarse sobre la población que le entrega el agente anterior, por
> una diferencia sustancial en la disponibilidad de la variable de tamaño entre ambas
> poblaciones. Del total de empresas, un 10,2 % completa el recorrido; el resto se detiene
> con el motivo registrado, mayoritariamente por ausencia de texto de la página web.


---

### E29 · A3 fase 2 · El ajuste de prioridad, incorporado al orquestador
**Fecha:** 01-10-2026 · 3.152 empresas · script `A0_orquestador.py`

**Qué se hizo.** La segunda fase de A3 se diseñó en `17_DISENO_A3_FASE2.md` y se incorporó
al recorrido **en su versión de tabla**, sin entrenar modelo alguno: emparejado el
servicio se conoce su tipo, y el cruce con la nota devuelve la conversión medida en E13.

| Prioridad | Empresas | % |
|---|---|---|
| Alta | 1.035 | 65,8 % |
| Media | 417 | 26,5 % |
| Baja | 121 | 7,7 % |

La cola de redacción sale ordenada: de las 270 que superan el umbral, 198 son de prioridad
alta.

#### De dónde sale cada cifra

| Origen | Casos |
|---|---|
| Celda medida (nota × tipo) | 668 |
| Media del tipo: la nota no está en el cruce | **828** |
| Conversión global del tipo | 77 |

#### 🔑 Dos salvedades, y las dos encadenan

**1 · El tipo lo predice A5, no lo pide el cliente.** E13 midió sobre lo que los clientes
solicitaron de verdad; aquí el tipo viene de un emparejamiento que acierta el 38,9 % (E24).
La prioridad hereda ese error. **Por la vía de entrada el problema no existe:** cuando el
cliente escribe, el tipo lo declara él, que es justamente por lo que D12 situó esta fase
entre F7 y F8.

**2 · Dos tercios no usan una celda medida.** La nota más predicha es T, y T no aparece en
el cruce de E13 porque en el histórico apenas hay administraciones solicitando servicios.
Es el desajuste de población de E28, dos pasos más abajo.

#### El caso que lo resume

El primer registro de la cola ordenada es **un ayuntamiento con prioridad alta para un
ensayo de vida útil**. Cada paso se defiende solo: nota T por falta de tamaño, ensayo
porque su web menciona alimentación, prioridad alta porque los ensayos convierten. El
resultado es absurdo.

**Tres componentes que superan su suelo por separado producen, encadenados, una decisión
que ninguno habría producido solo.** Es el argumento de E28 reducido a un caso.

#### Redacción sugerida para la memoria

> La incorporación de la segunda fase del agente de priorización permitió ordenar la cola
> de generación por prioridad estimada, empleando la relación medida entre valoración de
> cuenta y tipo de servicio sin necesidad de entrenar un modelo adicional. El resultado debe
> interpretarse, no obstante, con dos salvedades que ilustran el comportamiento de una
> arquitectura encadenada: el tipo de servicio procede de un emparejamiento con un 38,9 % de
> acierto en lugar de una declaración del cliente, y dos terceras partes de las asignaciones
> recurren al valor medio del tipo porque la valoración predicha no figura en la relación
> medida, consecuencia del desajuste de población documentado en el mismo apartado.


---

### E30 · A2 · La biblioteca de sectores ya existía, y ya había perdido
**Fecha:** 01-10-2026 · `F2_A2_E30_biblioteca_sectores.py`

**Por qué esta entrada se escribe tarde.** E30 se citaba en H29 y en dos lugares más como
evidencia, pero **no tenía entrada propia** en el cuaderno: quien siguiera la referencia no
encontraba nada. Se subsana el 04-10-2026.

**La pregunta, de la autora.** ¿Mejoraría la clasificación sectorial si al modelo se le
entregara una descripción de qué es cada sector, en lugar de que la deduzca de los
ejemplos? La idea tiene nombre en la literatura —descripciones de etiqueta— y encaja con la
tesis del trabajo: si el conocimiento de la casa no se deduce, hay que aportarlo.

#### Hallazgo 1 · La biblioteca ya estaba escrita

`taxanomia.json`, del proyecto anterior, contiene:

| | |
|---|---|
| Sectores de primer nivel | 39 |
| …con descripción propia | **0** |
| Subsectores descritos | 183 |
| Longitud media de la descripción | 90 caracteres |

Y no son etiquetas: llevan criterio de inclusión **y de exclusión**. El ejemplo de los
aceites dice «aceites vegetales comestibles; NO APLICA a aceites técnicos o cosméticos».
Eso es exactamente el conocimiento de la casa que RQ1 demuestra que un modelo general no
deduce, y estaba escrito desde antes de empezar.

**La asimetría que importa:** los 183 subsectores están descritos; los 39 sectores, no. Y
el sector es justo lo que A2 predice.

#### Hallazgo 2 · Y ya se había probado, en el *prompt* de un modelo cerrado

La evaluación de marzo de 2026 puso la biblioteca en el *prompt* del modelo cerrado y
midió **39,87 %** de acierto sectorial, frente al 51,73 % del clasificador supervisado:
unos doce puntos por debajo. La bitácora ya registraba un 40,47 % para ese mismo
experimento.

> ⚠️ **ESTA CIFRA NO ES REPRODUCIBLE HOY.** El fichero del que salía
> —`PRUEBA 1/OUTPUT/evaluacion_openai_resumen.xlsx`— **ya no está en esa carpeta**, que
> contiene ahora ejecuciones posteriores. El script E30 se detiene al no encontrarlo. El
> 39,87 % se conserva porque estaba registrado antes de que el fichero desapareciera, y
> **se declara como dato histórico no verificable**, no como medición propia de este
> trabajo. Si aparece el fichero, vuelve a serlo.

**Salvedad de comparabilidad, además.** Las dos evaluaciones no usan la misma partición: la
del modelo cerrado es de marzo sobre 602 casos y la de A2 es de septiembre sobre 2.652. La
diferencia indica un orden de magnitud, no una cifra exacta.

#### Hallazgo 3 · Una señal a favor que nadie había mirado

En aquella evaluación, el modelo acertaba **más** el subsector (183 clases, descritas) que
el sector (39 clases, sin describir). No es lo normal: a más clases, menos acierto. La
explicación más plausible es que el subsector sí tenía descripción.

**No está demostrado:** son dos espacios de etiquetas distintos y la comparación está
confundida por ese factor. Pero era la única evidencia disponible, y apuntaba a favor de
la idea. Por eso se probó la vía del entrenamiento (E31), y por eso el resultado negativo
de E31 tiene valor: refuta algo que la única señal disponible apoyaba.

**Qué se decidió.** Probar la vía que nadie había probado: meter las descripciones en el
**entrenamiento** del transformer, no en el *prompt*. Es E31, y también pierde.

---

### E31 · A2 · Dar al modelo la biblioteca de sectores **empeora** la clasificación
**Fecha:** 02-10-2026 · 2.652 casos de prueba · `F2_A2_E8_E10_transformer.py --biblioteca`

**La pregunta, de la autora.** El clasificador acierta el 51,73 %. ¿Mejoraría si en
lugar de deducir qué es cada sector solo a partir de ejemplos, se le entregara la
**descripción** de cada uno —qué es y por qué una empresa pertenece a él—?

La idea tiene respaldo en la propia tesis del trabajo: si el conocimiento de la casa
no se infiere (RQ1), la vía natural es aportarlo. Y la biblioteca existía ya: 38
sectores descritos con criterio de inclusión y de exclusión.

#### Diseño

Tres variantes sobre **el script original**, misma partición, misma semilla y mismos
hiperparámetros. La primera es la referencia y su función es validar el montaje.

| Variante | Qué cambia |
|---|---|
| Referencia | Nada. El modelo final actual |
| `inicial` | La capa de salida arranca con las descripciones codificadas y luego se mueve libremente |
| `fija` | La capa queda congelada en las descripciones: el modelo debe llevar el texto hasta ellas |

**Condición de validez cumplida:** la referencia dio 50,94 % frente al 51,73 %
publicado, una desviación de 0,79 puntos. La comparación entre variantes es legítima.

#### 🔑 Resultado: pierde, y pierde donde debía ganar

| Variante | Aciertos | F1-macro |
|---|---|---|
| **Referencia** | **50,94** | **41,69** |
| Cabeza inicializada con las descripciones | 46,91 | 29,17 |
| Cabeza congelada en las descripciones | 43,78 | 29,01 |

| | Aciertos | F1-macro |
|---|---|---|
| `inicial` frente a la referencia | **−4,03** | **−12,52** |
| `fija` frente a la referencia | −7,16 | −12,68 |

**El F1-macro cae tres veces más que el acierto.** Esa desproporción es el hallazgo:
el F1-macro pondera por igual a cada sector, de modo que el deterioro se concentra en
las clases con pocos ejemplos, que eran exactamente aquellas en las que se esperaba la
mejora. El efecto es el contrario del previsto.

Un segundo indicio apunta en la misma dirección:

| | Sin texto web | Con texto web |
|---|---|---|
| `inicial` | 35,22 | 54,51 |
| `fija` | 35,02 | 49,47 |

Sin texto todas las variantes convergen; **el daño aparece allí donde el modelo
disponía de señal con la que trabajar.**

#### Interpretación propuesta, declarada como hipótesis

Las 38 descripciones, una vez codificadas, probablemente **se parecen demasiado entre
sí**: todas describen empresas, en el mismo registro y con vocabulario próximo. Una
inicialización aleatoria sitúa las clases casi perpendiculares entre sí; la biblioteca
las sitúa casi paralelas, y el modelo debe deshacer esa degeneración antes de empezar a
aprender. Sería el mismo fenómeno de banda estrecha que E24 documentó en el
emparejamiento.

> **No está medido.** Comprobarlo cuesta dos minutos de procesamiento gráfico y no
> requiere entrenar: codificar las 38 descripciones e imprimir su similitud media por
> pares. Si superan holgadamente el 0,9, la explicación queda establecida.

#### Lo que este resultado sí permite afirmar

Se han probado **dos vías distintas de entregar la misma biblioteca, y ambas pierden**:

| Vía | Resultado |
|---|---|
| En el *prompt* de un modelo cerrado (E30) | 39,87 % frente a 51,73 % |
| Como inicialización de la capa de salida (E31) | 46,91 % frente a 50,94 % |

**La afirmación resultante es más fuerte que si solo se hubiera probado una.** El
conocimiento que la biblioteca contiene es real —es el que codifica la taxonomía—, pero
suministrarlo de forma declarativa no es el modo en que este modelo lo incorpora: lo
aprende mejor de 16.408 ejemplos que de 38 definiciones.

#### Lo que NO permite afirmar

Que las descripciones de etiqueta no sirvan nunca. Quedan sin probar, entre otras, la
ampliación del texto de entrenamiento con la descripción de su clase, y las
arquitecturas de doble codificador entrenadas desde el principio para ese fin.

#### ⚠️ Salvedad técnica

La versión de `transformers` disponible no admitió `warmup_ratio` y el script continuó
sin calentamiento del ritmo de aprendizaje. **Afecta por igual a las tres variantes**,
de modo que la comparación entre ellas se mantiene; y la referencia reprodujo pese a
ello.

#### Decisión

**A2 se mantiene como está.** El modelo final sigue siendo el transformer sin
biblioteca.

#### Redacción sugerida para la memoria

> Se evaluó si la incorporación de descripciones de clase mejoraba la clasificación
> sectorial, hipótesis razonable a la luz de RQ1: si el conocimiento organizacional no
> se infiere del lenguaje general, cabría suministrarlo explícitamente. Se ensayaron dos
> procedimientos —la inicialización de la capa de salida con las descripciones
> codificadas y su congelación en ellas— sobre una referencia que reprodujo el
> rendimiento publicado con una desviación de 0,79 puntos. Ambos degradaron el
> resultado, y lo hicieron de manera desproporcionada en el F1-macro (−12,52 frente a
> −4,03 puntos de exactitud en la variante menos lesiva), es decir, perjudicando
> precisamente a las clases minoritarias en las que se esperaba la mejora. Junto con el
> ensayo previo mediante instrucciones a un modelo generativo, son dos vías
> independientes de suministrar el mismo conocimiento y ambas resultan inferiores al
> aprendizaje a partir de ejemplos.


### E31b · A2 · Cuánto se mueve la misma referencia entre dos ejecuciones
**Fecha:** 04-10-2026 · 2.652 casos de prueba · `F2_A2_E31b_variacion_entre_ejecuciones.py`

**La objeción que había que responder.** E31 concluye que la biblioteca empeora el
clasificador, y lo sostiene sobre una caída de 12,52 puntos de F1-macro frente a 4,03 de
exactitud: la desproporción de tres a uno es el argumento de que el daño se concentra en
las clases minoritarias. Un tribunal preguntaría lo obvio: **¿y cómo se sabe que 12,52
puntos no son el ruido normal entre dos entrenamientos?** El trabajo no podía contestar.

**Resulta que sí hay dos ejecuciones iguales.** La referencia de E31 se entrenó dos veces
el 02-10-2026: una primera vez sola, y otra dentro de la tanda de las tres variantes.
Misma arquitectura, mismas épocas, misma partición, mismo ritmo de aprendizaje. Los
resultados de la primera estaban dentro del zip de 1,77 GB y no se habían mirado.

| Métrica | 1.ª ejecución | 2.ª ejecución | Se mueve |
|---|---|---|---|
| Aciertos (41 clases) | 50,98 | 50,94 | **0,04** |
| F1-macro (41 clases) | 43,08 | 41,69 | **1,39** |
| Aciertos (12 grupos) | 59,81 | 58,85 | 0,96 |
| F1-macro (12 grupos) | 57,60 | 55,97 | 1,63 |

**La exactitud no se mueve y el F1-macro sí.** Es coherente con lo que mide cada una: el
F1-macro pondera por igual las clases, de modo que depende de las que tienen pocos casos,
donde un puñado de aciertos distintos mueve bastante la cifra.

#### 🔑 La conclusión de E31 aguanta, y ahora tiene suelo de comparación

| | Puntos de F1-macro |
|---|---|
| Caída con la biblioteca | 12,52 |
| Movimiento entre ejecuciones idénticas | 1,39 |
| **Cociente** | **9,0 veces** |

La caída es **nueve veces** el movimiento observado. No es variabilidad de entrenamiento.

**Lo que esta cifra NO es, y hay que decirlo al presentarla.** Son dos ejecuciones, es
decir **una sola diferencia**: no es una desviación típica y no permite construir un
intervalo de confianza. Es la única observación disponible de cuánto se mueve esta
métrica, y como tal debe presentarse. Un intervalo de verdad exigiría cinco o diez
semillas, unas cinco horas de procesamiento gráfico, y **no está hecho**.

Aun con esa salvedad, cambia algo: antes la desproporción de tres a uno era un argumento
sin referencia contra la que medirse. Ahora la tiene.

**De paso.** El zip de 1,77 GB contenía 0,38 MB útiles —el json de resultados y el csv de
predicciones— y el resto eran los pesos del modelo y el estado del optimizador. Los dos
ficheros útiles quedan extraídos con el sufijo `_1a_ejecucion`.

---

### E32 · A9 · El agente de seguimiento, y el comercial como rival medido
**Fecha:** 04-10-2026 · 3833 oportunidades cerradas · `F9_A9_seguimiento_oportunidades.py`

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

Partición **temporal**, no aleatoria: se entrena con lo anterior a 2026Q1
y se prueba con 2026Q2. Una partición aleatoria dejaría ver el futuro,
que es justo lo que un agente de previsión no tiene.

El trimestre 2026Q3 **se aparta**: tiene un 81,0 % de
ganadas porque las recientes aún no se han resuelto. Incluirlo infla el resultado. Es
censura por la derecha y se declara.

| Conjunto | Casos | Se ganan |
|---|---|---|
| Entrenamiento (≤ 2026Q1) | 2738 | 50,6 % |
| Prueba (2026Q2) | 721 | 56,7 % |
| Apartado por censura | 374 | 81,0 % |

#### 🔑 Hallazgo 1 · El modelo supera con holgura al suelo

| Modelo | Acierto | AUC | Brier |
|---|---|---|---|
| **Suelo** (decir siempre «se gana») | 56,7 % | 0,500 | 0,2455 |
| Regresión logística | 71,0 % | 0,777 | 0,1976 |
| **Bosque aleatorio** | **72,4 %** | **0.788** | 0.1907 |
| Potenciación del gradiente | 71,8 % | 0,775 | 0,1920 |

Y esto **solo con lo que se sabe al crear la oportunidad**: tipo, tipología, línea
tecnológica, área, provincia, tamaño, si ya es cliente, y el histórico de la cuenta.

**El histórico se calcula hacia atrás.** «Cuántas oportunidades tuvo antes esta cuenta y
cuántas ganó» se computa solo con las creadas **antes** de la que se predice. Hacerlo de
otro modo es ver el futuro, y es el error más fácil de cometer en este montaje.

#### 🔑 Hallazgo 2 · Contra la persona: empata ordenando y gana calibrando

Sobre los 527 casos de prueba en que el comercial declaró
su porcentaje:

| Quién | AUC | IC 95 % | Brier | IC 95 % |
|---|---|---|---|---|
| La persona | 0.798 | [0.751, 0.844] | 0.1528 | [0.1392, 0.1657] |
| **A9** | **0.829** | [0.779, 0.870] | **0.1284** | [0.1164, 0.1426] |

Contraste **emparejado** —se remuestrean los mismos casos para los dos, no cada uno por
separado— con el signo puesto de modo que positivo significa «A9 mejor»:

| | Diferencia | IC 95 % | p |
|---|---|---|---|
| ORDENAR (AUC) | +0,034 | [-0,021, +0,084] | 0,216 |
| CALIBRAR (Brier) | +0,0258 | [+0,0107, +0,0392] | **0,002** |

**Son dos cosas distintas y aquí se separan.** Ordenando no se distinguen: el intervalo
cruza el cero. Calibrando, A9 es mejor y el intervalo no lo cruza.

Quitando los valores extremos —ver el hallazgo 3— sobre 480 casos la
diferencia de AUC queda en +0.033
[-0.021, +0.082], p ≈ 0.210.
Sigue sin distinguirse.

**La frase que resume A9:** *ordena igual que la persona, pero su número significa lo que
dice.*

#### 🔑 Hallazgo 3 · La persona es pesimista de forma sistemática, y parte de su cifra está contaminada

| Dice | Casos | Se gana de verdad | IC 95 % |
|---|---|---|---|
| 0–24 % | 11 | 0,0 % | [0,0, 25,9] |
| 25–49 % | 45 | 35,6 % | [23,2, 50,2] |
| 50–69 % | 181 | 65,7 % | [58,6, 72,3] |
| **70–89 %** | 241 | **95,0 %** | [91,5, 97,1] |
| 90–100 % | 49 | 91,8 % | [80,8, 96,8] |

**Cuando dicen 70–89 % se gana el 95,0 %.** El número ordena bien pero no vale como
probabilidad: hay que traducirlo antes de usarlo, que es exactamente lo que el proyecto de
previsión anticipaba sin haberlo cuantificado.

**Y hay contaminación.** 47 casos de los
527 llevan 0 o 100 exactos, y de los que marcan 100 se
gana el 90,7 %: **ese valor se escribe después de saber el resultado**, no es una
previsión. Por eso se usa la probabilidad de la **primera** oferta de cada oportunidad, y
por eso la comparación se repite sin los extremos.

#### Hallazgo 4 · El modelo aprende «qué», no «quién»

| | AUC |
|---|---|
| Con el propietario de la oportunidad | 0.788 |
| Sin el propietario | 0.770 |

Aporta +0.018. Importa porque un modelo que acierta
identificando al comercial no es transferible a otra organización ni a otra plantilla: lo
que hace es memorizar personas. Este no.

#### Hallazgo 5 · Lo que se pierde tarda seis veces más

| | Casos | Mediana | Media | p90 |
|---|---|---|---|---|
| Ganadas | 1.793 | **11 días** | 33 | 83 |
| Perdidas | 1.571 | **72 días** | 104 | 234 |

Una oportunidad que lleva mucho tiempo abierta es, casi siempre, una oportunidad perdida
que nadie ha cerrado. Y de eso sale una lista de trabajo que **no necesita modelo**:

El 90 % de las que cierran lo hacen antes de 185 días.
**418 de las 1048 abiertas (39,9 %)
pasan de ese plazo.**

#### Un defecto de los datos que conviene anotar

380 oportunidades tienen fecha de cierre **anterior** a la de
creación. Se excluyen del análisis de tiempos y queda declarado: son registros creados a
posteriori.

#### Lo que E32 no dice

No dice que usar A9 aumente las ventas: mide si ordena mejor que la persona, no el efecto
de actuar en consecuencia. La comparación es de **un** trimestre. Y sin importes, por D13:
un modelo con el importe podría ordenar mejor y no se ha probado.


#### Redacción sugerida para la memoria

> La integración de un modelo de estimación en la fase de seguimiento permitió contrastarlo
> contra la referencia que la propia organización produce: el porcentaje de probabilidad que
> el personal comercial consigna en cada oferta. Sobre las 527 oportunidades de prueba en
> que esa estimación constaba, el modelo y la persona resultaron **indistinguibles en
> capacidad de ordenación** —diferencia de AUC de +0,034, con intervalo [−0,021, +0,084]—
> mientras el modelo obtuvo una **calibración significativamente mejor** —diferencia de
> Brier de +0,0258, intervalo [+0,0107, +0,0392], p = 0,002—. La distinción no es
> accesoria: la estimación humana ordena correctamente pero no admite lectura como
> probabilidad, pues en el tramo declarado de 70–89 % se gana en realidad el 95,0 % de las
> oportunidades.


---

### E33 · A6 · El agente de recepción, y lo que A8 pierde con texto de cliente
**Fecha:** 04-10-2026 · 105 correos reales · `F6_A6_agente_recepcion.py`

**Qué es A6.** La fase 6: entra un mensaje al buzón general y hay que decidir cuatro cosas
antes de que lo vea una persona. ¿De quién es? ¿Qué pide? ¿A quién le toca? ¿Es comercial?

**Qué cambió para poder construirlo.** El corpus pasó de 52 correos a
105. Con 52 se podía medir; con 105 se puede además construir
y encadenar. Una quinta parte entra **en inglés** (23 de 105), lo que las
reglas no acusan pero cualquier modelo entrenado en español sí.

| Pieza | Cómo funciona | Estado |
|---|---|---|
| 1 · Resolver la identidad | reglas | medida en E22: 32/98 = 32,7 % |
| 2 · Detectar la norma citada | diccionario | medida aquí: 53/105 = 50,5 % |
| 3 · Enrutar al área técnica | modelo de A8 | **medida aquí sobre correo real** |
| 4 · Comercial / no comercial | modelo | construida, etiqueta automática |

#### 🔑 Hallazgo principal · El desajuste de población de A8, por fin cuantificado

El apartado 4.6.4 declaraba que **no se había medido** cuánto se degrada el 80,51 % de A8
al pasar de `Tema` —texto del comercial— al correo del cliente, porque solo ocho mensajes
traían su área asociada.

Ya no son ocho. De los 105 correos, **41 permiten deducir el área
con certeza** a partir de la norma citada, porque la correspondencia norma → área no es
estadística sino de definición. Eso da 41 etiquetas de prueba sobre texto de
entrada real.

| | Acierto | IC 95 % |
|---|---|---|
| A8 en su propia población (4.6.4) | 80,51 % | — |
| **A8 sobre correo de cliente real** | **79,5 %** | [64,5, 89,2] |
| Suelo: la clase más frecuente | 12,2 % | — |

**Cae 1,0 punto y conserva 66,7 sobre el
suelo.** La señal no se pierde: el enrutado sirve, pero la cifra buena para producción es
el 79,5 %, no el 80,51 %.

**Y esto contrasta con A3.** En E28 el encadenamiento redujo a la mitad el margen de la
priorización. Aquí el clasificador de área aguanta el cambio de población casi intacto.
**Dos componentes, dos comportamientos opuestos ante el mismo fenómeno**, y la diferencia
está en la etiqueta: el área la escribe quien la conoce, la nota de cuenta la deduce un
modelo de variables que cambian de distribución.

**Salvedades, y son importantes.** Son 39 casos y el intervalo mide 25 puntos.
La etiqueta de prueba la pone el diccionario, no una persona: es cierta por definición pero
**solo existe donde se cita una norma, que son los casos más fáciles**. Y entran solo las
cuatro áreas que el diccionario cubre, de diecinueve.

#### Hallazgo 2 · La norma citada resuelve la mitad de los casos

50 de 105 correos citan una norma reconocible
([41,1 %, 59,9 %]). De ellos, 41 apuntan a **una
sola** área y 12 a varias, donde el diccionario no decide. Los
52 restantes piden algo sin nombrar la norma que lo regula, y ahí hace falta
el clasificador.

#### 🔑 Hallazgo 3 · La pieza 4, y por qué la etiqueta automática la invalidaba

14 de 105 correos no son solicitudes comerciales, según la
clasificación que hizo la autora a mano. O sea que decir «todos son comerciales» acierta el
86,7 %.

**Por eso el acierto no vale aquí:** lo consigue una regla que no mira el texto. Se mide si
encuentra los negativos, con validación cruzada:

| | Valor |
|---|---|
| AUC (validación cruzada) | **0,919** |
| IC 95 % por remuestreo | [0,828, 0,980] |
| Suelo | 86,7 % |

De los veinte correos más sospechosos recupera **11 de los 14**, y de los treinta, 13.

Así se usa: **no como clasificador que decide solo, sino como cola de revisión ordenada.**
Una persona mira veinte correos en vez de 105.

**Esta cifra hubo que rehacerla.** La primera versión etiquetaba los negativos con una
lista de términos y daba un AUC de 0,700. Al contrastar esa lista contra la clasificación
manual de la autora resultó que **de los quince correos que marcaba solo dos lo eran**:
diez fallos venían de la palabra *proveedor*, que aquí aparece en correos de clientes
hablando de sus propios proveedores. Es el error X25, y el AUC de 0,700 queda retirado.

**Lo que sigue sin sostenerse** no es la etiqueta sino el tamaño y el número de
evaluadores: catorce negativos dan un intervalo de 0,15 puntos, y clasificó **una sola
persona**, que además es la autora. La concordancia entre evaluadores, que es el techo real
de esta tarea, no se ha medido.

#### El agente encadenado

| Decisión | Correos | % |
|---|---|---|
| Enrutado por el clasificador | 40 | 38,1 % |
| Enrutado por norma | 39 | 37,1 % |
| A revisión: no es una solicitud comercial | 14 | 13,3 % |
| A revisión: la norma apunta a varias áreas | 12 | 11,4 % |

**Resuelve solo 79 de 105 (75,2 %)** y pasa 26 a una persona, cada uno con el motivo
escrito. Igual que el orquestador: no adivina cuando no sabe.

#### 🔑 Pero esa cifra NO es automatización completa

El reparto solo mira el enrutado, que no depende de quién escriba —y eso es correcto: la
EN 13432 es compostabilidad venga de quien venga—. Pero por **D19**, cuando la identidad no
se resuelve el sistema **no da de alta la cuenta**: lo decide una persona.

| | Cuenta localizada | Cuenta NO localizada |
|---|---|---|
| El agente lo resuelve | **28** | 51 |
| Pasa a una persona | 4 | 22 |

De los 79 que resuelve, **solo 45 son de cuentas
que están en el sistema de gestión**. La cifra honesta de automatización completa es
**45 de 105, un 42,9 %**, no el 75,2 %.

> Esta cifra subió tras **E35**: al resolver la identidad también por el nuevo campo
> `Dominio`, los correos con cuenta localizada pasaron de 32 a 53 y la
> automatización completa del 26,7 % al 42,9 %.

El enrutado sigue valiendo para los otros 51: ahorra decidir el
área, que es la parte técnica. Lo que no ahorra es el alta, que es justo lo que D19 reserva.

Queda como error **X26**.


#### Redacción sugerida para la memoria

> El clasificador de enrutado, evaluado sobre su población de entrenamiento, alcanza un
> 80,51 % de acierto. Al aplicarse sobre mensajes redactados por el cliente —un registro
> textual distinto— el rendimiento desciende al 79,5 %, con intervalo [64,5 %, 89,2 %],
> conservando 66,7 puntos sobre el suelo. El descenso de 1,0 puntos contrasta con el
> observado en el modelo de priorización, que al encadenarse perdió la mitad de su margen:
> la diferencia es atribuible a la naturaleza de la etiqueta, registrada con certeza en un
> caso y deducida de variables de disponibilidad variable en el otro.


---

### E34 · A7 · La cualificación, con tres criterios en vez de siete
**Fecha:** 04-10-2026 · 684 solicitudes de prueba · `F7_A7_cualificacion_solicitud.py`

**Qué es A7.** La fase 7: llega una solicitud y hay que cualificarla antes de dedicarle
tiempo. El diseño original proponía siete criterios —necesidad, impacto, presupuesto,
plazo, decisor, encaje y campeón— extraídos de la conversación comercial.

**Por qué no se había construido, y qué cambia.** No existía el dato de entrada: Empresa no
graba las llamadas. Eso sigue siendo cierto. Lo que cambia es que el **sustituto escrito**
sí existe, y por duplicado: 105 correos reales de cliente, y
**3725 solicitudes históricas del sistema de gestión con su resultado
real**. Lo segundo permite plantear la pregunta que de verdad importaba:

> ¿Predice la conversión **contar criterios de cualificación**, o hay que **aprender del
> texto**?

#### 🔑 Hallazgo 1 · Contar criterios no ordena, y eso NO refuta el marco

| Referencia | AUC | IC 95 % |
|---|---|---|
| Azar | 0,500 | — |
| Contar los **siete** criterios | 0.492 | [0.459, 0.527] |
| Contar los **tres** que sí aparecen | 0.486 | [0.454, 0.521] |

Los dos intervalos cruzan el 0,5: ninguna ordena.

**Pero la lectura correcta no es que el marco falle.** En este texto los criterios apenas
aparecen: **0.45 de 7** de media, porque el campo son
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
| Suelo | 56,9 % | 0,500 | — |
| Contar los siete criterios | — | 0.492 | [0.459, 0.527] |
| **A7 · aprender del texto** | **66,2 %** | **0.714** | [0.677, 0.753] |

**+9,4 puntos sobre el suelo y +0.222 de AUC
sobre contar criterios.** Partición temporal, 2680 de entrenamiento y
684 de prueba.

#### Hallazgo 3 · Y no está leyendo el resultado

El texto lo escribe el comercial, a veces después de saber cómo acabó. Se comprobó de dos
formas, porque suponerlo no basta:

1. 29 de 3725 solicitudes (0,8 %) contienen algún
   término de desenlace —«anulado», «no procede»…—.
2. De los 200 términos más influyentes del modelo, **0 son de
   resultado**.

Y al reentrenar sin ese vocabulario: acierto 66,7 %, AUC 0.715.
**No cambia nada**, de modo que el modelo no se apoyaba en ellos y la cifra publicable es
la de arriba.

#### El agente sobre correo de cliente real

Corre y devuelve una puntuación para cada uno de los 105 correos,
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

### E35 · A6 · La identidad se resuelve mucho mejor con el dominio del correo
**Fecha:** 05-10-2026 · 98 correos reales · `F6_A6_identidad_dos_vias.py`

**De dónde sale.** La primera pieza de A6 decide si quien escribe ya está en el sistema de
gestión. Hasta ahora solo podía compararse el `@dominio` del remitente con el dominio
extraído del campo **`Sitio web`** de la cuenta: dos cosas que **no son la misma**, que es
exactamente la confusión que costó el error X19.

La autora añadió al CRM una columna **`Dominio`** con la parte de detrás de la arroba del
correo asociado a cada cuenta. Eso sí es comparable con lo mismo, y procedía medir si
funciona mejor.

#### 🔑 Funciona mejor, y con holgura

| Vía | Resuelve | % | IC 95 % |
|---|---|---|---|
| 1 · dominio del `Sitio web` | 35 de 98 | 35,7 % | [26,9, 45,6] |
| 2 · columna `Dominio` | **51 de 98** | **52,0 %** | [42,3, 61,7] |
| 3 · las dos juntas | 53 de 98 | 54,1 % | [44,2, 63,6] |

**Comparación emparejada**, sobre los mismos correos:

| | Vía Dominio sí | Vía Dominio no |
|---|---|---|
| Vía web sí | 33 | 2 |
| Vía web no | **18** | 45 |

Solo informan las casillas en que discrepan. Resuelven **solo** por la vía Dominio
18 correos, y solo por la vía web 2. Con la binomial exacta,
**p = 0.0004**.

#### Y el techo estructural sube veinte puntos

| Fuente | Cuentas | % de las 24079 |
|---|---|---|
| Con sitio web utilizable | 16260 | 67,5 % |
| Con la columna `Dominio` | 14383 | 59,7 % |
| **Con alguna de las dos** | **21186** | **88,0 %** |

**Son complementarias:** 4926 cuentas tienen `Dominio` y **no** tienen sitio
web. Por eso sumarlas sube el techo del 67,5 % al
88,0 %, y por eso se conservan las dos aunque la web aporte poco una
vez se tiene la otra.

**Ese techo no es acierto:** es el máximo al que se puede aspirar, porque una cuenta sin
ninguno de los dos campos no se encuentra por esta vía haga lo que haga el sistema. El
12,0 % restante sigue fuera de alcance.

#### Lo que arrastra: la automatización de A6 sube

La pieza 1 es la que limita la automatización completa, porque por **D19** un correo de una
empresa no identificada necesita que una persona decida el alta aunque el área esté bien
enrutada.

| | Antes (solo vía web) | Ahora (las dos) |
|---|---|---|
| Correos con la cuenta localizada | 32 | **53** |
| El agente los resuelve del todo | 28 | **45** |
| **Automatización completa** | 26,7 % | **42,9 %** |

#### Una diferencia de cifras que conviene declarar

La vía web da aquí **35 de 98** y la cifra publicada en E22 era
**32 de 98**. No es una corrección de un error: E22 cruzaba contra los ficheros derivados
—21.707 cuentas— y este experimento cruza contra el export completo, que trae
24079. Más cuentas, más coincidencias. **La comparación entre las tres vías sí es
limpia**, porque las tres usan la misma fuente y los mismos correos.

#### Lo que E35 no resuelve

Son 98 correos y los intervalos miden unos veinte puntos. Y las vías 1 y 2 de la
decisión **D18** —buscar la dirección completa, o el dominio, entre los contactos— siguen
sin medirse: exigen datos personales que no se exportaron por minimización.

#### Redacción sugerida para la memoria

> La incorporación al sistema de gestión de un campo con el dominio de correo asociado a
> cada cuenta elevó la resolución de identidad del 35,7 % al 52,0 % de
> los mensajes, diferencia que resulta significativa en una comparación emparejada
> (p = 0.0004). El resultado era previsible —compara el dominio del remitente
> con un dominio de correo, y no con el de una página web— pero su magnitud no lo era:
> 18 mensajes se resuelven únicamente por la vía nueva. El techo
> estructural del procedimiento asciende asimismo del 67,5 % al
> 88,0 % de las cuentas registradas.

---

### E36 · A7 · ¿Aporta el texto algo que los campos no capturen?
**Fecha:** 06-10-2026 · 720 oportunidades de prueba · `F7_A7_aporta_algo.py`

**La pregunta, de la autora.** «A7 tal y como está planteado no me sirve de nada: el tema
de la oportunidad y el correo son muy diferentes, como se vio en A6. ¿Me lo puedo cargar y
pasar de A6 directamente a A8?»

Había que contestar con una medición, y para eso hay que separar dos cosas que no son la
misma: si A7 sirve **donde está**, y si el texto sirve **para algo**.

**Lo primero ya tenía respuesta, y es desfavorable.** Se entrena con `Tema` —cuatro o cinco
palabras del comercial— y se aplicaría sobre correos de 154 palabras del cliente. A6 midió
esa frontera para el enrutado y cuesta 4,9 puntos; para A7 **no se puede medir**, porque
ningún correo trae su resultado. Y al pasarlo por los 105 correos, 104 caen en las dos
bandas bajas.

**Lo segundo no se había planteado**, y es lo que decide: A7 y A9 predicen **lo mismo** con
datos distintos.

| Predictor | AUC |
|---|---|
| Solo los campos (las 17 de A9) | 0,788 |
| Solo el texto | 0,720 |
| **Ambos** | **0,813** |

El texto sobre los campos: **+0.024**
[+0.010, +0.040],
p = 0.001. Y los campos sobre el texto:
+0.093. **Son complementarios.**

#### Un error que estuvo a punto de colarse

La primera versión comparó contra **siete** variables, no las diecisiete de A9, y el texto
aparecía aportando +0,044. Sobre el conjunto completo aporta
+0.024: la mitad. Comparar contra una versión recortada
del rival habría dado una recomendación inflada. **Al rehacerlo, el «solo campos» reprodujo
exactamente el 0,788 publicado de A9**, que es la señal de que el montaje era comparable.

---

### E37 · A8 · El briefing de traspaso, que era la mitad sin construir
**Fecha:** 06-10-2026 · 105 correos reales · `F8_A8_briefing_traspaso.py`

**Qué faltaba.** El diseño de la fase 8 pedía dos cosas: enrutar al área técnica y
**redactar el briefing de traspaso**. Lo primero estaba construido desde E25; esto es lo
segundo, y cierra el hueco que X27 declaró.

**Qué produce.** Una ficha por correo entrante con lo que el comercial necesita para
atenderlo: de quién es, a qué área va, qué pide, un tema propuesto para la oportunidad y si
es o no una solicitud comercial.

#### 🔑 Se compone, no se redacta, y el motivo es un dato

Se planteó usar el modelo generativo y el dato lo desaconsejó:

- **El 94 % de los temas del histórico aparece una sola vez**, así que no hay plantilla que
  copiar: habría que generar de verdad.
- Generar exige procesamiento gráfico, lo que mete el briefing en el circuito por lotes y
  le quita justo lo que lo hace útil, que es responder rápido.
- Y **un briefing inventado es peor que ninguno**: si dice que el cliente pide un ensayo que
  no pidió, el comercial llega a la reunión con una idea falsa.

Así que la ficha se **compone** de lo que consta. Cada campo lleva de dónde sale, y lo que no
se sabe aparece como no sabido en lugar de rellenarse.

| Campo | Se rellena | De dónde sale |
|---|---|---|
| Dominio del contacto | 105 de 105 | cabecera del correo |
| ¿Es comercial? | 105 de 105 | clasificador de A6 |
| Cuenta en el sistema | 53 de 105 | cruce por dominio (E35) |
| Tipo de servicio | 60 de 105 | diccionario |
| **Tema propuesto** | **53 de 105** | composición |
| Área por norma | 39 de 105 | diccionario norma → área |
| Sector de la cuenta | 47 de 105 | ficha de la cuenta |

#### Qué se mide de un briefing, que no es el acierto

No existe briefing verdadero contra el que comparar, así que no se mide acierto. Se mide
**fundamentación**: qué proporción del tema propuesto procede del correo o del catálogo y no
de ningún otro sitio. Es el mismo control que E19 aplicó a la redacción de A5.

| | Fundamentación |
|---|---|
| Suelo: las tres palabras más frecuentes del histórico | 72,3 % |
| **El tema compuesto** | **100,0 %** |

Los 53 temas propuestos están fundamentados al 100 %. **Por
construcción debería ser así**, y precisamente por eso se comprueba: la primera ejecución dio
99,1 % y el fallo que destapó es el error X28.

#### Lo que ninguna ficha lleva, y se declara

- **Nombre y cargo de quien escribe.** No se exportaron, por minimización (4.2.4).
- **Presupuesto y plazos**, que solo aparecen en el 43,8 % y el 28,6 % de los correos (E34).
- **Una estimación de si se va a ganar.** A9 la da, pero exige la oportunidad ya creada, y
  en este punto todavía no existe.

Fichas con cuenta, área y tema a la vez: 20 de 105. El
resto llega con parte de la información, y con el hueco señalado.

---

### E38 · A8 · El tipo de servicio deja de ser un diccionario
**Fecha:** 06-10-2026 · 4860 temas con etiqueta humana · `F8_A8_tema_modelo.py`

**De donde viene.** El briefing de E37 funcionaba, pero el tipo de servicio
—«Ensayo», «Consultoría»...— no lo decidía un modelo: lo buscaba en una lista de palabras
escrita a mano. Esto lo convierte en un clasificador entrenado y mide si gana.

#### 🔑 La etiqueta es humana, y eso es lo que hace válido el experimento

El export de oportunidades trae la columna **«Tipo Oportunidad» rellenada por las personas
de Empresa en 4860 filas**, con seis valores. Así que no hay circularidad: el
diccionario y el modelo reciben el mismo texto, proponen un tipo, y los dos se comparan
contra lo que puso una persona.

Al diccionario se le da su **mejor versión**: su etiqueta «Ensayo» se traduce a la clase
humana que más veces le corresponde, aprendido solo con los datos de entrenamiento de cada
vuelta. Y los textos repetidos —de 4860 temas solo 3814 son
distintos— van juntos en el mismo pliego, porque si no el modelo examina lo que ya ha
visto: sin esa precaución sale 87,2 %, medio punto de regalo.

| | cobertura | acierto |
|---|---|---|
| Suelo 1 · la clase más frecuente | 100 % | 46,0 % |
| Suelo 2 · el diccionario de E37 | 26,4 % | 22,2 % |
| **El modelo** | **100 %** | **86,6 %** [85,6, 87,5] |

Callarse cuenta como fallo, porque un briefing sin tipo no le sirve al comercial.
**64,4 puntos** de diferencia [63,0, 65,7], y McNemar
reparte 3165 casos arreglados contra 34
estropeados. Gana por dos motivos distintos: acierta más donde los dos hablan
(90,0 % frente a 83,9 %) y
además contesta donde el otro se calla, con un
85,4 % de acierto.

#### La prueba que de verdad importa: sin la palabra clave

Se borran del texto de prueba todas las palabras del diccionario, que es lo que pasa en un
correo real: el cliente no escribe «ensayo», escribe «comprobar si el film aguanta».

| | acierto |
|---|---|
| El diccionario, sin sus palabras | 0,0 % |
| **El modelo, sin esas palabras** | **82,6 %** |
| Suelo · la clase más frecuente | 46,0 % |

#### 🔑 Y entonces se derrumba, y hay que decirlo

El modelo se entrena con telegramas de cinco palabras y se le pide trabajar sobre correos de
doscientas. **Para medir eso con etiqueta** se fabrican correos: un tema real del histórico
—del que sí se sabe el tipo— envuelto en la cortesía de un correo real, saludo y firma
incluidos.

| | acierto |
|---|---|
| El tema solo | 86,6 % |
| **El correo fabricado, entero** | **41,5 %** |
| Su telegrama de 10 palabras | 69,4 % |
| El diccionario sobre el correo fabricado | 29,1 % |

Envolver el tema en cortesía cuesta **45,1 puntos**. Sobre los correos de
verdad el síntoma es visible: el modelo contesta «Desarrollo I+D» al
46,7 % de los mensajes cuando en el histórico esa clase es el 16,6 %, y los
ensayos desaparecen.

**La solución no es otro modelo, es otra entrada.** En vez del correo entero se le pasa un
telegrama sacado de él: solo las palabras que existen en el histórico, las
10 que más distinguen, quitando la cortesía —las que salen en más de la cuarta
parte de los correos— y lo demasiado raro. **No escribe nada: descarta.** Eso recupera
27,9 de los 45,1 puntos perdidos, y
10,5 puntos [8,7, 12,4] **por encima del
diccionario incluso donde el diccionario ve su palabra** (2320 casos).

#### Sobre los 105 correos reales, lo único comprobable

Nadie ha anotado a mano el tipo de esos mensajes, así que no se mide acierto sino **acuerdo
con lo que el correo dice con sus propias palabras**, en los 60
donde eso consta: del 16,7 % con el correo entero al
**73,3 % con el telegrama**. Acuerdo no es acierto y queda
como comprobación pendiente, igual que el segundo evaluador de A6.

#### Cuándo callarse, y por qué el umbral de un sitio no vale en otro

El umbral que iguala la cobertura del diccionario sobre temas es 0,98, y **sobre correos
dejaría el briefing sin tipo en 100 de 105**: las probabilidades caen de una mediana de
0,92 sobre temas a 0,68 sobre
correos. El umbral que iguala la *calidad* del diccionario sale **cero**: contestando siempre
el modelo ya acierta más de lo que acierta el diccionario donde se atreve. Así que contesta
siempre y declara su tramo:

| tramo | casos | acierto |
|---|---|---|
| confianza alta · p ≥ 0,80 | 3.433 | 94,5 % |
| media · 0,50 a 0,80 | 1.194 | 72,1 % |
| baja · p < 0,50 | 233 | 44,6 % |

#### La materia se queda extractiva, y la ampliación automática se rechaza

No hay ninguna columna donde una persona haya escrito cuál es el objeto de la oportunidad,
así que etiquetar con el propio diccionario y aprender de esas etiquetas sería enseñarle al
modelo a repetir el diccionario. Y además la materia **tiene** que salir literal del texto:
es lo que sostiene la fundamentación.

Lo que sí se puede aprender del dato es la lista, y se probó: la lista escrita a mano
aparece en el 20,0 % de los temas, y las catorce palabras
frecuentes que no cubre subirían la cobertura al
39,8 %. **Pero ninguna es un objeto**: «interés»,
«asociarse» y «sentiatech» hablan de socios, «simulación» y «valorización» son servicios.
Rechazada, y el 20,0 % no es el techo de la lista sino los
temas que de verdad nombran algo.

---

### E39 · A8 · ¿sirve la probabilidad cuando la cuenta es nueva?
**Fecha:** 07-10-2026 · 245 casos sin historial de 721 · `F9_A9_sin_historial.py`

**Por qué se hace.** El circuito de recepción que describe 7.2c crearía la oportunidad de
empresas que escriben por primera vez. Pero **diez de las diecisiete variables de A8
dependen de que la cuenta ya exista**: tres resumen su historial —oportunidades previas,
cerradas, tasa de acierto— y siete salen de su ficha en el sistema de gestión. La cifra
publicada en 4.6.7 está medida sobre todas las oportunidades mezcladas, y la mayoría son de
cuentas veteranas. Procedía comprobar qué queda en el trozo que al circuito le importa.

**Cómo.** La misma tubería de 4.6.7 —mismos datos, mismas variables, misma partición
temporal, mismo bosque—. Lo único que se añade es partir el conjunto de prueba al final.

| Grupo | Casos | Acierto | AUC | Brier |
|---|---|---|---|---|
| Todas, la cifra de 4.6.7 | 721 | 73,9 % | 0,811 | 0,181 |
| Con historial | 476 | 75,2 % | 0,808 [0,766, 0,846] | 0,172 |
| **Sin historial** | **245** | 71,4 % | **0,748** [0,679, 0,808] | 0,199 |

#### 🔑 Ordenando pierde, calibrando es donde más gana

**Ordenando pierde**: de 0,808 a 0,748 de AUC. Los intervalos se
solapan, así que la caída **no está demostrada**, pero la dirección es esa y sería ingenuo
no contarla. Frente a la persona, además, en cuentas nuevas el modelo ordena *peor*:
-0,098 [-0,224, 0,017], p = 0,090
—el intervalo toca el cero, de modo que tampoco eso está demostrado, pero es el riesgo que
un lector sospecharía y conviene enseñarlo.

**Calibrando gana, y mucho más que antes.** Frente a la probabilidad que declara el personal
comercial:

| | n | Mejora de Brier | p |
|---|---|---|---|
| Cuentas con historial | 380 | +0,0176 | 0,038 |
| **Cuentas nuevas** | 147 | **+0,0911** | 0,000 |

**Cinco veces más ventaja justo donde el modelo tiene menos información.** Y tiene
explicación: ante una empresa que escribe por primera vez la persona tampoco tiene de dónde
agarrarse y pone un número de oficio. El modelo, con diez variables vacías, sigue dando un
número que significa lo que dice.

**Qué se decide con esto.** La oportunidad de una cuenta nueva **se crea con su
probabilidad**: es donde más vale la pena. Se marca como calculada sin historial porque
ordena algo peor, no porque no sirva. Corrige la cautela que D25 había dejado escrita a la
espera de esta medición.

**Lo que no se puede afirmar.** El subgrupo sin historial **ni ficha de cuenta** —el caso
puro del circuito— son solo 27 casos; su intervalo va de
0,636 a 1,000
y no se publica como resultado.

---

### E40 · El circuito de recepción, construido sobre hojas de cálculo
**Fecha:** 07-10-2026 · 105 correos reales · `A0_circuito_recepcion.py`

> **Actualizado con E41.** La pieza que distingue la solicitud se rehizo con representaciones densas (AUC 0.946) y pasó a usarse como **lista de 15 sospechosos** en vez de como umbral: recupera 13 de los 14 no comerciales, baja las oportunidades improcedentes de 2 a **1** y retiene 2 solicitudes legítimas, que no se pierden. Las cifras de arriba son ya las del circuito con la lista.

**Qué es.** El equivalente del orquestador para la vía de ENTRADA: toma los correos, los
pasa por A6 y A7, decide qué hacer con cada uno, crea la oportunidad y le pone la
probabilidad de A8. Escribe el resultado en cuatro hojas que hacen de sistema de gestión.

**Por qué hojas de cálculo.** Los tres export del CRM empiezan por las columnas
«(No modificar) …», que existen para que el fichero editado pueda volver al sistema. Tratar
las hojas como las tablas no es un apaño: es el camino que el propio producto contempla. Lo
que esto demuestra es que la cadena corre entera y produce registros con la forma
esperada. Lo que no demuestra es que la integración funcione.

| Destino | Correos |
|---|---|
| Oportunidad creada | 44 de 105 |
| Revisión · la cuenta no consta (D19) | 35 |
| Revisión · **puede no ser una solicitud** | 15 |
| Revisión · la norma apunta a varias áreas | 11 |
| Buzón genérico, automático | **0** |

#### 🔑 El clasificador de «es una solicitud» NO sirve como puerta, y está medido

Se probó a usarlo como filtro antes de crear nada. Resultado: **no evita ni una sola
oportunidad espuria**. Los 2 correos no comerciales que
llegan a la rama de creación son precisamente los que el modelo puntúa como comerciales. Y
a cambio retenía tres solicitudes reales.

| Umbral | Van al buzón | Aciertos | Solicitudes perdidas |
|---|---|---|---|
| 0,50 | 2 | 0 | 2 |
| 0,45 | 12 | 9 | 3 |
| 0,40 | 27 | 13 | 14 |
| 0,35 | 64 | 14 | 50 |

**No hay ningún umbral limpio.** Un AUC de 0,919 —el de 4.6.5— y aun así inservible en el
punto donde se toma la decisión. Es exactamente la lección del umbral de E38, repetida en
otra pieza: **ordenar bien y decidir bien son cosas distintas**, y el motivo de fondo está
declarado en 4.6.9, la clase negativa está casi vacía por sesgo de selección.

Así que la puntuación **viaja como columna** en la hoja de revisión en vez de abrir o cerrar
una puerta, el buzón genérico se alimenta de propuestas que una persona confirma, y el
circuito **crea 2 oportunidades que no debería**. Se dice, y es el coste conocido de
automatizar esta rama hoy.

#### El área también se decide sobre el telegrama

Mismo hallazgo que E38, en otra pieza. Contra el área que da la norma citada, sobre los 39
correos donde eso consta: **48,7 % leyendo el correo entero, 64,1 % leyendo el telegrama**.

Esa cifra **no se compara con el 79,5 % de 4.6.5**: aquel mide un problema de cuatro áreas
—las que el diccionario cubre— y este las dieciocho del sistema de gestión, porque un correo
puede ir a cualquiera. Más clases, menos acierto; miden tareas distintas.

#### Lo que sale, y dos detalles que importan

| Hoja | Filas |
|---|---|
| `crm_oportunidades_nuevas.xlsx` | 94 |
| `crm_cuentas_propuestas.xlsx` | 40 |
| `buzon_no_comercial.xlsx` | 12 propuestas a confirmar |
| `buzon_a_revisar.xlsx` | 58 |

- **Una cuenta por dominio, no una por correo.** Los 47 correos de empresas desconocidas
  se agrupan en 40 altas: 3 dominios habían escrito más de una vez. Sin agrupar, el
  circuito duplicaría cuentas.
- **Las altas son PROPUESTAS, no altas.** Lo impide D19. La fila sale preparada y marcada
  como pendiente, y el correo aparece además en la hoja de revisión.
- **La probabilidad va en columna propia** y marcada como calculada sin historial en
  72 de las 94, que es lo que E39 justifica.

**Ningún fichero original se toca.** Todo va a `datos/05_simulacion_crm/`.

---

### E41 · A6 · Distinguir una solicitud de trabajo: siete vías y una zona de duda
**Fecha:** 07-10-2026 · 105 correos, 14 no comerciales · `F6_A6_distinguir_solicitud.py`

**Por qué.** E40 dejó la pieza inservible como puerta y el circuito creando dos
oportunidades espurias. La pregunta de la autora fue la correcta: **si no se puede
distinguir, el sistema no debería actuar**. Así que antes de cambiar el diseño, se probó a
distinguir mejor.

**Siete vías, cinco repeticiones de validación cruzada cada una**, porque con catorce
negativos una sola partición no dice nada.

| Vía | AUC | ± | Certifica solicitudes | Aparta no comerciales |
|---|---|---|---|---|
| V1 · palabras, lo que había | 0,918 | 0,023 | 50 | 2 |
| V2 · palabras + caracteres | 0,939 | 0,008 | 48 | 0 |
| V3 · sobre el telegrama | 0,807 | 0,050 | 39 | 2 |
| V4 · representaciones densas (e5) | 0,944 | 0,004 | 44 | 0 |
| V5 · parecido a descripciones, sin entrenar | 0,783 | — | 23 | 1 |
| **V6 · densas + palabras** | **0,946** | — | **48** | 0 |
| V7 · vecinos más cercanos | 0,898 | 0,006 | 0 | 1 |

#### 🔑 Mejora de verdad, pero no donde hacía falta

El AUC sube de 0,918 a **0,946** juntando las representaciones densas
de e5-small —el mismo modelo del emparejamiento de A5, ya descargado, sin GPU— con las
palabras. Y **certifica 48 solicitudes sin colar un solo correo no
comercial**: ésas el circuito puede tratarlas solo.

Pero la banda limpia del otro lado **sigue vacía**: no hay ningún punto por encima del cual
solo haya correos no comerciales. Exigir cero contaminación con catorce negativos es brutal,
así que la pregunta útil es otra:

| Los K más sospechosos | No comerciales | Solicitudes tocadas | Precisión |
|---|---|---|---|
| 5 | 3 | 2 | 60 % |
| 10 | 8 | 2 | 80 % |
| **14** | **12 de 14** | **2** | **86 %** |
| 20 | 13 | 7 | 65 % |

**Una lista de quince correos recoge trece de los catorce no comerciales tocando dos
solicitudes**, que no se pierden: se revisan. Eso sí es utilizable, y es la respuesta a «aunque
sea con un porcentaje de duda».

#### El residuo que ningún modelo de texto va a cazar

De los dos correos que hacían crear una oportunidad espuria en E40, el nuevo clasificador
**caza uno** —sube al puesto 6 de 105— y **no caza el otro**, que se queda en el 57. Vale la
pena leer por qué: pregunta si Empresa conoce algún cliente capaz de producir a escala
industrial con un biopolímero concreto. Pide un contacto, no un servicio, **y lo pide con el
vocabulario exacto de una solicitud técnica**. Distinguirlo exige saber qué hace y qué no
hace la organización, no leer mejor el texto.

**Con la lista de sospecha, el circuito pasaría de dos oportunidades espurias a una.**

#### Lo que no se puede concluir

Hay catorce negativos. Siete vías comparadas sobre catorce casos significa que **la mejor lo
es en parte por azar**, y las bandas limpias bailan de una repetición a otra —la desviación
está en la tabla—. Lo que sí aguanta es el orden de magnitud: las representaciones densas
están por encima de las palabras solas, y la lista corta funciona. Para afinar haría falta
exportar del buzón **sin filtrar**, que es lo que 4.6.9 ya reclama.

---

### E42 · A7 · El historial de la cuenta en la ficha, y el alta como precondición
**Fecha:** 09-10-2026 · 105 correos · `F8_A8_briefing_traspaso.py` v3 · `A0_circuito_recepcion.py`

**Por qué.** D27 decide que la ficha lleve lo que la organización ya sabe de la empresa. Esto
mide **cuánto se puede llevar de verdad**, que no es lo mismo.

**Seis campos nuevos, y su cobertura sobre los 105 mensajes.**

| Campo | Consta en | De las 53 cuentas identificadas |
|---|---|---|
| Oportunidades previas | 53 | 26 tienen alguna; en 27 la respuesta es «ninguna» |
| Ganadas previas | 53 | **solo 7 han ganado algo alguna vez** |
| Ofertas previas | 53 | 15 han recibido presupuesto antes |
| Días desde la última | 26 | solo donde hay algo previo que fechar |
| Área habitual | 20 | 20 tienen un área registrada |
| Situación de alta | 105 | se resuelve siempre, conste la cuenta o no |

#### 🔑 Un cero es un dato, y por poco no se cuenta como tal

La tabla distingue dos cosas que es fácil confundir: **el campo consta** en las 53 cuentas
identificadas, y **el campo vale cero** en buena parte de ellas. «Esta empresa no ha ganado
nunca nada con nosotros» informa tanto como «ha ganado tres veces», y la ficha lo escribe. El
primer recuento, de hecho, declaró 7 de 105 donde la respuesta era 53 por tratar el cero como
ausencia: es el error X30.

**El sesgo del corpus queda a la vista.** De las 53 cuentas identificadas, 26 tienen
historial de oportunidades pero **solo 7 han ganado alguna**. El registro de los clientes
recurrentes es mucho más fino que el de quien escribe por primera vez, y los 52 mensajes cuya
cuenta no se identifica **llegan sin historial de ningún tipo**. La ficha lo dice en lugar de
dejar el hueco en blanco, que es lo que permite distinguir «cliente nuevo» de «dato que
falta».

**Ningún campo incorpora importes**, por la decisión D13.

#### El alta de la cuenta, medida sobre el circuito

| Situación | Mensajes | Qué puede hacer el sistema |
|---|---|---|
| La cuenta consta | 44 | crea la oportunidad con su asunto, su área y su probabilidad |
| La cuenta no consta | 35 | prepara la ficha y **propone** el alta |

Las 35 solicitudes de empresas desconocidas no producen 35 propuestas sino **29**: tres
dominios habían escrito más de una vez, y crear una cuenta por mensaje duplicaría registros.
Esa agrupación por dominio es lo que separa proponer altas de generar basura.

#### Lo que no se puede concluir

**Cobertura no es acierto.** Que un campo conste no dice que sea el dato que el responsable
comercial necesita; dice que existe y que no se ha inventado. El historial se **lee** del
sistema de gestión, de modo que su corrección es la de ese sistema y no la del agente. Y todo
lo anterior se apoya en que la cuenta se identifique: con 53 de 105, la mitad de la ficha
histórica **no existe por falta de cuenta, no por falta de método**.

---

## 4 · Hallazgos sobre la calidad de los datos

| # | Hallazgo | Fecha | Estado |
|---|---|---|---|
| C1 | `validacion_clasificaciones.xlsx`: la columna `es_correcto` está vacía en las 263 filas. La validación humana se preparó pero nunca se completó | 21-09 | Pendiente (≈2 h de trabajo) |
| C2 | Solo el 53 % del dataset antiguo tenía texto web; 994 empresas sin URL | 21-09 | Resuelto con el scraping |
| C3 | Banners de cookies contaminando el texto: en algunas webs las palabras de mayor peso eran `cookielawinfo`, `gdpr`, `consent` | 26-09 | Resuelto (limpieza) |
| C4 | 3 empresas aparecían a la vez en train y test (fuga de datos) | 21-09 | Resuelto |
| C5 | 24 subsectores cuelgan de más de un sector (5.154 filas) | 25-09 | Marcado, no corregido (D3) |
| C6 | El campo `Probabilidad` de las ofertas tiene valor máximo 800 (debería ser 0-100) | 25-09 | Pendiente de limpiar |
| C7 | 2.288 cuentas del export sin sector o sin nombre | 25-09 | Eliminadas |
| C8 | El primer export de cuentas no incluía la columna `Sitio web` | 25-09 | Resuelto (reexport) |
| C9 | `Tamaño cuenta` informado en el 93,8 % de las cuentas valoradas frente al 27,9 % de las no valoradas | 27-09 | Cuantificado (E14): cuesta 4,9 puntos |

---

## 5 · Errores cometidos y corregidos

Se anotan por honestidad metodológica y porque varios habrían invalidado resultados.

| # | Error | Consecuencia si no se detecta | Cómo se detectó |
|---|---|---|---|
| X1 | El script de preparación reasignaba automáticamente el sector de 5.154 filas (24 % del dataset) | Etiquetas oficiales sobrescritas en silencio; los resultados no serían sobre los datos reales de Empresa | Revisión del propio código antes de dar por bueno el resultado |
| X2 | Sobrevaloré el impacto de limpiar los banners de cookies. Medido: +0,83 puntos, no la mejora grande que anuncié | Habría justificado el esfuerzo con un número falso | Se midió en lugar de suponerlo |
| X3 | El detector de plantillas por frecuencia en el corpus no funciona: encuentra 0 plantillas al 5 % de umbral | Habría quedado en la memoria como técnica útil sin serlo | Se midió |
| X4 | El prompt de few-shot ocupaba 6.691 tokens con el límite en 4.096: se habría cortado dejando fuera la empresa a clasificar | Resultados sin sentido, sin ningún aviso | Prueba en local antes de gastar GPU |
| X8 | Las señales del catálogo se buscaban como subcadena: `pla` encontraba "planta" (66,8 % de las webs) y `pet` encontraba "competencia". Además la normalización eliminaba el `+` de `i+d`, dejándolo inbuscable | El método léxico habría parecido funcionar (33 % fiable) cuando en realidad es 17,5 %, y se habría descartado el semántico | Frecuencias imposibles al analizar la especificidad de las señales |
| X7 | El modelo de conversión incluía `es_cliente`, variable circular respecto al objetivo. Inflaba el AUC de 0,774 a 0,829 y el ratio de priorización de 16,3× a 24,9× | Se habría reportado una capacidad de priorización un 50 % superior a la real | Revisión antes de registrar el resultado |
| X6 | El script de LLM no guardaba la respuesta cruda del modelo, solo la interpretada. Impedía diagnosticar el 34,7 % de respuestas inválidas de Salamandra | Sin saber *qué* contestaba, no se puede distinguir un fallo de formato de uno de comprensión | Al analizar E7. Corregido |
| X5 | Los notebooks se generaron sin saltos de línea en las celdas: Colab concatenaba todo el código en una línea | Los notebooks no funcionaban | Error de sintaxis al ejecutar |
| X13 | `06_MODELOS_POR_AGENTE.md` contenía un párrafo redactado para la memoria que afirmaba que la elección de modelos de árboles estaba «verificada experimentalmente», cuando el experimento estaba pendiente (M4) | Se habría afirmado en la memoria una medición inexistente, y con un número de apartado concreto | Al redactar el apartado 4.2.5 y buscar la tabla a la que remitía el párrafo |
| X10 | Buena parte de los análisis (E9, E11, E12, E13, E15, E16 y todo F6) se ejecutó de forma exploratoria y solo se guardaron los resultados, no el código | Las cifras centrales del trabajo no eran recomprobables por nadie, incluida la autora | Pregunta directa de la autora: «¿dónde estás haciendo esas pruebas?» |
| X11 | El modelo final de A2 está en `pred_abl_sin_jerarquia.csv`, no en `pred_principal.csv`: la ablación resultó mejor y pasó a ser el modelo final, pero los ficheros mantuvieron su nombre original | Al escribir el script de contrastes se comparó el modelo equivocado y pareció que la bitácora estaba mal (p = 0,026 en lugar de 0,002, y diferencia de F1-macro negativa) | El cotejo automático incorporado a `F2_A2_E9_E11_contrastes.py` |
| X12 | **Error del auditor, no del experimento.** Al verificar E16 declaré que su ratio de priorización (16,3×) no se reproducía, comparándolo con un 4,6× que yo mismo había calculado. Eran dos métricas distintas —cociente entre quintiles frente a lift del decil sobre la tasa de base— y sobre dos poblaciones distintas: cuentas valoradas (12 % de conversión) frente a la cartera entera (3,5 %) | Se habría sustituido una cifra correcta por otra que mide algo distinto, y se habría debilitado sin motivo la conclusión de E16 | Releer el texto original de E16 antes de aplicar la corrección: decía «el 20 % mejor frente al 20 % peor», no «sobre la base» |
| X14 | Al generar la figura de deciles salió que la reconstrucción de E16 predice **tener una venta ganada** (12,1 % de base) mientras que la cifra publicada se calculó sobre **tener una oportunidad**, que es más frecuente. De ahí que el decil superior sea 47,1 % reconstruido y 29,5 % publicado | La figura habría contradicho al texto del apartado 4.6.2 sin que ninguna de las dos cifras estuviera mal | Al escribir el cotejo de `FIG_resultados.py`, que compara cada cifra dibujada con la publicada. **No es un error de cálculo: es una variable objetivo distinta.** Queda por decidir cuál adopta la memoria (ver Preguntas abiertas) |
| X15 | Al cruzar los dominios de los correos contra el CRM usé el fichero `_anon.csv`, donde la columna `Sitio web` está **seudonimizada**: son códigos, no dominios. Salieron 0 coincidencias de 48 | Habría reportado un 0 % de resolución por dominio, contradiciendo el 25 % ya publicado y hundiendo sin motivo la viabilidad del paso 2 de A6 | Que cero de cuarenta y ocho no es un resultado creíble. Las URL reales están en los ficheros derivados. El script lleva ahora un aviso que salta si vuelve a salir 0 |
| X16 | En E23 di por causa del fallo del emparejador que «los servicios se describen demasiado parecido». Lo escribí marcándolo como no medido, pero lo escribí | Habría orientado el trabajo a reescribir el catálogo, que es justo lo único que **no** falla: es separable 14 de 14 | La autora preguntó por esa afirmación concreta. Se midió en E24 y la causa real es otra: el modelo agrupa por género de texto, no por tema. **Marcar algo como no medido no autoriza a afirmarlo** |
| X17 | La columna `Tema` del export de oportunidades tenía asignado el tratamiento LIMPIAR, que solo normaliza espacios y acentos. Es texto libre del equipo comercial y el 70 % de sus 4.878 filas contiene alguna palabra capitalizada: nombres de producto y marcas de clientes | El nombre de la cuenta estaba seudonimizado, pero el tema podía reidentificar al cliente por sí solo. Llevaba así desde el primer día en la carpeta de datos limpios | Al preguntar la autora por la confidencialidad del catálogo de servicios. Su hipótesis (que las fichas salían de `Tema`) era falsa, pero la pregunta destapó una fuga distinta y mayor |
| X18 | Di por protegido el texto comercial al sacarlo de la carpeta de trabajo, sin caer en que un TF-IDF con clasificador lineal **guarda el vocabulario dentro del modelo**: 3.382 términos, de los cuales el 47 % de los más influyentes aparece en cinco asuntos o menos | La forma natural de explicar un modelo lineal en una memoria es una tabla de términos influyentes por clase. Publicarla habría publicado el vocabulario comercial con el fichero de datos perfectamente guardado | La autora insistió en que el texto seguía usándose «tal cual». Medido en E26. **Proteger el fichero no protege el modelo** |
| X19 | Usé «dominio» para dos cosas distintas —el `@dominio` de un correo y el dominio extraído del campo *Sitio web*— y reporté el techo del 70 % de cuentas con web como si fuera el techo del sistema | La memoria afirmaba que la resolución de identidad no puede superar el 70 %. Es falso: esa cota solo afecta a la tercera vía; la búsqueda por contactos no depende de ese campo | La autora señaló que estábamos hablando de cosas distintas. Corregido en D18. **La cifra del 29,2 % sigue siendo correcta: lo que estaba mal era presentarla como el límite del sistema** |
| X20 | Para probar la biblioteca de sectores **reimplementé el entrenamiento desde cero** en vez de añadir una opción al script que ya reproducía el 51,73 %. La reimplementación se desviaba en cinco cosas: sin calentamiento del ritmo de aprendizaje, sin ritmo decreciente, sin decaimiento de pesos, sin quedarse con la mejor época, y entrenando con train+val en lugar de train | **Dos horas de GPU perdidas.** La referencia dio 43,59 % en vez de 51,73 %, ocho puntos abajo, de modo que ninguna comparación era válida. Y la variante con biblioteca se quedó en el 2,04 % —por debajo del suelo— porque inyectaba las descripciones en la cabeza de dos capas de `AutoModelForSequenceClassification` cuando la arquitectura real es una sola capa lineal sobre media enmascarada: dos espacios distintos | La pérdida no se movió en cuatro épocas (3,698 → 3,693, y ln 41 = 3,71: azar puro). **El propio script avisaba** de que con la referencia desviada no se interpretara nada. Corregido añadiendo `--biblioteca` al script original |
| X21 | Dos fallos seguidos en la misma función de inicialización con la biblioteca: **(a)** los vectores quedaban en la CPU y el peso en la GPU, lo que abortó la ejecución; **(b)** al reescalar, multiplicar una matriz de filas normalizadas por la desviación típica la dejaba **28 veces más pequeña** de lo pretendido | El primero solo costó tiempo: falló antes de entrenar. **El segundo era el peligroso**: no produce error, produce un resultado falso. Con la capa inicializada casi a cero, las descripciones apenas habrían pesado y el experimento habría concluido «la biblioteca no aporta» por un motivo equivocado | El primero, en la propia ejecución. El segundo, al verificar la aritmética con tensores simulados **antes** de entregar el paquete. La lección: comprobar los cálculos antes de gastar procesamiento gráfico ajeno |
| X22 | Dije que el orquestador quedaba **integrado en la memoria** y no lo estaba. Llegó a la bitácora, a 14_REPRODUCIBILIDAD, al capítulo 7 y a sus dos figuras, pero **no al capítulo de resultados ni al de discusión**. Los cambios se aplicaron con ficheros `_patch.py` desechables cuyo resultado no se cotejó después | **El trabajo se contradecía a sí mismo durante tres días.** El capítulo 5 afirmaba «el sistema secuencial no se construyó» y marcaba el objetivo 3 en rojo, mientras el capítulo 7 describía el prototipo ya integrado; y remitía a un apartado 4.6.5 que hablaba de otra cosa. Un evaluador que coteje objetivos contra resultados —lo primero que se hace— habría encontrado el objetivo que da título al trabajo declarado incumplido por su propia autora, teniéndolo cumplido | Al cotejar la numeración de las figuras apareció un ancla que no existía: la de un apartado 4.6.5 del orquestador que nunca se escribió. **Lo encontró una comprobación de otra cosa, no una revisión del contenido.** Corregido con `PREP_integrar_orquestador_memoria.py`, que releé cada fichero después de escribirlo y falla si algo no cuadra |
| X23 | La comprobación con que di por buena la numeración de las figuras **era ciega a los duplicados**: contaba los marcadores con `uniq -c` y luego imprimía solo el número, descartando el recuento, de modo que «2 [FIGURA 7]» se veía igual que «1 [FIGURA 7]» | Di por correcta una numeración que tenía **dos figuras con el número 7** y le faltaban dos de las veintiuna. Es el peor tipo de comprobación: la que no detecta nada y produce la confianza de haber comprobado | Al reejecutar el renumerador avisó de doce cambios pendientes sobre un fichero que yo había declarado correcto. Corregido escribiendo `FIG_cotejar_numeracion.py`, que comprueba unicidad, concordancia marcador–fichero, cobertura de las veintiuna y existencia de los png, y devuelve código de error. **La lección: una comprobación que no distingue «una vez» de «dos veces» no comprueba nada** |
| X24 | Al cargar las fechas del export anonimizado pasé `dayfirst=True` a `pd.to_datetime`, pero venían en formato ISO (`2025-01-25 14:00:47`). Pandas leyó el 25 como MES, lo declaró inválido y devolvió `NaT` | **Se perdieron dos tercios de las filas en silencio.** A7 se entrenó con 1.060 casos y se evaluó con 155 en vez de 2.680 y 684, y la primera cifra que obtuve —72,9 % de acierto— era de un conjunto de prueba cuatro veces menor, o sea mucho menos fiable. No dio ningún error: solo menos datos | Al extrañarme de que un fichero de 4.881 filas diera 2.002, conté los `NaT` por trimestre y aparecieron 2.723 sin fecha. Quitando `dayfirst` se leen todas. **La cifra buena es 66,2 %, no 72,9 %**, y es la que está publicada. La lección: un filtro que descarta filas tiene que decir cuántas descarta |
| X25 | Para la cuarta pieza de A6 etiqueté los correos no comerciales con una **lista de términos** —«proveedor», «webinar», «prácticas»— y publiqué un AUC de 0,700 obtenido con ella, **sin contrastar la etiqueta contra ningún juicio humano** | **De los quince correos que la lista marcaba, solo dos lo eran.** Diez fallos venían de la palabra *proveedor*, que en este corpus aparece en correos de CLIENTES hablando de sus propios proveedores: «la caja la fabrica nuestro proveedor, ¿qué ensayos debe superar?». En este registro esa palabra es señal COMERCIAL, o sea lo contrario de lo que yo suponía. La lista tenía una precisión del 13,3 % y una cobertura del 14,3 %: el modelo no medía lo que yo creía, medía su capacidad de reproducir una lista equivocada | La autora preguntó qué significaba «si son comerciales o no». Al mirar el contexto de los quince uno a uno aparecieron los falsos positivos, y ella clasificó los 105 a mano. Con la etiqueta buena el AUC es **0,919 [0,828, 0,980]**. La cifra de 0,700 queda retirada. **La lección: una etiqueta automática se contrasta contra el juicio humano ANTES de publicar nada obtenido con ella; una métrica puede salir excelente midiendo lo que no es** |
| X26 | Publiqué que A6 «resuelve solo el 75,2 % de los mensajes» contando igual los de cuentas conocidas y los de empresas que el sistema no identifica | **La cifra mezclaba dos cosas distintas.** Por la decisión D19 el sistema no da de alta cuentas por su cuenta, de modo que un mensaje bien enrutado de una empresa desconocida sigue necesitando a una persona. De los 79 que el agente resuelve, solo 28 son de cuentas registradas: la automatización completa es del **26,7 %, no del 75,2 %** | La autora preguntó si las pruebas de A6 se hacían sobre los correos cuya cuenta se localiza o sobre todos. Al mirarlo, la función que decide **no consultaba la identidad en absoluto**. Corregido cruzando las dos cosas en el paso 5, y la memoria publica ahora las dos cifras con la diferencia explicada. **La lección: antes de publicar un porcentaje, comprobar que el numerador y el denominador midan la misma cosa.** Nota posterior: con E35 esa cifra subió al 42,9 %, porque la identidad pasó a resolverse también por el campo `Dominio` |
| X27 | Presenté A6 y A8 como dos agentes que enrutan al área técnica sin declarar que **emplean el mismo clasificador**, y sin declarar que de A8 solo se construyó una de sus dos funciones | El diseño de la fase 8 pedía enrutar **y** redactar el briefing de traspaso. Solo existe lo primero, y es exactamente el modelo que A6 invoca. Así que **mientras el briefing no exista, la fase 8 no añade en la vía de entrada ninguna decisión que la fase 6 no haya tomado ya**, y la memoria presentaba dos capacidades donde hay una | La autora preguntó qué diferencia hay entre A6 y A8, porque le parecía trabajo repetido. Al revisarlo: el solapamiento ya estaba en el diseño de las once fases —F6 dice «sale enrutado» y F8 dice «enrutar»— y la mitad que los distinguía no se construyó. Declarado en 4.6.4, en 4.6.6 y en el 7.2b. **La lección: reutilizar un modelo está bien, pero hay que decir que es el mismo.** Nota posterior: el briefing se construyó el mismo día (E37), de modo que las dos fases vuelven a distinguirse por algo real |
| X28 | El diccionario que detecta normas y materiales toleraba un sufijo de hasta tres letras para que «ensayo» encontrara «ensayos». Aplicado a siglas, **«reach» encontraba «reached» y «reaching»** | El briefing proponía «Ensayo · REACH» para un correo que hablaba de biodegradación, y el agente lo enrutaba al área equivocada. Tres falsos positivos de 105, dos de ellos cambiando el veredicto del correo. **Todos en los correos en inglés**, que son el 21,9 % del corpus, de modo que era un sesgo de idioma además de un error | Lo destapó el verificador de fundamentación del propio briefing: dio 99,1 % cuando por construcción tenía que dar 100 %. Corregido limitando la tolerancia al **plural castellano** —«caidas» sí, «reached» no—. Las cifras de A6 se rehicieron: las normas reconocidas bajan de 53 a 50, y el enrutado sobre correo real **sube** del 75,6 % al 79,5 %, porque esos casos estaban mal clasificados. **La lección: una comprobación que debe dar el 100 % por construcción hay que ejecutarla igualmente** |
| X29 | El recortador de palabras dejaba «envase» tal cual pero convertía «envases» en «envas»: la regla del plural mira «es» al final y «envase» acaba en «se». **La misma palabra no se reconocía a sí misma en plural** | La comprobación de fundamentación del briefing daba 84,4 % donde por construcción tenía que dar 100 %. Afecta igual a «embalaje/embalajes» y «informe/informes», y al verificador de A5, que usa otro recortador con el mismo agujero. **El sentido del error importa: subestimaba, nunca infló ninguna cifra** | Lo destapó la comprobación del propio briefing al medirse contra el correo solo. Corregido quitando también la «e» final. Alcance medido en `VERIFICAR_X29_fundamentacion.py`: la fundamentación de A5 pasa de 34,84 % a 36,06 % **y su suelo de 28,77 % a 29,89 %**, de modo que la diferencia apenas se mueve (6,07 a 6,17 puntos, z de 4,76 a 4,81) y la conclusión de E19 aguanta. **La lección: una métrica que compara dos textos hay que probarla con la misma palabra escrita de dos maneras** |
| X9 | Fijé umbrales de calidad para la fundamentación de A5 ("bien por encima del 70 %", "revisar por debajo del 60 %") sin ningún control que dijera cuál es el suelo de esa métrica. El suelo real, medido después, es el 29 % | Los 40 correos habrían quedado clasificados como fallidos cuando el anclaje es significativo (p < 0,0005). O, con otro umbral, lo contrario | Control por permutación en E19, hecho al no cuadrar el número con la lectura de los correos |
| X30 | El contador de cobertura de la ficha preguntaba si el campo «tenía valor», y en Python **un cero es falso**: `0 == False`. Los campos del historial que valían cero —«ninguna oportunidad previa», «ninguna ganada»— se contaban como ausentes | La tabla de cobertura declaraba **7 campos de 105 donde la respuesta correcta era 53**, y la memoria habría dicho que el historial apenas puede rellenarse cuando se rellena en todas las cuentas identificadas. **Habría invertido la conclusión de E42**: de «un cero informa» a «no hay datos» | Lo destapó la propia tabla al leerla entera: no podían constar 53 cuentas con oportunidades previas y solo 7 con ganadas si el campo se rellena en bloque. Corregido comprobando `is not None` en vez de la verdad del valor. **La lección: en una medición de cobertura, «vacío» y «cero» son cosas distintas, y el lenguaje de programación las confunde por omisión** |
| X31 | Al actualizar la discusión escribí que el enrutado acierta «el 79,5 % de los mensajes reales **frente a un suelo del 27,1 %**». Las dos cifras existen, pero el 27,1 % es el suelo de **otra población**: la de entrenamiento, de 2.790 oportunidades. El suelo de los 41 mensajes de cliente reales es 12,8 % | La discusión habría comparado el rendimiento medido en una población con el suelo de otra, y el margen del agente habría parecido **menor** de lo que es: 52,4 puntos en lugar de 66,7. Es el mismo error que X2, X9 y X12 —poner un número en un contexto que no se ha medido— y con este van cinco | Se detectó al ir a buscar la cifra a 4.6.5 para reutilizarla en el capítulo 6: la tabla del desajuste de población daba otro suelo. **La lección: un suelo pertenece a una población, y al trasladar una cifra de un apartado a otro hay que trasladar también su referencia** |
| X32 | La tabla del desajuste de población publicaba «Suelo: la clase más frecuente **12,2 %**» cuando la medición guardada da **12,82 %**. Un dígito mal transcrito al montar la tabla | Una cifra publicada incorrecta, y de las que nadie recalcula porque parece de contexto. Además **el margen que la prosa declara —66,7 puntos— no cuadraba con la resta de su propia tabla**, que daba 67,3 | Lo destapó X31: al comprobar cuál era el suelo verdadero, la resta no cerraba. Corregido a 12,8 % en la tabla y en las dos copias de la cifra que ya se habían escrito en los capítulos 5 y 6. **Y se ha añadido al cotejo automático**, que ahora compara contra el JSON el acierto, el suelo y el margen de esta pieza. La lección: cuando una tabla trae también el resultado de una resta, hacer la resta |
| X33 | La carpeta de entrega **no entregaba el sistema vigente**. `F5_A5_E20_campana.py` —el modo campaña, que es el diseño de A5 en vigor desde que se retiró la selección automática de servicio, y de donde sale el ×3,9 de RQ4— estaba clasificado como experimento, mientras `1_SISTEMA` llevaba la versión anterior. Además el sistema **no arrancaba** desde esa carpeta: dos documentos que los guiones leen al ejecutarse —el catálogo de servicios y el de campañas— solo iban en `3_DOCUMENTACION`. Y quedaban copias viejas, porque el guion de montaje solo copiaba y nunca retiraba: un script del 04-10 cuando su original era del 06-10 | Quien reprodujera el trabajo desde la entrega habría ejecutado **la versión de A5 que se descartó**, el generador de campaña habría salido con «No encuentro 12_CAMPANAS.md», y habría leído una copia de dos días antes de un guion ya corregido. Es el riesgo de X11 —comparar el fichero equivocado— trasladado a la entrega | Lo destapó una pregunta de la autora: «este script no lo puedo ver en MASTER PRESENTACION». Corregido: E20 pasa a `1_SISTEMA`, los dos documentos se copian también donde los guiones los buscan, y el montaje **nombra y retira** lo que sobra en las dos carpetas que genera. **La lección: un guion de empaquetado que solo copia no produce una copia reproducible, porque lo que deja de estar en la lista sigue estando en el disco** |
| X34 | El apartado de reproducibilidad afirmaba que **«todos los experimentos emplean semilla aleatoria fija (42)»**. La semilla gobierna los repartos de datos y el muestreo de empresas, pero la redaccion de los correos usa muestreo con temperatura 0,6 **sin fijar la semilla del generador**: repetir la ejecucion da correos distintos | Una afirmacion de metodo falsa, y en el apartado que se lee precisamente para decidir si fiarse del resto. Quien repitiera una ejecucion obtendria otros correos y concluiria que el trabajo no es reproducible, cuando lo que no es repetible es la generacion y no la medicion | Se destapo al decidir si el brief leido desde Word debia ser identico cadena a cadena al del .md: al comprobar si eso importaba, aparecio que la generacion nunca fue reproducible cadena a cadena. Corregido declarando la excepcion y lo que si es determinista —la seleccion de empresas, la evidencia y la verificacion—, y senalando que fijar la semilla es una correccion de una linea. **La leccion: «todos» es una palabra que hay que comprobar agente por agente antes de escribirla** |
| X35 | El capítulo 4.1 declaraba **«tres agentes se construyeron y ocho se diseñaron»** y daba por **no integrado el sistema secuencial**, cuando son seis construidos y los dos circuitos del orquestador están medidos desde D17. Además fechaba la redacción hasta el 13 de octubre | El capítulo de planificación contradecía al de resultados y al de discusión en el número de agentes y en el objetivo que da título al trabajo. **Es el mismo fallo que X22**, en el único capítulo donde no se había cotejado: un evaluador que compare la planificación con los resultados encuentra el trabajo desdiciéndose a sí mismo | Al ampliar el apartado 4.1.4 hubo que releer el capítulo entero. **Lo destapó escribir otra cosa, no una revisión del contenido** — igual que X22. Corregido con `PREP_ampliar_asistencia_ia.py`, que relee y falla si algo no cuadra |
| X36 | La renumeración de agentes de D24 (A8→A7, A9→A8) falló de **tres maneras distintas, todas invisibles para un recuento**: el pie de una figura recibió el pase dos veces y quedó con el agente equivocado; las variantes con letra —`A7a`, `A8b`, `A9a`— no casaban con el patrón de palabra completa y dejaron la tabla de familias de modelo mezclando numeración vieja y nueva; y un texto que ya estaba escrito con los nombres nuevos se volvió a renumerar, convirtiendo «A6, A7 y A8» en «A6, A7 y A7» | La memoria habría llamado al mismo agente de dos maneras según el apartado, y en un trabajo cuyo índice son los agentes eso no es una errata: es no poder seguir el sistema. **El recuento de apariciones daba correcto en los tres casos** | Al leer una muestra de cada clase de aparición con sesenta caracteres de contexto, en vez de contarlas. De aquí sale la regla permanente de la tabla 12d: las sustituciones masivas se aplican una sola vez, con marcas intermedias, y después se lee. **Anotado el 18-10 al escribir el apartado 4.1.4: el fallo es del 07-10 y se había corregido sin registrarlo** |

**Nota metodológica:** X2 y X3 son resultados negativos y se conservan. Una técnica que
se prueba y no funciona es información, no un fracaso, siempre que se declare.

**Lo que anade X12.** Los tres casos anteriores son de no medir el contexto. X12 es
distinto y merece nombrarse aparte: **medir algo parecido y darlo por lo mismo**. Un
ratio de priorizacion no significa nada sin decir *entre qué grupos* (deciles, quintiles,
frente a la base) y *sobre qué población*. Dos definiciones razonables del mismo concepto
daban 16,3× y 4,6× sin que ninguna estuviera mal calculada.

Es un riesgo propio de la fase de revisión: quien audita llega con su propia definición
y, al no coincidir, concluye que el original está mal. La verificación tiene que empezar
por releer qué se midió exactamente, no por recalcularlo a la primera interpretación
razonable.

**Un patrón que se repite (X2, X9 y las dos afirmaciones sobre significación estadística):**
en los cuatro casos el error consistió en **poner un número en contexto antes de medir el contexto**.
Un 34,8 % de fundamentación, un +0,83 de mejora o una diferencia de 2 puntos no son buenos ni
malos en abstracto: dependen del suelo, del control y de la variabilidad, que son precisamente
lo que hay que medir. No fueron descuidos independientes sino la misma omisión repetida.


#### Redacción sugerida para la memoria

> La cualificación de solicitudes mediante un clasificador entrenado sobre el histórico
> alcanza un 66,2 % de acierto frente a un suelo del 56,9 %, con un AUC de 0,714
> [0,677, 0,753]. El recuento de los criterios del marco de cualificación, en cambio, no
> ordena mejor que el azar (AUC 0,492). Este segundo resultado **no refuta el marco**: en el
> texto disponible los criterios aparecen con una media de 0,45 de siete, de modo que su
> recuento carece de capacidad discriminante por ausencia de materia prima y no por
> invalidez del constructo. La comprobación sobre texto en que los criterios sí aparecen
> requeriría mensajes de cliente con resultado comercial asociado, que no existen.


---

## 6 · Preguntas abiertas

### Qué significa exactamente «oportunidad ganada»
**Fecha:** 09-10-2026 · `VERIFICAR_embudo_oportunidad_oferta.py` · lo preguntó la autora

**La pregunta.** «¿Entiendes que una oportunidad ganada quiere decir que se tiene que
transformar en oferta y luego ganarse?» Era una comprobación de si el modelado respetaba el
proceso real. Se midió en lugar de contestarla de memoria.

**El embudo existe y es casi estricto.** De 3833 oportunidades cerradas,
3002 llegan a tener oferta. Y de las 2097
ganadas, **solo 2 no tienen oferta asociada** —un
0,1 %, probablemente un enlace
que falta entre las dos tablas—. Para ganar hay que presupuestar.

| Paso | Pasan |
|---|---|
| 1 · la oportunidad llega a oferta | 78,3 % [77,0, 79,6] |
| 2 · presupuestada, se gana | 69,8 % [68,1, 71,4] |
| **1 y 2 · lo que A8 llama «se gana»** | **54,7 %** |

78,3 × 69,8 = 54,7.
**La etiqueta de A8 es el producto de dos pasos, no uno.**

#### 🔑 Y «no ganada» esconde dos fracasos distintos

| De las 1736 no ganadas | |
|---|---|
| Nunca llegaron a presupuestarse | 829 · 47,8 % |
| Se presupuestaron y se perdieron | 907 · 52,2 % |

Casi mitad y mitad, **y el modelo las trata igual**. Para un comercial no son lo mismo: la
primera se corrige cualificando mejor o respondiendo antes; la segunda, con el precio, el
plazo o la competencia.

**Qué cambia y qué no.** A8 sigue estando bien construido: predice el resultado final con lo
que se sabe **al registrar** la oportunidad, que es antes de que la oferta exista, y esa es la
pregunta que la organización se hace en ese momento. Lo que no puede decirse es que prediga
«si se gana la oferta». Predice el recorrido completo, y así queda escrito en 4.6.7.

**Lo que abre.** Separar los dos pasos en dos modelos —«llegará a oferta» y, una vez
presupuestada, «se gana»— es una continuación con datos ya disponibles. El segundo contaría
además con la probabilidad que declara el comercial, que solo existe cuando hay oferta: de
ahí que en la prueba de 4.6.7 solo 527 de 721 casos tengan estimación humana con la que
compararse.

---

### ¿Qué cifras de priorización adopta el apartado 4.6.2?

Las dos versiones son correctas y miden objetivos distintos (ver X14):

| | Reconstrucción reproducible | Publicado en E16 |
|---|---|---|
| Qué predice | tener una **venta ganada** | tener una **oportunidad** |
| Tasa de base | 12,1 % | más alta |
| AUC | 0,788 | 0,774 |
| Ratio quintil superior / inferior | **14,7×** | **16,3×** |
| Decil superior | 47,1 % | 29,5 % |

El ratio entre quintiles, que es la métrica que la memoria titula, coincide
razonablemente. El decil superior no, y por el motivo anterior.

**Dos salidas posibles.** Adoptar las cifras de la reconstrucción, que son las
que un tercero puede reproducir lanzando un script; o declarar las dos y
explicar la diferencia. Lo que no puede quedarse es la figura 10 diciendo una
cosa y el texto otra.

`FIG_resultados.py` lo avisa cada vez que se ejecuta.


| # | Pregunta | Bloquea | Cómo resolverla |
|---|---|---|---|
| P1 | ¿Cuánto del error residual es ruido de etiqueta del propio CRM? | Saber el techo alcanzable de A2 | Completar las 263 filas de C1 y medir la concordancia humano–CRM |
| P2 | ¿Supera el transformer al modelo lineal? | Cerrar A2 | Paso 6 |
| P3 | ¿Qué distinciones de subsector cambian realmente lo que hace Empresa? | Decidir el nivel operativo | Preguntar a negocio |
| P4 | ¿Se puede registrar más de un área por oportunidad en el CRM? | Diseño de A8 (multi-etiqueta o no) | Preguntar a sistemas |
| P5 | ¿Existe histórico del formulario web o del buzón de contacto? | A6 con datos reales frente a sintéticos | Preguntar a marketing |
| P6 | ¿Está el playbook validado por el responsable comercial? | Objetivo específico 1 | Reunión de 60-90 min |


---

## 7 · Mediciones pendientes y prompts para retomarlas

### M7 · ¿Mejora A2 si ve la biblioteca de sectores?

**De dónde sale.** E30 estableció que la biblioteca de descripciones existe —38
sectores con criterio de inclusión y exclusión— y que metida en el *prompt* de un
modelo cerrado no superó al supervisado (39,87 % frente a 51,73 %). Pero el
transformer nunca la ha visto: se entrenó con pares texto → etiqueta.

También hay un indicio a favor sin explotar: en aquella misma evaluación, el modelo
acertó más clasificando 183 subsectores **con** descripción (46,35 %) que 39 sectores
**sin** ella (39,87 %). Más clases y mejor acierto no es lo normal.

**Qué está preparado.** El script de entrenamiento original lleva ya la opción
`--biblioteca`, con dos modos:

| Modo | Qué hace |
|---|---|
| `inicial` | La capa de salida arranca con las descripciones codificadas y luego se mueve libremente |
| `fija` | La capa queda clavada en las descripciones: el modelo debe llevar el texto hasta ellas |

Las descripciones se codifican por la **misma vía** que usa el modelo —media
enmascarada del codificador— y se reescalan a la desviación típica de la
inicialización por defecto, para conservar la geometría sin desajustar la
optimización. Haberlo hecho sobre otra arquitectura fue el error X20.

**Cómo lanzarlo.** `A2_biblioteca_colab.ipynb` y `paquete_biblioteca_v2.zip`.
Dos ejecuciones de una hora:

```
--alfa 0 --beta 0 --etiqueta e31_referencia
--alfa 0 --beta 0 --biblioteca inicial --etiqueta e31_biblioteca
```

**Condición de validez:** si la referencia no sale cerca del 51,73 %, no se
interpreta nada. Es la lección de X20.

**Qué mirar:** el F1-macro antes que el acierto. La ganancia esperada está en los
sectores con pocos ejemplos, que apenas mueven el acierto global.


### M6 · ¿Cuánto cae el enrutado al pasar de `Tema` a texto de cliente?

**De dónde sale.** E25 midió 78,97 % de acierto entrenando y validando sobre
`Tema`. E25 también midió que `Tema` y el correo de un cliente son registros
distintos. Falta saber cuánto cuesta el salto.

**Qué haría falta.** Etiquetar a mano el área de los 52 correos del corpus de
entrada —trabajo de una tarde— y aplicar sobre ellos el clasificador entrenado
con `Tema`. La caída respecto al 78,97 % es la medida del desajuste.

**Por qué importa.** Es la diferencia entre un dato honesto y una cifra que
promete lo que no puede cumplir. Sin esta medición, el 78,97 % debe reportarse
declarando que es un techo.

**Prompt para retomarlo:**

```
Retomamos la medición M6 de la bitácora del TFM.

Tengo etiquetada a mano el área de cada uno de los 52 correos de
datos/01_limpio/entradas_inbound_50_anon.csv. Entrenar el clasificador de
F8_A8_utilidad_tema.py sobre `Tema` (carpeta privada) y evaluarlo sobre esos 52
correos. Comparar con el 78,97 % de E25 y con el suelo de la clase mayoritaria
en la nueva población.
```


### M5 · ¿Arregla el emparejamiento traducir la petición al registro del catálogo?

**De dónde sale.** E24 estableció que el emparejador falla por un desajuste de
género: un correo se parece más a otro correo (0,872) que al servicio que pide
(0,823). La hipótesis es que extraer la necesidad como enunciado técnico breve
antes de emparejar convierte el problema en ficha contra ficha, que el modelo sí
resuelve (14 de 14).

**Qué haría falta.** GPU, para ejecutar el modelo generativo sobre los 52
correos y obtener el enunciado normalizado. Después se repite el emparejamiento
y se compara contra el 39 % actual, sobre los mismos 18 correos con área
inequívoca.

**Cuidado con la circularidad.** El enunciado extraído no puede construirse con
el diccionario de normas, porque ese diccionario es el que define la respuesta
correcta. Sería el error X7 otra vez.

**Prompt para retomarlo:**

```
Retomamos la medición M5 de la bitácora del TFM.

Sobre datos/01_limpio/entradas_inbound_50_anon.csv, usar un modelo abierto en
Colab para extraer de cada correo la necesidad como enunciado técnico breve, sin
usar el diccionario de normas. Repetir el emparejamiento contra
datos/03_resultados/a5_catalogo.json y comparar el acierto con el 38,9 % de E24
sobre los mismos 18 correos con área inequívoca. Declarar el suelo (14,3 %).
```


Cada entrada tiene un **prompt listo para copiar y pegar** en una sesión nueva. Incluye
el contexto necesario para que se pueda retomar sin releer toda la bitácora.

---

### M1 · Separar comprensión de cumplimiento de formato en los LLM

**Por qué está pendiente:** Salamandra obtuvo 16,0 % frente al 33,3 % de Qwen, pero el
34,7 % de sus respuestas fueron inválidas. No sabemos cuánto de esa diferencia es peor
comprensión de la taxonomía y cuánto es peor seguimiento de instrucciones.

**Por qué importa:** sin esto no se puede afirmar nada sobre la comprensión relativa de
los modelos, solo sobre su obediencia. Y una comparación mal planteada es más peligrosa
que no hacerla.

**Método correcto — elección forzada por verosimilitud.** En lugar de dejar que el modelo
genere texto libre, se calcula la probabilidad que asigna a cada una de las 41 categorías
y se elige la más alta. Así **el modelo no puede fallar el formato**, porque no genera:
solo puntúa. Los dos modelos quedan comparados en comprensión pura.

**Prompt para retomarlo:**

```
Retomamos la medición M1 de la bitácora del TFM (MASTER/08_BITACORA.md).

Contexto: comparamos dos LLM abiertos clasificando empresas en los 41 sectores de
Empresa. Qwen2.5-7B sacó 33,33% con 99,3% de respuestas bien formateadas. Salamandra-7B
sacó 16,00% pero con solo 65,3% bien formateadas, así que la comparación no es válida.

Lo que necesito: modificar scripts/F2_A2_E5_E7_llm_abierto.py para que en vez de generar texto
libre calcule la verosimilitud de cada una de las 41 categorías y elija la mayor
(elección forzada). Así ningún modelo puede fallar el formato y se compara comprensión
pura. Luego relanzar los dos modelos sobre las mismas 300 empresas y comparar contra
el 48,91% del modelo supervisado.

Los datos están en MASTER/datos/02_derivado/ y el paquete de Colab en
MASTER/paquete_colab.zip.
```

---

### M2 · Test de McNemar  ✅ *(parte del transformer resuelta en E9; falta la de los LLM)*

**Resuelto:** transformer frente a lineal → p = 0,026 (sector) y p = 0,005 (agrupado).
**Pendiente:** zero-shot frente a few-shot, requiere los dos CSV de Qwen desde Colab.

#### Parte pendiente: zero-shot frente a few-shot

**Por qué está pendiente:** la diferencia entre E5 y E6 es de +1,34 puntos (4 empresas de
300). Lo hemos llamado ruido, pero eso hay que demostrarlo, no afirmarlo.

**Método:** como las 300 empresas son las mismas en ambos experimentos, la comparación es
pareada y el test correcto es el de McNemar.

**Qué hace falta:** descargar de Colab los dos ficheros de resultados y dejarlos en
`MASTER/datos/03_resultados/`:
- `llm_Qwen2.5-7B-Instruct_zero.csv`
- `llm_Qwen2.5-7B-Instruct_few.csv`

**Segunda comparación pendiente del mismo test (ver D11):** transformer frente a
regresión logística, 50,98 % contra 48,91 %. Requiere `pred_principal.csv` del
entrenamiento del transformer.

**Prompt para retomarlo:**

```
Retomamos la medición M2 de la bitácora del TFM (MASTER/08_BITACORA.md).

He dejado en MASTER/datos/03_resultados/ los ficheros de predicciones. Necesito dos
tests de McNemar, ambos sobre comparaciones pareadas:

1. LLM zero-shot frente a few-shot (33,33% vs 34,67%, mismas 300 empresas).
   Ficheros: llm_Qwen2.5-7B-Instruct_zero.csv y llm_Qwen2.5-7B-Instruct_few.csv

2. Transformer frente a regresión logística (50,98% vs 48,91%, mismas 2.652 empresas).
   Fichero: pred_principal.csv

Para cada uno, el valor de p y la frase exacta para la memoria.
```

---

### M3 · Ruido de etiqueta del CRM (el techo alcanzable)

**Por qué está pendiente:** no sabemos si el techo de A2 está en el 60 % o en el 85 %. Si
dos personas de Empresa no coinciden en el 30 % de los casos, ningún modelo puede pasar del
70 %, y estaríamos persiguiendo un objetivo imposible.

**Qué hace falta:** completar la columna `es_correcto` de
`PRUEBA 1/OUTPUT/validacion_clasificaciones.xlsx`. **Comprobado el 04-10-2026: el fichero
tiene 805 filas y 730 empresas distintas, y las tres columnas de validación
—`sector_validado`, `subsector_validado`, `es_correcto`— están vacías por completo.** Se
regeneró el 02-10-2026 y antes tenía 263 filas. No hace falta validarlas todas: con 150
tomadas al azar el intervalo de la concordancia baja de ±6 puntos, y son unas 2 horas.

> ⚠️ **Antes de usar ese fichero para nada más:** la columna `confianza_ia` **mezcla dos
> escalas**. De sus 805 valores, 612 están entre 0 y 1 y 193 pasan de 1, con un máximo de
> 26,07. Promediarla da 3,886, que no significa nada. Si se quiere usar la confianza del
> modelo cerrado hay que averiguar primero qué escala usó cada ejecución.
**Truco:** que un compañero etiquete 50 de esas filas por su cuenta sin ver tus
respuestas. La coincidencia entre ambos mide la dificultad real de la tarea y es un
resultado citable.

**Prompt para retomarlo:**

```
Retomamos la medición M3 de la bitácora del TFM (MASTER/08_BITACORA.md).

He completado la columna es_correcto de validacion_clasificaciones.xlsx (263 filas).
[Si aplica: y un compañero ha etiquetado 50 filas por separado.]

Necesito medir el ruido de etiqueta del CRM: qué porcentaje de las clasificaciones
históricas son incorrectas según revisión humana, y por tanto cuál es el techo real
que puede alcanzar el modelo de A2. Si hay doble etiquetado, calcula también la
concordancia entre anotadores (Cohen's kappa).
```

---

### M4 · Comparar árboles frente a redes neuronales en datos tabulares (RQ2b)  ✅ *(RESUELTA el 29-09-2026 · ver E21)*

> **Resuelta.** `scripts/F3_A3_E21_arboles_vs_redes.py` compara seis familias sobre
> las mismas variables. El bosque aleatorio supera a la mejor red en 7,52 puntos
> de F1-macro con un coste 8,5 veces menor. Ver E21.

**Por qué está pendiente:** depende del export de oportunidades del CRM.

**Por qué importa:** blinda la defensa frente a la pregunta *"¿por qué no ha usado deep
learning?"*. Ver `06_MODELOS_POR_AGENTE.md`.

**Prompt para retomarlo:**

```
Retomamos la medición M4 (RQ2b) de la bitácora del TFM.

Necesito comparar, sobre las mismas variables tabulares del agente A3, cuatro modelos:
LightGBM, Random Forest, regresión logística y una red neuronal densa de 2-3 capas.
Reportar rendimiento, tiempo de entrenamiento e interpretabilidad, y redactar el
párrafo para la memoria con las citas de Grinsztajn et al. (2022) y Shwartz-Ziv y
Armon (2022).
```

---

## Cómo mantener esta bitácora

- **Añadir, no reescribir.** Si algo resulta estar mal, se anota la corrección debajo.
- **Cada experimento con su fecha, sus datos y sus números exactos.** Un resultado sin
  el tamaño de muestra no es un resultado.
- **Cada decisión con su alternativa descartada.** El tribunal pregunta "¿por qué no
  hizo X?", y la respuesta tiene que estar escrita.
- **Los resultados negativos se quedan.** Son la diferencia entre un experimento y una
  demostración.
