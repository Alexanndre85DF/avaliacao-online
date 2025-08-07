import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Garante que a pasta de uploads existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuração do PostgreSQL via variáveis de ambiente

# Função auxiliar para executar consultas SQL
def execute_query(conn, query, params=None):
    cur = conn.cursor()
    is_sqlite = hasattr(conn, 'row_factory')
    if params is None:
        params = ()
    
    if is_sqlite:
        # Converter ? para ? para SQLite
        query = query.replace('?', '?')
        cur.execute(query, params)
    else:
        cur.execute(query, params)
    return cur

# Nova função para conectar ao PostgreSQL ou SQLite
def get_db():   
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL is None:
        # Usar SQLite como fallback
        import sqlite3
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn
    else:
        # Usar SQLite como fallback para PostgreSQL
        import sqlite3
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn




# Atualizar função init_db para funcionar com SQLite e PostgreSQL
def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    # Detectar se é SQLite ou PostgreSQL
    is_sqlite = hasattr(conn, 'row_factory')
    
    if is_sqlite:
        # Sintaxe SQLite
        cur.execute('''CREATE TABLE IF NOT EXISTS professor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            senha TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS avaliacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_id INTEGER REFERENCES professor(id),
            titulo TEXT,
            cabecalho TEXT,
            data_criacao TIMESTAMP
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS questao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avaliacao_id INTEGER REFERENCES avaliacao(id),
            enunciado TEXT,
            suporte_texto TEXT,
            suporte_imagem TEXT,
            comando TEXT,
            imagem TEXT,
            valor REAL,
            tipo TEXT DEFAULT 'objetiva',
            resposta_correta TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS alternativa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            questao_id INTEGER REFERENCES questao(id),
            texto TEXT,
            correta INTEGER DEFAULT 0
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS resposta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avaliacao_id INTEGER REFERENCES avaliacao(id),
            aluno_nome TEXT,
            escola TEXT,
            turma TEXT,
            serie TEXT,
            componente TEXT,
            professor_nome TEXT,
            data_envio TIMESTAMP
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS resposta_questao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resposta_id INTEGER REFERENCES resposta(id),
            questao_id INTEGER REFERENCES questao(id),
            alternativa_id INTEGER REFERENCES alternativa(id),
            resposta_texto TEXT,
            corrigida INTEGER DEFAULT 0,
            correta INTEGER DEFAULT 0
        )''')
        
        # Tabelas para redação
        cur.execute('''CREATE TABLE IF NOT EXISTS redacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_id INTEGER REFERENCES professor(id),
            titulo TEXT,
            texto_apoio TEXT,
            arquivo_apoio TEXT,
            cabecalho TEXT,
            comando TEXT,
            max_linhas INTEGER DEFAULT 30,
            data_criacao TIMESTAMP
        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS resposta_redacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            redacao_id INTEGER REFERENCES redacao(id),
            aluno_nome TEXT,
            escola TEXT,
            turma TEXT,
            serie TEXT,
            componente TEXT,
            professor_nome TEXT,
            texto_redacao TEXT,
            titulo_redacao TEXT,
            nota_final REAL,
            competencia1 REAL,
            competencia2 REAL,
            competencia3 REAL,
            competencia4 REAL,
            competencia5 REAL,
            corrigida INTEGER DEFAULT 0,
            data_envio TIMESTAMP
        )''')
        
        # Cria um professor padrão para testes
        cur.execute('SELECT * FROM professor WHERE email = ?', ('prof@escola.com',))
        if not cur.fetchone():
            cur.execute('INSERT INTO professor (nome, email, senha) VALUES (?, ?, ?)',
                        ('Professor Padrão', 'prof@escola.com', '1234'))
        # Cria usuário admin (CPF como email)
        cur.execute('SELECT * FROM professor WHERE email = ?', ('01099080150',))
        if not cur.fetchone():
            cur.execute('INSERT INTO professor (nome, email, senha) VALUES (?, ?, ?)',
                        ('Administrador', '01099080150', 'brasilia85DF'))
    else:
        # Sintaxe PostgreSQL
        cur.execute('''CREATE TABLE IF NOT EXISTS professor (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            email TEXT,
            senha TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS avaliacao (
            id SERIAL PRIMARY KEY,
            professor_id INTEGER REFERENCES professor(id),
            titulo TEXT,
            cabecalho TEXT,
            data_criacao TIMESTAMP
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS questao (
            id SERIAL PRIMARY KEY,
            avaliacao_id INTEGER REFERENCES avaliacao(id),
            enunciado TEXT,
            suporte_texto TEXT,
            suporte_imagem TEXT,
            comando TEXT,
            imagem TEXT,
            valor REAL,
            tipo TEXT DEFAULT 'objetiva',
            resposta_correta TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS alternativa (
            id SERIAL PRIMARY KEY,
            questao_id INTEGER REFERENCES questao(id),
            texto TEXT,
            correta BOOLEAN DEFAULT FALSE
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS resposta (
            id SERIAL PRIMARY KEY,
            avaliacao_id INTEGER REFERENCES avaliacao(id),
            aluno_nome TEXT,
            escola TEXT,
            turma TEXT,
            serie TEXT,
            componente TEXT,
            professor_nome TEXT,
            data_envio TIMESTAMP
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS resposta_questao (
            id SERIAL PRIMARY KEY,
            resposta_id INTEGER REFERENCES resposta(id),
            questao_id INTEGER REFERENCES questao(id),
            alternativa_id INTEGER REFERENCES alternativa(id),
            resposta_texto TEXT,
            corrigida BOOLEAN DEFAULT FALSE,
            correta BOOLEAN DEFAULT FALSE
        )''')
        
        # Tabelas para redação
        cur.execute('''CREATE TABLE IF NOT EXISTS redacao (
            id SERIAL PRIMARY KEY,
            professor_id INTEGER REFERENCES professor(id),
            titulo TEXT,
            texto_apoio TEXT,
            arquivo_apoio TEXT,
            cabecalho TEXT,
            comando TEXT,
            max_linhas INTEGER DEFAULT 30,
            data_criacao TIMESTAMP
        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS resposta_redacao (
            id SERIAL PRIMARY KEY,
            redacao_id INTEGER REFERENCES redacao(id),
            aluno_nome TEXT,
            escola TEXT,
            turma TEXT,
            serie TEXT,
            componente TEXT,
            professor_nome TEXT,
            texto_redacao TEXT,
            titulo_redacao TEXT,
            nota_final REAL,
            competencia1 REAL,
            competencia2 REAL,
            competencia3 REAL,
            competencia4 REAL,
            competencia5 REAL,
            corrigida BOOLEAN DEFAULT FALSE,
            data_envio TIMESTAMP
        )''')
        
        # Cria um professor padrão para testes
        cur.execute('SELECT * FROM professor WHERE email = ?', ('prof@escola.com',))
        if not cur.fetchone():
            cur.execute('INSERT INTO professor (nome, email, senha) VALUES (?, ?, ?)',
                        ('Professor Padrão', 'prof@escola.com', '1234'))
        # Cria usuário admin (CPF como email)
        cur.execute('SELECT * FROM professor WHERE email = ?', ('01099080150',))
        if not cur.fetchone():
            cur.execute('INSERT INTO professor (nome, email, senha) VALUES (?, ?, ?)',
                        ('Administrador', '01099080150', 'brasilia85DF'))
    
    conn.commit()
    cur.close()
    conn.close()

# Página inicial (login do professor)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        admin_cpfs = ['01099080150', '010.990.801-50', '010.990.80150', '010990801-50']
        if email.replace('.', '').replace('-', '') == '01099080150':
            email = '01099080150'

        conn = get_db()
        cur = execute_query(conn, 'SELECT * FROM professor WHERE email = ? AND senha = ?', (email, senha))
        prof = cur.fetchone()
        conn.close()

        if prof:
            session['professor_id'] = prof[0]
            session['professor_email'] = prof[1]
            # Corrigir para garantir que is_admin sempre é setado
            if prof[2] == '01099080150' and prof[3] == 'brasilia85DF':
                session['is_admin'] = True
                print(f"ADMIN LOGIN: {prof[2]} - is_admin: {session['is_admin']}")
            else:
                session['is_admin'] = False
                print(f"REGULAR LOGIN: {prof[2]} - is_admin: {session['is_admin']}")
            print(f"DEBUG: prof[0]={prof[0]}, prof[1]={prof[1]}, prof[2]={prof[2]}")
            return redirect(url_for('dashboard', professor_id=prof[0]))
        else:
            flash("Login inválido!", "danger")
            return render_template('index.html')  # ← substitua aqui

    return render_template('index.html')



# Dashboard do professor
@app.route('/dashboard/<int:professor_id>') 
def dashboard(professor_id):
    print(f"DASHBOARD DEBUG: professor_id={professor_id}, is_admin={session.get('is_admin')}, email={session.get('professor_email')}")
    conn = get_db()
    cur = execute_query(conn, 'SELECT * FROM avaliacao WHERE professor_id = ?', (professor_id,))
    avaliacoes = cur.fetchall()
    professores = []
    if session.get('is_admin'):
        cur = execute_query(conn, "SELECT * FROM professor WHERE email != ?", ('01099080150',))
        professores = cur.fetchall()
        print(f"ADMIN DASHBOARD: {len(professores)} professores encontrados")
    
    # Buscar o nome do professor logado
    cur = execute_query(conn, 'SELECT nome FROM professor WHERE id = ?', (professor_id,))
    professor_nome = cur.fetchone()
    nome_professor = professor_nome['nome'] if professor_nome else 'Professor'
    
    conn.close()
    return render_template('dashboard.html', professor_id=professor_id, avaliacoes=avaliacoes, professores=professores, nome_professor=nome_professor)

@app.route('/avaliacoes_questoes/<int:professor_id>')
def avaliacoes_questoes(professor_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM avaliacao WHERE professor_id = ?', (professor_id,))
    avaliacoes = cur.fetchall()
    conn.close()
    return render_template('avaliacoes_questoes.html', professor_id=professor_id, avaliacoes=avaliacoes)

@app.route('/redacoes/<int:professor_id>')
def redacoes(professor_id):
    print(f"DEBUG: Acessando redacoes para professor_id: {professor_id}")
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Verificar se a tabela redacao existe
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='redacao'")
        if not cur.fetchone():
            print("DEBUG: Tabela redacao não existe, criando...")
            init_db()
        
        cur.execute('SELECT * FROM redacao WHERE professor_id = ?', (professor_id,))
        redacoes = cur.fetchall()
        print(f"DEBUG: Encontradas {len(redacoes)} redações")
        conn.close()
        return render_template('redacoes.html', professor_id=professor_id, redacoes=redacoes)
    except Exception as e:
        print(f"DEBUG: Erro na rota redacoes: {e}")
        return f"Erro: {str(e)}", 500

@app.route('/nova_redacao/<int:professor_id>', methods=['GET', 'POST'])
def nova_redacao(professor_id):
    if request.method == 'POST':
        print("DEBUG: Recebido POST para nova_redacao")
        try:
            titulo = request.form.get('titulo', '')
            texto_apoio = request.form.get('texto_apoio', '')
            cabecalho = request.form.get('cabecalho', '')
            comando = request.form.get('comando', '')
            max_linhas = int(request.form.get('max_linhas', 30))
            
            print(f"DEBUG: Dados recebidos - titulo: {titulo}, comando: {comando}, max_linhas: {max_linhas}")
            
            arquivo_apoio = None
            if 'arquivo_apoio' in request.files:
                file = request.files['arquivo_apoio']
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    arquivo_apoio = filename
            
            conn = get_db()
            cur = conn.cursor()
            
            # Verificar se a tabela redacao existe
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='redacao'")
            if not cur.fetchone():
                print("DEBUG: Tabela redacao não existe, criando...")
                init_db()
            
            cur.execute('INSERT INTO redacao (professor_id, titulo, texto_apoio, arquivo_apoio, cabecalho, comando, max_linhas, data_criacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (professor_id, titulo or '', texto_apoio, arquivo_apoio, cabecalho, comando, max_linhas, datetime.now()))
            redacao_id = cur.lastrowid
            conn.commit()
            conn.close()
            print(f"DEBUG: Redação criada com ID: {redacao_id}")
            flash('Redação criada com sucesso!')
            return redirect(url_for('gerar_link_redacao', redacao_id=redacao_id))
        except Exception as e:
            print(f"DEBUG: Erro ao criar redação: {e}")
            flash(f'Erro ao criar redação: {str(e)}')
            return redirect(url_for('redacoes', professor_id=professor_id))
    
    return render_template('nova_redacao.html', professor_id=professor_id)

@app.route('/gerar_link_redacao/<int:redacao_id>')
def gerar_link_redacao(redacao_id):
    try:
        print(f"DEBUG: Gerando link para redacao_id: {redacao_id}")
        conn = get_db()
        cur = conn.cursor()
        
        # Verificar se a tabela redacao existe
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='redacao'")
        if not cur.fetchone():
            print("DEBUG: Tabela redacao não existe, criando...")
            init_db()
        
        cur.execute('SELECT * FROM redacao WHERE id = ?', (redacao_id,))
        redacao = cur.fetchone()
        
        if not redacao:
            print(f"DEBUG: Redação {redacao_id} não encontrada")
            flash('Redação não encontrada!')
            return redirect(url_for('index'))
        
        professor_id = redacao['professor_id']
        print(f"DEBUG: professor_id: {professor_id}")
        print(f"DEBUG: redacao data: {redacao}")
        
        conn.close()
        return render_template('gerar_link_redacao.html', redacao=redacao, professor_id=professor_id)
    except Exception as e:
        print(f"DEBUG: Erro ao gerar link da redação: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao gerar link: {str(e)}')
        return redirect(url_for('index'))

@app.route('/responder_redacao/<int:redacao_id>', methods=['GET', 'POST'])
def responder_redacao(redacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM redacao WHERE id = ?', (redacao_id,))
    redacao = cur.fetchone()
    
    if request.method == 'POST':
        aluno_nome = request.form['aluno_nome']
        escola = request.form['escola']
        turma = request.form['turma']
        serie = request.form['serie']
        componente = request.form['componente']
        professor_nome = request.form['professor_nome']
        texto_redacao = request.form['texto_redacao']
        titulo_redacao = request.form.get('titulo_redacao', '')
        
        cur.execute('INSERT INTO resposta_redacao (redacao_id, aluno_nome, escola, turma, serie, componente, professor_nome, texto_redacao, titulo_redacao, data_envio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (redacao_id, aluno_nome, escola, turma, serie, componente, professor_nome, texto_redacao, titulo_redacao, datetime.now()))
        conn.commit()
        conn.close()
        flash('Redação enviada com sucesso!')
        return redirect(url_for('redacao_enviada'))
    
    conn.close()
    return render_template('responder_redacao.html', redacao=redacao)

@app.route('/redacao_enviada')
def redacao_enviada():
    return '<h2>Redação enviada! Obrigado por participar.</h2>'

@app.route('/corrigir_redacoes/<int:redacao_id>')
def corrigir_redacoes(redacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM redacao WHERE id = ?', (redacao_id,))
    redacao = cur.fetchone()
    cur.execute('SELECT * FROM resposta_redacao WHERE redacao_id = ?', (redacao_id,))
    respostas = cur.fetchall()
    conn.close()
    
    # Get professor_id from the redacao
    professor_id = redacao['professor_id'] if redacao else None
    
    return render_template('corrigir_redacoes.html', redacao=redacao, respostas=respostas, professor_id=professor_id)

@app.route('/avaliar_redacao/<int:resposta_id>', methods=['POST'])
def avaliar_redacao(resposta_id):
    try:
        competencia1 = float(request.form.get('competencia1', 0))
        competencia2 = float(request.form.get('competencia2', 0))
        competencia3 = float(request.form.get('competencia3', 0))
        competencia4 = float(request.form.get('competencia4', 0))
        competencia5 = float(request.form.get('competencia5', 0))
        
        nota_final = competencia1 + competencia2 + competencia3 + competencia4 + competencia5
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute('UPDATE resposta_redacao SET competencia1 = ?, competencia2 = ?, competencia3 = ?, competencia4 = ?, competencia5 = ?, nota_final = ?, corrigida = 1 WHERE id = ?',
                    (competencia1, competencia2, competencia3, competencia4, competencia5, nota_final, resposta_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Redação avaliada com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/excluir_redacao/<int:redacao_id>', methods=['POST'])
def excluir_redacao(redacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT professor_id FROM redacao WHERE id = ?', (redacao_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        flash('Redação não encontrada!')
        return redirect(url_for('index'))
    professor_id = row['professor_id']
    
    cur.execute('DELETE FROM resposta_redacao WHERE redacao_id = ?', (redacao_id,))
    cur.execute('DELETE FROM redacao WHERE id = ?', (redacao_id,))
    conn.commit()
    conn.close()
    flash('Redação excluída com sucesso!')
    return redirect(url_for('redacoes', professor_id=professor_id))

# Criar nova avaliação
@app.route('/novo/<int:professor_id>', methods=['GET', 'POST'])
def nova_avaliacao(professor_id):
    if request.method == 'POST':
        titulo = request.form['titulo']
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO avaliacao (professor_id, titulo, data_criacao) VALUES (?, ?, ?)',
                    (professor_id, titulo, datetime.now()))
        conn.commit()
        avaliacao_id = cur.lastrowid
        conn.close()
        return redirect(url_for('adicionar_questoes', avaliacao_id=avaliacao_id))
    return render_template('nova_avaliacao.html', professor_id=professor_id)

# Adicionar questões
@app.route('/avaliacao/<int:avaliacao_id>', methods=['GET', 'POST'])
def adicionar_questoes(avaliacao_id):
    if request.method == 'POST':
        enunciado = request.form['enunciado']
        suporte_texto = request.form.get('suporte_texto')
        comando = request.form.get('comando')
        valor = float(request.form['valor'])
        tipo = request.form.get('tipo', 'objetiva')
        resposta_correta = request.form.get('resposta_correta', '')
        imagem = None
        suporte_imagem = None
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagem = filename
        if 'suporte_imagem' in request.files:
            file2 = request.files['suporte_imagem']
            if file2 and file2.filename != '':
                filename2 = secure_filename(file2.filename)
                file2.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2))
                suporte_imagem = filename2
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO questao (avaliacao_id, enunciado, suporte_texto, suporte_imagem, comando, imagem, valor, tipo, resposta_correta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (avaliacao_id, enunciado, suporte_texto, suporte_imagem, comando, imagem, valor, tipo, resposta_correta))
        questao_id = cur.lastrowid
        
        if tipo == 'objetiva':
            alternativas = request.form.getlist('alternativa')
            corretas = request.form.getlist('correta')
            for i, alt in enumerate(alternativas):
                cur.execute('INSERT INTO alternativa (questao_id, texto, correta) VALUES (?, ?, ?)',
                            (questao_id, alt, str(i) in corretas))
        
        conn.commit()
        conn.close()
        flash('Questão adicionada!')
    # Buscar questões já adicionadas
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = ?', (avaliacao_id,))
    questoes = cur.fetchall()
    conn.close()
    return render_template('adicionar_questoes.html', avaliacao_id=avaliacao_id, questoes=questoes)

# Finalizar avaliação e gerar link
@app.route('/gerar_link/<int:avaliacao_id>')
def gerar_link(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT professor_id FROM avaliacao WHERE id = ?', (avaliacao_id,))
    row = cur.fetchone()
    professor_id = row['professor_id'] if row else 1
    link = url_for('responder_avaliacao', avaliacao_id=avaliacao_id, _external=True)
    return render_template('gerar_link.html', link=link, professor_id=professor_id)

# Aluno responde avaliação
@app.route('/responder/<int:avaliacao_id>', methods=['GET', 'POST'])
def responder_avaliacao(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM avaliacao WHERE id = ?', (avaliacao_id,))
    avaliacao = cur.fetchone()
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = ?', (avaliacao_id,))
    questoes = cur.fetchall()
    questoes_com_alternativas = []
    for q in questoes:
        cur.execute('SELECT * FROM alternativa WHERE questao_id = ?', (q['id'],))
        alternativas = cur.fetchall()
        questoes_com_alternativas.append({'questao': q, 'alternativas': alternativas})
    if request.method == 'POST':
        aluno_nome = request.form['aluno_nome']
        escola = request.form['escola']
        turma = request.form['turma']
        serie = request.form['serie']
        componente = request.form['componente']
        professor_nome = request.form['professor_nome']
        cur.execute('INSERT INTO resposta (avaliacao_id, aluno_nome, escola, turma, serie, componente, professor_nome, data_envio) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (avaliacao_id, aluno_nome, escola, turma, serie, componente, professor_nome, datetime.now()))
        resposta_id = cur.lastrowid
        for q in questoes:
            if q['tipo'] == 'objetiva':
                alternativa_id = request.form.get(f'questao_{q["id"]}')
                if alternativa_id:
                    cur.execute('INSERT INTO resposta_questao (resposta_id, questao_id, alternativa_id) VALUES (?, ?, ?)',
                                (resposta_id, q['id'], alternativa_id))
            else:  # subjetiva
                resposta_texto = request.form.get(f'questao_{q["id"]}', '')
                if resposta_texto:
                    cur.execute('INSERT INTO resposta_questao (resposta_id, questao_id, resposta_texto) VALUES (?, ?, ?)',
                                (resposta_id, q['id'], resposta_texto))
        conn.commit()
        conn.close()
        flash('Respostas enviadas com sucesso!')
        return redirect(url_for('resposta_enviada'))
    conn.close()
    return render_template('responder_avaliacao.html', avaliacao=avaliacao, questoes=questoes_com_alternativas)

@app.route('/resposta_enviada')
def resposta_enviada():
    return '<h2>Respostas enviadas! Obrigado por participar.</h2>'

# Professor vê resultados
@app.route('/resultado/<int:avaliacao_id>')
def resultado(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT professor_id FROM avaliacao WHERE id = ?', (avaliacao_id,))
    row = cur.fetchone()
    professor_id = row['professor_id'] if row else 1
    cur.execute('SELECT * FROM resposta WHERE avaliacao_id = ?', (avaliacao_id,))
    respostas = cur.fetchall()
    resultados = []
    for resp in respostas:
        cur.execute('SELECT rq.*, q.valor FROM resposta_questao rq JOIN questao q ON rq.questao_id = q.id WHERE rq.resposta_id = ?', (resp['id'],))
        respostas_questoes = cur.fetchall()
        acertos = 0
        total = 0
        for rq in respostas_questoes:
            if rq['alternativa_id']:  # questão objetiva
                cur.execute('SELECT correta, valor FROM alternativa JOIN questao ON alternativa.questao_id = questao.id WHERE alternativa.id = ?', (rq['alternativa_id'],))
                alt = cur.fetchone()
                if alt and alt['correta']:
                    acertos += alt['valor']
                if alt:
                    total += alt['valor']
            else:  # questão subjetiva
                if rq['corrigida'] and rq['correta']:
                    acertos += rq['valor']
                total += rq['valor']
        resultados.append({'resposta': resp, 'acertos': acertos, 'total': total})
    conn.close()
    return render_template('resultado.html', resultados=resultados, professor_id=professor_id, avaliacao_id=avaliacao_id)

# Servir imagens de upload
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/excluir_avaliacao/<int:avaliacao_id>', methods=['POST'])
def excluir_avaliacao(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    # Descobrir o professor_id antes de deletar
    cur.execute('SELECT professor_id FROM avaliacao WHERE id = ?', (avaliacao_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        flash('Avaliação não encontrada!')
        return redirect(url_for('index'))
    professor_id = row['professor_id']
    # Excluir respostas e respostas_questao
    cur.execute('SELECT id FROM resposta WHERE avaliacao_id = ?', (avaliacao_id,))
    respostas = cur.fetchall()
    for r in respostas:
        cur.execute('DELETE FROM resposta_questao WHERE resposta_id = ?', (r['id'],))
    cur.execute('DELETE FROM resposta WHERE avaliacao_id = ?', (avaliacao_id,))
    # Excluir alternativas e questões
    cur.execute('SELECT id FROM questao WHERE avaliacao_id = ?', (avaliacao_id,))
    questoes = cur.fetchall()
    for q in questoes:
        cur.execute('DELETE FROM alternativa WHERE questao_id = ?', (q['id'],))
    cur.execute('DELETE FROM questao WHERE avaliacao_id = ?', (avaliacao_id,))
    # Excluir avaliação
    cur.execute('DELETE FROM avaliacao WHERE id = ?', (avaliacao_id,))
    conn.commit()
    conn.close()
    flash('Avaliação excluída com sucesso!')
    return redirect(url_for('dashboard', professor_id=professor_id))

@app.route('/resposta/<int:resposta_id>')
def resposta_detalhe(resposta_id):
    conn = get_db()
    cur = conn.cursor()
    # Buscar resposta e avaliação
    cur.execute('SELECT * FROM resposta WHERE id = ?', (resposta_id,))
    resposta = cur.fetchone()
    if not resposta:
        conn.close()
        flash('Resposta não encontrada!')
        return redirect(url_for('index'))
    avaliacao_id = resposta['avaliacao_id']
    # Buscar questões
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = ?', (avaliacao_id,))
    questoes = cur.fetchall()
    questoes_detalhe = []
    for q in questoes:
        cur.execute('SELECT * FROM alternativa WHERE questao_id = ?', (q['id'],))
        alternativas = cur.fetchall()
        cur.execute('SELECT alternativa_id FROM resposta_questao WHERE resposta_id = ? AND questao_id = ?', (resposta_id, q['id']))
        marcada = cur.fetchone()
        marcada_id = marcada['alternativa_id'] if marcada else None
        questoes_detalhe.append({'questao': q, 'alternativas': alternativas, 'marcada_id': marcada_id})
    conn.close()
    return render_template('resposta_detalhe.html', resposta=resposta, questoes=questoes_detalhe, avaliacao_id=avaliacao_id)

@app.route('/cadastrar_professor', methods=['GET', 'POST'])
def cadastrar_professor():
    # Só permite acesso se for admin
    if not session.get('is_admin'):
        flash('Acesso restrito ao administrador!')
        return redirect(url_for('index'))
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM professor WHERE email = ?', (email,))
        if cur.fetchone():
            conn.close()
            flash('Já existe um professor com este email!')
            return render_template('cadastrar_professor.html')
        cur.execute('INSERT INTO professor (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha))
        conn.commit()
        conn.close()
        flash('Professor cadastrado com sucesso!')
        return redirect(url_for('cadastrar_professor'))
    return render_template('cadastrar_professor.html')

@app.route('/excluir_questao/<int:questao_id>/<int:avaliacao_id>', methods=['POST'])
def excluir_questao(questao_id, avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    # Excluir alternativas da questão
    cur.execute('DELETE FROM alternativa WHERE questao_id = ?', (questao_id,))
    # Excluir a questão
    cur.execute('DELETE FROM questao WHERE id = ?', (questao_id,))
    conn.commit()
    conn.close()
    flash('Questão excluída com sucesso!')
    return redirect(url_for('adicionar_questoes', avaliacao_id=avaliacao_id))

@app.route('/resetar_senha/<int:professor_id>', methods=['POST'])
def resetar_senha(professor_id):
    if not session.get('is_admin'):
        flash('Acesso restrito ao administrador!')
        return redirect(url_for('index'))
    conn = get_db()
    cur = conn.cursor()
    # Não permite resetar o admin
    cur.execute("SELECT * FROM professor WHERE id = ? AND email != ?", (professor_id, '01099080150'))
    prof = cur.fetchone()
    if not prof:
        conn.close()
        flash('Professor não encontrado ou não pode ter a senha resetada!')
        return redirect(url_for('dashboard', professor_id=session.get('professor_id')))
    cur.execute('UPDATE professor SET senha = ? WHERE id = ?', ('123456', professor_id))
    conn.commit()
    conn.close()
    flash('Senha resetada para 123456 com sucesso!')
    return redirect(url_for('dashboard', professor_id=session.get('professor_id')))

@app.route('/excluir_professor/<int:professor_id>', methods=['POST'])
def excluir_professor(professor_id):
    if not session.get('is_admin'):
        flash('Acesso restrito ao administrador!')
        return redirect(url_for('index'))
    conn = get_db()
    cur = conn.cursor()
    # Não permite excluir o admin
    cur.execute("SELECT * FROM professor WHERE id = ? AND email != ?", (professor_id, '01099080150'))
    prof = cur.fetchone()
    if not prof:
        conn.close()
        flash('Professor não encontrado ou não pode ser excluído!')
        return redirect(url_for('dashboard', professor_id=session.get('professor_id')))
    cur.execute('DELETE FROM professor WHERE id = ?', (professor_id,))
    conn.commit()
    conn.close()
    flash('Professor excluído com sucesso!')
    return redirect(url_for('dashboard', professor_id=session.get('professor_id')))

@app.route('/visualizar_avaliacao/<int:avaliacao_id>')
def visualizar_avaliacao(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM avaliacao WHERE id = ?', (avaliacao_id,))
    avaliacao = cur.fetchone()
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = ?', (avaliacao_id,))
    questoes = cur.fetchall()
    questoes_com_alternativas = []
    for q in questoes:
        cur.execute('SELECT * FROM alternativa WHERE questao_id = ?', (q['id'],))
        alternativas = cur.fetchall()
        questoes_com_alternativas.append({'questao': q, 'alternativas': alternativas})
    conn.close()
    return render_template('visualizar_avaliacao.html', avaliacao=avaliacao, questoes=questoes_com_alternativas, avaliacao_id=avaliacao_id)

@app.route("/")
def home():
    return render_template("index.html")


@app.route('/grafico_resultado/<int:avaliacao_id>')
def grafico_resultado(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM resposta WHERE avaliacao_id = ?', (avaliacao_id,))
    respostas = cur.fetchall()
    pontuacoes = []
    nomes = []
    for resp in respostas:
        cur.execute('SELECT rq.*, q.valor FROM resposta_questao rq JOIN questao q ON rq.questao_id = q.id WHERE rq.resposta_id = ?', (resp['id'],))
        respostas_questoes = cur.fetchall()
        acertos = 0
        total = 0
        for rq in respostas_questoes:
            if rq['alternativa_id']:  # questão objetiva
                cur.execute('SELECT correta, valor FROM alternativa JOIN questao ON alternativa.questao_id = questao.id WHERE alternativa.id = ?', (rq['alternativa_id'],))
                alt = cur.fetchone()
                if alt and alt['correta']:
                    acertos += alt['valor']
                if alt:
                    total += alt['valor']
            else:  # questão subjetiva
                if rq['corrigida'] and rq['correta']:
                    acertos += rq['valor']
                total += rq['valor']
        nomes.append(resp['aluno_nome'])
        pontuacoes.append(acertos)
    conn.close()
    return render_template('grafico_resultado.html', avaliacao_id=avaliacao_id, nomes=nomes, pontuacoes=pontuacoes)

@app.route('/corrigir_subjetivas/<int:avaliacao_id>')
def corrigir_subjetivas(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    # Buscar questões subjetivas da avaliação
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = ? AND tipo = ?', (avaliacao_id, 'subjetiva'))
    questoes_subjetivas = cur.fetchall()
    
    # Buscar respostas para questões subjetivas
    respostas_subjetivas = []
    for questao in questoes_subjetivas:
        cur.execute('SELECT rq.*, r.aluno_nome FROM resposta_questao rq JOIN resposta r ON rq.resposta_id = r.id WHERE rq.questao_id = ? AND rq.resposta_texto IS NOT NULL', (questao['id'],))
        respostas = cur.fetchall()
        respostas_subjetivas.append({'questao': questao, 'respostas': respostas})
    
    conn.close()
    return render_template('corrigir_subjetivas.html', respostas_subjetivas=respostas_subjetivas, avaliacao_id=avaliacao_id)

@app.route('/marcar_correta/<int:resposta_questao_id>', methods=['POST'])
def marcar_correta(resposta_questao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE resposta_questao SET corrigida = 1, correta = 1 WHERE id = ?', (resposta_questao_id,))
    conn.commit()
    conn.close()
    flash('Resposta marcada como correta!')
    return redirect(request.referrer)

@app.route('/marcar_incorreta/<int:resposta_questao_id>', methods=['POST'])
def marcar_incorreta(resposta_questao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE resposta_questao SET corrigida = 1, correta = 0 WHERE id = ?', (resposta_questao_id,))
    conn.commit()
    conn.close()
    flash('Resposta marcada como incorreta!')
    return redirect(request.referrer)

@app.route('/analise_questoes/<int:avaliacao_id>')
def analise_questoes(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    # Buscar todas as questões da avaliação
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = ?', (avaliacao_id,))
    questoes = cur.fetchall()
    questoes_analise = []
    for questao in questoes:
        if questao['tipo'] == 'objetiva':
            cur.execute('SELECT * FROM alternativa WHERE questao_id = ?', (questao['id'],))
            alternativas = cur.fetchall()
            alternativas_dados = []
            total_respostas = 0
            for alt in alternativas:
                cur.execute('SELECT COUNT(*) as total FROM resposta_questao WHERE questao_id = ? AND alternativa_id = ?', (questao['id'], alt['id']))
                count = cur.fetchone()['total']
                alternativas_dados.append({'id': alt['id'], 'texto': alt['texto'], 'total': count})
                total_respostas += count
            # Calcular porcentagem
            for alt in alternativas_dados:
                alt['porcentagem'] = (alt['total'] / total_respostas * 100) if total_respostas > 0 else 0
            questoes_analise.append({'questao': questao, 'alternativas': alternativas_dados})
        else:  # subjetiva
            cur.execute('SELECT COUNT(*) as total FROM resposta_questao WHERE questao_id = ? AND resposta_texto IS NOT NULL', (questao['id'],))
            total = cur.fetchone()['total']
            cur.execute('SELECT COUNT(*) as corretas FROM resposta_questao WHERE questao_id = ? AND corrigida = 1 AND correta = 1', (questao['id'],))
            corretas = cur.fetchone()['corretas']
            questoes_analise.append({'questao': questao, 'total': total, 'corretas': corretas})
    conn.close()
    return render_template('analise_questoes.html', questoes_analise=questoes_analise, avaliacao_id=avaliacao_id)

def cadastrar_professor_manual(nome, email, senha):
    conn = get_db()
    cur = execute_query(conn, 'SELECT * FROM professor WHERE email = ?', (email,))
    if cur.fetchone():
        print('Já existe um professor com este email!')
    else:
        cur = execute_query(conn, 'INSERT INTO professor (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha))
        conn.commit()
        print('Professor cadastrado com sucesso!')
    cur.close()
    conn.close()

if __name__ == '__main__':
    init_db()
    # Chame a função assim:
    cadastrar_professor_manual('Noádia Martins', 'noadiamartins@seduc.to.gov.br', '123456')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 
