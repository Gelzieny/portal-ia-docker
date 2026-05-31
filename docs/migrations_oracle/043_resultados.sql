CREATE TABLE CIA_RESULTADO (
    ID_RESULTADO NUMBER(10) NOT NULL,

    DATA_CRIACAO TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP NOT NULL,

    INFO_RESULTADO CLOB NOT NULL,

    ID_BANCO_QUESTAO NUMBER(10),

    ID_MODELO NUMBER(10),

    TIPO_RESULTADO VARCHAR2(2 CHAR) NOT NULL,

    INDI_ERRO VARCHAR2(1 CHAR) DEFAULT 'N' NOT NULL,

    INFO_ERRO CLOB,

    QTDE_TOTAL_TOKEN NUMBER(10) NOT NULL,

    QTDE_TOKEN_INPUT NUMBER(10) NOT NULL,

    QTDE_TOKEN_OUTPUT NUMBER(10) NOT NULL,

    CONSTRAINT PK_CIA_RESULTADO
        PRIMARY KEY (ID_RESULTADO),

    CONSTRAINT FK_CIA_RESULTADO_BANCO
        FOREIGN KEY (ID_BANCO_QUESTAO)
        REFERENCES CIA_BANCO_QUESTAO (ID_BANCO_QUESTAO)
        ON DELETE SET NULL,

    CONSTRAINT FK_CIA_RESULTADO_MODELO
        FOREIGN KEY (ID_MODELO)
        REFERENCES CIA_MODELO (ID_MODELO)
        ON DELETE SET NULL,

    CONSTRAINT CK_CIA_RESULTADO_ERRO
        CHECK (
            INDI_ERRO IN ('S', 'N')
        ),

    CONSTRAINT CK_CIA_RESULTADO_TIPO
        CHECK (
            TIPO_RESULTADO IN (
                'PC',
                'NM'
            )
        )
)


CREATE SEQUENCE SEQ_CIA_RESULTADO
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE


CREATE OR REPLACE TRIGGER TRG_BI_CIA_RESULTADO
BEFORE INSERT ON CIA_RESULTADO
FOR EACH ROW
BEGIN
    IF :NEW.ID_RESULTADO IS NULL THEN
        SELECT SEQ_CIA_RESULTADO.NEXTVAL
          INTO :NEW.ID_RESULTADO
          FROM DUAL
    END IF
END



CREATE UNIQUE INDEX IDX_CIA_RESULTADO_BANCO_MODELO
    ON CIA_RESULTADO (
        ID_BANCO_QUESTAO,
        ID_MODELO
    )

CREATE INDEX IDX_CIA_RESULTADO_TIPO
    ON CIA_RESULTADO (TIPO_RESULTADO)

CREATE INDEX IDX_CIA_RESULTADO_DATA
    ON CIA_RESULTADO (DATA_CRIACAO)


COMMENT ON TABLE CIA_RESULTADO IS
'Tabela responsável pelo armazenamento dos resultados gerados pelos modelos de inteligência artificial durante execuções e avaliações da plataforma.'

COMMENT ON COLUMN CIA_RESULTADO.ID_RESULTADO IS
'Identificador único do resultado registrado.'

COMMENT ON COLUMN CIA_RESULTADO.DATA_CRIACAO IS
'Data e hora de criação do registro do resultado.'

COMMENT ON COLUMN CIA_RESULTADO.INFO_RESULTADO IS
'Conteúdo estruturado do resultado retornado pelo modelo armazenado em formato JSON.'

COMMENT ON COLUMN CIA_RESULTADO.ID_BANCO_QUESTAO IS
'Identificador da questão vinculada ao resultado gerado.'

COMMENT ON COLUMN CIA_RESULTADO.ID_MODELO IS
'Identificador do modelo responsável pela geração do resultado.'

COMMENT ON COLUMN CIA_RESULTADO.TIPO_RESULTADO IS
'Tipo de resultado retornado pelo processamento. PC = Porcentagem, NM = Número.'

COMMENT ON COLUMN CIA_RESULTADO.INDI_ERRO IS
'Indica se ocorreu erro durante o processamento do resultado. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_RESULTADO.INFO_ERRO IS
'Informações detalhadas sobre o erro ocorrido durante o processamento armazenadas em formato JSON.'

COMMENT ON COLUMN CIA_RESULTADO.QTDE_TOTAL_TOKEN IS
'Quantidade total de tokens processados na execução do resultado.'

COMMENT ON COLUMN CIA_RESULTADO.QTDE_TOKEN_INPUT IS
'Quantidade de tokens de entrada utilizados na execução do modelo.'

COMMENT ON COLUMN CIA_RESULTADO.QTDE_TOKEN_OUTPUT IS
'Quantidade de tokens de saída gerados pelo modelo.'
