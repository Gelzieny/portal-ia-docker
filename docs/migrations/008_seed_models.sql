
    INSERT INTO modelos
      (name, slug, provider, category, description, capabilities, status,
       context_window, usage_limit, tags, is_new, is_featured, sort_order)
    VALUES

    -- ── Meta / Ollama ──────────────────────────────────────────────────────────

    (
      'Llama 3.2 3B', 'llama3-2-3b', 'Meta / Open Source', 'texto',
      'Modelo compacto e eficiente da família LLaMA 3.2 da Meta. Ideal para tarefas de texto leves com baixo consumo de recursos, como geração de respostas curtas, sumarização básica e classificação de texto.',
      ARRAY['Geração de Texto', 'Sumarização', 'Classificação', 'Instrução'],
      'disponivel', 131072, NULL,
      ARRAY['llama', 'meta', 'ollama', 'leve', 'eficiente'],
      FALSE, FALSE, 10
    ),

    (
      'Llama 3.1 8B Instruct', 'llama3-1-8b-instruct', 'Meta / Open Source', 'texto',
      'Versão instrução da LLaMA 3.1 com 8 bilhões de parâmetros. Otimizado para seguir instruções complexas, geração de código, redação e análise de documentos com janela de contexto de 128K tokens.',
      ARRAY['Instrução', 'Geração de Texto', 'Código', 'Análise', 'Redação'],
      'disponivel', 131072, NULL,
      ARRAY['llama', 'meta', 'ollama', 'instruct', '8b'],
      FALSE, TRUE, 20
    ),

    (
      'Llama 3.3 70B', 'llama3-3-70b', 'Meta / Open Source', 'texto',
      'Modelo LLaMA 3.3 de 70 bilhões de parâmetros. Desempenho comparável ao LLaMA 3.1 405B em tarefas de raciocínio, codificação e análise, com melhorias em seguir instruções e geração multilíngue.',
      ARRAY['Raciocínio', 'Código', 'Análise', 'Redação Oficial', 'Multilíngue', 'Instrução'],
      'disponivel', 131072, NULL,
      ARRAY['llama', 'meta', 'ollama', '70b', 'avancado'],
      TRUE, TRUE, 30
    ),

    (
      'LLaVA 7B v1.5 FP16', 'llava-7b-v1-5-fp16', 'Open Source', 'visao',
      'Large Language and Vision Assistant (LLaVA) versão 1.5 com 7B parâmetros em precisão FP16. Combina um encoder visual com LLaMA para análise de imagens, descrição visual e resposta a perguntas sobre conteúdo gráfico.',
      ARRAY['Análise de Imagem', 'Descrição Visual', 'Visual QA', 'OCR'],
      'disponivel', 4096, NULL,
      ARRAY['llava', 'visao', 'ollama', 'multimodal', 'imagem'],
      FALSE, FALSE, 40
    ),

    (
      'Llama 3.2 Vision 11B', 'llama3-2-vision-11b', 'Meta / Open Source', 'visao',
      'Modelo multimodal da família LLaMA 3.2 com capacidade de visão computacional. Suporta análise de imagens, gráficos, tabelas e documentos escaneados com janela de contexto de 128K tokens.',
      ARRAY['Análise de Imagem', 'Documentos', 'Gráficos', 'Tabelas', 'Visual QA', 'OCR'],
      'disponivel', 131072, NULL,
      ARRAY['llama', 'meta', 'ollama', 'vision', 'multimodal', '11b'],
      TRUE, FALSE, 50
    ),

    -- ── Alibaba / Ollama ───────────────────────────────────────────────────────

    (
      'Qwen3 8B', 'qwen3-8b', 'Alibaba', 'texto',
      'Modelo Qwen3 de 8B parâmetros da Alibaba. Destaca-se em raciocínio lógico, geração de código, matemática e suporte multilíngue, com arquitetura de atenção aprimorada e janela de contexto de 32K tokens.',
      ARRAY['Raciocínio', 'Código', 'Matemática', 'Multilíngue', 'Instrução'],
      'disponivel', 32768, NULL,
      ARRAY['qwen', 'alibaba', 'ollama', 'multilíngue', 'raciocínio'],
      TRUE, FALSE, 60
    ),

    -- ── Google Gemini ──────────────────────────────────────────────────────────

    (
      'Gemini 2.5 Flash', 'gemini-2-5-flash', 'Google', 'multimodal',
      'Modelo Gemini 2.5 Flash do Google, otimizado para velocidade e eficiência. Suporta texto, imagens, áudio e vídeo com janela de contexto de 1 milhão de tokens. Ideal para tarefas que exigem baixa latência e alto throughput.',
      ARRAY['Texto', 'Imagem', 'Áudio', 'Vídeo', 'Contexto Longo', 'Raciocínio', 'Código'],
      'disponivel', 1048576, NULL,
      ARRAY['gemini', 'google', 'multimodal', 'flash', 'rapido'],
      FALSE, TRUE, 70
    ),

    (
      'Gemini 2.5 Pro', 'gemini-2-5-pro', 'Google', 'multimodal',
      'Modelo Gemini 2.5 Pro do Google, versão avançada com estado da arte em raciocínio e codificação. Janela de contexto de 1 milhão de tokens com suporte a texto, imagens, áudio e vídeo. Recomendado para análises complexas e geração de documentos extensos.',
      ARRAY['Texto', 'Imagem', 'Áudio', 'Vídeo', 'Contexto Longo', 'Raciocínio Avançado', 'Código', 'Análise'],
      'disponivel', 1048576, NULL,
      ARRAY['gemini', 'google', 'multimodal', 'pro', 'avancado'],
      FALSE, TRUE, 80
    ),

    (
      'Gemini 3 Pro Preview', 'gemini-3-pro-preview', 'Google', 'multimodal',
      'Preview experimental do Gemini 3 Pro. Modelo de próxima geração do Google com capacidades avançadas de raciocínio multimodal, janela de contexto expandida e melhorias significativas em seguir instruções complexas.',
      ARRAY['Texto', 'Imagem', 'Áudio', 'Vídeo', 'Raciocínio Avançado', 'Código', 'Análise'],
      'beta', 2097152, NULL,
      ARRAY['gemini', 'google', 'preview', 'experimental', 'next-gen'],
      TRUE, FALSE, 90
    ),

    (
      'Gemini 3 Flash Preview', 'gemini-3-flash-preview', 'Google', 'multimodal',
      'Preview experimental do Gemini 3 Flash. Versão rápida da próxima geração do Gemini 3, mantendo baixa latência com melhorias em capacidades multimodais e raciocínio sobre documentos longos.',
      ARRAY['Texto', 'Imagem', 'Áudio', 'Vídeo', 'Contexto Longo', 'Raciocínio', 'Código'],
      'beta', 1048576, NULL,
      ARRAY['gemini', 'google', 'preview', 'flash', 'experimental'],
      TRUE, FALSE, 100
    ),

    (
      'Gemini 3.1 Pro Preview', 'gemini-3-1-pro-preview', 'Google', 'multimodal',
      'Preview do Gemini 3.1 Pro com refinamentos sobre o Gemini 3 Pro. Melhoras em raciocínio matemático, análise de documentos longos e geração de código com suporte a 2M tokens de contexto.',
      ARRAY['Texto', 'Imagem', 'Áudio', 'Vídeo', 'Raciocínio', 'Matemática', 'Código'],
      'beta', 2097152, NULL,
      ARRAY['gemini', 'google', 'preview', 'pro', 'experimental'],
      TRUE, FALSE, 110
    ),

    (
      'Gemini 3.1 Pro Preview Custom Tools', 'gemini-3-1-pro-preview-customtools', 'Google', 'multimodal',
      'Variante do Gemini 3.1 Pro Preview com suporte aprimorado a ferramentas customizadas (Function Calling e Tool Use). Ideal para integrações com sistemas externos, chamadas de API e agentes de IA que precisam interagir com serviços do Estado.',
      ARRAY['Texto', 'Imagem', 'Function Calling', 'Tool Use', 'Agentes', 'Integração API'],
      'beta', 2097152, NULL,
      ARRAY['gemini', 'google', 'preview', 'tools', 'agentes', 'function-calling'],
      TRUE, FALSE, 120
    ),

    (
      'Gemini 3.1 Flash Lite Preview', 'gemini-3-1-flash-lite-preview', 'Google', 'multimodal',
      'Versão mais leve e eficiente do Gemini 3.1 Flash. Otimizado para alta velocidade e baixo custo computacional, ideal para automações em larga escala, processamento em batch e tarefas de classificação e extração.',
      ARRAY['Texto', 'Imagem', 'Classificação', 'Extração', 'Sumarização', 'Código'],
      'beta', 1048576, NULL,
      ARRAY['gemini', 'google', 'preview', 'flash', 'lite', 'eficiente'],
      TRUE, FALSE, 130
    ),

    -- ── OpenAI ─────────────────────────────────────────────────────────────────

    (
      'GPT-4o Mini', 'gpt-4o-mini', 'OpenAI', 'multimodal',
      'Versão compacta e eficiente do GPT-4o da OpenAI. Combina capacidades de visão e texto com latência reduzida e custo otimizado. Suporta análise de imagens, geração de código e raciocínio com janela de contexto de 128K tokens.',
      ARRAY['Texto', 'Imagem', 'Código', 'Análise', 'Raciocínio', 'Instrução'],
      'disponivel', 128000, NULL,
      ARRAY['gpt', 'openai', 'multimodal', 'mini', 'eficiente'],
      FALSE, FALSE, 140
    )

    ON CONFLICT (slug) DO NOTHING;
