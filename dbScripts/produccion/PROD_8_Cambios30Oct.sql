ALTER TABLE `detallevalor`
DROP FOREIGN KEY `detallevalor_ibfk_3`;

ALTER TABLE `detallevalor`
CHANGE COLUMN `promoId` `promoId` INT NULL ;
ALTER TABLE `detallevalor`

ADD CONSTRAINT `detallevalor_ibfk_3`
  FOREIGN KEY (`promoId`)
  REFERENCES `promo` (`idPromo`);


ALTER TABLE `detallevalor`
CHANGE COLUMN `comentario` `comentario` VARCHAR(500) NULL DEFAULT NULL ;

ALTER TABLE `detallevalorotros`
CHANGE COLUMN `comentario` `comentario` VARCHAR(500) NULL DEFAULT NULL ;

ALTER TABLE `saldos`
DROP COLUMN `Saldos`;
