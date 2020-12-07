    ALTER TABLE `ex4playdev`.`clasificacion`
    CHANGE COLUMN `valorPuntos` `valorPuntos` FLOAT NULL DEFAULT NULL ;

    ALTER TABLE `ex4playdev`.`qya`
    ADD COLUMN `leido` INT NOT NULL DEFAULT 0 AFTER `PregResp`;

