from flask import Flask
from datamodel import db, Usuario, EjeUsuario, VideoJuego, Clasificacion, FotoEjeUsuario
import base64

app = Flask(__name__)

###
###Archivo que contiene todas las operaciones relacionadas con el
### tratamiento de los ejemplares que cargan los usuarios. Todas las rutas se invocan desde main.py
###


# Funcion: Cargar videojuego
def funCargarEjemplar(nick, idUsuario, VJ, estado, publicar, comentario, imagen):
    try:
        mensaje = nick + ", "
        #Busca el videojuego para obtener el valor
        obVj = db.session.query(VideoJuego).filter_by(nombre=VJ).first()
        if obVj is None:
            app.logger.error("["+nick+"] CargarEjemplar: No existe el videojuego: ["+VJ+"]")
            mensaje = mensaje + "No existe el VJ: Lo crearemos "
            publicado = 0
            bloqueado = 1 #Se bloquea el ejemplar si no existe el videojuego
            valor = 0
            #print("Nombre:"+VJ)
            obVj = VideoJuego(clasifId=1, consolaId=1, nombre=VJ, imagen="No identificada")
            db.session.add(obVj)
            obVj = db.session.query(VideoJuego).filter_by(nombre=VJ).one_or_none()
        else:
            clasif = db.session.query(Clasificacion).filter_by(idClasifica=obVj.clasifId).first()
            app.logger.error("["+nick+"] CargarEjemplar: SI existe el videojuego: ["+VJ+"]")
            bloqueado = 0  # No bloqueado
            publicado = publicar
            mensaje = mensaje + "Publicamos tu videojuego "
            valor = clasif.valorPuntos

        #crea el ejemplar del videojuego
        ejeUsuario = EjeUsuario(usuarioIdAct=idUsuario, vjId=obVj.idVj, comentario=comentario,
                                estado=estado, valor=valor, publicado=publicado, bloqueado=bloqueado)

        db.session.add(ejeUsuario)

        ejeUsuario = db.session.query(EjeUsuario).filter_by(usuarioIdAct=idUsuario, vjId=obVj.idVj, publicado=publicado, estado=estado).first()

        fotoEjemplar = FotoEjeUsuario(ejeUsuarioId=ejeUsuario.idEjeUsuario, foto=imagen.read())

        db.session.add(fotoEjemplar)

        app.logger.error("[" + nick + "] CargarEjemplar: Crea EjemplarUsuaro: [" + VJ + "]")

        db.session.commit()
        return mensaje
    except:
        raise
        app.logger.error("[" + nick + "] publicarEjemplar: Usuario a confirmar: " + nick)


# Funcion: lista todos los ejemplares que posee un usuario, con su estado
def funListarEjemplaresUsuario(idUsuario):
    try:
        #Busca el videojuego para obtener el valor
        obEjeUsuario = db.session.query(EjeUsuario).filter_by(usuarioIdAct=idUsuario).all()
        usuario = db.session.query(Usuario).filter_by(idUsuario=idUsuario).first()
        nick = usuario.nickName
        ejemplares = []
        if obEjeUsuario is None:
            app.logger.error("["+nick+"] ListarEjemplaresUsuario: No hay ejemplares")
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

                ejemplares.append([ejemplar.idEjeUsuario, idUsuario, foto, obVideojuego.nombre, ejemplar.publicado])
                #for campo in ejemplar:
                #    print(campo)
            app.logger.error("["+nick+"] ListarEjemplaresUsuario: hay "+ len(ejemplares).__str__()+" ejemplares")
            #print("hay "+ len(ejemplares).__str__()+" ejemplares")
            #for elm in ejemplares:
            #    print(ejemplares[0])
            #app.logger.error("[" + nick + "] ListaEjemplar: Crea EjemplarUsuaro: [" + obEjeUsuario['idEjeUsuario'].str() + "]")

        return ejemplares
    except:
        raise
        app.logger.error("[" + nick + "] ListarEjemplarUsuario: Problemas al listar los ejemplares")
