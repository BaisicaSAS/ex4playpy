#diciona campo email en cambiosusuario

ALTER TABLE `ex4play$ex4playprod`.`cambiosusuario`
ADD COLUMN `email` VARCHAR(100) NULL AFTER `celular`;
