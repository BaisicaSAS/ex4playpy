ALTER TABLE `ex4playdev`.`detallevalor`
DROP FOREIGN KEY `detallevalor_ibfk_3`;
ALTER TABLE `ex4playdev`.`detallevalor`
CHANGE COLUMN `promoId` `promoId` INT NULL ;
ALTER TABLE `ex4playdev`.`detallevalor`
ADD CONSTRAINT `detallevalor_ibfk_3`
  FOREIGN KEY (`promoId`)
  REFERENCES `ex4playdev`.`promo` (`idPromo`);

ALTER TABLE `ex4playdev`.`detallevalor`
CHANGE COLUMN `comentario` `comentario` VARCHAR(500) NULL DEFAULT NULL ;

ALTER TABLE `ex4playdev`.`detallevalorotros`
CHANGE COLUMN `comentario` `comentario` VARCHAR(500) NULL DEFAULT NULL ;

ALTER TABLE `ex4playdev`.`saldos`
DROP COLUMN `Saldos`;

ALTER TABLE `ex4playdev`.`saldos`
ADD COLUMN `TotalPuntos` FLOAT NULL DEFAULT 0 AFTER `ValorCobrado`;

ALTER TABLE `ex4playdev`.`saldos`
CHANGE COLUMN `valorPagado` `valorPagado` FLOAT NULL DEFAULT 0 ,
CHANGE COLUMN `ValorCobrado` `ValorCobrado` FLOAT NULL DEFAULT 0 ;

ALTER TABLE `ex4playdev`.`qya`
    DROP COLUMN `leido`;
