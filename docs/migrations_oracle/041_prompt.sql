STAT_PUBLICACAO:
    'RS': Rascunho,
    'PV': Privado,
    'AG': Aguardando Aprovação,
    'PB': Publicado,
    'ER': Em Revisão,
    'AR': Arquivado

NIVEL_DIFICULDADE:
    'IN': Iniciante,
    'IT': Intermediário,
    'AV': Avançado

CREATE TABLE CIA_PROMPT (
    ID_PROMPT NUMBER(10) NOT NULL,
    TITULO_PROMPT VARCHAR2(300 CHAR) NOT NULL,
    DESC_PROMPT CLOB DEFAULT '' NOT NULL,
    DESC_CONTEUDO CLOB NOT NULL,
    ID_PROMPT_CATEGORIA NUMBER(10),
    ID_MODELO NUMBER(10),
    DESC_ETIQUETA__PROMPT CLOB DEFAULT '[]' NOT NULL,
    NIVEL_DIFICULDADE VARCHAR2(2 CHAR) DEFAULT 'IN' NOT NULL,
    QTDE_USO NUMBER(10) DEFAULT 0 NOT NULL,
    INFO_VARIAVEL CLOB DEFAULT '[]' NOT NULL,
    CODG_USUARIO_AUTOR NUMBER(10),
    INDI_PUBLICO VARCHAR2(1 CHAR) DEFAULT 'S' NOT NULL,
    INDI_ATIVO VARCHAR2(1 CHAR) DEFAULT 'S' NOT NULL,
    DATA_CRIACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    DATA_ATUALIZACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    VALR_MEDIA_AVALIACAO NUMBER(3,2) DEFAULT 0 NOT NULL,
    QTDE_AVALIACAO NUMBER(10) DEFAULT 0 NOT NULL,
    STAT_PUBLICACAO VARCHAR2(2 CHAR) DEFAULT 'PV' NOT NULL,
    TIPO_ORIGEM VARCHAR2(2 CHAR) DEFAULT 'OF' NOT NULL,
    DATA_SUBMISSAO TIMESTAMP,
    CODG_USUARIO_REVISAO NUMBER(10),
    DATA_REVISAO TIMESTAMP,
    DESC_OBSERVACAO_REVISAO CLOB,
    NOME_AUTOR_ORIGINAL VARCHAR2(200 CHAR),
    QTDE_DENUNCIA NUMBER(10) DEFAULT 0 NOT NULL,
    NUMR_VERSAO NUMBER(10) DEFAULT 1 NOT NULL,
    DESC_OBSERVACAO_SUBMISSAO CLOB,

    CONSTRAINT PK_CIA_PROMPT PRIMARY KEY (ID_PROMPT),

    CONSTRAINT FK_CIA_PROMPT_AUTOR
        FOREIGN KEY (CODG_USUARIO_AUTOR)
        REFERENCES USUARIO_SISTEMA (CODG_USUARIO)
        ON DELETE SET NULL,

    CONSTRAINT FK_CIA_PROMPT_CATEGORIA
        FOREIGN KEY (ID_PROMPT_CATEGORIA)
        REFERENCES CIA_PROMPT_CATEGORIA (ID_PROMPT_CATEGORIA)
        ON DELETE SET NULL,

    CONSTRAINT FK_CIA_PROMPT_MODELO
        FOREIGN KEY (ID_MODELO)
        REFERENCES CIA_MODELO (ID_MODELO)
        ON DELETE SET NULL,

    CONSTRAINT FK_CIA_PROMPT_REVISAO
        FOREIGN KEY (CODG_USUARIO_REVISAO)
        REFERENCES USUARIO_SISTEMA (CODG_USUARIO)
        ON DELETE SET NULL,

    CONSTRAINT CK_CIA_PROMPT_DIFICULDADE
        CHECK (
            NIVEL_DIFICULDADE IN (
                'IN',
                'IT',
                'AV'
            )
        ),

    CONSTRAINT CK_CIA_PROMPT_PUBLICO
        CHECK (
            INDI_PUBLICO IN ('S', 'N')
        ),

    CONSTRAINT CK_CIA_PROMPT_ATIVO
        CHECK (
            INDI_ATIVO IN ('S', 'N')
        ),

    CONSTRAINT CK_CIA_PROMPT_PUBLICACAO
        CHECK (
            STAT_PUBLICACAO IN (
                'RS',
                'PV',
                'AG',
                'PB',
                'ER',
                'AR'
            )
        ),

    CONSTRAINT CK_CIA_PROMPT_ORIGEM
        CHECK (
            TIPO_ORIGEM IN (
                'OF',
                'US'
            )
        )
)


CREATE SEQUENCE SEQ_CIA_PROMPT
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE


CREATE OR REPLACE TRIGGER TRG_BI_CIA_PROMPT
BEFORE INSERT ON CIA_PROMPT
FOR EACH ROW
BEGIN
    IF :NEW.ID_PROMPT IS NULL THEN
        SELECT SEQ_CIA_PROMPT.NEXTVAL
          INTO :NEW.ID_PROMPT
          FROM DUAL
    END IF
END


CREATE OR REPLACE TRIGGER TRG_BU_CIA_PROMPT
BEFORE UPDATE ON CIA_PROMPT
FOR EACH ROW
BEGIN
    :NEW.DATA_ATUALIZACAO := CURRENT_TIMESTAMP
END


CREATE INDEX IDX_CIA_PROMPT_AUTOR_ORIGEM
    ON CIA_PROMPT (
        CODG_USUARIO_AUTOR,
        TIPO_ORIGEM
    )

CREATE INDEX IDX_CIA_PROMPT_AGUARDANDO
    ON CIA_PROMPT (
        STAT_PUBLICACAO,
        DATA_SUBMISSAO
    )

CREATE INDEX IDX_CIA_PROMPT_CATEGORIA
    ON CIA_PROMPT (ID_PROMPT_CATEGORIA)

CREATE INDEX IDX_CIA_PROMPT_DIFICULDADE
    ON CIA_PROMPT (NIVEL_DIFICULDADE)

CREATE INDEX IDX_CIA_PROMPT_REVISAO
    ON CIA_PROMPT (
        STAT_PUBLICACAO,
        QTDE_DENUNCIA
    )

CREATE INDEX IDX_CIA_PROMPT_PUBLICACAO ON CIA_PROMPT (STAT_PUBLICACAO)

CREATE INDEX IDX_CIA_PROMPT_ORIGEM ON CIA_PROMPT (TIPO_ORIGEM)


COMMENT ON TABLE CIA_PROMPT IS
'Tabela responsável pelo cadastro e gerenciamento dos prompts disponibilizados na plataforma.'

COMMENT ON COLUMN CIA_PROMPT.ID_PROMPT IS
'Identificador único do prompt cadastrado.'

COMMENT ON COLUMN CIA_PROMPT.TITULO_PROMPT IS
'Título principal do prompt disponibilizado na plataforma.'

COMMENT ON COLUMN CIA_PROMPT.DESC_PROMPT IS
'Descrição resumida do prompt cadastrado.'

COMMENT ON COLUMN CIA_PROMPT.DESC_CONTEUDO IS
'Conteúdo completo do prompt utilizado pelos usuários.'

COMMENT ON COLUMN CIA_PROMPT.ID_PROMPT_CATEGORIA IS
'Identificador da categoria associada ao prompt.'

COMMENT ON COLUMN CIA_PROMPT.ID_MODELO IS
'Identificador do modelo de inteligência artificial recomendado para utilização do prompt.'

COMMENT ON COLUMN CIA_PROMPT.DESC_ETIQUETA__PROMPT IS
'Lista de etiquetas utilizadas para categorização e pesquisa do prompt armazenada em formato JSON.'

COMMENT ON COLUMN CIA_PROMPT.NIVEL_DIFICULDADE IS
'Nível de dificuldade do prompt. IN = Iniciante, IT = Intermediário, AV = Avançado.'

COMMENT ON COLUMN CIA_PROMPT.QTDE_USO IS
'Quantidade total de utilizações registradas para o prompt.'

COMMENT ON COLUMN CIA_PROMPT.INFO_VARIAVEL IS
'Lista estruturada das variáveis utilizadas no prompt armazenada em formato JSON.'

COMMENT ON COLUMN CIA_PROMPT.CODG_USUARIO_AUTOR IS
'Identificador do usuário autor do prompt cadastrado.'

COMMENT ON COLUMN CIA_PROMPT.INDI_PUBLICO IS
'Indica se o prompt é público para visualização dos usuários. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_PROMPT.INDI_ATIVO IS
'Indica se o prompt está ativo para utilização na plataforma. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_PROMPT.DATA_CRIACAO IS
'Data e hora de criação do registro do prompt.'

COMMENT ON COLUMN CIA_PROMPT.DATA_ATUALIZACAO IS
'Data e hora da última atualização do registro do prompt.'

COMMENT ON COLUMN CIA_PROMPT.VALR_MEDIA_AVALIACAO IS
'Valor médio das avaliações recebidas pelo prompt.'

COMMENT ON COLUMN CIA_PROMPT.QTDE_AVALIACAO IS
'Quantidade total de avaliações registradas para o prompt.'

COMMENT ON COLUMN CIA_PROMPT.STAT_PUBLICACAO IS
'Situação de publicação do prompt. RS = Rascunho, PV = Privado, AG = Aguardando, PB = Público, ER = Em Revisão, AR = Arquivado.'

COMMENT ON COLUMN CIA_PROMPT.TIPO_ORIGEM IS
'Origem do prompt cadastrado. OF = Oficial, US = Usuário.'

COMMENT ON COLUMN CIA_PROMPT.DATA_SUBMISSAO IS
'Data e hora da submissão do prompt para publicação ou revisão.'

COMMENT ON COLUMN CIA_PROMPT.CODG_USUARIO_REVISAO IS
'Identificador do usuário responsável pela revisão do prompt.'

COMMENT ON COLUMN CIA_PROMPT.DATA_REVISAO IS
'Data e hora da revisão realizada no prompt.'

COMMENT ON COLUMN CIA_PROMPT.DESC_OBSERVACAO_REVISAO IS
'Observações registradas durante o processo de revisão do prompt.'

COMMENT ON COLUMN CIA_PROMPT.NOME_AUTOR_ORIGINAL IS
'Nome do autor original do prompt, quando aplicável.'

COMMENT ON COLUMN CIA_PROMPT.QTDE_DENUNCIA IS
'Quantidade total de denúncias registradas para o prompt.'

COMMENT ON COLUMN CIA_PROMPT.NUMR_VERSAO IS
'Número atual da versão do prompt.'

COMMENT ON COLUMN CIA_PROMPT.DESC_OBSERVACAO_SUBMISSAO IS
'Observações informadas durante a submissão do prompt.'
