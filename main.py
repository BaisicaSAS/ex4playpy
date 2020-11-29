from passlib.hash import sha256_crypt
import logging
from sqlalchemy.exc import IntegrityError
import base64
from datetime import datetime, timedelta
from smtplib import SMTPException
from flask_mail import Mail, Message
from threading import Thread
from flask import Flask, request, redirect, render_template, session, current_app, url_for
from config import ProductionConfig, DevelopmentConfig, Config
from datamodel import db, Usuario, ConexionUsuario, VideoJuego, EjeUsuario, FotoEjeUsuario, BusquedaUsuario, \
    Transaccion, DetalleTrx, DetalleLugar, DetalleValor, DetalleValorOtros, QyA, FotoUsuario, Saldos
from operavideojuegos import funCargarEjemplar, funListarEjemplaresUsuario, funMarcarEjemplaresUsuario, \
    funListarEjemplaresDisponibles, funEditarEjemplar, funListarNombresVJ, funObtenerDatosUsuario, \
    funUpdateDatosUsuario, funPuntosDisponiblesUsuario, funCrearTransaccion, \
    funListarSaldosUsuarios, funListarNuevosJuegos, funCambiarJuego, funListarJuegosValorizar, \
    funReclasifica, C_TRXACTIVA, funListarUsuariosAdmin, funEditarUsuariosAdmin, funUpdateDatosUsuario, \
    funPuntosDisponiblesUsuario, funCrearTransaccion, funcObtenerCiudades, funcCrearUpdateQA, funListarEnviosPendientes, \
    funEntregaroRecibir

from imagen import IMG_USR

app = Flask(__name__)

# DESARROLLO
app.config.from_object(DevelopmentConfig)
# PRODUCCION
# app.config.from_object(ProductionConfig)

# C 0 N S T A N T E S
ESTADO_USR_INACTIVO = 0  # Si el usuario está inactivo
ESTADO_USR_ACTIVO = 1  # Si el usuario está activo
ESTADO_USR_SANCIO = 1  # Si el usuario está sancionado
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
#github
app.config['MAIL_PASSWORD'] = 'p3plcpnl1009@Ju$o2020@103466'
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
@app.route('/', methods=["POST", "GET"])
def index():
    try:
        videojuegos = []
        novedades = []
        # print("la lista de nombres")
        g_nombres = funListarNombresVJ()
        # for reg in g_nombres:
        #    print(reg)
        if request.method == "GET":
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[NO_USER] index: inicia index")
            if not (session) or (session['email'] is None):
                app.logger.info("[NO_USER] GET::index inicia")
                # print("[NO_USER] GET::index inicia")
                # Recupera listado de videojuegos generales
                result = funListarEjemplaresDisponibles(1)
                for reg in result:
                    videojuegos.append(reg)

                # Recupera listado de ejemplares existentes en la plataforma
                result = funListarEjemplaresDisponibles(0)
                for reg in result:
                    novedades.append(reg)

                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[NO_USER] index: No hay sesion")
                return render_template('home_page.html', mensaje="Registrate y disfruta!", videojuegos=videojuegos,
                                       novedades=novedades, logged=0, lista=g_nombres)
            else:
                app.logger.info(
                    datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[" + session['email'] + "] index: Hay sesion")
                app.logger.info("[NO_USER] GET::index inicia")
                # print("[NO_USER] GET::index inicia")
                # Recupera listado de videojuegos generales
                # print("index: cantidad de registros de VJ " + str(len(g_nombres)))
                usuario = db.session.query(Usuario).filter_by(email=session['email']).first()
                result = funListarEjemplaresDisponibles(1, idusuario=usuario.idUsuario)
                for reg in result:
                    videojuegos.append(reg)

                # Recupera listado de ejemplares existentes en la plataforma
                result = funListarEjemplaresDisponibles(0, idusuario=usuario.idUsuario)
                for reg in result:
                    novedades.append(reg)

                return render_template('inicio.html', usuario=usuario.nickName,
                                       mensaje="Bienvenido " + session['email'], videojuegos=videojuegos,
                                       novedades=novedades, logged=1, lista=g_nombres,
                                       puntosusu=funPuntosDisponiblesUsuario(usuario.idUsuario))
    except:
        raise


# Funcion: buscar
# Busca y presenta resultados en la página principal
@app.route('/buscar', methods=["POST", "GET"])
def buscar():
    videojuegos = []
    novedades = []
    if request.method == "POST":
        palabrabuscar = request.form.get("busqueda")
        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: Entra a buscar por el POST de inicio")

        if not(session) or (session['email'] is None):
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] index: No hay sesion")
            #print("[NO_USER] GET::buscar inicia")
            #Recupera listado de videojuegos generales
            result = funListarEjemplaresDisponibles(1, palabrabuscar)
            for reg in result:
                videojuegos.append(reg)

            # Recupera listado de ejemplares existentes en la plataforma
            result = funListarEjemplaresDisponibles(0, palabrabuscar)
            for reg in result:
                novedades.append(reg)

            return render_template('home_page.html', mensaje="Registrate y disfruta!", videojuegos=videojuegos, novedades=novedades, logged=0)
        else:
            obUsuario = db.session.query(Usuario).filter_by(email=session['email']).one_or_none()
            #print("Buscar Usuario: " + str(obUsuario.idUsuario))
            # Recupera listado de videojuegos generales
            result = funListarEjemplaresDisponibles(1, idusuario=obUsuario.idUsuario, palabrabuscar=palabrabuscar)
            for reg in result:
                videojuegos.append(reg)

            # Recupera listado de ejemplares existentes en la plataforma
            result = funListarEjemplaresDisponibles(0, idusuario=obUsuario.idUsuario, palabrabuscar=palabrabuscar)
            for reg in result:
                novedades.append(reg)

            numreg = len(novedades) + len(videojuegos)
            newBusUsuario = BusquedaUsuario(usuarioId=obUsuario.idUsuario, busqueda=palabrabuscar, resultados=numreg)
            db.session.add(newBusUsuario)
            db.session.commit()

            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+session['email']+"] index: Hay sesion")

        #print("buscar: cantidad de registros de VJ" + str(len(g_nombres)))
        usuario = db.session.query(Usuario).filter_by(email=session['email']).first()
        return render_template('inicio.html', usuario=usuario.nickName, mensaje="Bienvenido "+session['email'], videojuegos=videojuegos, novedades=novedades, logged=1, lista=g_nombres, puntosusu=funPuntosDisponiblesUsuario(usuario.idUsuario))


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
                # Si el usuario está sancionado
                if obUsuario.sancionado == ESTADO_USR_SANCIO:
                    app.logger.info(datetime.today().strftime(
                        "%Y-%m-%d %H:%M:%S") + "[" + email + "] Usuario bloqueado!")
                    return render_template('login.html', mensaje="Usuario bloqueado!")
                else:
                    if not((not session) or (not email in session['email'])): #Si hay una sesion activa
                        # Si existe el usuario, pero es inactivo, debe remitirse al mail
                        if obUsuario.activo == ESTADO_USR_INACTIVO:
                            #print("login: cantidad de registros de VJ" + str(len(g_nombres)))
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
                            #print("Login Usuario: " + str(obUsuario.idUsuario))
                            result = funListarEjemplaresDisponibles(1, idusuario=obUsuario.idUsuario)
                            for reg in result:
                                videojuegos.append(reg)

                            # Recupera listado de ejemplares existentes en la plataforma
                            result = funListarEjemplaresDisponibles(0, idusuario=obUsuario.idUsuario)
                            for reg in result:
                                novedades.append(reg)

                            #print("login: cantidad de registros de VJ" + str(len(g_nombres)))
                            usuario = db.session.query(Usuario).filter_by(email=session['email']).first()
                            return render_template('inicio.html', usuario=usuario.nickName,mensaje="Ya estabas logueado " + email, videojuegos=videojuegos, novedades=novedades, logged=1, lista=g_nombres, puntosusu=funPuntosDisponiblesUsuario(usuario.idUsuario))
                    else:
                        #Revisa si el usuario está activo o inactivo
                        if obUsuario.activo == ESTADO_USR_INACTIVO:
                            return render_template('home_page.html', confirmarusr=1, url_confirma=URL_APP+"/reenviarconf" ,accion=email+", No has confirmado en tu correo, clic aquí para reenviarte el email de registro! ", logged=0)
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
                            #print("Login Usuario: " + str(obUsuario.idUsuario))
                            result = funListarEjemplaresDisponibles(1, idusuario=obUsuario.idUsuario)
                            for reg in result:
                                videojuegos.append(reg)

                            # Recupera listado de ejemplares existentes en la plataforma
                            result = funListarEjemplaresDisponibles(0, idusuario=obUsuario.idUsuario)
                            for reg in result:
                                novedades.append(reg)

                            #print("login: cantidad de registros de VJ" + str(len(g_nombres)))
                            usuario = db.session.query(Usuario).filter_by(email=email).first()
                            return render_template('inicio.html', usuario=usuario.nickName, mensaje="Bienvenido a ex4play "+email+"!", videojuegos=videojuegos, novedades=novedades, logged=1, lista=g_nombres, puntosusu=funPuntosDisponiblesUsuario(usuario.idUsuario))

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
            #print("email:" + email)
            #Recuperar usuario
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            obEjeUsuario = db.session.query(EjeUsuario).filter_by(email=email).one_or_none()


# Funcion: Cargar un ejemplar
@app.route("/cargarEjemplar", methods=["GET", "POST"])
def cargarEjemplar():
    g_nombres = funListarNombresVJ()

    if request.method == "POST":
        if session is not None:
            email = session['email']
            email = email.lower()
            #print("cargarEjemplar: email:" + email)
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            if obUsuario is not None:
                usrid = obUsuario.idUsuario
                imagen = request.files["imgInp"]

                #vj = request.form.get("ejemplar")
                vj = request.form.get("busqueda")
                #print("cargarEjemplar: ej:" + str(vj))

                estado = request.form.get("estado")

                comentario = request.form.get("comentario")
                publicar = str(request.form.get("publicar"))
                #print("publicar:" + publicar)
                if publicar is not "1":
                    publicar = 0
                #print("publicar:" + str(publicar))

                msg = funCargarEjemplar(email, usrid, vj, estado, publicar, comentario, imagen)

                ejeblk, ejepub, ejenopub = funListarEjemplaresUsuario(usrid)
                return render_template('ejemplaresusuario.html', usuario=obUsuario.nickName, mensaje=msg, vjblk=ejeblk,
                                       vjpub=ejepub, vjnopub=ejenopub, logged=0)
            else:
                return render_template('login.html', mensaje="oopppss...algo suce   dió con tu sesión. Ingresa de nuevo!")

       #print("Inicia carga de ejemplar: Cantidad videojuego " + str(len(g_nombres)))
        usuario = db.session.query(Usuario).filter_by(email=session['email']).first()
        return render_template('cargarejemplar.html', usuario=usuario.nickName, mensaje="Carga tu ejemplar!", lista=g_nombres)

   #print("Inicia carga de ejemplar: Cantidad videojuego " + str(len(g_nombres)))
    usuario = db.session.query(Usuario).filter_by(email=session['email']).first()
    return render_template('cargarejemplar.html', usuario=usuario.nickName, mensaje="Carga tu ejemplar!", lista=g_nombres)


# Funcion: Editar un ejemplar
@app.route("/editarEjemplar/<int:idejeusuario>", methods=["GET", "POST"])
def editarEjemplar(idejeusuario):
    email = session['email']
    email = email.lower()

   #print("El metodo = " + request.method + " - email " + email)

    if request.method == "GET":
        obUsuario =  db.session.query(Usuario).filter_by(email=email).first()
        obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejeusuario).first()
        obVideojuego = db.session.query(VideoJuego).filter_by(idVj=obEjeUsuario.vjId).first()
        obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=obEjeUsuario.idEjeUsuario, activa=1).first()

        foto = base64.b64encode(obFoto.foto).decode("utf-8")

        #print("ejidejeusuario"+str(idejeusuario)+" -- ejimagen=" + foto + "--ejnombre=" + obVideojuego.nombre + "--ejestado= "+ str(obEjeUsuario.estado) + "--ejcomentario="+obEjeUsuario.comentario+"ejpublicar="+str(obEjeUsuario.publicado))
        return render_template('editarejemplar.html', usuario=obUsuario.nickName, mensaje="Edita el videojuego!", ejidejeusuario=idejeusuario, ejimagen=foto, ejnombre=obVideojuego.nombre, ejestado=obEjeUsuario.estado, ejcomentario=obEjeUsuario.comentario, ejpublicar=obEjeUsuario.publicado)

    elif request.method == "POST":
        #print("Entra al POST: " + email)
        if request.form['btnejemplar'] == 'Guardar':
            #print("Guardará para el email:" + email)
            obUsuario = db.session.query(Usuario).filter_by(email=email).one_or_none()
            if obUsuario is not None:

                #print("ejeusuario:" + str(idejeusuario))
                usrid = obUsuario.idUsuario
                #print("usr:" + str(usrid))
                imagen = request.files["imgInp"]
                vj = request.form.get("ejemplar")
                #print("ej:" + str(vj))
                #print("IMAGEN:" + imagen)
                estado = request.form.get("estado")
                #imagen = request.form.get("imagen")
                comentario = request.form.get("comentario")

                #print("imagen:" + str(imagen))
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

                return render_template('ejemplaresusuario.html', usuario=usuario.nickName, mensaje="Bienvenido "+email, vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=1)

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
                #print('EJEMPLARESUSUARIO: ejemplar ' + str(idejemplar))
                if request.form['btnejemplar'] == 'editar':
                    #print('EJEMPLARESUSUARIO: Editar el ejemplar: ' + str(idejemplar))
                    obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejemplar).first()
                    obVideojuego = db.session.query(VideoJuego).filter_by(idVj=obEjeUsuario.vjId).first()
                    obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=obEjeUsuario.idEjeUsuario,
                                                                        activa=1).first()

                    foto = base64.b64encode(obFoto.foto).decode("utf-8")

                    #print("ejidejeusuario" + str(idejemplar) + " -- ejimagen=" + foto + "--ejnombre=" + obVideojuego.nombre + "--ejestado= " + str(obEjeUsuario.estado) + "--ejcomentario=" + obEjeUsuario.comentario + "ejpublicar=" + str(obEjeUsuario.publicado))
                    return render_template('editarejemplar.html', usuario=usuario.nickName, mensaje="Edita el videojuego!",
                                           ejidejeusuario=idejemplar, ejimagen=foto, ejnombre=obVideojuego.nombre,
                                           ejestado=obEjeUsuario.estado, ejcomentario=obEjeUsuario.comentario,
                                           ejpublicar=obEjeUsuario.publicado)
                elif request.form['btnejemplar'] == 'despublicar':
                    funMarcarEjemplaresUsuario(email,idejemplar,0)
                    #print('despublicar ' + idejemplar)
                elif request.form['btnejemplar'] == 'publicar':
                    funMarcarEjemplaresUsuario(email,idejemplar,1)
                    #print('publicar ' + idejemplar)

                ejeblk, ejepub, ejenopub = funListarEjemplaresUsuario(usuario.idUsuario)

    usuario = db.session.query(Usuario).filter_by(email=session['email']).first()
    return render_template('ejemplaresusuario.html', usuario=usuario.nickName, mensaje="Bienvenido "+session['email'], vjblk=ejeblk, vjpub=ejepub, vjnopub=ejenopub, logged=0)


#Cuando el usuario hace clic en "Quiero este juego"
#Crea transacción, detalle transacción y un QyA..
#El sistema verifica si el ejemplar no sea del mismo usuario, y en este caso no permite el cambio
#tambien verifica que el usuario tenga puntos suficientes para la solicitud
@app.route('/solicitarejemplar/<int:idejeusuario>', methods=["GET", "POST"])
def solicitarejemplar(idejeusuario):
    try:
        if not (session) or (session['email'] is None):
            email = ""
        else:
            email = session['email']
            email = email.lower()

        if request.method == "GET":
            obUsuario =  db.session.query(Usuario).filter_by(email=email).first()
            obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejeusuario).first()
            obVideojuego = db.session.query(VideoJuego).filter_by(idVj=obEjeUsuario.vjId).first()
            obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=obEjeUsuario.idEjeUsuario, activa=1).first()

            foto = base64.b64encode(obFoto.foto).decode("utf-8")

            #print("ejidejeusuario"+str(idejeusuario)+" -- ejimagen=" + foto + "--ejnombre=" + obVideojuego.nombre + "--ejestado= "+ str(obEjeUsuario.estado) + "--ejcomentario="+obEjeUsuario.comentario+"ejpublicar="+str(obEjeUsuario.publicado))
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[" + email + "] GET::solicitarejemplarCarga pantalla de solicitud de ejemplar: " + str(idejeusuario)+"-"+obVideojuego.nombre)
            return render_template('solicitarejemplar.html', usuario=obUsuario.nickName, mensaje="Edita el videojuego!", idejeusuario=idejeusuario, ejimagen=foto, ejnombre=obVideojuego.nombre, ejestado=obEjeUsuario.estado, ejcomentario=obEjeUsuario.comentario, editar=1)

        if request.method=="POST":
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+email+"] POST::solicitarjemplar: inicia solicitarejemplar")
            if not(session) or (session['email'] is None):
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] solicitarjemplar: No hay sesion")

                return render_template('registro.html', mensaje="Regístrate para que puedas obtener este y otros videojuegos!", logged=0)
            else:
                if db.session is not None:
                    email = session['email']

                    if request.form['btnejemplar'] == 'Cancelar':
                        app.logger.info(datetime.today().strftime(
                            "%Y-%m-%d %H:%M:%S") + "[" + email + "] POST::solicitarejemplar: Cancela")
                        return index()

                    if request.form['btnejemplar'] == 'Solicitar':
                        usuario = db.session.query(Usuario).filter_by(email=email).first()
                        ejemplar = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejeusuario).first()
                        vj = db.session.query(VideoJuego).filter_by(idVj=ejemplar.vjId).first()
                        usuarioDueno = db.session.query(Usuario).filter_by(idUsuario=ejemplar.usuarioIdAct).first()

                        mensaje=request.form.get("mensaje")
                        if mensaje=="":
                            mensaje="Hola, quiero tu videojuego!"
                        app.logger.info(datetime.today().strftime(
                            "%Y-%m-%d %H:%M:%S") + "[" + email + "] POST::solicitarejemplar: Inicia la solicitud")
                        idusuariosolic = usuario.idUsuario
                        idusuariodueno = ejemplar.usuarioIdAct
                        if idusuariodueno == idusuariosolic:
                            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+email+"] solicitaejemplar: El ejemplar es del mismo usuario")
                            pass
                        else:
                            #Recupera los puntos que tiene el usuario
                            puntosusr = funPuntosDisponiblesUsuario(usuario.idUsuario)
                            #print("puntos usuario" + str(puntosusr))
                            app.logger.error("[" + email + "] solicitarejemplar: Puntos usuario"+str(puntosusr))
                            if puntosusr >= ejemplar.valor:

                                #Crea transacción
                                inresp = funCrearTransaccion(idusuariosolic, idusuariodueno, ejemplar.idEjeUsuario, mensaje)

                                msg = "Perfecto " + usuario.nickName + ", casi es tuyo, espera respuesta del dueño!"
                                #****************Enviar mails para avisar**********************
                                enviar_correo(subject="Solicitaron tu videojuego", sender=app.config['MAIL_USERNAME'], \
                                              recipients=usuarioDueno.email, text_body=None, cc=None, \
                                              bcc=app.config['MAIL_USERNAME'], html_body=None, template="mailsolicitaejemplar.html", \
                                              dueno="S", juego=vj.nombre, nick=usuarioDueno.nickName)

                                enviar_correo(subject="Se envió tu solicitud de videojuego", sender=app.config['MAIL_USERNAME'], \
                                              recipients=usuario.email, text_body=None, cc=None, \
                                              bcc=app.config['MAIL_USERNAME'], html_body=None, template="mailsolicitaejemplar.html", \
                                              dueno="N", juego=vj.nombre, nick=usuario.nickName)

                                app.logger.error("[" + email + "] solicitarejemplar: Si hay puntos suficientes")
                            else:
                                msg = usuario.nickName + ", No tienes los puntos suficientes!. Cambia más videojuegos!"
                                app.logger.error("[" + email + "] solicitarejemplar: No hay puntos suficientes")

                            novedades = []
                            videojuegos = []
                            usuario = db.session.query(Usuario).filter_by(email=email).first()
                            result = funListarEjemplaresDisponibles(1, idusuario=usuario.idUsuario)
                            for reg in result:
                                videojuegos.append(reg)

                            # Recupera listado de ejemplares existentes en la plataforma
                            result = funListarEjemplaresDisponibles(0, idusuario=usuario.idUsuario)
                            for reg in result:
                                novedades.append(reg)

                            return render_template('inicio.html', usuario=usuario.nickName,
                                                   mensaje=msg, videojuegos=videojuegos,
                                                   novedades=novedades, logged=1, lista=g_nombres,
                                                   puntosusu=funPuntosDisponiblesUsuario(usuario.idUsuario))
                        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+email+"] index: Hay sesion")
    except:
        app.logger.error("[" + email + "] solicitarejemplar: error")
        #return render_template('error.html', mensaje="Error en la solicitud!")
        raise


# Funcion: terminos y condiciones
@app.route("/terminos", methods=["GET"])
def terminos():
    return render_template('terminos.html')

# Funcion: Condiciones de calidad en videojuegos
@app.route("/calidadvj", methods=["GET"])
def calidadvj():
    return render_template('calidadvj.html')


# Funcion: Lista de transacciones del usuario, listando
@app.route("/transacciones", methods=["GET", "POST"])
def transacciones():
    try:
        if not (session) or (session['email'] is None):
            email = ""
        else:
            email = session['email']
            email = email.lower()

        if request.method == "GET":
            obUsuario = db.session.query(Usuario).filter_by(email=email).first()
            # Transacciones de solicitud de videojuegos por parte del usuario
            obTrxSolic =  db.session.query(Transaccion).filter_by(usuarioIdSolic=obUsuario.idUsuario, estadoTrx=C_TRXACTIVA).all()
            # Transacciones de solicitud de videojuegos realizadas al usuario
            obTrxRecib =  db.session.query(Transaccion).filter_by(usuarioIdDueno=obUsuario.idUsuario, estadoTrx=C_TRXACTIVA).all()

            solicitadas = []
            recibidas = []
            for reg in obTrxSolic:
                obUser = db.session.query(Usuario).filter_by(idUsuario=reg.usuarioIdDueno).first()
                obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=reg.ejeUsuarioId).first()
                obVideojuego = db.session.query(VideoJuego).filter_by(idVj=obEjeUsuario.vjId).first()
                obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=obEjeUsuario.idEjeUsuario,
                                                                    activa=1).first()

                foto = base64.b64encode(obFoto.foto).decode("utf-8")
                lista={"idtrx":reg.idTrx, "foto":foto, "videojuego":obVideojuego.nombre, "usuario":obUser.nickName}
                solicitadas.append(lista)
                #print("solicitadas")
                #print(solicitadas)

            for reg in obTrxRecib:
                obUser = db.session.query(Usuario).filter_by(idUsuario=reg.usuarioIdSolic).first()
                obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=reg.ejeUsuarioId).first()
                obVideojuego = db.session.query(VideoJuego).filter_by(idVj=obEjeUsuario.vjId).first()
                obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=obEjeUsuario.idEjeUsuario,
                                                                    activa=1).first()

                foto = base64.b64encode(obFoto.foto).decode("utf-8")
                lista={"idtrx":reg.idTrx, "foto":foto, "videojuego":obVideojuego.nombre, "usuario":obUser.nickName}
                recibidas.append(lista)
                #print("recibidas")
                #print(recibidas)

            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[" + email + "] GET::transacciones : Carga lista de transacciones")
            return render_template('transacciones.html', usuario=obUsuario.nickName, mensaje="Videojuegos en negociación", solicitadas=solicitadas, recibidas=recibidas, editar=1)


        #elif request.method == "POST":
        #    obUsuario = db.session.query(Usuario).filter_by(email=email).first()
        #    return render_template('solicitarejemplar.html', usuario=obUsuario.nickName, mensaje="Edita el videojuego!", idejeusuario=idejeusuario, ejimagen=foto, ejnombre=obVideojuego.nombre, ejestado=obEjeUsuario.estado, ejcomentario=obEjeUsuario.comentario, editar=1)

    except:
        app.logger.error("[" + email + "] TRANSACCIONES: problema con las transacciones del usuario : " + email)
        raise


#Muestra toda la conversación que hay a nivel de una solicitud de ejemplar
@app.route('/detalletransacciones/<int:idtrx>', methods=["GET", "POST"])
def detalletransacciones(idtrx):
    try:
        if not (session) or (session['email'] is None):
            email = ""
        else:
            email = session['email']
            email = email.lower()


        obUsuario =  db.session.query(Usuario).filter_by(email=email).first()
        obTrx = db.session.query(Transaccion).filter_by(idTrx=idtrx).first()
        # Si el usuario que solicitó es el logeado
        if obTrx.usuarioIdSolic == obUsuario.idUsuario:
            obUsuarioOtro = db.session.query(Usuario).filter_by(idUsuario=obTrx.usuarioIdDueno).first()
        else:
            obUsuarioOtro = db.session.query(Usuario).filter_by(idUsuario=obTrx.usuarioIdSolic).first()

        obDetTrx = db.session.query(DetalleTrx).filter_by(trxId=idtrx).all()
        #obDetVal = db.session.query(DetalleValor).filter_by(trxId=idtrx).all()

        obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=obTrx.ejeUsuarioId).first()
        obVideojuego = db.session.query(VideoJuego).filter_by(idVj=obEjeUsuario.vjId).first()

        obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=obEjeUsuario.idEjeUsuario,
                                                            activa=1).first()

        fotoVj = base64.b64encode(obFoto.foto).decode("utf-8")
        # Foto usuario
        obFotoU = db.session.query(FotoUsuario).filter_by(usuarioId=obUsuario.idUsuario,
                                                            activa=1).first()
        if obFotoU is None:
            fotousuario = IMG_USR
        else:
            fotousuario = base64.b64encode(obFotoU.foto).decode("utf-8")

        # Foto usuario otro
        obFotoO = db.session.query(FotoUsuario).filter_by(usuarioId=obUsuarioOtro.idUsuario,
                                                            activa=1).first()
        if obFotoO is None:
            fotousuariootro = IMG_USR
        else:
            fotousuariootro = base64.b64encode(obFotoO.foto).decode("utf-8")

        if request.method == "GET":
            obQyA = db.session.query(QyA).filter_by(trxId=idtrx).all()

            print("Detalle Transaccion GET")
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[" + email + "]" +"GET::detalletransacciones: Detalle de la transaccion: " + str(idtrx)+"-"+obVideojuego.nombre)
            return render_template('detalletransacciones.html', usuario=obUsuario.nickName, mensaje="Mensajes!", qya=obQyA, usrlog=obUsuario, usrotro=obUsuarioOtro, fotousr=fotousuario,fotousrotro=fotousuariootro, videojuego=obVideojuego.nombre, fotovj=fotoVj)

        if request.method == "POST":

            #print("dijo:" + mensaje)
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"["+email+"] POST::detalletransacciones: inicia detalletransacciones")
            if not(session) or (session['email'] is None):
                app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S")+"[NO_USER] detalletransacciones: No hay sesion")
                return render_template('registro.html', mensaje="Regístrate para que puedas obtener este y otros videojuegos!", logged=0)
            else:
                if db.session is not None:
                    email = session['email']
                    obUsuario = db.session.query(Usuario).filter_by(email=email).first()
                    transaccion = db.session.query(DetalleTrx).filter_by(trxId=idtrx).all()

                    if request.form['btnsend'] == 'Enviar':
                        mensaje=request.form.get("mensaje")
                        app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[" + email + "] POST::detalletransacciones: Inicia la solicitud")

                        qya = funcCrearUpdateQA(idtrx, mensaje, obUsuario.idUsuario, 'qa')

                    elif request.form['btnSiDeal'] == 'Si':
                        print('Entre al trato si')

                    elif request.form['btnSiCanc'] == 'No':
                        print('Entre al cancelar trato')
                        mensaje = 'Lamentablemente el trato no fue aceptado.'
                        qya = funcCrearUpdateQA(idtrx, mensaje, obUsuario.idUsuario,'cancelar')

                subject = SUBJECT_REGISTRO.format(nick=obUsuario.nombres)
                correoEnviado = enviar_correo(subject, app.config['MAIL_USERNAME'], email, text_body=None,
                                 template="mailmensajes.html", nick=email, urlconfirma=None,
                                 urlapp=urlapp)

                return render_template('detalletransacciones.html', usuario=obUsuario.nickName, mensaje="Mensajes!", qya=qya, usrlog=obUsuario, usrotro=obUsuarioOtro, fotousr=fotousuario,fotousrotro=fotousuariootro, videojuego=obVideojuego.nombre, fotovj=fotoVj)
    except:
        app.logger.error("[" + email + "] solicitarejemplar: error")
        #return render_template('error.html', mensaje="Error en la solicitud!")
        raise


# Funcion: Actualizar datos usuario
@app.route("/updateUser", methods=["GET", "POST"])
def updateUser():
    datosUsuario = None
    ciudades = None
    foto = None
    saldo = None
    direcciones = None
    dirPrinc = ""
    dirOp2 = ""
    dirOp3 = ""
    dirOp4 = ""

    if ciudades is None:
        ciudades = funcObtenerCiudades()

    if request.method == "GET":
        if not(session) or (session['email'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")

            return render_template('home_page.html', mensaje="Inicia Sesión o Registrate y disfruta!")
        else:
            if db.session is not None:
                nick = session['email']
                usuario = db.session.query(Usuario).filter_by(email=nick).first()
                datosUsuario, foto, direcciones = funObtenerDatosUsuario(usuario.idUsuario)

                if datosUsuario.fechanac is not None:
                    datosUsuario.fechanac = datosUsuario.fechanac.strftime("%Y-%m-%d")

                if datosUsuario.genero is not None:
                    datosUsuario.genero = str(datosUsuario.genero)

                saldo = db.session.query(Saldos).filter_by(usuarioId=usuario.idUsuario).first()
                saldo.TotalPuntos = int(saldo.TotalPuntos)
                saldo.valorPagado = int(saldo.valorPagado)
                saldo.ValorCobrado = int(saldo.ValorCobrado)

                if len(direcciones) > 0:
                    for dir in direcciones:
                        if dir.principal == 1:
                            dirPrinc = dir.direccion
                        else:
                            if dirOp2 == "":
                                dirOp2 = dir.direccion
                            else:
                                if dirOp3 == "":
                                    dirOp3 = dir.direccion
                                else:
                                    if dirOp4 == "":
                                        dirOp4 = dir.direccion


    if request.method == "POST":
        if not(session) or (session['email'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")
            return render_template('home_page.html', mensaje="Inicia Sesión o Registrate y disfruta!")
        else:
            if session is not None:
                direc = []
                nick = session['email']
                obUsuario = db.session.query(Usuario).filter_by(email=nick).one_or_none()

                if 'saveDataUser' in request.form:
                    if request.form['saveDataUser'] == 'Guardar':

                        print("email:" + nick)

                        if obUsuario is not None:
                            usrid = obUsuario.idUsuario
                            imagen = request.files["imgInp"]
                            nombres = request.form.get("nombres")
                            apellidos = request.form.get("apellidos")
                            edad = request.form.get("edad")
                            genero = request.form.get("genero")
                            fechanac = request.form.get("fecha")
                            celular = request.form.get("celular")
                            nickname = request.form.get("nickname")

                            funUpdateDatosUsuario(usrid,nombres,apellidos,edad,fechanac,genero,celular,nickname,nick, imagen, None, hoy, 0)

                if 'saveAddress' in request.form:
                    if request.form['saveAddress'] == 'Guardar':
                        usrid = obUsuario.idUsuario

                        if request.form['dir1'] != '':
                            direc.append(request.form['dir1'])
                        if request.form['dir2'] != '':
                            direc.append(request.form['dir2'])
                        if request.form['dir3'] != '':
                            direc.append(request.form['dir3'])
                        if request.form['dir4'] != '':
                            direc.append(request.form['dir4'])

                        funUpdateDatosUsuario(usrid,None,None,None,None,None,None,None,None, None, direc, hoy, 1)


    return render_template('act_datos_usuario.html', usuario=datosUsuario, ciudades=ciudades, foto=foto, saldo=saldo, dirP=dirPrinc, dirOp2=dirOp2, dirOp3=dirOp3, dirOp4=dirOp4)

# Funcion: Desplegar inicio
def desplegarinicio():
    videojuegos = []
    novedades = []
    app.logger.info(
        datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[" + session['email'] + "] index: Hay sesion")
    app.logger.info("[NO_USER] GET::index inicia")
    # print("[NO_USER] GET::index inicia")
    # Recupera listado de videojuegos generales
    # print("index: cantidad de registros de VJ " + str(len(g_nombres)))
    usuario = db.session.query(Usuario).filter_by(email=session['email']).first()
    result = funListarEjemplaresDisponibles(1, idusuario=usuario.idUsuario)
    for reg in result:
        videojuegos.append(reg)

    # Recupera listado de ejemplares existentes en la plataforma
    result = funListarEjemplaresDisponibles(0, idusuario=usuario.idUsuario)
    for reg in result:
        novedades.append(reg)

    return render_template('inicio.html', usuario=usuario.nickName,
                           mensaje="Bienvenido " + session['email'], videojuegos=videojuegos,
                           novedades=novedades, logged=1, lista=g_nombres,
                           puntosusu=funPuntosDisponiblesUsuario(usuario.idUsuario))


# Funcion: Módulo de Administración
@app.route("/admin4play", methods=["GET"])
def admninistracion():
    if request.method == "GET":
        if db.session is not None:
            nick = session['email']
            if nick == "alexviatela@gmail.com":
                return render_template('admin4play.html')
            else:
                return desplegarinicio()

# OK Funcion: Ver nuevos videojuegos que no cargan los usuarios y no hicieron match
# Opcion del menú:  Videojuegos sin crear
@app.route("/nuevosjuegos", methods=["GET", "POST"])
def nuevosjuegos():
    #print("Inicia a /nuevosjuegos")
    if request.method == "GET":
        if db.session is not None:
            nick = session['email']
            if nick == "alexviatela@gmail.com":
                #print("GET: Inicia a listar nuevosjuegos")
                vjuegos = funListarNuevosJuegos()
                #print("vjuegos : " + str(vjuegos))
                return render_template('nuevosjuegos.html', juegos=vjuegos)
            else:
                return desplegarinicio()
    elif request.method == "POST":
        if db.session is not None:
            nick = session['email']
            if nick == "alexviatela@gmail.com":
                if request.form['accion'] == 'updatevj':
                    idejem=request.form.get("ideje")
                    #print("idtrx: " + str(idejem))
                    categ=request.form.get("categ")
                    #if categ is not None:
                    #    print("categ="+str(categ))
                    nombre=request.form.get("nnombre")
                    #if nombre is not None:
                    #    print("nombre"+nombre)
                    puntos=request.form.get("cpuntos")
                    #if puntos is not None:
                    #    print("npuntos="+str(puntos))
                    consola=request.form.get("consola")
                    #if consola is not None:
                    #    print("consola="+str(consola))
                    funCambiarJuego(idejem=idejem, puntos=puntos, juego=None, nnombre=nombre, categ=categ, consola=consola)
                if request.form['accion'] == 'otrovj':
                    idejem=request.form.get("ideje")
                    #print("idtrx: " + str(idejem))
                    njuego=request.form.get("njuego")
                    #if njuego is not None:
                    #    print("njuego="+str(njuego))
                    puntos=request.form.get("npuntos")
                    #if puntos is not None:
                    #    print("puntos="+str(puntos))

                    funCambiarJuego(idejem=idejem, puntos=puntos, juego=njuego, nnombre="", categ="", consola="")

                vjuegos = funListarNuevosJuegos()
                return render_template('nuevosjuegos.html', juegos=vjuegos)
            else:
                return desplegarinicio()

# Funcion: Módulo de Administración
@app.route("/nuevosusuarios", methods=["GET", "POST"])
def nuevosusuarios():
    if request.method == "GET":
        if db.session is not None:
            nick = session['email']
            if nick == "alexviatela@gmail.com":
                #print("GET: Inicia a listar manejoenvios")
                vusuarios = funListarUsuariosAdmin()
                #print("vusuarios : " + str(vusuarios))
                return render_template('nuevosusuarios.html', usuarios=vusuarios)
            else:
                return desplegarinicio()
    elif request.method == "POST":
        idusr = request.form.get("idusu")
        if request.form['accion'] == 'activar':
            funEditarUsuariosAdmin(idusr, activar=1, sancionar=-1)
        elif request.form['accion'] == 'inactivar':
            funEditarUsuariosAdmin(idusr, activar=0, sancionar=-1)
        elif request.form['accion'] == 'sancionar':
            funEditarUsuariosAdmin(idusr, activar=-1, sancionar=1)
        elif request.form['accion'] == 'desancionar':
            funEditarUsuariosAdmin(idusr, activar=-1, sancionar=0)

        vusuarios = funListarUsuariosAdmin()
        return render_template('nuevosusuarios.html', usuarios=vusuarios)


# Funcion: Ver nuevos tratos cerrados
@app.route("/nuevostratos", methods=["GET"])
def nuevostratos():
    if request.method == "GET":
        if db.session is not None:
            nick = session['email']
            if nick == "alexviatela@gmail.com":
                return render_template('inicioadmin.html')
            else:
                return desplegarinicio()

# OK Funcion: Manejo manual de envíos
# Lista todos los tratos cerrados por los dos usuarios, que no han sido entregados o recibidos
@app.route("/manejoenvios", methods=["GET", "POST"])
def manejoenvios():
    #print("Inicia a /manejoenvios")
    if request.method == "GET":
        if db.session is not None:
            nick = session['email']
            if nick == "alexviatela@gmail.com":
                #print("GET: Inicia a listar manejoenvios")
                venvios = funListarEnviosPendientes()
                #print("venvios : " + str(venvios))
                return render_template('manejoenvios.html', envios=venvios)
            else:
                return desplegarinicio()
    elif request.method == "POST":
        if db.session is not None:
            nick = session['email']
            if nick == "alexviatela@gmail.com":
                if request.form['estadoenvio'] == 'entrega':
                    idtrx=request.form.get("idtrx")
                    funEntregaroRecibir(idtrx, 1)
                    venvios = funListarEnviosPendientes()
                    #print("POST para recoger TRX: " + str(idtrx))

                if request.form['estadoenvio'] == 'recibe':
                    idtrx = request.form.get("idtrx")
                    funEntregaroRecibir(idtrx, 2)
                    venvios = funListarEnviosPendientes()
                    #print("POST para entregar TRX: " + str(idtrx))
                return render_template('manejoenvios.html', envios=venvios)
            else:
                return desplegarinicio()

# OK Funcion: Lista los saldos y movimientos de los usuarios
@app.route("/saldosusuarios", methods=["GET", "POST"])
def saldosusuarios():
    #print("Inicia a /saldosusuarios")
    if request.method == "GET":
        if db.session is not None:
            nick = session['email']
            if nick == "alexviatela@gmail.com":
                #print("GET: Inicia a listar saldos usuarios")
                vsaldos = funListarSaldosUsuarios()
                #print("vsaldos : " + str(vsaldos))
                return render_template('saldosusuarios.html', saldos=vsaldos)
            else:
                return desplegarinicio()

# Funcion: Re-Valoracion de videojuegos
@app.route("/valoracionjuegos", methods=["GET", "POST"])
def valoracionjuegos():
    #print("Inicia a /valoracionjuegos")
    if request.method == "GET":
        if db.session is not None:
            nick = session['email']
            if nick == "alexviatela@gmail.com":
                #print("GET: Inicia a listar valoracion juegos")
                vjuegos = funListarJuegosValorizar()
                #print("vjuegos : " + str(vjuegos))
                return render_template('valoracionjuegos.html', juegos=vjuegos)
            else:
                return desplegarinicio()
    elif request.method == "POST":
        if db.session is not None:
            nick = session['email']
            if nick == "alexviatela@gmail.com":
                if request.form['accion'] == 'reclasif':
                    idvj=request.form.get("idvj")
                    categ=request.form.get("categ")
                    funReclasifica(idvj, categ)
                    vjuegos = funListarJuegosValorizar()
                    #print("vjuegos : " + str(vjuegos))
                    return render_template('valoracionjuegos.html', juegos=vjuegos)
                    #print("POST : " + str(idvj))
            else:
                return desplegarinicio()

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

