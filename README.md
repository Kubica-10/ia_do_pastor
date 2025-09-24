# 📖 Assistente de Pregação com IA - A Voz da Unção em Suas Mãos!

Bem-vindo ao **Assistente de Pregação com IA**, uma ferramenta revolucionária desenvolvida para apoiar pastores, líderes e estudantes da Palavra na elaboração de sermões poderosos, profundos e inspirados! Inspirado na autoridade teológica e no estilo inconfundível do Pastor Silas Malafaia, esta IA não apenas consulta a Palavra, mas a prega com vigor, paixão e unção!

---

## 🌟 Recursos e Funcionalidades:

* **Geração de Sermões no Estilo Silas Malafaia:** A IA foi cuidadosamente treinada para emular a retórica, a cadência, os gestos (indicados no texto), o uso de maiúsculas para ênfase e as interjeições impactantes do Pastor Silas.
* **Fidelidade Bíblica Rigorosa (RAG - Retrieval-Augmented Generation):** Baseado em uma robusta base de conhecimento da Palavra de Deus (Bíblia JFA em português), a IA garante que todas as citações bíblicas são precisas e contextualizadas, evitando alucinações.
* **Base de Conhecimento Expansível:** Você pode adicionar seus próprios PDFs e transcrições em TXT de estudos, livros e sermões (na pasta `pdfs/` e `textos_transcritos/`) para expandir a "memória" da IA e personalizar suas respostas.
* **Autenticação Segura:** Sistema de login e registro de usuários integrado com Supabase, garantindo acesso seguro e personalizado.
* **Exportação de Sermões:** Baixe os sermões gerados em formato PDF ou imprima-os diretamente do aplicativo.

---

## 🛠️ Como Funciona (Para Desenvolvedores/Administradores):

Este projeto é construído com Python, Streamlit, LangChain e Supabase.

### Pré-requisitos:

* Python 3.9+
* `pip` (gerenciador de pacotes Python)

### 🚀 Configuração Local:

1.  **Clone o Repositório:**
    ```bash
    git clone [LINK_DO_SEU_REPOSITORIO]
    cd ia_do_pastor
    ```

2.  **Crie e Ative o Ambiente Virtual:**
    ```bash
    python3 -m venv ia_pastor_env
    source ia_pastor_env/bin/activate  # No Windows, use `ia_pastor_env\Scripts\activate`
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuração de Variáveis de Ambiente (`.env`):**
    Crie um arquivo `.env` na raiz do projeto com suas credenciais:
    ```
    GROQ_API_KEY=sua_chave_api_groq
    SUPABASE_URL=sua_url_supabase
    SUPABASE_KEY=sua_chave_anon_supabase
    ```
    **Importante:** Mantenha este arquivo **SENSÍVEL** e **NÃO** o adicione ao controle de versão Git (ele já está no `.gitignore`).

5.  **Prepare a Base de Conhecimento:**
    * Crie as pastas `pdfs/` e `textos_transcritos/` na raiz do projeto.
    * Adicione seus documentos em PDF e/ou TXT nessas pastas.
    * **Execute o script de treinamento para criar o índice FAISS:**
        ```bash
        python treinar_ia.py
        ```
        Este comando criará a pasta `faiss_index/` com a base de conhecimento.

6.  **Execute o Aplicativo Streamlit:**
    ```bash
    streamlit run main.py
    ```
    O aplicativo será aberto em seu navegador padrão.

---

## ☁️ Deploy (Hospedagem Online):

Para compartilhar o aplicativo com seus amigos e clientes, você pode hospedá-lo em plataformas como o **Streamlit Community Cloud**.

### Passos para Deploy no Streamlit Community Cloud:

1.  **Faça Upload do Código para o GitHub:**
    Certifique-se de que todo o seu código (exceto os arquivos ignorados pelo `.gitignore`) esteja em um repositório público no GitHub.
    * `main.py`
    * `prompts.py`
    * `treinar_ia.py`
    * `requirements.txt`
    * `Procfile` (se houver, para gunicorn/render.com)
    * **Opcional:** Adicione o arquivo `DejaVuSans.ttf` na raiz do projeto se você o estiver usando para PDFs e não quiser problemas de fonte no deploy.

2.  **Configuração no Streamlit Community Cloud:**
    * Vá para [https://share.streamlit.io/](https://share.streamlit.io/) e faça login.
    * Clique em "New app".
    * Selecione seu repositório GitHub, o branch principal e `main.py` como o arquivo principal.
    * **Variáveis de Ambiente (Secrets):** No Streamlit Cloud, você precisará adicionar suas chaves `GROQ_API_KEY`, `SUPABASE_URL` e `SUPABASE_KEY` como "Secrets" no painel de configuração do seu aplicativo. Elas serão acessadas como variáveis de ambiente pelo aplicativo.
    * **Indexação da Base de Conhecimento no Deploy:**
        O Streamlit Cloud não executa `treinar_ia.py` automaticamente. Você tem duas opções:
        * **Opção A (Recomendado para testes):** Faça o upload da pasta `faiss_index/` (com os arquivos `index.faiss` e `index.pkl`) diretamente para o seu repositório GitHub. **NOTA:** Esta pasta pode ser grande. Se for muito grande, considere a Opção B.
        * **Opção B (Mais robusta, para produção):** Modifique seu `main.py` para verificar se o `faiss_index` existe. Se não existir, ele deve chamar `treinar_ia.py` automaticamente na primeira execução do deploy. **No entanto, isso pode levar tempo e recursos de CPU/RAM no Streamlit Cloud na primeira vez.** (Para os testes iniciais com amigos, a Opção A é mais simples).

3.  **Deploy:** Clique em "Deploy!" e aguarde o Streamlit construir e lançar seu aplicativo.

---

## 🤝 Contribuição e Suporte:

Este projeto foi desenvolvido com a paixão pela Palavra e a inovação tecnológica. Para dúvidas, sugestões ou suporte, entre em contato com [Seu Nome/Email/Contato aqui].

---

**Deus abençoe poderosamente sua jornada com esta ferramenta!**