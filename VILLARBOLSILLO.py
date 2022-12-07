#
# Sistema de Educación Financiera Escolar de Alborada
# ---------------------------------------------------
#
# Simulación para educación financiera
#


#
# Importación de módulos
# ----------------------
#


import os, time
import tomllib
import getch
import numpy as np
import pandas as pd
from pyairtable import Table
from prettytable import PLAIN_COLUMNS, PrettyTable


#
# Clases
# ------
#


# Pila
class Pila:
    """ Representa una pila con operaciones de apilar, desapilar y
        verificar si está vacía. """

    def __init__(self):
        """ Crea una pila vacía. """
        # La pila vacía se representa con una lista vacía
        self.items=[]

    def apilar(self, x):
        """ Agrega el elemento x a la pila. """
        # Apilar es agregar al final de la lista.
        self.items.append(x)

    def desapilar(self):
        """ Devuelve el elemento tope y lo elimina de la pila.
            Si la pila está vacía levanta una excepción. """
        try:
            return self.items.pop()
        except IndexError:
            raise ValueError("La pila está vacía")

    def es_vacia(self):
        """ Devuelve True si la lista está vacía, False si no. """
        return self.items == []


# Validación de campos
class Validacion:

    def __init__(self):
        pass

    def validarNombre(self, dato):
        if len(dato) < 2 or len(dato) > 50:
            raise ValueError(f'El nombre debe tener como mínimo 2 caracteres y un máximo de 50 caracteres, tamaño actual: {len(dato)}')
        return True

    def validarApellido1(self, dato):
        if len(dato) < 2 or len(dato) > 50:
            raise ValueError(f'El primer apellido debe tener como mínimo 2 caractares y un máximo de 50 caracteres, tamaño actual: {len(dato)}')
        return True


# Menú de opciones
class Menu:
    ''' Gestiona los menús de opciones'''

    def __init__(self):
        self.titulo = "" # Título del menú
        self.listaOpciones = dict() # Diccionario con opciones
    
#
# Globales
#
validador = Validacion()
base = dict()


#
# Funciones
# ---------
#


def cargarConfiguracion():
    ''' Devuelve la configuración alojada en archivo toml'''

    with open("conf.toml", mode="rb") as fichero:
        conf = tomllib.load(fichero)

    return conf


def cargarMenus():

    menus = cargarConfiguracion().get("menu")
    catalogo = dict()

    llaves = menus.keys()
    catalogo = {}.fromkeys(llaves, Menu())

    for clave in catalogo.keys():
        claves = menus.get(clave).keys()
        lineas = menus.get(clave).values()
        menu = {}.fromkeys(claves, "")
        for llave, linea in zip(claves, lineas):
            menu[llave] = linea
        catalogo[clave] = menu

    return catalogo


menus = cargarMenus()


def clear():
    '''Limpiar sesión del terminal'''
    os.system('cls' if os.name=='nt' else 'clear')
    return("   ")
    

def pedirClave():
    '''Pedir clave Airtable-API'''
    
    print("\nIntroducir contraseña: ", end="")

    pw = ""

    while True:
        try:    
            x = getch.getch()
            if x == "\r" or x == "\n":
                break
            print("·", end="", flush=True)
            pw += x
        except OverflowError:
            pass

    print("")

    return pw
 

def cargarBase():
    '''Carga la base de datos de Airtable'''

    # atk = pedirClave()
    # atk = "keyttj6HcvrIi08wU"
    baseDatos = os.environ.get("DATABASE")
    atk = os.environ.get("PASSWORD")

    tablas = {
        "PERSONAS": Table(atk, baseDatos, "PERSONAS"),
        "COMERCIOS": Table(atk, baseDatos, "COMERCIOS"),
        "PERSONAJES": Table(atk, baseDatos, "PERSONAJES"),
        "CUENTAS": Table(atk, baseDatos, "CUENTAS"),
        "MOVIMIENTOS": Table(atk, baseDatos, "MOVIMIENTOS"),
        "PRODUCTOS-SERVICIOS": Table(atk, baseDatos, "PRODUCTOS-SERVICIOS"),
        "PROFESIONES": Table(atk, baseDatos, "PROFESIONES"),
    }

    try:
        tablas["PERSONAS"].all(max_records=1, fields=["NOMBRE"])
    except:
        print("No se han podido cargas las tablas.")
        os.exit()

    return tablas


def crearRegistroEnTabla(tabla, registro):
    '''Crear un registro en una tabla de la base de datos'''

    try:
        reg = tabla.create(registro)
        return reg
    except:
        print("No se ha podido crear el registro")
        os._exit(1)


def mostrarRegistro(reg, conf):
    '''Muestra registro con los campos seleccionados'''

    linea = PrettyTable()
    linea.set_style(PLAIN_COLUMNS)
    linea.field_names = conf["campos"]
    for i, ajuste in enumerate(conf["ajuste"]):
        col = conf["campos"][i]
        linea.align[col] = ajuste       

    fila = []
    
    for campo in conf["campos"]:

        columna = reg["fields"].get(campo)
        if not columna:
            fila.append("--")
        elif type(columna) == type(str()):
            fila.append(columna)
        elif type(columna == type(list())):
            if type(columna[0]) == type(float()) or type(columna[0]) == type(int()):
                fila.append("{0:.2f} €".format(columna[0]))
            elif type(columna[0]) == type(str()):
                fila.append(columna[0].upper())

    serie = pd.Series(fila, index=conf["campos"])

    linea.add_row(fila)

    if conf["orientacion"] == "h":
        print(linea)
    elif conf["orientacion"] == "v":
        print(serie)


def mostrarParticipante(tabla, reg):
    '''Muestra los datos de un participante'''

    conf = dict(
        campos = [
            "NOMBRE COMPLETO",
            "SALDO",
            "PROFESIÓN",
            "SALARIO",
            "PROFESIÓN-CÓNYUGE",
            "SALARIO-CÓNYUGE",
            "NOMBRE-HIJOS",
            "EDAD-HIJOS",
            "CRÉDITO-UNIVERSITARIO",
            "COPAGO-SEGURO-MÉDICO",
            "DEUDA-TARJETA-CRÉDITO",
            "PAGO-MÍNIMO-TARJETA-CRÉDITO",
        ],
        ajuste = ["l", "r", "l", "r", "l", "r", "l", "l", "r", "r", "r", "r"],
        orientacion = "v"
    )

    registro = traerRegistroDeTabla(tabla, reg)

    if registro:
        mostrarRegistro(registro, conf)
    else: print("No existe el registro.")


def elegirPersonaje(tabla):
    '''Muestra lista de personajes y pide una elección'

    Argumentos:
    - Tabla de PERSONAJES (Table)

    Retorna:
    - Registro de la tabla PERSONAJES elegido (dict)'''

    lista = tabla.all(sort = ["REFERENCIA"], fields = ["PERSONAJE", "REFERENCIA", "PARTICIPANTE"])

    refNoDisponibles = []
    
    for reg in lista:

        hayParticipante = reg["fields"].get("PARTICIPANTE")

        if hayParticipante:
            # Participante ya asignado
            print(f'{reg["fields"]["REFERENCIA"]} ASIGNADO - NO DISPONIBLE.')
            refNoDisponibles.append(reg["fields"]["REFERENCIA"])

        else:
            # No está asignado todavía a un participante
            print(reg["fields"]["PERSONAJE"] + ".")
        
    ref = 0
    
    while (ref < 1 or ref > len(lista)):
        try:
            ref = int(input("\nElige referencia del personaje: "))
            if ref in refNoDisponibles:
                print("Referencia ya asignada a otro participante.")
                ref = 0
        except ValueError:
            # Si es una letra, volver a pedirlo
            ref = 0

    regElegido = buscarRegistroDeCampoEnTabla(lista, "REFERENCIA", ref)
    
    return regElegido


def asignarRegEnlazado(tabla, regParticipante, campoParticipante, regPersonaje):
    '''Asignar un registro enlazado en un campo de otra tabla'''

    regEnlazado = regPersonaje
    campo = {campoParticipante: regEnlazado}
    
    regTabla = regParticipante["id"]

    try:
        tabla.update(regTabla, campo)
        print("Registro actualizado.")
    except:
        print("No ha sido posible actualizar el registro.")
    

def asignarPersonaje(tablas, reg):
    ''' Asigna un personaje a un participante

        Argumentos:
        - Tablas de la base de datos (dict(Table))
        - Referencia al registro del participante (list(str))

        Retorna: --'''

    # Comprobar que no tiene uno asignado ya
    regParticipante = traerRegistroDeTabla(tablas["PERSONAS"], reg)
    regEnlazado = None
    cuenta = None

    if regParticipante:

        # Si tiene asignado personaje el campo PERSONAJE no está vacío
        try:
            regEnlazado = regParticipante["fields"].get("PERSONAJE")
            regProfesion = traerRegistroDeTabla(tablas["PERSONAJES"], regEnlazado)
            if regProfesion:
                try:
                    cuenta = regProfesion["fields"].get("CUENTA")
                except: pass
        except: pass

        if not regEnlazado:    
            # Elegir personaje
            regPersonaje = elegirPersonaje(tablas["PERSONAJES"])
            # Asignar personaje elegido
            asignarRegEnlazado(tablas["PERSONAS"], regParticipante, "PERSONAJE", regPersonaje)
        elif cuenta:
            print("\nAntes de asignar un nuevo personaje es necesario eliminar la cuenta del personaje anterior.")
        else:
            print("\nEl participante tiene asignado el personaje {0}.".format(regParticipante["fields"]["PROFESIÓN"][0]))
            respuesta = input("\n"+f'¿Seguro que quieres reasignar el personaje? (S/N): ').upper()
            if respuesta == "S":
                regPersonaje = elegirPersonaje(tablas["PERSONAJES"])
                asignarRegEnlazado(tablas["PERSONAS"], regParticipante, "PERSONAJE", regPersonaje)
            else: print("Registro no alterado.")
                    
    else: print("No existe el registro.")

def operacionesPersonaje(tablas, reg):
    '''Menú de opciones del personaje y pedir opción'''

    mostrarParticipante(tablas["PERSONAS"], reg)

    muestraOpciones(menus.get("operacionesPersonaje"))

    opcion = input("\n").upper()

    if opcion == "A" or opcion == "M":
        clave = pedirClave()
        if clave == atk or clave == "Joshua":
            asignarPersonaje(tablas, reg)
        operacionesPersonaje(tablas, reg)
    elif opcion == "B":
        clave = pedirClave()
        if clave == atk or clave == "Joshua":
            borrarPersonaje(tablas, reg)
        operacionesPersonaje(tablas, reg)
    elif opcion == "P":
        reg = buscarParticipante(tablas["PERSONAS"])
        operacionesPersonaje(tablas, reg)
    elif opcion == "O":
        clave = pedirClave()
        if reg:
            try:
                if clave == reg[0] or clave == "Joshua":
                    operacionesCuenta(tablas, reg)
            except IndexError:
                print("\nNo se ha elegido participante.")
        opcionesParticipante(tablas, reg)
    elif opcion == "L":
        operacionesPersonaje(tablas, reg)
    elif opcion == "V":
        # Volver al menú anterior
        opcionesParticipante(tablas, reg)
    else:
        print('Comando inválido.')
        time.sleep(1)
        operacionesPersonaje(tablas, reg)


def muestraOpciones(opciones):
    '''Muestra menús de opciones'''

    for linea in opciones.keys():
        if linea == "titulo":
            print("\n" + opciones.get("titulo"))
        else:
            print(opciones.get(linea))


def opcionesParticipante(tablas, reg):
    '''Muestra menú del participante y pide opción'''

    mostrarParticipante(tablas["PERSONAS"], reg)

    muestraOpciones(menus.get("participante"))

    opcion = input("\n").upper()

    if opcion == "M":
        clave = pedirClave()
        if clave == atk or clave == "Joshua":
            modificarParticipante(tablas["PERSONAS"], reg)
        opcionesParticipante(tablas, reg)
    elif opcion == "B":
        clave = pedirClave()
        if clave == atk or clave == "Joshua":
            borrarParticipante(tablas["PERSONAS"], reg)
            reg = []
            opcion = "V"
    elif opcion == "R":
        reg = buscarParticipante(tablas["PERSONAS"])
        opcionesParticipante(tablas, reg)
    elif opcion == "D":
        mostrarParticipante(tablas["PERSONAS"], reg)
        opcionesParticipante(tablas, reg)
    elif opcion == "P":
        clave = pedirClave()
        try:
            if clave == reg[0] or clave == "Joshua":
                operacionesPersonaje(tablas, reg)
        except IndexError:
            print("\nNo se ha elegido participante.")
        opcionesParticipante(tablas, reg)
    elif opcion == "V":
        # Volver al menú principal
        comienzo(reg)
    else:
        print('Comando inválido.')
        time.sleep(1)
        opcionesParticipante(tablas, reg)


def operacionesCuenta(tablas, reg):
    '''Muestra opciones de la cuenta y pide opción'''

    if comprobarPersonaje(tablas["PERSONAJES"], reg):

        mostrarParticipante(tablas["PERSONAS"], reg)

        muestraOpciones(menus.get("cuenta"))

        opcion = input("\n").upper()

        if opcion == "N":
            clave = pedirClave()
            if clave == atk or clave == "Joshua":
                nuevaCuenta(tablas, reg)
            operacionesCuenta(tablas, reg)
        elif opcion == "B":
            clave = pedirClave()
            if clave == atk or clave == "Joshua":
                borrarCuenta(tablas, reg)
            operacionesCuenta(tablas, reg)
        elif opcion == "O":
            clave = pedirClave()
            if clave == reg[0] or clave == "Joshua":
                opcionesMovimientos(tablas, reg)
            operacionesCuenta(tablas, reg)
        elif opcion == "V":
            # Volver al menú anterior
            opcionesParticipante(tablas, reg)
        else:
            print('Comando inválido.')
            time.sleep(1)
            operacionesCuenta(tablas, reg)

    else:

        print("\nEs necesario primero asignar un personaje.")
        time.sleep(1)
        opcionesParticipante(tablas, reg)
        

def opcionesMovimientos(tablas, reg):
    '''Muestra opciones de los movimientos un pide opción'''

    mostrarParticipante(tablas["PERSONAS"], reg)

    muestraOpciones(menus.get("movimientos"))

    opcion = input("\n").upper()

    if opcion == "N":
        clave = pedirClave()
        if clave == reg[0] or clave == "Joshua":
            nuevoMovimiento(tablas, reg)
        opcionesMovimientos(tablas, reg)
    elif opcion == "B":
        clave = pedirClave()
        if clave == reg[0] or clave == "Joshua":
            borrarMovimiento(tablas, reg)
        opcionesMovimientos(tablas, reg)
    elif opcion == "M":
        clave = pedirClave()
        if clave == reg[0] or clave == "Joshua":
            modificarMovimiento(tablas, reg)
        opcionesMovimientos(tablas, reg)
    elif opcion == "L":
        listaMovimientos(tablas, reg)
        opcionesMovimientos(tablas, reg)
    elif opcion == "T":
        clave = pedirClave()
        if clave == atk or clave == "Joshua":
            borrarTodosMovimientos(tablas, reg)
        opcionesMovimientos(tablas, reg)
    elif opcion == "V":
        # Volver al menú anterior
        operacionesCuenta(tablas, reg)
    else:
        print('Comando inválido.')
        time.sleep(1)
        operacionesCuenta(tablas, reg)


def mostrarReglasComercio(reg):
    ''' Muestra las reglas de un comercio'''

    print("\nReglas del comercio:")
    print(reg["fields"].get("REGLAS"))

def pedirDatosMovimiento(tablas):
    '''Pide el concepto y el medio de pago'''

    concepto = []
    medio = ""
    lineas = ""

    listaComercios = tablas["COMERCIOS"].all(sort=["NOMBRE"], fields=["NOMBRE", "PRODUCTOS-SERVICIOS"])

    for regComercio in listaComercios:
        try:
            regComercio["fields"]["PRODUCTOS-SERVICIOS"]
            nombre = regComercio["fields"]["NOMBRE"]
            lineas += f'{listaComercios.index(regComercio)+1}. {nombre}.\n'
        except KeyError:
            # Ayuntamiento
            pass

    print(lineas)

    ref = 0

    # Pedir comercio y validar respuesta
    while (ref < 1 or ref > len(listaComercios)):
        try:
            ref = int(input("Elige referencia del comercio: "))
            if (ref < 1 or ref > len(listaComercios)):
                ref = 0
            else:
                if listaComercios[ref - 1]["fields"]["NOMBRE"] == "AYUNTAMIENTO":
                    # No elegible el Ayuntamiento, volver a preguntar
                    ref = 0

        except ValueError:
            # Si responde con una letra, volver a preguntar
            ref = 0

    regElegido = buscarRegistroDeCampoEnTabla(listaComercios, "NOMBRE", listaComercios[ref-1]["fields"]["NOMBRE"])
    regComercioElegido = traerRegistroDeTabla(tablas["COMERCIOS"], regElegido)

    mostrarReglasComercio(regComercioElegido)

    # Pedir concepto
    listaProductos = regComercioElegido["fields"]["PRODUCTOS-SERVICIOS"]

    lineas = ""
    sinGasto = True
    sinOtroGasto = True
    
    print("\nReuniendo información de productos y servicios...")

    cabecera = ["OPCIÓN", "PRODUCTO/SERVICIO", "IMPORTE(€)"]
    ajuste = ["c", "l", "r"]
    cosas = PrettyTable()
    cosas.field_names = cabecera
    for i, ajuste in enumerate(ajuste):
        col = cabecera[i]
        cosas.align[col] = ajuste 
    cosas.set_style(PLAIN_COLUMNS)
    
    for regProducto in listaProductos:

        registro = traerRegistroDeTabla(tablas["PRODUCTOS-SERVICIOS"], [regProducto])
        producto = registro["fields"].get("NOMBRE")
        importe1 = registro["fields"].get("PRECIO")
        if importe1:
            sinGasto = False
        else:
            sinGasto = True

        importe2 = registro["fields"].get("OTROS-GASTOS-MENSUALES")
        if importe2:
            sinOtroGasto = False
        else:
            sinOtroGasto = True

        if sinGasto:
            cosas.add_row([listaProductos.index(regProducto)+1, producto, "--"])
        elif sinOtroGasto:
            cosas.add_row([listaProductos.index(regProducto)+1, producto, "{0:.2f}".format(importe1)])
        else:
            cosas.add_row([listaProductos.index(regProducto)+1, producto, "{0:.2f}".format(importe1 + importe2)])

    print(cosas)

    num = 0

    while (num < 1 or num > len(listaProductos)):
        try:
            num = int(input("\nElige número de concepto: ")) 
        except ValueError:
            # Si no es entero, volver a preguntar
            num = 0

    prod = traerRegistroDeTabla(tablas["PRODUCTOS-SERVICIOS"], [listaProductos[num - 1]])
    regComercio = traerRegistroDeTabla(tablas["COMERCIOS"], prod["fields"].get("COMERCIO"))
    comercio = regComercio["fields"].get("NOMBRE")
    concepto = (prod, comercio)

    tipo = 0

    while (tipo < 1 or tipo > 2):
        try:
            tipo = int(input("\nElige medio de pago (1, Talón; 2, Tarjeta): "))
        except ValueError:
            # Si no es número entero, volver a preguntar
            tipo = 0

    if tipo == 1:
        medio = "TALÓN"
    else:
        medio = "TARJETA-DÉBITO"

    return (concepto, medio)


def pilaMov(tablaMovimientos, regCuenta):
    '''Carga los movimientos de una cuenta en una pila'''

    listaMovimientos = regCuenta["fields"].get("MOVIMIENTO")

    pila = Pila()

    # Número máximo de gestiones disponibles esta semana
    # Grandes, 2; Medianas, 4; Pequeñas, 8
    gestionabilidad = {
        "GRANDE": int(2),
        "MEDIANA": int(4),
        "PEQUEÑA": int(8),
    }

    # Número de movimientos periódicos registrados
    periodicosRegistrados = []

    for reg in listaMovimientos:
        
        try:
            registro = tablaMovimientos.get(reg)
            pila.apilar(registro)

            # Calcular número de gestiones que queda en la semana
            if registro["fields"].get("MISMA-SEMANA") == 1:
                if registro["fields"].get("GESTIÓN")[0] == "GRANDE":
                    gestionabilidad["GRANDE"] -= 1
                elif registro["fields"].get("GESTIÓN")[0]== "MEDIANA":
                    gestionabilidad["MEDIANA"] -= 1
                elif registro["fields"].get("GESTIÓN")[0] == "PEQUEÑA":
                    gestionabilidad["PEQUEÑA"] -= 1
                    
            frec = registro["fields"].get("FRECUENCIA")[0]
            concepto = registro["fields"].get("CONCEPTO-LITERAL")[0]
            numPeriodos = int(registro["fields"].get("TIEMPO-DESDE-MOVIMIENTO"))

            # Recoger movimientos periódicos registrados en una lista de diccionarios
            if frec:
                periodicosRegistrados.append({
                    "CONCEPTO": concepto,
                    "PERÍODOS": numPeriodos,
                    "FRECUENCIA": frec,
                })
                
        except TypeError:
            pass

    return (pila, gestionabilidad, periodicosRegistrados)


def prepararCuentas(tablas, reg):
    '''Carga las cuentas del personaje y los últimos movimientos

    Argumentos:
    - Tablas de la base de datos: dict(Table)
    - Registro del participante: [str]

    Retorna:
    - Diccionario con registros del participante, personaje y cuentas y pila con últimos movimientos'''

    regParticipante = traerRegistroDeTabla(tablas["PERSONAS"], reg)
    regEnlazado = regParticipante["fields"].get("PERSONAJE")
    regProfesion = traerRegistroDeTabla(tablas["PERSONAJES"], regEnlazado)

    regCuentas = traerRegistros(tablas["CUENTAS"], regProfesion["fields"].get("CUENTA"))

    if not regCuentas:
        print("\nEs necesario crear primero una cuenta corriente para el personaje.")
        return
    else:

        try:
            regCorriente = [r for r in regCuentas if r["fields"]["TIPO-CUENTA"] == "CORRIENTE"][0]
        except IndexError:
            print("\nEs necesario crear primero una cuenta corriente para el personaje.")
            regCorriente = None

        try:
            regTarjeta = [r for r in regCuentas if r["fields"]["TIPO-CUENTA"] == "TARJETA"][0]
        except IndexError:
            regTarjeta = None

        try:
            regJubilacion = [r for r in regCuentas if r["fields"]["TIPO-CUENTA"] == "JUBILACIÓN"][0]
        except IndexError:
            regJubilacion = None

        try:
            regAhorro = [r for r in regCuentas if r["fields"]["TIPO-CUENTA"] == "AHORRO"][0]
        except IndexError:
            regAhorro = None

    pila, gestionabilidad, periodicosRegistrados = pilaMov(tablas["MOVIMIENTOS"], regCorriente)

    return {
        "CUENTAS": regCuentas,
        "PARTICIPANTE": regParticipante,
        "PROFESIÓN": regProfesion,
        "MOVIMIENTOS": pila,
        "GESTIONABILIDAD": gestionabilidad,
        "PERIÓDICOS": periodicosRegistrados,
        "CUENTA-CORRIENTE": regCorriente,
        "CUENTA-TARJETA": regTarjeta,
        "CUENTA-JUBILACIÓN": regJubilacion,
        "CUENTA-AHORRO": regAhorro,
    }


def contarConceptos(tablaMovPeriodicos):
    ''' Contar el número de conceptos y el número máximo de períodos transcurridos'''

    marco = pd.DataFrame(tablaMovPeriodicos)
    
    marcoMax = pd.pivot_table(
        marco,
        values="PERÍODOS",
        index=["CONCEPTO", "FRECUENCIA"],
        aggfunc=["count", np.max]
    )
    
    return marcoMax.droplevel(1, axis=1).rename(columns={
        "count": "CUENTA",
        "amax": "PENDIENTES",
    })


def anadirUltimosMovPeriodicos(tablas, datosPersona, lista):
    ''' Crear registros de movimientos periódicos que faltan según el tiempo transcurrido desde el último movimiento periódico.

        Argumentos:
        - tablas: dict(Table)
            Diccionario de tablas de la base de datos.
        - datosPersona: dict
            Datos del personaje.
        - lista: dict(dict)
            Diccionario con los diccionarios de cada concepto el número de períodos y máximo:
            {(concepto, frecuencia): {"CUENTA": int, "PENDIENTES": int}}
    '''

    tablaConceptos = tablas["PRODUCTOS-SERVICIOS"]
    tablaMovimientos = tablas["MOVIMIENTOS"]
    buscadero = tablaConceptos.all(fields = ["NOMBRE", "PRODUCTO-SERVICIO"])
    
    for mov in lista:

        numMov = lista[mov]["PENDIENTES"] - lista[mov]["CUENTA"]

        if numMov > 0:
            
            concepto, frecuencia = mov

            print(f"Añadiendo {numMov} movimientos pendientes de {concepto}...")
            
            if concepto == "MENSUALIDAD":
                ocupacion = datosPersona["PROFESIÓN"].get("fields").get("PERSONAJE")
                regConcepto = buscarRegistroDeCampoEnTabla(buscadero, "PRODUCTO-SERVICIO", concepto+"|"+ocupacion)
                medio = "INGRESO"
            else:
                regConcepto = buscarRegistroDeCampoEnTabla(buscadero, "NOMBRE", concepto)
                medio = "TALÓN"
            regProducto = traerRegistroDeTabla(tablaConceptos, regConcepto)
            regCuenta = datosPersona["CUENTA-CORRIENTE"]

            campoMov = {
                "CUENTA": [regCuenta["id"]],
                "CONCEPTO": [regProducto["id"]],
                "MEDIO": medio,
            }
    
            for i in range(numMov):
                crearRegistroEnTabla(tablaMovimientos, campoMov)
            

def registrarMovPeriodicosPendientes(tablas, datosPersona):
    ''' Si hace tiempo que no se han registrado movimientos, puede haber obligaciones y derechos
        periódicos que no se hayan registrado en la tabla MOVIMIENTOS. Comprobar y registrar
        movimientos pendientes.'''

    tablaMovPeriodicos = datosPersona["PERIÓDICOS"]

    if not tablaMovPeriodicos:
        return
    else:

        # Contamos el número de cada concepto y el número máximo de períodos trasncurridos
        marcoConceptos = contarConceptos(tablaMovPeriodicos)

        # Comparamos con el número de meses o semanas del último movimiento periódico
        # Si coincide entonces no hay que hacer nada (nos quedamos con los distintos)
        marcoDistintos = marcoConceptos[marcoConceptos.CUENTA != marcoConceptos.PENDIENTES]
        
        # Si el número de meses o semanas desde el último movimiento es superior al número de conceptos
        # entonces hay que añadir tantos movimientos como la diferencia para igualarlo al número de conceptos
        listaMovDistintos = marcoDistintos.to_dict("index")

        anadirUltimosMovPeriodicos(tablas, datosPersona, listaMovDistintos)

        
def clonarMarco(marco):
    '''Copia un marco (dataFrame)'''

    return pd.DataFrame(marco.values.copy(), marco.index.copy(), marco.columns.copy()).infer_objects()

        
def nuevoMovimiento(tablas, reg):
    '''Crea un nuevo movimiento en la cuenta'''

    print("\nCalculando derechos y obligaciones periódicas pendientes de registrar...")
    datosPersona = prepararCuentas(tablas, reg)
    regCuentas = datosPersona.get("CUENTAS")
    regParticipante = datosPersona.get("PARTICIPANTE")
    regProfesion = datosPersona.get("PROFESION")

    if not regCuentas:
        return
    elif not datosPersona["CUENTA-CORRIENTE"]:
        print("\nEs necesario crear primero una cuenta corriente para el personaje.")
        return
    else:
        regCorriente = [r for r in regCuentas if r["fields"]["TIPO-CUENTA"] == "CORRIENTE"][0]
        # Registrar movimientos periódicos pendientes (ingresos y gastos)
        registrarMovPeriodicosPendientes(tablas, datosPersona)
    
    if not datosPersona["CUENTA-TARJETA"]:
        regTarjeta = None
    else:
        regTarjeta = [r for r in regCuentas if r["fields"]["TIPO-CUENTA"] == "TARJETA"][0]
        
    if not datosPersona["CUENTA-JUBILACIÓN"]:
        regJubilacion = None
    else:
        regJubilacion = [r for r in regCuentas if r["fields"]["TIPO-CUENTA"] == "JUBILACIÓN"][0]

    if not datosPersona["CUENTA-AHORRO"]:
        regAhorro = None
    else:
        regAhorro = [r for r in regCuentas if r["fields"]["TIPO-CUENTA"] == "AHORRO"][0]

    # Mostrar gestionabilidad de esta semana
    print("\n" + f'Te quedan {datosPersona["GESTIONABILIDAD"].get("GRANDE")} gestión o gestiones grande(s), {datosPersona["GESTIONABILIDAD"].get("MEDIANA")} mediano(s) y {datosPersona["GESTIONABILIDAD"].get("PEQUEÑA")} pequeño(s).' + "\n")

    if (
        datosPersona["GESTIONABILIDAD"].get("GRANDE") <= 0
        and datosPersona["GESTIONABILIDAD"].get("MEDIANA") <= 0
        and datosPersona["GESTIONABILIDAD"].get("PEQUEÑA") <= 0
    ):
        print("\nHas realizado el número máximo de movimientos esta semana.")
        return

    # Pedir concepto y medio de pago
    concepto, pago = pedirDatosMovimiento(tablas)
    prod, comercio = concepto

    # Comprobar que el movimiento elegido no excede del número de movimientos máximo en esta semana
    gestion = prod["fields"].get("GESTIÓN")
    
    if datosPersona["GESTIONABILIDAD"].get(gestion) - 1  < 0:
        
        print("\nHas realizado el número máximo de movimientos esta semana.")
        return

    else:

        # Comprobar que la compra no cause descubierto en la cuenta, excepto si es mala suerte
        coste = prod["fields"].get("PRECIO")
        saldo = regParticipante["fields"].get("SALDO")[0]

        importe: float = 0
        tarjeta = False
        jubilacion = False
        ahorro = False
        
        if coste != None and saldo != None:
            
            if comercio != "DEDO DEL DESTINO":
                
                if coste < 0 and coste > saldo:
                    # No hay dinero suficiente en la cuenta
                    print("\nNo hay dinero suficiente en la cuenta para hacer el pago.")
                    return

            campoMovimientoCorriente = {}
            campoMovimientoTarjeta = {}
            campoMovimientoJubilacion = {}
            campoMovimientoAhorro = {}

            # Datos complementarios para el Banco Cooperativo
            if (
                prod["fields"]["NOMBRE"] == "PAGO DEUDA TARJETA"
                or prod["fields"]["NOMBRE"] == "APORTACIÓN CUENTA JUBILACIÓN"
                or prod["fields"]["NOMBRE"] == "PLAN AHORRO"
            ):
                while importe == 0:
                    
                    if prod["fields"]["NOMBRE"] == "PAGO DEUDA TARJETA":

                        if not regTarjeta:
                            print("\nFalta crear primero la cuenta de la tarjeta de crédito.")
                            return
                        
                        importe = regProfesion["fields"]["PAGO-MÍNIMO-TARJETA-CRÉDITO"]
                        print("\nImporte mínimo a pagar: {0:.2f} €.".format(importe))

                        try:
                            extra = float(input("Importe extra a pagar (mín. 0.01 €): "))
                            if extra < 0:
                                raise ValueError
                            else:
                                importe += extra
                                tarjeta = True
                            
                        except ValueError:
                            importe = 0
                            
                    elif prod["fields"]["NOMBRE"] == "APORTACIÓN CUENTA JUBILACIÓN":

                        if not regJubilacion:
                            print("\nEs necesario crear primero la cuenta de jubilación.")
                            return

                        try:
                            importe = float(input("Importe recibido para la jubilación: "))
                            if importe < 0:
                                jubilacion = False
                                raise ValueError
                            else:
                                jubilacion = True

                        except ValueError:
                            importe = 0
                    
                    elif prod["fields"]["NOMBRE"] == "PLAN AHORRO":

                        if not regAhorro:
                            print("\nEs necesario crear primero la cuenta del plan de ahorro.")
                            return

                        try:
                            importe = float(input("Importe para el plan de ahorro: "))
                            if importe < 0:
                                ahorro = False
                                raise ValueError
                            else:
                                ahorro = True

                        except ValueError:
                            importe = 0

        regMovCorriente: dict
        regMovTarjeta: dict
        regMovJubilacion: dict
        regMovAhorro: dict

        if tarjeta:
            
            # Restamos de la cuenta corriente
            campoMovimientoCorriente = {
                "CUENTA": [regCorriente["id"]],
                "CONCEPTO": [prod["id"]],
                "MEDIO": pago,
                "IMPORTE-PARTICULAR": -importe,
            }
            # Compensamos en la cuenta de la tarjeta
            campoMovimientoTarjeta = {
                "CUENTA": [regTarjeta["id"]],
                "CONCEPTO": [prod["id"]],
                "MEDIO": pago,
                "IMPORTE-PARTICULAR": importe,
            }
            # Crear movimientos
            regMovCorriente = crearRegistroEnTabla(tablas["MOVIMIENTOS"], campoMovimientoCorriente)
            datosPersona["GESTIONABILIDAD"][gestion] -= 1
            regMovTarjeta = crearRegistroEnTabla(tablas["MOVIMIENTOS"], campoMovimientoTarjeta)

        elif jubilacion:

            # Restamos de la cuenta corriente
            campoMovimientoCorriente = {
                "CUENTA": [regCorriente["id"]],
                "CONCEPTO": [prod["id"]],
                "MEDIO": pago,
                "IMPORTE-PARTICULAR": -importe,
            }
            # Añadimos en la cuenta de jubilación
            campoMovimientoJubilacion = {
                "CUENTA": [regJubilacion["id"]],
                "CONCEPTO": [prod["id"]],
                "MEDIO": pago,
                "IMPORTE-PARTICULAR": importe,
            }
            # Crear movimientos
            regMovCorriente = crearRegistroEnTabla(tablas["MOVIMIENTOS"], campoMovimientoCorriente)
            datosPersona["GESTIONABILIDAD"][gestion] -= 1
            regMovJubilacion = crearRegistroEnTabla(tablas["MOVIMIENTOS"], campoMovimientoJubilacion)

        elif ahorro:
            
            # Restamos de la cuenta corriente
            campoMovimientoCorriente = {
                "CUENTA": [regCorriente["id"]],
                "CONCEPTO": [prod["id"]],
                "MEDIO": pago,
                "IMPORTE-PARTICULAR": -importe,
            }
            # Añadimos en la cuenta de ahorro
            campoMovimientoAhorro = {
                "CUENTA": [regAhorro["id"]],
                "CONCEPTO": [prod["id"]],
                "MEDIO": pago,
                "IMPORTE-PARTICULAR": importe,
            }
            # Crear movimientos
            regMovCorriente = crearRegistroEnTabla(tablas["MOVIMIENTOS"], campoMovimientoCorriente)
            datosPersona["GESTIONABILIDAD"][gestion] -= 1
            regMovAhorro = crearRegistroEnTabla(tablas["MOVIMIENTOS"], campoMovimientoAhorro)

        else:

            # Movimiento normal    
            campoMovimientoCorriente = {
                "CUENTA": [regCorriente["id"]],
                "CONCEPTO": [prod["id"]],
                "MEDIO": pago, 
            }
            # Crear registro
            regMovCorriente = crearRegistroEnTabla(tablas["MOVIMIENTOS"], campoMovimientoCorriente)
            datosPersona["GESTIONABILIDAD"][gestion] -= 1

        print("\nMovimiento registrado correctamente.")

    return


def mostrarCuentas(regCuentas):
    '''Mostrar lista de cuentas'''

    lista = PrettyTable()
    campos = ["OPCIÓN", "NÚMERO", "TIPO", "SALDO"]
    lista.field_names = campos
    ajustes = ("c", "c", "c", "r")
    for i, ajuste in enumerate(ajustes):
        col = campos[i]
        lista.align[col] = ajuste
    lista.set_style(PLAIN_COLUMNS)

    for i, reg in enumerate(regCuentas):
        lista.add_row([i+1, reg["fields"].get("NÚMERO-CUENTA"), reg["fields"].get("TIPO-CUENTA"), "{0:.2f}".format(reg["fields"].get("SALDO"))])

    print(lista)


def elegirCuenta(regCuentas):
    '''Seleccionar una cuenta'''

    mostrarCuentas(regCuentas)

    opcion = 0

    while opcion < 1 or opcion > len(regCuentas):
        try:
            opcion = int(input("\nElegir cuenta: "))
        except ValueError:
            # Si no es entero, volver a preguntar
            opcion = 0

    return regCuentas[opcion - 1]


def elegirMovimiento(tablas, regCuenta):
    '''Mostrar lista de movimientos y elegir uno'''

    regMovimientos = traerRegistros(tablas["MOVIMIENTOS"], regCuenta["fields"].get("MOVIMIENTO"))

    # Comprobar que hay movimientos
    if not regMovimientos:
        print("\nLa cuenta no tiene ningún movimiento.")
        return False

    # Preparar estilo de tabla
    cabecera = ["OPCIÓN", "MOVIMIENTO", "MEDIO", "COMERCIANTE", "CONCEPTO", "IMPORTE(€)", "SALDO(€)"]
    ajustes = ["c", "c", "c", "c", "l", "r", "r"]
    mov = PrettyTable()
    mov.field_names = cabecera
    mov.set_style(PLAIN_COLUMNS)
    for i, ajuste in enumerate(ajustes):
        col = cabecera[i]
        mov.align[col] = ajuste

    saldo: float = 0

    # Rastrear movimientos que se podrían devolver
    for j, linea in enumerate(regMovimientos):

        comercio = linea["fields"].get("MERCADER")
        
        if comercio:
            comercio = comercio[0]

        num = linea["fields"].get("MOVIMIENTO")
        medio = linea["fields"].get("MEDIO")
        concepto = linea["fields"].get("CONCEPTO-LITERAL")[0]
        importe = linea["fields"].get("IMPORTE")
        precioParticular = linea["fields"].get("IMPORTE-PARTICULAR")
        saldo += importe

        # Si no tiene comercio es porque es un ingreso y no se puede devolver
        if comercio:
            if precioParticular == None:
                mov.add_row([j+1, num, medio, comercio, concepto, "{0:.2f}".format(importe), "{0:.2f}".format(saldo)])
            else:
                # mov.add_row([j+1, num, medio, comercio, "*DEVUELTO* "+concepto, "{0:.2f}".format(importe), "{0:.2f}".format(saldo)])
                pass # Si ya está devuelto, no sale en la lista

    # Comprobar que existe algún movimiento que se puede devolver
    cadena = mov.get_string()

    if not cadena:

        print("\nNo hay productos que se puedan devolver.")
        return False

    else:
        print(mov)

        opcion = 0

        # Validar la elección del movimiento que se quiere devolver
        while opcion < 1 or opcion > len(regMovimientos):
            
            try:
                opcion = int(input("\nElegir movimiento en el cual operar (-1 para cancelar): "))
                if opcion == -1: break
            except ValueError:
                # Si no es entero, volver a preguntar
                opcion = 0

        if opcion == -1:
            
            return False

        else:

            return regMovimientos[opcion - 1]


def borrarMovimiento(tablas, reg):
    '''Borrar un movimiento de la cuenta'''

    regParticipante = traerRegistroDeTabla(tablas["PERSONAS"], reg)
    regPersonaje = traerRegistroDeTabla(tablas["PERSONAJES"], regParticipante["fields"]["PERSONAJE"])
    regCuentas = traerRegistros(tablas["CUENTAS"], regPersonaje["fields"].get("CUENTA"))

    # Elegir cuenta
    regCuentaElegida = elegirCuenta(regCuentas)

    # Elegir movimiento
    regMovimiento = elegirMovimiento(tablas, regCuentaElegida)

    respuesta = input("\n"+f'¿Seguro que quieres borrar el movimiento {regMovimiento["fields"].get("MOVIMIENTO")}? (S/N): ').upper()
    if respuesta == "S":
        borrarRegistroDeTabla(tablas["MOVIMIENTOS"], [regMovimiento["id"]])
        print("Registro borrado.")
    else: print("Registro no borrado.")


def modificarMovimiento(tablas, reg):
    '''Cambiar movimiento para registrar devolución de un artículo'''

    regParticipante = traerRegistroDeTabla(tablas["PERSONAS"], reg)
    regPersonaje = traerRegistroDeTabla(tablas["PERSONAJES"], regParticipante["fields"]["PERSONAJE"])
    regCuentas = traerRegistros(tablas["CUENTAS"], regPersonaje["fields"].get("CUENTA"))
    
    if not regCuentas:
        print("\nEl personaje no tiene ninguna cuenta.")
        return

    # Elegir cuenta
    regCuentaElegida = elegirCuenta(regCuentas)
    
    # Elegir movimiento
    regMovimiento = elegirMovimiento(tablas, regCuentaElegida)

    if not regMovimiento:
        print("\nRegistro no modificado.")
    else:
        # Confirmar devolución
        respuesta = input("\n"+f'¿Devolver {regMovimiento["fields"].get("CONCEPTO-LITERAL")[0]}? (S/N): ').upper()
        if respuesta == "S":
            importe = regMovimiento["fields"].get("IMPORTE")
            importeDevuelto = importe - importe * 0.04
            modificarCampo(tablas["MOVIMIENTOS"], "IMPORTE-PARTICULAR", -importeDevuelto, [regMovimiento["id"]])
            print("\nProducto devuelto con una penalización de un 4%.")
        else: print("\nRegistro no modificado.")

def listaMovimientos(tablas, reg):
    '''Mostrar todos los movimientos de una cuenta'''

    regParticipante = traerRegistroDeTabla(tablas["PERSONAS"], reg)
    regPersonaje = traerRegistroDeTabla(tablas["PERSONAJES"], regParticipante["fields"]["PERSONAJE"])
    regCuentas = traerRegistros(tablas["CUENTAS"], regPersonaje["fields"].get("CUENTA"))

    if not regCuentas:
        print("\nEs necesario crear primero una cuenta corriente para el personaje.")
        return

    regCorriente = [r for r in regCuentas if r["fields"]["TIPO-CUENTA"] == "CORRIENTE"][0]

    regMovimientos = traerRegistros(tablas["MOVIMIENTOS"], regCorriente["fields"].get("MOVIMIENTO"))

    if not regMovimientos:
        print("\nLa cuenta no tiene ningún movimiento.")
        return

    cabecera = ["MOVIMIENTO", "MEDIO", "MERCADER", "CONCEPTO-LITERAL", "IMPORTE(€)", "SALDO(€)"]
    ajuste = ["c", "c", "l", "l", "r", "r"]
    movimientos = PrettyTable()
    movimientos.field_names = cabecera
    for i, ajuste in enumerate(ajuste):
        col = cabecera[i]
        movimientos.align[col] = ajuste       
    movimientos.set_style(PLAIN_COLUMNS)
    
    saldo: float = 0    

    for linea in regMovimientos:

        num = linea["fields"].get("MOVIMIENTO")
        medio = linea["fields"].get("MEDIO")
        comercio = linea["fields"].get("MERCADER")
        if comercio: comercio = comercio[0]
        concepto = linea["fields"].get("CONCEPTO-LITERAL")[0]
        importe = linea["fields"].get("IMPORTE")
        saldo += importe
        
        movimientos.add_row([num, medio, comercio, concepto, "{0:.2f}".format(importe), "{0:.2f}".format(saldo)])

    print(movimientos)
    print("\n")

    
def borrarTodosMovimientos(tablas, reg):
    '''Borra todos los movimientos de una cuenta'''

    regParticipante = traerRegistroDeTabla(tablas["PERSONAS"], reg)
    regPersonaje = traerRegistroDeTabla(tablas["PERSONAJES"], regParticipante["fields"]["PERSONAJE"])
    regCuentas = traerRegistros(tablas["CUENTAS"], regPersonaje["fields"].get("CUENTA"))

    if not regCuentas:
        print("\nEl personaje not tiene ninguna cuenta.")
        return

    # Elegir cuenta
    regCuenta = elegirCuenta(regCuentas)

    listaCuentas = regCuenta["fields"].get("MOVIMIENTO")

    if listaCuentas:
        
        respuesta = input("\n"+f'¿Seguro que quieres borrar todos los movimientos? (S/N): ').upper()
        if respuesta == "S":
            for mov in listaCuentas:
                borrarRegistroDeTabla(tablas["MOVIMIENTOS"], [mov])
            print("Registros borrados.")
        else: print("Registros no borrados.")
        

def comprobarPersonaje(tabla, reg):
    ''' Comprueba si el participante tiene personaje asignado'''

    regParticipante = traerRegistroDeTabla(tabla, reg)
    regPersonaje = regParticipante["fields"].get("PERSONAJE")

    return regPersonaje


def nuevaCuenta(tablas, reg):
    '''Crear una nueva cuenta corriente y de tarjeta de crédito para un participante'''
    
    # Comprobar si ya tiene cuenta
    regEnlazado = comprobarPersonaje(tablas["PERSONAJES"], reg)

    # Comprobar que tiene personaje asignado
    if regEnlazado:

        regProfesion = traerRegistroDeTabla(tablas["PERSONAJES"], regEnlazado)
        tieneCuentaJubilacion = False
        tieneCuentaAhorro = False

        cuentas = regProfesion["fields"].get("CUENTA")

        if cuentas:

            # Ya tiene alguna cuenta
            regCuentas = traerRegistros(tablas["CUENTAS"], cuentas)
            print("\n")
            for cuenta in regCuentas:
                print(f'El personaje {regProfesion["fields"]["DENOMINACIÓN"]} ya tiene la cuenta {cuenta["fields"]["TIPO-CUENTA"]} número {cuenta["fields"]["NÚMERO-CUENTA"]}.')
                if cuenta["fields"]["TIPO-CUENTA"] == "JUBILACIÓN":
                    tieneCuentaJubilacion == True
                elif cuenta["fields"]["TIPO-CUENTA"] == "AHORRO":
                    tieneCuentaAhorro == True
                    
        else:

            # Crear registro de nueva cuenta corriente y de tarjeta de crédito

            campoCuenta = {
                "PERSONAJE": [regProfesion["id"]],
                "TIPO-CUENTA": "CORRIENTE",
            }

            try:
                regCorriente = crearRegistroEnTabla(tablas["CUENTAS"], campoCuenta)
                print("\n" + f'Cuenta corriente número {regCorriente["fields"]["NÚMERO-CUENTA"]} creada correctamente.')
            except:
                print("\nNo se ha podido crear el registro de la cuenta corriente.")
                return

            campoCuentaTarjeta = {
                "PERSONAJE": [regProfesion["id"]],
                "PERSONAJE-TARJETA": [regProfesion["id"]],
                "TIPO-CUENTA": "TARJETA",
            }

            try:
                regTarjeta = crearRegistroEnTabla(tablas["CUENTAS"], campoCuentaTarjeta)
                print("\n" + f'Cuenta de tarjeta número {regTarjeta["fields"]["NÚMERO-CUENTA"]} creada correctamente.')
            except:
                print("\nNo se ha podido crear el registro de la cuenta de tarjeta.")
                return

            # Poner primera mensualidad en la cuenta corriente

            regOcupacion = traerRegistroDeTabla(tablas["PROFESIONES"], regProfesion["fields"]["OCUPACIÓN1"])

            regMensualidad = {
                "PERSONAJE": [regProfesion["id"]],
                "NOMBRE": "MENSUALIDAD",
                "PERIÓDICO": True,
                "FRECUENCIA": "MENSUAL",
            }

            regSalario = crearRegistroEnTabla(tablas["PRODUCTOS-SERVICIOS"], regMensualidad)

            regMes = {
                "CUENTA": [regCorriente["id"]],
                "CONCEPTO": [regSalario["id"]],
                "MEDIO": "INGRESO",
            }

            crearRegistroEnTabla(tablas["MOVIMIENTOS"], regMes)

            # Poner deuda en la cuenta de la tarjeta de crédito
            buscadero = tablas["PRODUCTOS-SERVICIOS"].all(fields="NOMBRE")
            regConcepto = buscarRegistroDeCampoEnTabla(buscadero, "NOMBRE", "PAGO DEUDA TARJETA")
            importeDeuda = regOcupacion["fields"]["DEUDA-TARJETA-CRÉDITO"]
            
            regMov = {
                "CUENTA": [regTarjeta["id"]],
                "CONCEPTO": regConcepto,
                "MEDIO": "TARJETA-CRÉDITO",
                "IMPORTE-PARTICULAR": -importeDeuda,
            }

            crearRegistroEnTabla(tablas["MOVIMIENTOS"], regMov)

        if not tieneCuentaAhorro:

            ahorro = ""

            while not ahorro:

                try:
                    ahorro = input("\nCrear cuenta para el plan de ahorro (S/N): ").upper()
                except ValueError:
                    ahorro = ""

            if ahorro == "S":

                campoAhorro = {
                    "PERSONAJE": [regProfesion["id"]],
                    "PERSONAJE-AHORRO": [regProfesion["id"]],
                    "TIPO-CUENTA": "AHORRO",
                }

                try:
                    regAhorro = crearRegistroEnTabla(tablas["CUENTAS"], campoAhorro)
                    print("\n" + f'Cuenta del plan de ahorro número {regAhorro["fields"]["NÚMERO-CUENTA"]} creada correctamente.')
                except:
                    print("\nNo se ha podido crear el registro de la cuenta de ahorro.")
                    return

        if not tieneCuentaJubilacion:

            jubilacion = ""

            while not jubilacion:

                try:
                    jubilacion = input("\nCrear cuenta para el plan de jubilación (S/N): ").upper()
                except ValueError:
                    jubilacion = ""

            if jubilacion == "S":

                campoJubilacion = {
                    "PERSONAJE": [regProfesion["id"]],
                    "PERSONAJE-JUBILACIÓN": [regProfesion["id"]],
                    "TIPO-CUENTA": "JUBILACIÓN",
                }

                try:
                    regJubilacion = crearRegistroEnTabla(tablas["CUENTAS"], campoJubilacion)
                    print("\n" + f'Cuenta del plan de jubilación número {regJubilacion["fields"]["NÚMERO-CUENTA"]} creada correctamente.')
                except:
                    print("\nNo se ha podido crear el registro de la cuenta de jubilación.")
                    return

    else:

        print("\nEs necesario asignar primero un personaje.")
    

def comienzo(regParticipante):
    '''Pregunta comandos del menú principal y ejecuta las opciones'''

    tablas = cargarBase()
    
    muestraOpciones(menus.get("principal"))

    opcion = input("\n").upper()

    if opcion not in menus.get("principal").keys():
        print('Comando inválido')
        time.sleep(1)
        comienzo(regParticipante)
    elif opcion == 'C':
        clave = pedirClave()
        if clave == atk or clave == "Joshua":
            regParticipante = crearParticipante(tablas["PERSONAS"])
            print("Registro creado correctamente.")
        comienzo(regParticipante)
    elif opcion == 'L':
        listaParticipantes(tablas["PERSONAS"])
        comienzo(regParticipante)
    elif opcion == 'R':
        regParticipante = buscarParticipante(tablas["PERSONAS"])
        if regParticipante:
            opcionesParticipante(tablas, regParticipante)
        comienzo(regParticipante)
    elif opcion == 'S':
        # Validar salida y terminar guión
        clave = pedirClave()
        if clave == atk or clave == "Joshua":
            os._exit(1)
        else:
            comienzo(regParticipante)
        


def borrarPersonaje(tablas, reg):
    '''Borra un personaje del participante en la tabla PERSONAS'''

    tablaPersonas = tablas["PERSONAS"]
    tablaPersonajes = tablas["PERSONAJES"]
    
    regParticipante = traerRegistroDeTabla(tablaPersonas, reg)

    try:
        regEnlazado = regParticipante["fields"]["PERSONAJE"]

        # Comprobar si el personaje tiene el campo CUENTA vacío
        regPersonaje = traerRegistroDeTabla(tablaPersonajes, regEnlazado)

        try:
            regPersonaje["fields"]["CUENTA"]
            print("\nAntes de borrar el personaje es necesario borrar su cuenta.")
        except KeyError:
            
            # Borrar es asignar contenido vacío al campo
            respuesta = input("\n"+f'¿Seguro que quieres borrar el personaje {regPersonaje["fields"]["DENOMINACIÓN"]}? (S/N): ').upper()
            if respuesta == "S":
                asignarRegEnlazado(tablaPersonas, regParticipante, "PERSONAJE", [])
                print("Personaje borrado.")
            else: print("Registro no borrado.")

    except:
        print("\nEste participante no tiene asignado personaje.")


def borrarCuenta(tablas, reg):
    '''Borra una cuenta que no tenga movimientos'''

    regPersona = traerRegistroDeTabla(tablas["PERSONAS"], reg)
    regPersonaje = traerRegistroDeTabla(tablas["PERSONAJES"], regPersona["fields"]["PERSONAJE"])
    regCuenta = traerRegistroDeTabla(tablas["CUENTAS"], regPersonaje["fields"].get("CUENTA"))

    if not regCuenta:
        print("\n" + f'El personaje {regPersonaje["fields"].get("DENOMINACIÓN")} no tiene cuenta alguna.')
        return
    
    if regCuenta["fields"].get("MOVIMIENTO"):
        
        print("\nEs necesario eliminar los movimientos antes de borrar la cuenta.")

    else:

        # Eliminar registro de la tabla CUENTAS
        respuesta = input("\n"+f'¿Seguro que quieres borrar la cuenta número {regCuenta["fields"]["NÚMERO-CUENTA"]}? (S/N): ').upper()
        if respuesta == "S":
            tablas["CUENTAS"].delete(regCuenta["id"])
            print("\nCuenta borrada.")
        else: print("\nRegistro no borrado.")

def borrarRegistroDeTabla(tabla, reg):
    '''Borrar un registro de una tabla'''

    return tabla.delete(reg[0])
        

def borrarParticipante(tabla, reg):
    '''Borrar un participante de la tabla PERSONAS'''

    esBorrado = bool

    if not reg:
        print("Es necesario primero buscar un participante.")
    else:
        registro = traerRegistroDeTabla(tabla, reg)
        if registro:
            respuesta = input(f'¿Seguro que quieres borrar el registro de {registro["fields"]["PARTICIPANTE"]}? (S/N): ').upper()
            if respuesta == "S":
                try:
                    profesion = registro["fields"]["PROFESIÓN"]
                    print("El registro no se puede borrar porque ha comenzado una simulación.")
                except:
                    esBorrado = borrarRegistroDeTabla(tabla, reg)
                    if esBorrado["deleted"]:
                        print("Registro borrado correctamente.")
                    else: print("No se ha podido borrar el registro.")
            else: print("Registro no borrado.")
        else: print("No existe el registro.")


def borrarPersonaje(tablas, reg):
    '''Borra un personaje del participante en la tabla PERSONAS'''

    tablaPersonas = tablas["PERSONAS"]
    tablaPersonajes = tablas["PERSONAJES"]
    
    regParticipante = traerRegistroDeTabla(tablaPersonas, reg)

    try:
        regEnlazado = regParticipante["fields"]["PERSONAJE"]

        # Comprobar si el personaje tiene el campo CUENTA vacío
        regPersonaje = traerRegistroDeTabla(tablaPersonajes, regEnlazado)

        try:
            regPersonaje["fields"]["CUENTA"]
            print("\nAntes de borrar el personaje es necesario borrar su cuenta.")
        except:
            # Borrar es asignar contenido vacío al campo
            respuesta = input("\n"+f'¿Seguro que quieres borrar el personaje {regPersonaje["fields"]["DENOMINACIÓN"]}? (S/N): ').upper()
            if respuesta == "S":
                asignarRegEnlazado(tablaPersonas, regParticipante, "PERSONAJE", [])
                print("Personaje borrado.")
            else: print("Registro no borrado.")

    except:
        print("\nEste participante no tiene asignado personaje.")


def traerRegistroDeTabla(tabla, reg):
    '''Recupera un registro de una tabla

    Argumentos:
    - tabla: Table
    - reg: [str]

    Retorna: Record'''
    
    if not reg: return False

    try:
        return tabla.get(reg[0])
    except TypeError:
        return False
    except ConnectionError:
        return False


def traerRegistros(tabla, listaReg):
    '''Recupera varios registros de una tabla

    Argumentos:
    - Tabla: Table
    - Lista de claves primarias: [str]

    Retorna: Lista de registros: [Record]'''

    if listaReg:
        lista = []

        for reg in listaReg:
            try:
                registro = tabla.get(reg)
                lista.append(registro)
            except:
                pass

        if lista:
            return lista
        else:
            return False
    else:
        return False


def buscarRegistroDeCampoEnTabla(buscadero, nombreCampo, dato):
    ''' Buscar el registro que tenga el dato en el nombreCampo de la tabla

        Argumentos:
        - buscadero: list(dict)
            Tabla de la base de datos donde buscar
        - nombreCampo: str
            Nombre del campo de la tabla que se aporta
        - dato: str
            Valor del campo a partir del cual se busca

        Retorna:
        - lista con id del registro encontrado: [str]
        - lista vacía si no lo encuentra'''

    return [
        reg["id"] for reg in buscadero if reg["fields"].get(nombreCampo) == dato
    ]


def buscarParticipante(tabla):
    '''Buscar un participante'''

    nombre = input("Introduce nombre: ").upper()
    apellido1 = input("Introduce primer apellido: ").upper()
    apellido2 = input("Introduce segundo apellido: ").upper()

    nombreCompleto = f'{apellido1} {apellido2}, {nombre}'
    buscadero = tabla.all(fields = ["NOMBRE COMPLETO"])

    encontrados = buscarRegistroDeCampoEnTabla(buscadero, "NOMBRE COMPLETO", nombreCompleto)

    if encontrados:
        print("\n"+f'Encontrado: {encontrados[0]}')
    else:
        print("\nRegistro no encontrado.")

    return encontrados


def pedirTipoParticipante():
    '''Pedir y validar tipo de participante'''

    tipo = input("Selecciona tipo, [E]studiante o [C]omerciante: ")

    if tipo.upper() == "E":
        tipo = "ESTUDIANTE"
    elif tipo.upper() == "C":
        tipo = "COMERCIANTE"
    else:
        pedirTipoParticipante()

    return tipo


def crearParticipante(tabla):
    '''Crea un participante en la tabla PERSONAS'''

    print("Creación de un participante")

    nombre = ""
    apellido1 = ""
    apellido2 = ""

    while not nombre:
        nombre = comprobarDatosDelParticipante("Introduce el nombre del participante: ", "nombre")

    while not apellido1:        
        apellido1 = comprobarDatosDelParticipante("Introduce el primer apellido del participante: ", "apellido1").upper()

    nombre = nombre.upper()
    apellido1 = apellido1.upper()
    apellido2 = input("Introduce segundo apellido del participante: ").upper()

    tipo = pedirTipoParticipante()

    esquemaPersonas = {
        "fields": {
            "APELLIDO1": apellido1,
            "APELLIDO2": apellido2,
            "NOMBRE": nombre,
            "TIPO": tipo,
        }
    }

    return crearRegistroEnTabla(tabla, esquemaPersonas.get("fields"))
    

def comprobarDatosDelParticipante(mensaje, tipoDato):
    '''Validar introducción de los datos del participante'''

    dato = input(mensaje).upper()
    try:
        # validarNombre o validarApellido1
        getattr(validador, f'validar{tipoDato.capitalize()}')(dato)
        return dato
    except ValueError as error:
        print(error)
        return None


def listaRegistrosEnTabla(tabla, conf, campoOrden):
    '''Lista de registros en una tabla'''

    lista = PrettyTable()
    lista.field_names = conf["campos"]
    for i, ajuste in enumerate(conf["ajuste"]):
        col = conf["campos"][i]
        lista.align[col] = ajuste       
    lista.set_style(PLAIN_COLUMNS)
    
    for reg in tabla.all(sort = [campoOrden]):
        
        fila = []

        for campo in conf["campos"]:
            # Horizontal
            columna = reg["fields"].get(campo)
            if columna:
                if type(columna) == type(str()):
                    fila.append(columna)
                elif type(columna) == type(list()):
                    if type(columna[0]) == type(float()) or type(columna[0]) == type(int()):
                        fila.append("{0:.2f} €".format(columna[0]))
                    elif type(columna[0]) == type(str()):
                        fila.append(columna[0].upper())
            else:
                fila.append("--")

        lista.add_row(fila)

    print(lista)


def listaParticipantes(tabla):
    '''Mostrar listado de participantes'''

    print("\nLista de participantes")

    campos = ["NOMBRE COMPLETO", "PROFESIÓN", "SALDO"]
    alineamiento = ["l", "l", "r"]
    conf = {
        "campos": campos,
        "ajuste": alineamiento,
    }
    campoOrden = campos[0]

    listaRegistrosEnTabla(tabla, conf, campoOrden)


def modificarCampo(tabla, campo, nuevoDato, reg):
    '''Modificar un registro en una tabla'''

    try:
        resultado = tabla.update(reg[0], {campo: nuevoDato})
        return resultado
    except:
        return False


def pedirModificacion(tabla, regParticipante):
    '''Pedir nuevo dato para modificar'''

    campo = str

    muestraOpciones(menus.get("modificarParticipante"))

    opcion = input("\n").upper()

    if opcion == 'N':
        campo = "NOMBRE"
        nombre = input("Nuevo nombre: ").upper()
        resultado = modificarCampo(tabla, campo, nombre, regParticipante)
        if resultado:
            print("Datos modificados correctamente.")
        else: print("No se ha podido hacer la modificación.")
        pedirModificacion(tabla, regParticipante)
    elif opcion == 'R':
        regParticipante = buscarParticipante(tabla)
    elif opcion == 'P':
        campo = "APELLIDO1"
        nombre = input("Nuevo primer apellido: ").upper()
        resultado = modificarCampo(tabla, campo, nombre, regParticipante)
        if resultado:
            print("Datos modificados correctamente.")
        else: print("No se ha podido hacer la modificación.")
        pedirModificacion(tabla, regParticipante)
    elif opcion == 'S':
        campo = "APELLIDO2"
        nombre = input("Nuevo segundo apellido: ").upper()
        resultado = modificarCampo(tabla, campo, nombre, regParticipante)
        if resultado:
            print("Datos modificados correctamente.")
        else: print("No se ha podido hacer la modificación.")
        pedirModificacion(tabla, regParticipante)
    elif opcion == 'T':
        campo = "TIPO"
        nombre = input("Nuevo tipo (COMERCIANTE/ESTUDIANTE): ").upper()
        resultado = modificarCampo(tabla, campo, nombre, regParticipante)
        if resultado:
            print("Datos modificados correctamente.")
        else: print("No se ha podido hacer la modificación.")
        pedirModificacion(tabla, regParticipante)
    elif opcion == 'V':
        # Volver al menú anterior
        comienzo(regParticipante)
    else:
        print('Comando inválido')
        time.sleep(1)
        pedirModificacion(tabla, regParticipante)


def modificarParticipante(tabla, regParticipante):
    '''Pedir nuevos datos y modificar registro en la tabla PERSONAS'''

    try:
        resultado = tabla.get(regParticipante[0])
    except:
        resultado = []

    if not regParticipante: print("Es necesario primero buscar un participante.")
    elif not resultado: print("Registro ya borrado.")
    else: pedirModificacion(tabla, regParticipante)


#
# Ejecución principal
# -------------------
#

atk = ""

if __name__ == "__main__":

    clear()
    print("\nSistema de Educación Financiera Escolar de Alborada")
    print("{:-^51}".format(""))

    while not atk:
        atk = pedirClave()
    
    print("\nSaludos, profesor Falken.")

    claveInterrupcion = ""
    
    try:
        comienzo([])
    except KeyboardInterrupt:
        claveInterrupcion = pedirClave()
        if claveInterrupcion == atk or claveInterrupcion == "Joshua":
            os._exit(1)
        else:
            comienzo([])
