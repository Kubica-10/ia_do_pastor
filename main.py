import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client
import bcrypt

# --- Importação para PDF (com sintaxe moderna) ---
from fpdf import FPDF, XPos, YPos

# --- Importações do agente (LangChain, etc.) ---
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# --- IMPORTAÇÃO DO SYSTEM_PROMPT DO ARQUIVO prompts.py ---
from prompts import SYSTEM_PROMPT # Isso já puxa o prompt corrigido!

# --- Configuração Inicial ---
st.set_page_config(page_title="Assistente de Pregação - IA", page_icon="📖", layout="wide")
load_dotenv() # Garante que as variáveis do .env sejam carregadas

# --- DEFINIÇÃO DAS FUNÇÕES PRINCIPAIS DO APP ---
FAISS_INDEX_PATH = "faiss_index"

def gerar_pdf_da_conversa(historico_chat):
    pdf = FPDF()
    pdf.add_page()
    try:
        # Tenta adicionar a fonte DejaVu para suportar caracteres especiais, se disponível
        # Certifique-se de que o arquivo DejaVuSans.ttf está na mesma pasta do main.py
        # Baixe de: https://dejavu-fonts.github.io/
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf') 
        pdf.set_font('DejaVu', '', 12)
    except FileNotFoundError:
        # Fallback para uma fonte padrão se DejaVu não for encontrada
        st.warning("Fonte 'DejaVuSans.ttf' não encontrada. Usando Helvetica. Para melhor compatibilidade com caracteres especiais no PDF, baixe 'DejaVuSans.ttf' e coloque na mesma pasta do main.py.")
        pdf.set_font('Helvetica', '', 12)

    pdf.cell(0, 10, 'Sermão Gerado pelo Assistente de Pregação IA', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)

    for mensagem in historico_chat:
        role = "Usuário" if mensagem['role'] == 'user' else "Assistente de IA"
        # Ajusta para UTF-8 e trata erros para evitar problemas de codificação no PDF
        # Nota: FPDF ainda tem algumas limitações com UTF-8 completo, `latin-1` é um workaround comum.
        content = mensagem['content'].encode('latin-1', 'replace').decode('latin-1') 
        pdf.multi_cell(0, 10, f"{role}: {content}")
        pdf.ln(5)

    return bytes(pdf.output())

@st.cache_resource(show_spinner="Carregando base de conhecimento...")
def carregar_base_de_conhecimento():
    # CORREÇÃO CRÍTICA: Usar o mesmo modelo de embedding do treinar_ia.py
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-MiniLM-L3-v2")
    if os.path.exists(FAISS_INDEX_PATH):
        # allow_dangerous_deserialization=True é necessário para carregar índices salvos
        return FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    return None

def criar_cadeia_de_conversa(_vectorstore):
    llm = ChatGroq(model='llama-3.1-8b-instant', temperature=0.7)

    # O prompt agora é mais simples aqui, pois o SYSTEM_PROMPT já contém TUDO.
    # A ordem é: Contexto RAG -> System Prompt (com todas as regras e persona) -> Input do Usuário.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Contexto Bíblico para Consulta Rigorosa: {context}"), # Injeta o contexto dos documentos recuperados AQUI
        ("system", SYSTEM_PROMPT),                                     # O prompt de persona principal (agora importado com tudo)
        ("human", "{input}"),                                           # A pergunta do usuário
    ])

    # create_stuff_documents_chain combina os documentos recuperados no prompt
    chain = create_stuff_documents_chain(llm, prompt)

    # as_retriever busca os documentos relevantes no vectorstore
    # Aumentado 'k' para buscar mais chunks, aumentando a chance de encontrar o versículo exato
    retriever = _vectorstore.as_retriever(search_kwargs={"k": 7}) 

    # create_retrieval_chain orquestra a busca e a geração da resposta
    return create_retrieval_chain(retriever, chain)

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

        # Botões de ação para a conversa (baixar, imprimir, limpar)
        if "chat_history" in st.session_state and st.session_state.chat_history:
            st.header("Ações da Conversa")
            pdf_data = gerar_pdf_da_conversa(st.session_state.chat_history)
            st.download_button(label="⬇️ Baixar (PDF)", data=pdf_data, file_name="sermão_gerado.pdf", mime="application/pdf")
            # Adiciona o botão de impressão via HTML e JavaScript
            imprimir_js = "<script>function printPage() { window.print(); }</script><button onclick='printPage()'>🖨️ Imprimir</button>"
            st.markdown(imprimir_js, unsafe_allow_html=True)
            st.button("🗑️ Limpar", on_click=limpar_conversa)

    # Carrega a base de conhecimento FAISS
    vectorstore = carregar_base_de_conhecimento()

    if vectorstore:
        if "conversation_chain" not in st.session_state:
            st.session_state.conversation_chain = criar_cadeia_de_conversa(vectorstore)

        st.info("Estou pronto. Faça uma pergunta ou peça para criar um sermão.")

        if "chat_history" not in st.session_state: 
            st.session_state.chat_history = []

        # Exibe o histórico de mensagens
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Campo de entrada para o usuário
        user_query = st.chat_input("Ex: 'Crie um sermão sobre fé e perseverança'")
        if user_query:
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"): 
                st.markdown(user_query)

            with st.chat_message("assistant"):
                with st.spinner("Estruturando a mensagem..."):
                    response = st.session_state.conversation_chain.invoke({'input': user_query})
                    st.write(response["answer"])
            st.session_state.chat_history.append({"role": "assistant", "content": response["answer"]})
            st.rerun()
    else:
        st.error("ERRO CRÍTICO: A base de conhecimento (pasta 'faiss_index') não foi encontrada ou está corrompida.")
        st.warning("Por favor, garanta que o script 'treinar_ia.py' foi executado com sucesso e que o modelo de embedding no main.py corresponde ao modelo usado no treinamento.")