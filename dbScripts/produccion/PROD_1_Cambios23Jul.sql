ALTER TABLE `ex4play$ex4playprod`.`conexionusuario`
CHANGE COLUMN `ipaddr` `ipaddr` VARCHAR(128) NULL DEFAULT NULL ;

ALTER TABLE `ex4play$ex4playprod`.`conexionusuario`
ADD COLUMN `tipo` VARCHAR(10) NOT NULL DEFAULT 'LOGIN' AFTER `ipaddr`;
