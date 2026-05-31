TIPO_NOTIFICACAO:
    IN: Informação
    AV: Aviso
    SC: Sucesso
    ER: Erro

CREATE TABLE CIA_NOTIFICACAO (
    ID_NOTIFICACAO NUMBER(10) NOT NULL,

    TIPO_NOTIFICACAO VARCHAR2(2 CHAR) DEFAULT 'IN' NOT NULL,

    TITULO_NOTIFICACAO VARCHAR2(300 CHAR) NOT NULL,

    DESC_MENSAGEM CLOB NOT NULL,

    URL_LINK VARCHAR2(500 CHAR),

    INDI_GLOBAL VARCHAR2(1 CHAR) DEFAULT 'S' NOT NULL,

    DATA_CRIACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    DATA_EXPIRACAO TIMESTAMP,

    CONSTRAINT PK_CIA_NOTIFICACAO
        PRIMARY KEY (ID_NOTIFICACAO),

    CONSTRAINT CK_CIA_NOTIFICACAO_TIPO
        CHECK (
            TIPO_NOTIFICACAO IN (
                'IN',
                'AV',
                'SC',
                'ER'
            )
        ),

    CONSTRAINT CK_CIA_NOTIFICACAO_GLOBAL
        CHECK (
            INDI_GLOBAL IN ('S', 'N')
        )
)


CREATE SEQUENCE SEQ_CIA_NOTIFICACAO
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE


CREATE OR REPLACE TRIGGER TRG_BI_CIA_NOTIFICACAO
BEFORE INSERT ON CIA_NOTIFICACAO
FOR EACH ROW
BEGIN
    IF :NEW.ID_NOTIFICACAO IS NULL THEN
        SELECT SEQ_CIA_NOTIFICACAO.NEXTVAL
          INTO :NEW.ID_NOTIFICACAO
          FROM DUAL
    END IF
END

CREATE INDEX IDX_CIA_NOTIFICACAO_GLOBAL
    ON CIA_NOTIFICACAO (
        INDI_GLOBAL,
        DATA_CRIACAO
    )


COMMENT ON TABLE CIA_NOTIFICACAO IS
'Tabela responsável pelo cadastro e gerenciamento das notificações exibidas aos usuários da plataforma.'

COMMENT ON COLUMN CIA_NOTIFICACAO.ID_NOTIFICACAO IS
'Identificador único da notificação cadastrada.'

COMMENT ON COLUMN CIA_NOTIFICACAO.TIPO_NOTIFICACAO IS
'Tipo da notificação exibida ao usuário. IN = Informação, AV = Aviso, SC = Sucesso, ER = Erro.'

COMMENT ON COLUMN CIA_NOTIFICACAO.TITULO_NOTIFICACAO IS
'Título principal da notificação apresentada ao usuário.'

COMMENT ON COLUMN CIA_NOTIFICACAO.DESC_MENSAGEM IS
'Conteúdo textual da mensagem da notificação.'

COMMENT ON COLUMN CIA_NOTIFICACAO.URL_LINK IS
'Endereço complementar relacionado à notificação exibida.'

COMMENT ON COLUMN CIA_NOTIFICACAO.INDI_GLOBAL IS
'Indica se a notificação é global para todos os usuários da plataforma. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_NOTIFICACAO.DATA_CRIACAO IS
'Data e hora de criação do registro da notificação.'

COMMENT ON COLUMN CIA_NOTIFICACAO.DATA_EXPIRACAO IS
'Data e hora limite para exibição da notificação na plataforma.'
