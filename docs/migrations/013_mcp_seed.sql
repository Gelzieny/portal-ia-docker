
    -- Categorias iniciais
    INSERT INTO mcp_categories (name, slug, description, icon, color, sort_order) VALUES
      ('Sistemas de Governo', 'sistemas-governo',
       'Integração com sistemas governamentais (SEI, SIAF, SIGEC, etc)', 'Building2', '#1a5e38', 1),
      ('Dados e Analytics', 'dados-analytics',
       'Acesso a bases de dados, relatórios e análises', 'BarChart3', '#185FA5', 2),
      ('Automação de Processos', 'automacao',
       'Automação de tarefas e workflows administrativos', 'Zap', '#854F0B', 3),
      ('Comunicação', 'comunicacao',
       'E-mail, mensageria e notificações institucionais', 'MessageSquare', '#993556', 4),
      ('Documentos', 'documentos',
       'Leitura, geração e gestão de documentos oficiais', 'FileText', '#534AB7', 5),
      ('Segurança e Identidade', 'seguranca',
       'Autenticação, assinatura digital e controle de acesso', 'ShieldCheck', '#0F6E56', 6),
      ('Utilitários', 'utilitarios',
       'Ferramentas gerais de produtividade', 'Wrench', '#888780', 7);

    -- Servidor de exemplo: SEI MCP
    INSERT INTO mcp_servers (
      name, slug, tagline, description, status, is_verified, is_official,
      compatible_models, author_name, author_org, tags, is_active
    )
    SELECT
      'SEI MCP Server',
      'sei-mcp-server',
      'Acesse e gerencie processos do SEI diretamente pelo seu assistente de IA',
      'Servidor MCP oficial para integração com o Sistema Eletrônico de Informações (SEI). Permite consultar processos, ler documentos, verificar tramitação e criar minutas diretamente através de modelos de linguagem compatíveis com o protocolo MCP.',
      'beta',
      true,
      true,
      ARRAY['Gemini Pro', 'Gemini Enterprise'],
      'Equipe GO.IA',
      'SGTIC - Goiás',
      ARRAY['sei', 'processos', 'documentos', 'governo'],
      true
    WHERE EXISTS (SELECT 1 FROM mcp_categories WHERE slug = 'sistemas-governo');

    -- Vincula o SEI MCP à categoria Sistemas de Governo
    UPDATE mcp_servers
    SET category_id = (SELECT id FROM mcp_categories WHERE slug = 'sistemas-governo')
    WHERE slug = 'sei-mcp-server';
  