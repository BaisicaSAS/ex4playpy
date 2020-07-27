--Actualiza los nombres de los videojuegos, adiciona la consola

update ex4playdev.videojuego v
set v.nombre = concat(v.nombre, " [", (select c.nombre from ex4playdev.consola c where c.idconsola = v.consolaid), "]")
where v.idvj > 0
