from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import Sequence

import datetime
import time

db = SQLAlchemy()


class Pais(db.Model):
    __tablename__ = 'pais'

    idPais = db.Column(db.Integer, Sequence('idpais_seq'), primary_key=True)
    nombrePais = db.Column(db.String(200), nullable=False)


class Ciudad(db.Model):
    __tablename__ = 'ciudad'

    idCiudad = db.Column(db.Integer, Sequence('idciudad_seq'), primary_key=True)
    nombreCiudad = db.Column(db.String(200))
    paisId = db.Column(db.Integer, db.ForeignKey('pais.idPais'), nullable=False)
    PaisCiu = db.relationship("Pais", lazy=True)


class Usuario(db.Model):
    __tablename__ = 'usuario'

    idUsuario = db.Column(db.Integer, Sequence('idusuario_seq'), primary_key=True)
    nickName = db.Column(db.String(50), nullable=False, unique=True)
    celular = db.Column(db.Integer, unique=True)
    pwd = db.Column(db.String(256), nullable=False)
    paisIndic = db.Column(db.Integer, default=57) #Indicativo del pais
    email = db.Column(db.String(100), unique=True, nullable=False)
    nombres = db.Column(db.String(100))
    apellidos = db.Column(db.String(100))
    edad = db.Column(db.Integer, default=0)
    fechanac = db.Column(db.DateTime)
    genero = db.Column(db.Integer) #0: M, 1: F, 2: Otro, 3: No dar info
    activo = db.Column(db.Integer, default=0) #0 Inactivo, #1 Activo
    sancionado = db.Column(db.Integer, default=0)  #0 No, #1 Si
    recibenot = db.Column(db.Integer, default=0) #0: No #1: Si
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)


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
    activa = db.Column(db.Integer, default=1)  #0 No, #1 Si
    principal = db.Column(db.Integer, default=0)  #0 No, #1 Si
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrLug = db.relationship("Usuario", lazy=True)
    CiuLug = db.relationship("Ciudad", lazy=True)


class Marca(db.Model):
    __tablename__ = 'marca'

    idMarca = db.Column(db.Integer, Sequence('idmarca_seq'), primary_key=True)
    nombre =  db.Column(db.String(100), nullable=False)
    comun =  db.Column(db.String(100))
    urlresena =  db.Column(db.String(500))
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)


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


class Clasificacion(db.Model):
    __tablename__ = 'clasificacion'

    idClasifica = db.Column(db.Integer, Sequence('idclasif_seq'), primary_key=True)
    clase = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(100))
    valor = db.Column(db.String(10))


class VideoJuego(db.Model):
    __tablename__ = 'videojuego'

    idVj = db.Column(db.Integer, Sequence('idvj_seq'), primary_key=True)
    usuarioIdAct = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    clasifId = db.Column(db.Integer, db.ForeignKey('clasificacion.idClasifica'), nullable=False)
    consolaId = db.Column(db.Integer, db.ForeignKey('consola.idConsola'), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    imagen = db.Column(db.String(200), nullable=False)
    version = db.Column(db.String(100))
    complementosvj = db.Column(db.String(200))
    urlresena =  db.Column(db.String(500))
    anioPublica = db.Column(db.String(10))
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsuVJ = db.relationship("Usuario", lazy=True)
    ClasiVJ = db.relationship("Clasificacion", lazy=True)
    ConsVJ = db.relationship("Consola", lazy=True)


class EjeUsuario(db.Model):
    __tablename__ = 'ejeusuario'

    idEjeUsuario = db.Column(db.Integer, Sequence('idejeusuario_seq'), primary_key=True)
    usuarioIdAct = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    vjId = db.Column(db.Integer, db.ForeignKey('videojuego.idVj'), nullable=False)
    comentario = db.Column(db.String(500))
    estado = db.Column(db.Integer, default=1)  #1 - 10
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    publicado = db.Column(db.Integer, default=1)  #1: S - 0: N
    bloqueado = db.Column(db.Integer, default=1)  #1: S - 0: N
    valor = db.Column(db.Float, default=1)  #Valor en puntos o barts
    UsrEjeU = db.relationship("Usuario", lazy=True)
    UsrEjeU = db.relationship("VideoJuego", lazy=True)


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


class Transaccion(db.Model):
    __tablename__ = 'transaccion'

    idTrx = db.Column(db.Integer, Sequence('idtrx_seq'), primary_key=True)
    usuarioIdOrig = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    usuarioIdDest = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    vjId = db.Column(db.Integer, db.ForeignKey('videojuego.idVj'), nullable=False)
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), nullable=False)
    estado = db.Column(db.Integer, default=1)  #1 - 10
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    valor = db.Column(db.Float, default=1)  #Valor en puntos o barts
    UsrOrigTrx = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdOrig])
    UsrDestTrx = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdDest])
    VJTrx = db.relationship("VideoJuego", lazy=True)
    EjeUTrx = db.relationship("EjeUsuario", lazy=True)


class DetalleTrx(db.Model):
    __tablename__ = 'detalletrx'

    idDetTrx = db.Column(db.Integer, Sequence('iddettrx_seq'), primary_key=True)
    trxId = db.Column(db.Integer, db.ForeignKey('transaccion.idTrx'), nullable=False)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    accion = db.Column(db.Integer, default=1)  #Identificar las acciones
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrDetTrx = db.relationship("Usuario", lazy=True)
    TrxDetTrx = db.relationship("Transaccion", lazy=True)


class DetalleValor(db.Model):
    __tablename__ = 'detallevalor'

    idDetVal = db.Column(db.Integer, Sequence('iddetval_seq'), primary_key=True)
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), nullable=False)
    trxId = db.Column(db.Integer, db.ForeignKey('transaccion.idTrx'), nullable=False)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    tipo = db.Column(db.Integer, default=1)  # Cambio, otros
    vigente = db.Column(db.Integer, default=1)  # 1: S - 0: N
    egreso = db.Column(db.Float, default=0)  # Valor en contra
    ingreso = db.Column(db.Float, default=0)  # Valor a favor
    realegreso = db.Column(db.Float, default=0)  # Valor en contra materializado
    realingreso = db.Column(db.Float, default=0)  # Valor a favor materializado
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrDetVal = db.relationship("Usuario", lazy=True)
    EjeUDetVal = db.relationship("EjeUsuario", lazy=True)
    TransDetVal = db.relationship("Transaccion", lazy=True)


class QyA(db.Model): ##Preguntas y respuestas
    __tablename__ = 'qya'

    idQyA = db.Column(db.Integer, Sequence('idqya_seq'), primary_key=True)
    idPadre = db.Column(db.Integer, db.ForeignKey('qya.idQyA'), nullable=True)
    tipo = db.Column(db.Integer, default=0)  # 0: Question-pregunta - 1: Answer-respuesta
    trxId = db.Column(db.Integer, db.ForeignKey('transaccion.idTrx'), nullable=False)
    usuarioIdQ = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    usuarioIdA = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    vjId = db.Column(db.Integer, db.ForeignKey('videojuego.idVj'), nullable=False)
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), nullable=False)
    PregResp = db.Column(db.String(500), nullable=False)
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    QyAPadre = db.relationship("QyA", lazy=True)
    UsrQyAQ = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdQ])
    UsrQyAA = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdA])
    UsrQyA = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioId])
    TrxQyA = db.relationship("Transaccion", lazy=True)
    VJQyA = db.relationship("VideoJuego", lazy=True)
    EjeQyA = db.relationship("EjeUsuario", lazy=True)



class Saldos(db.Model):
    __tablename__ = 'saldos'

    idSaldos = db.Column(db.Integer, Sequence('idsaldos_seq'), primary_key=True)
    usuarioId = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), unique=True)
    egreso = db.Column(db.Float, default=0)  # Valor en contra
    ingreso = db.Column(db.Float, default=0)  # Valor a favor
    realegreso = db.Column(db.Float, default=0)  # Valor en contra materializado
    realingreso = db.Column(db.Float, default=0)  # Valor a favor materializado
    ejeRecibidos = db.Column(db.Integer, default=0)  #Cantidad Ejemplares recibidos
    ejeEntregados = db.Column(db.Integer, default=0)  #Cantidad Ejemplares recibidos
    ejePublicados = db.Column(db.Integer, default=0)  #Cantidad Ejemplares recibidos
    OtrAcciones = db.Column(db.Integer, default=0)  #Cantidad Ejemplares recibidos
    fechacrea = db.Column(db.DateTime, default=datetime.datetime.now)
    UsrSaldos = db.relationship("Usuario", lazy=True)


class Cadena(db.Model):
    __tablename__ = 'cadena'

    idCadena = db.Column(db.Integer, Sequence('idcadena_seq'), primary_key=True)
    PHash = db.Column(db.String(64), nullable=True)
    CHash = db.Column(db.String(64), nullable=False)
    Time = db.Column(db.String(64),  default=time.localtime())
    usuarioIdOrig = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), unique=True)
    usuarioIdDest = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), unique=True)
    vjId = db.Column(db.Integer, db.ForeignKey('videojuego.idVj'), unique=True)
    ejeUsuarioId = db.Column(db.Integer, db.ForeignKey('ejeusuario.idEjeUsuario'), unique=True)
    trxId = db.Column(db.Integer, db.ForeignKey('transaccion.idTrx'), unique=True)
    fechaEntrega = db.Column(db.DateTime, default=datetime.datetime.now)
    valor = db.Column(db.Float, default=0)
    UsrCadOri = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdOrig])
    UsrCadDes = db.relationship("Usuario", lazy=True, foreign_keys=[usuarioIdDest])
    VJCad = db.relationship("VideoJuego", lazy=True)
    EjeUCad = db.relationship("EjeUsuario", lazy=True)
    TrxCad = db.relationship("Transaccion", lazy=True)
