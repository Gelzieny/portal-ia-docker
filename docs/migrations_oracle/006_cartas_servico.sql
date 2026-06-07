CREATE TABLE CIA_CARTA_SERVICO (
    ID_CARTA_SERVICO NUMBER(10) NOT NULL,
    JSON_CONTEUDO CLOB NOT NULL,
    JSON_METADADO CLOB NOT NULL,
    JSON_EMBEDDING CLOB,

    CONSTRAINT PK_CIA_CARTA_SERVICO PRIMARY KEY (ID_CARTA_SERVICO)
)


CREATE SEQUENCE SEQ_CIA_CARTA_SERVICO START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE


CREATE OR REPLACE TRIGGER TRG_BI_CIA_CARTA_SERVICO
BEFORE INSERT ON CIA_CARTA_SERVICO
FOR EACH ROW
BEGIN
    IF :NEW.ID_CARTA_SERVICO IS NULL THEN
        SELECT SEQ_CIA_CARTA_SERVICO.NEXTVAL
          INTO :NEW.ID_CARTA_SERVICO
          FROM DUAL
    END IF
END


CREATE INDEX IDX_CIA_CARTA_SERVICO_EMBED ON CIA_CARTA_SERVICO (ID_CARTA_SERVICO)


COMMENT ON TABLE CIA_CARTA_SERVICO IS
'Tabela responsável pelo armazenamento das cartas de serviço utilizadas pela plataforma, incluindo conteúdo textual, metadados e informações vetoriais para pesquisa semântica.'

COMMENT ON COLUMN CIA_CARTA_SERVICO.ID_CARTA_SERVICO IS
'Identificador único da carta de serviço cadastrada na plataforma.'

COMMENT ON COLUMN CIA_CARTA_SERVICO.JSON_CONTEUDO IS
'Conteúdo textual completo da carta de serviço (tipo do arquivo .md).'

COMMENT ON COLUMN CIA_CARTA_SERVICO.JSON_METADADO IS
'Metadados estruturados relacionados à carta de serviço armazenados em formato JSON.'

COMMENT ON COLUMN CIA_CARTA_SERVICO.JSON_EMBEDDING IS
'Informações vetoriais utilizadas em mecanismos de busca semântica e inteligência artificial (tipo do arquivo .md).'
