-- =============================================================================
-- SCRIPT DE CREACIÓN DE BASE DE DATOS: framework_style
-- Generado a partir de los modelos SQLAlchemy de FRAMEWORK_BACKEND
-- Motor: MySQL 8.0+ / MariaDB 10.3+
-- Codificación: utf8mb4_unicode_ci
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `framework_style`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `framework_style`;

SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- 1. TABLA: users
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `username` VARCHAR(50) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `hashed_password` VARCHAR(255) NOT NULL,
  `full_name` VARCHAR(100) NULL,
  `profile_picture` VARCHAR(255) NULL,
  `last_login` DATETIME NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_username` (`username`),
  UNIQUE KEY `uq_users_email` (`email`),
  KEY `ix_users_id` (`id`),
  KEY `ix_users_username` (`username`),
  KEY `ix_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. TABLA: clientes
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `clientes`;
CREATE TABLE `clientes` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `nombre` VARCHAR(160) NOT NULL,
  `contacto_nombre` VARCHAR(120) NULL,
  `contacto_correo` VARCHAR(160) NULL,
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. TABLA: proyectos
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `proyectos`;
CREATE TABLE `proyectos` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `nombre` VARCHAR(160) NOT NULL,
  `tipo` ENUM('nuevo', 'rediseño') NOT NULL DEFAULT 'nuevo',
  `cliente_id` BIGINT NULL,
  `plataforma` VARCHAR(80) NULL,
  `nivel_diseno_objetivo` ENUM('bajo', 'medio', 'alto') NOT NULL DEFAULT 'medio',
  `estado` ENUM('en_proceso', 'en_espera', 'completado', 'detenido') NOT NULL DEFAULT 'en_proceso',
  `fase_actual_id` INT NOT NULL DEFAULT 1,
  `user_id` INT NOT NULL,
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_proyectos_cliente_id` (`cliente_id`),
  KEY `fk_proyectos_user_id` (`user_id`),
  CONSTRAINT `fk_proyectos_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_proyectos_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. TABLA: archivos
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `archivos`;
CREATE TABLE `archivos` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `fase_id` INT NULL,
  `contexto_tipo` VARCHAR(40) NULL,
  `contexto_id` BIGINT NULL,
  `nombre_original` VARCHAR(255) NOT NULL,
  `ruta_almacenamiento` VARCHAR(500) NOT NULL,
  `mime_type` VARCHAR(120) NULL,
  `tamano_bytes` INT NULL,
  `subido_por` INT NOT NULL,
  `subido_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_archivos_proyecto_id` (`proyecto_id`),
  KEY `fk_archivos_subido_por` (`subido_por`),
  CONSTRAINT `fk_archivos_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_archivos_usuario` FOREIGN KEY (`subido_por`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. TABLA: investigacion_informe
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `investigacion_informe`;
CREATE TABLE `investigacion_informe` (
  `proyecto_id` BIGINT NOT NULL,
  `problema` TEXT NULL,
  `objetivo` TEXT NULL,
  `producto` TEXT NULL,
  `expectativas` TEXT NULL,
  `referencias` JSON NULL,
  `analisis_actual` TEXT NULL,
  `restricciones` TEXT NULL,
  `identidad_marca` JSON NULL,
  `conclusiones_fase2` TEXT NULL,
  `actualizado_en` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`proyecto_id`),
  CONSTRAINT `fk_investigacion_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 6. TABLA: arquetipos_usuario
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `arquetipos_usuario`;
CREATE TABLE `arquetipos_usuario` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `nombre` VARCHAR(120) NOT NULL,
  `etiqueta` VARCHAR(60) NULL,
  `avatar_archivo_id` BIGINT NULL,
  `orden` INT DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `fk_arquetipos_proyecto_id` (`proyecto_id`),
  KEY `fk_arquetipos_avatar_id` (`avatar_archivo_id`),
  CONSTRAINT `fk_arquetipos_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_arquetipos_avatar` FOREIGN KEY (`avatar_archivo_id`) REFERENCES `archivos` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Perfiles representativos de los usuarios finales (ej. Estudiante, Docente). Ayudan a enfocar el diseño en sus necesidades reales.';

-- -----------------------------------------------------------------------------
-- 7. TABLA: arquetipo_necesidades
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `arquetipo_necesidades`;
CREATE TABLE `arquetipo_necesidades` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `arquetipo_id` BIGINT NOT NULL,
  `descripcion` VARCHAR(255) NOT NULL,
  `orden` INT DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `fk_necesidades_arquetipo_id` (`arquetipo_id`),
  CONSTRAINT `fk_necesidades_arquetipo` FOREIGN KEY (`arquetipo_id`) REFERENCES `arquetipos_usuario` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 8. TABLA: nodos_pantalla
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `nodos_pantalla`;
CREATE TABLE `nodos_pantalla` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `nombre` VARCHAR(120) NOT NULL,
  `tipo` ENUM('modulo', 'pantalla', 'componente', 'texto') NOT NULL DEFAULT 'pantalla',
  `icono` VARCHAR(60) NULL,
  `descripcion` VARCHAR(255) NULL,
  `pos_x` INT DEFAULT 0,
  `pos_y` INT DEFAULT 0,
  `prioridad` VARCHAR(20) NULL,
  `estado_verificacion` ENUM('pendiente', 'en_revision', 'verificado') DEFAULT 'pendiente',
  `enlace_diseno_externo` VARCHAR(500) NULL,
  `fase_creacion` INT DEFAULT 2,
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_nodos_proyecto_id` (`proyecto_id`),
  CONSTRAINT `fk_nodos_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 9. TABLA: nodo_conexiones
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `nodo_conexiones`;
CREATE TABLE `nodo_conexiones` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `nodo_origen_id` BIGINT NOT NULL,
  `nodo_destino_id` BIGINT NOT NULL,
  `tipo_conexion` ENUM('navegacion', 'jerarquia') DEFAULT 'navegacion',
  PRIMARY KEY (`id`),
  KEY `fk_conexiones_proyecto_id` (`proyecto_id`),
  KEY `fk_conexiones_origen_id` (`nodo_origen_id`),
  KEY `fk_conexiones_destino_id` (`nodo_destino_id`),
  CONSTRAINT `fk_conexiones_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_conexiones_origen` FOREIGN KEY (`nodo_origen_id`) REFERENCES `nodos_pantalla` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_conexiones_destino` FOREIGN KEY (`nodo_destino_id`) REFERENCES `nodos_pantalla` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 10. TABLA: contenido_items
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `contenido_items`;
CREATE TABLE `contenido_items` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `nodo_id` BIGINT NULL,
  `tipo` ENUM('texto', 'imagen', 'otro') NOT NULL,
  `nombre` VARCHAR(160) NOT NULL,
  `detalle` VARCHAR(120) NULL,
  `prioridad` ENUM('alta', 'media', 'baja') NOT NULL DEFAULT 'media',
  `archivo_id` BIGINT NULL,
  `orden` INT DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `fk_contenido_proyecto_id` (`proyecto_id`),
  KEY `fk_contenido_nodo_id` (`nodo_id`),
  KEY `fk_contenido_archivo_id` (`archivo_id`),
  CONSTRAINT `fk_contenido_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_contenido_nodo` FOREIGN KEY (`nodo_id`) REFERENCES `nodos_pantalla` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_contenido_archivo` FOREIGN KEY (`archivo_id`) REFERENCES `archivos` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 11. TABLA: wireframes
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `wireframes`;
CREATE TABLE `wireframes` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `nodo_id` BIGINT NULL,
  `archivo_id` BIGINT NOT NULL,
  `titulo` VARCHAR(255) NULL,
  `version` VARCHAR(10) DEFAULT 'v1',
  `generado_por_ia` TINYINT(1) DEFAULT 0,
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_wireframes_proyecto_id` (`proyecto_id`),
  KEY `fk_wireframes_nodo_id` (`nodo_id`),
  KEY `fk_wireframes_archivo_id` (`archivo_id`),
  CONSTRAINT `fk_wireframes_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_wireframes_nodo` FOREIGN KEY (`nodo_id`) REFERENCES `nodos_pantalla` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_wireframes_archivo` FOREIGN KEY (`archivo_id`) REFERENCES `archivos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 12. TABLA: wireframe_checklist_items
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `wireframe_checklist_items`;
CREATE TABLE `wireframe_checklist_items` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `wireframe_id` BIGINT NOT NULL,
  `pregunta` VARCHAR(255) NOT NULL,
  `origen` ENUM('manual', 'ia') NOT NULL DEFAULT 'ia',
  `estado` ENUM('pendiente', 'aceptado', 'descartado') NOT NULL DEFAULT 'pendiente',
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_wireframe_chk_wf_id` (`wireframe_id`),
  CONSTRAINT `fk_wireframe_chk_wireframe` FOREIGN KEY (`wireframe_id`) REFERENCES `wireframes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 13. TABLA: diseno_conceptual_checklist_items
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `diseno_conceptual_checklist_items`;
CREATE TABLE `diseno_conceptual_checklist_items` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `pregunta` VARCHAR(255) NOT NULL,
  `origen` ENUM('manual', 'ia') NOT NULL DEFAULT 'ia',
  `estado` ENUM('pendiente', 'aceptado', 'descartado') NOT NULL DEFAULT 'pendiente',
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_conceptual_chk_proy_id` (`proyecto_id`),
  CONSTRAINT `fk_conceptual_chk_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 14. TABLA: diseno_visual_config
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `diseno_visual_config`;
CREATE TABLE `diseno_visual_config` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `fuente_principal` VARCHAR(100) DEFAULT 'Inter',
  `fuente_secundaria` VARCHAR(100) DEFAULT 'Roboto',
  `estilo_iconos` VARCHAR(50) DEFAULT 'lineal',
  `libreria_iconos` VARCHAR(50) DEFAULT 'Bootstrap Icons',
  `grosor_iconos` FLOAT DEFAULT 1.5,
  `escala_espaciado_base` INT DEFAULT 8,
  `radio_borde_base` INT DEFAULT 8,
  `grid_columnas` INT DEFAULT 12,
  `grid_gutter` INT DEFAULT 16,
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_diseno_visual_config_proyecto` (`proyecto_id`),
  CONSTRAINT `fk_visual_cfg_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 15. TABLA: diseno_visual_colores
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `diseno_visual_colores`;
CREATE TABLE `diseno_visual_colores` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `hex_code` VARCHAR(7) NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `token_name` VARCHAR(100) NULL,
  `uso` VARCHAR(100) NOT NULL,
  `orden` INT DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `fk_visual_colores_proy_id` (`proyecto_id`),
  CONSTRAINT `fk_visual_colores_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 16. TABLA: diseno_visual_tipografias
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `diseno_visual_tipografias`;
CREATE TABLE `diseno_visual_tipografias` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `estilo` VARCHAR(100) NOT NULL,
  `tamano_px` INT NOT NULL,
  `peso` VARCHAR(50) NOT NULL,
  `interlineado` FLOAT NOT NULL,
  `tipo_fuente` VARCHAR(50) DEFAULT 'Principal',
  `orden` INT DEFAULT 0,
  `letter_spacing` FLOAT NULL,
  `line_height_px` INT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_visual_tipografias_proy_id` (`proyecto_id`),
  CONSTRAINT `fk_visual_tipografias_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 17. TABLA: diseno_visual_iconos
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `diseno_visual_iconos`;
CREATE TABLE `diseno_visual_iconos` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `token_name` VARCHAR(100) NOT NULL,
  `svg_content` MEDIUMTEXT NOT NULL,
  `estilo` VARCHAR(50) NULL,
  PRIMARY KEY (`id`),
  KEY `fk_visual_iconos_proy_id` (`proyecto_id`),
  CONSTRAINT `fk_visual_iconos_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 18. TABLA: diseno_detallado_archivos
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `diseno_detallado_archivos`;
CREATE TABLE `diseno_detallado_archivos` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `nodo_id` BIGINT NOT NULL,
  `archivo_id` BIGINT NOT NULL,
  `estado` ENUM('pendiente', 'en_revision', 'verificado') DEFAULT 'en_revision',
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_detallado_nodo_id` (`nodo_id`),
  KEY `fk_detallado_arch_archivo_id` (`archivo_id`),
  CONSTRAINT `fk_detallado_arch_nodo` FOREIGN KEY (`nodo_id`) REFERENCES `nodos_pantalla` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_detallado_arch_archivo` FOREIGN KEY (`archivo_id`) REFERENCES `archivos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 19. TABLA: diseno_detallado_alertas
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `diseno_detallado_alertas`;
CREATE TABLE `diseno_detallado_alertas` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `diseno_archivo_id` BIGINT NOT NULL,
  `tipo` ENUM('error', 'warning', 'info') DEFAULT 'info',
  `elemento` VARCHAR(255) NOT NULL,
  `mensaje` VARCHAR(500) NOT NULL,
  `detectado` VARCHAR(100) NULL,
  `esperado` VARCHAR(100) NULL,
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_detallado_alertas_arch_id` (`diseno_archivo_id`),
  CONSTRAINT `fk_detallado_alertas_archivo` FOREIGN KEY (`diseno_archivo_id`) REFERENCES `diseno_detallado_archivos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 20. TABLA: diseno_detallado_checklist_items
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `diseno_detallado_checklist_items`;
CREATE TABLE `diseno_detallado_checklist_items` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `diseno_archivo_id` BIGINT NOT NULL,
  `pregunta` VARCHAR(255) NOT NULL,
  `estado` VARCHAR(50) NOT NULL DEFAULT 'pendiente',
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_detallado_chk_arch_id` (`diseno_archivo_id`),
  CONSTRAINT `fk_detallado_chk_archivo` FOREIGN KEY (`diseno_archivo_id`) REFERENCES `diseno_detallado_archivos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 21. TABLA: evaluaciones_esteticas
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `evaluaciones_esteticas`;
CREATE TABLE `evaluaciones_esteticas` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `proyecto_id` BIGINT NOT NULL,
  `metodo_seleccionado` VARCHAR(100) DEFAULT 'Revisión Heurística (Checklist)',
  `estado` VARCHAR(50) DEFAULT 'en_proceso',
  `encuesta_url` VARCHAR(255) DEFAULT 'https://style-eval.com/survey/abc123',
  `encuesta_activa` TINYINT(1) DEFAULT 1 NOT NULL,
  `encuesta_token` VARCHAR(64) UNIQUE NULL,
  `auto_cerrar_cupo` TINYINT(1) DEFAULT 1 NOT NULL,
  `total_respuestas` INT DEFAULT 12,
  `respuestas_completadas` INT DEFAULT 12,
  `conclusion_estado` VARCHAR(50) DEFAULT 'Aprobado',
  `conclusion_texto` TEXT NULL,
  `checklist` JSON NULL,
  `visawi_metricas` JSON NULL,
  `justificaciones` JSON NULL,
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_evaluaciones_proyecto_id` (`proyecto_id`),
  CONSTRAINT `fk_evaluaciones_proyecto` FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 22. TABLA: evaluacion_hallazgos
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `evaluacion_hallazgos`;
CREATE TABLE `evaluacion_hallazgos` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `evaluacion_id` BIGINT NOT NULL,
  `problema` TEXT NOT NULL,
  `severidad` VARCHAR(50) DEFAULT 'mayor',
  `fase_origen` INT DEFAULT 3,
  `fase_origen_nombre` VARCHAR(100) DEFAULT 'Diseño Visual',
  `resuelto` TINYINT(1) DEFAULT 0,
  `creado_en` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_hallazgos_evaluacion_id` (`evaluacion_id`),
  CONSTRAINT `fk_hallazgos_evaluacion` FOREIGN KEY (`evaluacion_id`) REFERENCES `evaluaciones_esteticas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- DATOS INICIALES SEMILLA (Opcionales, tomados de seed.py)
-- =============================================================================
INSERT INTO `users` (`id`, `username`, `email`, `hashed_password`, `full_name`)
VALUES (1, 'admin_style', 'admin@style.com', '$2b$12$e8kPq6s6Yl8w1X8V7X8P7.9y5vBvG5D7hE1K2m3n4o5p6q7r8s9t', 'Administrador STYLE')
ON DUPLICATE KEY UPDATE `email` = VALUES(`email`);

INSERT INTO `clientes` (`id`, `nombre`, `contacto_nombre`, `contacto_correo`)
VALUES (1, 'Colegio San Martín', 'Director', 'director@colegiosanmartin.edu')
ON DUPLICATE KEY UPDATE `nombre` = VALUES(`nombre`);

INSERT INTO `proyectos` (`id`, `nombre`, `tipo`, `cliente_id`, `plataforma`, `nivel_diseno_objetivo`, `estado`, `fase_actual_id`, `user_id`)
VALUES (1, 'Plataforma Educativa', 'nuevo', 1, 'Web', 'medio', 'en_proceso', 1, 1)
ON DUPLICATE KEY UPDATE `nombre` = VALUES(`nombre`);
