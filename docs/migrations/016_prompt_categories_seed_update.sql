
    -- Atualizar descrições das categorias existentes
    UPDATE prompt_categories SET
      description = 'Ofícios, memorandos, despachos e documentos oficiais do Estado'
    WHERE slug = 'redacao-oficial';

    UPDATE prompt_categories SET
      description = 'Interpretação de dados, relatórios e indicadores governamentais'
    WHERE slug = 'analise-dados';

    UPDATE prompt_categories SET
      description = 'Respostas a cidadãos, ouvidoria e comunicação com o público'
    WHERE slug = 'atendimento';

    UPDATE prompt_categories SET
      description = 'Pareceres, análise de contratos, legislação e normativas'
    WHERE slug = 'juridico';

    UPDATE prompt_categories SET
      description = 'Síntese de documentos, atas, relatórios e textos longos'
    WHERE slug = 'resumo';

    UPDATE prompt_categories SET
      description = 'Planejamento estratégico, OKRs, indicadores e gestão de projetos'
    WHERE slug = 'gestao';

    -- Adicionar categorias novas se ainda não existirem
    INSERT INTO prompt_categories (name, slug, icon, color, description, sort_order)
    VALUES
      ('Comunicação Interna', 'comunicacao-interna',
       'Mail', '#185FA5',
       'E-mails institucionais, avisos e comunicados internos', 7),
      ('Pesquisa e Inovação', 'pesquisa-inovacao',
       'Lightbulb', '#854F0B',
       'Levantamentos, benchmarking e propostas de inovação no setor público', 8)
    ON CONFLICT (slug) DO NOTHING;
  