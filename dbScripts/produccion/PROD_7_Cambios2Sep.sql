ALTER TABLE `clasificacion`
CHANGE COLUMN `valorPuntos` `valorPuntos` FLOAT NULL DEFAULT NULL ;

ALTER TABLE `qya`
ADD COLUMN `leido` INT NOT NULL DEFAULT 0 AFTER `PregResp`;
