
    INSERT INTO users (name, email, codg_usuario, role, organ, is_active)
    VALUES
      ('Demo Produto GO.IA', 'demo.produto@goia.local', 'demo.produto', 'gestor_produto', 'Secretaria-Geral de Governo', TRUE),
      ('Ana Demo', 'demo.ana@goia.local', 'demo.ana', 'servidor', 'Secretaria de Administração', TRUE),
      ('Bruno Demo', 'demo.bruno@goia.local', 'demo.bruno', 'gestor', 'Secretaria de Economia', TRUE),
      ('Carla Demo', 'demo.carla@goia.local', 'demo.carla', 'curador', 'Controladoria-Geral do Estado', TRUE),
      ('Diego Demo', 'demo.diego@goia.local', 'demo.diego', 'servidor', 'Secretaria de Saúde', TRUE)
    ON CONFLICT (email) DO UPDATE SET
      name = EXCLUDED.name,
      role = EXCLUDED.role,
      organ = EXCLUDED.organ,
      is_active = TRUE,
      updated_at = NOW();

    INSERT INTO idea_versions (name, description, forecast, sort_order, is_active, created_by)
    SELECT v.name, v.description, v.forecast, v.sort_order, TRUE, u.id
    FROM (
      VALUES
        ('GO.IA 1.0 - Portal colaborativo', 'Marco inicial com ideias, votos, comentários e roadmap público.', 'Entregue', 10),
        ('GO.IA 1.1 - Produtividade', 'Melhorias para acompanhamento, atalhos e trabalho em equipe.', 'Próxima versão', 20),
        ('GO.IA 1.2 - Governança', 'Evoluções de auditoria, revisão e rastreabilidade.', 'Planejada', 30),
        ('GO.IA 2.0 - Integrações', 'Conectores e automações entre o GO.IA e sistemas corporativos.', 'Futuro', 40)
    ) AS v(name, description, forecast, sort_order)
    CROSS JOIN users u
    WHERE u.email = 'demo.produto@goia.local'
    ON CONFLICT (name) DO UPDATE SET
      description = EXCLUDED.description,
      forecast = EXCLUDED.forecast,
      sort_order = EXCLUDED.sort_order,
      is_active = TRUE,
      updated_at = NOW();

    WITH idea_input AS (
      SELECT *
      FROM (
        VALUES
          (
            'Painel de acompanhamento dos meus pedidos de acesso',
            'Centralizar em uma única visão o andamento dos pedidos de acesso a modelos.',
            'Hoje o usuário precisa navegar por telas diferentes para entender se um pedido foi aprovado, negado ou precisa de ajuste. Um painel resumido reduziria chamados ao suporte e deixaria o acompanhamento mais claro.',
            'demo.ana@goia.local',
            'publicada',
            'planejada',
            'GO.IA 1.1 - Produtividade',
            'Ideia aprovada para planejamento porque reduz atrito no uso diário.',
            NULL,
            NULL,
            NULL,
            NULL,
            NOW() - INTERVAL '12 days',
            NOW() - INTERVAL '11 days',
            'demo.produto@goia.local'
          ),
          (
            'Favoritos compartilhados por equipe',
            'Permitir que equipes compartilhem modelos, prompts e MCPs favoritos.',
            'Unidades com trabalho recorrente poderiam manter uma curadoria própria de atalhos para seus fluxos mais usados, acelerando onboarding e padronizando boas práticas.',
            'demo.bruno@goia.local',
            'publicada',
            'em_desenvolvimento',
            'GO.IA 1.1 - Produtividade',
            'Priorizada por impacto transversal entre órgãos.',
            NULL,
            NULL,
            NULL,
            NULL,
            NOW() - INTERVAL '25 days',
            NOW() - INTERVAL '24 days',
            'demo.produto@goia.local'
          ),
          (
            'Histórico de mudanças dos prompts oficiais',
            'Mostrar versões anteriores e justificativa de alterações em prompts oficiais.',
            'Quando um prompt oficial muda, os usuários precisam entender o que foi alterado e por qual motivo. Um histórico visível melhora governança, confiança e auditoria.',
            'demo.carla@goia.local',
            'publicada',
            'concluida',
            'GO.IA 1.0 - Portal colaborativo',
            'Entregue junto com a primeira rodada de governança de conteúdo.',
            NULL,
            NULL,
            NULL,
            NULL,
            NOW() - INTERVAL '45 days',
            NOW() - INTERVAL '44 days',
            'demo.produto@goia.local'
          ),
          (
            'Atalhos personalizáveis na tela inicial',
            'Permitir que cada usuário escolha seus atalhos mais usados no Início.',
            'A tela inicial poderia se adaptar ao perfil de uso, exibindo modelos, prompts, documentos ou páginas administrativas que o usuário acessa com frequência.',
            'demo.diego@goia.local',
            'publicada',
            NULL,
            NULL,
            'Publicada para medir apoio antes de entrar no roadmap.',
            NULL,
            NULL,
            NULL,
            NULL,
            NOW() - INTERVAL '4 days',
            NOW() - INTERVAL '3 days',
            'demo.produto@goia.local'
          ),
          (
            'Sugestão automática de prompt por contexto',
            'Sugerir prompts relevantes conforme texto digitado pelo usuário.',
            'Ao escrever uma necessidade, o GO.IA poderia indicar prompts existentes que resolvem problemas parecidos, evitando duplicidade e aumentando o reuso da biblioteca.',
            'demo.ana@goia.local',
            'aguardando_curadoria',
            NULL,
            NULL,
            NULL,
            NULL,
            NULL,
            NULL,
            NULL,
            NOW() - INTERVAL '1 day',
            NULL,
            NULL
          ),
          (
            'Permitir exportar dados sensíveis sem mascaramento',
            'Adicionar opção para exportar dados sensíveis sem máscara quando o usuário desejar.',
            'A ideia propunha remover mascaramento em relatórios exportados, mas não apresentava controles de segurança, trilha de auditoria ou justificativa compatível com as políticas de proteção de dados.',
            'demo.bruno@goia.local',
            'rejeitada',
            NULL,
            NULL,
            NULL,
            'Rejeitada por violar política de segurança e proteção de dados.',
            NULL,
            NULL,
            NULL,
            NOW() - INTERVAL '18 days',
            NULL,
            'demo.produto@goia.local'
          ),
          (
            'Agrupar modelos por secretaria',
            'Criar agrupamentos de modelos e prompts por secretaria ou unidade administrativa.',
            'A organização por secretaria facilitaria encontrar recursos homologados para cada contexto institucional. O autor solicitou exclusão porque a proposta será reescrita com escopo menor.',
            'demo.carla@goia.local',
            'exclusao_solicitada',
            NULL,
            NULL,
            'Publicada originalmente para avaliação da comunidade.',
            NULL,
            NOW() - INTERVAL '2 days',
            'A ideia será reenviada com foco apenas em modelos oficiais por unidade.',
            NULL,
            NOW() - INTERVAL '20 days',
            NOW() - INTERVAL '19 days',
            'demo.produto@goia.local'
          ),
          (
            'Publicar credenciais de integração em comentários',
            'Permitir colar tokens e chaves de API em comentários para facilitar suporte.',
            'A proposta foi removida da experiência pública porque incentivava compartilhamento de segredos em área colaborativa.',
            'demo.diego@goia.local',
            'excluida',
            NULL,
            NULL,
            NULL,
            'Excluída por violação de política de segurança.',
            NULL,
            NULL,
            NOW() - INTERVAL '6 days',
            NOW() - INTERVAL '28 days',
            NOW() - INTERVAL '27 days',
            'demo.produto@goia.local'
          )
      ) AS raw(
        title,
        short_description,
        description,
        author_email,
        moderation_status,
        idea_status,
        version_name,
        curation_notes,
        rejection_reason,
        deletion_requested_at,
        deletion_request_reason,
        deleted_at,
        created_at,
        published_at,
        reviewer_email
      )
    )
    INSERT INTO ideas (
      title,
      description,
      author_id,
      moderation_status,
      idea_status,
      version_id,
      curation_notes,
      rejection_reason,
      deletion_requested_at,
      deletion_request_reason,
      deleted_at,
      created_at,
      published_at,
      reviewed_by,
      reviewed_at
    )
    SELECT
      i.title,
      i.description,
      author.id,
      i.moderation_status::idea_moderation_status,
      i.idea_status::idea_status,
      version.id,
      i.curation_notes,
      i.rejection_reason,
      i.deletion_requested_at,
      i.deletion_request_reason,
      i.deleted_at,
      i.created_at,
      i.published_at,
      reviewer.id,
      CASE WHEN reviewer.id IS NULL THEN NULL ELSE COALESCE(i.published_at, i.created_at + INTERVAL '1 day') END
    FROM idea_input i
    JOIN users author ON author.email = i.author_email
    LEFT JOIN users reviewer ON reviewer.email = i.reviewer_email
    LEFT JOIN idea_versions version ON version.name = i.version_name
    WHERE NOT EXISTS (
      SELECT 1
      FROM ideas existing
      WHERE existing.title = i.title
        AND existing.author_id = author.id
    );

    UPDATE idea_topics
    SET name = CASE slug
      WHEN 'documentacao' THEN 'Documentação'
      WHEN 'noticias' THEN 'Notícias'
      WHEN 'seguranca' THEN 'Segurança'
      WHEN 'integracoes' THEN 'Integrações'
      WHEN 'administracao' THEN 'Administração'
      WHEN 'governanca' THEN 'Governança'
      ELSE name
    END,
    updated_at = NOW()
    WHERE slug IN ('documentacao', 'noticias', 'seguranca', 'integracoes', 'administracao', 'governanca');

    WITH topic_input AS (
      SELECT *
      FROM (
        VALUES
          ('Painel de acompanhamento dos meus pedidos de acesso', 'modelos'),
          ('Painel de acompanhamento dos meus pedidos de acesso', 'administracao'),
          ('Painel de acompanhamento dos meus pedidos de acesso', 'interface'),
          ('Favoritos compartilhados por equipe', 'plataforma'),
          ('Favoritos compartilhados por equipe', 'interface'),
          ('Favoritos compartilhados por equipe', 'governanca'),
          ('Histórico de mudanças dos prompts oficiais', 'prompts'),
          ('Histórico de mudanças dos prompts oficiais', 'governanca'),
          ('Atalhos personalizáveis na tela inicial', 'interface'),
          ('Atalhos personalizáveis na tela inicial', 'plataforma'),
          ('Sugestão automática de prompt por contexto', 'prompts'),
          ('Sugestão automática de prompt por contexto', 'modelos'),
          ('Permitir exportar dados sensíveis sem mascaramento', 'seguranca'),
          ('Permitir exportar dados sensíveis sem mascaramento', 'governanca'),
          ('Agrupar modelos por secretaria', 'modelos'),
          ('Agrupar modelos por secretaria', 'administracao'),
          ('Publicar credenciais de integração em comentários', 'seguranca'),
          ('Publicar credenciais de integração em comentários', 'integracoes')
      ) AS raw(idea_title, topic_slug)
    )
    INSERT INTO idea_topic_links (idea_id, topic_id)
    SELECT idea.id, topic.id
    FROM topic_input input
    JOIN ideas idea ON idea.title = input.idea_title
    JOIN idea_topics topic ON topic.slug = input.topic_slug
    ON CONFLICT DO NOTHING;

    WITH comment_input AS (
      SELECT *
      FROM (
        VALUES
          ('Painel de acompanhamento dos meus pedidos de acesso', 'demo.bruno@goia.local', NULL, 'Isso ajudaria muito os gestores que acompanham pedidos de várias equipes.', 'publicado', NULL, NULL, NOW() - INTERVAL '9 days'),
          ('Painel de acompanhamento dos meus pedidos de acesso', 'demo.carla@goia.local', 'Isso ajudaria muito os gestores que acompanham pedidos de várias equipes.', 'Concordo. Também seria útil filtrar por status e por órgão.', 'publicado', NULL, NULL, NOW() - INTERVAL '8 days'),
          ('Painel de acompanhamento dos meus pedidos de acesso', 'demo.diego@goia.local', NULL, 'Seria bom receber alerta quando o pedido mudar de etapa.', 'publicado', NULL, NULL, NOW() - INTERVAL '7 days'),
          ('Favoritos compartilhados por equipe', 'demo.ana@goia.local', NULL, 'Poder compartilhar listas oficiais por unidade evitaria retrabalho.', 'publicado', NULL, NULL, NOW() - INTERVAL '20 days'),
          ('Favoritos compartilhados por equipe', 'demo.produto@goia.local', 'Poder compartilhar listas oficiais por unidade evitaria retrabalho.', 'Esse ponto entrou nos critérios de desenho da versão em desenvolvimento.', 'publicado', NULL, NULL, NOW() - INTERVAL '18 days'),
          ('Histórico de mudanças dos prompts oficiais', 'demo.bruno@goia.local', NULL, 'A rastreabilidade ficou essencial para justificar mudanças em prompts usados por vários órgãos.', 'publicado', NULL, NULL, NOW() - INTERVAL '40 days'),
          ('Atalhos personalizáveis na tela inicial', 'demo.carla@goia.local', NULL, 'Apoio a ideia, especialmente se os atalhos respeitarem permissões do usuário.', 'publicado', NULL, NULL, NOW() - INTERVAL '2 days'),
          ('Atalhos personalizáveis na tela inicial', 'demo.produto@goia.local', NULL, 'Comentário oculto de exemplo para validar restauração pela curadoria.', 'oculto', 'Conteúdo duplicado usado em teste de moderação.', 'demo.produto@goia.local', NOW() - INTERVAL '1 day')
      ) AS raw(idea_title, author_email, parent_content, content, moderation_status, moderation_reason, moderator_email, created_at)
    )
    INSERT INTO idea_comments (
      idea_id,
      parent_id,
      author_id,
      content,
      moderation_status,
      moderation_reason,
      moderated_by,
      moderated_at,
      created_at
    )
    SELECT
      idea.id,
      parent.id,
      author.id,
      input.content,
      input.moderation_status::idea_comment_moderation_status,
      input.moderation_reason,
      moderator.id,
      CASE WHEN input.moderation_status = 'oculto' THEN input.created_at + INTERVAL '2 hours' ELSE NULL END,
      input.created_at
    FROM comment_input input
    JOIN ideas idea ON idea.title = input.idea_title
    JOIN users author ON author.email = input.author_email
    LEFT JOIN users moderator ON moderator.email = input.moderator_email
    LEFT JOIN idea_comments parent ON parent.idea_id = idea.id AND parent.content = input.parent_content
    WHERE NOT EXISTS (
      SELECT 1
      FROM idea_comments existing
      WHERE existing.idea_id = idea.id
        AND existing.content = input.content
    );

    WITH vote_input AS (
      SELECT *
      FROM (
        VALUES
          ('Painel de acompanhamento dos meus pedidos de acesso', 'demo.bruno@goia.local'),
          ('Painel de acompanhamento dos meus pedidos de acesso', 'demo.carla@goia.local'),
          ('Painel de acompanhamento dos meus pedidos de acesso', 'demo.diego@goia.local'),
          ('Favoritos compartilhados por equipe', 'demo.ana@goia.local'),
          ('Favoritos compartilhados por equipe', 'demo.carla@goia.local'),
          ('Histórico de mudanças dos prompts oficiais', 'demo.ana@goia.local'),
          ('Histórico de mudanças dos prompts oficiais', 'demo.bruno@goia.local'),
          ('Histórico de mudanças dos prompts oficiais', 'demo.diego@goia.local'),
          ('Atalhos personalizáveis na tela inicial', 'demo.ana@goia.local'),
          ('Atalhos personalizáveis na tela inicial', 'demo.bruno@goia.local')
      ) AS raw(idea_title, user_email)
    )
    INSERT INTO idea_votes (idea_id, user_id, created_at)
    SELECT idea.id, voter.id, NOW() - INTERVAL '3 days'
    FROM vote_input input
    JOIN ideas idea ON idea.title = input.idea_title
    JOIN users voter ON voter.email = input.user_email
    WHERE idea.moderation_status = 'publicada'
    ON CONFLICT DO NOTHING;

    WITH reaction_input AS (
      SELECT *
      FROM (
        VALUES
          ('Isso ajudaria muito os gestores que acompanham pedidos de várias equipes.', 'demo.ana@goia.local', 'thumbs_up'),
          ('Isso ajudaria muito os gestores que acompanham pedidos de várias equipes.', 'demo.diego@goia.local', 'idea'),
          ('Concordo. Também seria útil filtrar por status e por órgão.', 'demo.bruno@goia.local', 'heart'),
          ('Seria bom receber alerta quando o pedido mudar de etapa.', 'demo.ana@goia.local', 'rocket'),
          ('Poder compartilhar listas oficiais por unidade evitaria retrabalho.', 'demo.bruno@goia.local', 'thumbs_up'),
          ('Esse ponto entrou nos critérios de desenho da versão em desenvolvimento.', 'demo.ana@goia.local', 'eyes'),
          ('A rastreabilidade ficou essencial para justificar mudanças em prompts usados por vários órgãos.', 'demo.carla@goia.local', 'heart'),
          ('Apoio a ideia, especialmente se os atalhos respeitarem permissões do usuário.', 'demo.diego@goia.local', 'thumbs_up')
      ) AS raw(comment_content, user_email, reaction)
    )
    INSERT INTO idea_comment_reactions (comment_id, user_id, reaction, created_at)
    SELECT comment.id, reactor.id, input.reaction, NOW() - INTERVAL '2 days'
    FROM reaction_input input
    JOIN idea_comments comment ON comment.content = input.comment_content
    JOIN users reactor ON reactor.email = input.user_email
    ON CONFLICT (comment_id, user_id) DO UPDATE SET
      reaction = EXCLUDED.reaction,
      created_at = EXCLUDED.created_at;
  