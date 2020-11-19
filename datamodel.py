from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import Sequence

import datetime
import time

db = SQLAlchemy()

#Tabla de Paises
class Pais(db.Model):
    __tablename__ = 'pais'

    idPais = db.Column(db.Integer, Sequence('idpais_seq'), primary_key=True)
    nombrePais = db.Column(db.String(200), nullable=False)


#Tabla de Ciudades
class Ciudad(db.Model):
    __tablename__ = 'ciudad'

    idCiudad = db.Column(db.Integer, Sequence('idciudad_seq'), primary_key=True)
    nombreCiudad = db.Column(db.String(200))
    paisId = db.Column(db.Integer, db.ForeignKey('pais.idPais'), nullable=False)
    PaisCiu = db.relationship("Pais", lazy=True)


#Tabla de Usuario
class Usuario(db.Model):
    __tablename__ = 'usuario'

    idUsuario = db.Column(db.Integer, Sequence('idusuario_seq'), primary_key=True)
    nickName = db.Column(db.String(50), nullable=False, unique=True)
    celular = db.Column(db.String(20), unique=True) # celular
    pwd = db.Column(db.String(256), nullable=False)
    paisIndic = db.Column(db.Integer, default=57) #Indicativo del pais
    email = db.Column(db.String(100), unique=True, nullable=False)
    nombres = db.Column(db.String(100))
    apellidos = db.Column(db.String(100))
    edad = db.Column(db.Integer, default=0)
    fechanac = db.Column(db.DateTime)
    genero = db.Column(db.Integer) #0: M, 1: F, 2: Otro, 3: No dar info
    activo = db.Column(db.Integer, default=0) #0 Inactivo, #1 Activo
    sancionado = db.Column(db.Integer, default=0)  #0 No, #1 Si - Si un usuario fue sancionado o no por su conducta o por intentar timar
    aceptater = db.Column(db.Integer, default=0)  #0 No, #1 Si - Acepta terminos y condiciones: TOOS DEBERIA ESTAR EN SI
    recibenot = db.Column(db.Integer, default=0) #0: No #1: Si - Recibe notificaciones
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)

#Tabla de Foto Usuario: Almacena todas las fotografias de perfil que el usuario cambie.
#Solo hay una activa=1 a la vez, todas las "anteriores" estarán activa = 0
class FotoUsuario(db.Model):
    __tablename__ = 'fotousuario'

    idFotousuario = db.Column(db.Integer, Sequence('idfotousuario_seq'), primary_key=True)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    tipo = db.Column(db.Integer, default=57) #tipo: 1: Perfil ...despues podríamos usarlas para otros imagenes
    foto = db.Column(db.LargeBinary, nullable=False)
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    activa = db.Column(db.Integer, default=1, nullable=False)  #0 No, #1 Si
    UsrFot = db.relationship("Usuario", lazy=True)

class BusquedaUsuario(db.Model):
    __tablename__ = 'busquedausuario'

    idBusquedausuario = db.Column(db.Integer, Sequence('idbusquedausuario_seq'), primary_key=True)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    busqueda = db.Column(db.String(100), nullable=False) #string de busqueda
    resultados = db.Column(db.Integer, nullable=False)
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrBus = db.relationship("Usuario", lazy=True)

#Registra los cambios de nombre, telefono, apellidos, celular.
#Cada vez que el usuario cambia se genera registro con los datos anteriores
class CambioUsuario(db.Model):
    __tablename__ = 'cambiosusuario'

    idCamusuario = db.Column(db.Integer, Sequence('idcamusuario_seq'), primary_key=True)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    nickName = db.Column(db.String(100))
    nombres = db.Column(db.String(100))
    apellidos = db.Column(db.String(100))
    celular = db.Column(db.String(100))
    email = db.Column(db.String(100))
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrCam = db.relationship("Usuario", lazy=True)

#Cada vez que el usuario abre una sesión se almacena la dirección IP
class ConexionUsuario(db.Model):
    __tablename__ = 'conexionusuario'

    idConxusuario = db.Column(db.Integer, Sequence('idconxusuario_seq'), primary_key=True)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    ipaddr = db.Column(db.String(128), nullable=False)
    tipo = db.Column(db.String(10), nullable=False, default="LOGIN")
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrCon = db.relationship("Usuario", lazy=True)

#El usuario puede tener varias direcciones a la vez, esta tabla las mantiene.
#por trazabilidad, el usuario puede "borrar" direcciones, sin embargo no se borran realmente,
#sino se inactivan y no se muestran más al usuario.
class LugarUsuario(db.Model):
    __tablename__ = 'lugarusuario'

    idLugar = db.Column(db.Integer, Sequence('idlugarusuario_seq'), primary_key=True)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    ciudadId = db.Column(db.Integer, db.ForeignKey('ciudad.idCiudad'), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    complem1 = db.Column(db.String(100))
    complem2 = db.Column(db.String(100))
    complem3 = db.Column(db.String(100))
    zipcode =  db.Column(db.String(20))
    activa = db.Column(db.Integer, default=1)  #0 No, #1 Si -- Campo de borrado lógico
    principal = db.Column(db.Integer, default=0)  #0 No, #1 Si
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrLug = db.relationship("Usuario", lazy=True)
    CiuLug = db.relationship("Ciudad", lazy=True)

#Marcas de fabricantes de consolas y VJ
class Marca(db.Model):
    __tablename__ = 'marca'

    idMarca = db.Column(db.Integer, Sequence('idmarca_seq'), primary_key=True)
    nombre =  db.Column(db.String(100), nullable=False)
    comun =  db.Column(db.String(100))
    urlresena =  db.Column(db.String(500))
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)

#lista de las consolas que manejemos
class Consola(db.Model):
    __tablename__ = 'consola'

    idConsola = db.Column(db.Integer, Sequence('idconsola_seq'), primary_key=True)
    marcaId = db.Column(db.Integer, db.ForeignKey('marca.idMarca'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(100))
    anio = db.Column(db.String(10))
    urlresena =  db.Column(db.String(500))
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    ConsMarc = db.relationship("Marca", lazy=True)

#Tabla de clasificación de los videojuegos. Indica en que cateptía de puntaje se
# encuentra cada uno de ellos
class Clasificacion(db.Model):
    __tablename__ = 'clasificacion'

    idClasifica = db.Column(db.Integer, Sequence('idclasif_seq'), primary_key=True)
    clase = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(100))
    valorPuntos = db.Column(db.String(10))

#Tabla con los nombres de todos los Videojuegos
class VideoJuego(db.Model):
    __tablename__ = 'videojuego'

    idVj = db.Column(db.Integer, Sequence('idvj_seq'), primary_key=True)
    clasifId = db.Column(db.Integer, db.ForeignKey('clasificacion.idClasifica'), nullable=True)
    consolaId = db.Column(db.Integer, db.ForeignKey('consola.idConsola'), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    version = db.Column(db.String(100))
    complementosvj = db.Column(db.String(200))
    urlresena = db.Column(db.String(500))
    popularidad = db.Column(db.Integer, default=0)
    obs = db.Column(db.String(500))
    genero = db.Column(db.String(500))
    imagen = db.Column(db.String(500))
    anioPublica = db.Column(db.String(10))
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    ClasiVJ = db.relationship("Clasificacion", lazy=True)
    ConsVJ = db.relationship("Consola", lazy=True)

#Contiene los "ejemplares" de cada videojuego que los usuarios cargan y negocian en el sistema
class EjeUsuario(db.Model):
    __tablename__ = 'ejeusuario'

    idEjeUsuario = db.Column(db.Integer, Sequence('idejeusuario_seq'), primary_key=True)
    usuarioIdAct = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    vjId = db.Column(db.Integer, db.ForeignKey('videojuego.idVj'), nullable=False)
    comentario = db.Column(db.String(500)) #Manipulable poe el dueño actual de un VJ
    estado = db.Column(db.Integer, default=1)  #1 - 10 Estado físico del VJ
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    #Publicado 1: S - 0: N -- Ejemplar que está dispobible para los demás
    publicado = db.Column(db.Integer, default=1)
    #Bloqueado 1: S - 0: N - Se bloquea mientras está en una transacción (Solo cuando
    #ya fue aceptado por los dos y no se ha finalizado la transacción
    bloqueado = db.Column(db.Integer, default=0)
    #Cuarentena 1: S - 0: N - Se pone en cuarentena, mientras se crea el videojuego en caso
    #de que no exista y se haya creado
    cuarentena = db.Column(db.Integer, default=0)
    #Comprometido 1: S - 0: N - Está comprometido cuando el usuario lo ingresa y recibe una promoción
    # ...no se puede despublicar, pero si editar...aparece en los publicados y en la oferta
    comprometido = db.Column(db.Integer, default=0)
    valor = db.Column(db.Float, default=1)  #Valor en puntos o barts, heredados de la tabla VJ en cada momento, pensando en la valorización / desvalorización
    UsrEjeU = db.relationship("Usuario", lazy=True)
    UsrEjeU = db.relationship("VideoJuego", lazy=True)

#Tabla de Foto Ejemplar Usuario: Almacena todas las fotografias de un ejemplar->cada usuario debe cargar una sola fotografía del videojuego
#Todas están activas, pero el registro de EjeUsuario, muestra la que corresponde a cada usuario
class FotoEjeUsuario(db.Model):
    __tablename__ = 'fotoejeusuario'

    idFotoejeusuario = db.Column(db.Integer, Sequence('idfotoejeusuario_seq'), primary_key=True)
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), nullable=False)
    foto = db.Column(db.LargeBinary, nullable=False)
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    activa = db.Column(db.Integer, default=1, nullable=False)  #0 No, #1 Si: Por ahora todas las imagenes están activas, pero solo se ve la del Ejeusuario Actual
    UsrFot = db.relationship("EjeUsuario", lazy=True)

#Tabla de trazabilidad de EjemplarUsuario: Cada vez que se modifica ejemplarUsuario,
#se genera el registro con la información anterior. Aplica solo cuando cambia de dueño por transacción
class TraceEjemplar(db.Model):
    __tablename__ = 'traceejemplar'

    idTrace = db.Column(db.Integer, Sequence('idtrace_seq'), primary_key=True)
    vjId = db.Column(db.Integer, db.ForeignKey('videojuego.idVj'), nullable=False)
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), nullable=False)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    comentario = db.Column(db.String(500))
    estado = db.Column(db.Integer, default=1)  #1 - 10
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    valor = db.Column(db.Float, default=1)  #Valor en puntos o barts
    VJTraceE = db.relationship("VideoJuego", lazy=True)
    UsrTraceE = db.relationship("Usuario", lazy=True)
    EjeUTraceE = db.relationship("EjeUsuario", lazy=True)

#Tabla donde se registra una solicitud: Cada vez que un usuario hace clic en "Quiero este juego",
#se crea un registro en transacción con los datos actuales del trato.
#Al crear este registro, tambien se crean registros en simultáneo para detalle transacción,
#detalle valor, QyA. La transacción se va actualizando cuando DetalleTransaccion registra acciones, aqui actualiza el estadoTrx
class Transaccion(db.Model):
    __tablename__ = 'transaccion'

    idTrx = db.Column(db.Integer, Sequence('idtrx_seq'), primary_key=True)
    usuarioIdSolic = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False) #Usuario Solicita VJ
    usuarioIdDueno = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False) #Usuario Dueño VJ
    vjId = db.Column(db.Integer, db.ForeignKey('videojuego.idVj'), nullable=False) # referencia Videojuego
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), nullable=False) # referencia ejemplar
    estado = db.Column(db.Integer, default=1)  #1 - 10
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    valor = db.Column(db.Float, default=1)  #Valor en puntos o barts
    estadoTrx = db.Column(db.Integer, default=1)  #0: Cancelada, 1: Activa-vigente, 2: Finalizada correctamente
    UsrSolicTrx = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdSolic])
    UsrDuenoTrx = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdDueno])
    VJTrx = db.relationship("VideoJuego", lazy=True)
    EjeUTrx = db.relationship("EjeUsuario", lazy=True)

#Cuando se acepta una transacción, el sistema selecciona la dirección que el usuario
#tenga configurada, o le permite configurar una, esta se almacena el LugarUsuario y en el
#detalleLugar de cada transacción
class DetalleLugar(db.Model):
    __tablename__ = 'detallelugar'

    idDetTrx = db.Column(db.Integer, Sequence('iddettrx_seq'), primary_key=True)
    trxId = db.Column(db.Integer, db.ForeignKey('transaccion.idTrx'), nullable=False)
    ciudadIdDueno = db.Column(db.Integer, db.ForeignKey('ciudad.idCiudad'), nullable=False) #Dirección del dueño: Origen
    direccionDueno = db.Column(db.String(200), nullable=False)
    complem1Dueno = db.Column(db.String(100))
    complem2Dueno = db.Column(db.String(100))
    complem3Dueno = db.Column(db.String(100))
    zipcodeDueno =  db.Column(db.String(20))
    ciudadIdSolic = db.Column(db.Integer, db.ForeignKey('ciudad.idCiudad'), nullable=False) #Dirección del solicitante: Desino
    direccionSolic = db.Column(db.String(200), nullable=False)
    complem1Solic = db.Column(db.String(100))
    complem2Solic = db.Column(db.String(100))
    complem3Solic = db.Column(db.String(100))
    zipcodeSolic =  db.Column(db.String(20))
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    CiuDetLugS = db.relationship("Ciudad", lazy=True, foreign_keys=[ciudadIdSolic])
    CiuDetLugD = db.relationship("Ciudad", lazy=True, foreign_keys=[ciudadIdDueno])
    TrxDetLug = db.relationship("Transaccion", lazy=True)

#Define una promoción en el sistema
class Promo(db.Model):
    __tablename__ = 'promo'

    idPromo = db.Column(db.Integer, Sequence('idpromo_seq'), primary_key=True)
    descripcion = db.Column(db.String(300), nullable=False) #descripcion de la promoción
    multiplicador = db.Column(db.Integer, default=1)  #Multiplicador de puntos en una promocion
    puntos = db.Column(db.Integer, default=1)  #Cantidad de puntos en una promocion
    aplicasobre = db.Column(db.String(2), default="IC")  #RG: Registro, IC: Intercambio, EV: Entrega VJ, RS: Reseña, CF: Califica
    activa = db.Column(db.Integer, default=0)  #0: inactiva 1: activa
    fechainicia = db.Column(db.DateTime, default=datetime.datetime.now) #Fecha de inicio de la promocion
    fechafinal = db.Column(db.DateTime, default=datetime.datetime.now) #Fecha de fin de la promocion
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)

#Contiene el detalla de la transacción...aquí se deben registrar las acciones:
#Aceptar trato = 1, Enviar = 2, Recibir = 3, Calificar = 4 (Un registro para cada usuario)
#Con esta tabla se actualiza el estado de la transacción y se indica se fue exitoso o no, o el estado actual
class DetalleTrx(db.Model):
    __tablename__ = 'detalletrx'

    idDetTrx = db.Column(db.Integer, Sequence('iddettrx_seq'), primary_key=True)
    trxId = db.Column(db.Integer, db.ForeignKey('transaccion.idTrx'), nullable=False)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    accion = db.Column(db.Integer, default=1)  #1: Solicita, 2: Acepta Solicitud, 3: Entrega, 4: Recibe, 5: Califica
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrDetTrx = db.relationship("Usuario", lazy=True)
    TrxDetTrx = db.relationship("Transaccion", lazy=True)

#Registra las calificaciones que un usuario efectúa en una transacción. Debe haber
#2 registros por transacción, uno para cada usuario
class CalificaTrx(db.Model):
    __tablename__ = 'calificatrx'

    idCalTrx = db.Column(db.Integer, Sequence('idcaltrx_seq'), primary_key=True)
    trxId = db.Column(db.Integer, db.ForeignKey('transaccion.idTrx'), nullable=False) #referencia a la transacción
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False) #Usuario que califica
    usuarioIdCal = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False) #Usuario calificado
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), nullable=False) #ejemplar calificado
    califUsuario = db.Column(db.Integer, default=1)  #Calificación usuario
    obsUsuario = db.Column(db.String(300), nullable=True) #Observacion calificacion usuario
    tagsMejoraUsuario = db.Column(db.String(300), nullable=True) #Tags de características buenas o malas que apoyan calificacion
    califEjemplar = db.Column(db.Integer, default=1)  #Calificación ejemplar
    obsEjemplar = db.Column(db.String(300), nullable=True) #Observacion calificacion ejemplar
    tagsMejoraEjemplar = db.Column(db.String(300), nullable=True) #Tags de características buenas o malas que apoyan calificacion
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrCalif = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioId])
    UsrCaldo = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdCal])
    TrxCalif = db.relationship("Transaccion", lazy=True)
    EjeUCalif = db.relationship("EjeUsuario", lazy=True)

#Almacena la información de puntos de la transacción
#Debe existir un detalle de valor para cada uno de los usuarios que participan en el trato
class DetalleValor(db.Model):
    __tablename__ = 'detallevalor'

    idDetVal = db.Column(db.Integer, Sequence('iddetval_seq'), primary_key=True)
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), nullable=False)
    trxId = db.Column(db.Integer, db.ForeignKey('transaccion.idTrx'), nullable=False)
    promoId = db.Column(db.Integer, db.ForeignKey('promo.idPromo'), nullable=False)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=True)
    tipo = db.Column(db.Integer, default=1)  # Cambio, otros
    vigente = db.Column(db.Integer, default=1)  # 1: S - 0: N
    valorPaga = db.Column(db.Float, default=0)  # Valor que paga por la transacción
    valorCobra = db.Column(db.Float, default=0)  # Valor que cobra por la transacción
    multiplicador = db.Column(db.Float, default=1)  # Cuando haya promoción, los puntos de la transacción se multiplican, aqui se registr por cuanto fueron multiplicados lo que están registrados
    comentario = db.Column(db.String(100), nullable=True) #Comentario
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    PromoDetVal = db.relationship("Promo", lazy=True)
    UsrDetVal = db.relationship("Usuario", lazy=True)
    EjeUDetVal = db.relationship("EjeUsuario", lazy=True)
    TransDetVal = db.relationship("Transaccion", lazy=True)

#Almacena la información de puntos de la transacción
#Debe existir un detalle de valor para cada uno de los usuarios que participan en el trato
class DetalleValorOtros(db.Model):
    __tablename__ = 'detallevalorotros'

    idDetValOtr = db.Column(db.Integer, Sequence('iddetvalotr_seq'), primary_key=True)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=True)
    promoId = db.Column(db.Integer, db.ForeignKey('promo.idPromo'), nullable=False)
    tipo = db.Column(db.Integer, default=1)  # Promocion, por entregar un juego, por reseñar, etc...
    valorPaga = db.Column(db.Float, default=0)  # Valor que paga por la transacción
    valorCobra = db.Column(db.Float, default=0)  # Valor que cobra por la transacción
    multiplicador = db.Column(db.Float, default=1)  # Cuando haya promoción, los puntos de la transacción se multiplican, aqui se registr por cuanto fueron multiplicados lo que están registrados
    comentario = db.Column(db.String(100), nullable=True) #Comentario
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    PromoDetVal = db.relationship("Promo", lazy=True)
    UsrDetVal = db.relationship("Usuario", lazy=True)

#Preguntas y respuestas de una transacción. Cuando la transacción es creada por el usuario que solicita el VJ,
# el sistema crea un registro de solicitud con un mensaje para que inicie la conversacion.
#El mensaje va del solicitante al dueño del VJ. Es una tabla recursiva,
# así que se encadena la secuencia por el idQyA e idPadre. El primer registro va con idPadre = NULL
class QyA(db.Model):
    __tablename__ = 'qya'

    idQyA = db.Column(db.Integer, Sequence('idqya_seq'), primary_key=True)
    idPadre = db.Column(db.Integer, db.ForeignKey('qya.idQyA'), nullable=True) #id del registro que antecede. NULL para el primero
    tipo = db.Column(db.Integer, default=0)  # 0: Question-pregunta - 1: Answer-respuesta
    trxId = db.Column(db.Integer, db.ForeignKey('transaccion.idTrx'), nullable=False)  #referencia a la transacción
    usuarioIdDueno = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False) #Usuario dueño
    usuarioIdSolic = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False) #Usuario solicitante
    usuarioIdMsg = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)#usuario que emite el mensaje
    vjId = db.Column(db.Integer, db.ForeignKey('videojuego.idVj'), nullable=False)#referencia al videojuego
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), nullable=False)#referencia al ejemplar
    PregResp = db.Column(db.String(1500), nullable=False)#Lo que pregunta / responde...el mensaje
    leido = db.Column(db.Integer, default=0)  # 0: No leido - 1: Leido
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now) #Fecha del mensaje automática
    QyAPadre = db.relationship("QyA", lazy=True)
    UsrQyAD = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdDueno])
    UsrQyAS = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdSolic])
    UsrQyA = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdMsg])
    TrxQyA = db.relationship("Transaccion", lazy=True)
    VJQyA = db.relationship("VideoJuego", lazy=True)
    EjeQyA = db.relationship("EjeUsuario", lazy=True)

#Tabla donde se registrn saldos de resumen para el usuario, estos se muestran en la preferencias de usuario.
#Debe haber un script que revise y sincronice (pyuede ser cada vez que se actualice o diario en un proceo batch
class Saldos(db.Model):
    __tablename__ = 'saldos'

    idSaldos = db.Column(db.Integer, Sequence('idsaldos_seq'), primary_key=True)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), unique=True)
    valorPagado = db.Column(db.Float, default=0)  # Valor total que ha pagado
    ValorCobrado = db.Column(db.Float, default=0)  # Valor total que ha cobrado
    Saldos = db.Column(db.Float, default=0)  # Valor total que tiene actualmente en puntos
    ejeRecibidos = db.Column(db.Integer, default=0)  #Cantidad Ejemplares recibidos
    ejeEntregados = db.Column(db.Integer, default=0)  #Cantidad Ejemplares recibidos
    ejePublicados = db.Column(db.Integer, default=0)  #Cantidad Ejemplares recibidos
    OtrAcciones = db.Column(db.Integer, default=0)  #Otras acciones por las que se genera saldos...
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrSaldos = db.relationship("Usuario", lazy=True)

#Información que se llenará cuando tengamos definida una blockchain
class Cadena(db.Model):
    __tablename__ = 'cadena'

    idCadena = db.Column(db.Integer, Sequence('idcadena_seq'), primary_key=True)
    PHash = db.Column(db.String(64), nullable=True)
    CHash = db.Column(db.String(64), nullable=False)
    Time = db.Column(db.String(64),  default=time.localtime())
    usuarioIdSolic = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), unique=True)
    usuarioIdDueno = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), unique=True)
    vjId = db.Column(db.Integer, db.ForeignKey('videojuego.idVj'), unique=True)
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), unique=True)
    trxId = db.Column(db.Integer, db.ForeignKey('transaccion.idTrx'), unique=True)
    fechaEntrega = db.Column(db.DateTime, default=datetime.datetime.now)
    valor = db.Column(db.Float, default=0)
    UsrCadSol = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdSolic])
    UsrCadDue = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdDueno])
    VJCad = db.relationship("VideoJuego", lazy=True)
    EjeUCad = db.relationship("EjeUsuario", lazy=True)
    TrxCad = db.relationship("Transaccion", lazy=True)
