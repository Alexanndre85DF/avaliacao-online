import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
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
PG_HOST = os.environ.get('PG_HOST', 'localhost')
PG_DB = os.environ.get('PG_DB', 'prova_saeb')
PG_USER = os.environ.get('PG_USER', 'postgres')
PG_PASSWORD = os.environ.get('PG_PASSWORD', 'postgres')
PG_PORT = os.environ.get('PG_PORT', '5432')

# Nova função para conectar ao PostgreSQL
def get_db():   
    import psycopg2

    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL is None:
        raise Exception("DATABASE_URL não definida")

    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    conn.autocommit = True
    return conn




# Atualizar função init_db para sintaxe PostgreSQL
# Trocar AUTOINCREMENT por SERIAL, BOOLEAN por BOOLEAN DEFAULT FALSE, etc.
def init_db():
    conn = get_db()
    cur = conn.cursor()
    # Professores
    cur.execute('''CREATE TABLE IF NOT EXISTS professor (
        id SERIAL PRIMARY KEY,
        nome TEXT,
        email TEXT,
        senha TEXT
    )''')
    # Avaliações
    cur.execute('''CREATE TABLE IF NOT EXISTS avaliacao (
        id SERIAL PRIMARY KEY,
        professor_id INTEGER REFERENCES professor(id),
        titulo TEXT,
        cabecalho TEXT,
        data_criacao TIMESTAMP
    )''')
    # Questões
    cur.execute('''CREATE TABLE IF NOT EXISTS questao (
        id SERIAL PRIMARY KEY,
        avaliacao_id INTEGER REFERENCES avaliacao(id),
        enunciado TEXT,
        suporte_texto TEXT,
        suporte_imagem TEXT,
        comando TEXT,
        imagem TEXT,
        valor REAL
    )''')
    # Alternativas
    cur.execute('''CREATE TABLE IF NOT EXISTS alternativa (
        id SERIAL PRIMARY KEY,
        questao_id INTEGER REFERENCES questao(id),
        texto TEXT,
        correta BOOLEAN DEFAULT FALSE
    )''')
    # Respostas dos alunos
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
        alternativa_id INTEGER REFERENCES alternativa(id)
    )''')
    # Cria um professor padrão para testes
    cur.execute('SELECT * FROM professor WHERE email = %s', ('prof@escola.com',))
    if not cur.fetchone():
        cur.execute('INSERT INTO professor (nome, email, senha) VALUES (%s, %s, %s)',
                    ('Professor Padrão', 'prof@escola.com', '1234'))
    # Cria usuário admin (CPF como email)
    cur.execute('SELECT * FROM professor WHERE email = %s', ('01099080150',))
    if not cur.fetchone():
        cur.execute('INSERT INTO professor (nome, email, senha) VALUES (%s, %s, %s)',
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
        # Normaliza CPF do admin
        admin_cpfs = ['01099080150', '010.990.801-50', '010.990.80150', '010990801-50']
        if email.replace('.', '').replace('-', '') == '01099080150':
            email = '01099080150'
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM professor WHERE email = %s AND senha = %s', (email, senha))
        prof = cur.fetchone()
        conn.close()
        if prof:
            session['professor_id'] = prof['id']
            session['professor_email'] = prof['email']
            # Se for admin, marca na sessão
            if prof['email'] == '01099080150' and prof['senha'] == 'brasilia85DF':
                session['is_admin'] = True
            else:
                session['is_admin'] = False
            return redirect(url_for('dashboard', professor_id=prof['id']))
        else:
            flash('Login inválido!')
    return render_template('index.html')

# Dashboard do professor
@app.route('/dashboard/<int:professor_id>')
def dashboard(professor_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM avaliacao WHERE professor_id = %s', (professor_id,))
    avaliacoes = cur.fetchall()
    professores = []
    if session.get('is_admin'):
        cur.execute("SELECT * FROM professor WHERE email != %s", ('01099080150',))
        professores = cur.fetchall()
    conn.close()
    return render_template('dashboard.html', professor_id=professor_id, avaliacoes=avaliacoes, professores=professores)

# Criar nova avaliação
@app.route('/novo/<int:professor_id>', methods=['GET', 'POST'])
def nova_avaliacao(professor_id):
    if request.method == 'POST':
        titulo = request.form['titulo']
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO avaliacao (professor_id, titulo, data_criacao) VALUES (%s, %s, %s)',
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
        cur.execute('INSERT INTO questao (avaliacao_id, enunciado, suporte_texto, suporte_imagem, comando, imagem, valor) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (avaliacao_id, enunciado, suporte_texto, suporte_imagem, comando, imagem, valor))
        questao_id = cur.lastrowid
        alternativas = request.form.getlist('alternativa')
        corretas = request.form.getlist('correta')
        for i, alt in enumerate(alternativas):
            cur.execute('INSERT INTO alternativa (questao_id, texto, correta) VALUES (%s, %s, %s)',
                        (questao_id, alt, str(i) in corretas))
        conn.commit()
        conn.close()
        flash('Questão adicionada!')
    # Buscar questões já adicionadas
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = %s', (avaliacao_id,))
    questoes = cur.fetchall()
    conn.close()
    return render_template('adicionar_questoes.html', avaliacao_id=avaliacao_id, questoes=questoes)

# Finalizar avaliação e gerar link
@app.route('/gerar_link/<int:avaliacao_id>')
def gerar_link(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT professor_id FROM avaliacao WHERE id = %s', (avaliacao_id,))
    row = cur.fetchone()
    professor_id = row['professor_id'] if row else 1
    link = url_for('responder_avaliacao', avaliacao_id=avaliacao_id, _external=True)
    return render_template('gerar_link.html', link=link, professor_id=professor_id)

# Aluno responde avaliação
@app.route('/responder/<int:avaliacao_id>', methods=['GET', 'POST'])
def responder_avaliacao(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM avaliacao WHERE id = %s', (avaliacao_id,))
    avaliacao = cur.fetchone()
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = %s', (avaliacao_id,))
    questoes = cur.fetchall()
    questoes_com_alternativas = []
    for q in questoes:
        cur.execute('SELECT * FROM alternativa WHERE questao_id = %s', (q['id'],))
        alternativas = cur.fetchall()
        questoes_com_alternativas.append({'questao': q, 'alternativas': alternativas})
    if request.method == 'POST':
        aluno_nome = request.form['aluno_nome']
        escola = request.form['escola']
        turma = request.form['turma']
        serie = request.form['serie']
        componente = request.form['componente']
        professor_nome = request.form['professor_nome']
        cur.execute('INSERT INTO resposta (avaliacao_id, aluno_nome, escola, turma, serie, componente, professor_nome, data_envio) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    (avaliacao_id, aluno_nome, escola, turma, serie, componente, professor_nome, datetime.now()))
        resposta_id = cur.lastrowid
        for q in questoes:
            alternativa_id = request.form.get(f'questao_{q["id"]}')
            if alternativa_id:
                cur.execute('INSERT INTO resposta_questao (resposta_id, questao_id, alternativa_id) VALUES (%s, %s, %s)',
                            (resposta_id, q['id'], alternativa_id))
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
    cur.execute('SELECT professor_id FROM avaliacao WHERE id = %s', (avaliacao_id,))
    row = cur.fetchone()
    professor_id = row['professor_id'] if row else 1
    cur.execute('SELECT * FROM resposta WHERE avaliacao_id = %s', (avaliacao_id,))
    respostas = cur.fetchall()
    resultados = []
    for resp in respostas:
        cur.execute('SELECT * FROM resposta_questao WHERE resposta_id = %s', (resp['id'],))
        respostas_questoes = cur.fetchall()
        acertos = 0
        total = 0
        for rq in respostas_questoes:
            cur.execute('SELECT correta, valor FROM alternativa JOIN questao ON alternativa.questao_id = questao.id WHERE alternativa.id = %s', (rq['alternativa_id'],))
            alt = cur.fetchone()
            if alt and alt['correta']:
                acertos += alt['valor']
            if alt:
                total += alt['valor']
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
    cur.execute('SELECT professor_id FROM avaliacao WHERE id = %s', (avaliacao_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        flash('Avaliação não encontrada!')
        return redirect(url_for('index'))
    professor_id = row['professor_id']
    # Excluir respostas e respostas_questao
    cur.execute('SELECT id FROM resposta WHERE avaliacao_id = %s', (avaliacao_id,))
    respostas = cur.fetchall()
    for r in respostas:
        cur.execute('DELETE FROM resposta_questao WHERE resposta_id = %s', (r['id'],))
    cur.execute('DELETE FROM resposta WHERE avaliacao_id = %s', (avaliacao_id,))
    # Excluir alternativas e questões
    cur.execute('SELECT id FROM questao WHERE avaliacao_id = %s', (avaliacao_id,))
    questoes = cur.fetchall()
    for q in questoes:
        cur.execute('DELETE FROM alternativa WHERE questao_id = %s', (q['id'],))
    cur.execute('DELETE FROM questao WHERE avaliacao_id = %s', (avaliacao_id,))
    # Excluir avaliação
    cur.execute('DELETE FROM avaliacao WHERE id = %s', (avaliacao_id,))
    conn.commit()
    conn.close()
    flash('Avaliação excluída com sucesso!')
    return redirect(url_for('dashboard', professor_id=professor_id))

@app.route('/resposta/<int:resposta_id>')
def resposta_detalhe(resposta_id):
    conn = get_db()
    cur = conn.cursor()
    # Buscar resposta e avaliação
    cur.execute('SELECT * FROM resposta WHERE id = %s', (resposta_id,))
    resposta = cur.fetchone()
    if not resposta:
        conn.close()
        flash('Resposta não encontrada!')
        return redirect(url_for('index'))
    avaliacao_id = resposta['avaliacao_id']
    # Buscar questões
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = %s', (avaliacao_id,))
    questoes = cur.fetchall()
    questoes_detalhe = []
    for q in questoes:
        cur.execute('SELECT * FROM alternativa WHERE questao_id = %s', (q['id'],))
        alternativas = cur.fetchall()
        cur.execute('SELECT alternativa_id FROM resposta_questao WHERE resposta_id = %s AND questao_id = %s', (resposta_id, q['id']))
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
        cur.execute('SELECT * FROM professor WHERE email = %s', (email,))
        if cur.fetchone():
            conn.close()
            flash('Já existe um professor com este email!')
            return render_template('cadastrar_professor.html')
        cur.execute('INSERT INTO professor (nome, email, senha) VALUES (%s, %s, %s)', (nome, email, senha))
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
    cur.execute('DELETE FROM alternativa WHERE questao_id = %s', (questao_id,))
    # Excluir a questão
    cur.execute('DELETE FROM questao WHERE id = %s', (questao_id,))
    conn.commit()
    conn.close()
    flash('Questão excluída com sucesso!')
    return redirect(url_for('adicionar_questoes', avaliacao_id=avaliacao_id))

@app.route('/excluir_professor/<int:professor_id>', methods=['POST'])
def excluir_professor(professor_id):
    if not session.get('is_admin'):
        flash('Acesso restrito ao administrador!')
        return redirect(url_for('index'))
    conn = get_db()
    cur = conn.cursor()
    # Não permite excluir o admin
    cur.execute("SELECT * FROM professor WHERE id = %s AND email != %s", (professor_id, '01099080150'))
    prof = cur.fetchone()
    if not prof:
        conn.close()
        flash('Professor não encontrado ou não pode ser excluído!')
        return redirect(url_for('dashboard', professor_id=session.get('professor_id')))
    cur.execute('DELETE FROM professor WHERE id = %s', (professor_id,))
    conn.commit()
    conn.close()
    flash('Professor excluído com sucesso!')
    return redirect(url_for('dashboard', professor_id=session.get('professor_id')))

@app.route('/visualizar_avaliacao/<int:avaliacao_id>')
def visualizar_avaliacao(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM avaliacao WHERE id = %s', (avaliacao_id,))
    avaliacao = cur.fetchone()
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = %s', (avaliacao_id,))
    questoes = cur.fetchall()
    questoes_com_alternativas = []
    for q in questoes:
        cur.execute('SELECT * FROM alternativa WHERE questao_id = %s', (q['id'],))
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
    cur.execute('SELECT * FROM resposta WHERE avaliacao_id = %s', (avaliacao_id,))
    respostas = cur.fetchall()
    pontuacoes = []
    nomes = []
    for resp in respostas:
        cur.execute('SELECT * FROM resposta_questao WHERE resposta_id = %s', (resp['id'],))
        respostas_questoes = cur.fetchall()
        acertos = 0
        total = 0
        for rq in respostas_questoes:
            cur.execute('SELECT correta, valor FROM alternativa JOIN questao ON alternativa.questao_id = questao.id WHERE alternativa.id = %s', (rq['alternativa_id'],))
            alt = cur.fetchone()
            if alt and alt['correta']:
                acertos += alt['valor']
            if alt:
                total += alt['valor']
        nomes.append(resp['aluno_nome'])
        pontuacoes.append(acertos)
    conn.close()
    return render_template('grafico_resultado.html', avaliacao_id=avaliacao_id, nomes=nomes, pontuacoes=pontuacoes)

@app.route('/analise_questoes/<int:avaliacao_id>')
def analise_questoes(avaliacao_id):
    conn = get_db()
    cur = conn.cursor()
    # Buscar todas as questões da avaliação
    cur.execute('SELECT * FROM questao WHERE avaliacao_id = %s', (avaliacao_id,))
    questoes = cur.fetchall()
    questoes_analise = []
    for questao in questoes:
        cur.execute('SELECT * FROM alternativa WHERE questao_id = %s', (questao['id'],))
        alternativas = cur.fetchall()
        alternativas_dados = []
        total_respostas = 0
        for alt in alternativas:
            cur.execute('SELECT COUNT(*) as total FROM resposta_questao WHERE questao_id = %s AND alternativa_id = %s', (questao['id'], alt['id']))
            count = cur.fetchone()['total']
            alternativas_dados.append({'id': alt['id'], 'texto': alt['texto'], 'total': count})
            total_respostas += count
        # Calcular porcentagem
        for alt in alternativas_dados:
            alt['porcentagem'] = (alt['total'] / total_respostas * 100) if total_respostas > 0 else 0
        questoes_analise.append({'questao': questao, 'alternativas': alternativas_dados})
    conn.close()
    return render_template('analise_questoes.html', questoes_analise=questoes_analise, avaliacao_id=avaliacao_id)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 
