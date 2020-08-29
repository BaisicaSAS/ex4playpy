CREATE TABLE `busquedausuario` (
  `idBusquedausuario` int NOT NULL AUTO_INCREMENT,
  `usuarioId` int NOT NULL,
  `busqueda` varchar(100) DEFAULT NULL,
  `resultados` int NOT NULL,
  `fechacrea` datetime DEFAULT NULL,
  PRIMARY KEY (`idBusquedausuario`),
  KEY `usuarioId` (`usuarioId`),
  CONSTRAINT `busquedausuario_ibfk_1` FOREIGN KEY (`usuarioId`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8


ALTER TABLE `ejeusuario`
ADD COLUMN `cuarentena` int NOT NULL default 0 AFTER `bloqueado`;
