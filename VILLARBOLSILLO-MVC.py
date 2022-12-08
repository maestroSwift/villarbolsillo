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
import collections
import numpy as np
import pandas as pd
from pyairtable import Table
from prettytable import PLAIN_COLUMNS, PrettyTable


#
# Clases
# ------
#


#
# Modelo
#
class modelo:

    # Atributos

    # Menú de opciones
    class Menu(object):
        'Gestiona los menús de opciones'
        def __init__(self):
            self.titulo = "" # Título del menú
            self.listaOpciones = dict() # Diccionario con opciones

    # Personaje
    class Persona(object):
        "Gestiona el registro completo de un participante."

        # Atributos

        # Constructor
        def __init__(self, tablas, reg={
            {
                "id": "",
                "fields": {
                    "NOMBRE": "",
                    "APELLIDO1": "",
                    "APELLIDO2": "",
                    "TIPO": "",
                    "PERSONAJE": [],
                    # Campos calculados
                    "NOMBRE COMPLETO": "",
                    "SALDO": 0.0,
                    "PROFESIÓN": "",
                    "SALARIO": 0.0,
                    "PROFESIÓN-CÓNYUGE": "",
                    "SALARIO-CÓNYUGE": 0.0,
                    "NOMBRE-HIJOS": "",
                    "EDAD-HIJOS": "",
                    "CRÉDITO-UNIVERSITARIO": 0.0,
                    "COPAGO-SEGURO-MÉDICO": 0.0,
                    "DEUDA-TARJETA-CRÉDITO": 0.0,
                    "PAGO-MÍNIMO-TARJETA-CRÉDITO": 0.0,
                }
            }
        }):
            "Construye el participante con sus registros enlazados."
            # Tablas para usar
            self.tablaParticipantes = tablas["PERSONAS"]
            self.tablaPersonajes = tablas["PERSONAJES"]
            self.tablaCuentas = tablas["CUENTAS"]
            self.tablaMovimientos = tablas["MOVIMIENTOS"]
            self.tablaProdServicios = tablas["PRODUCTOS-SERVICIOS"]
            self.tablaComercios = tablas["COMERCIOS"]
            # Identificación del registro
            self.reg = reg
            "Registro del participante."
            # Banderas de estado del registro
            self.estado = {
                "tienePersonaje": False,
                "tieneCuentas": False,
                "tieneMovimientos": False,
            }
            self.regPersonaje = {}
            "Registro del personaje asignado."
            self.listaRegCuentas = []
            "Lista de registros de cuentas asignadas y sus movimientos."
            # Registro enlazado de personaje
            id = reg["fields"].get("PERSONAJE")
            if id:
                # Tiene personaje
                self.estado["tienePersonaje"] = True
                self.regPersonaje = self.tablaPersonajes.get(id[0])
                # Registros enlazados de cuentas
                listaIdCuentas = self.regPersonaje["fields"].get("CUENTA")
                if listaIdCuentas:
                    # Tiene cuentas
                    self.estado["tieneCuentas"] = True
                    for i, idCuenta in enumerate(listaIdCuentas):
                        self.listaRegCuentas.append({
                            "idReg": self.tablaCuentas.get(idCuenta).get("id"),
                            "tipo": self.tablaCuentas.get(idCuenta)["fields"].get("TIPO-CUENTA"),
                            "movCuenta": [],
                            "periodicosRegistrados": [],
                            # Número máximo de gestiones disponibles esta semana
                            # Grandes, 2; Medianas, 4; Pequeñas, 8
                            "gestionabilidad": {
                                "GRANDE": int(2),
                                "MEDIANA": int(4),
                                "PEQUEÑA": int(8),
                            },
                        })
                        "Lista de registros de cuentas asignadas al personaje."
                        # Registros enlazados de movimientos
                        listaIdMovimientosCuenta = self.tablaCuentas.get(idCuenta)["fields"].get("MOVIMIENTO")
                        if listaIdMovimientosCuenta:
                            # Hay movimientos en esta cuenta
                            "Lista de movimientos asignados a una cuenta del personaje."
                            self.estado["tieneMovimientos"] = True
                            # Número de movimientos periódicos registrados
                            for reg in listaIdMovimientosCuenta:
                                try:
                                    registro = self.tablaMovimientos.get(reg)
                                    self.listaRegCuentas[-1]["movCuenta"].append(registro)
                                    # Calcular número de gestiones que queda en la semana
                                    if registro["fields"].get("MISMA-SEMANA") == 1:
                                        if registro["fields"].get("GESTIÓN")[0] == "GRANDE":
                                            self.listaRegCuentas[-1]["gestionabilidad"]["GRANDE"] -= 1
                                        elif registro["fields"].get("GESTIÓN")[0]== "MEDIANA":
                                            self.listaRegCuentas[-1]["gestionabilidad"]["MEDIANA"] -= 1
                                        elif registro["fields"].get("GESTIÓN")[0] == "PEQUEÑA":
                                            self.listaRegCuentas[-1]["gestionabilidad"]["PEQUEÑA"] -= 1        
                                    # Recoger movimientos periódicos registrados en una lista de diccionarios
                                    frec = registro["fields"].get("FRECUENCIA")[0]
                                    concepto = registro["fields"].get("CONCEPTO-LITERAL")[0]
                                    numPeriodos = int(registro["fields"].get("TIEMPO-DESDE-MOVIMIENTO"))
                                    if frec:
                                        self.listaRegCuentas[-1]["periodicosRegistrados"].append({
                                            "CONCEPTO": concepto,
                                            "PERÍODOS": numPeriodos,
                                            "FRECUENCIA": frec,
                                        })                                        
                                except TypeError:
                                    pass
            

        # Métodos privados

        # Comprobar si existe el registro en la tabla
        def _existe(self):
            "Comprueba si existe el registro en la tabla."
            if self.id:
                return True
            else:
                return False

        # Comprobar si todas las cuentas han sido borradas
        def _comprobarSinCuentas(self):
            "Comprueba si todas las cuentas han sido borradas"
            if len(self.listaRegCuentas):
                self.estado["tieneCuentas"] = True
            else:
                self.estado["tieneCuentas"] = False

        # Métodos públicos

        # Actualizar campos
        def actualizarCampos(self, campos):
            "Modifica los campos que cambian del registro"
            conCambios = []
            for llave in campos:
                valorViejo = self.reg["fields"][llave]
                valorNuevo = campos.get(llave)
                if valorViejo == valorNuevo:
                    conCambios.append(False)
                else:
                    conCambios.append(True)
                    valorViejo = valorNuevo
            # Solo guardamos si hay algún cambio
            if True in conCambios:
                self.guardar()
                return True
            else:
                return False

        # Guardar datos
        def guardar(self):
            "Crea o actualiza el registro en la tabla."
            # Comprobar si existe el registro en la tabla
            if self._existe():
                # Actualizar
                return self.tablaParticipante.update(self.reg.get("id"), self.reg.get("fields"))
            else:
                # Crear registro
                try:
                    reg = self.tablaParticipante.create(self.reg.get("fields"))
                    self.reg["id"] = reg.get("id")
                except:
                    self.reg["id"] = reg.get("id")
                
        # Recuperar un registro de una tabla a partir de un campo
        def traerRegistroDeCampoEnTabla(self, tabla, nombreCampo, dato):
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
                reg["id"] for reg in tabla if reg["fields"].get(nombreCampo) == dato
            ]

        # Recuperar un registro de una tabla
        def traerRegistroDeTabla(self, tabla, reg):
            "Recupera un registro de una tabla"
            if not reg: return False
            try:
                return tabla.get(reg)
            except TypeError:
                return False
            except ConnectionError:
                return False

        # Borrar registro
            

        # Comprobar si tiene personaje asignado
        def conPersonaje(self):
            "Comprueba si tiene personaje asignado."
            if self.estado.get("tienePersonaje"):
                return True
            else:
                return False

        # Comprobar si el personaje tiene cuentas asignadas
        def conCuentas(self):
            "Comprueba si el personaje tiene cuentas asignadas."
            if self.estado.get("tieneCuentas"):
                return True
            else:
                return False

        # Comprobar si la cuenta tiene movimientos asignados
        def conMovimientos(self):
            "Comprueba si la cuenta tiene movimimentos asignados."
            if self.estado.get("tieneMovimientos"):
                return True
            else:
                return False

        # Recuperar lista de cuentas
        def listaCuentas(self):
            "Recupera la lista de cuentas de un personaje"
            return self.listaRegCuentas

        # Crear cuenta
        def crearCuenta(self, tipo):
            """Crea en la tabla de cuentas una cuenta del tipo indicado para el personaje
            con las reglas de cada tipo de cuenta:
            - Corriente: primer movimiento con importe de la mensualidad del personaje.
            - Tarjeta: primer movimiento con importe de la deuda
            - Ahorro: saldo cero
            - Jubilación: saldo cero"""
            if tipo == "CORRIENTE":
                campoCuenta = {
                    "PERSONAJE": [self.regPersonaje["id"]],
                    "TIPO-CUENTA": tipo,
                }
                regCorriente = self.tablaCuentas.create(campoCuenta)
                # Poner primera mensualidad en la cuenta corriente
                regMensualidad = {
                    "PERSONAJE": [self.regPersonaje["id"]],
                    "NOMBRE": "MENSUALIDAD",
                    "PERIÓDICO": True,
                    "FRECUENCIA": "MENSUAL",
                }
                regSueldo = self.tablaProdServicios.create(regMensualidad)
                regMes = {
                    "CUENTA": [regCorriente["id"]],
                    "CONCEPTO": [regSueldo["id"]],
                    "MEDIO": "INGRESO",
                }
                regMovimiento = self.tablaMovimientos.create(regMes)

    class BaseDatos(Persona):
        "Gestión reunida de los registros"

        # Constructor
        def __init__(self, tablas):
            self.listaPersonas = []
            tablaPersonas = tablas["PERSONAS"].all()
            for registro in tablaPersonas["records"]:
                reg = super().__init__(tablas, registro)
                self.listaPersonas.append(reg)

        def buscarPersona(self, nombreCampo, datoCampo):
            "Busca una persona que tenga un nombre. Devuelve: (registro, posición)"
            resultado = [(reg.reg["id"], self.listaPersonas.index(reg)) for reg in self.listaPersonas if reg.reg["fields"].get(nombreCampo) == datoCampo]
            return resultado

        def borrarPersona(self, reg):
            "Borra una persona reg de la tabla: reg = (registro, posición)"
            registroBorrado = self.listaPersonas.pop(reg[1])
            # Guardar borrado en la tabla
            return registroBorrado.tablaParticipantes.delete(reg[0].reg["id"])
            
            

    # Métodos privados

    # Autentificación
    def _cargaCredenciales(self):
        'Carga credenciales de acceso a la base de datos desde las variables de entorno'
        return {
            "bd": os.environ.get("DATABASE"),
            "atk": os.environ.get("PASSWORD"),
        }

    # Cargar configuración
    def _cargarConfiguracion(self):
        'Devuelve la configuración alojada en archivo toml'
        with open("conf.toml", mode="rb") as fichero:
            conf = tomllib.load(fichero)
        return conf

    # Crear un registro en una tabla de la base de datos
    def _crearRegistroEnTabla(self, tabla, registro):
        "Crea un registro en una tabla de la base de datos"
        try:
            reg = tabla.create(registro)
            return reg
        except:
            return None

    # # Recuperar un registro de una tabla
    # def _traerRegistroDeTabla(self, tabla, reg):
    #     '''Recupera un registro de una tabla de la base de datos
    #     Argumentos:
    #     - tabla: Table
    #     - reg: [str]
    #     Devuelve: Record o False'''
    #     # Validar que no esté vacío
    #     if not reg: return False
    #     # Intentar carga
    #     try:
    #         return tabla.get(reg[0])
    #     except TypeError:
    #         return False
    #     except ConnectionError:
    #         return False

    # Buscar un registro a partir de un campo en una tabla
    def _buscarPersona(self, baseDatos, nombreCampo, dato):
        ''' Busca el registro con el dato en el campo de la tabla.
        Argumentos:
            - tabla: list(dict)
                Tabla de la base de datos donde buscar
            - nombreCampo: str
                Nombre del campo de la tabla que se aporta
            - dato: str
                Valor del campo a partir del cual se busca
        Retorna:
            - lista con id del registro encontrado: [str]
            - lista vacía si no lo encuentra'''
        return baseDatos.buscarPersona(nombreCampo, dato)

    # Comprobar si un participante es borrable
    def _esParticipanteBorrable(self, reg):
        "Comprueba si no tiene asignado personaje, cuentas, movimientos"
        return not reg.estado["tienePersonaje"]

    # Comprobar si un personaje es borrable
    def _esSinCuentas(self, reg):
        "Comprueba si no tiene asignadas cuentas"
        cuentas = reg["fields"].get("CUENTA")
        if cuentas:
            return False
        else:
            return True

    # Cargar lista de personajes
    def _cargarPersonajes(self, tabla):
        "Pone en una lista los personajes"
        return tabla.all(sort=["REFERENCIA"], fields=["PERSONAJE", "REFERENCIA", "PARTICIPANTE"])

    # Preparar lista de personajes
    def _prepararListaProfesiones(self, lista):
        "Preparar una lista con las profesiones ocupadas para mostrar"
        referenciasOcupadas = []
        for i, reg in enumerate(lista):
            personajeOcupado = reg["fields"].get("PARTICIPANTE")
            referenciasOcupadas.append(reg)
            if personajeOcupado:
                # Eliminar profesión de la lista
                referenciasOcupadas[i] = "--"
        return referenciasOcupadas

    # Contar conceptos y número máximo de períodos transcurridos en movimientos
    def _contarConceptos(self, tablaMovPeriodicos):
        "Cuenta los conceptos y el número máximo de períodos transcurridos en los movimientos."
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

    # Añadir los movimientos periódicos distintos últimos en la tabla de MOVIMIENTOS
    def _anadirUltimosMovPeriodicos(self, regParticipante, regCuenta, lista):
        """ Crear registros de movimientos periódicos que faltan según el tiempo transcurrido desde el último movimiento periódico.
        Argumentos:
        - regCuenta: registro de la cuenta que tiene los movimientos.
        - lista: dict(dict)
            Diccionario con los diccionarios de cada concepto el número de períodos y máximo:
            {(concepto, frecuencia): {"CUENTA": int, "PENDIENTES": int}}
        """
        listaRegConceptos = regParticipante.tablaProdServicios.all(fields=["NOMBRE", "PRODUCTO-SERVICIO"])
        for mov in lista:
            numMov = lista[mov]["PENDIENTES"] - lista[mov]["CUENTA"]
            if numMov > 0:
                concepto, frecuencia = mov
                # Añadir movimiento del concepto
                if concepto == "MENSUALIDAD":
                    ocupacion = regParticipante.regPersonaje["fields"].get("PERSONAJE")
                    regConcepto = [
                        reg["id"] for reg in listaRegConceptos if reg["fields"].get("PRODUCTO-SERVICIO") == concepto+"|"+ocupacion
                    ]
                    medio = "INGRESO"
                else:
                    regConcepto = [
                        reg["id"] for reg in listaRegConceptos if reg["fields"].get("NOMBRE") == concepto    
                    ]
                    medio = "TALÓN"
                regProducto = regParticipante.tablaProdServicios.get(regConcepto[0])
                # Crear registro del movimiento en la tabla MOVIMIENTOS
                campoMov = {
                    "CUENTA": [regCuenta["id"]],
                    "CONCEPTO": [regConcepto["id"]],
                    "MEDIO": medio,
                }
                # Posición de la cuenta en la lista
                indice = [i for i, valor in enumerate(regParticipante.listaRegCuentas.values()) if i == regCuenta["id"]]
                # Añadimos tantos movimientos periódicos como períodos han pasado desde la última vez
                for _ in range(numMov):
                    reg = self._crearRegistroEnTabla(regParticipante.tablaMovimientos, campoMov)
                    # Añadir registro recién creado en la lista de movimientos
                    regParticipante.listaRegCuentas[indice]["movCuenta"].append(reg)


    # Métodos públicos

    # Validación de la contraseña
    def validarAcceso(self, clave):
        "Comprueba si las credenciales son correctas"
        credenciales = self._cargaCredenciales()
        if clave == credenciales.get("atk") or clave == "Joshua":
            return True
        else:
            return False

    # Cargar menús
    def cargaMenus(self):
        "Recupera los menús del archivo de configuración"
        menus = self._cargarConfiguracion().get("menu")
        catalogo = dict()
        llaves = menus.keys()
        catalogo = {}.fromkeys(llaves, self.Menu())
        for clave in catalogo.keys():
            claves = menus.get(clave).keys()
            lineas = menus.get(clave).values()
            menu = {}.fromkeys(claves, "")
            for llave, linea in zip(claves, lineas):
                menu[llave] = linea
            catalogo[clave] = menu
        return catalogo
    
    # Cargar base de datos
    def cargaBaseDatos(self):
        'Carga la base de datos de Airtable'
        # Cargar credenciales
        credenciales = self._cargaCredenciales()
        atk = credenciales.get("atk")
        idBaseDatos = credenciales.get("bd")
        # Cargar tablas
        tablas = {
            "PERSONAS": Table(atk, idBaseDatos, "PERSONAS"),
            "COMERCIOS": Table(atk, idBaseDatos, "COMERCIOS"),
            "PERSONAJES": Table(atk, idBaseDatos, "PERSONAJES"),
            "CUENTAS": Table(atk, idBaseDatos, "CUENTAS"),
            "MOVIMIENTOS": Table(atk, idBaseDatos, "MOVIMIENTOS"),
            "PRODUCTOS-SERVICIOS": Table(atk, idBaseDatos, "PRODUCTOS-SERVICIOS"),
            "PROFESIONES": Table(atk, idBaseDatos, "PROFESIONES"),
        }
        # Lista de participantes
        baseDatos = self.BaseDatos(tablas)
        return (tablas, baseDatos)

    # Crear participante
    def crearParticipante(self, baseDatos, participante):
        "Prepara datos del registro y crea un registro en la tabla PERSONAS"
        campos = participante["PERSONAJE"] = []
        esquema = {
            "id": "",
            "fields": campos,
        }
        tablas = {
            "PERSONAS": baseDatos[0].tablaParticipante,
            "PERSONAJES": baseDatos[0].tablaPersonajes,
            "CUENTAS": baseDatos[0].tablaCuentas,
            "MOVIMIENTOS": baseDatos[0].tablaMovimientos,
        }
        persona = self.Persona(tablas, esquema)
        baseDatos.append(persona)
        persona.guardar()
        return persona

    # Preparar impresión de un participante
    def prepararImpresionRegParticipante(self):
        "Prepara los datos del registro y la configuración para mostrar en pantalla"
        # Configuración de los campos y orientación
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
        return conf

    # Preparar lista de participantes
    def prepararImpresionListaParticipantes(self):
        "Prepara la configuración de la lista de participantes"
        campos = ["NOMBRE COMPLETO", "PROFESIÓN", "SALDO"]
        alineamiento = ["l", "l", "r"]
        conf = {
            "campos": campos,
            "ajuste": alineamiento,
        }
        campoOrden = campos[0]
        return (conf, campoOrden)

    # Recuperar participante
    def yaExiste(self, baseDatos, persona):
        "Busca un participante en la tabla PERSONAS"
        nombreCompleto = f'{persona["APELLIDO1"]} {"APELLIDO2"}, {persona["NOMBRE"]}'
        buscadero = baseDatos.tablaParticipante.all(fields = ["NOMBRE COMPLETO"])
        encontrado = self._buscarRegistroDeCampoEnTabla(buscadero, "NOMBRE COMPLETO", nombreCompleto)
        return encontrado

    # Guardar datos

    # Modificar registro
    def modificarCampos(campos, reg):
        '''Modificar un registro en una tabla'''
        return reg.actualizarCampos(campos)

    # Borrar registro de una tabla
    def borrarRegistroDeTabla(self, baseDatos, reg):
        "Borra un registro de una tabla"
        return baseDatos.borrarPersona(reg)

    # Determinar estado del participante para asignar personaje
    def estadoParticipante(self, regParticipante):
        "Comprueba si el participante ya tiene personaje o cuentas o movimientos"
        # Estado del participante
        estado = {
            "tienePersonaje": False,
            "tieneCuentas": False,
            "tieneMovimientos": False,
        }
        estado = regParticipante[0].estado
        return estado

    # Asignar un registro enlazado en un campo
    def asignarRegistroEnlazado(self, tabla, regPrincipal, nombreCampo, regDato):
        "Asigna a un campo de un registro principal un registro enlazado"
        # Preparar datos
        campo = {nombreCampo: regDato}
        idRegPrincipal = regPrincipal.reg["id"]
        # Actualización del campo
        try:
            tabla.update(idRegPrincipal, campo)
            regPrincipal.reg["fields"][nombreCampo] = regDato
            return True
        except:
            return False

    # Crear cuentas
    def crearCuentas(self, reg):
        """ Comprueba si existe personaje y crea las cuentas que faltan.
            Devuelve:
                · lista de cuentas sin tipo de cuenta para completar.
                · 0 si todas las cuentas están creadas.
                · -1 si no tiene personaje creado.
        """
        # Determinar si existe personaje
        if reg.conPersonaje():
            # Determinar qué cuentas existen
            tiposCuenta = ["CORRIENTE", "JUBILACIÓN", "AHORRO", "TARJETA"]
            if reg.conCuentas():
                # Mirar si alguna cuenta no tiene tipo
                cuentasSinTipo = filter(lambda regCuenta: regCuenta["fields"].get("TIPO-CUENTA") not in ["CORRIENTE", "JUBILACIÓN", "AHORRO", "TARJETA"], reg.listaRegCuentas)
                # Determinar qué cuentas faltan
                listaTiposCuenta = [regCuenta["fields"].get("TIPO-CUENTA") for regCuenta in reg.listaCuentas]
                tiposCuentaYaCreados = collections.Counter(listaTiposCuenta).keys()
                tiposCuentaQueFaltan = [tipo for tipo in tiposCuenta if tipo not in tiposCuentaYaCreados]
                if tiposCuentaQueFaltan:
                    # Crear las cuentas que faltan
                    for tipo in tiposCuentaQueFaltan:
                        if cuentasSinTipo:
                            # Informar de las cuentas para actualizar el tipo
                            return cuentasSinTipo
                        else:
                            reg.crearCuenta(tipo)
                else:
                    # Todas las cuentas creadas y no falta ninguna
                    return 0
            else:
                # No tiene cuentas creadas
                for tipo in tiposCuenta:
                    reg.crearCuenta(tipo)
                return 0
        else:
            # No tiene personaje
            return -1                  
                        
    # Borrar cuentas
    def borrarCuenta(self, reg, regCuenta):
        """ Comprueba si existe personaje y sus cuentas tienen borrados sus movimientos.
            Devuelve:
            cuenta con movimientos sin borrar.
            0 si esta cuenta ha sido borrada.
            -1 si no hay personaje asignado.
        """
        if reg.conPersonaje():
            # Determinar si existen cuentas
            if reg.conCuentas():
                # Determinar si la cuenta tiene movimientos
                listaMovimientos = regCuenta["fields"].get("MOVIMIENTO")
                tipoCuenta = regCuenta["fields"].get("TIPO-CUENTA")
                cuenta = {
                    "idReg": regCuenta["id"],
                    "movCuenta": listaMovimientos,
                }
                if listaMovimientos:
                    # Devolvemos la cuenta con movimientos para que los puedan borrar
                    return (cuenta, tipoCuenta)
                else:
                    # Podemos borrar la cuenta porque no tiene movimientos
                    reg.tablaCuentas.delete(regCuenta["id"])
                    reg.listaIdCuentas.remove(cuenta)
                    reg._comprobarSinCuentas()
                    # REVISAR: ¿Guardar datos?
                    return 0
            else:
                return 0
        else:
            return -1

    # Registrar movimientos periódicos pendientes
    def registrarMovPendientes(self, regParticipante):
        ''' Si hace tiempo que no se han registrado movimientos, puede haber obligaciones y derechos
        periódicos que no se hayan registrado en la tabla MOVIMIENTOS. Comprobar y registrar
        movimientos pendientes.'''
        for cuenta in regParticipante.listaCuentas():
            regCuenta = regParticipante.tablaCuentas.get(cuenta.get("idReg"))
            # Contamos el número de cada concepto y el número máximo de períodos transcurridos
            marcoConceptos = self._contarConceptos(cuenta.get("periodicosRegistrados"))
            # Comparamos con el número de meses o semanas del último movimiento periódico
            # Si coincide entonces no hay que hacer nada (nos quedamos con los distintos)
            marcoDistintos = marcoConceptos[marcoConceptos.CUENTA != marcoConceptos.PENDIENTES]
            # Si el número de meses o semanas desde el último movimiento es superior al número de conceptos
            # entonces hay que añadir tantos movimientos como la diferencia para igualarlo al número de conceptos
            listaMovDistintos = marcoDistintos.to_dict("index")
            self._anadirUltimosMovPeriodicos(regParticipante, regCuenta, listaMovDistintos)
            
    def listaComercios(self, regParticipante):
        "Recopila los comercios en una lista para mostrar"
        listaComercios = regParticipante.tablaComercios.all(sort=["NOMBRE"], fields=["NOMBRE", "PRODUCTOS-SERVICIOS"])
        lineas = str
        for regComercio in listaComercios:
            if regComercio["fields"].get("PRODUCTOS-SERVICIOS"):
                # No es Ayuntamiento
                nombre = regComercio["fields"].get("NOMBRE")
                lineas += f'{listaComercios.index(regComercio) + 1}. {nombre}.\n'
        return (listaComercios, lineas)

    def prepararListaProductos(self, regParticipante, listaProductos):
        "Reune los productos o servicios de un comercio en una lista para mostrar"
        sinGasto = True
        sinOtroGasto = True
        # Preparar ajustes de la tabla
        cabecera = ["OPCIÓN", "PRODUCTO/SERVICIO", "IMPORTE(€)"]
        ajuste = ["c", "l", "r"]
        cosas = PrettyTable()
        cosas.field_names = cabecera
        for i, ajuste in enumerate(ajuste):
            col = cabecera[i]
            cosas.align[col] = ajuste 
        cosas.set_style(PLAIN_COLUMNS)
        # Reunir en lista los productos
        for regProducto in listaProductos:
            registro = regParticipante.tablaProdServicios.get(regProducto["id"])
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
        return cosas

    def traerRegistroDeTabla(self, tabla, reg):
        "Recupera el registro de una tabla"
        return tabla.get(reg)

    def esGestionable(self, regParticipante, regProducto):
        "Comprueba si se excede el número máximo de movimientos esta semana."
        # Para este producto se requiere una gestión PEQUEÑA, MEDIANA o GRANDE
        gestion = regProducto["fieds"].get("GESTIÓN")
        # Buscamos la gestionabilidad de la cuenta corriente
        gestionabilidad = [
            elemento.get("gestionabilidad") for elemento in regParticipante.listaRegCuentas if regParticipante.tablaCuentas.get(elemento.get("idReg"))["fields"].get("TIPO-CUENTA") == "CORRIENTE"
        ]
        # Comprobar si hay suficientes gestiones disponibles
        if gestionabilidad.get(gestion) - 1 < 0:
            return False
        else:
            return True
        
    def haySaldoSuficiente(self, regParticipante, regProducto):
        "Comprueba si hay saldo suficiente en la cuenta corriente"
        coste = regProducto["fields"].get("PRECIO")
        saldo = regParticipante.tablaParticipantes.get(regParticipante.reg["id"])["fields"].get("SALDO")
        if coste and saldo:
            if coste < 0 and coste > saldo:
                # No hay dinero suficiente en la cuenta
                return False
            else:
                return True

    def gestionBanco(self, regParticipante, producto):
        """ Reunir datos complementarios para el Banco Cooperativo
            Devuelve:
            -1 si no tiene cuenta de tarjeta de crédito.
            -2 si no tiene cuenta de jubilación.
            -3 si no tiene cuenta de ahorro.
            1 si es movimiento para tarjeta de crédito.
            2 si es movimiento para aportar a jubilación.
            3 si es movimiento para aportar al ahorro.
        """
        resultado = 0
        listaCuentas = regParticipante.listaCuentas()
        tipoCuentas = [tipo.get("tipo") for tipo in listaCuentas]
        if producto == "PAGO DEUDA TARJETA":
            if "TARJETA" not in tipoCuentas:
                resultado = -1
            else:
                resultado = 1
        elif producto == "APORTACIÓN CUENTA JUBILACIÓN":
            if "JUBILACIÓN" not in tipoCuentas:
                resultado = -2
            else:
                resultado = 2
        elif producto == "PLAN AHORRO":
            if "AHORRO" not in tipoCuentas:
                resultado = -3
            else:
                resultado = 3
        return resultado
    
    # Nuevo movimiento

    # Borrar movimiento

    # Modificar movimiento (devoución de artículo)

    # Borrar todos los movimientos


#
# Vista en consola
#
class vistaTerminal:

    # Métodos privados

    # Limpiar sesión
    def _clear(self):
        'Limpiar sesión del terminal'
        os.system('cls' if os.name=='nt' else 'clear')
        return("   ")

    # Saludo
    def _saludar(self):
        'Saludo inicial'
        print("\nSaludos, profesor Falken.")
        return

    # Métodos públicos

    # Mostrar cabecera inicial
    def cabecera(self):
        self._clear()
        print("\nSistema de Educación Financiera Escolar de Alborada")
        print("{:-^51}".format(""))
        return

    # Mensaje en pantalla
    def mensaje(self, mensaje):
        print("\n" + mensaje)

    # Pedir contraseña
    def pedirClave(self):
        'Pedir clave Airtable-API'
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

    # Resultado de contraseña
    def responderAcceso(self, esAutorizado):
        "Dar o bloquear acceso al usuario"
        if esAutorizado:
            return 1
        else:
            self.error("Contraseña incorrecta. Proceso terminado.")
            return 0

    # Mostrar menús
    def muestraOpciones(self, opciones):
        'Muestra menús de opciones'
        for linea in opciones.keys():
            if linea == "titulo":
                print("\n" + opciones.get("titulo"))
            else:
                print(opciones.get(linea))
        return opciones

    # Pedir opción de menú
    def eligeOpcion(self, menu):
        "Pide opción del menú validando la entrada"
        entradaValida = False
        eleccion = ""
        while not entradaValida:
            opcionEntrada = input("\nOpción: ").upper()
            # Validar entrada como opción de menú
            # Opciones del menú
            opcionesMenu = [x for x in menu if x != "titulo"]
            # Menú de opciones
            if opcionEntrada in opcionesMenu:
                # Determinar qué opción ha elegido
                eleccion = opcionEntrada
                entradaValida = True
            else:
                self.error("Opción incorrecta.")
                entradaValida = False
                continue
        return eleccion

    # Mostrar error
    def error(self, mensaje):
        print("Error: {}".format(mensaje))
        return

    def pideDatosParticipante(self):
        "Pide datos para crear un participante"
        nombre = ""
        apellido1 = ""
        apellido2 = ""
        while not nombre:
            nombre = input("Introducir nombre: ").upper()
        while not apellido1:
            apellido1 = input("Introducir apellido1: ").upper()
        apellido2 = input("Introduce apellido2: ").upper()
        tipo = ""
        while tipo not in ["E", "C", ""]:
            tipo = input("Selecciona tipo, [E]studiante o [C]omerciante: ")
            if tipo.upper() == "E":
                tipo = "ESTUDIANTE"
            elif tipo.upper() == "C":
                tipo = "COMERCIANTE"
            elif tipo.upper() == "":
                tipo = ""
            else:
                self.error("Opción incorrecta.")
                continue
        esquema = {
            "NOMBRE": nombre,
            "APELLIDO1": apellido1,
            "APELLIDO2": apellido2,
            "TIPO": tipo,
        }
        return esquema

    # Mostrar registro en pantalla
    def mostrarRegistro(self, reg, conf):
        '''Muestra registro con los campos seleccionados'''
        # Preparar alineamientos
        linea = PrettyTable()
        linea.set_style(PLAIN_COLUMNS)
        linea.field_names = conf["campos"]
        for i, ajuste in enumerate(conf["ajuste"]):
            col = conf["campos"][i]
            linea.align[col] = ajuste       
        # Comprobar cada tipo de dato para formato correcto según configuración
        fila = []
        for campo in conf["campos"]:
            columna = reg.reg["fields"].get(campo)
            if not columna:
                fila.append("--")
            elif type(columna) == type(str()):
                fila.append(columna)
            elif type(columna == type(list())):
                if type(columna[0]) == type(float()) or type(columna[0]) == type(int()):
                    fila.append("{0:.2f} €".format(columna[0]))
                elif type(columna[0]) == type(str()):
                    fila.append(columna[0].upper())
        # Columnas
        serie = pd.Series(fila, index=conf["campos"])
        # Filas
        linea.add_row(fila)
        # Determinar orientación del listado
        if conf["orientacion"] == "h":
            print(linea)
        elif conf["orientacion"] == "v":
            print(serie)

    # Mostrar contraseña de un registro
    def mostrarIdRegistro(self, reg):
        "Muestra id del registro como contraseña"
        print("Contraseña del participante: " + reg.id)

    # Mostrar registros de una tabla
    def listaRegistrosEnTabla(self, baseDatos, tabla, conf):
        'Lista de registros en una tabla'
        # Preparar lista
        lista = PrettyTable()
        lista.field_names = conf["campos"]
        # Preparar configuración de lista
        for i, ajuste in enumerate(conf["ajuste"]):
            col = conf["campos"][i]
            lista.align[col] = ajuste       
        lista.set_style(PLAIN_COLUMNS)
        # Recorrer tabla
        for reg in baseDatos:
            fila = []
            for campo in conf["campos"]:
                # Horizontal
                columna = reg.reg["fields"].get(campo)
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
        # Mostrar tabla
        print(lista)

    # Pedir confirmación para borrar registro
    def seguroBorrar(self, nombre):
        "Pide confirmación para borrar un registro"
        respuesta = ""
        while respuesta not in ["S", "N"]:
            respuesta = input(f'¿Seguro que quieres borrar el registro de {nombre}? (S/N): ').upper()
        return respuesta

    # Mostrar lista de personajes
    def muestraListaPersonajes(self, lista):
        "Muestra en pantalla la lista de personajes"
        for reg in lista:
            print(f'{reg["fields"].get("REFERENCIA")}.')

    # Pedir elección de personaje
    def eligeOpcion(self, lista):
        "Elegir el personaje"
        ref = 0
        while (ref < 1 or ref > len(lista)):
            ref = input("\nElige referencia del personaje: ")
            if ref in range(1, len(lista) + 1):
                if lista[ref - 1] == "--":
                    ref = 0
                    self.error("Referencia ya asignada a otro participante.")
        return ref

    # Mostrar lista de cuentas y pedir elección
    def elegirCuenta(self, lista):
        "Muestra lista de cuentas y pide elección"
        numCuentas = []
        for reg in lista:
            numCuentas.append(reg["fields"].get("NÚMERO-CUENTA"))
            print(f'Cuenta número {numCuentas[-1]}, {reg["fields"].get("TIPO-CUENTA")}')
        while cuenta not in numCuentas:
            cuenta = input("\nElige número de cuenta: ")
        return cuenta

    def pedirComercio(self, lista):
        "Pide elegir un comercio de la lista"
        ref = 0
        while (ref < 1 or ref > len(lista)):
            try:
                ref = int(input("Elige referencia del comercio: "))
                if (ref < 1 or ref > len(lista)):
                    ref = 0
                else:
                    if lista[ref - 1]["fields"]["NOMBRE"] == "AYUNTAMIENTO":
                        # No elegible el Ayuntamiento, volver a preguntar
                        ref = 0
            except ValueError:
                # Si responde con una letra, volver a preguntar
                ref = 0
        return ref

    def mostrarReglasComercio(self, reg):
        'Muestra las reglas de un comercio'
        print("\nReglas del comercio:")
        print(reg["fields"].get("REGLAS"))

    def pedirConcepto(self, lista):
        "Pide el producto o servicio del comercio"
        num = 0
        while num not in range(1, len(lista)+1):
            num = int(input("\nElige número de concepto: "))
        return num

    def pedirMedioPago(self):
        "Pide el medio de pago para un movimiento"
        tipo = 0
        while tipo not in ["1", "2"]:
            tipo = input("\nElige medio de pago (1, Talón; 2, Tarjeta): ")
        if tipo == "1":
            medio = "TALÓN"
        else:
            medio = "TARJETA-DÉBITO"
        return medio
    
    def pedirImportes(self, tipoCuenta):
        "Pide importe para las cuentas del Banco Cooperativo"
        importe: float = 0
        while importe == 0:
            if tipoCuenta == 1:
                # Importe extra para reducir la deuda de la tarjeta de crédito
                mensaje = "Importe extra a pagar (mín. 0.01 €): "
            elif tipoCuenta == 2:
                mensaje = "Importe recibido para la jubilación: "
            elif tipoCuenta == 3:
                mensaje = "Importe para el plan de ahorro: "
                try:
                    importe = float(input(mensaje))
                except ValueError:
                    importe = 0
                if importe < 0:
                    importe = 0
        return importe

        
#
# Controlador en consola
#


class controladorTerminal:

    def __init__(self):
        "Preparación del modelo y la vista"
        self.modelo = modelo()
        self.vista = vistaTerminal()

    def _salir(self):
        "Terminar ejecución"
        os._exit(1)

    def _pedirAcceso(self):
        "Pide credenciales para continuar"
        atk = ""
        while not atk:
            atk = self.vista.pedirClave()
        return atk

    def _comprobarClave(self, atk):
        "Comprueba clave para continuar"
        esAutorizado = self.modelo.validarAcceso(atk)
        continuar = self.vista.responderAcceso(esAutorizado)
        if not continuar:
            self._salir()

    def _eligeOpcion(self):
        "Pide opción del menú"
        entradaValida = False
        while not entradaValida:
            try:
                opcion = self.vista.eligeOpcion()
                opcion = str(opcion)
                entradaValida = True
            except ValueError as err:
                self.vista.error("Opción incorrecta.")
            comando = self.modelo.cargaBaseDatos(opcion)
            self.vista.muestraOpciones(comando)

    def _crearParticipante(self, baseDatos):
        "Pide datos y pide la creación de un participante al modelo"
        self.vista.mensaje("Creación de un participante")
        participante = self.vista.pideDatosParticipante()
        yaExiste = self.modelo.yaExiste(baseDatos, participante)
        if not yaExiste:
            self.vista.error("Ya existe ese participante.")
            return 0
        regParticipante = self.modelo.crearParticipante(baseDatos, participante)
        if regParticipante.reg.id:
            reg, conf = self.modelo.prepararImpresionRegParticipante([regParticipante.reg.id])
            if not reg:
                self.vista.error("No se encuentra el registro.")
                self._salir()
            self.vista.mostrarRegistro(reg, conf)
            self.vista.mensaje("Registro creado correctamente.")
            return regParticipante
        else:
            self.vista.error("No se ha podido crear el registro.")
            self._salir()

    def _listaParticipantes(self, baseDatos):
        "Prepara la lista de participantes para mostrar"
        conf, campoOrden = self.modelo.prepararImpresionListaParticipantes()
        tabla = baseDatos[0].tablaParticipantes
        self.vista.listaRegistrosEnTabla(baseDatos, tabla, conf)

    def _buscarParticipante(self, baseDatos):
        "Buscar un participante en la tabla PERSONAS"
        participante = self.vista.pideDatosParticipante()
        nombreCompleto = f'{participante["NOMBRE"]} {participante["APELLIDO1"]}, {participante.get("APELLIDO2")}'
        encontrados = self.modelo._buscarPersona(baseDatos, "NOMBRE COMPLETO", nombreCompleto)
        return encontrados

    def _mostrarParticipante(self, baseDatos):
        "Presentar datos del participante"
        regParticipante, posicion = self._buscarParticipante(baseDatos)
        if regParticipante:
            conf = self.modelo.prepararImpresionRegParticipante()
            self.vista.mostrarRegistro(regParticipante, conf)
        else:
            self.vista.error("No se ha encontrado el participante.")
            self._salir()

    def _modificarParticipante(self, baseDatos):
        "Pedir datos y modificar el participante"
        regParticipante, posicion = self._buscarParticipante(baseDatos)
        if regParticipante:
            self.vista.mensaje("Introducir los nuevos datos. Dejar en blanco los campos que no cambian.")
            participante = self.vista.pideDatosParticipante()
            campos = {}
            # Solo consideramos campos que han sido cumplimentados
            if participante.get("NOMBRE"): campos["NOMBRE"] = participante["NOMBRE"]
            if participante.get("APELLIDO1"): campos["APELLIDO1"] = participante["APELLIDO1"]
            if participante.get("APELLIDO2"): campos["APELLIDO2"] = participante["APELLIDO2"]
            if participante.get("TIPO"): campos["TIPO"] = participante["TIPO"]
            resultado = self.modelo.modificarCampos(campos, regParticipante)
            if resultado:
                self.vista.mensaje("Registro actualizado correctamente.")
            else:
                self.vista.error("No se ha podido actualizar el registro.")
                self._salir()
        else:
            self.vista.error("No se ha encontrado el participante.")
            self._salir()

    def _borrarParticipante(self, baseDatos):
        "Comprobar que es borrable y borrar un participante"
        # Elegir participante
        regParticipante = self._buscarParticipante(baseDatos)
        if regParticipante:
            # Comprobar que no tiene asignado personaje, cuentas, movimientos
            esBorrable = self.modelo._esParticipanteBorrable(regParticipante)
            if esBorrable:
                # Confirmar borrado
                respuesta = self.vista.seguroBorrar(regParticipante[0])
                if respuesta == "S":
                    # Borrar participante
                    esBorrado = self.modelo.borrarRegistroDeTabla(baseDatos, regParticipante)
                    if esBorrado:
                        self.vista.mensaje("Registro borrado correctamente.")
                    else:
                        self.vista.error("No se ha podido borrar el registro.")
                        self._salir()
                else:
                    self.vista.mensaje("Registro no borrado.")
            else:
                self.vista.mensaje("Es necesario borrar primero el personaje asignado.")
        else:
            self.vista.error("No existe el participante.")
            self._salir()

    def _elegirPersonaje(self, tabla):
        "Muestra lista de personajes y pide una elección"
        # Preparar lista de profesiones
        lista = self.modelo._cargarPersonajes(tabla)
        listaProfesiones = self.modelo._prepararListaProfesiones(lista)
        self.vista.muestraListaPersonajes(listaProfesiones)
        opcion = self.vista.eligeOpcion(listaProfesiones)
        regPersonaje = self.modelo._buscarRegistroDeCampoEnTabla(tabla, "REFERENCIA", opcion)
        return regPersonaje
            
    def _asignarPersonaje(self, baseDatos):
        "Asigna o reasigna un personaje a un participante"
        # Elegir participante
        regParticipante = self._buscarParticipante(baseDatos)
        # Comprobar si tiene cuentas u otro personaje
        if regParticipante:
            estado = self.modelo.estadoParticipante(regParticipante)
            if estado["tieneCuentas"]:
                self.vista.error("Antes de asignar un nuevo personaje es necesario eliminar las cuentas del personaje anterior.")
                return
            if estado["tienePersonaje"]:
                profesion = regParticipante[0]["fields"].get("PROFESIÓN")[0]
                self.vista.mensaje("El participante tiene asignado el personaje {0}.".format(profesion))
                respuesta = self.vista.seguroReasignarParticipante()
                if respuesta == "N":
                    self.vista.mensaje("Registro no alterado.")
                    return
            # Sin personaje ni cuentas
            regPersonaje = self._elegirPersonaje(regParticipante[0].tablaPersonajes)
            resultado = self.modelo.asignarRegistroEnlazado(regParticipante[0].tablaPersonas, regParticipante[0], "PERSONAJE", regPersonaje)
            if resultado:
                self.vista.mensaje("Registro actualizado correctamente.")
            else:
                self.vista.error("No ha sido posible actualizar el registro.")
                self._salir()
        else:
            # No existe el participante buscado
            self.vista.error("No existe ese participante.")

    def _borrarPersonaje(self, baseDatos):
        "Elige personaje para desasignarlo al participante, siempre que no tenga cuentas"
        # Elegir participante
        regParticipante = self._buscarParticipante(baseDatos)
        # Comprobar si tiene cuentas u otro personaje
        if regParticipante:
            estado = self.modelo.estadoParticipante(regParticipante)
            if estado["tieneCuentas"]:
                self.vista.error("Antes de borrar el personaje es necesario eliminar sus cuentas.")
                return
            if estado["tienePersonaje"]:
                profesion = regParticipante[0]["fields"].get("PROFESIÓN")[0]
                self.vista.mensaje("El participante tiene asignado el personaje {0}.".format(profesion))
                respuesta = self.vista.seguroBorrar(profesion)
                if respuesta == "N":
                    self.vista.mensaje("Registro no alterado.")
                    return
                else:
                    # Borrar es asignar contenido vacío al campo
                    resultado = self.modelo.asignarRegistroEnlazado(regParticipante[0].tablaPersonas, regParticipante[0], "PERSONAJE", [])
                    if resultado:
                        self.vista.mensaje("Personaje borrado correctamente.")
                        return
                    else:
                        self.vista.error("No se ha podido borrar el personaje.")
                        self._salir()
            else:
                # Sin personaje
                self.vista.error("No tiene personaje asignado.")
        else:
            # No existe el participante buscado
            self.vista.error("No existe ese participante.")

    def _crearCuenta(self, baseDatos):
        "Crear las cuentas de un personaje"
        # Elegir participante
        regParticipante = self._buscarParticipante(baseDatos)[0]
        # Comprobar si tiene personaje y cuentas y crear las cuentas que falten
        resultado = self.modelo.crearCuentas(regParticipante)
        if not resultado:
            # Todas las cuentas están creadas
            self.vista.mensaje("Se han creado todas las cuentas.")
        elif resultado == -1:
            # No hay personaje
            self.vista.error("Antes de crear las cuentas es necesario asignar un personaje.")
        else:
            # Hay cuentas mal creadas (sin tipo de cuenta)
            self.vista.error("Alguna de las cuentas de este personaje no tiene finalidad (corriente, tarjeta, ahorro o jubilación).")

    def _elegirCuenta(self, reg):
        "Muestra lista de cuentas y pide un elección"
        # Preparar lista de cuentas
        lista = self.modelo.listaCuentas(reg)
        numCuenta = self.vista.elegirCuenta(lista)
        regCuenta = self.modelo._buscarRegistroDeCampoEnTabla(reg.tablaCuentas, "NÚMERO-CUENTA", numCuenta)
        return regCuenta

    def _borrarCuenta(self, baseDatos):
        "Borrar una cuenta de un personaje."
        # Elegir participante
        regParticipante = self._buscarParticipante(baseDatos)[0]
        # Elegir cuenta
        regCuenta = self._elegirCuenta(regParticipante)
        # Comprobar si tiene personaje y borrar la cuentas si no tiene movimientos
        resultado = self.modelo.borrarCuenta(regParticipante, regCuenta)
        if not resultado:
            # Cuenta borrada
            self.vista.mensaje("Cuenta borrada correctamente.")
        elif resultado == -1:
            # No hay personaje
            self.vista.error("Antes de borrar las cuentas de un personaje es necesario asignar un personaje.")
        else:
            # Hay movimientos en esta cuenta
            self.vista.error("Antes de borrar esta cuenta es necesario borrar primero todos sus movimientos.")

    def _registrarMovPendientes(self, regParticipante):
        ''' Si hace tiempo que no se han registrado movimientos, puede haber obligaciones y derechos
        periódicos que no se hayan registrado en la tabla MOVIMIENTOS. Comprobar y registrar
        movimientos pendientes.'''
        self.vista.mensaje("Calculando derechos y obligaciones periódicas pendientes de registrar...")
        self.modelo.registrarMovPendientes(regParticipante)

    def _pedirConcepto(self, regParticipante, regComercio):
        "Pedir el producto o servicio del comercio"
        self.vista.mensaje("Reuniendo información de productos y servicios...")
        listaProductos = regComercio["fields"]["PRODUCTOS-SERVICIOS"]
        productos = self.modelo.prepararListaProductos(regParticipante, listaProductos)
        self.vista.mensaje(productos)
        numProducto = self.vista.pedirConcepto(listaProductos)
        regProducto = self.modelo.traerRegistroDeTabla(regParticipante.tablaProdServicios, listaProductos[numProducto - 1])
        return regProducto
    
    def _pedirDatosMovimiento(self, regParticipante):
        "Pedir el concepto y medio de pago"
        listaComercios, lineas = self.modelo.listaComercios(regParticipante)
        self.vista.mensaje(lineas)
        numComercio = self.vista.pedirComercio(listaComercios)
        regComercio = listaComercios[numComercio - 1]
        self.vista.mostrarReglas(regComercio)
        regProducto = self._pedirConcepto(regParticipante, regComercio)
        medio = self.vista.pedirMedioPago()
        return (regComercio, regProducto, medio)

    def _esGestionable(self, regParticipante, regProducto):
        "Comprobar si el movimiento del producto es gestionable esta semana"
        return self.modelo.esGestionable(regParticipante, regProducto)

    def _faltanCuentas(self, tipoCuenta):
        "Mensajes de error porque faltan cuentas por crear"
        if tipoCuenta == -1:
            self.vista.error("Falta crear primero la cuenta de la tarjeta de crédito.")
        elif tipoCuenta == -2:
            self.vista.error("Es necesario crear primero la cuenta de jubilación.")
        elif tipoCuenta == -3:
            self.vista.error("Es necesario crear primero la cuenta del plan de ahorro.")
    
    def _nuevoMovimiento(self, baseDatos):
        "Registrar un nuevo movimiento en una cuenta."
        # Elegir participante
        regParticipante = self._buscarParticipante(baseDatos)[0]
        # Elegir cuenta
        regCuenta = self._elegirCuenta(regParticipante)
        # Registrar movimientos periódicos pendientes (ingresos y gastos)
        self._registrarMovPendientes(regParticipante)
        gestionesGrandes = regParticipante.listaRegCuentas[0].get("gestionabilidad").get("GRANDE")
        gestionesMedianas = regParticipante.listaRegCuentas[0].get("gestionabilidad").get("MEDIANA")
        gesionesPeq = regParticipante.listaRegCuentas[0].get("gestionabilidad").get("PEQUEÑA")
        self.vista.mensaje(f'En esta semana te quedan {gestionesGrandes} gestión o gestiones grande(s), {gestionesMedianas} mediana(s) y {gesionesPeq} pequeña(s).')
        if (
            gestionesGrandes <= 0
            and gestionesMedianas <= 0
            and gesionesPeq <= 0
        ):
            self.error("Has consumido el número máximo de movimientos esta semana.")
            return
        # Pedir concepto y medio de pago
        regComercio, regProducto, medio = self._pedirDatosMovimiento(regParticipante)
        # Comprobar que el movimiento no excede del máximo para esta semana
        if not self._esGestionable(regParticipante, regProducto):
            self.vista.error("Excedido el número máximo semanal de movimientos.")
            return
        # Comprobar que la compra no cause descubierto en la cuenta, excepto si es mala suerte
        comercio = regComercio["fields"].get("NOMBRE")
        if comercio != "DEDO DEL DESTINO":
            if not self.modelo.haySaldoSuficiente(regParticipante, regProducto):
                self.vista.error("No hay saldo suficiente en la cuenta corriente para hacer el pago.")
                return
        # Gestión del Banco Cooperativo
        nombreProducto = regProducto["fields"].get("NOMBRE")
        if (nombreProducto in ["PAGO DEUDA TARJETA", "APORTACIÓN CUENTA JUBILACIÓN", "PLAN AHORRO"]):
            resultado = self.modelo.gestionBanco(regParticipante, nombreProducto)
            if resultado < 0:
                # Faltan cuentas
                self._faltanCuentas(resultado)
                return
            elif resultado > 0:
                # Importes para tarjeta, jubilación o ahorro
                importe = 0
                if resultado == 1:
                    importe = regParticipante.reg["fields"].get("PAGO-MÍNIMO-TARJETA-CRÉDITO")
                    self.vista.mensaje("Importe mínimo a pagar: {0:.2f} €.".format(importe))
                pago = importe + self.vista.pedirImportes(resultado)

        # Preparar transacción
        if regCuenta["fields"].get("TIPO-CUENTA") == "TARJETA":
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
        
    
    def comienza(self):
        "Bucle principal"

        # Mostrar cabecera inicial
        self.vista.cabecera()

        # Pedir acceso
        atk = self._pedirAcceso()

        # Comprobar clave
        self._comprobarClave(atk)

        # Cargar menús y base de datos
        catalogo = self.modelo.cargaMenus()
        tablas, baseDatos = self.modelo.cargaBaseDatos()
        
        # Comprobar si se ha cargado correctamente
        if not tablas:
            self.vista.error("No se ha podido cargar la base de datos.")
            self._salir()

        # Mostrar menú principal
        menu = self.vista.muestraOpciones(catalogo.get("completo"))
        regParticipante = []
        while True:
            # Pedir opción de menú
            eleccion = self.vista.eligeOpcion(menu)
            # Determinar procedimiento elegido
            if eleccion == '0':
                # Validar salida y terminar guión
                esAutorizado = self.modelo.validarAcceso(atk)
                continuar = self.vista.responderAcceso(esAutorizado)
                if continuar: self._salir()
                continue
            elif eleccion == '1':
                self._comprobarClave()
                regParticipante = self._crearParticipante(baseDatos)
                if regParticipante.reg.id:
                    self.vista.mensaje("Contraseña del participante: " + regParticipante.reg.id)
                continue
            elif eleccion == '2':
                self._listaParticipantes(baseDatos)
                continue
            elif eleccion == '3':
                self._mostrarParticipante(baseDatos)
                continue
            elif eleccion == "4":
                self._modificarParticipante(baseDatos)
                continue
            elif eleccion == "5":
                self._borrarParticipante(baseDatos)
                continue
            elif eleccion == "6":
                self._asignarPersonaje(baseDatos)
                continue
            elif eleccion == "7":
                self._borrarPersonaje(baseDatos)
                continue
            elif eleccion == '8':
                self._crearCuenta(baseDatos)
                continue
            elif eleccion == "9":
                self._borrarCuenta(baseDatos)
                continue
            elif eleccion == "A":
                self._nuevoMovimiento(baseDatos)
                continue
            elif eleccion == "B":
                self._borrarMovimiento(baseDatos)
                continue
            elif eleccion == "C":
                self._modificarMovimiento(baseDatos)
                continue
            elif eleccion == "D":
                self._listaMovimientos(baseDatos)
                continue
            elif eleccion == "E":
                self._borrarTodosMovimientos(baseDatos)
                continue

#
# Bucle principal
#
def main():
    controlador = controladorTerminal()
    while True:
        controlador.comienza()

if __name__ == "__main__":
    main()
