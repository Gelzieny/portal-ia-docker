STAT_MODELO:
    DP = Disponível,
    BT = Beta,
    MN = Manutenção

CREATE TABLE CIA_MODELO (
    ID_MODELO NUMBER(10) NOT NULL,

    NOME_MODELO VARCHAR2(200 CHAR) NOT NULL,
    SLUG_MODELO VARCHAR2(200 CHAR) NOT NULL,

    DESC_MODELO CLOB DEFAULT '' NOT NULL,

    INFO_CAPACIDADE CLOB DEFAULT '[]' NOT NULL,

    STAT_MODELO VARCHAR2(2 CHAR) DEFAULT 'DP' NOT NULL,

    QTDE_JANELA_CONTEXTO NUMBER(10),

    INFO_LIMITE_USO VARCHAR2(200 CHAR),

    TAG CLOB DEFAULT '[]' NOT NULL,

    INDI_NOVO VARCHAR2(1 CHAR) DEFAULT 'N' NOT NULL,
    INDI_DESTAQUE VARCHAR2(1 CHAR) DEFAULT 'N' NOT NULL,
    INDI_ATIVO VARCHAR2(1 CHAR) DEFAULT 'S' NOT NULL,

    NUMR_ORDEM NUMBER(10) DEFAULT 0 NOT NULL,

    DATA_CRIACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    DATA_ATUALIZACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    INDI_APROVACAO_ACESSO VARCHAR2(1 CHAR) DEFAULT 'N' NOT NULL,

    DESC_RESUMO_ACESSO CLOB DEFAULT '' NOT NULL,
    DESC_DOCUMENTACAO_ACESSO CLOB DEFAULT '' NOT NULL,

    URL_ENDPOINT_PADRAO VARCHAR2(500 CHAR),

    TIPO_AUTENTICACAO_PADRAO VARCHAR2(50 CHAR) DEFAULT 'api_key' NOT NULL,

    ID_PROVEDOR NUMBER(10),

    ID_CATEGORIA_MODELO NUMBER(10),

    CONSTRAINT PK_CIA_MODELO
        PRIMARY KEY (ID_MODELO),

    CONSTRAINT UK_CIA_MODELO_SLUG
        UNIQUE (SLUG_MODELO),

    CONSTRAINT FK_CIA_MODELO_PROVEDOR
        FOREIGN KEY (ID_PROVEDOR)
        REFERENCES CIA_PROVEDOR (ID_PROVEDOR)
        ON DELETE SET NULL,

    CONSTRAINT FK_CIA_MODELO_CATEGORIA
        FOREIGN KEY (ID_CATEGORIA_MODELO)
        REFERENCES CIA_CATEGORIA_MODELO (ID_CATEGORIA_MODELO)
        ON DELETE SET NULL,

    CONSTRAINT CK_CIA_MODELO_STATUS
        CHECK (
            STAT_MODELO IN (
                'DP',
                'BT',
                'MN'
            )
        ),

    CONSTRAINT CK_CIA_MODELO_NOVO
        CHECK (
            INDI_NOVO IN ('S', 'N')
        ),

    CONSTRAINT CK_CIA_MODELO_DESTAQUE
        CHECK (
            INDI_DESTAQUE IN ('S', 'N')
        ),

    CONSTRAINT CK_CIA_MODELO_ATIVO
        CHECK (
            INDI_ATIVO IN ('S', 'N')
        ),

    CONSTRAINT CK_CIA_MODELO_APROVACAO
        CHECK (
            INDI_APROVACAO_ACESSO IN ('S', 'N')
        )
)


CREATE SEQUENCE SEQ_CIA_MODELO START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE


CREATE OR REPLACE TRIGGER TRG_BI_CIA_MODELO
BEFORE INSERT ON CIA_MODELO
FOR EACH ROW
BEGIN
    IF :NEW.ID_MODELO IS NULL THEN
        SELECT SEQ_CIA_MODELO.NEXTVAL
          INTO :NEW.ID_MODELO
          FROM DUAL
    END IF
END

CREATE OR REPLACE TRIGGER TRG_BU_CIA_MODELO
BEFORE UPDATE ON CIA_MODELO
FOR EACH ROW
BEGIN
    :NEW.DATA_ATUALIZACAO := CURRENT_TIMESTAMP
END

CREATE INDEX IDX_CIA_MODELO_SLUG ON CIA_MODELO (SLUG_MODELO)

CREATE INDEX IDX_CIA_MODELO_STATUS ON CIA_MODELO (STAT_MODELO)

CREATE INDEX IDX_CIA_MODELO_CATEGORIA ON CIA_MODELO (ID_CATEGORIA_MODELO)


COMMENT ON TABLE CIA_MODELO IS
'Tabela responsável pelo cadastro e gerenciamento dos modelos de inteligência artificial disponíveis na plataforma.'

COMMENT ON COLUMN CIA_MODELO.ID_MODELO IS
'Identificador único do modelo de inteligência artificial.'

COMMENT ON COLUMN CIA_MODELO.NOME_MODELO IS
'Nome de exibição do modelo de inteligência artificial.'

COMMENT ON COLUMN CIA_MODELO.SLUG_MODELO IS
'Identificador textual único utilizado em URLs e integrações do modelo.'

COMMENT ON COLUMN CIA_MODELO.DESC_MODELO IS
'Descrição detalhada do modelo de inteligência artificial.'

COMMENT ON COLUMN CIA_MODELO.INFO_CAPACIDADE IS
'Lista de capacidades e funcionalidades suportadas pelo modelo armazenada em formato JSON.'

COMMENT ON COLUMN CIA_MODELO.STAT_MODELO IS
'Situação atual do modelo. DP = Disponível, BT = Beta, MN = Manutenção.'

COMMENT ON COLUMN CIA_MODELO.QTDE_JANELA_CONTEXTO IS
'Quantidade máxima de tokens suportados na janela de contexto do modelo.'

COMMENT ON COLUMN CIA_MODELO.INFO_LIMITE_USO IS
'Informações sobre limites de utilização do modelo.'

COMMENT ON COLUMN CIA_MODELO.TAG IS
'Lista de etiquetas utilizadas para categorização e pesquisa do modelo armazenada em formato JSON.'

COMMENT ON COLUMN CIA_MODELO.INDI_NOVO IS
'Indica se o modelo é considerado novo na plataforma. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_MODELO.INDI_DESTAQUE IS
'Indica se o modelo deve ser exibido em destaque. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_MODELO.INDI_ATIVO IS
'Indica se o modelo está ativo para utilização. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_MODELO.NUMR_ORDEM IS
'Ordem de exibição do modelo nas interfaces da plataforma.'

COMMENT ON COLUMN CIA_MODELO.DATA_CRIACAO IS
'Data e hora de criação do registro do modelo.'

COMMENT ON COLUMN CIA_MODELO.DATA_ATUALIZACAO IS
'Data e hora da última atualização do registro do modelo.'

COMMENT ON COLUMN CIA_MODELO.INDI_APROVACAO_ACESSO IS
'Indica se o modelo exige aprovação prévia para utilização. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_MODELO.DESC_RESUMO_ACESSO IS
'Resumo das regras e condições de acesso ao modelo.'

COMMENT ON COLUMN CIA_MODELO.DESC_DOCUMENTACAO_ACESSO IS
'Documentação complementar sobre acesso e utilização do modelo.'

COMMENT ON COLUMN CIA_MODELO.URL_ENDPOINT_PADRAO IS
'Endereço padrão de integração utilizado pelo modelo.'

COMMENT ON COLUMN CIA_MODELO.TIPO_AUTENTICACAO_PADRAO IS
'Tipo de autenticação padrão utilizado para acesso ao modelo.'

COMMENT ON COLUMN CIA_MODELO.ID_PROVEDOR IS
'Identificador do provedor responsável pelo modelo de inteligência artificial.'

COMMENT ON COLUMN CIA_MODELO.ID_CATEGORIA_MODELO IS
'Identificador da categoria funcional do modelo de inteligência artificial.'
