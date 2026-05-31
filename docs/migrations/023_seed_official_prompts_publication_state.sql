
    UPDATE prompts
    SET
      source = 'oficial',
      publication_status = 'publico',
      is_public = TRUE,
      is_active = TRUE,
      version = COALESCE(NULLIF(version, 0), 1),
      report_count = 0,
      submitted_at = NULL,
      submission_notes = NULL,
      reviewed_by = NULL,
      reviewed_at = NULL,
      review_notes = NULL,
      original_author_name = NULL
    WHERE title IN (
      'Ofício de Solicitação de Informações',
      'Memorando Interno',
      'Nota Técnica',
      'Resposta a Recurso Administrativo',
      'Análise de Relatório de Execução Orçamentária',
      'Análise Comparativa de Indicadores de Desempenho',
      'Resposta a Requerimento de Cidadão',
      'FAQ — Respostas a Perguntas Frequentes',
      'Parecer Jurídico Simplificado',
      'Análise de Cláusulas Contratuais',
      'Resumo Executivo de Documento ou Processo',
      'Ata de Reunião',
      'Plano de Ação 5W2H',
      'Análise SWOT de Projeto ou Iniciativa',
      'Relatório de Gestão Mensal'
    );

    INSERT INTO prompt_versions (
      prompt_id,
      version_number,
      title,
      description,
      content,
      variables,
      tags,
      approved_by,
      approved_at
    )
    SELECT
      p.id,
      1,
      p.title,
      p.description,
      p.content,
      p.variables,
      p.tags,
      NULL,
      COALESCE(p.created_at, NOW())
    FROM prompts p
    WHERE p.title IN (
      'Ofício de Solicitação de Informações',
      'Memorando Interno',
      'Nota Técnica',
      'Resposta a Recurso Administrativo',
      'Análise de Relatório de Execução Orçamentária',
      'Análise Comparativa de Indicadores de Desempenho',
      'Resposta a Requerimento de Cidadão',
      'FAQ — Respostas a Perguntas Frequentes',
      'Parecer Jurídico Simplificado',
      'Análise de Cláusulas Contratuais',
      'Resumo Executivo de Documento ou Processo',
      'Ata de Reunião',
      'Plano de Ação 5W2H',
      'Análise SWOT de Projeto ou Iniciativa',
      'Relatório de Gestão Mensal'
    )
      AND NOT EXISTS (
        SELECT 1
        FROM prompt_versions pv
        WHERE pv.prompt_id = p.id
          AND pv.version_number = 1
      );
  