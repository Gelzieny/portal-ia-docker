
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
      END,
      default_endpoint_base = NULL,
      default_auth_scheme = 'api_key'
    WHERE slug IN (
      'llama3-2-3b',
      'llama3-1-8b-instruct',
      'llama3-3-70b',
      'llava-7b-v1-5-fp16',
      'llama3-2-vision-11b',
      'qwen3-8b'
    );

    UPDATE modelos
    SET
      requires_access_approval = TRUE,
      access_summary = CASE slug
        WHEN 'gemini-2-5-flash' THEN 'Acesso controlado. Solicite aprovação para receber endpoint, chave e orientações de uso institucional.'
        WHEN 'gemini-2-5-pro' THEN 'Acesso controlado para uso analítico avançado. Requer aprovação e credenciais individuais.'
        WHEN 'gemini-3-pro-preview' THEN 'Acesso controlado em ambiente beta. Uso sujeito a validação do curador de modelos.'
        WHEN 'gemini-3-flash-preview' THEN 'Acesso controlado para cenários experimentais com baixa latência.'
        WHEN 'gemini-3-1-pro-preview' THEN 'Acesso controlado para experimentação avançada e contextos longos.'
        WHEN 'gemini-3-1-pro-preview-customtools' THEN 'Acesso controlado para integrações com ferramentas e fluxos agentes.'
        WHEN 'gemini-3-1-flash-lite-preview' THEN 'Acesso controlado para automações de alto volume e cenários otimizados.'
        WHEN 'gpt-4o-mini' THEN 'Acesso controlado. Solicite aprovação para receber credenciais e endpoint de integração.'
        ELSE access_summary
      END,
      access_documentation = CASE slug
        WHEN 'gemini-2-5-flash' THEN E'# Como usar\n\nEste modelo exige solicitação e aprovação prévia.\n\nApós aprovação, utilize as credenciais fornecidas em **Meus Acessos a Modelos**.\n\nExemplo em Python:\nimport requests\n\nresponse = requests.post(\n    "{{endpoint_base}}",\n    headers={\n        "Authorization": "Bearer {{access_key}}",\n        "Content-Type": "application/json"\n    },\n    json={\n        "model": "gemini-2-5-flash",\n        "messages": [{"role": "user", "content": "Resuma o relatório."}]\n    }\n)\n'
        WHEN 'gemini-2-5-pro' THEN E'# Como usar\n\nAcesso sujeito à curadoria. Use este modelo para análise mais profunda e geração de documentos extensos.\n\nExemplo em cURL:\ncurl -X POST {{endpoint_base}} \\\n  -H "Authorization: Bearer {{access_key}}" \\\n  -H "Content-Type: application/json" \\\n  -d ''{"model":"gemini-2-5-pro","messages":[{"role":"user","content":"Analise este conjunto de dados."}]}''\n'
        WHEN 'gemini-3-pro-preview' THEN E'# Como usar\n\nModelo em preview com acesso controlado. Utilize apenas em cenários homologados e revise saídas com atenção.\n'
        WHEN 'gemini-3-flash-preview' THEN E'# Como usar\n\nPreview com acesso controlado para experimentação de baixa latência. Consulte o curador para limites e finalidade autorizada.\n'
        WHEN 'gemini-3-1-pro-preview' THEN E'# Como usar\n\nModelo sujeito à curadoria por operar em modo preview avançado. Registre claramente a finalidade da aplicação ao solicitar o acesso.\n'
        WHEN 'gemini-3-1-pro-preview-customtools' THEN E'# Como usar\n\nUso recomendado em integrações com ferramentas. Após aprovação, aplique os headers e credenciais exatamente como disponibilizados em **Meus Acessos a Modelos**.\n'
        WHEN 'gemini-3-1-flash-lite-preview' THEN E'# Como usar\n\nAcesso controlado para automações de menor custo. Priorize tarefas curtas e alto volume.\n'
        WHEN 'gpt-4o-mini' THEN E'# Como usar\n\nEste modelo exige aprovação para emissão de credenciais.\n\nExemplo em Python:\nimport requests\n\nresponse = requests.post(\n    "{{endpoint_base}}",\n    headers={\n        "Authorization": "Bearer {{access_key}}",\n        "Content-Type": "application/json"\n    },\n    json={\n        "model": "gpt-4o-mini",\n        "messages": [{"role": "user", "content": "Gere um resumo executivo."}]\n    }\n)\n'
        ELSE access_documentation
      END,
      default_endpoint_base = CASE slug
        WHEN 'gemini-2-5-flash' THEN 'https://api.goia.go.gov.br/v1/models/gemini-2-5-flash/chat'
        WHEN 'gemini-2-5-pro' THEN 'https://api.goia.go.gov.br/v1/models/gemini-2-5-pro/chat'
        WHEN 'gemini-3-pro-preview' THEN 'https://api.goia.go.gov.br/v1/models/gemini-3-pro-preview/chat'
        WHEN 'gemini-3-flash-preview' THEN 'https://api.goia.go.gov.br/v1/models/gemini-3-flash-preview/chat'
        WHEN 'gemini-3-1-pro-preview' THEN 'https://api.goia.go.gov.br/v1/models/gemini-3-1-pro-preview/chat'
        WHEN 'gemini-3-1-pro-preview-customtools' THEN 'https://api.goia.go.gov.br/v1/models/gemini-3-1-pro-preview-customtools/chat'
        WHEN 'gemini-3-1-flash-lite-preview' THEN 'https://api.goia.go.gov.br/v1/models/gemini-3-1-flash-lite-preview/chat'
        WHEN 'gpt-4o-mini' THEN 'https://api.goia.go.gov.br/v1/models/gpt-4o-mini/chat'
        ELSE default_endpoint_base
      END,
      default_auth_scheme = 'bearer'
    WHERE slug IN (
      'gemini-2-5-flash',
      'gemini-2-5-pro',
      'gemini-3-pro-preview',
      'gemini-3-flash-preview',
      'gemini-3-1-pro-preview',
      'gemini-3-1-pro-preview-customtools',
      'gemini-3-1-flash-lite-preview',
      'gpt-4o-mini'
    );
