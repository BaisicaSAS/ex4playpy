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
