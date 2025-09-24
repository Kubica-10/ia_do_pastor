import os
import json

SOURCE_JSON_FILE = "biblia_completa.json" # DEVE SER O NOME EXATO DO SEU ARQUIVO JSON
OUTPUT_DIR = "textos_transcritos" 

# Mapeamento de abreviações para nomes completos dos livros (igual ao bible_utils.py)
# Este mapeamento é crucial para o script funcionar.
BOOK_ABBREVIATIONS = {
    "Gn": "Gênesis", "Ex": "Êxodo", "Lv": "Levítico", "Nm": "Números", "Dt": "Deuteronômio",
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
    return BOOK_ABBREVIATIONS.get(abbreviation, abbreviation)

def convert_json_to_txt():
    print(f"DEPURAÇÃO: Iniciando função convert_json_to_txt().")
    print(f"DEPURAÇÃO: Tentando encontrar o arquivo JSON: '{SOURCE_JSON_FILE}'")

    if not os.path.exists(SOURCE_JSON_FILE):
        print(f"ERRO: Arquivo JSON '{SOURCE_JSON_FILE}' NÃO ENCONTRADO na raiz do projeto. Por favor, verifique o nome e o local.")
        return

    print(f"DEPURAÇÃO: Arquivo '{SOURCE_JSON_FILE}' ENCONTRADO.")
    print(f"DEPURAÇÃO: Verificando/criando pasta de saída: '{OUTPUT_DIR}'")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"DEPURAÇÃO: Pasta '{OUTPUT_DIR}' criada.")
    else:
        print(f"DEPURAÇÃO: Pasta '{OUTPUT_DIR}' já existe.")

    print(f"Convertendo '{SOURCE_JSON_FILE}' para arquivos TXT na pasta '{OUTPUT_DIR}'...")

    try:
        with open(SOURCE_JSON_FILE, 'r', encoding='utf-8') as f:
            bible_data = json.load(f)
        print(f"DEPURAÇÃO: JSON carregado com sucesso. Contém {len(bible_data)} entradas de livros.")

        total_verses = 0
        for book_entry in bible_data:
            abbrev = book_entry.get("abbrev") # Usar .get() para evitar KeyError se a chave não existir
            if not abbrev:
                print(f"AVISO: Entrada de livro sem 'abbrev': {book_entry}. Pulando.")
                continue

            book_name = get_full_book_name(abbrev) 

            # Ajuste o nome do arquivo para remover caracteres inválidos se necessário
            book_filename = os.path.join(OUTPUT_DIR, f"{book_name.replace(' ', '_').replace(':', '')}.txt") 

            print(f"DEPURAÇÃO: Processando livro: {book_name} (abreviação: {abbrev})")

            # Verifique se 'chapters' existe e é uma lista
            if "chapters" not in book_entry or not isinstance(book_entry["chapters"], list):
                print(f"AVISO: Livro '{book_name}' não possui a chave 'chapters' ou 'chapters' não é uma lista. Pulando.")
                continue

            with open(book_filename, 'w', encoding='utf-8') as outfile:
                for chapter_idx, chapter_verses in enumerate(book_entry["chapters"]):
                    chapter_num = chapter_idx + 1 

                    # Verifique se chapter_verses é uma lista
                    if not isinstance(chapter_verses, list):
                        print(f"AVISO: Capítulo {chapter_num} do livro '{book_name}' não é uma lista de versículos. Pulando.")
                        continue

                    for verse_idx, verse_text in enumerate(chapter_verses):
                        verse_num = verse_idx + 1 

                        # Garante o formato: Livro Capítulo:Versículo - Texto
                        formatted_line = f"{book_name} {chapter_num}:{verse_num} - {verse_text.strip()}\n"
                        outfile.write(formatted_line)
                        total_verses += 1
            print(f"Livro '{book_name}' salvo em '{book_filename}'. Total de versículos para este livro: {total_verses - (total_verses - len(chapter_verses))}.") # Pequena correção para contar versículos por livro

        print(f"Conversão concluída. Total de {total_verses} versículos salvos em TXT.")

    except json.JSONDecodeError as e:
        print(f"ERRO FATAL: Não foi possível decodificar o JSON. Verifique a sintaxe do arquivo '{SOURCE_JSON_FILE}'. Erro: {e}")
    except KeyError as e:
        print(f"ERRO FATAL: Estrutura do JSON inesperada. Faltando chave: {e}. Verifique o formato do arquivo '{SOURCE_JSON_FILE}'.")
    except Exception as e:
        print(f"ERRO FATAL desconhecido ao converter JSON para TXT: {e}")

if __name__ == "__main__":
    convert_json_to_txt()