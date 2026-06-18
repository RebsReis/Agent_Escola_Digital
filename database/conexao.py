#Agora que as classes existem, precisamos do mecanismo que abre as conexões com o PostgreSQL e gerencia as 
# sessões que os agentes usarão.
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Carrega as variáveis do .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("A variável DATABASE_URL não foi configurada no arquivo .env!")

# Cria o motor de conexão
engine = create_engine(DATABASE_URL, echo=False) # Mude para True se quiser ver os SQLs no terminal

# Fábrica de Sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Função utilitária para obter uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

'''Por que estruturamos assim? > Quando o LangGraph chamar uma Tool (ferramenta de consulta), a ferramenta usará 
o SessionLocal() para ler ou atualizar os dados de forma isolada e segura, fechando a conexão logo em seguida.

Nossas fundações de dados estão prontas! O próximo passo natural é dar "mãos" aos agentes construindo as Tools 
(ferramentas). Como o Agente Secretário precisa lidar com o gerenciamento dos alunos, faz sentido começarmos 
pelas ferramentas administrativas.

Para o nosso próximo passo, você prefere criar as ferramentas do Aluno e Matrícula (Criar Aluno, Matricular 
em Matéria, Consultar Matrículas) ou prefere começar escrevendo as ferramentas de Tópicos e Progresso?'''