ALTER TABLE `ex4playdev`.`saldos`
ADD COLUMN `Saldos` FLOAT NULL AFTER `ValorCobrado`;

ALTER TABLE `ex4playdev`.`usuario`
ADD COLUMN `aceptater` INT NULL DEFAULT 0 AFTER `sancionado`;

CREATE TABLE `ex4playdev`.`fotoejeusuario` (
  `idFotoejeusuario` INT NOT NULL AUTO_INCREMENT,
  `ejeUsuarioId` INT NOT NULL,
  `foto` BLOB NOT NULL,
  `fechacrea` DATETIME NOT NULL,
  `activa` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`idFotoejeusuario`));


ALTER TABLE `ex4playdev`.`fotoejeusuario`
ADD INDEX `ejeusuario1_idx` (`ejeUsuarioId` ASC) VISIBLE;
;
ALTER TABLE `ex4playdev`.`fotoejeusuario`
ADD CONSTRAINT `ejeusuario1`
  FOREIGN KEY (`ejeUsuarioId`)
  REFERENCES `ex4playdev`.`ejeusuario` (`idEjeUsuario`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;

ALTER TABLE `ex4playdev`.`fotousuario`
CHANGE COLUMN `foto` `foto` LONGBLOB NOT NULL ;

ALTER TABLE `ex4playdev`.`fotoejeusuario`
CHANGE COLUMN `foto` `foto` LONGBLOB NOT NULL ;
