from smtplib import SMTPException
from flask_mail import Mail, Message
from threading import Thread
from flask import Flask, request, redirect, render_template, session, current_app, url_for
from config import ProductionConfig, DevelopmentConfig, Config
from datamodel import db, Usuario, ConexionUsuario, VideoJuego, EjeUsuario, FotoEjeUsuario, BusquedaUsuario
from operavideojuegos import funCargarEjemplar, funListarEjemplaresUsuario, funMarcarEjemplaresUsuario, \
    funListarEjemplaresDisponibles, funEditarEjemplar, funListarNombresVJ
from passlib.hash import sha256_crypt
import logging
from sqlalchemy.exc import IntegrityError
import base64
from datetime import datetime, timedelta

app = Flask(__name__)

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
URL_CAMBIACLAVE = "http://127.0.0.1:8000/nuevaclave?"
# PRODUCCION
# URL_CONFIRMA = "http://www.ex4play.com/confirma?"
# URL_APP = "http://www.ex4play.com/"
# URL_CAMBIACLAVE = "http://www.ex4play.com/nuevaclave?"

urlapp =  "http://www.ex4play.com/"

hoy = datetime.today()
# PRODUCCION
# LOG_FILENAME = 'ex4playpy/tmp/errores'+hoy.strftime("%Y-%m-%d")+'.log'
# DESARROLLO
LOG_FILENAME = 'tmp\errores'+hoy.strftime("%Y-%m-%d")+'.log'

app.config['MAIL_SERVER'] = 'p3plcpnl1009.prod.phx3.secureserver.net'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "ex4play@baisica.co"
app.config['MAIL_PASSWORD'] = 'JuSo2015@'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
SUBJECT_REGISTRO = "Bienvenido a ex4play {nick} !"
SUBJECT_CAMBIACLAVE = "Enlace para cambio de clave {nick} !"
SUBJECT_CLAVECAMBIADA = "Tu clave se cambió con exito {nick} !"

logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

app.config['SQLALCHEMY_POOL_RECYCLE'] = 299

# PRODUCCION - ESTE CODIGO SE HABILITA EN PRODUCCION
mail = Mail(app)
#mail.init_app(app)
#db.init_app(app)

# Variable global de nombres
g_nombres = []


# Funcion: index
# La pagina principal debe tener todos los accesos y mostrar todos los juegos en la plataforma
@app.route('/', methods=["POST","GET"])
def index():
    videojuegos = []
    novedades = []
    g_nombres = funListarNombresVJ()
    #print("la lista:")
    #for reg in g_nombres:
    #    print(reg)
    if request.method == "GET":
        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: inicia index")
        if db.session is not None:
            # Recupera listado de videojuegos generales
            result = funListarEjemplaresDisponibles(1)
            for reg in result:
                videojuegos.append(reg)

            # Recupera listado de ejemplares existentes en la plataforma
            result = funListarEjemplaresDisponibles(0)
            for reg in result:
                novedades.append(reg)

        if not(session) or (session['email'] is None):
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: No hay sesion")
            return render_template('home_page.html', mensaje="Registrate y disfruta!", videojuegos=videojuegos, novedades=novedades, logged=0, lista=g_nombres)
        else:
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+session['email']+"] index: Hay sesion")

        print("index: cantidad de registros de VJ" + str(len(g_nombres)))
        return render_template('inicio.html', mensaje="Bienvenido "+session['email'], videojuegos=videojuegos, novedades=novedades, logged=1, lista=g_nombres)


# Funcion: buscar
# Busca y presenta resultados en la página principal
@app.route('/buscar', methods=["POST", "GET"])
def buscar():
    videojuegos = []
    novedades = []
    if request.method == "POST":
        buscar = request.form.get("busqueda")
        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: Entra a buscar por el POST de inicio")
        if db.session is not None:
            # Recupera listado de videojuegos generales
            result = funListarEjemplaresDisponibles(1, buscar)
            for reg in result:
                videojuegos.append(reg)

            # Recupera listado de ejemplares existentes en la plataforma
            result = funListarEjemplaresDisponibles(0, buscar)
            for reg in result:
                novedades.append(reg)

        if not(session) or (session['email'] is None):
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: No hay sesion")
            return render_template('home_page.html', mensaje="Registrate y disfruta!", videojuegos=videojuegos, novedades=novedades, logged=0)
        else:
            numreg = len(novedades) + len(videojuegos)
            obUsuario = db.session.query(Usuario).filter_by(email=session['email']).one_or_none()
            newBusUsuario = BusquedaUsuario(usuarioId=obUsuario.idUsuario, busqueda=buscar, resultados=numreg)
            db.session.add(newBusUsuario)
            db.session.commit()

            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+session['email']+"] index: Hay sesion")

        print("buscar: cantidad de registros de VJ" + str(len(g_nombres)))
        return render_template('inicio.html', mensaje="Bienvenido "+session['email'], videojuegos=videojuegos, novedades=novedades, logged=1, lista=g_nombres)


# Funcion: login
@app.route("/login", methods=["POST","GET"])
def login():
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] login: inicia login")
    email=""
    g_nombres = funListarNombresVJ()
    if request.method == "POST":
        try:
            email = str(request.form.get("email")).lower()
            pwdorig = str(request.form.get("clave"))
            idnick = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(pwdorig)
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] login: Datos del usuario ingresado: email[" + email + "]")
            #app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"login: Datos del usuario ingresado: email[" + email + "], pwd[" + idnick + "], pwdorg["+pwdorig+"]")
            #app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[email: " + email + "] - [sesion: " + str(session['email']) + "]")

            #usuarioValido = db.session.query(Usuario.email, Usuario.pwd).filter_by(email=email,
            #                                                                          pwd=idnick).scalar() is not None

            obUsuario = db.session.query(Usuario).filter_by(email=email, pwd=idnick).one_or_none()

            #if usuarioValido == True:
            if obUsuario is not None:
                if not((not session) or (not email in session['email'])): #Si hay una sesion activa
                    # Si existe el usuario, pero es inactivo, debe remitirse al mail
                    if obUsuario.activo == ESTADO_USR_INACTIVO:
                        print("login: cantidad de registros de VJ" + str(len(g_nombres)))
                        return render_template('inicio.html', mensaje=email+", debes confirmar tu registro en tu correo para poder ingresar!", logged=0)
                    else:
                        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] login: Hay una sesion")
                        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] login: Usuario a ingresar con sesion recuperada: " + email)

                        #print("LOGIN pwdorig " + pwdorig)

                        #Crea el registro de seguimiento a las conexion - IP ConexionUsuario
                        newConnUsuario = ConexionUsuario(usuarioId=obUsuario.idUsuario, ipaddr=request.remote_addr)
                        db.session.add(newConnUsuario)
                        db.session.commit()

                        videojuegos=[]
                        novedades=[]
                        # Recupera listado de videojuegos generales
                        result = funListarEjemplaresDisponibles(1)
                        for reg in result:
                            videojuegos.append(reg)

                        # Recupera listado de ejemplares existentes en la plataforma
                        result = funListarEjemplaresDisponibles(0)
                        for reg in result:
                            novedades.append(reg)

                        print("login: cantidad de registros de VJ" + str(len(g_nombres)))
                        return render_template('inicio.html', mensaje="Ya estabas logueado " + email, videojuegos=videojuegos, novedades=novedades, logged=1, lista=g_nombres)
                else:
                    #Revisa si el usuario está activo o inactivo
                    if obUsuario.activo == ESTADO_USR_INACTIVO:
                        return render_template('home_page.html', confirmarusr=1, url_confirma=URL_APP+"/reenviarconf" ,accion=email+"No has confirmado tu correo, clic aquí para reenviarte el correo de registro! ", logged=0)
                    else:
                        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] login: No hay sesion")

                        session['email'] = email
                        session['idnick'] = idnick

                        #print("LOGIN email " + email)

                        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] login: Sesion generada: " + email)

                        # Crea el registro de seguimiento a las conexion - IP ConexionUsuario
                        newConnUsuario = ConexionUsuario(usuarioId=obUsuario.idUsuario, ipaddr=request.remote_addr)

                        db.session.add(newConnUsuario)
                        db.session.commit()

                        videojuegos=[]
                        novedades=[]
                        # Recupera listado de videojuegos generales
                        result = funListarEjemplaresDisponibles(1)
                        for reg in result:
                            videojuegos.append(reg)

                        # Recupera listado de ejemplares existentes en la plataforma
                        result = funListarEjemplaresDisponibles(0)
                        for reg in result:
                            novedades.append(reg)

                        print("login: cantidad de registros de VJ" + str(len(g_nombres)))
                        return render_template('inicio.html', mensaje="Bienvenido al sistema "+email+"!", videojuegos=videojuegos, novedades=novedades, logged=1, lista=g_nombres)
            else:
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] Usuario o password inválido. Intenta de nuevo!")
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
            email = email.lower()
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
    email=""
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] registro: inicia registro")
    if request.method == "POST":
        try:
            nombres = request.form.get("nombres")
            apellidos = request.form.get("apellidos")
            email = request.form.get("email").lower()
            clave = request.form.get("clave")
            aceptater = request.form.get("aceptat") # Acepta los términos
            recibenot = request.form.get("recibir") # Acepta recibir notificaciones
            pwdseguro = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(clave))
            nickname = email
            newUsuario = Usuario(nombres=nombres, apellidos=apellidos, pwd=pwdseguro, email=email, nickName=nickname, aceptater=aceptater, recibenot=recibenot)
            db.session.add(newUsuario)
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] registro: Usuario adicionado a BD: " + newUsuario.nombres + " - mail - " + newUsuario.email)
            urlconfirma = URL_CONFIRMA +"usr=" + email + "&id=" + sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(email+pwdseguro))
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] registro: armó urlconfirma: " + urlconfirma)

            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] registro: va a enviar correo")
            subject = SUBJECT_REGISTRO.format(nick=nombres)

            if enviar_correo(subject, app.config['MAIL_USERNAME'], email, text_body=None, template="mailbienvenida.html", nick=email, urlconfirma=urlconfirma, urlapp=urlapp) == 1:
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + nickname + "] registro: envió mail a : " + newUsuario.nombres + " - mail - " + newUsuario.email)

                #***************************************
                #Manejo de clave duplicada en la inserción del usuario
                try:
                    db.session.commit()
                    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+
                        "[" + email + "] registro: Usuario registrado: " + newUsuario.nombres + " - mail - " + newUsuario.email)
                    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+
                        "registro: Usuario registrado: " + newUsuario.nombres + " - mail - " + newUsuario.email + " " + clave + " " + pwdseguro)
                except IntegrityError as e:

                    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] registro: Repetido")

                    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"%s Ya esta registrado.")
                    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] registro: %s Ya esta registrado." % e.params[0])
                    db.session.rollback()
                    return render_template('resetclave.html',
                                       mensaje="Ya existe un registro para " + email + ". Recupera tu clave!")

                #***************************************
            return render_template('registro.html', mensaje="Ya estás registrado " + newUsuario.nombres + ". Confirma en tu correo para finalizar!")
        except:
            app.logger.error("[" + email + "] registro: Error con usuario a registrar ")
            raise
            #return render_template('error.html', mensaje="Error en registro!")
    return render_template('registro.html', mensaje="" )

# Funcion: reenviar correo confirmacion
@app.route("/reenviarconf", methods=["POST", "GET"])
def reenviarconf():
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] reenviar mail: inicia reenviar mail confirmacion")
    pwdseguro = ""
    email = ""
    if request.method == "POST":
        try:
            email = request.form.get("email").lower()
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            if obUsuario is not None:
                pwdseguro = obUsuario.pwd
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] reenviar mail: Usuario adicionado a BD: " + obUsuario.nombres + " - mail - " + obUsuario.email)
                urlconfirma = URL_CONFIRMA +"usr=" + email + "&id=" + sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(email+pwdseguro))
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] reenviar mail: armó urlconfirma: " + urlconfirma)

                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] reenviar mail: va a enviar correo")
                subject = SUBJECT_REGISTRO.format(nick=obUsuario.nombres)

                if enviar_correo(subject, app.config['MAIL_USERNAME'], email, text_body=None, template="mailbienvenida.html", nick=email, urlconfirma=urlconfirma, urlapp=urlapp) == 1:
                    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] reenviar mail: envió mail a : " + obUsuario.nombres + " - mail - " + obUsuario.email)
                    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"reenviar mail: Usuario registrado: " + obUsuario.nombres + " - mail - " + obUsuario.email + " " + pwdseguro)
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
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] confirma: inicia confirmación ")
    email = ""
    if request.method == "GET":
        try:
            email = request.args.get("usr").lower()
            id = request.args.get("id")

            #Busca el usuario para validar
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] confirma: Usuario a confirmar: " + email)
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()

            if obUsuario is not None:
                if obUsuario.activo == ESTADO_USR_ACTIVO:
                    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+
                        "[" + email + "] confirma: Usuario YA estaba activo: " + obUsuario.nombres + " - mail - " + obUsuario.email)
                    return render_template('login.html', mensaje="El enlace ya no funciona, pero ya estás activo " + obUsuario.nombres + ". Ingresa!")
                else:
                    pwd= obUsuario.pwd
                    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] confirma: Usuario recuperado: " + email+pwd )

                    idvalida = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(email+pwd))

                    if idvalida==id:
                        obUsuario.activo = ESTADO_USR_ACTIVO
                        db.session.commit()
                        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] confirma: Usuario activo: " + obUsuario.nombres + " - mail - " + obUsuario.email)
                        return render_template('login.html', mensaje="Ya estás activo " + obUsuario.nombres + ". Ingresa!")
                    else:
                        return render_template('error.html', mensaje="Hubo un error " + obUsuario.nombres + ". Vuelve a intentarlo desde tu correo!")
            else:
                return render_template('registro.html',
                                       mensaje="El usuario " + email + ", no se encuentra registrado. Regístrate antes!")
        except:
            app.logger.error("[" + email + "] confirma: Usuario a confirmar: " + email)
            #return render_template('error.html', mensaje="Error en confirmación!")
            raise
    return render_template('login.html', mensaje= "Ingresa al sistema!")


# Funcion: reset clave
@app.route("/resetclave", methods=["POST", "GET"])
def resetclave():
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] reset clave: inicia reset clave ")
    email = ""
    if request.method == "POST":
        try:
            email = request.form.get('email').lower()
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            fechacrea = str(obUsuario.fechacrea)
            subject = SUBJECT_CAMBIACLAVE.format(nick=obUsuario.nombres)
            iduser = fechacrea+email+obUsuario.pwd

            urlcambiarclave = URL_CAMBIACLAVE + "usr=" + email + "&id=" + sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(iduser)

            if enviar_correo(subject, app.config['MAIL_USERNAME'], email, text_body=None, template="mailcambioclave.html", nick=email, urlconfirma=urlcambiarclave, urlapp=urlapp) == 1:
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + email + "] registro: envió mail a : " + obUsuario.nombres + " - mail - " + obUsuario.email)

                return render_template('login.html', mensaje="Revisa tu correo para continuar el cambio de clave  " + obUsuario.nombres + "!")
            else:
                return render_template('registro.html',
                                       mensaje="El usuario " + email + ", no se encuentra registrado. Regístrate antes!")
        except:
            #raise
            app.logger.error("[" + email + "] confirma: Usuario a confirmar: " + email)
            return render_template('error.html', mensaje="Error en confirmación!")
    return render_template('resetclave.html', mensaje="")

# Funcion: nueva clave
# En el correo de confirmación viene un enlace que lanza la pantalla de cambio de clave
@app.route("/nuevaclave", methods=["POST", "GET"])
def nuevaclave():
    email = ""
    try:
        if request.method == "GET":
            email = request.args.get("usr").lower()
            id = request.args.get("id")

            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "["+email+"] nueva clave: inicia nueva clave ")
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            fechacrea = str(obUsuario.fechacrea)

            iduser = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(fechacrea + email + obUsuario.pwd)

            #print("id:" + id)
            #print("iduser:" + iduser)
            #print("email:" + email)
            subject = SUBJECT_CLAVECAMBIADA.format(nick=obUsuario.nombres)

            if id == iduser:
                app.logger.info(
                    datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[" + email + "] nueva clave: va a enviar correo ")
                enviar_correo(subject, app.config['MAIL_USERNAME'], email, text_body=None,
                                 template="mailclavecambiada.html", nick=email, urlapp=urlapp)
                return render_template('nuevaclave.html', mensaje="Asigna una nueva clave  " + obUsuario.nombres + "!", email=email)
            else:
                return render_template('resetclave.html', mensaje=obUsuario.nombres+", El enlace ya no es válido. Intenta solicitarlo de nuevo!")

        if request.method == "POST":
            email = request.form.get("email").lower()
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "["+email+"] nueva clave: recupera info del usuario")
            clave = request.form.get("clave1")
            pwdseguro = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(clave))

            obUsuario = db.session.query(Usuario).filter_by(email=email).update(dict(pwd=pwdseguro))
            db.session.commit()
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "["+email+"] nueva clave: la clave nueva se guardó")

            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            nombres = obUsuario.nombres
            return render_template('login.html',
                                   mensaje="La clave fue cambiada " + nombres + "! Ingresa tus credenciales.")

    except:
          raise
          app.logger.error("[" + email + "] confirma: Usuario a confirmar: " + email)
          return render_template('error.html', mensaje="Error en confirmación!")


# Funcion: enviar_correo
def enviar_correo(subject, sender, recipients, text_body,
                  cc=None, bcc=None, html_body=None, template=None, **kwargs):
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + recipients + "] enviar_correo: Inicia ")
    try:
        #f or key, value in kwargs.items():
        #    print("The value of {} is {}".format(key, value))

        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[" + recipients + "] va enviar_correo: SEND ")

        #envía copia al usuario que envía
        msg = Message(subject, sender=sender, recipients=[recipients, ], cc=cc, bcc=bcc)
        msg.html = render_template(template, **kwargs)
        msg.body = render_template(template, **kwargs)

        mail.send(msg)
        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[CORREO A: " + recipients.lower() + "] Envió correo")
        #thr1 = Thread(target=_send_async_email, args=(current_app._get_current_object(), msg))
        #thr1.start()
        #app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[CORREO A: " + recipients.lower() + "] Generó tarea para enviar ")

        msg = Message(subject, sender=sender, recipients=[sender, ], cc=cc, bcc=bcc)
        msg.html = render_template(template, **kwargs)
        msg.body = render_template(template, **kwargs)

        mail.send(msg)
        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[CORREO A: " + recipients.lower() + "] Envió correo")
        #thr2 = Thread(target=_send_async_email, args=(current_app._get_current_object(), msg))
        #thr2.start()
        #app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[CORREO A: " + sender.lower() + "] Generó tarea para enviar ")
        return 1
    except SMTPException:
        app.logger.error("[NO_USER] enviar_correo: error en enviar correo " + sender)
        #raise
        return 0


def _send_async_email(app, msg):
    with app.app_context():
        try:
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"_send_async_email ENVIARÁ MAIL")
            mail.send(msg)
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"_send_async_email ENVIÓ MAIL")
        except SMTPException:
            app.logger.exception("Ocurrió un error al enviar el email")
            raise


# Funcion: Dar de Baja Usuario
@app.route("/bajausuario", methods=["GET", "POST"])
def bajausuario():
    if request.method == "POST":
        if session is not None:
            email = session['email']
            email = email.lower()
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
            email = email.lower()
            print("email:" + email)
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            if obUsuario is not None:
                usrid = obUsuario.idUsuario
                imagen = request.files["imgInp"]

                vj = request.form.get("ejemplar")
                print("ej:" + vj)

                estado = request.form.get("estado")

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
    email = session['email']
    email = email.lower()

    print("El metodo = " + request.method + " - email " + email)

    if request.method == "GET":
        obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejeusuario).first()
        obVideojuego = db.session.query(VideoJuego).filter_by(idVj=obEjeUsuario.vjId).first()
        obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=obEjeUsuario.idEjeUsuario, activa=1).first(),

        foto = base64.b64encode(obFoto.foto).decode("utf-8")

        print("ejidejeusuario"+str(idejeusuario)+" -- ejimagen=" + foto + "--ejnombre=" + obVideojuego.nombre + "--ejestado= "+ str(obEjeUsuario.estado) + "--ejcomentario="+obEjeUsuario.comentario+"ejpublicar="+str(obEjeUsuario.publicado))
        return render_template('editarejemplar.html', mensaje="Edita el videojuego!", ejidejeusuario=idejeusuario, ejimagen=foto, ejnombre=obVideojuego.nombre, ejestado=obEjeUsuario.estado, ejcomentario=obEjeUsuario.comentario, ejpublicar=obEjeUsuario.publicado, editar=1)

    elif request.method == "POST":
        print("Entra al POST: " + email)
        if request.form['btnejemplar'] == 'Guardar':
            print("Guardará para el email:" + email)
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            if obUsuario is not None:

                print("ejeusuario:" + str(idejeusuario))
                usrid = obUsuario.idUsuario
                print("usr:" + str(usrid))
                imagen = request.files["imgInp"]
                vj = request.form.get("ejemplar")
                print("ej:" + str(vj))
                #print("IMAGEN:" + imagen)
                estado = request.form.get("estado")
                #imagen = request.form.get("imagen")
                comentario = request.form.get("comentario")

                msg = funEditarEjemplar(idejeusuario, email, estado, comentario, imagen)
                #return render_template('ejemplaresusuario.html', mensaje=msg, logged=1)
                return redirect(url_for('ejemplaresusuario'))
            else:
                return redirect(url_for('ejemplaresusuario'))
        if request.form['btnejemplar'] == 'Cancelar':
            return redirect(url_for('ejemplaresusuario'))


@app.route('/ejemplaresusuario', methods=["GET", "POST"])
def ejemplaresusuario():
    ejeblk = []
    ejepub = []
    ejenopub = []
    if request.method=="GET":
        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: inicia ejemplaresusuario")
        if not(session) or (session['email'] is None):
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: No hay sesion")

            return render_template('ejemplaresusuario.html', mensaje="Registrate y disfruta!", vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=0)
        else:
            if db.session is not None:
                # Recupera listado de ejemplares
                email = session['email']
                email = email.lower()
                usuario = db.session.query(Usuario).filter_by(email=email).first()
                ejeblk, ejepub, ejenopub = funListarEjemplaresUsuario(usuario.idUsuario)
                ejemplares = len(ejeblk) + len(ejepub) + len(ejenopub)
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+email+"] index: Hay sesion")
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+email+"] Encontró "+ejemplares.__str__()+" ejemplares para el usuario [" + email + "]")
                #print(lista)

                return render_template('ejemplaresusuario.html', mensaje="Bienvenido "+email, vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=1)

    if request.method=="POST":
        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: inicia ejemplaresusuario")
        if not(session) or (session['email'] is None):
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: No hay sesion")

            return render_template('ejemplaresusuario.html', mensaje="Registrate y disfruta!", vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=0)
        else:
            if db.session is not None:
                # Recupera listado de ejemplares
                email = session['email']
                email = email.lower()
                usuario = db.session.query(Usuario).filter_by(email=email).first()

                idejemplar = request.form.get('idejemplar')
                print('EJEMPLARESUSUARIO: ejemplar ' + str(idejemplar))
                if request.form['btnejemplar'] == 'editar':
                    print('EJEMPLARESUSUARIO: Editar el ejemplar: ' + str(idejemplar))
                    obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejemplar).first()
                    obVideojuego = db.session.query(VideoJuego).filter_by(idVj=obEjeUsuario.vjId).first()
                    obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=obEjeUsuario.idEjeUsuario,
                                                                        activa=1).first()

                    foto = base64.b64encode(obFoto.foto).decode("utf-8")

                    print("ejidejeusuario" + str(idejemplar) + " -- ejimagen=" + foto + "--ejnombre=" + obVideojuego.nombre + "--ejestado= " + str(obEjeUsuario.estado) + "--ejcomentario=" + obEjeUsuario.comentario + "ejpublicar=" + str(obEjeUsuario.publicado))
                    return render_template('editarejemplar.html', mensaje="Edita el videojuego!",
                                           ejidejeusuario=idejemplar, ejimagen=foto, ejnombre=obVideojuego.nombre,
                                           ejestado=obEjeUsuario.estado, ejcomentario=obEjeUsuario.comentario,
                                           ejpublicar=obEjeUsuario.publicado,editar=1)
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
        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: inicia ejemplaresusuario")
        if not(session) or (session['email'] is None):
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: No hay sesion")

            return render_template('ejemplaresusuario.html', mensaje="Registrate y disfruta!", vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=0)
        else:
            if db.session is not None:
                # Recupera listado de ejemplares
                email = session['email']
                usuario = db.session.query(Usuario).filter_by(email=email).first()
                ejeblk, ejepub, ejenopub = funListarEjemplaresUsuario(usuario.idUsuario)
                ejemplares = len(ejeblk) + len(ejepub) + len(ejenopub)
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+email+"] index: Hay sesion")
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+email+"] Encontró "+ejemplares.__str__()+" ejemplares para el usuario [" + email + "]")
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
        if not(session) or (session['email'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")

            return render_template('home_page.html', mensaje="Inicia Sesión o Registrate y disfruta!")
        else:
            if db.session is not None:
                nick = session['email']
                usuario = db.session.query(Usuario).filter_by(nickName=nick).first()
                datosUsuario = funObtenerDatosUsuario(usuario.idUsuario)
                datosUsuario.fechanac = datosUsuario.fechanac.strftime("%Y-%m-%d")

    if request.method == "POST":
        if not(session) or (session['email'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")
            return render_template('home_page.html', mensaje="Inicia Sesión o Registrate y disfruta!")
        else:
            if session is not None:
                nick = session['email']
                print("email:" + nick)
                obUsuario = db.session.query(Usuario).filter_by(email=nick).one_or_none()
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
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] main: **************************************************")
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] main: Importa configuracion")
    mail.init_app(app)
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] main: Inicializa DB")
    db.init_app(app)
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] main: Crea la BD")

    with app.app_context():
        db.create_all()
    app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] main: Run aplicacion 8000")
    #DESARROLLO
    app.run(port=8000)
    #PRODUCCION
    #app.run(port=80)

