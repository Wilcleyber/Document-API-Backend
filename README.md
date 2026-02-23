Document-API
Uma API de alta performance para gerenciamento hierárquico de documentos, desenvolvida com foco em concorrência assíncrona, segurança rigorosa e integridade de dados.

🔗 Documentação Interativa (Swagger) https://document-api-backend.onrender.com/docs

🏛️ Arquitetura e Decisões de Engenharia
Este projeto foi estruturado para simular um ambiente de produção real, priorizando a escalabilidade e a separação de responsabilidades.

Processamento Assíncrono: Utilização integral de FastAPI e asyncpg para otimizar operações de I/O, permitindo que a API gerencie múltiplas requisições simultâneas sem bloqueio de thread.

Hierarquia via CTEs Recursivas: Implementação de consultas SQL avançadas para manipulação de árvores de diretórios diretamente no PostgreSQL, minimizando a carga de processamento na aplicação.

Segurança de Grão Fino (RBAC): Sistema de autorização baseado em papéis (Admin/User), protegendo recursos em nível de endpoint e de dados.

Infraestrutura Cloud: Deploy automatizado via Render integrado a um banco de dados PostgreSQL Gerenciado (Neon), utilizando SSL e pooling de conexões para resiliência.

🛠️ Stack Tecnológica

Camada            Tecnologia
FastAPI           FastAPI (Python 3.14+)
Banco de Dados    PostgreSQL (Neon)
Driver DB         asyncpg (Interface assíncrona)
Segurança         JWT (PyJWT) + Bcrypt
Ambiente          Render (Web Service)
Testes            Pytest + HTTPX

🚀 Funcionalidades Principais
Gestão de Fluxo de Usuário: Registro, autenticação e renovação de acesso via Tokens JWT.

Navegação Dinâmica: Recuperação de árvores de arquivos completas com suporte a caminhos (breadcrumbs).

Persistência de Conteúdo: Edição e leitura de arquivos de texto com controle de metadados.

Logs Estruturados: Monitoramento de requisições e erros via logs em formato JSON, prontos para ferramentas de observabilidade.

Garantia de Qualidade: Cobertura de testes de integração que validam desde a conexão com o banco até as regras de negócio de permissão.

📂 Estrutura
src/
├── auth/           # Protocolos de segurança e tokens
├── authorization/  # Lógica de controle de acesso (RBAC)
├── db/             # Camada de persistência e migrações automáticas
├── nodes/          # Gestão de pastas e arquivos
├── navigation/     # Algoritmos de busca e árvore hierárquica
└── core/           # Configurações globais, logs e middlewares

🚀 Como Rodar o Projeto
1. Clone e Ambiente:
git clone https://github.com/Wilcleyber/Document-API-Backend.git
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

2. Configuração: Crie um .env com sua DATABASE_URL e SECRET_KEY.

3. Execução:
uvicorn src.main:app --reload

4. Testes:
pytest -v


