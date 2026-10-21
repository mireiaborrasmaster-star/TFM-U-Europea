# -*- coding: utf-8 -*-
"""
PREP_completar_A6_A7_A9.py · lo que faltaba de los agentes nuevos
==================================================================

QUE HACE
    Tres cosas que los apartados nuevos no traian y el resto del trabajo si:

    1. LA INSTRUCCION DE CONSTRUCCION de A0, A6, A7 y A9. El apartado 4.6.0
       declara que «cada apartado de resultados incluye la instruccion con
       la que se dirigio la construccion del agente». A2, A3, A5 y A8 la
       tienen; estos cuatro no. Sin ellas el 4.6.0 promete algo que no
       cumple.

    2. LAS HIPOTESIS H30 a H33, porque la norma del cuaderno es que cada
       experimento contrasta una hipotesis declarada de antemano. E32, E33
       y E34 contrastaban hipotesis que no estaban escritas.

    3. LA REDACCION SUGERIDA de E32, E33 y E34, que es el parrafo listo para
       pegar en la memoria. Los experimentos anteriores la llevan.

    Es idempotente y se coteja al final.

COMO SE EJECUTA
    python scripts/PREP_completar_A6_A7_A9.py
    python scripts/PREP_completar_A6_A7_A9.py --aplicar
"""

import sys
from pathlib import Path

VERSION_SCRIPT = "v1 · 04-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
BITA = RAIZ / "08_BITACORA.md"
P46 = RAIZ / "memoria" / "CAP4_6_resultados.md"

# ===========================================================================
# 1 · LAS INSTRUCCIONES DE CONSTRUCCION
# ===========================================================================
PROMPT_A0 = """> **Instrucción de construcción · orquestador A0**
>
> ```
> Encadena los agentes ya construidos en un recorrido unico. Entra una
> empresa y sale una fila con TODO lo decidido sobre ella y el MOTIVO de
> cada decision.
>
> Orden: A2 clasifica el sector -> A3 puntua la cuenta recibiendo el sector
> QUE PREDIJO A2, no el real -> A5 empareja un servicio -> A3 fase 2 ajusta
> la prioridad -> cola de redaccion.
>
> No reentrenes nada. Si las interfaces no encajan, dilo en vez de adaptar
> los modelos: que no encajen seria un resultado.
>
> Mide dos cosas que la evaluacion por separado NO puede dar:
>   1. Propagacion del error. Puntua cada empresa DOS VECES, con el sector
>      predicho y con el real, y cuenta en cuantas cambia la nota. Separa
>      los casos en que A2 acerto de aquellos en que fallo.
>   2. Desajuste de poblacion. Compara, variable a variable, cuantos nulos
>      habia al entrenar A3 y cuantos hay en las empresas que entran. Si
>      alguna variable se mueve mucho, busca que aprendio el modelo de esa
>      ausencia.
>
> Reevalua A3 sobre la poblacion de entrada y da su suelo ahi, no el de su
> particion. Si el margen cae, esa es la cifra que vale.
>
> La redaccion generativa NO se ejecuta: deja la cola escrita. Y que cada
> empresa detenida lleve su motivo.
> ```
>
> La instruccion de puntuar dos veces es lo que convierte el orquestador en un
> experimento y no en una tuberia: sin esa comparacion el componente funcionaria igual y
> no se habria aprendido nada de el.

"""

PROMPT_A6 = """> **Instrucción de construcción · agente A6**
>
> ```
> Construye el agente de recepcion sobre los correos reales del buzon, ya
> seudonimizados. Son cuatro piezas y hay que medirlas POR SEPARADO, porque
> dos son reglas y dos son modelos y no se evaluan igual.
>
> Pieza 1, identidad: por reglas sobre el dominio. Ya esta medida, no la
> repitas.
> Pieza 2, norma citada: diccionario norma -> area. Mide cobertura con
> intervalo de Wilson. Separa los correos que apuntan a UNA area de los que
> apuntan a varias: en esos el diccionario no decide.
> Pieza 3, enrutado: usa el clasificador de A8 tal cual, sin reentrenarlo
> con estos correos.
> Pieza 4, comercial o no.
>
> LO IMPORTANTE DE LA PIEZA 3. El 4.6.4 declara que no se sabe cuanto se
> degrada el 80,51 % de A8 al pasar del texto del comercial al del cliente,
> porque solo ocho correos traian area. Usa como etiqueta de prueba el area
> que se deduce de la norma citada: esa correspondencia es de definicion, no
> estadistica. Con eso hay etiquetas suficientes. Da la cifra con intervalo
> y declara que solo cubre los casos que citan una norma, que son los
> faciles.
>
> EN LA PIEZA 4 NO USES EL ACIERTO. Si la mayoria son comerciales, decir
> «todos comerciales» acierta mucho sin leer nada. Mide si ENCUENTRA los
> negativos: AUC con validacion cruzada e intervalo, y cuantos recupera en
> los N primeros.
>
> Y la etiqueta de esa pieza NO la pongas tu con una lista de palabras. Si
> no hay etiquetado humano, NO PUBLIQUES CIFRA y dilo.
>
> Encadena las cuatro y reparte los correos: cuantos resuelve solo y cuantos
> pasan a una persona, cada uno con el motivo.
> ```
>
> La penultima instruccion se incorporo **despues** del error X25: la primera version si
> uso una lista de terminos, y de los quince correos que marcaba solo dos lo eran.

"""

PROMPT_A7 = """> **Instrucción de construcción · agente A7**
>
> ```
> Construye el cualificador de solicitudes. El diseno pedia siete criterios
> de la conversacion comercial, pero esa conversacion no se graba. Usa el
> sustituto escrito.
>
> PRIMERO mide la materia prima, antes de modelar nada: ¿cuantos de los
> siete criterios aparecen de verdad en el texto? Si alguno no aparece
> nunca, ningun modelo podra extraerlo y hay que decirlo.
>
> Entrena con las solicitudes historicas del sistema de gestion, que traen
> su RESULTADO COMERCIAL real. Particion temporal: lo viejo entrena, lo
> nuevo prueba. Nada de particion aleatoria.
>
> Compara contra TRES referencias, no contra ninguna:
>   1. el suelo, la clase mayoritaria
>   2. contar los siete criterios
>   3. contar solo los que de verdad aparecen
>
> Lo que se contrasta es si cualifica mejor CONTAR CRITERIOS o APRENDER DEL
> TEXTO. Es la pregunta que el marco de los siete criterios da por resuelta.
>
> CUIDADO CON LA FUGA: el texto lo escribe el comercial, a veces despues de
> saber como acabo. Busca terminos de desenlace, mira cuantos de los
> terminos mas influyentes lo son, y reentrena sin ellos. Si la cifra no se
> mueve, no habia fuga; si se mueve, la buena es la de sin ellos.
>
> Por ultimo pasalo por los correos de cliente reales y enseña el reparto de
> puntuaciones. Pero si esos correos no traen resultado, NO des una cifra de
> acierto ahi: describe el comportamiento y declara que no se puede medir.
>
> Y si contar criterios no ordena, no lo presentes como que el marco esta
> refutado: mira primero si los criterios siquiera aparecen en ese texto.
> ```
>
> La ultima instruccion es la que separa un resultado negativo de una conclusion
> indebida, y responde a la disciplina que impuso el error X16.

"""

PROMPT_A9 = """> **Instrucción de construcción · agente A9**
>
> ```
> Construye el agente de seguimiento de oportunidades. SIN NINGUNA VARIABLE
> MONETARIA, por la decision D13: si necesitas una medida de tamano usa las
> horas presupuestadas.
>
> Dale la forma del proyecto de prevision de ventas que ya existe: ese mide
> la CALIBRACION con el error de Brier y la DISCRIMINACION con el AUC, de la
> columna de probabilidad que rellena el comercial, con intervalos por
> remuestreo. Conserva las dos metricas y anade lo que alli falta: un modelo
> que compita contra esa persona.
>
> El rival no es una referencia inventada, sale del sistema de gestion. Es
> lo que hace defendible este apartado.
>
> Particion TEMPORAL. Y aparta el ultimo trimestre: las oportunidades
> recientes aun no se han resuelto y su tasa de exito esta inflada por
> censura. Dilo en vez de incluirlo.
>
> El historial de la cuenta —cuantas tuvo antes y cuantas gano— calculalo
> SOLO con las anteriores a la que se predice. Es el error mas facil de
> cometer aqui.
>
> COMPRUEBA LA PROBABILIDAD DEL COMERCIAL ANTES DE USARLA COMO RIVAL. Si hay
> muchos valores exactos de 0 o 100, mira si se escriben despues de saber el
> resultado. Usa la probabilidad de la PRIMERA oferta de cada oportunidad y
> repite la comparacion sin los extremos.
>
> El contraste contra la persona tiene que ser EMPAREJADO: remuestrea los
> mismos casos para los dos, no cada uno por su lado.
>
> Haz una ablacion quitando el propietario de la oportunidad. Si el acierto
> depende de identificar al comercial, el modelo no es transferible y hay
> que declararlo.
>
> Y mira los plazos: cuanto tarda lo que se gana y cuanto lo que se pierde.
> De ahi puede salir una lista de trabajo que no necesite modelo.
> ```
>
> La instruccion de comprobar la probabilidad del comercial **antes** de usarla fue
> decisiva: resulto que 47 casos llevaban 0 o 100 exactos y que de los que marcan 100 se
> gana el 90,7 %, de modo que ese valor no es una prevision sino un registro posterior.

"""

# ===========================================================================
# 2 · LAS HIPOTESIS
# ===========================================================================
HIPOTESIS = (
    "| **H30** | Un modelo estima la probabilidad de cierre de una oportunidad "
    "mejor que la persona que hoy la declara | 🟡 **Parcialmente confirmada**: "
    "ordenando no se distinguen (+0,031 de AUC, p = 0,27); calibrando el modelo "
    "es mejor (+0,0244 de Brier, p = 0,002) | E32 |\n"
    "| **H31** | Contar los criterios de cualificación del marco de siete "
    "predice si la solicitud se convierte | ⬜ **Sin resolver**: no ordena (AUC "
    "0,492) pero en ese texto los criterios apenas aparecen —0,45 de 7—, así que "
    "no es una refutación sino una medición imposible | E34 |\n"
    "| **H32** | El clasificador de área aguanta el paso del texto del comercial "
    "al del cliente | ✅ **Confirmada, con un coste medido**: 75,6 % frente al "
    "80,51 % de su propia población, conservando 63,4 puntos sobre el suelo | E33 |\n"
    "| **H33** | Una etiqueta construida con una lista de términos aproxima el "
    "juicio humano lo bastante para evaluar con ella | ❌ **Refutada**: de los "
    "quince correos que la lista marcaba como no comerciales solo dos lo eran; "
    "precisión del 13,3 % | E33, X25 |\n")

# ===========================================================================
# 3 · LAS REDACCIONES SUGERIDAS
# ===========================================================================
RED_E32 = """
#### Redacción sugerida para la memoria

> La integración de un modelo de estimación en la fase de seguimiento permitió contrastarlo
> contra la referencia que la propia organización produce: el porcentaje de probabilidad que
> el personal comercial consigna en cada oferta. Sobre las 527 oportunidades de prueba en
> que esa estimación constaba, el modelo y la persona resultaron **indistinguibles en
> capacidad de ordenación** —diferencia de AUC de +0,031, con intervalo [−0,027, +0,080]—
> mientras el modelo obtuvo una **calibración significativamente mejor** —diferencia de
> Brier de +0,0244, intervalo [+0,0091, +0,0372], p = 0,002—. La distinción no es
> accesoria: la estimación humana ordena correctamente pero no admite lectura como
> probabilidad, pues en el tramo declarado de 70–89 % se gana en realidad el 95,0 % de las
> oportunidades.

"""

RED_E33 = """
#### Redacción sugerida para la memoria

> El clasificador de enrutado, evaluado sobre su población de entrenamiento, alcanza un
> 80,51 % de acierto. Al aplicarse sobre mensajes redactados por el cliente —un registro
> textual distinto— el rendimiento desciende al 75,6 %, con intervalo [60,7 %, 86,2 %],
> conservando 63,4 puntos sobre el suelo. El descenso de 4,9 puntos contrasta con el
> observado en el modelo de priorización, que al encadenarse perdió la mitad de su margen:
> la diferencia es atribuible a la naturaleza de la etiqueta, registrada con certeza en un
> caso y deducida de variables de disponibilidad variable en el otro.

"""

RED_E34 = """
#### Redacción sugerida para la memoria

> La cualificación de solicitudes mediante un clasificador entrenado sobre el histórico
> alcanza un 66,2 % de acierto frente a un suelo del 56,9 %, con un AUC de 0,714
> [0,677, 0,753]. El recuento de los criterios del marco de cualificación, en cambio, no
> ordena mejor que el azar (AUC 0,492). Este segundo resultado **no refuta el marco**: en el
> texto disponible los criterios aparecen con una media de 0,45 de siete, de modo que su
> recuento carece de capacidad discriminante por ausencia de materia prima y no por
> invalidez del constructo. La comprobación sobre texto en que los criterios sí aparecen
> requeriría mensajes de cliente con resultado comercial asociado, que no existen.

"""


# ===========================================================================
def main():
    aplicar = "--aplicar" in sys.argv
    print()
    print("=" * 74)
    print(f"PREP · completar A6, A7 y A9  ·  {VERSION_SCRIPT}")
    print("=" * 74)
    print(f"   modo: {'APLICAR' if aplicar else 'ensayo'}")
    print()

    notas = []
    t46 = P46.read_text(encoding="utf-8")
    tb = BITA.read_text(encoding="utf-8")

    # --- los prompts ---------------------------------------------------
    print("CAP4_6_resultados.md · instrucciones de construcción")
    for titulo, prompt, etiq in (
            ("## 4.6.5 A0 · El sistema secuencial de la vía de salida\n",
             PROMPT_A0, "A0"),
            ("## 4.6.6 A6 · Recepción y cualificación de entradas\n",
             PROMPT_A6, "A6"),
            ("## 4.6.7 A7 · Cualificación de la solicitud\n", PROMPT_A7, "A7"),
            ("## 4.6.8 A9 · Seguimiento de oportunidades\n", PROMPT_A9, "A9")):
        marca = f"Instrucción de construcción · {'orquestador A0' if etiq == 'A0' else 'agente ' + etiq}"
        if marca in t46:
            notas.append(f"   [ya]  prompt de {etiq}")
        elif titulo not in t46:
            notas.append(f"   [!!]  prompt de {etiq}: no encuentro el título")
        else:
            t46 = t46.replace(titulo, titulo + "\n" + prompt, 1)
            notas.append(f"   [ok]  prompt de {etiq}")
    for n in notas:
        print(n)

    # --- las hipotesis -------------------------------------------------
    notas = []
    print()
    print("08_BITACORA.md · hipótesis y redacciones sugeridas")
    if "| **H30** |" in tb:
        notas.append("   [ya]  H30 a H33")
    else:
        i = tb.find("| **H29** |")
        if i == -1:
            notas.append("   [!!]  no encuentro H29")
        else:
            fin = tb.index("\n", i) + 1
            tb = tb[:fin] + HIPOTESIS + tb[fin:]
            notas.append("   [ok]  H30, H31, H32 y H33")

    # --- las redacciones sugeridas -------------------------------------
    for exp, texto in (("E32", RED_E32), ("E33", RED_E33), ("E34", RED_E34)):
        ini = tb.find(f"### {exp} · ")
        if ini == -1:
            notas.append(f"   [!!]  no encuentro {exp}")
            continue
        sig = tb.find("\n### ", ini + 10)
        tramo = tb[ini:sig if sig != -1 else len(tb)]
        if "Redacción sugerida" in tramo:
            notas.append(f"   [ya]  redacción sugerida de {exp}")
            continue
        # se pone justo antes del separador que cierra la entrada
        corte = tramo.rfind("\n---\n")
        if corte == -1:
            notas.append(f"   [!!]  {exp} no acaba en separador")
            continue
        tb = tb[:ini + corte] + "\n" + texto + tramo[corte:] + \
            (tb[sig:] if sig != -1 else "")
        notas.append(f"   [ok]  redacción sugerida de {exp}")

    for n in notas:
        print(n)

    if not aplicar:
        print()
        print("   Ensayo. Lánzalo con --aplicar para escribir.")
        print()
        return

    P46.write_text(t46, encoding="utf-8")
    BITA.write_text(tb, encoding="utf-8")

    print()
    print("=" * 74)
    print("COTEJO · releyendo los ficheros")
    print("=" * 74)
    v46, vb = P46.read_text(encoding="utf-8"), BITA.read_text(encoding="utf-8")
    fallos = 0
    for texto, clave, etiqueta in (
            (v46, "Instrucción de construcción · orquestador A0", "prompt de A0"),
            (v46, "Instrucción de construcción · agente A6", "prompt de A6"),
            (v46, "Instrucción de construcción · agente A7", "prompt de A7"),
            (v46, "Instrucción de construcción · agente A9", "prompt de A9"),
            (vb, "| **H30** |", "H30"), (vb, "| **H33** |", "H33"),
            (vb, "indistinguibles en\n> capacidad de ordenación",
             "redacción sugerida de E32"),
            (vb, "no refuta el marco", "redacción sugerida de E34")):
        ok = clave in texto
        print(f"   [{'ok' if ok else 'NO'}]  {etiqueta}")
        fallos += 0 if ok else 1

    # cada agente construido debe tener su instruccion: son ocho
    n_prompt = v46.count("> **Instrucción de construcción ·")
    ok = n_prompt == 8
    print(f"   [{'ok' if ok else 'NO'}]  hay {n_prompt} instrucciones "
          f"(A2, A3, A5, A8, A0, A6, A7, A9)")
    fallos += 0 if ok else 1

    # las redacciones sugeridas no pueden duplicarse dentro de una entrada
    for exp in ("E32", "E33", "E34"):
        i = vb.find(f"### {exp} · ")
        s = vb.find("\n### ", i + 10)
        n = vb[i:s if s != -1 else len(vb)].count("Redacción sugerida")
        ok = n == 1
        print(f"   [{'ok' if ok else 'NO'}]  {exp} tiene {n} redacción(es) sugerida(s)")
        fallos += 0 if ok else 1

    print()
    if fallos:
        raise SystemExit(f"   {fallos} comprobación(es) fallan.")
    print("   Todo cotejado.")
    print()


if __name__ == "__main__":
    main()
