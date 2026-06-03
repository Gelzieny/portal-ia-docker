-- dados = [
--   {
--     "nome_tipo_recurso": "PDF",
--     "desc_tipo_recurso": "Documento em formato PDF, usado para leitura, download ou impressão",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Documento",
--     "desc_tipo_recurso": "Arquivo de texto editável, como Word ou similar",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Planilha",
--     "desc_tipo_recurso": "Arquivo de planilha eletrônica para dados tabulares e cálculos",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Imagem",
--     "desc_tipo_recurso": "Arquivo de imagem estática, como JPG, PNG ou GIF",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Vídeo",
--     "desc_tipo_recurso": "Conteúdo audiovisual gravado, hospedado ou para download",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Áudio",
--     "desc_tipo_recurso": "Arquivo de som, como gravações, podcasts ou áudios explicativos",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Link Externo",
--     "desc_tipo_recurso": "URL que direciona para um recurso fora do sistema",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Página Web",
--     "desc_tipo_recurso": "Conteúdo acessado diretamente em uma página web",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Apresentação",
--     "desc_tipo_recurso": "Arquivo de slides para apresentação de conteúdo",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Manual",
--     "desc_tipo_recurso": "Documento com instruções detalhadas de uso ou procedimentos",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Tutorial",
--     "desc_tipo_recurso": "Material explicativo passo a passo para aprendizagem",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Relatório",
--     "desc_tipo_recurso": "Documento com análises, resultados ou consolidação de dados",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Formulário",
--     "desc_tipo_recurso": "Documento ou página para preenchimento de informações",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Código Fonte",
--     "desc_tipo_recurso": "Arquivo contendo código de programação",
--     "codg_usuario": "02763696104"
--   },
--   {
--     "nome_tipo_recurso": "Arquivo Compactado",
--     "desc_tipo_recurso": "Pacote de arquivos compactados (ZIP, RAR, etc.)",
--     "codg_usuario": "02763696104"
--   }
-- ]

INSERT ALL
	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('PDF', 'Documento em formato PDF, usado para leitura, download ou impressao')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Documento', 'Arquivo de texto editavel, como Word ou similar')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Planilha', 'Arquivo de planilha eletronica para dados tabulares e calculos')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Imagem', 'Arquivo de imagem estatica, como JPG, PNG ou GIF')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Video', 'Conteudo audiovisual gravado, hospedado ou para download')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Audio', 'Arquivo de som, como gravacoes, podcasts ou audios explicativos')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Link Externo', 'URL que direciona para um recurso fora do sistema')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Pagina Web', 'Conteudo acessado diretamente em uma pagina web')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Apresentacao', 'Arquivo de slides para apresentacao de conteudo')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Manual', 'Documento com instrucoes detalhadas de uso ou procedimentos')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Tutorial', 'Material explicativo passo a passo para aprendizagem')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Relatorio', 'Documento com analises, resultados ou consolidacao de dados')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Formulario', 'Documento ou pagina para preenchimento de informacoes')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Codigo Fonte', 'Arquivo contendo codigo de programacao')

	INTO CIA.CIA_DOCUMENTACAO_TIPO_RECURSO (NOME_TIPO_RECURSO, DESC_TIPO_RECURSO)
	VALUES ('Arquivo Compactado', 'Pacote de arquivos compactados (ZIP, RAR, etc.)')
SELECT 1 FROM DUAL;
