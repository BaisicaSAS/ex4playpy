from smtplib import SMTPException
from flask_mail import Mail, Message
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from config import DevelopmentConfig, Config
from datamodel import db, Usuario
from passlib.hash import sha256_crypt
import logging

app = Flask(__name__)

#mail= Mail(app)

app.config['MAIL_SERVER']='p3plcpnl0478.prod.phx3.secureserver.net'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'registro@ex4read.co'
app.config['MAIL_PASSWORD'] = 'R3g15tr0'
app.config['MAIL_USE_TLS'] = True
#app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

#C 0 N S T A N T E S
ESTADO_USR_INACTIVO = 0
ESTADO_USR_ACTIVO = 1
SUBJECT_REGISTRO = "Bienvenido a ex4play!"
MAIL_REGISTRO = "registro@ex4read.co"
URL_CONFIRMA = "http://127.0.0.1:8000/confirma?"

#LOG_FILENAME = 'tmp/errores.log'
LOG_FILENAME = 'tmp\errores.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


# Funcion: index
# La pagina principal debe tener todos los accesos y mostrar todos los juegos en la plataforma
@app.route('/')
def index():
    app.logger.debug("[NO_USER] index: inicia index")
    #if 'nombre' in session:
    #    print("index: Hay una sesion")
    #    return render_template('inicio.html', 334455)
    #else:
    #    print("index: No hay sesion")
    return render_template('login.html', mensaje="Registrate o ingresa al sistema!" )


# Funcion: login
@app.route("/login", methods=["POST"])
def login():
    app.logger.debug("[NO_USER] login: inicia login")
    if request.method == "POST":
        try:
            nick = str(request.form.get("nick"))
            pwdorig = str(request.form.get("clave"))
            idnick = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(pwdorig)
            app.logger.info("[" + nick + "] login: Datos del usuario ingresado: nick[" + nick + "]")
            #app.logger.info("login: Datos del usuario ingresado: nick[" + nick + "], pwd[" + idnick + "], pwdorg["+pwdorig+"]")
            #app.logger.info("[nick: " + nick + "] - [sesion: " + str(session['nick']) + "]")

            #usuarioValido = db.session.query(Usuario.nickName, Usuario.pwd).filter_by(nickName=nick,
            #                                                                          pwd=idnick).scalar() is not None

            obUsuario = db.session.query(Usuario.nickName, Usuario.pwd).filter_by(nickName=nick,
                                                                                      pwd=idnick).one_or_none()

            #if usuarioValido == True:
            if obUsuario is not None:
                if not((not session) or (not nick in session['nick'])):
                    app.logger.debug("[" + nick + "] login: Hay una sesion")
                    app.logger.info("[" + nick + "] login: Usuario a ingresar con sesion recuperada: " + nick)
                    return render_template('inicio.html', mensaje="Ya estabas logueado " + nick)
                else:
                    # Si existe el usuario, pero es inactivo, debe remitirse al mail
                    if obUsuario.activo == ESTADO_USR_INACTIVO:
                        return render_template('inicio.html', mensaje=nick+", debes confirmar tu registro en tu correo para poder ingresar!")
                    else:
                        app.logger.debug("[" + nick + "] login: No hay sesion")

                        session['nick'] = nick
                        session['idnick'] = idnick
                        app.logger.info("[" + nick + "] login: Sesion generada: " + nick)
                        #app.logger.info("login: Sesion generada: " + nick + " " + idnick)
                        return render_template('inicio.html', mensaje="Bienvenido al sistema "+nick+"!" )
            else:
                app.logger.info("[" + nick + "] Usuario o password inválido. Intenta de nuevo!")
                return render_template('login.html', mensaje="Usuario o password inválido. Intenta de nuevo!" )

        except:
            raise
            app.logger.error("[" + nick + "] login: problema con usuario a ingresar: " + nick)
            return render_template('login.html', mensaje="Algo sucedió, intenta de nuevo !" )


# Funcion: registro
@app.route("/registro", methods=["POST"])
def registro():
    app.logger.debug("[NO_USER] registro: inicia registro")
    if request.method == "POST":
        try:
            nombres = request.form.get("nombres")
            apellidos = request.form.get("apellidos")
            email = request.form.get("email")
            clave = request.form.get("clave")
            pwdseguro = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(clave))
            nickname = email.lower()
            newUsuario = Usuario(nombres=nombres, apellidos=apellidos, pwd=pwdseguro, email=email.lower(), nickName=nickname)
            db.session.add(newUsuario)
            app.logger.debug("[" + nickname + "] registro: Usuario adicionado a BD: " + newUsuario.nombres + " - mail - " + newUsuario.email)
            urlconfirma = URL_CONFIRMA +"usr=" + nickname + "&id=" + sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(email+pwdseguro))
            app.logger.debug("[" + nickname + "] registro: armó urlconfirma: " + urlconfirma)
            txbody = "<p>Hola, solo falta un paso para que empieces a intercambiar tus videojuegos. \n \n Confirma aquí: " + urlconfirma + " </p>"

            app.logger.debug("[" + nickname + "] registro: va a enviar correo")
            if enviar_correo(SUBJECT_REGISTRO, MAIL_REGISTRO, nickname, txbody, html_body=txbody) == 1:
                app.logger.debug("[" + nickname + "] registro: envió mail a : " + newUsuario.nombres + " - mail - " + newUsuario.email)
                db.session.commit()
                app.logger.debug("[" + nickname + "] registro: Usuario registrado: " + newUsuario.nombres + " - mail - " + newUsuario.email)
                #app.logger.debug("registro: Usuario registrado: " + newUsuario.nombres + " - mail - " + newUsuario.email + " " + clave + " " + pwdseguro)
                return render_template('login.html', mensaje="Ya estás registrado " + newUsuario.nombres + ". Confirma en tu correo para finalizar!")
        except:
            raise
            app.logger.error("[" + email + "] registro: Usuario a registrar: " + nombres + " - mail - " + pwdseguro)
            return render_template('error.html', mensaje="Error en registro!")


# Funcion: confirma
@app.route("/confirma", methods=["GET"])
def confirma():
    app.logger.debug("[NO_USER] confirma: inicia confirmación ")
    if request.method == "GET":
        try:
            usr = request.args.get("usr").lower()
            id = request.args.get("id")

            #Busca el usuario para validar
            app.logger.debug("[NO_USER] confirma: Usuario a confirmar: " + usr)
            obUsuario = db.session.query(Usuario.nickName).filter_by(nickName=usr).one_or_none()

            if obUsuario is not None:
                pwd= obUsuario.pwd
                app.logger.debug("[" + usr + "] confirma: Usuario recuperado: " + usr+pwd )

                idvalida = sha256_crypt.using(salt=Config.SECRET_SALT, rounds=5000).hash(str(usr+pwd))

                if idvalida==id:
                    obUsuario.activo = ESTADO_USR_ACTIVO;
                    db.session.commit()
                    app.logger.debug("[" + usr + "] confirma: Usuario activo: " + obUsuario.nombres + " - mail - " + obUsuario.email)
                    return render_template('login.html', mensaje="Ya estás activo " + obUsuario.nombres + ". Ingresa!")
                else:
                    return render_template('error.html', mensaje="Hubo un error " + obUsuario.nombres + ". Vuelve a intentarlo desde tu correo!")
            else:
                return render_template('login.html',
                                       mensaje="El usuario " + usr + ", no se encuentra registrado. Regístrate antes!")
        except:
            app.logger.error("[" + usr + "] confirma: Usuario a confirmar: " + usr)
            return render_template('error.html', mensaje="Error en confirmación!")

# Funcion: enviar_correo
def enviar_correo(subject, sender, recipients, text_body,
                  cc=None, bcc=None, html_body=None):
    app.logger.debug("[" + recipients + "] enviar_correo: Inicia ")
    msg = Message(subject, sender=sender, recipients=recipients, cc=cc, bcc=bcc)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    try:
        app.logger.debug("[" + recipients + "] va enviar_correo: SEND ")
        msg.send(msg)
        app.logger.debug("[" + recipients + "] Si lo envió ")
        return 1
    except SMTPException:
        #raise
        app.logger.debug("[" + nickname + "] enviar_correo: error en enviar correo")
        logger.exception("Ocurrió un error al enviar el email")
        return 0
    #Thread(target=_send_async_email, args=(current_app._get_current_object(), msg)).start()

if __name__ == '__main__':
    app.logger.debug("[NO_USER] main: **************************************************")
    app.logger.debug("[NO_USER] main: Importa configuracion")
    app.config.from_object(DevelopmentConfig)
    app.logger.debug("[NO_USER] main: Inicializa DB")
    db.init_app(app)
    app.logger.debug("[NO_USER] main: Crea la BD")

    with app.app_context():
        db.create_all()
    app.logger.debug("[NO_USER] main: Run aplicacion 8000")
    app.run(port=8000)
