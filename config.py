import os
# base de datos creada
# Usuario: ex4playdevadmin - Pass: JuSo2020@
# BD - ex4playDEV
# Usuario: root - Pass: Ju$o2020@+%
# BD - ex4playDEV

class Config(object):
    SECRET_KEY = 'eX-4-P-l-A-y-S-e-C-r-E-t-A'
    SECRET_SALT = 'lnuyjask8790j22'


class DevelopmentConfig(Config):
    DEBUG = True
    #DEV
    #Usuario: ex4playdevadmin Password: JuSo2020% Database: ex4playdev
    #SQLALCHEMY_DATABASE_URI  = 'mysql://ex4playdevadmin:JuSo2020%@localhost/ex4playdev'
    #PRD
    #Usuario: root Password: Ju$o2020@+% Database: ex4playdev
    SQLALCHEMY_DATABASE_URI  = 'mysql://root:Ju$o2020@+%@localhost/ex4playdev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
