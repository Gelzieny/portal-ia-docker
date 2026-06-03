TIPO_PERFIL:
    'AD': Administrador - Perfil com acesso total às funcionalidades da plataforma, incluindo gerenciamento de usuários, configurações avançadas e acesso a relatórios detalhados.
    'GT': Gestor - Perfil com acesso a funcionalidades de gerenciamento de equipes e projetos, incluindo visualização de relatórios e métricas.
    'SV': Servidor - Perfil com acesso limitado às funcionalidades da plataforma, focado em operações diárias e tarefas específicas.
    'CR': Curador - Perfil com acesso para revisar e aprovar conteúdos gerados pelos usuários, como prompts e resultados, garantindo a qualidade e conformidade com as diretrizes da plataforma.
    'CM': Curador Modelos - Perfil com acesso compermissão somente para avaliar modelos.
    'GP': Gestor Produto - Perfil com acesso para gerenciar o catálogo de produtos, incluindo adição, edição e remoção de produtos, bem como visualização de relatórios relacionados a vendas e desempenho dos produtos.


CREATE TABLE CIA_USUARIO (
    ID_USUARIO NUMBER(10) NOT NULL,
    NOME_USUARIO VARCHAR2(200 CHAR) NOT NULL,
    DESC_EMAIL VARCHAR2(200 CHAR) NOT NULL,
    CODG_USUARIO VARCHAR2(32 CHAR),
    TIPO_PERFIL VARCHAR2(2 CHAR) DEFAULT 'SV' NOT NULL,
    NOME_ORGAO VARCHAR2(200 CHAR) DEFAULT '' NOT NULL,
    URL_AVATAR VARCHAR2(500 CHAR),
    INDI_ATIVO VARCHAR2(1 CHAR) DEFAULT 'S' NOT NULL,
    DATA_CRIACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    DATA_ATUALIZACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT PK_CIA_USUARIO PRIMARY KEY (ID_USUARIO),

    CONSTRAINT UK_CIA_USUARIO_EMAIL UNIQUE (DESC_EMAIL),

    CONSTRAINT CK_CIA_USUARIO_ATIVO
        CHECK (
            INDI_ATIVO IN ('S', 'N')
        ),

    CONSTRAINT CK_CIA_USUARIO_PERFIL
        CHECK (
            TIPO_PERFIL IN (
                'AD',
                'GT',
                'SV',
                'CR',
                'CM',
                'GP'
            )
        )
)


CREATE SEQUENCE SEQ_CIA_USUARIO
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE


CREATE OR REPLACE TRIGGER TRG_BI_CIA_USUARIO
BEFORE INSERT ON CIA_USUARIO
FOR EACH ROW
BEGIN
    IF :NEW.ID_USUARIO IS NULL THEN
        SELECT SEQ_CIA_USUARIO.NEXTVAL
          INTO :NEW.ID_USUARIO
          FROM DUAL
    END IF
END



CREATE OR REPLACE TRIGGER TRG_BU_CIA_USUARIO
BEFORE UPDATE ON CIA_USUARIO
FOR EACH ROW
BEGIN
    :NEW.DATA_ATUALIZACAO := CURRENT_TIMESTAMP
END



CREATE INDEX IDX_CIA_USUARIO_EMAIL
    ON CIA_USUARIO (DESC_EMAIL)

CREATE INDEX IDX_CIA_USUARIO_PERFIL
    ON CIA_USUARIO (TIPO_PERFIL)


COMMENT ON TABLE CIA_USUARIO IS
'Tabela responsável pelo cadastro e gerenciamento dos usuários da plataforma.'

COMMENT ON COLUMN CIA_USUARIO.ID_USUARIO IS
'Identificador único do usuário cadastrado.'

COMMENT ON COLUMN CIA_USUARIO.NOME_USUARIO IS
'Nome completo do usuário cadastrado na plataforma.'

COMMENT ON COLUMN CIA_USUARIO.DESC_EMAIL IS
'Endereço de e-mail utilizado pelo usuário para autenticação e comunicação.'

COMMENT ON COLUMN CIA_USUARIO.CODG_USUARIO IS
'Código identificador interno do usuário na plataforma ou organização.'

COMMENT ON COLUMN CIA_USUARIO.TIPO_PERFIL IS
'Perfil de acesso do usuário na plataforma. AD = Administrador, GT = Gestor, SV = Servidor, CR = Curador, CM = Curador de Modelos, GP = Gestor de Produto.'

COMMENT ON COLUMN CIA_USUARIO.NOME_ORGAO IS
'Nome do órgão ou instituição ao qual o usuário está vinculado.'

COMMENT ON COLUMN CIA_USUARIO.URL_AVATAR IS
'Endereço da imagem de avatar associada ao usuário.'

COMMENT ON COLUMN CIA_USUARIO.INDI_ATIVO IS
'Indica se o usuário está ativo para acesso à plataforma. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_USUARIO.DATA_CRIACAO IS
'Data e hora de criação do registro do usuário.'

COMMENT ON COLUMN CIA_USUARIO.DATA_ATUALIZACAO IS
'Data e hora da última atualização do registro do usuário.'

COMMENT ON COLUMN CIA_USUARIO.HASH_SENHA IS
'Hash criptográfico da senha utilizada pelo usuário para autenticação.'
