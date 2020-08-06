ALTER TABLE `ex4play$ex4playprod`.`saldos`
ADD COLUMN `Saldos` FLOAT NULL AFTER `ValorCobrado`;

ALTER TABLE `ex4play$ex4playprod`.`usuario`
ADD COLUMN `aceptater` INT NULL DEFAULT 0 AFTER `sancionado`;

CREATE TABLE `ex4play$ex4playprod`.`fotoejeusuario` (
  `idFotoejeusuario` INT NOT NULL AUTO_INCREMENT,
  `ejeUsuarioId` INT NOT NULL,
  `foto` BLOB NOT NULL,
  `fechacrea` DATETIME NOT NULL,
  `activa` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`idFotoejeusuario`));


ALTER TABLE `ex4play$ex4playprod`.`fotoejeusuario`
ADD INDEX `ejeusuario1_idx` (`ejeUsuarioId` ASC) VISIBLE;
;
ALTER TABLE `ex4play$ex4playprod`.`fotoejeusuario`
ADD CONSTRAINT `ejeusuario1`
  FOREIGN KEY (`ejeUsuarioId`)
  REFERENCES `ex4play$ex4playprod`.`ejeusuario` (`idEjeUsuario`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;

ALTER TABLE `ex4play$ex4playprod`.`fotousuario`
CHANGE COLUMN `foto` `foto` LONGBLOB NOT NULL ;

ALTER TABLE `ex4play$ex4playprod`.`fotoejeusuario`
CHANGE COLUMN `foto` `foto` LONGBLOB NOT NULL ;
