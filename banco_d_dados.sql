CREATE DATABASE db_coleta2;
USE db_coleta2;
DROP TABLE tb_registro;

CREATE TABLE  tb_registro (
id int (10) auto_increment NOT NULL, 
tempo_registro DATETIME,
co2 FLOAT (20),
poeira1 FLOAT (20),
poeira2 FLOAT (20),
altitude FLOAT (20),
umidade FLOAT (20),
temperatura FLOAT (20),
pressao FLOAT (20),
status_registro VARCHAR (200),
PRIMARY KEY (id)
); 

SELECT * FROM tb_registro;








CREATE TABLE  tb_registros_teste(
id_registro int (10) auto_increment NOT NULL, 
temperatura_c decimal(10,2),
pressao_pa decimal(10,2),
altitude_m decimal(10,2),
umidade_ur decimal(10,2),
co2_ppm decimal(10,2),
data_registro datetime,
poeira1_mg_m3  decimal(10,2),
poeira2_mg_m3  decimal(10,2),
status_registro VARCHAR (200),
PRIMARY KEY (id_registro)
); 

SELECT * FROM tb_registros_teste;

update tb_registros_teste set status_registro = True where 1 = 1;
