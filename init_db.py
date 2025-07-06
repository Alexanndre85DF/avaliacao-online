import sqlite3

# Cria ou abre o banco de dados
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Cria a tabela de professores (se não existir)
cursor.execute('''
CREATE TABLE IF NOT EXISTS professores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL
)
''')

# Verifica se o usuário admin já existe
cursor.execute("SELECT * FROM professores WHERE email = ?", ("admin@teste.com",))
if cursor.fetchone() is None:
    # Insere o usuário padrão
    cursor.execute(
        "INSERT INTO professores (email, senha) VALUES (?, ?)",
        ("admin@teste.com", "123456")
    )
    print("✅ Usuário padrão inserido.")
else:
    print("ℹ️ Usuário padrão já existe.")

conn.commit()
conn.close()

print("✅ Banco de dados criado com sucesso!")
