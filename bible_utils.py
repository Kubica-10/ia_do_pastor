import os
import json
import re

# Caminho para o arquivo JSON da Bíblia completo
BIBLE_JSON_FILE = "biblia_completa.json" # OU o nome exato do arquivo que você salvou

# Dicionário global para armazenar a Bíblia
# Formato: { "Gênesis 1:1": "No princípio criou Deus os céus e a terra.", ... }
BIBLE_VERSES = {}

# Mapeamento de abreviações para nomes completos dos livros (apenas para o validador)
# Isso pode ser ajustado se as abreviações no JSON forem diferentes
BOOK_ABBREVIATIONS = {
    "Gn": "Gênesis", "Ex": "Êxodo", "Lv": "Levítico", "Nm": "Números", "        Dt": "Deuteronômio",
    "Js": "Josué", "Jz": "Juízes", "Rt": "Rute", "1Sm": "1 Samuel", "2Sm": "2 Samuel",
    "1Rs": "1 Reis", "2Rs": "2 Reis", "1Cr": "1 Crônicas", "2Cr": "2 Crônicas", "Ed": "Esdras",
    "Ne": "Neemias", "Et": "Ester", "Jó": "Jó", "Sl": "Salmos", "Pv": "Provérbios",
    "Ec": "Eclesiastes", "Ct": "Cânticos", "Is": "Isaías", "Jr": "Jeremias", "Lm": "Lamentações",
    "Ez": "Ezequiel", "Dn": "Daniel", "Os": "Oséias", "Jl": "Joel", "Am": "Amós",
    "Ob": "Obadias", "Jn": "Jonas", "Mq": "Miquéias", "Na": "Naum", "Hc": "Habacuque",
    "Sf": "Sofonias", "Ag": "Ageu", "Zc": "Zacarias", "Ml": "Malaquias",
    "Mt": "Mateus", "Mc": "Marcos", "Lc": "Lucas", "Jo": "João", "At": "Atos",
    "Rm": "Romanos", "1Co": "1 Coríntios", "2Co": "2 Coríntios", "Gl": "Gálatas", "Ef": "Efésios",
    "Fp": "Filipenses", "Cl": "Colossenses", "1Ts": "1 Tessalonicenses", "2Ts": "2 Tessalonicenses",
    "1Tm": "1 Timóteo", "2Tm": "2 Timóteo", "Tt": "Tito", "Fm": "Filemom", "Hb": "Hebreus",
    "Tg": "Tiago", "1Pe": "1 Pedro", "2Pe": "2 Pedro", "1Jo": "1 João", "2Jo": "2 João",
    "3Jo": "3 João", "Jd": "Judas", "Ap": "Apocalipse"
}

def get_full_book_name(abbreviation: str) -> str:
    """Retorna o nome completo do livro a partir da abreviação."""
    return BOOK_ABBREVIATIONS.get(abbreviation, abbreviation) # Retorna a própria abrev. se não encontrar


def load_bible_into_memory_from_json():
    """
    Carrega todos os versículos da Bíblia de um arquivo JSON na memória.
    A estrutura JSON esperada é:
    [
        {
            "abbrev": "Gn",
            "chapters": [
                ["texto v1 c1", "texto v2 c1", ...], // Capítulo 1
                ["texto v1 c2", "texto v2 c2", ...], // Capítulo 2
                ...
            ]
        },
        ...
    ]
    """
    if BIBLE_VERSES: # Se já carregou, não precisa carregar de novo
        return

    print(f"Carregando Bíblia do arquivo JSON: {BIBLE_JSON_FILE}...")

    if not os.path.exists(BIBLE_JSON_FILE):
        print(f"ERRO: Arquivo '{BIBLE_JSON_FILE}' não encontrado. Baixe-o e coloque-o na pasta raiz.")
        return

    try:
        with open(BIBLE_JSON_FILE, 'r', encoding='utf-8') as f:
            bible_data = json.load(f)

        for book_entry in bible_data:
            abbrev = book_entry["abbrev"]
            book_name = get_full_book_name(abbrev) # Obter nome completo

            for chapter_idx, chapter_verses in enumerate(book_entry["chapters"]):
                chapter_num = chapter_idx + 1 # Capítulos são baseados em 1
                for verse_idx, verse_text in enumerate(chapter_verses):
                    verse_num = verse_idx + 1 # Versículos são baseados em 1
                    reference = f"{book_name} {chapter_num}:{verse_num}"
                    BIBLE_VERSES[reference] = verse_text.strip()

        print(f"Bíblia carregada do JSON: {len(BIBLE_VERSES)} versículos encontrados.")

    except json.JSONDecodeError as e:
        print(f"ERRO: Não foi possível decodificar o JSON. Verifique a sintaxe do arquivo '{BIBLE_JSON_FILE}'. Erro: {e}")
    except KeyError as e:
        print(f"ERRO: Estrutura do JSON inesperada. Faltando chave: {e}. Verifique o formato do arquivo '{BIBLE_JSON_FILE}'.")
    except Exception as e:
        print(f"ERRO desconhecido ao carregar JSON da Bíblia: {e}")


def get_verse_text(reference: str) -> str | None:
    """
    Retorna o texto de um versículo dado sua referência (e.g., "Gênesis 1:1").
    """
    return BIBLE_VERSES.get(reference)

def find_reference_by_text(text: str) -> str | None:
    """
    Tenta encontrar a referência de um versículo dado seu texto (aproximado).
    Prioriza busca por substring, mais robusta para pequenas variações.
    """
    text_lower = text.lower()

    # Iterar sobre os versículos carregados
    for ref, v_text in BIBLE_VERSES.items():
        v_text_lower = v_text.lower()
        # Verifica se o texto da IA está contido no versículo da Bíblia
        if text_lower in v_text_lower: 
            return ref
        # Verifica se o versículo da Bíblia está contido no texto da IA
        if v_text_lower in text_lower: 
            return ref
    return None

# Carrega a Bíblia assim que o módulo é importado
load_bible_into_memory_from_json()