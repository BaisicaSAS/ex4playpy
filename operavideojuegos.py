from flask import Flask
from sqlalchemy import func
from datamodel import db, Usuario, EjeUsuario, VideoJuego, Clasificacion, FotoEjeUsuario, TraceEjemplar, \
    Promo, DetalleValorOtros, DetalleValor, Transaccion, DetalleTrx, QyA
from datamodel import db, Usuario, EjeUsuario, VideoJuego, Clasificacion, FotoEjeUsuario, TraceEjemplar, Ciudad, FotoUsuario, CambioUsuario, LugarUsuario
from datetime import datetime, timedelta
import base64

#from PIL import Image

app = Flask(__name__)

# Constantes para las consultas de videojuegos: Cantidad de videojuegos y tiempo en días para que sea novedad
C_DIAS = 300
# Constantes para las consultas de videojuegos: Cantidad de ideojuegos y tiempo en días para que sea novedad
C_DIAS = 300
C_CANTIDAD = 10
# Constantes para los tipos de promocion
C_REGISTRO = "RG"
C_INTERCAMBIO = "IC"
C_ENTREGAVJ = "EV"
C_RESENA = "RS"
C_CALIFICA = "CF"
C_PROMOCION = 1

# Constantes para el estado en Transaccion
C_TRXCANCELADA = 0
C_TRXACTIVA = 1
C_TRXFINALIZADA = 2

# Constantes para la accion en DetTrx
# 1: Solicita, 2: Acepta Solicitud, 3: Entrega, 4: Recibe, 5: Califica
C_DETTRXSOLIC = 1
C_DETTRXACEPT = 2
C_DETTRXENTRE = 3
C_DETTRXRECIB = 4
C_DETTRXCALIF = 5
C_DETTRXCANCELAR = 6

# Constantes para el tipo de QyA
# 0: Question-pregunta - 1: Answer-respuesta
C_QYAPREG = 0
C_QYARESP = 1


#Constantes ciudad, Bogotá es la única por el momento
IDCIUDAD = 1

###Archivo que contiene todas las operaciones relacionadas con el
### tratamiento de los ejemplares que cargan los usuarios. Todas las rutas se invocan desde main.py

# Funcion: Listar nombres de videojuegos
def funListarNombresVJ():
    try:
        nombres = []

        result = db.session.query(VideoJuego).filter_by().all()
        for reg in result:
            nombres.append(reg.nombre)

        print("funListarNombresVJ: cantidad de registros de VJ" + str(len(nombres)))
        return nombres
    except:
        app.logger.error("[  ] publicarEjemplar: Error en lista VJ")
        raise


# Funcion: Cargar videojuego
def funCargarEjemplar(email, idUsuario, VJ, estado, publicar, comentario, imagen):
    try:
        mensaje = email + ", "
        #Busca el videojuego para obtener el valor
        obVj = db.session.query(VideoJuego).filter_by(nombre=VJ).first()
        if obVj is None:
            #app.logger.error("["+email+"] CargarEjemplar: No existe el videojuego: ["+VJ+"]")
            mensaje = mensaje + "No existe el VJ: Lo crearemos "
            publicado = 0
            cuarentena = 1 #Se pone en cuarentena el ejemplar si no existe el videojuego
            valor = 0
            #print("Nombre:"+VJ)
            obVj = VideoJuego(clasifId=1, consolaId=1, nombre=VJ, imagen="No identificada")
            db.session.add(obVj)
            obVj = db.session.query(VideoJuego).filter_by(nombre=VJ).one_or_none()
        else:
            clasif = db.session.query(Clasificacion).filter_by(idClasifica=obVj.clasifId).first()
            app.logger.error("["+email+"] CargarEjemplar: SI existe el videojuego: ["+VJ+"]")
            cuarentena = 0  # No en cuarentena
            publicado = publicar
            mensaje = mensaje + "Publicamos tu videojuego "
            valor = clasif.valorPuntos

        # Al cargar un ejemplar siempre revisa que sea el primero
        obUsuario = db.session.query(Usuario).filter_by(email=email).first()
        cantvj = db.session.query(EjeUsuario).filter_by(usuarioIdAct=obUsuario.idUsuario).count()
        print("Cantidad de VJ :"+str(cantvj))
        #Si es el primer videojuego --es decir no hay ninguno creado
        if cantvj == 0:
            print("Ingresa :" + str(cantvj))
            # ...y tenga una promo activa de tipo RG
            # Esta promo cargará los puntos de la promo gratis en la tabla DetalleValorOtros.
            promo = db.session.query(Promo).filter_by(activa=1).filter_by(aplicasobre=C_REGISTRO).first()
            puntos = promo.puntos

            # Al publicarlo, el videojuego queda "comprometido"...no puede ser editado está en cuarentena
            # pero debe ser publicado...ese estado

            comprometido=1

            obDeVaOtr = DetalleValorOtros(usuarioId=obUsuario.idUsuario, promoId=promo.idPromo, tipo=C_PROMOCION,\
                                          valorCobra=puntos, comentario=promo.descripcion)
            db.session.add(obDeVaOtr)

            mensaje = obUsuario.nombres + ", lo hiciste!. Tienes tus primeros " +str(puntos)+ " puntos. Ya puedes obtener un videojuego!"
        else:
            comprometido=0

        #crea el ejemplar del videojuego
        ejeUsuario = EjeUsuario(usuarioIdAct=idUsuario, vjId=obVj.idVj, comentario=comentario, estado=estado,
                                valor=valor, publicado=publicado, cuarentena=cuarentena, comprometido=comprometido)

        db.session.add(ejeUsuario)

        ejeUsuario = db.session.query(EjeUsuario).filter_by(usuarioIdAct=idUsuario, vjId=obVj.idVj,\
                                                            publicado=publicado, estado=estado).first()

        vfoto = imagen.read()

        fotoEjemplar = FotoEjeUsuario(ejeUsuarioId=ejeUsuario.idEjeUsuario, foto=vfoto)

        db.session.add(fotoEjemplar)

        funRegistrarTraceEjemplar(ejeUsuario.idEjeUsuario, email)

        app.logger.error("[" + email + "] CargarEjemplar: Crea EjemplarUsuaro: [" + VJ + "]")

        db.session.commit()
        return mensaje
    except:
        app.logger.error("[" + email + "] publicarEjemplar: Usuario a confirmar: " + email)
        raise


# Funcion: lista todos los ejemplares que posee un usuario, con su estado
def funListarEjemplaresUsuario(idUsuario):
    try:
        #Busca el videojuego para obtener el valor
        obEjeUsuario = db.session.query(EjeUsuario).filter_by(usuarioIdAct=idUsuario).all()
        usuario = db.session.query(Usuario).filter_by(idUsuario=idUsuario).first()
        email = usuario.email
        ejemplaresblk = []
        ejemplarespub = []
        ejemplaresnopub = []
        if obEjeUsuario is None:
            app.logger.error("["+email+"] ListarEjemplaresUsuario: No hay ejemplares")
        else:
            #SQL que se ejecutará en la consulta
            #SQL = db.session.query(EjeUsuario, FotoEjeUsuario, VideoJuego).filter_by(idEjeUsuario=idUsuario).join(FotoEjeUsuario, VideoJuego)
            #print(SQL)
            obEjeUsuario = db.session.query(EjeUsuario).filter_by(usuarioIdAct=idUsuario).all()
            #print("hay "+ len(obEjeUsuario).__str__()+" registros ejemplares")
            for ejemplar in obEjeUsuario:
                #print(ejemplar)
                #print("Ejemplar usuario " + ejemplar.idEjeUsuario.__str__())
                obVideojuego = db.session.query(VideoJuego).filter_by(idVj=ejemplar.vjId).first()
                obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=ejemplar.idEjeUsuario).first()
                if obFoto is None:
                    foto = "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brcoOR8CFF4BPmHddd6BNAhQeAX4YoHLoFkr9529++ojBCiUAvyHYTE/CFCYBWDSYgABIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAABAAAkAACAABIAAEgAAQAAJAAAgAASAABIAAEAACQAAIAAEgAASAABAAAkAACAABIAAEgAAQAAJAAAgAASAABIAAEAACQAAIAAEgAASAABAAAkAACAABIAAEgAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAA8BUrp2geBDju06NJGRRX0lRoMyJox6U3StlxIsBn3ibvWjiqbUUZai216N0nrk58oyo27gT4vwfn1k7uXBlllwKymr0DD71QnxfnAnwh/eii/rUMEIF4FHeb9c8rGknxJMBnMg7N7VQKUYgQfueF53JphsSnAJ/IvxT6owUiEfCw3/D3kzkMAuJbgE/kJc52xulACIzdlz9mGI4QAnzi+equxRAQrxi0XZnOPBihBCggc72HMWLii+rzHrJKRUABCni2uDai4uPE77E/n2UkwgrwqdWwpyEC4/jM73WdfR6CCyCX3xtngtC4w3DIPW3SEEEAufzJ+CIIjiNaJ2mXhSgCyOW3uyE6LrBer20SIgkgl++phPi0pvMzxnV/9YwHAeI2nHrM+Co0YyAC1PLsv5BR90xc1OSeDUvxMiDk00ZMav/gszT2CZNdWo2mIW0ocYBmnbMSI8e1slERK2cCfKVU8+Fhx17TXC+hLGJkTekLNCqcHRfa395AXayhHAvwBdvu/off0LkWrIIgWWJ5SVNx07b7NDbWGGu2PR8CfG6adhwRfV9jm0BFRMmKoifVN7vv+bk2zVivlNRegJkq97Oa9+aXale9XAJhsiFSTU1TQtqq6XQZRF78VAmtBeit9lrV2e+ymnVjMIiQBX1U1vN+QH31q5bNI6+S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"
                else:
                    foto = base64.b64encode(obFoto.foto).decode("utf-8")

                #Si el ejemplar está bloqueado
                if (ejemplar.bloqueado == 1 or ejemplar.cuarentena == 1) :
                    ejemplaresblk.append([ejemplar.idEjeUsuario, idUsuario, foto, obVideojuego.nombre, ejemplar.publicado, ejemplar.bloqueado, ejemplar.valor, ejemplar.estado, ejemplar.comentario, ejemplar.comprometido])
                else:
                    # Si el ejemplar no está publicado
                    if ejemplar.publicado == 1:
                        ejemplarespub.append([ejemplar.idEjeUsuario, idUsuario, foto, obVideojuego.nombre, ejemplar.publicado, ejemplar.bloqueado, ejemplar.valor, ejemplar.estado, ejemplar.comentario, ejemplar.comprometido])
                    else:
                        ejemplaresnopub.append([ejemplar.idEjeUsuario, idUsuario, foto, obVideojuego.nombre, ejemplar.publicado, ejemplar.bloqueado, ejemplar.valor, ejemplar.estado, ejemplar.comentario, ejemplar.comprometido])
                #for campo in ejemplar:
                #    print(campo)
            totejemplares = len(ejemplaresblk) + len(ejemplarespub) + len(ejemplaresnopub)
            app.logger.debug("["+email+"] ListarEjemplaresUsuario: hay "+ totejemplares.__str__()+" ejemplares")
            print("hay "+ len(ejemplaresblk).__str__()+" ejemplares bloqueados")
            print("hay "+ len(ejemplarespub).__str__()+" ejemplares publicados")
            print("hay "+ len(ejemplaresnopub).__str__()+" ejemplares no publicados")
            #print("hay "+ len(ejemplares).__str__()+" ejemplares")
            #for elm in ejemplares:
            #    print(ejemplares[0])
            #app.logger.error("[" + email + "] ListaEjemplar: Crea EjemplarUsuaro: [" + obEjeUsuario['idEjeUsuario'].str() + "]")

        return ejemplaresblk, ejemplarespub, ejemplaresnopub
    except:
        app.logger.error("[" + email + "] ListarEjemplarUsuario: Problemas al listar los ejemplares")
        raise


# Funcion: lista todos los ejemplares disponibles en la plataforma : Publicados por los usuarios
# maymen : Mayor o menor (1 Mayor que, 0 Menor que, para indicar si la consulta busca ejemplares cargados días antes )
# itdias : Numero de días limite para la consulta
# itcantidad: Numero de registros que se deben recuperar
# Cuando se lista con un usuario logged los ejemplares listados excluyen los de este usuario, si no está logged el parámetro es 0
def funListarEjemplaresDisponibles(maymen, idusuario=0, palabrabuscar=""):
    try:
        #print("usuario logueado: " + str(idusuario))
        app.logger.info("[NO_USER] ListarEjemplaresDisponibles: Inicia")
        #Busca los videojuegos NOVEDADES, que han sido cargados dentro de los # días anteriores
        # SI el parámetro es mayor
        if maymen == 1:
            obEjeUsuario = db.session.query(EjeUsuario).filter(EjeUsuario.fechacrea < datetime.today() - timedelta(days=C_DIAS)).\
            filter_by(publicado=1).filter_by(bloqueado=0).filter_by(cuarentena=0).limit(C_CANTIDAD)
        else:
            obEjeUsuario = db.session.query(EjeUsuario).filter(EjeUsuario.fechacrea >= datetime.today() - timedelta(days=C_DIAS)).\
                filter_by(publicado=1).filter_by(bloqueado=0).filter_by(cuarentena=0).limit(C_CANTIDAD)

        ejemplarespub = []
        if obEjeUsuario is None:
            app.logger.error("[no_user] ListarEjemplaresUsuario: No hay ejemplares")
        else:
            for ejemplar in obEjeUsuario:
                obVideojuego = db.session.query(VideoJuego).filter_by(idVj=ejemplar.vjId).first()
                #print("usuario logueado: " + str(idusuario)+" - dueño del ejemplar: "+ str(ejemplar.usuarioIdAct))
                if ejemplar.usuarioIdAct != idusuario:
                    nomvj = obVideojuego.nombre.lower()
                    #print("palabrebuscar = " + palabrabuscar)
                    if palabrabuscar != "":
                        palabrabuscar = palabrabuscar.lower()
                    if palabrabuscar in nomvj:
                        obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=ejemplar.idEjeUsuario).first()
                        if obFoto is None:
                            foto = "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brcoOR8CFF4BPmHddd6BNAhQeAX4YoHLoFkr9529++ojBCiUAvyHYTE/CFCYBWDSYgABIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAAAACAAgAIACAABAAAkAACAABIAAEgAAQAAJAAAgAASAABIAAEAACQAAIAAEgAASAABAAAkAACAABIAAEgAAQAAJAAAgAASAABIAAEAACQAAIAAEgAASAABAAAkAACAABIAAEgAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAAAAEABAAQAEAA8BUrp2geBDju06NJGRRX0lRoMyJox6U3StlxIsBn3ibvWjiqbUUZai216N0nrk58oyo27gT4vwfn1k7uXBlllwKymr0DD71QnxfnAnwh/eii/rUMEIF4FHeb9c8rGknxJMBnMg7N7VQKUYgQfueF53JphsSnAJ/IvxT6owUiEfCw3/D3kzkMAuJbgE/kJc52xulACIzdlz9mGI4QAnzi+equxRAQrxi0XZnOPBihBCggc72HMWLii+rzHrJKRUABCni2uDai4uPE77E/n2UkwgrwqdWwpyEC4/jM73WdfR6CCyCX3xtngtC4w3DIPW3SEEEAufzJ+CIIjiNaJ2mXhSgCyOW3uyE6LrBer20SIgkgl++phPi0pvMzxnV/9YwHAeI2nHrM+Co0YyAC1PLsv5BR90xc1OSeDUvxMiDk00ZMav/gszT2CZNdWo2mIW0ocYBmnbMSI8e1slERK2cCfKVU8+Fhx17TXC+hLGJkTekLNCqcHRfa395AXayhHAvwBdvu/off0LkWrIIgWWJ5SVNx07b7NDbWGGu2PR8CfG6adhwRfV9jm0BFRMmKoifVN7vv+bk2zVivlNRegJkq97Oa9+aXale9XAJhsiFSTU1TQtqq6XQZRF78VAmtBeit9lrV2e+ymnVjMIiQBX1U1vN+QH31q5bNI6+S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"
                        else:
                            foto = base64.b64encode(obFoto.foto).decode("utf-8")
                        #print("inserta ejemplar # " + str(ej))
                        ejemplarespub.append([ejemplar.idEjeUsuario, ejemplar.usuarioIdAct, foto, obVideojuego.nombre, ejemplar.publicado, ejemplar.bloqueado, ejemplar.valor, ejemplar.estado, ejemplar.comentario])

            app.logger.info("[NO_USER] ListarEjemplaresDisponibles: hay "+ len(ejemplarespub).__str__()+" ejemplares disponibles")
            #print("buscar = "+buscar+" -- hay "+ len(ejemplarespub).__str__()+" ejemplares publicados - maymen (1: May - 0: Men) " + str(maymen) )

        return ejemplarespub
    except:
        app.logger.error("[" + str(idusuario) + "] ListarEjemplaresDisponibles: Problemas al listar los ejemplares")
        raise


#Cada vez que un ejemplar se actualiza, se crea un registro en el trace
def funRegistrarTraceEjemplar(idEjeUsuario, email):
    try:
        obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idEjeUsuario).first()
        obTraceEjemplar = TraceEjemplar(vjId=obEjeUsuario.vjId, ejeUsuarioId=obEjeUsuario.idEjeUsuario, usuarioId=obEjeUsuario.usuarioIdAct, comentario=obEjeUsuario.comentario, estado=obEjeUsuario.estado, valor=obEjeUsuario.valor,)

        db.session.add(obTraceEjemplar)

        app.logger.debug("[" + email + "] funMarcarEjemplaresUsuario: ejemplar actualizado por usuario "+email)
        db.session.commit()
    except:
        app.logger.error("[" + email + "] funMarcarEjemplaresUsuario: Problemas al actualizar ejemplar usuario")
        raise


# Funcion: marcar un ejemplar de usuario cómo publicado o no publicado {estado= 1 publicado, 0: no publicado}
def funMarcarEjemplaresUsuario(email, idEjeUsuario, estado):
    try:
        ejeusr = EjeUsuario.query.filter_by(idEjeUsuario=idEjeUsuario).update(dict(publicado=estado))
        app.logger.debug("[" + email + "] funMarcarEjemplaresUsuario: ejemplar actualizadom por usuario "+email)
        db.session.commit()
    except:
        app.logger.error("[" + email + "] funMarcarEjemplaresUsuario: Problemas al actualizar ejemplar usuario")
        raise


# Funcion: Editar ejemplar
def funEditarEjemplar(idejeusuario, email, estado, comentario, imagen):
    try:
        ejeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejeusuario).update(dict(estado=estado, comentario=comentario))

        #if imagen.read() is not None:
        #    print("imagen not none")
        #    print(imagen.read())
        fotoEjemplar = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=idejeusuario).update(dict(foto=imagen.read()))
        #else:
        #    print("imagen None")

        funRegistrarTraceEjemplar(idejeusuario, email)

        app.logger.error("[" + email + "] EditarEjemplar: Edita EjemplarUsuaro: [" + str(idejeusuario) + "]")

        db.session.commit()
        return "Se editó el ejemplar!"
    except:
        db.session.rollback()
        app.logger.error("[" + email + "] EditarEjemplar: Usuario a confirmar: " + email)
        raise


# Funcion: Obtener los datos del usuario
def funObtenerDatosUsuario(idUsuario):
    usuario = db.session.query(Usuario).filter_by(idUsuario=idUsuario).first()
    obFoto = db.session.query(FotoUsuario).filter_by(usuarioId=idUsuario, activa=1).first()
    direcciones = db.session.query(LugarUsuario).filter_by(usuarioId=idUsuario, activa=1).all()

    nick = usuario.nickName
    if obFoto is None:
        foto = "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"
    else:
        foto = base64.b64encode(obFoto.foto).decode("utf-8")

    if usuario is None:
        app.logger.error("[" + nick + "] funObtenerDatosUsuario: No se pudieron obtener los datos del usuario")
    else:
        return usuario, foto, direcciones


def funUpdateDatosUsuario(idUsuario,nombres,apellidos,edad,fechanac,genero, celular, nickname,email, imagen, direcciones,hoy, where):
    try:
        if where == 0:
            # Actualiza los datos del usuario
            datosUsuario = Usuario.query.filter_by(idUsuario=idUsuario).update(dict(nombres=nombres, apellidos=apellidos, edad=edad,
                                    fechanac=fechanac, genero=genero, celular=celular, nickName=nickname ))

            if imagen.filename != '':
                fotoAnt = FotoUsuario.query.filter_by(usuarioId=idUsuario).update(dict(activa=0))

                vfoto = imagen.read()
                fotoUsuario = FotoUsuario(usuarioId=idUsuario, foto=vfoto, activa=1)
                db.session.add(fotoUsuario)

            cambioUsuario = CambioUsuario(usuarioId=idUsuario, nombres=nombres, apellidos=apellidos, celular=celular, nickName=nickname, email=email, fechacrea=hoy)

            db.session.add(cambioUsuario)
            db.session.commit()
        else:
            cont = 0
            principal = 0

            if len(direcciones) > 0:
                direccionesAnt = LugarUsuario.query.filter_by(usuarioId=idUsuario).update(dict(activa=0))
                for dir in direcciones:
                    if cont == 0:
                        principal = 1
                    else:
                        principal = 0
                    cont+=1
                    direccion = LugarUsuario(usuarioId=idUsuario, ciudadId = IDCIUDAD, direccion=dir, activa=1, principal=principal, fechacrea=hoy)
                    db.session.add(direccion)
                db.session.commit()
    except:
        db.session.rollback()
        raise

# Recupera los puntos que un usuario tiene disponibles para adquirir videojuegos
def funPuntosDisponiblesUsuario(idusuario):
    try:
        usuario = db.session.query(Usuario).filter_by(idUsuario=idusuario).first()
        email = usuario.email
        puntoscambios = db.session.query(DetalleValor).filter_by(usuarioId=usuario.idUsuario).all()
        puntosotros = db.session.query(DetalleValorOtros).filter_by(usuarioId=usuario.idUsuario).all()
        sum = 0;
        for pc in puntoscambios:
            print("Puntos cambios : " + str(pc.valorCobra-pc.valorPaga))
            sum = sum + pc.valorCobra - pc.valorPaga
        for po in puntosotros:
            print("Puntos otros : " + str(po.valorCobra-po.valorPaga))
            sum = sum + po.valorCobra - po.valorPaga
        app.logger.error("[" + email + "] funPuntosDisponiblesUsuario: Puntos para : " + email + "- ["+str(sum)+"]")
        print("Puntos usuario : " + str(sum))

        return sum
    except:
        app.logger.error("[" + email + "] funPuntosDisponiblesUsuario: problema al buscar puntos para : " + email)
        #return 0
        raise

# crear transacción de solicitd del usuario
# aquí se crea la trx de solicitud, activa y además el detalle para el usuario que solicita
# con la primera QyA que recibirá
#
def funCrearTransaccion(idusrsolicita, idusrdueno, idejemplar, mensaje):
    try:
        resultado = 0
        ejeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejemplar).first()
        usuario = db.session.query(Usuario).filter_by(idUsuario=idusrsolicita).first()
        email = usuario.email
        trx = db.session.query(Transaccion).filter_by(usuarioIdSolic=idusrsolicita, usuarioIdDueno=idusrdueno,
                                                      estadoTrx=C_TRXACTIVA, ejeUsuarioId=ejeUsuario.idEjeUsuario).\
                                                      first()
        # Revisa si existe una transación, si exste la recupera, si no existe la crea
        if trx is None:
            #Crea la transacción
            obTrx = Transaccion(usuarioIdSolic=idusrsolicita, usuarioIdDueno=idusrdueno, estadoTrx=C_TRXACTIVA,
                                ejeUsuarioId=ejeUsuario.idEjeUsuario, estado=ejeUsuario.estado, valor=ejeUsuario.valor,
                                vjId=ejeUsuario.vjId)

            db.session.add(obTrx)

            selTrx = db.session.query(Transaccion).filter_by(usuarioIdSolic=idusrsolicita, usuarioIdDueno=idusrdueno,
                                ejeUsuarioId=ejeUsuario.idEjeUsuario, vjId=ejeUsuario.vjId).first()

            # Crea el detalle de la transacción
            obDetTrx = DetalleTrx(trxId=selTrx.idTrx, usuarioId=idusrdueno, accion=C_DETTRXSOLIC)

            # Crea la QyA
            obQyA = QyA(tipo=C_QYAPREG, trxId=selTrx.idTrx, usuarioIdDueno=idusrdueno, usuarioIdSolic=idusrsolicita,
                        usuarioIdMsg=idusrsolicita, vjId=ejeUsuario.vjId, ejeUsuarioId=ejeUsuario.idEjeUsuario,
                        PregResp=mensaje)

            resultado = selTrx.idTrx
            db.session.add(obDetTrx)
            db.session.add(obQyA)

            db.session.commit()
        else:
            resultado = trx.idTrx

        return resultado
    except:
        app.logger.error("[" + email + "] funCrearTransaccion: problema al crear solicitud de " + email)
        db.session.rollback()
        #return resultado
        raise


def funcObtenerCiudades():
    try:
        result = db.session.query(Ciudad).filter_by().all()
    except:
        raise

    return result


def funcCrearUpdateQA(idTrx, mensaje, idUsuario, where):
    qya = db.session.query(QyA).filter_by(trxId=idTrx).first()
    # Crea la QyA
    obQyA = QyA(tipo=C_QYAPREG, trxId=idTrx, usuarioIdDueno=qya.usuarioIdDueno, usuarioIdSolic=qya.usuarioIdSolic,
                usuarioIdMsg=idUsuario, vjId=qya.vjId, ejeUsuarioId=qya.ejeUsuarioId,PregResp=mensaje)

    db.session.add(obQyA)

    if where == 'cancelar':
        obDetTrx = DetalleTrx(trxId=idTrx, usuarioId=idUsuario, accion=C_DETTRXCANCELAR)
        db.session.add(obDetTrx)

    db.session.commit()
    qya = db.session.query(QyA).filter_by(trxId=idTrx).all()

    return qya



def funTransaccionTrato(idTrx,idusuario,idotrousuario, accion):
    try:
        obDetTrx = DetalleTrx(trxId=idTrx, usuarioId=idusuario, accion=C_DETTRXSOLIC)

        db.session.add(obDetTrx)
        db.session.commit()


    except:
        db.session.rollback()
        #return resultado
        raise

