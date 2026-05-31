INSERT INTO metricas (metricas, tipo)
VALUES
    ('Taxa de compreensao', 'CompreensaoTextual'),
    ('Clareza da resposta', 'ClarezaResposta'),
    ('Teste do embed', 'TesteDoEmbed'),
    ('Direito Administrativo', 'DireitoAdministrativo'),
    ('Matematica', 'Matematica'),
    ('Raciocinio Logico', 'RaciocinioLogico'),
    ('Vibe Coding', 'VibeCoding')
ON CONFLICT (tipo) DO UPDATE
SET metricas = EXCLUDED.metricas;
