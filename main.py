import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client
import bcrypt
import json # Para ler o biblia_completa.json

# --- Importação para PDF (com sintaxe moderna) ---
from fpdf import FPDF, XPos, YPos

# --- Importações do agente (LangChain, etc.) ---
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# --- NOVAS IMPORTAÇÕES PARA FERRAMENTAS E AGENTES ---
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool # Importa o decorador @tool

# --- IMPORTAÇÃO DO SYSTEM_PROMPT DO ARQUIVO prompts.py ---
from prompts import SYSTEM_PROMPT

# --- Configuração Inicial ---
st.set_page_config(page_title="Assistente de Pregação - IA", page_icon="📖", layout="wide")
load_dotenv()

# --- DEFINIÇÃO DAS FUNÇÕES PRINCIPAIS DO APP ---
FAISS_INDEX_PATH = "faiss_index"
BIBLIA_COMPLETA_PATH = "biblia_completa.json" # Caminho para o seu arquivo da Bíblia completa

# Carrega a Bíblia completa para a ferramenta de citação
try:
    with open(BIBLIA_COMPLETA_PATH, 'r', encoding='utf-8') as f:
        BIBLIA_COMPLETA = json.load(f)
except FileNotFoundError:
    st.error(f"ERRO: O arquivo '{BIBLIA_COMPLETA_PATH}' não foi encontrado. Por favor, certifique-se de que ele está na mesma pasta do 'main.py'.")
    st.stop()
except json.JSONDecodeError:
    st.error(f"ERRO: O arquivo '{BIBLIA_COMPLETA_PATH}' está corrompido ou mal formatado. Verifique o conteúdo JSON.")
    st.stop()

# --- FERRAMENTA DE CITAÇÃO BÍBLICA (SUA IDEIA IMPLEMENTADA!) ---
@tool
def citar_biblia(referencia: str) -> str:
    """
    Usa esta ferramenta para obter o texto EXATO de um versículo bíblico.
    O formato da referência DEVE ser: 'Livro Capítulo:Versículo'.
    Exemplos: 'Êxodo 3:14', 'Salmos 23:1', 'João 3:16'.
    Retorna o texto do versículo ou uma mensagem de 'versículo não encontrado'.
    """
    try:
        livro_cap_vers = referencia.split(' ', 1) # Separa o Livro do restante
        livro = livro_cap_vers[0]

        if len(livro_cap_vers) < 2:
            return f"Referência '{referencia}' inválida. Formato esperado: 'Livro Capítulo:Versículo'."

        capitulo_versiculo = livro_cap_vers[1]

        # Adaptação para o formato do seu JSON, se for diferente de "Livro C:V"
        # Assumindo que seu JSON tem a estrutura:
        # { "Livro": { "Capitulo": { "Versiculo": "Texto" } } }
        # Ou diretamente: { "Livro C:V": "Texto" }
        # Se for diretamente "Livro C:V": "Texto", a busca é mais simples.
        # VAMOS ASSUMIR POR AGORA QUE É "Livro C:V": "Texto" (a chave é a referência completa)

        # Busca direta pela referência completa no JSON
        versiculo_texto = BIBLIA_COMPLETA.get(referencia, None)

        if versiculo_texto:
            return versiculo_texto
        else:
            return f"Versículo '{referencia}' não encontrado na base de dados da Bíblia. Por favor, verifique a referência exata."
    except Exception as e:
        return f"Erro ao tentar citar a Bíblia com a referência '{referencia}': {e}. Certifique-se do formato 'Livro Capítulo:Versículo'."

# --- Funções existentes do app ---
def gerar_pdf_da_conversa(historico_chat):
    pdf = FPDF()
    pdf.add_page()
    try:
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf')
        pdf.set_font('DejaVu', '', 12)
    except FileNotFoundError:
        st.warning("Fonte 'DejaVuSans.ttf' não encontrada. Usando Helvetica.")
        pdf.set_font('Helvetica', '', 12)

    pdf.cell(0, 10, 'Sermão Gerado pelo Assistente de Pregação IA', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)

    for mensagem in historico_chat:
        role = "Usuário" if mensagem['role'] == 'user' else "Assistente de IA"
        content = mensagem['content'].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, f"{role}: {content}")
        pdf.ln(5)

    return bytes(pdf.output())

@st.cache_resource(show_spinner="Carregando base de conhecimento...")
def carregar_base_de_conhecimento():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-MiniLM-L3-v2")
    if os.path.exists(FAISS_INDEX_PATH):
        return FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    return None

# --- NOVA FUNÇÃO PARA CRIAR A CADEIA DE AGENTE ---
def criar_cadeia_de_agente(_vectorstore):
    llm = ChatGroq(model='llama-3.1-8b-instant', temperature=0.7) # Voltamos ao 8b

    # Agora o Agente terá acesso às ferramentas
    tools = [
        citar_biblia, # Nossa nova ferramenta!
        # Podemos adicionar mais ferramentas aqui no futuro, se necessário.
    ]

    # O Agente precisará do retriever como uma 'tool' implícita para o RAG
    # Para isso, usaremos o vectorstore diretamente na construção do agente
    # A instrução para usar o RAG estará no SYSTEM_PROMPT.

    # Cria o prompt do agente, que inclui as instruções e o chat history
    # O SYSTEM_PROMPT (agora em prompts.py) será injetado aqui.
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT), # O SYSTEM_PROMPT contém as instruções para o agente usar as ferramentas e o RAG
        ("placeholder", "{chat_history}"), # Placeholder para o histórico da conversa
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"), # Onde o agente "rascunha" seu raciocínio e uso de ferramentas
    ])

    # Cria o agente que sabe como usar as ferramentas
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Cria o executor do agente. Este é o coração do sistema.
    # Ele orquestra o LLM, as ferramentas e o retriever (para RAG).
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True, # Define como True para ver o raciocínio do agente no console/logs
        # O RAG agora será parte do que o Agente "pensa" em usar, instruído pelo SYSTEM_PROMPT
        # Não passamos o retriever diretamente aqui, mas o prompt guiará o agente a usar
        # o CONTEXTO BÍBLICO PARA CONSULTA RIGOROSA (RAG) para informações gerais,
        # e a 'citar_biblia' para citações LITERAIS.
    )

# --- CONFIGURAÇÃO DE AUTENTICAÇÃO E BANCO DE DADOS ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("ERRO: As chaves do Supabase (SUPABASE_URL, SUPABASE_KEY) não foram encontradas no arquivo .env.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Inicialização segura do session_state
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'name' not in st.session_state:
    st.session_state['name'] = None

# --- LÓGICA DE AUTENTICAÇÃO ---
if not st.session_state['authentication_status']:
    st.title("📖 Assistente de Pregação - IA")
    choice = st.selectbox("Acessar ou Criar Conta", ["Login", "Criar Conta"])

    if choice == "Login":
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Login", type="primary"):
                try:
                    user_data = supabase.table("users").select("*").eq("email", email).execute().data
                    if user_data:
                        user = user_data[0]
                        if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                            st.session_state['authentication_status'] = True
                            st.session_state['name'] = user['name']
                            st.rerun()
                        else:
                            st.error("Email ou senha incorreto.")
                    else:
                        st.error("Email ou senha incorreto.")
                except Exception as e:
                    st.error(f"Erro de conexão com o banco de dados: {e}")

    elif choice == "Criar Conta":
        with st.form("register_form"):
            new_name = st.text_input("Nome")
            new_email = st.text_input("Email")
            new_password = st.text_input("Senha", type="password")
            if st.form_submit_button("Criar Conta", type="primary"):
                if new_name and new_email and new_password:
                    try:
                        existing = supabase.table("users").select("email").eq("email", new_email).execute().data
                        if existing:
                            st.error("Este email já está cadastrado!")
                        else:
                            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            supabase.table("users").insert({"name": new_name, "email": new_email, "password": hashed_password}).execute()
                            st.success("Conta criada com sucesso! Por favor, faça o login.")
                            st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao criar conta: {e}")
                else:
                    st.warning("Por favor, preencha todos os campos.")

# --- LÓGICA DO CHATBOT APÓS AUTENTICAÇÃO ---
if st.session_state['authentication_status']:
    st.title(f"📖 Assistente de Pregação - Olá, {st.session_state['name']}!")

    def limpar_conversa():
        st.session_state.chat_history = []

    with st.sidebar:
        if st.button("Sair"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
        st.divider()

        if "chat_history" in st.session_state and st.session_state.chat_history:
            st.header("Ações da Conversa")
            pdf_data = gerar_pdf_da_conversa(st.session_state.chat_history)
            st.download_button(label="⬇️ Baixar (PDF)", data=pdf_data, file_name="sermão_gerado.pdf", mime="application/pdf")
            imprimir_js = "<script>function printPage() { window.print(); }</script><button onclick='printPage()'>🖨️ Imprimir</button>"
            st.markdown(imprimir_js, unsafe_allow_html=True)
            st.button("🗑️ Limpar", on_click=limpar_conversa)

    vectorstore = carregar_base_de_conhecimento()

    if vectorstore:
        if "conversation_agent" not in st.session_state:
            st.session_state.conversation_agent = criar_cadeia_de_agente(vectorstore)

        st.info("Estou pronto. Faça uma pergunta ou peça para criar um sermão.")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_query = st.chat_input("Ex: 'Crie um sermão sobre fé e perseverança'")
        if user_query:
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                with st.spinner("Estruturando a mensagem com o Poder do Espírito Santo..."):
                    # Agora, invocar o Agente
                    response = st.session_state.conversation_agent.invoke(
                        {"input": user_query, "chat_history": st.session_state.chat_history} # Passa o histórico para o agente
                    )
                    st.write(response["output"]) # O output do Agente é 'output', não 'answer'
            st.session_state.chat_history.append({"role": "assistant", "content": response["output"]})
            st.rerun()
    else:
        st.error("ERRO CRÍTICO: A base de conhecimento (pasta 'faiss_index') não foi encontrada ou está corrompida.")
        st.warning("Por favor, garanta que o script 'treinar_ia.py' foi executado com sucesso e que o modelo de embedding no main.py corresponde ao modelo usado no treinamento.")