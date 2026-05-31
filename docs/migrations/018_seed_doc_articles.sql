
    -- Guia de Uso: Instalando um Servidor MCP no Claude Code
    INSERT INTO doc_articles (section_id, title, slug, content, reading_time, sort_order, is_published)
    SELECT
      (SELECT id FROM doc_sections WHERE slug = 'guia-de-uso'),
      'Como instalar um Servidor MCP no Claude Code',
      'instalar-servidor-mcp-claude-code',
      '# Como instalar um Servidor MCP no Claude Code

O **Model Context Protocol (MCP)** permite estender as capacidades do Claude conectando-o a servidores que fornecem ferramentas, dados e contexto adicionais. Neste guia, você aprenderá a instalar e configurar um servidor MCP diretamente no Claude Code (CLI).

---

## Pré-requisitos

- **Claude Code** instalado e funcionando (instale com `npm install -g @anthropic-ai/claude-code`)
- **Node.js** versão 18 ou superior
- Terminal com acesso à internet

---

## Passo 1 — Abrir as configurações do Claude Code

No terminal, execute o Claude Code e use o comando de configuração:

```bash
claude
```

Dentro do Claude Code, digite:

```
/mcp
```

Isso abrirá o menu de gerenciamento de servidores MCP.

---

## Passo 2 — Adicionar um novo servidor MCP

Selecione a opção **Add MCP Server** e escolha o tipo de transporte. O mais comum é **stdio** para servidores locais.

Exemplo para adicionar o servidor **filesystem** (acesso a arquivos):

```
Nome: filesystem
Tipo: stdio
Comando: npx -y @modelcontextprotocol/server-filesystem /caminho/do/diretorio
```

---

## Passo 3 — Verificar a instalação

Após adicionar o servidor, o Claude Code tentará se conectar automaticamente. Você verá uma mensagem indicando as ferramentas disponíveis:

```
✓ MCP server "filesystem" connected
  Tools available: read_file, write_file, list_directory
```

Para listar os servidores configurados:

```
/mcp
```

---

## Passo 4 — Usar o servidor MCP

Agora você pode pedir ao Claude para usar as ferramentas do servidor. Exemplos:

- *"Liste os arquivos no diretório /projetos"*
- *"Leia o conteúdo do arquivo config.yaml"*

O Claude utilizará automaticamente as ferramentas do servidor MCP para atender ao seu pedido.

---

## Exemplos de servidores MCP populares

| Servidor | Comando | Descrição |
|----------|---------|-----------|
| Filesystem | `npx -y @modelcontextprotocol/server-filesystem /pasta` | Acesso a arquivos locais |
| GitHub | `npx -y @modelcontextprotocol/server-github` | Integração com repositórios GitHub |
| PostgreSQL | `npx -y @modelcontextprotocol/server-postgres postgres://...` | Consultas ao banco de dados |
| Memory | `npx -y @modelcontextprotocol/server-memory` | Memória persistente para o Claude |

---

## Configuração via arquivo

Você também pode configurar servidores MCP editando o arquivo de configuração diretamente:

```bash
# Arquivo de configuração do projeto
.claude/settings.json

# Arquivo de configuração global
~/.claude/settings.json
```

Adicione a seção `mcpServers`:

```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/caminho"]
    }
  }
}
```

---

## Solução de problemas

- **Servidor não conecta:** Verifique se o comando funciona diretamente no terminal antes de configurá-lo no Claude Code.
- **Ferramentas não aparecem:** Reinicie o Claude Code após alterar configurações.
- **Erros de permissão:** Certifique-se de que o servidor tem acesso aos recursos necessários (arquivos, rede, etc.).

---

## Próximos passos

- Explore o catálogo de servidores MCP disponíveis na plataforma
- Crie seu próprio servidor MCP seguindo a [especificação oficial](https://modelcontextprotocol.io)',
      8,
      1,
      TRUE
    WHERE EXISTS (SELECT 1 FROM doc_sections WHERE slug = 'guia-de-uso');

    -- Guia de Uso: Instalando um Servidor MCP no VS Code
    INSERT INTO doc_articles (section_id, title, slug, content, reading_time, sort_order, is_published)
    SELECT
      (SELECT id FROM doc_sections WHERE slug = 'guia-de-uso'),
      'Como instalar um Servidor MCP no VS Code',
      'instalar-servidor-mcp-vscode',
      '# Como instalar um Servidor MCP no VS Code

O **VS Code** oferece suporte a servidores MCP através da extensão **GitHub Copilot** (modo Agent) e também pela extensão **Claude Code**. Neste guia, você aprenderá a configurar um servidor MCP no VS Code para expandir as capacidades do seu assistente de IA.

---

## Pré-requisitos

- **VS Code** versão 1.99 ou superior
- **GitHub Copilot** ativado ou extensão **Claude Code** instalada
- **Node.js** versão 18 ou superior

---

## Método 1 — Configuração via settings.json do VS Code

### Passo 1 — Abrir as configurações

Abra a paleta de comandos com `Ctrl+Shift+P` (ou `Cmd+Shift+P` no Mac) e digite:

```
Preferences: Open User Settings (JSON)
```

### Passo 2 — Adicionar o servidor MCP

Adicione a configuração do servidor MCP no arquivo `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "filesystem": {
        "type": "stdio",
        "command": "npx",
        "args": [
          "-y",
          "@modelcontextprotocol/server-filesystem",
          "/caminho/do/diretorio"
        ]
      }
    }
  }
}
```

### Passo 3 — Verificar o status

Após salvar, o VS Code detectará automaticamente o servidor. Você verá um indicador no painel do Copilot Chat mostrando o servidor conectado e as ferramentas disponíveis.

---

## Método 2 — Configuração via arquivo .vscode/mcp.json

Para configurações específicas de um projeto, crie o arquivo `.vscode/mcp.json` na raiz do projeto:

```json
{
  "servers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${input:github_token}"
      }
    },
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgres://usuario:senha@localhost:5432/banco"
      ]
    }
  },
  "inputs": [
    {
      "id": "github_token",
      "type": "promptString",
      "description": "Token de acesso pessoal do GitHub",
      "password": true
    }
  ]
}
```

> **Dica:** Use `inputs` para solicitar informações sensíveis como tokens, evitando armazená-las no código.

---

## Método 3 — Adicionar via linha de comando

O VS Code também suporta a instalação direta pela paleta de comandos:

1. Abra a paleta de comandos (`Ctrl+Shift+P`)
2. Digite **"MCP: Add Server"**
3. Escolha o tipo de transporte (stdio, sse, streamable-http)
4. Informe o comando e os argumentos

---

## Usando servidores MCP no Copilot Chat

Após configurar o servidor, abra o **Copilot Chat** no modo **Agent** (selecione "Agent" no dropdown do chat) e utilize normalmente:

1. As ferramentas do servidor MCP aparecerão automaticamente
2. O Copilot pedirá confirmação antes de usar cada ferramenta
3. Você pode referenciar ferramentas específicas com `#`

Exemplos de uso:
- *"Use o servidor filesystem para listar os arquivos da pasta src"*
- *"Consulte o banco de dados para ver as tabelas existentes"*

---

## Servidores MCP recomendados para VS Code

| Servidor | Finalidade | Instalação |
|----------|-----------|------------|
| Filesystem | Leitura e escrita de arquivos | `npx -y @modelcontextprotocol/server-filesystem` |
| GitHub | Issues, PRs, repositórios | `npx -y @modelcontextprotocol/server-github` |
| PostgreSQL | Consultas SQL | `npx -y @modelcontextprotocol/server-postgres` |
| Brave Search | Pesquisa web | `npx -y @anthropic-ai/mcp-server-brave-search` |

---

## Solução de problemas

- **Servidor não aparece:** Recarregue a janela do VS Code (`Ctrl+Shift+P` → "Reload Window").
- **Erro de conexão:** Teste o comando do servidor diretamente no terminal integrado.
- **Ferramentas não disponíveis:** Verifique se o modo Agent está selecionado no Copilot Chat.
- **Variáveis de ambiente:** Use o campo `env` na configuração ou o sistema de `inputs` para tokens e credenciais.

---

## Próximos passos

- Explore o catálogo de servidores MCP disponíveis na plataforma
- Combine múltiplos servidores para criar fluxos de trabalho avançados
- Consulte a documentação oficial do VS Code sobre [Language Model Tools](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)',
      10,
      2,
      TRUE
    WHERE EXISTS (SELECT 1 FROM doc_sections WHERE slug = 'guia-de-uso');

    -- Introdução: Como Criar Prompts Melhores
    INSERT INTO doc_articles (section_id, title, slug, content, reading_time, sort_order, is_published)
    SELECT
      (SELECT id FROM doc_sections WHERE slug = 'introducao'),
      'Como Criar Prompts Melhores',
      'como-criar-prompts-melhores',
      '# Como Criar Prompts Melhores

Escrever bons prompts é a habilidade mais importante para aproveitar ao máximo a Inteligência Artificial generativa. Um prompt bem escrito pode ser a diferença entre uma resposta genérica e um resultado altamente útil para o seu trabalho. Neste guia, você aprenderá técnicas práticas para criar prompts eficazes.

---

## O que é um Prompt?

Um **prompt** é a instrução ou pergunta que você envia para a IA. Pense nele como um briefing: quanto mais claro e completo, melhor será o resultado entregue.

---

## Os 5 Princípios de um Bom Prompt

### 1. Seja Específico

Evite instruções vagas. Quanto mais detalhes você fornecer, mais precisa será a resposta.

| Prompt fraco | Prompt forte |
|----------------|----------------|
| "Escreva um relatório" | "Escreva um relatório executivo de 2 páginas sobre o andamento do projeto de digitalização de serviços públicos, destacando os 3 principais marcos alcançados no último trimestre e os 2 riscos que exigem atenção." |
| "Resuma esse texto" | "Resuma o texto a seguir em 5 tópicos, destacando as obrigações legais e os prazos para o órgão público." |

### 2. Defina o Papel da IA

Atribuir um papel (persona) ajuda a IA a ajustar o tom, o vocabulário e a profundidade da resposta.

```
Você é um analista jurídico especializado em licitações públicas
do Estado de Goiás. Analise o edital a seguir e identifique
possíveis inconsistências com a Lei 14.133/2021.
```

Outros exemplos de papéis úteis:
- *"Você é um redator de comunicação oficial..."*
- *"Você é um cientista de dados do setor público..."*
- *"Você é um especialista em atendimento ao cidadão..."*

### 3. Forneça Contexto

A IA não sabe qual é o seu cargo, sua secretaria ou a situação específica. Inclua o contexto necessário.

```
Contexto: Sou gerente de TI na Secretaria de Saúde de Goiás.
Estamos migrando o sistema de prontuário eletrônico para a nuvem.
O prazo final é dezembro de 2026.

Tarefa: Elabore um checklist de segurança da informação para
essa migração, considerando a LGPD e as normas do CTIR Gov.
```

### 4. Especifique o Formato de Saída

Diga exatamente como você quer receber a resposta.

```
Liste as 10 principais métricas de desempenho para um portal
de serviços públicos, no seguinte formato:

| # | Métrica | O que mede | Meta sugerida |
```

Formatos que você pode pedir:
- **Tabela** — para comparações e dados estruturados
- **Lista numerada** — para passos sequenciais
- **Tópicos** — para resumos e destaques
- **JSON** — para integração com sistemas
- **Texto corrido** — para documentos e comunicações

### 5. Dê Exemplos (Few-Shot)

Mostrar um exemplo do resultado esperado é uma das técnicas mais poderosas.

```
Classifique as demandas de cidadãos abaixo por categoria e urgência.

Exemplo:
- Demanda: "Meu alvará de funcionamento está vencido há 3 meses"
- Categoria: Licenciamento
- Urgência: Alta

Agora classifique:
1. "Preciso de uma segunda via do meu IPVA"
2. "O sistema do Detran está fora do ar desde ontem"
3. "Gostaria de saber os horários do Vapt Vupt mais próximo"
```

---

## Técnicas Avançadas

### Cadeia de Pensamento (Chain of Thought)

Peça para a IA explicar o raciocínio passo a passo. Isso melhora significativamente a qualidade em tarefas analíticas.

```
Analise se a contratação abaixo está em conformidade com a
Lei 14.133/2021. Pense passo a passo:

1. Primeiro, identifique a modalidade de licitação aplicável
2. Depois, verifique os requisitos obrigatórios dessa modalidade
3. Por fim, compare com os dados da contratação e aponte
   conformidades e não-conformidades

Dados da contratação: [...]
```

### Iteração e Refinamento

Não espere o prompt perfeito na primeira tentativa. Use um ciclo de melhoria:

1. **Escreva** o prompt inicial
2. **Avalie** a resposta da IA
3. **Ajuste** o prompt adicionando mais contexto, restrições ou exemplos
4. **Repita** até obter o resultado desejado

### Restrições e Limites

Defina o que a IA **não** deve fazer:

```
Escreva uma resposta ao cidadão sobre o atraso na entrega
do documento solicitado.

Restrições:
- NÃO invente prazos ou datas
- NÃO cite legislação sem ter certeza da aplicabilidade
- Mantenha tom empático, mas formal
- Máximo de 200 palavras
```

---

## Erros Comuns a Evitar

1. **Prompt muito curto** — "Faça um resumo" não dá contexto suficiente
2. **Múltiplas tarefas em um prompt** — Divida tarefas complexas em etapas
3. **Falta de formato** — Sem indicação de formato, a IA escolhe por você
4. **Informação ambígua** — Seja preciso com nomes, datas e números
5. **Não revisar a resposta** — Sempre valide dados, datas e citações legais

---

## Modelo de Prompt Estruturado

Use este modelo como ponto de partida para seus prompts:

```
[PAPEL]: Você é um(a) [especialidade] do setor público de Goiás.

[CONTEXTO]: [Descreva a situação, o órgão, o projeto ou problema]

[TAREFA]: [O que exatamente você precisa que a IA faça]

[FORMATO]: [Como a resposta deve ser estruturada]

[RESTRIÇÕES]: [O que a IA deve evitar]

[EXEMPLO]: [Opcional — um exemplo do resultado esperado]
```

---

## Próximos passos

- Explore a **Biblioteca de Prompts** para ver exemplos prontos
- Experimente adaptar os prompts da biblioteca ao seu contexto
- Pratique o ciclo de iteração para aperfeiçoar seus resultados',
      12,
      1,
      TRUE
    WHERE EXISTS (SELECT 1 FROM doc_sections WHERE slug = 'introducao');
  