ALTER TABLE `dbmaster`.`conexionusuario`
CHANGE COLUMN `ipaddr` `ipaddr` VARCHAR(128) NULL DEFAULT NULL ;

ALTER TABLE `dbmaster`.`conexionusuario`
ADD COLUMN `tipo` VARCHAR(10) NOT NULL DEFAULT 'LOGIN' AFTER `ipaddr`;
