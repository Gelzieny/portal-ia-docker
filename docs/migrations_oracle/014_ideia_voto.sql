CREATE TABLE CIA_IDEIA_VOTO (
    ID_IDEIA NUMBER(10) NOT NULL,
    CODG_USUARIO NUMBER(10) NOT NULL,
    DATA_CRIACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT PK_CIA_IDEIA_VOTO
        PRIMARY KEY (
            ID_IDEIA,
            CODG_USUARIO
        ),

    CONSTRAINT FK_CIA_VOTO_IDEA
        FOREIGN KEY (ID_IDEIA)
        REFERENCES CIA_IDEIA (ID_IDEIA)
        ON DELETE CASCADE,

    CONSTRAINT FK_CIA_VOTO_USUARIO
        FOREIGN KEY (CODG_USUARIO)
        REFERENCES USUARIO_SISTEMA (CODG_USUARIO)
        ON DELETE CASCADE
)


CREATE INDEX IDX_CIA_VOTO_USUARIO
    ON CIA_IDEIA_VOTO (
        CODG_USUARIO,
        DATA_CRIACAO
    )


COMMENT ON TABLE CIA_IDEIA_VOTO IS
'Tabela responsável pelo armazenamento dos votos realizados pelos usuários nas ideias cadastradas na plataforma.'

COMMENT ON COLUMN CIA_IDEIA_VOTO.ID_IDEIA IS
'Identificador da ideia que recebeu o voto do usuário.'

COMMENT ON COLUMN CIA_IDEIA_VOTO.CODG_USUARIO IS
'Identificador do usuário responsável pelo voto registrado.'

COMMENT ON COLUMN CIA_IDEIA_VOTO.DATA_CRIACAO IS
'Data e hora de criação do registro do voto.'
