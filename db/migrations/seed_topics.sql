INSERT INTO topics (id, name, created_at)
VALUES
       (1, 'Seguridad ciudadana', '2026-03-22 17:00:00+00'::timestamptz),
       (2, 'Lucha contra la corrupción', '2026-03-22 17:00:00+00'::timestamptz),
       (3, 'Educación pública', '2026-03-22 17:00:00+00'::timestamptz),
       (4, 'Salud pública', '2026-03-22 17:00:00+00'::timestamptz),
       (5, 'Desarrollo económico', '2026-03-22 17:00:00+00'::timestamptz),
       (6, 'Infraestructura y obras públicas', '2026-03-22 17:00:00+00'::timestamptz),
       (7, 'Medio ambiente y sostenibilidad', '2026-03-22 17:00:00+00'::timestamptz),
       (8, 'Descentralización y desarrollo regional', '2026-03-22 17:00:00+00'::timestamptz),
       (9, 'Empleo y formalización laboral', '2026-03-22 17:00:00+00'::timestamptz),
       (10, 'Agricultura y desarrollo rural', '2026-03-22 17:00:00+00'::timestamptz),
       (11, 'Lucha contra el narcotráfico', '2026-03-22 17:00:00+00'::timestamptz),
       (12, 'Reforma del Estado', '2026-03-22 17:00:00+00'::timestamptz),
       (13, 'Vivienda y urbanismo', '2026-03-22 17:00:00+00'::timestamptz),
       (14, 'Transporte y movilidad', '2026-03-22 17:00:00+00'::timestamptz),
       (15, 'Inclusión social', '2026-03-22 17:00:00+00'::timestamptz),
       (16, 'Justicia y sistema judicial', '2026-03-22 17:00:00+00'::timestamptz),
       (17, 'Economía digital e innovación', '2026-03-22 17:00:00+00'::timestamptz),
       (18, 'Gestión de recursos naturales', '2026-03-22 17:00:00+00'::timestamptz),
       (19, 'Participación ciudadana', '2026-03-22 17:00:00+00'::timestamptz),
       (20, 'Seguridad alimentaria', '2026-03-22 17:00:00+00'::timestamptz),
       (32, 'Minería e industrias extractivas', '2026-03-22 17:00:00+00'::timestamptz),
       (33, 'Transporte y conectividad', '2026-03-22 17:00:00+00'::timestamptz),
       (35, 'Participación ciudadana y democracia', '2026-03-22 17:00:00+00'::timestamptz),
       (38, 'Protección social y programas sociales', '2026-03-22 17:00:00+00'::timestamptz),
       (39, 'Ciencia, tecnología e innovación', '2026-03-22 17:00:00+00'::timestamptz),
       (40, 'Relaciones exteriores y comercio', '2026-03-22 17:00:00+00'::timestamptz)
ON CONFLICT (id) DO UPDATE SET name       = EXCLUDED.name,
                               created_at = EXCLUDED.created_at;

SELECT setval(pg_get_serial_sequence('topics', 'id'), COALESCE((SELECT MAX(id) FROM topics), 1));
