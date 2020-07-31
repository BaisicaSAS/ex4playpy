#Actualiza los nombres de los videojuegos, adiciona la consola

update ex4play$ex4playprod.videojuego v
set v.nombre = concat(v.nombre, " [", (select c.nombre from ex4play$ex4playprod.consola c where c.idconsola = v.consolaid), "]")
where v.idvj > 0
