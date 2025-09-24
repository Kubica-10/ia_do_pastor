import os
import glob
from langchain_community.document_loaders import PyPDFLoader, TextLoader # Importamos TextLoader para TXT
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import warnings

warnings.filterwarnings("ignore") # Suprime avisos de bibliotecas internas

# --- Configurações de Pastas ---
PDF_FOLDER = "pdfs"
TRANSCRIPTS_FOLDER = "textos_transcritos" # Pasta para as transcrições em TXT
FAISS_INDEX_PATH = "faiss_index"

def treinar_ia_com_midias():
    print("Iniciando o treinamento da IA (Modo Focado em PDF e Transcrições TXT)...")
    
    all_docs = []

    # 1. Carregar documentos PDF
    print(f"\nProcurando por arquivos PDF na pasta '{PDF_FOLDER}'...")
    pdf_files = glob.glob(os.path.join(PDF_FOLDER, "*.pdf"))
    
    if not pdf_files:
        print(f"Nenhum arquivo PDF encontrado na pasta '{PDF_FOLDER}'.")

    for pdf_file in pdf_files:
        try:
            loader = PyPDFLoader(pdf_file)
            docs = loader.load()
            all_docs.extend(docs)
            print(f"  - SUCESSO PDF: {os.path.basename(pdf_file)}")
        except Exception as e:
            print(f"  - ERRO ao carregar PDF '{os.path.basename(pdf_file)}': {e}")

    # 2. Carregar transcrições de texto puro (TXT)
    print(f"\nProcurando por arquivos de texto (.txt) na pasta '{TRANSCRIPTS_FOLDER}'...")
    text_files = glob.glob(os.path.join(TRANSCRIPTS_FOLDER, "*.txt"))

    if not text_files:
        print(f"Nenhum arquivo de texto (.txt) encontrado na pasta '{TRANSCRIPTS_FOLDER}'.")

    for text_file in text_files:
        try:
            # TextLoader é ideal para arquivos .txt
            loader = TextLoader(text_file, encoding='utf-8') 
            docs = loader.load()
            
            # Adiciona metadados para identificar a fonte
            for doc in docs:
                doc.metadata['source'] = f"transcricao_txt:{os.path.basename(text_file)}"
            
            all_docs.extend(docs)
            print(f"  - SUCESSO Transcrição TXT: {os.path.basename(text_file)} (Carregadas {len(docs)} páginas/fragmentos)")
        except Exception as e:
            print(f"  - ERRO ao carregar TXT '{os.path.basename(text_file)}': {e}")
    
    if not all_docs:
        print("Nenhum documento (PDF ou TXT) foi carregado com sucesso. O treinamento será abortado.")
        return

    # 3. Dividir os textos em pedaços (chunks)
    print("\nDividindo os textos em pedaços (chunks)...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    splits = text_splitter.split_documents(all_docs)
    print(f"  - Documentos divididos em {len(splits)} pedaços.")

    # 4. Criar embeddings a partir dos pedaços
    print("\nCriando embeddings (pode demorar)...")
    # MODELO DE EMBEDDING OTIMIZADO PARA MENOR CONSUMO DE RECURSOS
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-MiniLM-L3-v2")

    # 5. Construir e salvar a base de conhecimento FAISS
    print("\nConstruindo e salvando a base de conhecimento (índice FAISS)...")
    vectorstore = FAISS.from_documents(splits, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)
    
    print("\n>>> TREINAMENTO CONCLUÍDO COM SUCESSO! <<<")
    print(f"Base de conhecimento salva em: '{FAISS_INDEX_PATH}'")

if __name__ == "__main__":
    # Garante que as pastas de mídias existem. Se não, as cria.
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)
        print(f"Pasta '{PDF_FOLDER}' criada. Por favor, adicione seus PDFs aqui.")
    if not os.path.exists(TRANSCRIPTS_FOLDER):
        os.makedirs(TRANSCRIPTS_FOLDER)
        print(f"Pasta '{TRANSCRIPTS_FOLDER}' criada. Por favor, adicione suas transcrições TXT aqui.")
    
    treinar_ia_com_midias()