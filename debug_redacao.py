import sqlite3
import os

def check_redacao_data():
    # Conectar ao banco de dados
    db_path = 'database.db'
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado!")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Verificar se a tabela redacao existe
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='redacao'")
    if not cur.fetchone():
        print("Tabela redacao não existe!")
        conn.close()
        return
    
    # Listar todas as redações
    cur.execute('SELECT * FROM redacao ORDER BY id DESC LIMIT 5')
    redacoes = cur.fetchall()
    
    print(f"Encontradas {len(redacoes)} redações:")
    print("-" * 50)
    
    for redacao in redacoes:
        print(f"ID: {redacao['id']}")
        print(f"Título: {redacao['titulo']}")
        print(f"Texto de Apoio: '{redacao['texto_apoio']}'")
        print(f"Arquivo de Apoio: '{redacao['arquivo_apoio']}'")
        print(f"Comando: '{redacao['comando']}'")
        print(f"Cabeçalho: '{redacao['cabecalho']}'")
        print("-" * 50)
    
    # Verificar estrutura da tabela
    print("\nEstrutura da tabela redacao:")
    cur.execute("PRAGMA table_info(redacao)")
    columns = cur.fetchall()
    for col in columns:
        print(f"  {col['name']}: {col['type']}")
    
    conn.close()

if __name__ == "__main__":
    check_redacao_data() 