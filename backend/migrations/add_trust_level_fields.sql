-- Migración: Agregar campos de nivel de confianza a la tabla usuarios
-- Fecha: 2025-10-25
-- Descripción: Agrega campos para trackear el nivel de confianza entre Loki y el usuario
--
-- nivel_confianza: Nivel de confianza (1-5)
--   1=Conociendo, 2=Estableciendo, 3=Construyendo, 4=Consolidado, 5=Íntimo
-- total_interacciones: Número total de mensajes intercambiados con el usuario

-- Agregar columna nivel_confianza (1-5)
ALTER TABLE usuarios ADD COLUMN nivel_confianza INTEGER DEFAULT 1;

-- Agregar columna total_interacciones (contador de mensajes)
ALTER TABLE usuarios ADD COLUMN total_interacciones INTEGER DEFAULT 0;
