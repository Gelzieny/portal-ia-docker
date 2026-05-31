
    -- ── Redação Oficial ───────────────────────────────────────────────────────

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Ofício de Solicitação de Informações',
      'Gera um ofício formal solicitando informações ou documentos a outro órgão ou entidade, seguindo o padrão de redação oficial do Estado de Goiás.',
      E'Você é um especialista em redação oficial do serviço público estadual de Goiás.

Elabore um ofício formal solicitando {{tipo_informacao}} ao(à) {{destinatario}}, referente ao(à) {{assunto}}.

Contexto adicional: {{contexto}}

O ofício deve:
- Seguir rigorosamente o Manual de Redação Oficial
- Incluir número de protocolo fictício no formato OF. {{numero_oficio}}/{{ano}}/{{sigla_orgao}}
- Ter linguagem formal, clara e objetiva
- Incluir prazo de resposta de 15 dias úteis
- Ser assinado pelo(a) {{cargo_solicitante}}

Formate o documento completo, incluindo cabeçalho, corpo e rodapé.',
      (SELECT id FROM prompt_categories WHERE slug = 'redacao-oficial'),
      ARRAY['ofício','solicitação','redação oficial','comunicação externa'],
      'iniciante',
      '[
        {"name":"tipo_informacao","description":"Tipo de informação ou documento solicitado","example":"os dados de execução orçamentária do 1º trimestre de 2025"},
        {"name":"destinatario","description":"Nome e cargo do destinatário","example":"Secretário de Estado da Fazenda"},
        {"name":"assunto","description":"Assunto do ofício","example":"Levantamento para Relatório de Transparência"},
        {"name":"contexto","description":"Contexto ou justificativa da solicitação","example":"Necessário para elaboração do Relatório Anual de Gestão"},
        {"name":"numero_oficio","description":"Número sequencial do ofício","example":"042"},
        {"name":"ano","description":"Ano do ofício","example":"2025"},
        {"name":"sigla_orgao","description":"Sigla do órgão emissor","example":"SEGPLAN"},
        {"name":"cargo_solicitante","description":"Cargo de quem assina o ofício","example":"Diretor de Planejamento e Orçamento"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'redacao-oficial');

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Memorando Interno',
      'Cria um memorando para comunicação interna entre unidades do mesmo órgão, com linguagem objetiva e formatação correta.',
      E'Você é um especialista em comunicação oficial interna do serviço público de Goiás.

Elabore um memorando interno destinado a {{destinatario_setor}}, solicitando ou comunicando {{assunto_memorando}}.

Detalhes: {{detalhes}}

Prazo ou data relevante: {{prazo}}

O memorando deve:
- Seguir o padrão MEMO Nº {{numero_memo}}/{{ano}}/{{sigla_orgao}}
- Ser direto e objetivo, sem prolixidade
- Indicar claramente a ação esperada do destinatário
- Ter no máximo 3 parágrafos

Emitido por: {{nome_emitente}}, {{cargo_emitente}}',
      (SELECT id FROM prompt_categories WHERE slug = 'redacao-oficial'),
      ARRAY['memorando','comunicação interna','redação oficial'],
      'iniciante',
      '[
        {"name":"destinatario_setor","description":"Setor ou unidade destinatária","example":"Gerência de Recursos Humanos"},
        {"name":"assunto_memorando","description":"Assunto principal do memorando","example":"liberação de servidores para capacitação obrigatória"},
        {"name":"detalhes","description":"Detalhes da solicitação ou comunicação","example":"O curso ocorrerá nos dias 10 e 11 de junho, das 8h às 17h, na EGGO"},
        {"name":"prazo","description":"Prazo ou data relevante","example":"Confirmação necessária até 05/06/2025"},
        {"name":"numero_memo","description":"Número do memorando","example":"015"},
        {"name":"ano","description":"Ano","example":"2025"},
        {"name":"sigla_orgao","description":"Sigla do órgão","example":"GOIÁS TI"},
        {"name":"nome_emitente","description":"Nome de quem emite","example":"Carlos Almeida"},
        {"name":"cargo_emitente","description":"Cargo de quem emite","example":"Gerente de Tecnologia"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'redacao-oficial');

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Nota Técnica',
      'Elabora uma nota técnica completa para subsidiar decisões administrativas, com embasamento legal e conclusões claras.',
      E'Você é um especialista em análise técnica e redação oficial do Governo de Goiás.

Elabore uma Nota Técnica sobre {{tema}}, solicitada por {{solicitante}} para subsidiar {{finalidade}}.

Baseie a análise nos seguintes aspectos:
{{aspectos_analisar}}

Normativa ou base legal aplicável: {{base_legal}}

A Nota Técnica deve conter:
1. **Objeto** — definição clara do tema
2. **Análise** — desenvolvimento técnico fundamentado
3. **Embasamento Legal** — legislação pertinente
4. **Conclusão** — posicionamento técnico objetivo
5. **Recomendação** — ação sugerida

Número: NT Nº {{numero_nt}}/{{ano}} | Área: {{area_tecnica}}',
      (SELECT id FROM prompt_categories WHERE slug = 'redacao-oficial'),
      ARRAY['nota técnica','análise','decisão administrativa','legislação'],
      'avancado',
      '[
        {"name":"tema","description":"Tema central da nota técnica","example":"viabilidade técnica de contratação de solução de IA generativa"},
        {"name":"solicitante","description":"Quem solicitou a nota","example":"Secretário Adjunto de Modernização"},
        {"name":"finalidade","description":"Para que será usada a nota","example":"embasar decisão de contratação via pregão eletrônico"},
        {"name":"aspectos_analisar","description":"Aspectos a serem analisados","example":"conformidade com LGPD, custo-benefício, segurança da informação, integração com sistemas legados"},
        {"name":"base_legal","description":"Legislação aplicável","example":"Lei 14.133/2021, LGPD (Lei 13.709/2018), Decreto Estadual 10.008/2022"},
        {"name":"numero_nt","description":"Número da nota técnica","example":"007"},
        {"name":"ano","description":"Ano","example":"2025"},
        {"name":"area_tecnica","description":"Área técnica responsável","example":"Diretoria de Infraestrutura e Segurança"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'redacao-oficial');

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Resposta a Recurso Administrativo',
      'Elabora resposta formal a recurso ou impugnação apresentados por cidadão ou empresa em processo administrativo.',
      E'Você é um especialista em direito administrativo e redação oficial do serviço público de Goiás.

Elabore a resposta ao recurso administrativo protocolado sob nº {{numero_processo}}, apresentado por {{recorrente}} em {{data_recurso}}, referente a {{objeto_recurso}}.

Argumentos apresentados pelo recorrente:
{{argumentos_recurso}}

Fundamentos para a decisão:
{{fundamentos_decisao}}

Decisão: {{decisao}} (Provido / Parcialmente Provido / Improvido)

A resposta deve:
- Analisar cada argumento do recurso
- Apresentar a fundamentação legal ({{base_legal}})
- Ser clara quanto à decisão e seus efeitos
- Informar sobre possibilidade de recurso à instância superior',
      (SELECT id FROM prompt_categories WHERE slug = 'redacao-oficial'),
      ARRAY['recurso administrativo','resposta','processo','decisão'],
      'avancado',
      '[
        {"name":"numero_processo","description":"Número do processo","example":"202500123456-7"},
        {"name":"recorrente","description":"Nome do recorrente","example":"Empresa XYZ Ltda., CNPJ 12.345.678/0001-90"},
        {"name":"data_recurso","description":"Data de interposição do recurso","example":"15/04/2025"},
        {"name":"objeto_recurso","description":"Objeto do recurso","example":"inabilitação no Pregão Eletrônico nº 12/2025"},
        {"name":"argumentos_recurso","description":"Principais argumentos do recorrente","example":"alega que os documentos de habilitação foram entregues tempestivamente e que a comissão interpretou equivocadamente o edital"},
        {"name":"fundamentos_decisao","description":"Fundamentos para manter ou reformar a decisão","example":"análise do edital item 8.3 e documentação entregue às 17h02, após o encerramento às 17h00"},
        {"name":"decisao","description":"Decisão a ser tomada","example":"Improvido"},
        {"name":"base_legal","description":"Base legal da decisão","example":"Lei 14.133/2021, art. 165 e seguintes"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'redacao-oficial');

    -- ── Análise de Dados ──────────────────────────────────────────────────────

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Análise de Relatório de Execução Orçamentária',
      'Interpreta dados de execução orçamentária e financeira, identifica desvios e sugere ações corretivas com linguagem acessível.',
      E'Você é um analista de orçamento público especializado em finanças governamentais do Estado de Goiás.

Analise os seguintes dados de execução orçamentária:

{{dados_orcamento}}

Período de referência: {{periodo}}
Órgão/Unidade: {{orgao_unidade}}
Meta prevista: {{meta_prevista}}

Sua análise deve:
1. **Situação Atual** — resumo do percentual executado vs. previsto
2. **Pontos de Atenção** — itens com execução abaixo de 70% ou acima de 100%
3. **Causas Prováveis** — hipóteses para os desvios identificados
4. **Recomendações** — ações concretas para os próximos {{prazo_acao}} dias
5. **Indicadores-Chave** — tabela com os 5 principais indicadores

Use linguagem clara, adequada para relatório gerencial.',
      (SELECT id FROM prompt_categories WHERE slug = 'analise-dados'),
      ARRAY['orçamento','execução orçamentária','finanças públicas','análise'],
      'intermediario',
      '[
        {"name":"dados_orcamento","description":"Dados de execução (cole aqui a tabela ou texto)","example":"Programa 1205 – Inovação: Dotação R$ 2.400.000, Empenhado R$ 980.000 (40,8%), Liquidado R$ 720.000 (30%)"},
        {"name":"periodo","description":"Período de referência","example":"1º Quadrimestre de 2025 (jan–abr)"},
        {"name":"orgao_unidade","description":"Órgão ou unidade gestora","example":"Secretaria de Ciência, Tecnologia e Inovação – SECTI"},
        {"name":"meta_prevista","description":"Meta de execução prevista para o período","example":"50% da dotação anual"},
        {"name":"prazo_acao","description":"Prazo para implementar ações corretivas","example":"60"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'analise-dados');

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Análise Comparativa de Indicadores de Desempenho',
      'Compara indicadores de desempenho entre períodos ou unidades, destacando tendências e oportunidades de melhoria.',
      E'Você é um especialista em gestão de desempenho no setor público.

Realize uma análise comparativa dos indicadores abaixo:

{{indicadores}}

Comparação entre: {{periodo_anterior}} vs. {{periodo_atual}}
Contexto: {{contexto_analise}}

Estruture a análise em:
1. **Evolução Geral** — tendência positiva, negativa ou estável
2. **Destaques Positivos** — indicadores que melhoraram acima de {{meta_melhoria}}%
3. **Indicadores Críticos** — que pioraram ou estão abaixo da meta
4. **Análise de Causas** — fatores que explicam as variações
5. **Mapa de Calor Textual** — classifique cada indicador como 🟢 Meta / 🟡 Atenção / 🔴 Crítico
6. **Próximos Passos** — 3 ações prioritárias com responsável sugerido',
      (SELECT id FROM prompt_categories WHERE slug = 'analise-dados'),
      ARRAY['indicadores','desempenho','KPI','comparativo','gestão'],
      'intermediario',
      '[
        {"name":"indicadores","description":"Lista de indicadores com valores","example":"Taxa de resolução de demandas: meta 85%, atual 78%, anterior 72% | Tempo médio de resposta: meta 5 dias, atual 6,3 dias, anterior 8,1 dias"},
        {"name":"periodo_anterior","description":"Período de comparação anterior","example":"2º Semestre de 2024"},
        {"name":"periodo_atual","description":"Período atual","example":"1º Semestre de 2025"},
        {"name":"contexto_analise","description":"Contexto relevante para a análise","example":"Implementação do novo sistema de protocolo digital em março de 2025"},
        {"name":"meta_melhoria","description":"Percentual mínimo para considerar melhoria significativa","example":"10"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'analise-dados');

    -- ── Atendimento ao Cidadão ────────────────────────────────────────────────

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Resposta a Requerimento de Cidadão',
      'Elabora resposta formal e acessível a requerimentos, solicitações ou reclamações de cidadãos, seguindo a LAI e o padrão de atendimento do Estado.',
      E'Você é um servidor público especializado em atendimento ao cidadão do Estado de Goiás.

Elabore uma resposta ao requerimento protocolado sob nº {{numero_protocolo}}, apresentado por {{nome_cidadao}}, referente a {{assunto_requerimento}}.

Solicitação do cidadão:
{{descricao_solicitacao}}

Decisão/Resposta a ser comunicada:
{{decisao_resposta}}

Base legal ou normativa aplicável: {{base_legal}}

A resposta deve:
- Ser respeitosa, clara e em linguagem cidadã (evitar jargões técnicos)
- Tratar o cidadão pelo nome
- Explicar a decisão de forma compreensível
- Indicar próximos passos ou recursos disponíveis
- Informar canais de contato para dúvidas
- Respeitar o prazo de {{prazo_lei}} dias da LAI/Lei de Acesso',
      (SELECT id FROM prompt_categories WHERE slug = 'atendimento'),
      ARRAY['atendimento ao cidadão','requerimento','LAI','resposta','protocolo'],
      'iniciante',
      '[
        {"name":"numero_protocolo","description":"Número do protocolo","example":"GOV-2025-00123456"},
        {"name":"nome_cidadao","description":"Nome do cidadão","example":"Maria da Silva"},
        {"name":"assunto_requerimento","description":"Assunto do requerimento","example":"solicitação de segunda via de certidão de tempo de serviço"},
        {"name":"descricao_solicitacao","description":"Descrição do que foi solicitado","example":"A cidadã solicita certidão de tempo de serviço prestado entre 2010 e 2018 para fins de aposentadoria"},
        {"name":"decisao_resposta","description":"Decisão ou resposta a ser dada","example":"Pedido deferido. A certidão está disponível para retirada na Gerência de RH ou download no portal"},
        {"name":"base_legal","description":"Base legal aplicável","example":"Lei Estadual 17.923/2012 – Acesso à Informação"},
        {"name":"prazo_lei","description":"Prazo previsto em lei","example":"20"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'atendimento');

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'FAQ — Respostas a Perguntas Frequentes',
      'Cria um conjunto de perguntas e respostas frequentes sobre um serviço ou processo público, em linguagem cidadã.',
      E'Você é especialista em comunicação pública e simplificação do atendimento ao cidadão.

Crie um FAQ (Perguntas Frequentes) sobre {{tema_servico}} para o(a) {{orgao_servico}}.

Público-alvo: {{publico_alvo}}
Principais dúvidas mapeadas: {{duvidas_conhecidas}}
Informações adicionais relevantes: {{informacoes_adicionais}}

Gere entre {{numero_perguntas}} perguntas e respostas que:
- Usem linguagem simples, direta e respeitosa
- Respondam de forma completa em até 3 frases
- Incluam links ou caminhos quando necessário
- Cubram os casos de exceção mais comuns
- Sigam o formato: **P:** pergunta / **R:** resposta

Organize as perguntas do mais simples ao mais complexo.',
      (SELECT id FROM prompt_categories WHERE slug = 'atendimento'),
      ARRAY['FAQ','perguntas frequentes','atendimento','serviço público','comunicação'],
      'iniciante',
      '[
        {"name":"tema_servico","description":"Serviço ou processo sobre o qual criar o FAQ","example":"emissão de alvará de funcionamento para pequenas empresas"},
        {"name":"orgao_servico","description":"Órgão responsável pelo serviço","example":"Secretaria de Desenvolvimento Econômico – SDE"},
        {"name":"publico_alvo","description":"Quem vai usar o FAQ","example":"micro e pequenos empresários do Estado de Goiás"},
        {"name":"duvidas_conhecidas","description":"Dúvidas mais comuns recebidas no atendimento","example":"prazo de emissão, documentos necessários, renovação, custo, cancelamento"},
        {"name":"informacoes_adicionais","description":"Informações relevantes do processo","example":"Prazo: 15 dias úteis. Gratuito para MEI. Renovação anual. Portal: goias.gov.br/alvara"},
        {"name":"numero_perguntas","description":"Número de perguntas desejado","example":"10"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'atendimento');

    -- ── Jurídico ──────────────────────────────────────────────────────────────

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Parecer Jurídico Simplificado',
      'Elabora parecer jurídico sobre questão administrativa ou contratual, com análise da legislação aplicável e conclusão fundamentada.',
      E'Você é um advogado especialista em direito administrativo e contratos públicos com experiência no Estado de Goiás.

Elabore um Parecer Jurídico sobre a seguinte questão:

{{questao_juridica}}

Contexto fático:
{{contexto_fatos}}

Legislação a ser analisada: {{legislacao_aplicavel}}

O parecer deve conter:
1. **Ementa** — síntese em até 2 linhas
2. **Relatório** — descrição dos fatos relevantes
3. **Fundamentação Jurídica** — análise da legislação e jurisprudência pertinente
4. **Conclusão** — posicionamento jurídico objetivo (Favorável / Desfavorável / Com ressalvas)
5. **Recomendações** — medidas para mitigar riscos jurídicos

PARECER Nº {{numero_parecer}}/{{ano}}/{{orgao_juridico}}',
      (SELECT id FROM prompt_categories WHERE slug = 'juridico'),
      ARRAY['parecer jurídico','direito administrativo','legislação','contratos','licitação'],
      'avancado',
      '[
        {"name":"questao_juridica","description":"Questão jurídica a ser analisada","example":"legalidade da dispensa de licitação para contratação emergencial de serviços de TI"},
        {"name":"contexto_fatos","description":"Contexto dos fatos relevantes","example":"O sistema de folha de pagamento apresentou falha crítica em 15/04/2025, impossibilitando o processamento da folha de maio. O contrato vigente encerrou em 31/03/2025"},
        {"name":"legislacao_aplicavel","description":"Legislação aplicável ao caso","example":"Lei 14.133/2021 (art. 75, VIII), Lei 8.666/93 (art. 24, IV), Decreto Estadual 9.488/2019"},
        {"name":"numero_parecer","description":"Número do parecer","example":"128"},
        {"name":"ano","description":"Ano","example":"2025"},
        {"name":"orgao_juridico","description":"Sigla do órgão jurídico","example":"PGE-GO"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'juridico');

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Análise de Cláusulas Contratuais',
      'Analisa cláusulas de contratos administrativos, identifica riscos jurídicos e sugere alterações para proteger o interesse público.',
      E'Você é um especialista em contratos administrativos e direito público.

Analise as seguintes cláusulas do contrato de {{tipo_contrato}} celebrado com {{contratada}}:

{{clausulas_analisar}}

Valor do contrato: {{valor_contrato}}
Prazo: {{prazo_contrato}}
Objeto: {{objeto_contrato}}

Para cada cláusula, indique:
- ✅ **Adequada** — está em conformidade com a lei e protege o interesse público
- ⚠️ **Atenção** — precisa de ajuste ou monitoramento
- ❌ **Problemática** — risco jurídico, sugira redação alternativa

Ao final, liste os 3 principais riscos do contrato e as medidas de mitigação recomendadas.',
      (SELECT id FROM prompt_categories WHERE slug = 'juridico'),
      ARRAY['contrato','cláusulas contratuais','risco jurídico','análise contratual'],
      'avancado',
      '[
        {"name":"tipo_contrato","description":"Tipo de contrato","example":"prestação de serviços de desenvolvimento de software"},
        {"name":"contratada","description":"Nome da empresa contratada","example":"TechGov Soluções Digitais Ltda."},
        {"name":"clausulas_analisar","description":"Cláusulas a serem analisadas (cole o texto)","example":"Cláusula 8ª – Em caso de rescisão, a contratada terá direito à indenização por lucros cessantes..."},
        {"name":"valor_contrato","description":"Valor do contrato","example":"R$ 480.000,00 (quatrocentos e oitenta mil reais)"},
        {"name":"prazo_contrato","description":"Prazo do contrato","example":"12 meses, prorrogável por igual período"},
        {"name":"objeto_contrato","description":"Objeto do contrato","example":"desenvolvimento e manutenção do Portal de Transparência Estadual"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'juridico');

    -- ── Resumo e Síntese ──────────────────────────────────────────────────────

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Resumo Executivo de Documento ou Processo',
      'Gera um resumo executivo claro e estruturado de documentos longos, processos administrativos ou relatórios técnicos.',
      E'Você é especialista em síntese de informações para gestores públicos do Estado de Goiás.

Elabore um resumo executivo do seguinte documento/processo:

{{texto_documento}}

Tipo de documento: {{tipo_documento}}
Destinatário do resumo: {{destinatario}}
Finalidade: {{finalidade_resumo}}

O resumo executivo deve:
- Ter no máximo {{max_palavras}} palavras
- Conter: Contexto (2 linhas) | Principais Pontos (bullets) | Decisões ou Pendências | Próximos Passos
- Destacar valores, datas e nomes relevantes em negrito
- Ser compreensível por quem não leu o documento original
- Preservar a precisão das informações sem distorções',
      (SELECT id FROM prompt_categories WHERE slug = 'resumo'),
      ARRAY['resumo executivo','síntese','processo administrativo','relatório','sumarização'],
      'iniciante',
      '[
        {"name":"texto_documento","description":"Texto do documento a ser resumido (cole aqui)","example":"RELATÓRIO DE AUDITORIA INTERNA Nº 05/2025 – Constatou-se que..."},
        {"name":"tipo_documento","description":"Tipo do documento","example":"Relatório de Auditoria Interna"},
        {"name":"destinatario","description":"Para quem se destina o resumo","example":"Secretário de Estado – uso em reunião de gabinete"},
        {"name":"finalidade_resumo","description":"Para que será usado o resumo","example":"subsidiar tomada de decisão em reunião de 30 minutos"},
        {"name":"max_palavras","description":"Número máximo de palavras","example":"300"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'resumo');

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Ata de Reunião',
      'Elabora ata de reunião formal ou simplificada a partir das anotações ou transcrição da reunião.',
      E'Você é um especialista em documentação administrativa do serviço público.

Elabore a ata da reunião com base nas seguintes informações:

Reunião: {{titulo_reuniao}}
Data e local: {{data_local}}
Presentes: {{presentes}}
Pauta: {{pauta}}

Anotações/transcrição da reunião:
{{anotacoes_reuniao}}

A ata deve:
- Seguir formato oficial (número, data, local, presentes, desenvolvimento, encaminhamentos)
- Registrar fielmente as decisões tomadas, sem interpretações
- Listar os encaminhamentos com responsável e prazo
- Usar linguagem formal e impessoal
- Incluir campo para assinatura dos participantes

ATA Nº {{numero_ata}}/{{ano}} — {{orgao}}',
      (SELECT id FROM prompt_categories WHERE slug = 'resumo'),
      ARRAY['ata','reunião','encaminhamentos','documentação','registro'],
      'iniciante',
      '[
        {"name":"titulo_reuniao","description":"Título ou tipo da reunião","example":"Reunião Ordinária do Comitê de Governança Digital"},
        {"name":"data_local","description":"Data, hora e local da reunião","example":"12 de maio de 2025, às 14h, Sala de Reuniões A – Palácio das Esmeraldas"},
        {"name":"presentes","description":"Lista de participantes com cargo","example":"João Silva (Presidente), Ana Costa (Secretária), Pedro Lima (TI), Carla Moura (Jurídico)"},
        {"name":"pauta","description":"Itens de pauta","example":"1. Aprovação da ata anterior; 2. Andamento do Projeto GO Digital; 3. Aprovação do orçamento de TI 2026; 4. Assuntos gerais"},
        {"name":"anotacoes_reuniao","description":"Anotações ou transcrição da reunião","example":"João abriu a sessão às 14h05. A ata anterior foi aprovada por unanimidade. Pedro apresentou o relatório do GO Digital: 65% concluído, prazo mantido para dezembro..."},
        {"name":"numero_ata","description":"Número sequencial da ata","example":"008"},
        {"name":"ano","description":"Ano","example":"2025"},
        {"name":"orgao","description":"Órgão ou comitê","example":"GOIÁS TI"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'resumo');

    -- ── Gestão e Planejamento ─────────────────────────────────────────────────

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Plano de Ação 5W2H',
      'Cria um plano de ação estruturado no formato 5W2H para projetos, iniciativas ou soluções de problemas no serviço público.',
      E'Você é um especialista em gestão pública e planejamento estratégico.

Elabore um Plano de Ação no formato 5W2H para:

Problema ou objetivo: {{problema_objetivo}}
Contexto: {{contexto}}
Recursos disponíveis: {{recursos}}
Prazo final: {{prazo_final}}
Responsável geral: {{responsavel_geral}}

Crie o plano com pelo menos {{numero_acoes}} ações, preenchendo todas as colunas:
- **What** (O quê) — ação específica
- **Why** (Por quê) — justificativa
- **Who** (Quem) — responsável
- **When** (Quando) — prazo
- **Where** (Onde) — local/sistema
- **How** (Como) — método/procedimento
- **How Much** (Quanto) — custo estimado ou "Sem custo adicional"

Ao final, adicione indicadores de sucesso para monitoramento.',
      (SELECT id FROM prompt_categories WHERE slug = 'gestao'),
      ARRAY['5W2H','plano de ação','gestão','planejamento','projetos'],
      'intermediario',
      '[
        {"name":"problema_objetivo","description":"Problema a resolver ou objetivo a atingir","example":"reduzir em 40% o tempo médio de resposta a solicitações de acesso à informação"},
        {"name":"contexto","description":"Contexto da situação","example":"O tempo médio atual é de 22 dias, acima do limite legal de 20 dias. Há 3 servidores na equipe e sistema manual de controle"},
        {"name":"recursos","description":"Recursos disponíveis","example":"3 servidores, sistema SEI, possibilidade de automatização via RPA, orçamento de R$ 15.000"},
        {"name":"prazo_final","description":"Data limite para conclusão","example":"30/09/2025"},
        {"name":"responsavel_geral","description":"Responsável geral pelo plano","example":"Coordenador de Transparência – João Mendes"},
        {"name":"numero_acoes","description":"Número mínimo de ações","example":"6"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'gestao');

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Análise SWOT de Projeto ou Iniciativa',
      'Realiza análise SWOT completa de um projeto, política pública ou iniciativa governamental, com recomendações estratégicas.',
      E'Você é um consultor especialista em estratégia e gestão pública.

Realize uma análise SWOT completa do seguinte projeto/iniciativa:

Nome: {{nome_projeto}}
Descrição: {{descricao_projeto}}
Órgão responsável: {{orgao}}
Objetivo estratégico: {{objetivo_estrategico}}
Contexto atual: {{contexto_atual}}

Mapeie:

**FORÇAS (Strengths)** — fatores internos positivos
**FRAQUEZAS (Weaknesses)** — fatores internos negativos
**OPORTUNIDADES (Opportunities)** — fatores externos favoráveis
**AMEAÇAS (Threats)** — fatores externos desfavoráveis

Ao final, desenvolva:
1. **Estratégias SO** (usar forças para aproveitar oportunidades)
2. **Estratégias WO** (superar fraquezas aproveitando oportunidades)
3. **Estratégias ST** (usar forças para minimizar ameaças)
4. **Estratégias WT** (minimizar fraquezas e evitar ameaças)
5. **Top 3 Recomendações** prioritárias com justificativa',
      (SELECT id FROM prompt_categories WHERE slug = 'gestao'),
      ARRAY['SWOT','análise estratégica','projetos','planejamento','gestão pública'],
      'intermediario',
      '[
        {"name":"nome_projeto","description":"Nome do projeto ou iniciativa","example":"Implantação do Atendimento Digital Integrado – ADI-GO"},
        {"name":"descricao_projeto","description":"Breve descrição do projeto","example":"Plataforma unificada de serviços digitais que integra 45 serviços de 8 secretarias em um único portal com autenticação gov.br"},
        {"name":"orgao","description":"Órgão responsável","example":"GOIÁS TI / SEGPLAN"},
        {"name":"objetivo_estrategico","description":"Objetivo estratégico do projeto","example":"Digitalizar 80% dos serviços ao cidadão até dezembro de 2026"},
        {"name":"contexto_atual","description":"Contexto atual relevante","example":"Atualmente 30% dos serviços são digitais, cidadãos precisam visitar fisicamente múltiplos órgãos, alto índice de reclamações no Fala.BR"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'gestao');

    INSERT INTO prompts (title, description, content, category_id, tags, difficulty, variables, is_public)
    SELECT
      'Relatório de Gestão Mensal',
      'Gera relatório de gestão mensal estruturado para prestação de contas interna, com indicadores, realizações e pendências.',
      E'Você é um especialista em gestão e reporting público do Governo de Goiás.

Elabore o Relatório de Gestão referente ao mês de {{mes_referencia}}/{{ano}} para {{area_responsavel}}.

Realizações do período:
{{realizacoes}}

Indicadores:
{{indicadores}}

Dificuldades encontradas:
{{dificuldades}}

Pendências para o próximo período:
{{pendencias}}

O relatório deve:
- Ter estrutura: Sumário Executivo | Realizações | Indicadores (tabela) | Desafios | Próximo Mês
- Destacar conquistas em relação às metas
- Ser objetivo, com no máximo 2 páginas
- Incluir semáforo de status: 🟢 No prazo | 🟡 Em atenção | 🔴 Atrasado
- Finalizar com os 3 compromissos prioritários do próximo mês',
      (SELECT id FROM prompt_categories WHERE slug = 'gestao'),
      ARRAY['relatório de gestão','prestação de contas','indicadores','mensal','monitoramento'],
      'iniciante',
      '[
        {"name":"mes_referencia","description":"Mês de referência","example":"Abril"},
        {"name":"ano","description":"Ano","example":"2025"},
        {"name":"area_responsavel","description":"Área ou gerência responsável","example":"Gerência de Inovação e Transformação Digital – GOIÁS TI"},
        {"name":"realizacoes","description":"Principais realizações do mês","example":"Lançamento do módulo de agendamento online (3.200 atendimentos na 1ª semana); Treinamento de 45 servidores no SEI; Homologação do novo portal de transparência"},
        {"name":"indicadores","description":"Indicadores com valores realizados vs. meta","example":"SLA de atendimento: 94% (meta 90%) ✅ | Projetos no prazo: 7/9 (78%, meta 85%) ⚠️ | Satisfação usuário: 4,3/5 (meta 4,0) ✅"},
        {"name":"dificuldades","description":"Principais dificuldades do período","example":"Indisponibilidade do servidor de homologação por 3 dias; 2 servidores em licença médica no período crítico"},
        {"name":"pendencias","description":"Pendências para o próximo período","example":"Migração do legado para nova plataforma (prazo: 30/05); Contratação de suporte técnico especializado"}
      ]'::jsonb,
      TRUE
    WHERE EXISTS (SELECT 1 FROM prompt_categories WHERE slug = 'gestao');
  