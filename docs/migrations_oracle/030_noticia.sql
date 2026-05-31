CATEGORIA_NOTICIA:
 AT: Atualização,
 MN: Manutenção,
 AV: Aviso,
 NR: Novo Recurso,
 SG: Segurança

CREATE TABLE CIA_NOTICIA (
    ID_NOTICIA NUMBER(10) NOT NULL,

    CATEGORIA_NOTICIA VARCHAR2(2 CHAR) DEFAULT 'AV' NOT NULL,

    TITULO_NOTICIA VARCHAR2(300 CHAR) NOT NULL,

    DESC_RESUMO CLOB NOT NULL,

    DESC_CONTEUDO CLOB DEFAULT '' NOT NULL,

    URL_LINK VARCHAR2(500 CHAR),

    QTDE_TEMPO_LEITURA NUMBER(10) DEFAULT 3 NOT NULL,

    INDI_PUBLICADO VARCHAR2(1 CHAR) DEFAULT 'N' NOT NULL,

    DATA_PUBLICACAO TIMESTAMP,

    DATA_CRIACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    DATA_ATUALIZACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT PK_CIA_NOTICIA
        PRIMARY KEY (ID_NOTICIA),

    CONSTRAINT CK_CIA_NOTICIA_CATEGORIA
        CHECK (
            CATEGORIA_NOTICIA IN (
                'AT',
                'MN',
                'AV',
                'NR',
                'SG'
            )
        ),

    CONSTRAINT CK_CIA_NOTICIA_PUBLICADO
        CHECK (
            INDI_PUBLICADO IN ('S', 'N')
        )
)


CREATE SEQUENCE SEQ_CIA_NOTICIA
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE


CREATE OR REPLACE TRIGGER TRG_BI_CIA_NOTICIA
BEFORE INSERT ON CIA_NOTICIA
FOR EACH ROW
BEGIN
    IF :NEW.ID_NOTICIA IS NULL THEN
        SELECT SEQ_CIA_NOTICIA.NEXTVAL
          INTO :NEW.ID_NOTICIA
          FROM DUAL
    END IF
END

CREATE OR REPLACE TRIGGER TRG_BU_CIA_NOTICIA
BEFORE UPDATE ON CIA_NOTICIA
FOR EACH ROW
BEGIN
    :NEW.DATA_ATUALIZACAO := CURRENT_TIMESTAMP
END


CREATE INDEX IDX_CIA_NOTICIA_PUBLICADA
    ON CIA_NOTICIA (
        INDI_PUBLICADO,
        DATA_PUBLICACAO
    )


COMMENT ON TABLE CIA_NOTICIA IS
'Tabela responsável pelo cadastro e publicação de notícias, comunicados e atualizações da plataforma.'

COMMENT ON COLUMN CIA_NOTICIA.ID_NOTICIA IS
'Identificador único da notícia cadastrada.'

COMMENT ON COLUMN CIA_NOTICIA.CATEGORIA_NOTICIA IS
'Categoria da notícia publicada. AT = Atualização, MN = Manutenção, AV = Aviso, NR = Novo Recurso, SG = Segurança.'

COMMENT ON COLUMN CIA_NOTICIA.TITULO_NOTICIA IS
'Título principal da notícia publicada na plataforma.'

COMMENT ON COLUMN CIA_NOTICIA.DESC_RESUMO IS
'Resumo descritivo da notícia utilizada para visualização rápida.'

COMMENT ON COLUMN CIA_NOTICIA.DESC_CONTEUDO IS
'Conteúdo completo da notícia publicada.'

COMMENT ON COLUMN CIA_NOTICIA.URL_LINK IS
'Endereço complementar relacionado à notícia ou publicação.'

COMMENT ON COLUMN CIA_NOTICIA.QTDE_TEMPO_LEITURA IS
'Tempo estimado de leitura da notícia em minutos.'

COMMENT ON COLUMN CIA_NOTICIA.INDI_PUBLICADO IS
'Indica se a notícia está publicada para visualização. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_NOTICIA.DATA_PUBLICACAO IS
'Data e hora da publicação oficial da notícia.'

COMMENT ON COLUMN CIA_NOTICIA.DATA_CRIACAO IS
'Data e hora de criação do registro da notícia.'

COMMENT ON COLUMN CIA_NOTICIA.DATA_ATUALIZACAO IS
'Data e hora da última atualização do registro da notícia.'
