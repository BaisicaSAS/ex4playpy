import os
# base de datos creada
# Usuario: ex4playdevadmin - Pass: JuSo2020@
# BD - ex4playDEV
# Usuario: root - Pass: Ju$o2020@+%
# BD - ex4playDEV

# BD - ex4playprod - Producción AWS LightSail
# Usuario: root - Pass: Ju$o2020+%px10n_env
DB_URI = "mysql://{username}:{password}@{hostname}/{databasename}".format(
    username="ex4play",
    password="Ju$o2020+%px10n_env",
    hostname="ex4play.mysql.pythonanywhere-services.com",
    databasename="ex4play$ex4playprod"
)

class Config(object):
    SECRET_KEY = 'eX-4-P-l-A-y-S-e-C-r-E-t-A'
    SECRET_SALT = 'lnuyjask8790j22'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI  = DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    #DEV

    #Usuario: ex4playdevadmin Password: JuSo2020% Database: ex4playdev
    #SQLALCHEMY_DATABASE_URI  = 'mysql://ex4playdevadmin:JuSo2020%@localhost/ex4playdev'

    #Usuario: root Password: Ju$o2020@+% Database: ex4playdev
    SQLALCHEMY_DATABASE_URI  = 'mysql://root:Ju$o2020@+%@localhost/ex4playdev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
