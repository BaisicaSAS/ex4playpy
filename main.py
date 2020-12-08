from passlib.hash import sha256_crypt
import logging
from sqlalchemy.exc import IntegrityError
import base64
from datetime import datetime, timedelta
from smtplib import SMTPException
from flask_mail import Mail, Message
from flask import Flask, request, redirect, render_template, session, current_app, url_for, \
    copy_current_request_context
from config import ProductionConfig, DevelopmentConfig, Config
from datamodel import db, Usuario, ConexionUsuario, VideoJuego, EjeUsuario, FotoEjeUsuario, BusquedaUsuario, \
    Transaccion, DetalleTrx, DetalleLugar, DetalleValor, DetalleValorOtros, QyA, FotoUsuario, Saldos, LugarUsuario
from operavideojuegos import funCargarEjemplar, funListarEjemplaresUsuario, funMarcarEjemplaresUsuario, \
    funListarEjemplaresDisponibles, funEditarEjemplar, funListarNombresVJ, funObtenerDatosUsuario, \
    funUpdateDatosUsuario, funPuntosDisponiblesUsuario, funCrearTransaccion, \
    funListarSaldosUsuarios, funListarNuevosJuegos, funCambiarJuego, funListarJuegosValorizar, \
    funReclasifica, C_TRXACTIVA, funListarUsuariosAdmin, funEditarUsuariosAdmin, funUpdateDatosUsuario, \
    funPuntosDisponiblesUsuario, funCrearTransaccion, funcObtenerCiudades, funcCrearUpdateQA, funListarEnviosPendientes, \
    funEntregaroRecibir
import threading

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
app.config['MAIL_PASSWORD'] = 'datab@Ju$o2020@1034567890.'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

SUBJECT_REGISTRO = "Bienvenido a ex4play {nick} !"
SUBJECT_CAMBIACLAVE = "Enlace para cambio de clave {nick} !"
SUBJECT_CLAVECAMBIADA = "Tu clave se cambió con exito {nick} !"
SUBJECT_MENSAJE = "Tienes un nuevo mensaje!"

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
            obUsuario = db.session.query(Usuario).filter_by(email=email).first()
            obEjeUsuario = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejeusuario).first()
            obVideojuego = db.session.query(VideoJuego).filter_by(idVj=obEjeUsuario.vjId).first()
            obFoto = db.session.query(FotoEjeUsuario).filter_by(ejeUsuarioId=obEjeUsuario.idEjeUsuario, activa=1).first()

            foto = base64.b64encode(obFoto.foto).decode("utf-8")

            #print("ejidejeusuario"+str(idejeusuario)+" -- ejimagen=" + foto + "--ejnombre=" + obVideojuego.nombre + "--ejestado= "+ str(obEjeUsuario.estado) + "--ejcomentario="+obEjeUsuario.comentario+"ejpublicar="+str(obEjeUsuario.publicado))
            app.logger.info(datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[" + email + "] GET::solicitarejemplarCarga pantalla de solicitud de ejemplar: " + str(idejeusuario)+"-"+obVideojuego.nombre)
            return render_template('solicitarejemplar.html', usuario=obUsuario.nickName, mensaje="Solicita el juego!!", idejeusuario=idejeusuario, ejimagen=foto, ejnombre=obVideojuego.nombre, ejestado=obEjeUsuario.estado, ejcomentario=obEjeUsuario.comentario, editar=1)

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
                            print("puntos usuario" + str(puntosusr))
                            app.logger.debug("[" + email + "] solicitarejemplar: Puntos usuario"+str(puntosusr))
                            if puntosusr >= ejemplar.valor:
                                app.logger.debug("[" + email + "] solicitarejemplar: puntosusr >= ejemplar.valor"+str(ejemplar.valor))
                                #Crea transacción
                                inresp = funCrearTransaccion(idusuariosolic, idusuariodueno, ejemplar.idEjeUsuario, mensaje)
                                #MR 03122020 Pone el ejemplar en negociaciacion para que no lo puedan tocar
                                ejemplaredit = db.session.query(EjeUsuario).filter_by(idEjeUsuario=idejeusuario).update(dict(bloqueado=1))
                                db.session.commit()


                                msg = "Perfecto " + usuario.nickName + ", casi es tuyo, espera respuesta del dueño!"

                                #****************Enviar mails para avisar**********************
                                #MR 03122020: Estos mails se deben enviar de manera async
                                @copy_current_request_context
                                def send_msg_dueno(subject, sender, recipients, text_body, dueno, vjnombre, nick,
                                            cc=None, bcc=None, html_body=None, template=None):
                                    enviar_correo(subject=subject, sender=sender, \
                                                  recipients=recipients, text_body=text_body, cc=cc, \
                                                  bcc=bcc, html_body=html_body, template=template, \
                                                  dueno=dueno, juego=vjnombre, nick=nick)

                                sender = threading.Thread(name='mail_sender', target=send_msg_dueno,
                                                            args = ("Solicitaron tu videojuego", \
                                                            app.config['MAIL_USERNAME'], \
                                                            usuarioDueno.email, None, "S", vj.nombre, \
                                                            usuarioDueno.nickName, \
                                                            None, app.config['MAIL_USERNAME'], None, \
                                                            "mailsolicitaejemplar.html",))
                                sender.start()

                                @copy_current_request_context
                                def send_msg_solic(subject, sender, recipients, text_body, dueno, vjnombre, nick,
                                            cc=None, bcc=None, html_body=None, template=None):
                                    enviar_correo(subject=subject, sender=sender, \
                                                  recipients=recipients, text_body=text_body, cc=cc, \
                                                  bcc=bcc, html_body=html_body, template=template, \
                                                  dueno=dueno, juego=vjnombre, nick=nick)

                                sender = threading.Thread(name='mail_sender', target=send_msg_solic,
                                                            args = ("Se envió tu solicitud de videojuego", \
                                                            app.config['MAIL_USERNAME'], \
                                                            usuario.email, None, "N", vj.nombre, usuario.nickName, \
                                                            None, app.config['MAIL_USERNAME'], None, \
                                                            "mailsolicitaejemplar.html",))

                                sender.start()
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


# Muestra toda la conversación que hay a nivel de una solicitud de ejemplar
@app.route('/detalletransacciones/<int:idtrx>', methods=["GET", "POST"])
def detalletransacciones(idtrx):
    mens = ''

    try:
        if not (session) or (session['email'] is None):
            email = ""
        else:
            email = session['email']
            email = email.lower()

        obUsuario = db.session.query(Usuario).filter_by(email=email).first()
        obTrx = db.session.query(Transaccion).filter_by(idTrx=idtrx).first()
        # Si el usuario que solicitó es el logeado
        if obTrx.usuarioIdSolic == obUsuario.idUsuario:
            obUsuarioOtro = db.session.query(Usuario).filter_by(idUsuario=obTrx.usuarioIdDueno).first()
        else:
            obUsuarioOtro = db.session.query(Usuario).filter_by(idUsuario=obTrx.usuarioIdSolic).first()

        obDetTrx = db.session.query(DetalleTrx).filter_by(trxId=idtrx).all()
        # obDetVal = db.session.query(DetalleValor).filter_by(trxId=idtrx).all()

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
            fotousuariootro = "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"
        else:
            fotousuariootro = base64.b64encode(obFotoO.foto).decode("utf-8")

        if request.method == "GET":
            obQyA = db.session.query(QyA).filter_by(trxId=idtrx).all()

            print("Detalle Transaccion GET")

            app.logger.info(datetime.today().strftime(
                "%Y-%m-%d %H:%M:%S") + "[" + email + "]" + "GET::detalletransacciones: Detalle de la transaccion: " + str(
                idtrx) + "-" + obVideojuego.nombre)

            transaccion = db.session.query(DetalleTrx).filter_by(trxId=idtrx).all()
            habilitar = ''

            for tran in transaccion:
                if tran.accion == 6:
                    habilitar = 'disabled'
                else:
                    habilitar = ''

            transaccionAceptada = db.session.query(DetalleTrx).filter_by(trxId=idtrx, accion=2).all()
            if len(transaccionAceptada) == 2:
                habilitar = 'disabled'

            showLoader = 'none'
            return render_template('detalletransacciones.html', usuario=obUsuario.nickName, mensaje="Mensajes!",
                                   qya=obQyA, usrlog=obUsuario, usrotro=obUsuarioOtro, fotousr=fotousuario,
                                   fotousrotro=fotousuariootro, videojuego=obVideojuego.nombre, fotovj=fotoVj,
                                   habilitar=habilitar, showLoader=showLoader)

        if request.method == "POST":
            if not (session) or (session['email'] is None):

                app.logger.info(
                    datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "[NO_USER] detalletransacciones: No hay sesion")

                return render_template('registro.html',
                                       mensaje="Regístrate para que puedas obtener este y otros videojuegos!", logged=0)
            else:
                if db.session is not None:
                    email = session['email']
                    usuario = db.session.query(Usuario).filter_by(email=email).first()
                    # transaccion = db.session.query(DetalleTrx).filter_by(trxId=idtrx).all()

                    if 'btnsend' in request.form:
                        if request.form['btnsend'] == 'Enviar':
                            mensaje = request.form.get("mensaje")

                            app.logger.info(datetime.today().strftime(
                                "%Y-%m-%d %H:%M:%S") + "[" + email + "] POST::detalletransacciones: Inicia la solicitud")

                            qya = funcCrearUpdateQA(idtrx, mensaje, usuario.idUsuario, 'qa')
                            habilitar = ''

                    if 'btnSiDeal' in request.form:
                        if request.form['btnSiDeal'] == 'Si':
                            print('Entre al trato si')
                            userDue = None
                            userSolic = None

                            transaccion = db.session.query(DetalleTrx).filter_by(trxId=idtrx,accion=2).all()
                            acpetarYa = db.session.query(DetalleTrx).filter_by(trxId=idtrx, accion=2, usuarioId=usuario.idUsuario).all()
                            direcciones = db.session.query(LugarUsuario).filter_by(usuarioId=usuario.idUsuario, activa=1, principal=1).first()

                            obUsuario = db.session.query(Usuario).filter_by(email=email).first()
                            obTrx = db.session.query(Transaccion).filter_by(idTrx=idtrx).first()

                            # Si el usuario que solicitó es el logeado
                            if obTrx.usuarioIdSolic == obUsuario.idUsuario:
                                userSolic = db.session.query(Usuario).filter_by(idUsuario=obTrx.usuarioIdSolic).first()
                            else:
                                userDue = db.session.query(Usuario).filter_by(idUsuario=obTrx.usuarioIdDueno).first()

                            if direcciones is not None:
                                if len(acpetarYa) == 0:
                                    if len(transaccion) == 0:
                                        mensaje = '{usuario} aceptó el trato para el juego {juego}, por favor envíale una respuesta.'.format(usuario=usuario.nombres, juego=obVideojuego.nombre)
                                        qya = funcCrearUpdateQA(idtrx, mensaje, usuario.idUsuario, 'aceptar')

                                        if userDue is not None:
                                            dir = db.session.query(LugarUsuario).filter_by(usuarioId=userDue.idUsuario, activa=1, principal=1).first()
                                            detalleLug = DetalleLugar(trxId=idtrx, ciudadIdDueno=dir.ciudadId, direccionDueno=dir.direccion, ciudadIdSolic=1,direccionSolic='')
                                        else:
                                            dir = db.session.query(LugarUsuario).filter_by(usuarioId=userSolic.idUsuario,activa=1, principal=1).first()
                                            detalleLug = DetalleLugar(trxId=idtrx, ciudadIdSolic=dir.ciudadId,direccionSolic=dir.direccion, ciudadIdDueno=1, direccionDueno='')

                                        db.session.add(detalleLug)
                                        db.session.commit()
                                        habilitar = ''

                                    elif len(transaccion) == 1:
                                        mensaje = 'Muy bien, se cerró el trato por el juego {juego}, nuestro equipo de logistica coordinará pronto para recogerlo/enviarlo..'.format(juego=obVideojuego.nombre)
                                        qya = funcCrearUpdateQA(idtrx, mensaje, usuario.idUsuario, 'aceptar')

                                        if userDue is not None:
                                            dir = db.session.query(LugarUsuario).filter_by(usuarioId=userDue.idUsuario, activa=1, principal=1).first()
                                            actDataLugar = db.session.query(DetalleLugar).filter_by(trxId=idtrx).update(dict(ciudadIdDueno=dir.ciudadId, direccionDueno=dir.direccion))
                                        else:
                                            dir = db.session.query(LugarUsuario).filter_by(usuarioId=userSolic.idUsuario,activa=1, principal=1).first()
                                            actDataLugar = db.session.query(DetalleLugar).filter_by(trxId=idtrx).update(dict(ciudadIdSolic=dir.ciudadId,direccionSolic=dir.direccion))

                                        db.session.commit()
                                        habilitar = 'disabled'
                                else:
                                    mens = 'Ya has aceptado el trato, espera la respuesta.'
                                    qya = db.session.query(QyA).filter_by(trxId=idtrx).all()
                                    habilitar = ''
                            else:
                                mens = 'Debe asignar una dirección a su perfil antes de acpetar el trato...'
                                qya= db.session.query(QyA).filter_by(trxId=idtrx).all()
                                habilitar = ''

                    if 'btnSiCanc' in request.form:
                        if request.form['btnSiCanc'] == 'Si':
                            print('Entre al cancelar trato')
                            mensaje = 'Lamentablemente el trato no fue aceptado.'
                            qya = funcCrearUpdateQA(idtrx, mensaje, usuario.idUsuario, 'cancelar')

                            habilitar = 'disabled'

                subject = SUBJECT_MENSAJE
                #correoEnviado = enviar_correo(subject, app.config['MAIL_USERNAME'], email, text_body=None,
                #                              template="mailmensajes.html", nick=email, urlconfirma=None,
                #                              urlapp=urlapp)

                # MR 03122020: Estos mails se deben enviar de manera async
                @copy_current_request_context
                def send_msg(subject, sender, recipients, template,
                             nick, urlapp, urlconfirma=None, text_body=None):
                    enviar_correo(subject=subject, sender=sender, \
                                  recipients=recipients, text_body=text_body, \
                                  template=template,  urlapp=urlapp)

                sender = threading.Thread(name='mail_sender', target=send_msg,
                                          args=(subject, app.config['MAIL_USERNAME'], email,
                                                "mailmensajes.html", email, \
                                                urlapp ))
                sender.start()

                showLoader = 'none'

                return render_template('detalletransacciones.html', usuario=obUsuario.nickName, mensaje=mens, qya=qya,
                                       usrlog=obUsuario, usrotro=obUsuarioOtro, fotousr=fotousuario,
                                       fotousrotro=fotousuariootro, videojuego=obVideojuego.nombre, fotovj=fotoVj,
                                       habilitar=habilitar, showLoader=showLoader)

    except:
        app.logger.error("[" + email + "] solicitarejemplar: error")
        # return render_template('error.html', mensaje="Error en la solicitud!")
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

    if request.method == "POST":
        if not(session) or (session['email'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")
            return render_template('home_page.html', mensaje="Inicia Sesión o Registrate y disfruta!")
        else:
            if session is not None:
                direc = []
                nick = session['email']
                print("updateUser: saveDataUser: Si hay sesion:" + nick)
                #manuel cambiar por one_or_none por first
                obUsuario = db.session.query(Usuario).filter_by(email=nick).first()

                if 'saveDataUser' in request.form:
                    if request.form['saveDataUser'] == 'Guardar':

                        print("updateUser: saveDataUser: email:" + nick)

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

    if ciudades is None:
        ciudades = funcObtenerCiudades()

    #if request.method == "GET":
        if not (session) or (session['email'] is None):
            app.logger.debug("[NO_USER] index: No hay sesion")

            return render_template('home_page.html', mensaje="Inicia Sesión o Registrate y disfruta!")
        else:
            if db.session is not None:
                nick = session['email']
                print("updateUser: saveDataUser: Si hay sesion:" + nick)
                usuario = db.session.query(Usuario).filter_by(email=nick).first()
                datosUsuario, foto, direcciones = funObtenerDatosUsuario(usuario.idUsuario)

                if datosUsuario.fechanac is not None:
                    datosUsuario.fechanac = datosUsuario.fechanac.strftime("%Y-%m-%d")

                if datosUsuario.genero is not None:
                    datosUsuario.genero = str(datosUsuario.genero)

                saldo = db.session.query(Saldos).filter_by(usuarioId=usuario.idUsuario).first()
                print("updateUser: saveDataUser: Si hay sesion:" + nick+" - id:"+str(usuario.idUsuario))
                if saldo is not None:
                    print("updateUser: Saldo is not None:" + nick)
                    saldo.TotalPuntos = int(saldo.TotalPuntos)
                    saldo.valorPagado = int(saldo.valorPagado)
                    saldo.ValorCobrado = int(saldo.ValorCobrado)
                else:
                    saldo = Saldos()
                    saldo.TotalPuntos = 0
                    saldo.valorPagado = 0
                    saldo.ValorCobrado = 0

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

