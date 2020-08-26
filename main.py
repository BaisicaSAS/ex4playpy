from smtplib import SMTPException
from flask_mail import Mail, Message
from threading import Thread
from flask import Flask, request, render_template, session, current_app
from config import ProductionConfig, DevelopmentConfig, Config
from datamodel import db, Usuario, ConexionUsuario, VideoJuego, EjeUsuario, FotoEjeUsuario
from operavideojuegos import funCargarEjemplar, funListarEjemplaresUsuario, funMarcarEjemplaresUsuario, \
    funListarEjemplaresDisponibles, funObtenerDatosUsuario, funUpdateDatosUsuario
from passlib.hash import sha256_crypt
import logging
from sqlalchemy.exc import IntegrityError
import base64
from flask_googlemaps import GoogleMaps, Map
from datetime import datetime

app = Flask(__name__)

# PRODUCCION - ESTE CODIGO SE HABILITA EN PRODUCCION
mail = Mail(app)
# mail.init_app(app)
# db.init_app(app)

#Google Maps
# Initialize the extension
GoogleMaps(app, key="AIzaSyC9YiF0Bqb2yA_Cb3WkWERvrSn59EhxmTs")

# DESARROLLO
app.config.from_object(DevelopmentConfig)
# PRODUCCION
# app.config.from_object(ProductionConfig)

# C 0 N S T A N T E S
ESTADO_USR_INACTIVO = 0  # Si el usuario está inactivo
ESTADO_USR_ACTIVO = 1  # Si el usuario está activo
USR_NONE = "NONE"
CON_LOGOUT = "LOGOUT"
ID_USR_NONE = 0


# DESARROLLO
URL_CONFIRMA = "http://127.0.0.1:8000/confirma?"
URL_APP = "http://127.0.0.1:8000"
# PRODUCCION
# URL_CONFIRMA = "http://ex4play.pythonanywhere.com/confirma?"
# URL_APP = "http://ex4play.pythonanywhere.com/"

# PRODUCCION
# LOG_FILENAME = 'ex4playpy/tmp/errores.log'
# DESARROLLO
LOG_FILENAME = 'tmp\errores.log'

app.config['MAIL_SERVER'] = 'p3plcpnl1009.prod.phx3.secureserver.net'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "ex4play@baisica.co"
app.config['MAIL_PASSWORD'] = 'JuSo2015@'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
SUBJECT_REGISTRO = "Bienvenido a ex4play {nick} !"


logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

# Funcion: index
# La pagina principal debe tener todos los accesos y mostrar todos los juegos en la plataforma
@app.route('/')
def index():
    app.logger.debug("[NO_USER] index: inicia index")
    videojuegos = []
    novedades = []
    if db.session is not None:
        # Recupera listado de videojuegos generales
        result = db.session.query(VideoJuego).filter_by().order_by(VideoJuego.idVj).limit(100)
        for reg in result:
            videojuegos.append(reg)

        # Recupera listado de ejemplares existentes en la plataforma
        result = funListarEjemplaresDisponibles()
        for reg in result:
            novedades.append(reg)

    if not(session) or (session['email'] is None):
        app.logger.debug("[NO_USER] index: No hay sesion")

        return render_template('home_page.html', mensaje="Registrate y disfruta!", videojuegos=videojuegos, novedades=novedades, logged=0)
    else:
        app.logger.debug("["+session['email']+"] index: Hay sesion")

    return render_template('inicio.html', mensaje="Bienvenido "+session['email'], videojuegos=videojuegos, novedades=novedades, logged=1)


# Funcion: login
@app.route("/login", methods=["POST","GET"])
def login():
    app.logger.debug("[NO_USER] login: inicia login")
    email=""
    if request.method == "POST":
        try:
            email = str(request.form.get("email"))
            pwdorig = str(request.form.get("clave"))
            idnick = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(pwdorig)
            app.logger.info("[" + email + "] login: Datos del usuario ingresado: email[" + email + "]")
            #app.logger.info("login: Datos del usuario ingresado: email[" + email + "], pwd[" + idnick + "], pwdorg["+pwdorig+"]")
            #app.logger.info("[email: " + email + "] - [sesion: " + str(session['email']) + "]")

            #usuarioValido = db.session.query(Usuario.email, Usuario.pwd).filter_by(email=email,
            #                                                                          pwd=idnick).scalar() is not None

            obUsuario = db.session.query(Usuario).filter_by(email=email, pwd=idnick).one_or_none()

            #if usuarioValido == True:
            if obUsuario is not None:
                if not((not session) or (not email in session['email'])): #Si hay una sesion activa
                    # Si existe el usuario, pero es inactivo, debe remitirse al mail
                    if obUsuario.activo == ESTADO_USR_INACTIVO:
                        return render_template('inicio.html', mensaje=email+", debes confirmar tu registro en tu correo para poder ingresar!", logged=0)
                    else:
                        app.logger.debug("[" + email + "] login: Hay una sesion")
                        app.logger.info("[" + email + "] login: Usuario a ingresar con sesion recuperada: " + email)

                        #Crea el registro de seguimiento a las conexion - IP ConexionUsuario
                        newConnUsuario = ConexionUsuario(usuarioId=obUsuario.idUsuario, ipaddr=request.remote_addr)
                        db.session.add(newConnUsuario)
                        db.session.commit()

                        result = db.session.query(VideoJuego).filter_by().order_by(VideoJuego.idVj).limit(100)
                        lista = []
                        for reg in result:
                            lista.append(reg)

                        novedades = []
                        # Recupera listado de ejemplares existentes en la plataforma
                        result = funListarEjemplaresDisponibles()
                        for reg in result:
                            novedades.append(reg)
                        return render_template('inicio.html', mensaje="Ya estabas logueado " + email, videojuegos=lista, novedades=novedades, logged=1)
                else:
                    #Revisa si el usuario está activo o inactivo
                    if obUsuario.activo == ESTADO_USR_INACTIVO:
                        return render_template('inicio.html', mensaje=email+", debes confirmar tu registro en tu correo para poder ingresar! <a href="+URL_APP+"/reenviarconf>Reenvíar el correo de confirmación</a>", logged=0)
                    else:
                        app.logger.debug("[" + email + "] login: No hay sesion")

                        session['email'] = email
                        session['idnick'] = idnick

                        app.logger.info("[" + email + "] login: Sesion generada: " + email)

                        # Crea el registro de seguimiento a las conexion - IP ConexionUsuario
                        newConnUsuario = ConexionUsuario(usuarioId=obUsuario.idUsuario, ipaddr=request.remote_addr)

                        db.session.add(newConnUsuario)
                        db.session.commit()

                        result = db.session.query(VideoJuego).filter_by().order_by(VideoJuego.idVj).limit(100)
                        lista = []
                        for reg in result:
                            lista.append(reg)

                        novedades = []
                        # Recupera listado de ejemplares existentes en la plataforma
                        result = funListarEjemplaresDisponibles()
                        for reg in result:
                            novedades.append(reg)
                        return render_template('inicio.html', mensaje="Bienvenido al sistema "+email+"!", videojuegos=lista, novedades=novedades, logged=1 )
            else:
                app.logger.info("[" + email + "] Usuario o password inválido. Intenta de nuevo!")
                return render_template('login.html', mensaje="Usuario o password inválido. Intenta de nuevo!" )
        except:
            app.logger.error("[" + email + "] login: problema con usuario a ingresar: " + email)
            #return render_template('login.html', mensaje="Algo sucedió, intenta de nuevo !" )
            raise
    return render_template('login.html', mensaje="" )


# Funcion: logout
@app.route("/logout", methods=["GET"])
def logout():
    if request.method == "GET":
        try:
            email = session['email']
            obUsuario = db.session.query(Usuario.idUsuario).filter_by(email=email).one_or_none()
            if obUsuario is not None:
                v_id = obUsuario.idUsuario
                session.clear()
                # Crea el registro de seguimiento a las conexion - IP ConexionUsuario con tipo LOGOUT
                newConnUsuario = ConexionUsuario(usuarioId=v_id, ipaddr=request.remote_addr, tipo=CON_LOGOUT)
                db.session.add(newConnUsuario)
                db.session.commit()
                return render_template('login.html', mensaje="Sesion finalizada, vuelve pronto!")
            else:
                return render_template('login.html', mensaje="No hay sesion, intenta ingresar de nuevo")
        except:
            #raise
            app.logger.error("[NO_USER logout: problema con usuario al cerrar sesion")
            return render_template('login.html', mensaje="Algo sucedió, intenta de nuevo !" )


# Funcion: registro
@app.route("/registro", methods=["POST", "GET"])
def registro():
    app.logger.debug("[NO_USER] registro: inicia registro")
    if request.method == "POST":
        try:
            nombres = request.form.get("nombres")
            apellidos = request.form.get("apellidos")
            email = request.form.get("email")
            email = email.lower()
            clave = request.form.get("clave")
            aceptater = request.form.get("aceptat") # Acepta los términos
            recibenot = request.form.get("recibir") # Acepta recibir notificaciones
            pwdseguro = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(clave))
            nickname = email
            newUsuario = Usuario(nombres=nombres, apellidos=apellidos, pwd=pwdseguro, email=email, nickName=nickname, aceptater=aceptater, recibenot=recibenot)
            db.session.add(newUsuario)
            app.logger.debug("[" + email + "] registro: Usuario adicionado a BD: " + newUsuario.nombres + " - mail - " + newUsuario.email)
            urlconfirma = URL_CONFIRMA +"usr=" + email + "&id=" + sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(email+pwdseguro))
            app.logger.debug("[" + email + "] registro: armó urlconfirma: " + urlconfirma)

            app.logger.debug("[" + email + "] registro: va a enviar correo")
            subject = SUBJECT_REGISTRO.format(nick=nombres)

            if enviar_correo(subject, app.config['MAIL_USERNAME'], email, text_body=None, template="mailbienvenida.html", nick=email, urlconfirma=urlconfirma) == 1:
                app.logger.debug("[" + nickname + "] registro: envió mail a : " + newUsuario.nombres + " - mail - " + newUsuario.email)

                #***************************************
                #Manejo de clave duplicada en la inserción del usuario
                try:
                    db.session.commit()
                    app.logger.debug(
                        "[" + email + "] registro: Usuario registrado: " + newUsuario.nombres + " - mail - " + newUsuario.email)
                    app.logger.debug(
                        "registro: Usuario registrado: " + newUsuario.nombres + " - mail - " + newUsuario.email + " " + clave + " " + pwdseguro)
                except IntegrityError as e:

                    app.logger.debug("[" + email + "] registro: Repetido")

                    app.logger.info("%s Ya esta registrado.")
                    app.logger.debug("[" + email + "] registro: %s Ya esta registrado." % e.params[0])
                    db.session.rollback()
                    return render_template('resetclave.html',
                                       mensaje="Ya existe un registro para " + email + ". Recupera tu clave!")

                #***************************************
            return render_template('registro.html', mensaje="Ya estás registrado " + newUsuario.nombres + ". Confirma en tu correo para finalizar!")
        except:
            app.logger.error("[" + email + "] registro: Usuario a registrar: " + nombres + " - mail - " + pwdseguro)
            raise
            #return render_template('error.html', mensaje="Error en registro!")
    return render_template('registro.html', mensaje="" )

# Funcion: reenviar correo confirmacion
@app.route("/reenviarconf", methods=["POST", "GET"])
def reenviarconf():
    app.logger.debug("[NO_USER] reenviar mail: inicia reenviar mail confirmacion")
    pwdseguro = ""
    email = ""
    if request.method == "POST":
        try:
            email = request.form.get("email")
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            if obUsuario is not None:
                pwdseguro = obUsuario.pwd
                app.logger.debug("[" + email + "] reenviar mail: Usuario adicionado a BD: " + obUsuario.nombres + " - mail - " + obUsuario.email)
                urlconfirma = URL_CONFIRMA +"usr=" + email + "&id=" + sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(email+pwdseguro))
                app.logger.debug("[" + email + "] reenviar mail: armó urlconfirma: " + urlconfirma)

                app.logger.debug("[" + email + "] reenviar mail: va a enviar correo")
                subject = SUBJECT_REGISTRO.format(nick=obUsuario.nombres)

                if enviar_correo(subject, app.config['MAIL_USERNAME'], email, text_body=None, template="mailbienvenida.html", nick=email, urlconfirma=urlconfirma) == 1:
                    app.logger.debug("[" + email + "] reenviar mail: envió mail a : " + obUsuario.nombres + " - mail - " + obUsuario.email)
                    app.logger.debug("reenviar mail: Usuario registrado: " + obUsuario.nombres + " - mail - " + obUsuario.email + " " + pwdseguro)
                return render_template('login.html', mensaje= "Correo reenviado a " + email + ". " + obUsuario.nombres + ". Confirma en tu correo para finalizar el registro!")
            else:
                return render_template('login.html', mensaje="El usuaurio no ha realizado registro en ex4play " + email)

        except:
            app.logger.error("[" + email + "] registro: Usuario a registrar: " + email + " - mail - " + pwdseguro)
            raise
            #return render_template('error.html', mensaje="Error en registro!")
    return render_template('reenviarconf.html', mensaje="Reenviar correo de confirmación!" )


# Funcion: confirma
@app.route("/confirma", methods=["GET", "POST"])
def confirma():
    app.logger.debug("[NO_USER] confirma: inicia confirmación ")
    email = ""
    if request.method == "GET":
        try:
            email = request.args.get("usr").lower()
            id = request.args.get("id")

            #Busca el usuario para validar
            app.logger.debug("[NO_USER] confirma: Usuario a confirmar: " + email)
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()

            if obUsuario is not None:
                if obUsuario.activo == ESTADO_USR_ACTIVO:
                    app.logger.debug(
                        "[" + email + "] confirma: Usuario YA estaba activo: " + obUsuario.nombres + " - mail - " + obUsuario.email)
                    return render_template('login.html', mensaje="El enlace ya no funciona, pero ya estás activo " + obUsuario.nombres + ". Ingresa!")
                else:
                    pwd= obUsuario.pwd
                    app.logger.debug("[" + usr + "] confirma: Usuario recuperado: " + usr+pwd )

                    idvalida = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(usr+pwd))

                    if idvalida==id:
                        obUsuario.activo = ESTADO_USR_ACTIVO
                        db.session.commit()
                        app.logger.debug("[" + usr + "] confirma: Usuario activo: " + obUsuario.nombres + " - mail - " + obUsuario.email)
                        return render_template('login.html', mensaje="Ya estás activo " + obUsuario.nombres + ". Ingresa!")
                    else:
                        return render_template('error.html', mensaje="Hubo un error " + obUsuario.nombres + ". Vuelve a intentarlo desde tu correo!")
            else:
                return render_template('registro.html',
                                       mensaje="El usuario " + usr + ", no se encuentra registrado. Regístrate antes!")
        except:
            app.logger.error("[" + usr + "] confirma: Usuario a confirmar: " + usr)
            #return render_template('error.html', mensaje="Error en confirmación!")
            raise
    return render_template('login.html', mensaje= "Ingresa al sistema!")


# Funcion: reset clave
@app.route("/resetclave", methods=["POST", "GET"])
def resetclave():
    app.logger.debug("[NO_USER] reset clave: inicia reset clave ")
    #email = ""
    if request.method == "POST":
        try:
            email = request['email']
            claveactual = request.args.get("id")
            id = request.args.get("id")

            #Busca el usuario para validare
            app.logger.debug("[NO_USER] confirma: Usuario a confirmar: " + email)
            obUsuario = db.session.query(Usuario.email).filter_by(email=email).one_or_none()

            if obUsuario is not None:
                pwd=obUsuario.pwd
                app.logger.debug("[" + email + "] confirma: Usuario recuperado: " + email+pwd )

                idvalida = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(email+pwd))

                if idvalida==id:
                    obUsuario.activo = ESTADO_USR_ACTIVO
                    db.session.commit()
                    app.logger.debug("[" + email + "] confirma: Usuario activo: " + obUsuario.nombres + " - mail - " + obUsuario.email)
                    return render_template('login.html', mensaje="Ya estás activo " + obUsuario.nombres + ". Ingresa!")
                else:
                    return render_template('resetclave.html', mensaje="Hubo un error " + obUsuario.nombres + ". Vuelve a intentarlo desde tu correo!")
            else:
                return render_template('registro.html',
                                       mensaje="El usuario " + email + ", no se encuentra registrado. Regístrate antes!")
        except:
            app.logger.error("[" + email + "] confirma: Usuario a confirmar: " + email)
            return render_template('error.html', mensaje="Error en confirmación!")
    return render_template('resetclave.html', mensaje="")


# Funcion: enviar_correo
def enviar_correo(subject, sender, recipients, text_body,
                  cc=None, bcc=None, html_body=None, template=None, **kwargs):
    app.logger.debug("[" + recipients + "] enviar_correo: Inicia ")
    try:
        #f or key, value in kwargs.items():
        #    print("The value of {} is {}".format(key, value))

        app.logger.debug("[" + recipients + "] va enviar_correo: SEND ")

        #envía copia al usuario que envía
        msg = Message(subject, sender=sender, recipients=[recipients, ], cc=cc, bcc=bcc)
        msg.html = render_template(template, **kwargs)
        msg.body = render_template(template, **kwargs)

        Thread(target=_send_async_email, args=(current_app._get_current_object(), msg)).start()

        msg = Message(subject, sender=sender, recipients=[sender, ], cc=cc, bcc=bcc)
        msg.html = render_template(template, **kwargs)
        msg.body = render_template(template, **kwargs)

        Thread(target=_send_async_email, args=(current_app._get_current_object(), msg)).start()
        app.logger.debug("[CORREO A: " + recipients[0].lower() + "] Generó tarea para enviar ")
        return 1
    except SMTPException:
        app.logger.debug("[NO_USER] enviar_correo: error en enviar correo " + sender)
        # raise
        return 0
    #Thread(target=_send_async_email, args=(current_app._get_current_object(), msg)).start()


# Funcion: Dar de Baja Usuario
@app.route("/bajausuario", methods=["GET", "POST"])
def bajausuario():
    if request.method == "POST":
        if session is not None:
            email = session['email']
            print("email:" + email)
            #Recuperar usuario
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            obEjeUsuario = db.session.query(EjeUsuario).filter_by(email=email).one_or_none()


# Funcion: Cargar un ejemplar
@app.route("/cargarEjemplar", methods=["GET", "POST"])
def cargarEjemplar():

    result = db.session.query(VideoJuego.nombre).filter_by().order_by(VideoJuego.nombre).all()
    lista = []
    for reg in result:
        lista.append(reg.nombre)

    if request.method == "POST":
        if session is not None:
            email = session['email']
            print("email:" + email)
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            if obUsuario is not None:
                usrid = obUsuario.idUsuario
                imagen = request.files["imgInp"]
                vj = request.form.get("ejemplar")
                print("ej:" + vj)
                #print("IMAGEN:" + imagen)
                estado = request.form.get("estado")
                #imagen = request.form.get("imagen")
                comentario = request.form.get("comentario")
                publicar = str(request.form.get("publicar"))
                print("publicar:" + publicar)
                if publicar is not "1":
                    publicar = 0
                print("publicar:" + str(publicar))

                msg = funCargarEjemplar(email, usrid, vj, estado, publicar, comentario, imagen)
                ejeblk, ejepub, ejenopub = funListarEjemplaresUsuario(usrid)
                return render_template('ejemplaresusuario.html', mensaje="!", vjblk=ejeblk,
                                       vjpub=ejepub, vjnopub=ejenopub, logged=0)
            else:
                return render_template('login.html', mensaje="oopppss...algo sucedió con tu sesión. Ingresa de nuevo!")
        return render_template('cargarejemplar.html', mensaje="Carga tu ejemplar!", videojuegos=lista)

    return render_template('cargarejemplar.html', mensaje="Carga tu ejemplar!", videojuegos=lista)


# Funcion: Editar un ejemplar
@app.route("/editarEjemplar/<int:idejeusuario>", methods=["GET", "POST"])
def editarEjemplar(idejeusuario):

    if request.method == "GET":
        obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejeusuario).first()
        obVideojuego = db.session.query(VideoJuego).filter_by(idVj=obEjeUsuario.vjId).first()
        obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=obEjeUsuario.idEjeUsuario, activa=1).first()

        foto = base64.b64encode(obFoto.foto).decode("utf-8")

        return render_template('editarejemplar.html', mensaje="Edita el videojuego!", ejidejeusuario=idejeusuario, ejimagen=foto, ejnombre=obVideojuego.nombre, ejestado=obEjeUsuario.estado, ejcomentario=obEjeUsuario.comentario, ejpublicar=obEjeUsuario.publicado)

    elif request.method == "POST":
        if session is not None:
            if request.form['btnejemplar'] == 'Editar':
                print("email:" + email)
                obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
                if obUsuario is not None:
                    usrid = obUsuario.idUsuario
                    imagen = request.files["imgInp"]
                    vj = request.form.get("ejemplar")
                    print("ej:" + vj)
                    #print("IMAGEN:" + imagen)
                    estado = request.form.get("estado")
                    #imagen = request.form.get("imagen")
                    comentario = request.form.get("comentario")
                    publicar = str(request.form.get("publicar"))
                    print("publicar:" + publicar)
                    if publicar is not "1":
                        publicar = 0
                    print("publicar:" + str(publicar))

                    msg = funCargarEjemplar(email, usrid, vj, estado, publicar, comentario, imagen)
                    return render_template('inicio.html', mensaje=msg, logged=1)
                else:
                    return render_template('login.html', mensaje="oopppss...algo sucedió con tu sesión. Ingresa de nuevo!")
            if request.form['btnejemplar'] == 'Cancelar':
                ejemplaresusuario()

def _send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except SMTPException:
            app.logger.exception("Ocurrió un error al enviar el email")
            raise


@app.route('/ejemplaresusuario', methods=["GET", "POST"])
def ejemplaresusuario():
    ejeblk = []
    ejepub = []
    ejenopub = []
    if request.method=="GET":
        app.logger.debug("[NO_USER] index: inicia ejemplaresusuario")
        if not(session) or (session['email'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")

            return render_template('ejemplaresusuario.html', mensaje="Registrate y disfruta!", vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=0)
        else:
            if db.session is not None:
                # Recupera listado de ejemplares
                email = session['email']
                usuario = db.session.query(Usuario).filter_by(email=email).first()
                ejeblk, ejepub, ejenopub = funListarEjemplaresUsuario(usuario.idUsuario)
                ejemplares = len(ejeblk) + len(ejepub) + len(ejenopub)
                app.logger.debug("["+email+"] index: Hay sesion")
                app.logger.debug("["+email+"] Encontró "+ejemplares.__str__()+" ejemplares para el usuario [" + email + "]")
                #print(lista)

                return render_template('ejemplaresusuario.html', mensaje="Bienvenido "+email, vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=1)

    if request.method=="POST":
        app.logger.debug("[NO_USER] index: inicia ejemplaresusuario")
        if not(session) or (session['email'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")

            return render_template('ejemplaresusuario.html', mensaje="Registrate y disfruta!", vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=0)
        else:
            if db.session is not None:
                # Recupera listado de ejemplares
                email = session['email']
                usuario = db.session.query(Usuario).filter_by(email=email).first()

                idejemplar = request.form.get('idejemplar')
                print('ejemplar ' + idejemplar)
                if request.form['btnejemplar'] == 'editar':
                    return render_template('editarejemplar.html', ejidejeusuario=idejemplar)
                elif request.form['btnejemplar'] == 'despublicar':
                    funMarcarEjemplaresUsuario(email,idejemplar,0)
                    print('despublicar ' + idejemplar)
                elif request.form['btnejemplar'] == 'publicar':
                    funMarcarEjemplaresUsuario(email,idejemplar,1)
                    print('publicar ' + idejemplar)

                ejeblk, ejepub, ejenopub = funListarEjemplaresUsuario(usuario.idUsuario)

    return render_template('ejemplaresusuario.html', mensaje="Bienvenido "+session['email'], vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=0)


@app.route('/solicitarejemplar', methods=["GET", "POST"])
def solicitarejemplar():
    ejeblk = []
    ejepub = []
    ejenopub = []
    if request.method=="GET":
        app.logger.debug("[NO_USER] index: inicia ejemplaresusuario")
        if not(session) or (session['email'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")

            return render_template('ejemplaresusuario.html', mensaje="Registrate y disfruta!", vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=0)
        else:
            if db.session is not None:
                # Recupera listado de ejemplares
                email = session['email']
                usuario = db.session.query(Usuario).filter_by(email=email).first()
                ejeblk, ejepub, ejenopub = funListarEjemplaresUsuario(usuario.idUsuario)
                ejemplares = len(ejeblk) + len(ejepub) + len(ejenopub)
                app.logger.debug("["+email+"] index: Hay sesion")
                app.logger.debug("["+email+"] Encontró "+ejemplares.__str__()+" ejemplares para el usuario [" + email + "]")
                #print(lista)

                return render_template('ejemplaresusuario.html', mensaje="Bienvenido "+email, vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=1)


# Funcion: terminos y condiciones
@app.route("/terminos", methods=["GET"])
def terminos():
    return render_template('terminos.html')

# Funcion: Actualizar datos usuario
@app.route("/updateUser", methods=["GET", "POST"])
def updateUser():
    # creating a map in the view
    map = Map(
        identifier="view-side",
        lat=37.4419,
        lng=-122.1419,
        markers=[(37.4419, -122.1419)]
    )

    datosUsuario = None
    if request.method == "GET":
        if not(session) or (session['nick'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")

            return render_template('home_page.html', mensaje="Inicia Sesión o Registrate y disfruta!")
        else:
            if db.session is not None:
                nick = session['nick']
                usuario = db.session.query(Usuario).filter_by(nickName=nick).first()
                datosUsuario = funObtenerDatosUsuario(usuario.idUsuario)
                datosUsuario.fechanac = datosUsuario.fechanac.strftime("%Y-%m-%d")

    if request.method == "POST":
        if not(session) or (session['nick'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")
            return render_template('home_page.html', mensaje="Inicia Sesión o Registrate y disfruta!")
        else:
            if session is not None:
                nick = session['nick']
                print("nick:" + nick)
                obUsuario = db.session.query(Usuario).filter_by(nickName=nick).one_or_none()
                if obUsuario is not None:
                    usrid = obUsuario.idUsuario
                    imagen = request.files["imgInp"]
                    nombres = request.form.get("nombres")
                    apellidos = request.form.get("apellidos")
                    edad = request.form.get("edad")
                    genero = request.form.get("genero")
                    fechanac = request.form.get("fecha")
                    celular = request.form.get("celular")

                    funUpdateDatosUsuario(usrid,nombres,apellidos,edad,fechanac,genero)


    return render_template('act_datos_usuario.html', usuario=datosUsuario, map=map)

if __name__ == '__main__':
    app.logger.debug("[NO_USER] main: **************************************************")
    app.logger.debug("[NO_USER] main: Importa configuracion")
    mail.init_app(app)
    app.logger.debug("[NO_USER] main: Inicializa DB")
    db.init_app(app)
    app.logger.debug("[NO_USER] main: Crea la BD")

    with app.app_context():
        db.create_all()
    app.logger.debug("[NO_USER] main: Run aplicacion 8000")
    #DESARROLLO
    app.run(port=8000)
    #PRODUCCION
    #app.run(port=80)

