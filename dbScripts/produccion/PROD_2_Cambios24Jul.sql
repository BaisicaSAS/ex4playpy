--Actualiza los nombres de los videojuegos, adiciona la consola

update dbmaster.videojuego v
set v.nombre = concat(v.nombre, " [", (select c.nombre from dbmaster.consola c where c.idconsola = v.consolaid), "]")
where v.idvj > 0
