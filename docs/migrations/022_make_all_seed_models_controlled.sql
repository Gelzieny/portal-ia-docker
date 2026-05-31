
    UPDATE modelos
    SET
      requires_access_approval = TRUE,
      access_summary = CASE slug
        WHEN 'llama3-2-3b' THEN 'Acesso controlado. Solicite aprovação para uso institucional deste modelo leve de texto e classificação.'
        WHEN 'llama3-1-8b-instruct' THEN 'Acesso controlado. Solicite aprovação para tarefas de texto, redação e apoio técnico.'
        WHEN 'llama3-3-70b' THEN 'Acesso controlado para análises mais extensas e geração de conteúdo com alto contexto.'
        WHEN 'llava-7b-v1-5-fp16' THEN 'Acesso controlado para leitura de imagens, OCR básico e descrição visual.'
        WHEN 'llama3-2-vision-11b' THEN 'Acesso controlado para leitura assistida de documentos, gráficos e tabelas.'
        WHEN 'qwen3-8b' THEN 'Acesso controlado para raciocínio, código e suporte multilíngue em ambiente institucional.'
        ELSE access_summary
      END,
      access_documentation = CASE slug
        WHEN 'llama3-2-3b' THEN E'# Como usar\n\nEste modelo exige solicitação e aprovação prévia.\n\nApós aprovação, utilize o endpoint e as credenciais disponibilizados em **Meus Acessos a Modelos**.\n\n- Revise a saída antes do uso institucional\n- Não envie dados sensíveis sem base legal\n'
        WHEN 'llama3-1-8b-instruct' THEN E'# Como usar\n\nAcesso controlado para tarefas de apoio à redação, análise e instruções técnicas.\n\n- Solicite o acesso informando claramente a aplicação\n- Valide saídas críticas antes de compartilhar\n'
        WHEN 'llama3-3-70b' THEN E'# Como usar\n\nAcesso controlado para análises mais longas, sínteses complexas e apoio técnico especializado.\n\n- Utilize prompts estruturados\n- Revise respostas antes de uso oficial\n'
        WHEN 'llava-7b-v1-5-fp16' THEN E'# Como usar\n\nModelo com acesso controlado para leitura de imagens e documentos.\n\n- Faça upload do arquivo na interface homologada\n- Informe claramente a tarefa desejada\n'
        WHEN 'llama3-2-vision-11b' THEN E'# Como usar\n\nModelo multimodal com acesso controlado para leitura assistida de documentos, gráficos e conteúdo visual.\n\n- Use instruções objetivas\n- Verifique o resultado antes de consolidar informações oficiais\n'
        WHEN 'qwen3-8b' THEN E'# Como usar\n\nAcesso controlado para raciocínio, suporte técnico e código.\n\n- Estruture a entrada por contexto, tarefa e formato esperado\n- Revise o resultado antes de publicação ou decisão\n'
        ELSE access_documentation
      END
    WHERE slug IN (
      'llama3-2-3b',
      'llama3-1-8b-instruct',
      'llama3-3-70b',
      'llava-7b-v1-5-fp16',
      'llama3-2-vision-11b',
      'qwen3-8b',
      'gemini-2-5-flash',
      'gemini-2-5-pro',
      'gemini-3-pro-preview',
      'gemini-3-flash-preview',
      'gemini-3-1-pro-preview',
      'gemini-3-1-pro-preview-customtools',
      'gemini-3-1-flash-lite-preview',
      'gpt-4o-mini'
    );
