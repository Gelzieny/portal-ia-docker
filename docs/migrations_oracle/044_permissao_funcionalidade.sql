TIPO_PERFIL:
    'AD': Administrador - Perfil com acesso total às funcionalidades da plataforma, incluindo gerenciamento de usuários, configurações avançadas e acesso a relatórios detalhados.
    'GT': Gestor - Perfil com acesso a funcionalidades de gerenciamento de equipes e projetos, incluindo visualização de relatórios e métricas.
    'SV': Servidor - Perfil com acesso limitado às funcionalidades da plataforma, focado em operações diárias e tarefas específicas.
    'CR': Curador - Perfil com acesso para revisar e aprovar conteúdos gerados pelos usuários, como prompts e resultados, garantindo a qualidade e conformidade com as diretrizes da plataforma.
    'CM': Curador Modelos - Perfil com acesso compermissão somente para avaliar modelos.
    'GP': Gestor Produto - Perfil com acesso para gerenciar o catálogo de produtos, incluindo adição, edição e remoção de produtos, bem como visualização de relatórios relacionados a vendas e desempenho dos produtos.

CREATE TABLE CIA_PERMISSAO_FUNCIONALIDADE (
    ID_PERMISSAO_FUNCIONALIDADE  NUMBER(9) NOT NULL,
    TIPO_PERFIL VARCHAR2(2 CHAR) NOT NULL,
    CHAVE_FUNCIONALIDADE VARCHAR2(200 CHAR) NOT NULL,
    INDI_HABILITADO VARCHAR2(1 CHAR) DEFAULT 'N' NOT NULL,
    DATA_CRIACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    DATA_ATUALIZACAO TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT PK_CIA_PERMISSAO_FUNC
        PRIMARY KEY (
            ID_PERMISSAO_FUNCIONALIDADE,
            CHAVE_FUNCIONALIDADE
        ),

    CONSTRAINT FK_CIA_PERM_FUNCIONALIDADE
        FOREIGN KEY (CHAVE_FUNCIONALIDADE)
        REFERENCES CIA_FUNCIONALIDADE (CHAVE_FUNCIONALIDADE)
        ON DELETE CASCADE,

    CONSTRAINT CK_CIA_PERM_FUNC_HABIL
        CHECK (
            INDI_HABILITADO IN ('S', 'N')
        ),

    CONSTRAINT CK_CIA_PERM_FUNC_PERFIL
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


CREATE OR REPLACE TRIGGER TRG_BU_CIA_PERM_FUNC
BEFORE UPDATE ON CIA_PERMISSAO_FUNCIONALIDADE
FOR EACH ROW
BEGIN
    :NEW.DATA_ATUALIZACAO := CURRENT_TIMESTAMP
END



CREATE INDEX IDX_CIA_PERM_FUNCIONALIDADE
    ON CIA_PERMISSAO_FUNCIONALIDADE (
        CHAVE_FUNCIONALIDADE
    )


COMMENT ON TABLE CIA_PERMISSAO_FUNCIONALIDADE IS
'Tabela responsável pelo controle de permissões de funcionalidades associadas aos perfis de usuários da plataforma.'

COMMENT ON COLUMN CIA_PERMISSAO_FUNCIONALIDADE.TIPO_PERFIL IS
'Tipo de perfil do usuário associado à permissão da funcionalidade. AD = Administrador, MG = Gestor, US = Usuário, AN = Analista.'

COMMENT ON COLUMN CIA_PERMISSAO_FUNCIONALIDADE.CHAVE_FUNCIONALIDADE IS
'Chave identificadora da funcionalidade vinculada à permissão do perfil.'

COMMENT ON COLUMN CIA_PERMISSAO_FUNCIONALIDADE.INDI_HABILITADO IS
'Indica se a funcionalidade está habilitada para o perfil informado. S = Sim, N = Não.'

COMMENT ON COLUMN CIA_PERMISSAO_FUNCIONALIDADE.DATA_CRIACAO IS
'Data e hora de criação do registro da permissão da funcionalidade.'

COMMENT ON COLUMN CIA_PERMISSAO_FUNCIONALIDADE.DATA_ATUALIZACAO IS
'Data e hora da última atualização do registro da permissão da funcionalidade.'
