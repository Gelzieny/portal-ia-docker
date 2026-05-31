CREATE TABLE CIA_VOTO_IDEIA (
    ID_IDEIA INTEGER NOT NULL,
    ID_USUARIO INTEGER NOT NULL,
    DATA_CRIACAO TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT PK_CIA_VOTO_IDEIA
        PRIMARY KEY (
            ID_IDEIA,
            ID_USUARIO
        ),

    CONSTRAINT FK_CIA_VOTO_IDEA
        FOREIGN KEY (ID_IDEIA)
        REFERENCES CIA_IDEIA (ID_IDEIA)
        ON DELETE CASCADE,

    CONSTRAINT FK_CIA_VOTO_USUARIO
        FOREIGN KEY (ID_USUARIO)
        REFERENCES CIA_USUARIO (ID_USUARIO)
        ON DELETE CASCADE
)
;

CREATE INDEX IDX_CIA_VOTO_USUARIO
    ON CIA_VOTO_IDEIA (
        ID_USUARIO,
        DATA_CRIACAO
    )
;

COMMENT ON TABLE CIA_VOTO_IDEIA IS
'Tabela responsável pelo armazenamento dos votos realizados pelos usuários nas ideias cadastradas na plataforma.';

COMMENT ON COLUMN CIA_VOTO_IDEIA.ID_IDEIA IS
'Identificador da ideia que recebeu o voto do usuário.';

COMMENT ON COLUMN CIA_VOTO_IDEIA.ID_USUARIO IS
'Identificador do usuário responsável pelo voto registrado.';

COMMENT ON COLUMN CIA_VOTO_IDEIA.DATA_CRIACAO IS
'Data e hora de criação do registro do voto.';
