from smtplib import SMTPException
from flask_mail import Mail, Message
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from config import DevelopmentConfig, Config
from datamodel import db, Usuario, ConexionUsuario, EjeUsuario, VideoJuego, Clasificacion
from passlib.hash import sha256_crypt
import logging

app = Flask(__name__)

###
###Archivo que contiene todas las operaciones relacionadas con el
### tratamiento de los ejemplares que cargan los usuarios. Todas las rutas se invocan desde main.py
###


# Funcion: Cargar videojuego
def funCargarEjemplar(nick, idUsuario, VJ, estado, publicar, comentario):
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
        app.logger.error("[" + nick + "] CargarEjemplar: Crea EjemplarUsuaro: [" + VJ + "]")
        print("Ejemplar Usuario")

        db.session.commit()
        print("Commit")

        print("retornará: " + mensaje)
        return mensaje
    except:
        raise
        app.logger.error("[" + nick + "] publicarEjemplar: Usuario a confirmar: " + nick)
