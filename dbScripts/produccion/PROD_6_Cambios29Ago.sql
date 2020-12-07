ALTER TABLE `detallevalor`
ADD COLUMN `comentario` VARCHAR(100) NULL AFTER `multiplicador`;


CREATE TABLE `detallevalorotros` (
  `idDetValOtr` int NOT NULL AUTO_INCREMENT,
  `usuarioId` int DEFAULT NULL,
  `promoId` int NOT NULL,
  `tipo` int DEFAULT NULL,
  `valorPaga` float DEFAULT NULL,
  `valorCobra` float DEFAULT NULL,
  `multiplicador` float DEFAULT NULL,
  `comentario` varchar(100) DEFAULT NULL,
  `fechacrea` datetime DEFAULT NULL,
  PRIMARY KEY (`idDetValOtr`),
  KEY `usuarioId` (`usuarioId`),
  KEY `promoId` (`promoId`),
  CONSTRAINT `detallevalorotros_ibfk_1` FOREIGN KEY (`usuarioId`) REFERENCES `usuario` (`idUsuario`),
  CONSTRAINT `detallevalorotros_ibfk_2` FOREIGN KEY (`promoId`) REFERENCES `promo` (`idPromo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `promo`
ADD COLUMN `aplicasobre` VARCHAR(2) NULL DEFAULT 'IC' AFTER `multiplicador`;

ALTER TABLE `promo`
ADD COLUMN `puntos` int NULL DEFAULT 0 AFTER `multiplicador`;


INSERT INTO `promo` (`descripcion`, `multiplicador`, puntos, `aplicasobre`, `activa`,
`fechainicia`, `fechafinal`, `fechacrea`) VALUES ('Te regalamos 180 puntos cuando publiques tu primer videojuego',
0, 180, 'RG', '1', '2020-09-01', '2021-01-01', '2020-08-28');


ALTER TABLE `ejeusuario`
ADD COLUMN `comprometido` INT NULL DEFAULT 0 AFTER `cuarentena`,
CHANGE COLUMN `publicado` `publicado` INT NOT NULL DEFAULT 0 ,
CHANGE COLUMN `bloqueado` `bloqueado` INT NOT NULL DEFAULT 0 ,
CHANGE COLUMN `valor` `valor` FLOAT NOT NULL DEFAULT 0 ;
