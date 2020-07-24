ALTER TABLE `ex4playdev`.`conexionusuario`
CHANGE COLUMN `ipaddr` `ipaddr` VARCHAR(128) NULL DEFAULT NULL ;

ALTER TABLE `ex4playdev`.`conexionusuario`
ADD COLUMN `tipo` VARCHAR(10) NOT NULL DEFAULT 'LOGIN' AFTER `ipaddr`;
