import os
# base de datos creada
# Usuario: ex4playdevadmin - Pass: JuSo2020@
# BD - ex4playDEV
# Usuario: root - Pass: JuSo2020@+*
# BD - ex4playDEV

#Python anywhere
DB_URI = "mysql://{username}:{password}@{hostname}/{databasename}".format(
    username="",
    password="",
    hostname="",
    databasename=""
)

#github
class Config(object):
    SECRET_KEY = 'eX-4-P-l-A-y-S-e-C-r-E-t-A'
    SECRET_SALT = 'lnuyjask8790j22'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    #DEV

    #Usuario: ex4playdevadmin Password: JuSo2020% Database: ex4playdev
    #SQLALCHEMY_DATABASE_URI  = 'mysql://ex4playdevadmin:JuSo2020%@localhost/ex4playdev'

    #Usuario: root Password: Ju$o2020@+% Database: ex4playdev
    SQLALCHEMY_DATABASE_URI  = 'mysql://root:Ju$o2020@+%@localhost/ex4playdev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
