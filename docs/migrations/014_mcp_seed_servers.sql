
    UPDATE mcp_servers SET
      status            = 'disponivel',
      is_featured       = true,
      version           = '1.2.0',
      license           = 'MIT',
      compatible_models = ARRAY['Gemini 2.0 Pro', 'Gemini 2.0 Enterprise', 'Claude 3.5 Sonnet', 'Claude 3 Opus'],
      docs_url          = 'https://sei.goias.gov.br/mcp/docs',
      homepage_url      = 'https://sei.goias.gov.br',
      install_count     = 142,
      description       = 'Servidor MCP oficial para integração com o Sistema Eletrônico de Informações (SEI) do Estado de Goiás. Permite consultar processos, ler e criar documentos, verificar tramitação, listar interessados e gerar minutas de documentos oficiais diretamente através de modelos de linguagem compatíveis com o protocolo MCP. Integração segura via token de API gerado no painel do SEI.',
      tags              = ARRAY['sei', 'processos', 'documentos', 'governo', 'protocolo', 'tramitacao', 'minutas']
    WHERE slug = 'sei-mcp-server';

    INSERT INTO mcp_tools (server_id, name, description, parameters, return_type, example_call, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sei-mcp-server'),
        'buscar_processo',
        'Busca processos no SEI por número, interessado ou assunto. Retorna lista de processos com metadados básicos.',
        '[
          {"name":"numero_processo","type":"string","required":false,"description":"Número do processo no formato XXXXXXXX-X.XXXX.X.X.XXXX","example":"00600-00054321/2024-99"},
          {"name":"interessado","type":"string","required":false,"description":"Nome do interessado ou órgão para filtrar processos"},
          {"name":"assunto","type":"string","required":false,"description":"Palavras-chave para buscar no assunto do processo"},
          {"name":"unidade","type":"string","required":false,"description":"Sigla da unidade para filtrar (ex: SEGPLAN, SECTI)"}
        ]'::jsonb,
        'ProcessoSEI[]',
        '{"tool":"buscar_processo","arguments":{"numero_processo":"00600-00054321/2024-99"}}',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sei-mcp-server'),
        'ler_documento',
        'Lê o conteúdo completo de um documento do SEI a partir do seu ID. Retorna texto, metadados e informações de assinatura.',
        '[
          {"name":"documento_id","type":"string","required":true,"description":"ID interno do documento no SEI","example":"8547321"},
          {"name":"incluir_anexos","type":"boolean","required":false,"description":"Se deve incluir lista de anexos do documento"}
        ]'::jsonb,
        'DocumentoSEI',
        '{"tool":"ler_documento","arguments":{"documento_id":"8547321","incluir_anexos":true}}',
        2
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sei-mcp-server'),
        'verificar_tramitacao',
        'Retorna o histórico completo de tramitação de um processo, incluindo todas as movimentações e unidades por onde passou.',
        '[
          {"name":"numero_processo","type":"string","required":true,"description":"Número do processo no formato padrão SEI","example":"00600-00054321/2024-99"},
          {"name":"apenas_pendentes","type":"boolean","required":false,"description":"Se true, retorna apenas tramitações pendentes de ação"}
        ]'::jsonb,
        'TramitacaoSEI[]',
        '{"tool":"verificar_tramitacao","arguments":{"numero_processo":"00600-00054321/2024-99"}}',
        3
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sei-mcp-server'),
        'listar_documentos_processo',
        'Lista todos os documentos vinculados a um processo SEI, com tipo, data, signatários e situação de cada documento.',
        '[
          {"name":"numero_processo","type":"string","required":true,"description":"Número do processo no formato padrão SEI","example":"00600-00054321/2024-99"},
          {"name":"tipo_documento","type":"string","required":false,"description":"Filtrar por tipo (Ofício, Memorando, Despacho, etc.)"}
        ]'::jsonb,
        'DocumentoSEI[]',
        '{"tool":"listar_documentos_processo","arguments":{"numero_processo":"00600-00054321/2024-99","tipo_documento":"Ofício"}}',
        4
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sei-mcp-server'),
        'obter_interessados',
        'Retorna todos os interessados (pessoas físicas, jurídicas ou órgãos) vinculados a um processo SEI.',
        '[
          {"name":"numero_processo","type":"string","required":true,"description":"Número do processo no formato padrão SEI","example":"00600-00054321/2024-99"}
        ]'::jsonb,
        'InteressadoSEI[]',
        '{"tool":"obter_interessados","arguments":{"numero_processo":"00600-00054321/2024-99"}}',
        5
      );

    INSERT INTO mcp_agents (server_id, name, description, capabilities, base_model, system_prompt, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sei-mcp-server'),
        'Assistente de Triagem de Processos',
        'Analisa processos recebidos, identifica prioridade, tipo e encaminhamento adequado conforme normas da SEGPLAN.',
        ARRAY['Leitura e síntese de processos SEI', 'Classificação por tipo e urgência', 'Sugestão de encaminhamento', 'Identificação de pendências e prazos'],
        'Gemini 2.0 Pro',
        'Você é um assistente especializado em triagem de processos administrativos do Estado de Goiás. Analise os processos usando as ferramentas do SEI MCP Server e forneça resumos objetivos, classificação de prioridade e sugestão de encaminhamento conforme as normas da SEGPLAN.',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sei-mcp-server'),
        'Analista de Documentos SEI',
        'Lê, resume e extrai informações-chave de documentos oficiais do SEI, incluindo contratos, ofícios e despachos.',
        ARRAY['Extração de informações de documentos', 'Resumo executivo de contratos', 'Identificação de cláusulas críticas', 'Comparação entre versões de documentos'],
        'Claude 3.5 Sonnet',
        'Você é um analista especializado em documentos administrativos do Estado de Goiás. Use as ferramentas disponíveis para ler documentos do SEI e forneça análises precisas, resumos executivos e identificação de pontos críticos relevantes para a tomada de decisão.',
        2
      );

    INSERT INTO mcp_config_snippets (server_id, client_type, label, config_json, notes, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sei-mcp-server'),
        'claude_desktop',
        'Claude Desktop',
        '{
  "mcpServers": {
    "sei-mcp": {
      "command": "node",
      "args": ["/opt/goias/mcp/sei-mcp-server/index.js"],
      "env": {
        "SEI_API_URL": "https://sei.goias.gov.br/api/v1",
        "SEI_API_KEY": "SEU_TOKEN_API_AQUI",
        "SEI_UNIDADE": "CODIGO_DA_SUA_UNIDADE"
      }
    }
  }
}',
        'Token gerado em SEI > Administração > API. CODIGO_DA_SUA_UNIDADE é o código numérico da sua unidade administrativa no SEI.',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sei-mcp-server'),
        'vscode',
        'VS Code',
        '{
  "mcp": {
    "servers": {
      "sei-mcp": {
        "command": "node",
        "args": ["/opt/goias/mcp/sei-mcp-server/index.js"],
        "env": {
          "SEI_API_URL": "https://sei.goias.gov.br/api/v1",
          "SEI_API_KEY": "${env:SEI_API_KEY}",
          "SEI_UNIDADE": "${env:SEI_UNIDADE}"
        }
      }
    }
  }
}',
        'Configure as variáveis SEI_API_KEY e SEI_UNIDADE no ambiente do sistema ou no arquivo .env do workspace.',
        2
      );
  


    INSERT INTO mcp_servers (
      name, slug, tagline, description, category_id, status,
      is_verified, is_featured, is_official, version, license,
      compatible_models, author_name, author_org, tags, install_count, is_active
    ) VALUES (
      'SIAF Consultas MCP',
      'siaf-consultas-mcp',
      'Consulte dotações, empenhos e saldos do SIAF em linguagem natural',
      'Servidor MCP para integração com o Sistema Integrado de Administração Financeira (SIAF) do Estado de Goiás. Permite consultar dotações orçamentárias, verificar empenhos, obter saldos por unidade gestora e gerar relatórios financeiros simplificados diretamente pelo assistente de IA. Ideal para analistas orçamentários e gestores de unidades executoras.',
      (SELECT id FROM mcp_categories WHERE slug = 'dados-analytics'),
      'beta',
      true, false, true,
      '0.8.0', 'MIT',
      ARRAY['Gemini 2.0 Pro', 'Gemini 2.0 Enterprise'],
      'Equipe GO.IA',
      'SEFAZ - Goiás',
      ARRAY['siaf', 'orcamento', 'financeiro', 'empenho', 'dotacao', 'sefaz'],
      87,
      true
    );

    INSERT INTO mcp_tools (server_id, name, description, parameters, return_type, example_call, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'siaf-consultas-mcp'),
        'consultar_dotacao',
        'Consulta a dotação orçamentária de uma unidade gestora por programa, ação ou elemento de despesa.',
        '[
          {"name":"unidade_gestora","type":"string","required":true,"description":"Código da unidade gestora (6 dígitos)","example":"190101"},
          {"name":"exercicio","type":"integer","required":false,"description":"Ano do exercício orçamentário (padrão: ano atual)","example":2024},
          {"name":"programa","type":"string","required":false,"description":"Código do programa orçamentário","example":"0042"},
          {"name":"elemento_despesa","type":"string","required":false,"description":"Elemento de despesa (ex: 33903900)","example":"33903900"}
        ]'::jsonb,
        'DotacaoSIAF',
        '{"tool":"consultar_dotacao","arguments":{"unidade_gestora":"190101","exercicio":2024}}',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'siaf-consultas-mcp'),
        'verificar_empenho',
        'Verifica detalhes de um empenho específico: valor, favorecido, natureza e situação atual.',
        '[
          {"name":"numero_empenho","type":"string","required":true,"description":"Número do empenho no formato NE/AAAA-NNNNNN","example":"NE/2024-004521"},
          {"name":"unidade_gestora","type":"string","required":false,"description":"Código da unidade gestora para validação cruzada"}
        ]'::jsonb,
        'EmpenhoSIAF',
        '{"tool":"verificar_empenho","arguments":{"numero_empenho":"NE/2024-004521"}}',
        2
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'siaf-consultas-mcp'),
        'obter_saldo_unidade',
        'Retorna o saldo disponível por fonte de recursos e elemento de despesa para uma unidade gestora.',
        '[
          {"name":"unidade_gestora","type":"string","required":true,"description":"Código da unidade gestora (6 dígitos)","example":"190101"},
          {"name":"exercicio","type":"integer","required":false,"description":"Ano do exercício (padrão: ano atual)","example":2024},
          {"name":"fonte_recurso","type":"string","required":false,"description":"Fonte de recurso para filtrar (ex: 100 - Recursos Ordinários)"}
        ]'::jsonb,
        'SaldoUnidadeSIAF',
        '{"tool":"obter_saldo_unidade","arguments":{"unidade_gestora":"190101"}}',
        3
      );

    INSERT INTO mcp_agents (server_id, name, description, capabilities, base_model, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'siaf-consultas-mcp'),
        'Analista Orçamentário',
        'Auxilia gestores e analistas na consulta e interpretação de dados orçamentários do SIAF, gerando relatórios e alertas de saldo.',
        ARRAY['Consulta de dotações e saldos', 'Verificação de empenhos', 'Alertas de saldo insuficiente', 'Relatório de execução orçamentária', 'Comparativo entre exercícios'],
        'Gemini 2.0 Pro',
        1
      );

    INSERT INTO mcp_config_snippets (server_id, client_type, label, config_json, notes, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'siaf-consultas-mcp'),
        'claude_desktop',
        'Claude Desktop',
        '{
  "mcpServers": {
    "siaf-mcp": {
      "command": "node",
      "args": ["/opt/goias/mcp/siaf-mcp/index.js"],
      "env": {
        "SIAF_API_URL": "https://siaf.sefaz.go.gov.br/api/v2",
        "SIAF_TOKEN": "SEU_TOKEN_SEFAZ_AQUI",
        "SIAF_UNIDADE": "190101"
      }
    }
  }
}',
        'Token gerado no Portal SEFAZ-GO em Meu Perfil > Integrações > Gerar Token API. Requer perfil de Consulta Orçamentária.',
        1
      );
  


    INSERT INTO mcp_servers (
      name, slug, tagline, description, category_id, status,
      is_verified, is_featured, is_official, version, license,
      compatible_models, author_name, author_org, tags, install_count, is_active
    ) VALUES (
      'Portal Transparência MCP',
      'portal-transparencia-mcp',
      'Acesse contratos, licitações e despesas públicas de Goiás via IA',
      'Servidor MCP de acesso aos dados do Portal da Transparência do Estado de Goiás. Permite buscar contratos vigentes, consultar processos licitatórios, obter despesas por órgão e período, e analisar indicadores de gestão fiscal. Dados abertos conforme a Lei de Acesso à Informação (LAI). Ideal para auditores, gestores e jornalistas de dados.',
      (SELECT id FROM mcp_categories WHERE slug = 'dados-analytics'),
      'disponivel',
      true, true, false,
      '2.1.0', 'Apache-2.0',
      ARRAY['Gemini 2.0 Pro', 'Gemini 2.0 Enterprise', 'Claude 3.5 Sonnet', 'Claude 3 Opus'],
      'CONTROLADORIA-GERAL',
      'CGE - Goiás',
      ARRAY['transparencia', 'contratos', 'licitacoes', 'despesas', 'lai', 'dados-abertos'],
      213,
      true
    );

    INSERT INTO mcp_tools (server_id, name, description, parameters, return_type, example_call, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'portal-transparencia-mcp'),
        'buscar_contratos',
        'Busca contratos administrativos do Estado de Goiás com filtros por órgão, fornecedor, valor e período de vigência.',
        '[
          {"name":"orgao","type":"string","required":false,"description":"Sigla ou nome do órgão contratante","example":"SEGPLAN"},
          {"name":"fornecedor","type":"string","required":false,"description":"CNPJ ou razão social do fornecedor"},
          {"name":"valor_min","type":"number","required":false,"description":"Valor mínimo do contrato em reais","example":100000},
          {"name":"valor_max","type":"number","required":false,"description":"Valor máximo do contrato em reais"},
          {"name":"ano","type":"integer","required":false,"description":"Ano de assinatura do contrato","example":2024},
          {"name":"objeto","type":"string","required":false,"description":"Palavras-chave no objeto do contrato"}
        ]'::jsonb,
        'Contrato[]',
        '{"tool":"buscar_contratos","arguments":{"orgao":"SEGPLAN","ano":2024,"valor_min":100000}}',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'portal-transparencia-mcp'),
        'consultar_licitacoes',
        'Consulta processos licitatórios abertos, encerrados ou em andamento, por modalidade, órgão e objeto.',
        '[
          {"name":"orgao","type":"string","required":false,"description":"Sigla ou nome do órgão licitante","example":"SEPLANH"},
          {"name":"modalidade","type":"string","required":false,"description":"Modalidade: pregao, concorrencia, tomada_precos, convite, leilao","example":"pregao"},
          {"name":"situacao","type":"string","required":false,"description":"Situação: aberta, encerrada, deserta, cancelada","example":"aberta"},
          {"name":"ano","type":"integer","required":false,"description":"Ano de abertura da licitação","example":2024}
        ]'::jsonb,
        'Licitacao[]',
        '{"tool":"consultar_licitacoes","arguments":{"modalidade":"pregao","situacao":"aberta","ano":2024}}',
        2
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'portal-transparencia-mcp'),
        'obter_despesas_por_orgao',
        'Retorna o total de despesas empenhadas, liquidadas e pagas por órgão em um período, com detalhamento por elemento de despesa.',
        '[
          {"name":"orgao","type":"string","required":true,"description":"Sigla do órgão (ex: SAUDE, EDUCACAO, SEGURANCA)","example":"SAUDE"},
          {"name":"ano","type":"integer","required":true,"description":"Ano do exercício","example":2024},
          {"name":"mes","type":"integer","required":false,"description":"Mês para filtrar (1-12). Omitir para acumulado anual","example":6}
        ]'::jsonb,
        'DespesaOrgao',
        '{"tool":"obter_despesas_por_orgao","arguments":{"orgao":"SAUDE","ano":2024}}',
        3
      );

    INSERT INTO mcp_resources (server_id, name, uri_template, description, mime_type, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'portal-transparencia-mcp'),
        'Contratos por Ano',
        'contratos://goias/{ano}',
        'Acessa todos os contratos vigentes de um determinado ano. Substitua {ano} pelo ano desejado (ex: 2024).',
        'application/json',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'portal-transparencia-mcp'),
        'Licitações por Modalidade',
        'licitacoes://goias/{modalidade}',
        'Lista licitações filtradas por modalidade. Valores válidos: pregao, concorrencia, tomada_precos, convite, leilao.',
        'application/json',
        2
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'portal-transparencia-mcp'),
        'Despesas por Órgão e Mês',
        'despesas://goias/{orgao}/{ano}/{mes}',
        'Retorna dados de execução orçamentária de um órgão em um mês específico. Ex: despesas://goias/SAUDE/2024/6',
        'application/json',
        3
      );

    INSERT INTO mcp_config_snippets (server_id, client_type, label, config_json, notes, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'portal-transparencia-mcp'),
        'claude_desktop',
        'Claude Desktop',
        '{
  "mcpServers": {
    "transparencia-go": {
      "command": "node",
      "args": ["/opt/goias/mcp/transparencia-mcp/index.js"],
      "env": {
        "TRANSPARENCIA_API_URL": "https://transparencia.goias.gov.br/api/v1",
        "TRANSPARENCIA_API_KEY": "SEU_TOKEN_AQUI"
      }
    }
  }
}',
        'Token opcional — aumenta o limite de requisições. Disponível em transparencia.goias.gov.br/desenvolvedores.',
        1
      );
  


    INSERT INTO mcp_servers (
      name, slug, tagline, description, category_id, status,
      is_verified, is_featured, is_official, version, license,
      compatible_models, author_name, author_org, tags, install_count, is_active
    ) VALUES (
      'E-mail Institucional MCP',
      'email-institucional-mcp',
      'Gerencie o e-mail funcional do Estado de Goiás diretamente pelo assistente',
      'Servidor MCP para integração com o sistema de e-mail institucional do Estado de Goiás (Google Workspace Governamental). Permite enviar, ler e organizar e-mails, buscar contatos no diretório LDAP corporativo e gerenciar a caixa postal sem sair do assistente de IA. Autenticação via OAuth2 com conta @goias.gov.br.',
      (SELECT id FROM mcp_categories WHERE slug = 'comunicacao'),
      'disponivel',
      false, false, false,
      '1.0.3', 'MIT',
      ARRAY['Gemini 2.0 Pro', 'Claude 3.5 Sonnet'],
      'Equipe GO.IA',
      'SGTIC - Goiás',
      ARRAY['email', 'comunicacao', 'gmail', 'workspace', 'ldap', 'contatos'],
      156,
      true
    );

    INSERT INTO mcp_tools (server_id, name, description, parameters, return_type, example_call, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'email-institucional-mcp'),
        'enviar_email',
        'Envia um e-mail pelo endereço institucional do usuário autenticado. Suporta CC, CCO e referência a processos SEI.',
        '[
          {"name":"para","type":"string","required":true,"description":"Endereço(s) do destinatário, separados por vírgula","example":"joao.silva@goias.gov.br"},
          {"name":"assunto","type":"string","required":true,"description":"Assunto do e-mail","example":"Encaminhamento - Processo 00600/2024"},
          {"name":"corpo","type":"string","required":true,"description":"Corpo do e-mail em texto simples ou HTML"},
          {"name":"cc","type":"string","required":false,"description":"Endereços em cópia, separados por vírgula"},
          {"name":"cco","type":"string","required":false,"description":"Endereços em cópia oculta, separados por vírgula"}
        ]'::jsonb,
        'EmailEnviado',
        '{"tool":"enviar_email","arguments":{"para":"joao.silva@goias.gov.br","assunto":"Encaminhamento de documento","corpo":"Segue documento conforme solicitado."}}',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'email-institucional-mcp'),
        'listar_emails',
        'Lista e-mails da caixa de entrada com filtros por remetente, assunto, data e status de leitura.',
        '[
          {"name":"pasta","type":"string","required":false,"description":"Pasta a listar: inbox, enviados, rascunhos (padrão: inbox)","example":"inbox"},
          {"name":"nao_lidos","type":"boolean","required":false,"description":"Se true, retorna apenas não lidos"},
          {"name":"remetente","type":"string","required":false,"description":"Filtrar por endereço ou domínio do remetente"},
          {"name":"quantidade","type":"integer","required":false,"description":"Número de e-mails a retornar (padrão: 20, máx: 50)","example":10}
        ]'::jsonb,
        'Email[]',
        '{"tool":"listar_emails","arguments":{"nao_lidos":true,"quantidade":10}}',
        2
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'email-institucional-mcp'),
        'buscar_contatos_ldap',
        'Busca servidores no diretório corporativo LDAP por nome, matrícula, cargo ou unidade organizacional.',
        '[
          {"name":"nome","type":"string","required":false,"description":"Nome ou sobrenome do servidor","example":"Maria Santos"},
          {"name":"unidade","type":"string","required":false,"description":"Sigla da unidade organizacional","example":"SEGPLAN"},
          {"name":"cargo","type":"string","required":false,"description":"Cargo ou função para filtrar"},
          {"name":"email","type":"string","required":false,"description":"Endereço de e-mail para busca direta"}
        ]'::jsonb,
        'ContatoLDAP[]',
        '{"tool":"buscar_contatos_ldap","arguments":{"unidade":"SEGPLAN","cargo":"Analista"}}',
        3
      );

    INSERT INTO mcp_agents (server_id, name, description, capabilities, base_model, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'email-institucional-mcp'),
        'Assistente de Comunicação Oficial',
        'Auxilia na redação, organização e envio de e-mails institucionais, garantindo linguagem formal e conformidade com padrões governamentais.',
        ARRAY['Redação de e-mails em linguagem formal', 'Resumo de caixas de entrada volumosas', 'Identificação de e-mails urgentes', 'Busca de contatos no diretório corporativo', 'Encaminhamento com nota de contexto'],
        'Gemini 2.0 Pro',
        1
      );

    INSERT INTO mcp_config_snippets (server_id, client_type, label, config_json, notes, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'email-institucional-mcp'),
        'claude_desktop',
        'Claude Desktop',
        '{
  "mcpServers": {
    "email-goias": {
      "command": "node",
      "args": ["/opt/goias/mcp/email-mcp/index.js"],
      "env": {
        "GOOGLE_CLIENT_ID": "SEU_CLIENT_ID_AQUI",
        "GOOGLE_CLIENT_SECRET": "SEU_CLIENT_SECRET_AQUI",
        "GOOGLE_REFRESH_TOKEN": "SEU_REFRESH_TOKEN_AQUI",
        "LDAP_URL": "ldaps://ldap.goias.gov.br",
        "LDAP_BASE_DN": "dc=goias,dc=gov,dc=br"
      }
    }
  }
}',
        'Configure as credenciais OAuth2 do Google Workspace com a conta @goias.gov.br. O Refresh Token é gerado na primeira autenticação com o script de setup: node setup.js',
        1
      );
  


    INSERT INTO mcp_servers (
      name, slug, tagline, description, category_id, status,
      is_verified, is_featured, is_official, version, license,
      compatible_models, author_name, author_org, tags, install_count, is_active
    ) VALUES (
      'Gerador de Documentos Oficiais MCP',
      'gerador-documentos-oficiais-mcp',
      'Gere ofícios, memorandos e despachos no padrão oficial de Goiás',
      'Servidor MCP especializado na geração automática de documentos oficiais do Estado de Goiás. Produz ofícios, memorandos, despachos e outros expedientes administrativos seguindo rigorosamente o Manual de Redação Oficial do Estado e os padrões tipográficos estabelecidos. Integra-se ao SEI para inserção direta dos documentos gerados.',
      (SELECT id FROM mcp_categories WHERE slug = 'documentos'),
      'disponivel',
      true, true, true,
      '3.0.1', 'MIT',
      ARRAY['Gemini 2.0 Pro', 'Gemini 2.0 Enterprise', 'Claude 3.5 Sonnet', 'Claude 3 Opus'],
      'Equipe GO.IA',
      'SEGPLAN - Goiás',
      ARRAY['documentos', 'oficio', 'memorando', 'despacho', 'redacao-oficial', 'padrao-goias'],
      198,
      true
    );

    INSERT INTO mcp_tools (server_id, name, description, parameters, return_type, example_call, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'gerador-documentos-oficiais-mcp'),
        'gerar_oficio',
        'Gera um Ofício no padrão oficial do Estado de Goiás, com numeração, destinatário, assunto e corpo formatados conforme o Manual de Redação.',
        '[
          {"name":"numero","type":"string","required":true,"description":"Número do ofício no formato NNN/AAAA","example":"042/2024"},
          {"name":"orgao_origem","type":"string","required":true,"description":"Nome e sigla do órgão de origem","example":"Secretaria de Estado de Planejamento - SEGPLAN"},
          {"name":"destinatario","type":"string","required":true,"description":"Nome, cargo e endereço completo do destinatário"},
          {"name":"assunto","type":"string","required":true,"description":"Assunto resumido do ofício (máx. 100 caracteres)","example":"Encaminhamento de Relatório de Gestão 2024"},
          {"name":"corpo","type":"string","required":true,"description":"Texto principal do ofício"},
          {"name":"local_data","type":"string","required":false,"description":"Local e data. Padrão: Goiânia, data atual"},
          {"name":"assinatura","type":"string","required":false,"description":"Nome, cargo e matrícula do signatário"}
        ]'::jsonb,
        'DocumentoOficial',
        '{"tool":"gerar_oficio","arguments":{"numero":"042/2024","orgao_origem":"SEGPLAN","destinatario":"Fulano de Tal, Secretário","assunto":"Encaminhamento de Relatório","corpo":"Encaminhamos o relatório..."}}',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'gerador-documentos-oficiais-mcp'),
        'gerar_memorando',
        'Gera um Memorando interno no padrão oficial para comunicação entre unidades do mesmo órgão.',
        '[
          {"name":"numero","type":"string","required":true,"description":"Número do memorando no formato NNN/AAAA","example":"015/2024"},
          {"name":"para","type":"string","required":true,"description":"Destinatário (nome e cargo/unidade)","example":"Coordenador de Logística"},
          {"name":"de","type":"string","required":true,"description":"Remetente (nome e cargo/unidade)","example":"Diretor de Administração"},
          {"name":"assunto","type":"string","required":true,"description":"Assunto do memorando"},
          {"name":"corpo","type":"string","required":true,"description":"Texto do memorando"},
          {"name":"urgente","type":"boolean","required":false,"description":"Se true, inclui marcação URGENTE no cabeçalho"}
        ]'::jsonb,
        'DocumentoOficial',
        '{"tool":"gerar_memorando","arguments":{"numero":"015/2024","para":"Coordenador de TI","de":"Diretor de Infraestrutura","assunto":"Solicitação de equipamentos","corpo":"Solicitamos..."}}',
        2
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'gerador-documentos-oficiais-mcp'),
        'gerar_despacho',
        'Gera um Despacho administrativo para encaminhamento de processos, com campo de decisão e fundamentação legal.',
        '[
          {"name":"numero_processo","type":"string","required":true,"description":"Número do processo SEI ao qual o despacho se refere","example":"00600-00054321/2024-99"},
          {"name":"decisao","type":"string","required":true,"description":"Decisão ou encaminhamento (texto da deliberação)"},
          {"name":"fundamentacao","type":"string","required":false,"description":"Base legal ou normativa que fundamenta a decisão"},
          {"name":"para_unidade","type":"string","required":false,"description":"Unidade de destino do encaminhamento"}
        ]'::jsonb,
        'DocumentoOficial',
        '{"tool":"gerar_despacho","arguments":{"numero_processo":"00600-00054321/2024-99","decisao":"Encaminhe-se à UGPLAN para análise orçamentária.","para_unidade":"UGPLAN"}}',
        3
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'gerador-documentos-oficiais-mcp'),
        'formatar_documento_padrao_goias',
        'Reformata qualquer texto de documento aplicando as regras tipográficas e de estilo do Manual de Redação Oficial do Estado de Goiás.',
        '[
          {"name":"texto","type":"string","required":true,"description":"Texto do documento a ser formatado"},
          {"name":"tipo_documento","type":"string","required":true,"description":"Tipo: oficio, memorando, despacho, nota_tecnica, parecer","example":"oficio"},
          {"name":"corrigir_gramatica","type":"boolean","required":false,"description":"Se true, aplica correção gramatical e ortográfica (padrão: true)"}
        ]'::jsonb,
        'DocumentoFormatado',
        '{"tool":"formatar_documento_padrao_goias","arguments":{"texto":"...","tipo_documento":"oficio","corrigir_gramatica":true}}',
        4
      );

    INSERT INTO mcp_agents (server_id, name, description, capabilities, base_model, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'gerador-documentos-oficiais-mcp'),
        'Redator de Documentos Oficiais',
        'Especialista em redação oficial governamental. Gera documentos completos e formatados a partir de instruções em linguagem natural, seguindo o Manual de Redação do Estado de Goiás.',
        ARRAY['Geração completa de ofícios, memorandos e despachos', 'Adequação ao nível de formalidade exigido', 'Fundamentação legal automática', 'Revisão de linguagem e ortografia', 'Inserção direta no SEI via integração'],
        'Claude 3.5 Sonnet',
        1
      );

    INSERT INTO mcp_config_snippets (server_id, client_type, label, config_json, notes, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'gerador-documentos-oficiais-mcp'),
        'claude_desktop',
        'Claude Desktop',
        '{
  "mcpServers": {
    "docs-goias": {
      "command": "node",
      "args": ["/opt/goias/mcp/docs-oficiais-mcp/index.js"],
      "env": {
        "DOCS_API_URL": "https://docs-mcp.goias.gov.br/api",
        "DOCS_API_KEY": "SEU_TOKEN_AQUI",
        "ORGAO_PADRAO": "SIGLA_DO_SEU_ORGAO",
        "SEI_INTEGRATION": "true"
      }
    }
  }
}',
        'Configure ORGAO_PADRAO com a sigla do seu órgão para pré-preenchimento automático. Com SEI_INTEGRATION=true, o documento é inserido diretamente no processo SEI indicado.',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'gerador-documentos-oficiais-mcp'),
        'vscode',
        'VS Code',
        '{
  "mcp": {
    "servers": {
      "docs-goias": {
        "command": "node",
        "args": ["/opt/goias/mcp/docs-oficiais-mcp/index.js"],
        "env": {
          "DOCS_API_URL": "https://docs-mcp.goias.gov.br/api",
          "DOCS_API_KEY": "${env:DOCS_GOIAS_API_KEY}",
          "ORGAO_PADRAO": "${env:ORGAO_GOIAS}"
        }
      }
    }
  }
}',
        'Configure as variáveis DOCS_GOIAS_API_KEY e ORGAO_GOIAS no ambiente do sistema ou no .env do workspace.',
        2
      );
  


    INSERT INTO mcp_servers (
      name, slug, tagline, description, category_id, status,
      is_verified, is_featured, is_official, version, license,
      compatible_models, author_name, author_org, tags, install_count, is_active
    ) VALUES (
      'SIGEC MCP',
      'sigec-mcp',
      'Consulte contratos e fornecedores do SIGEC em linguagem natural',
      'Servidor MCP para integração com o Sistema de Gestão de Contratos (SIGEC) do Estado de Goiás. Permite consultar contratos vigentes, verificar termos aditivos e prorrogações, listar fornecedores credenciados e acompanhar o status de execução contratual diretamente pelo assistente de IA.',
      (SELECT id FROM mcp_categories WHERE slug = 'sistemas-governo'),
      'beta',
      false, false, true,
      '0.5.2', 'MIT',
      ARRAY['Gemini 2.0 Pro', 'Gemini 2.0 Enterprise'],
      'Equipe GO.IA',
      'SEAD - Goiás',
      ARRAY['sigec', 'contratos', 'fornecedores', 'aditivos', 'gestao-contratual', 'sead'],
      54,
      true
    );

    INSERT INTO mcp_tools (server_id, name, description, parameters, return_type, example_call, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sigec-mcp'),
        'consultar_contrato',
        'Consulta contratos no SIGEC por número, objeto, fornecedor ou órgão contratante.',
        '[
          {"name":"numero_contrato","type":"string","required":false,"description":"Número do contrato no formato NNNNN/AAAA","example":"00123/2024"},
          {"name":"orgao","type":"string","required":false,"description":"Sigla ou nome do órgão contratante","example":"SEAD"},
          {"name":"fornecedor_cnpj","type":"string","required":false,"description":"CNPJ do fornecedor (apenas números)","example":"12345678000195"},
          {"name":"objeto","type":"string","required":false,"description":"Palavras-chave no objeto do contrato"},
          {"name":"vigente","type":"boolean","required":false,"description":"Se true, retorna apenas contratos com vigência ativa"}
        ]'::jsonb,
        'ContratoSIGEC[]',
        '{"tool":"consultar_contrato","arguments":{"orgao":"SEAD","vigente":true}}',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sigec-mcp'),
        'verificar_aditivo',
        'Verifica todos os termos aditivos de um contrato, incluindo prorrogações de prazo e acréscimos de valor.',
        '[
          {"name":"numero_contrato","type":"string","required":true,"description":"Número do contrato no formato NNNNN/AAAA","example":"00123/2024"},
          {"name":"tipo_aditivo","type":"string","required":false,"description":"Filtrar por tipo: prazo, valor, objeto, rescisao"}
        ]'::jsonb,
        'AditivoSIGEC[]',
        '{"tool":"verificar_aditivo","arguments":{"numero_contrato":"00123/2024"}}',
        2
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sigec-mcp'),
        'listar_fornecedores',
        'Lista fornecedores credenciados no SIGEC por categoria de serviço, porte ou situação cadastral.',
        '[
          {"name":"categoria","type":"string","required":false,"description":"Categoria de serviço ou produto","example":"Tecnologia da Informação"},
          {"name":"porte","type":"string","required":false,"description":"Porte da empresa: MEI, ME, EPP, MEDIO, GRANDE"},
          {"name":"municipio","type":"string","required":false,"description":"Município sede da empresa","example":"Goiânia"},
          {"name":"ativo","type":"boolean","required":false,"description":"Se true, retorna apenas fornecedores com cadastro ativo"}
        ]'::jsonb,
        'FornecedorSIGEC[]',
        '{"tool":"listar_fornecedores","arguments":{"categoria":"Tecnologia da Informação","municipio":"Goiânia","ativo":true}}',
        3
      );

    INSERT INTO mcp_config_snippets (server_id, client_type, label, config_json, notes, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'sigec-mcp'),
        'claude_desktop',
        'Claude Desktop',
        '{
  "mcpServers": {
    "sigec-mcp": {
      "command": "node",
      "args": ["/opt/goias/mcp/sigec-mcp/index.js"],
      "env": {
        "SIGEC_API_URL": "https://sigec.sead.go.gov.br/api/v1",
        "SIGEC_TOKEN": "SEU_TOKEN_SEAD_AQUI",
        "SIGEC_ORGAO": "CODIGO_DO_SEU_ORGAO"
      }
    }
  }
}',
        'Token gerado no painel do SIGEC em Configurações > Integrações > API. Em beta: funcionalidades podem mudar entre versões.',
        1
      );
  


    INSERT INTO mcp_servers (
      name, slug, tagline, description, category_id, status,
      is_verified, is_featured, is_official, version, license,
      compatible_models, author_name, author_org, tags, install_count, is_active
    ) VALUES (
      'Calendário Institucional MCP',
      'calendario-institucional-mcp',
      'Gerencie agendas e consulte feriados e expediente do Estado de Goiás',
      'Servidor MCP para gerenciamento de calendário e agenda institucional do Estado de Goiás. Permite criar e consultar eventos no Google Calendar Governamental, listar feriados estaduais e nacionais, verificar dias de expediente e pontos facultativos, e calcular prazos administrativos desconsiderando dias não úteis.',
      (SELECT id FROM mcp_categories WHERE slug = 'utilitarios'),
      'disponivel',
      false, false, false,
      '1.1.0', 'MIT',
      ARRAY['Gemini 2.0 Pro', 'Claude 3.5 Sonnet'],
      'Equipe GO.IA',
      'SGTIC - Goiás',
      ARRAY['calendario', 'agenda', 'feriados', 'expediente', 'prazos', 'google-calendar'],
      112,
      true
    );

    INSERT INTO mcp_tools (server_id, name, description, parameters, return_type, example_call, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'calendario-institucional-mcp'),
        'criar_evento',
        'Cria um evento na agenda institucional do usuário autenticado, com suporte a convidados, sala de reunião e videoconferência.',
        '[
          {"name":"titulo","type":"string","required":true,"description":"Título do evento","example":"Reunião de Planejamento Q1"},
          {"name":"data_inicio","type":"string","required":true,"description":"Data e hora de início em ISO 8601","example":"2024-03-15T09:00:00-03:00"},
          {"name":"data_fim","type":"string","required":true,"description":"Data e hora de fim em ISO 8601","example":"2024-03-15T10:00:00-03:00"},
          {"name":"convidados","type":"string","required":false,"description":"E-mails dos convidados separados por vírgula"},
          {"name":"local","type":"string","required":false,"description":"Local físico ou link de videoconferência"},
          {"name":"descricao","type":"string","required":false,"description":"Descrição ou pauta do evento"}
        ]'::jsonb,
        'Evento',
        '{"tool":"criar_evento","arguments":{"titulo":"Reunião GO.IA","data_inicio":"2024-03-15T09:00:00-03:00","data_fim":"2024-03-15T10:00:00-03:00"}}',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'calendario-institucional-mcp'),
        'listar_feriados_goias',
        'Lista os feriados nacionais, estaduais e municipais de um determinado ano, incluindo pontos facultativos decretados pelo Governo de Goiás.',
        '[
          {"name":"ano","type":"integer","required":false,"description":"Ano para listar feriados (padrão: ano atual)","example":2024},
          {"name":"municipio","type":"string","required":false,"description":"Incluir feriados municipais de uma cidade específica","example":"Goiânia"},
          {"name":"incluir_ponto_facultativo","type":"boolean","required":false,"description":"Se true, inclui pontos facultativos (padrão: true)"}
        ]'::jsonb,
        'Feriado[]',
        '{"tool":"listar_feriados_goias","arguments":{"ano":2024,"municipio":"Goiânia"}}',
        2
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'calendario-institucional-mcp'),
        'verificar_expediente',
        'Verifica se uma data é dia útil de expediente para os órgãos do Estado de Goiás, considerando feriados, decretos e portarias.',
        '[
          {"name":"data","type":"string","required":true,"description":"Data a verificar no formato YYYY-MM-DD","example":"2024-11-15"},
          {"name":"orgao","type":"string","required":false,"description":"Sigla do órgão para aplicar regras específicas de expediente"}
        ]'::jsonb,
        'SituacaoExpediente',
        '{"tool":"verificar_expediente","arguments":{"data":"2024-11-15"}}',
        3
      );

    INSERT INTO mcp_config_snippets (server_id, client_type, label, config_json, notes, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'calendario-institucional-mcp'),
        'claude_desktop',
        'Claude Desktop',
        '{
  "mcpServers": {
    "calendario-goias": {
      "command": "node",
      "args": ["/opt/goias/mcp/calendario-mcp/index.js"],
      "env": {
        "GOOGLE_CLIENT_ID": "SEU_CLIENT_ID_AQUI",
        "GOOGLE_CLIENT_SECRET": "SEU_CLIENT_SECRET_AQUI",
        "GOOGLE_REFRESH_TOKEN": "SEU_REFRESH_TOKEN_AQUI",
        "FERIADOS_API_URL": "https://feriados.goias.gov.br/api/v1"
      }
    }
  }
}',
        'Usa OAuth2 do Google Workspace Governamental. Gere o Refresh Token executando: node /opt/goias/mcp/calendario-mcp/setup.js',
        1
      );
  


    INSERT INTO mcp_servers (
      name, slug, tagline, description, category_id, status,
      is_verified, is_featured, is_official, version, license,
      compatible_models, author_name, author_org, tags, install_count, is_active
    ) VALUES (
      'Assinatura Digital MCP',
      'assinatura-digital-mcp',
      'Assine e valide documentos com certificado digital ICP-Brasil pelo assistente',
      'Servidor MCP para operações de assinatura digital e validação de certificados no Estado de Goiás. Permite assinar documentos PDF com certificado ICP-Brasil, verificar a validade de assinaturas digitais existentes, validar certificados na cadeia ITI e consultar o status de revogação via OCSP/CRL. Compatível com token USB A3 e certificado em nuvem BirdID.',
      (SELECT id FROM mcp_categories WHERE slug = 'seguranca'),
      'disponivel',
      true, false, true,
      '2.3.0', 'LGPL-3.0',
      ARRAY['Gemini 2.0 Pro', 'Gemini 2.0 Enterprise', 'Claude 3.5 Sonnet'],
      'Equipe GO.IA',
      'PRODERJ / SGTIC - Goiás',
      ARRAY['assinatura-digital', 'icp-brasil', 'certificado', 'pdf', 'birdid', 'validacao'],
      89,
      true
    );

    INSERT INTO mcp_tools (server_id, name, description, parameters, return_type, example_call, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'assinatura-digital-mcp'),
        'assinar_documento',
        'Assina digitalmente um documento PDF com o certificado ICP-Brasil configurado. Suporta assinatura simples, avançada (PAdES-B) e qualificada (PAdES-LTV).',
        '[
          {"name":"documento_url","type":"string","required":true,"description":"URL ou caminho local do documento PDF a assinar","example":"/documentos/oficio-042-2024.pdf"},
          {"name":"tipo_assinatura","type":"string","required":false,"description":"Tipo: simples (CMS), avancada (PAdES-B) ou qualificada (PAdES-LTV). Padrão: avancada","example":"avancada"},
          {"name":"razao","type":"string","required":false,"description":"Razão ou motivação da assinatura","example":"Aprovação conforme deliberação em reunião"},
          {"name":"localizacao","type":"string","required":false,"description":"Local físico da assinatura","example":"Goiânia, GO"}
        ]'::jsonb,
        'DocumentoAssinado',
        '{"tool":"assinar_documento","arguments":{"documento_url":"/docs/oficio.pdf","tipo_assinatura":"avancada","razao":"Aprovação da diretoria"}}',
        1
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'assinatura-digital-mcp'),
        'verificar_assinatura',
        'Verifica a validade e autenticidade de todas as assinaturas digitais presentes em um documento PDF.',
        '[
          {"name":"documento_url","type":"string","required":true,"description":"URL ou caminho local do documento PDF assinado","example":"/documentos/contrato-assinado.pdf"},
          {"name":"verificar_revogacao","type":"boolean","required":false,"description":"Se true, consulta OCSP/CRL para verificar revogação do certificado (padrão: true)"}
        ]'::jsonb,
        'ResultadoVerificacao',
        '{"tool":"verificar_assinatura","arguments":{"documento_url":"/docs/contrato.pdf","verificar_revogacao":true}}',
        2
      ),
      (
        (SELECT id FROM mcp_servers WHERE slug = 'assinatura-digital-mcp'),
        'validar_certificado',
        'Valida um certificado digital ICP-Brasil verificando cadeia de confiança, prazo de validade e status de revogação na ITI.',
        '[
          {"name":"certificado_b64","type":"string","required":false,"description":"Certificado em Base64 (PEM/DER) para validação direta"},
          {"name":"cpf_cnpj","type":"string","required":false,"description":"CPF ou CNPJ do titular para busca no repositório ICP-Brasil","example":"12345678901"},
          {"name":"tipo_certificado","type":"string","required":false,"description":"Tipo esperado: PF, PJ, PF_CODIGO, PJ_CODIGO, SSL"}
        ]'::jsonb,
        'ValidacaoCertificado',
        '{"tool":"validar_certificado","arguments":{"cpf_cnpj":"12345678901","tipo_certificado":"PF"}}',
        3
      );

    INSERT INTO mcp_agents (server_id, name, description, capabilities, base_model, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'assinatura-digital-mcp'),
        'Validador de Documentos Assinados',
        'Verifica a autenticidade e validade jurídica de documentos assinados digitalmente, emitindo relatório de conformidade com a legislação ICP-Brasil.',
        ARRAY['Verificação de validade de assinaturas', 'Validação de cadeia de certificados ICP-Brasil', 'Consulta de revogação em tempo real (OCSP)', 'Emissão de relatório de conformidade', 'Identificação de signatários e timestamps'],
        'Gemini 2.0 Pro',
        1
      );

    INSERT INTO mcp_config_snippets (server_id, client_type, label, config_json, notes, sort_order) VALUES
      (
        (SELECT id FROM mcp_servers WHERE slug = 'assinatura-digital-mcp'),
        'claude_desktop',
        'Claude Desktop',
        '{
  "mcpServers": {
    "assinatura-goias": {
      "command": "node",
      "args": ["/opt/goias/mcp/assinatura-digital-mcp/index.js"],
      "env": {
        "ASSINATURA_API_URL": "https://assinatura.sgtic.go.gov.br/api/v2",
        "ASSINATURA_API_KEY": "SEU_TOKEN_AQUI",
        "CERTIFICADO_TIPO": "token",
        "BIRDID_URL": "https://sign.birdid.com.br/api/v0"
      }
    }
  }
}',
        'Configure CERTIFICADO_TIPO como token para certificado em hardware (A3) ou cloud para BirdID. Para uso com token USB, o driver do dispositivo deve estar instalado no sistema.',
        1
      );
  