#diciona campo email en cambiosusuario

ALTER TABLE `ex4playdev`.`cambiosusuario`
ADD COLUMN `email` VARCHAR(100) NULL AFTER `celular`;
