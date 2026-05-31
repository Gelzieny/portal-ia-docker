
    INSERT INTO prompt_categories (name, slug, color, sort_order) VALUES
      ('Redação Oficial',        'redacao-oficial', '#1a5e38', 1),
      ('Análise de Dados',       'analise-dados',   '#185FA5', 2),
      ('Atendimento ao Cidadão', 'atendimento',     '#854F0B', 3),
      ('Jurídico',               'juridico',        '#993556', 4),
      ('Resumo e Síntese',       'resumo',          '#0F6E56', 5),
      ('Gestão e Planejamento',  'gestao',          '#534AB7', 6);

    INSERT INTO doc_sections (title, slug, sort_order) VALUES
      ('Introdução',        'introducao',    1),
      ('Guia de Uso',       'guia-de-uso',   2),
      ('Referência da API', 'api-reference', 3),
      ('Políticas',         'politicas',     4);
  