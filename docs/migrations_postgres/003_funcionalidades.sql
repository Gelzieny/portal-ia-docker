CREATE TABLE CIA_FUNCIONALIDADE (
    CHAVE_FUNCIONALIDADE VARCHAR(200) NOT NULL,
    NOME_FUNCIONALIDADE VARCHAR(200) NOT NULL,
    DESC_FUNCIONALIDADE TEXT,
    AREA_FUNCIONALIDADE VARCHAR(200) NOT NULL,
    NOME_MENU VARCHAR(200),
    CAMINHO_MENU VARCHAR(500),
    NUMR_ORDEM INTEGER DEFAULT 0 NOT NULL,
    INDI_ATIVO VARCHAR(1) DEFAULT 'S' NOT NULL,
    INDI_SISTEMA VARCHAR(1) DEFAULT 'S' NOT NULL,
    DATA_CRIACAO TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    DATA_ATUALIZACAO TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT PK_CIA_FUNCIONALIDADE PRIMARY KEY (CHAVE_FUNCIONALIDADE),

    CONSTRAINT CK_CIA_FUNCIONALIDADE_ATIVO CHECK (INDI_ATIVO IN ('S', 'N')),

    CONSTRAINT CK_CIA_FUNCIONALIDADE_SISTEMA  CHECK (INDI_SISTEMA IN ('S', 'N'))
)
;

CREATE INDEX IDX_CIA_FUNC_AREA_ORDEM ON CIA_FUNCIONALIDADE (AREA_FUNCIONALIDADE, NUMR_ORDEM);
;

COMMENT ON TABLE CIA_FUNCIONALIDADE IS
'Tabela responsável pelo cadastro das funcionalidades disponíveis na aplicação e seus respectivos agrupamentos de navegação.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.CHAVE_FUNCIONALIDADE IS
'Identificador único da funcionalidade utilizado internamente pelo sistema.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.NOME_FUNCIONALIDADE IS
'Nome de exibição da funcionalidade na aplicação.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.DESC_FUNCIONALIDADE IS
'Descrição detalhada da funcionalidade disponível na aplicação.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.AREA_FUNCIONALIDADE IS
'Área funcional da aplicação à qual a funcionalidade pertence.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.NOME_MENU IS
'Nome exibido no menu de navegação da aplicação.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.CAMINHO_MENU IS
'Caminho hierárquico utilizado na navegação do menu da aplicação.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.NUMR_ORDEM IS
'Ordem de exibição da funcionalidade nos menus e interfaces da aplicação.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.INDI_ATIVO IS
'Indica se a funcionalidade está ativa para utilização. S = Sim, N = Não.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.INDI_SISTEMA IS
'Indica se a funcionalidade é nativa do sistema. S = Sim, N = Não.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.DATA_CRIACAO IS
'Data e hora de criação do registro da funcionalidade.';

COMMENT ON COLUMN CIA_FUNCIONALIDADE.DATA_ATUALIZACAO IS
'Data e hora da última atualização do registro da funcionalidade.';

CREATE OR REPLACE FUNCTION trg_bu_cia_funcionalidade_fn()
RETURNS TRIGGER AS $$
BEGIN
  NEW.data_atualizacao = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_bu_cia_funcionalidade
  BEFORE UPDATE ON cia_funcionalidade
  FOR EACH ROW EXECUTE FUNCTION trg_bu_cia_funcionalidade_fn();
