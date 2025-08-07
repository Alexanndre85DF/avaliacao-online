import os
import firebase_admin
from firebase_admin import credentials, firestore
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

# Configuração do Firebase
def init_firebase():
    try:
        # Se já foi inicializado, não inicializa novamente
        firebase_admin.get_app()
    except ValueError:
        # Para desenvolvimento local, use arquivo de credenciais
        if os.path.exists('firebase-credentials.json'):
            cred = credentials.Certificate('firebase-credentials.json')
        elif os.getenv('FIREBASE_CREDENTIALS'):
            cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS'))
        else:
            # Use credenciais padrão para desenvolvimento
            cred = credentials.ApplicationDefault()
        
        firebase_admin.initialize_app(cred)

# Inicializar Firebase
init_firebase()
db = firestore.client()

# Função para obter dados do Firestore
def get_collection(collection_name):
    return db.collection(collection_name)

# Função para adicionar documento
def add_document(collection_name, data):
    doc_ref = db.collection(collection_name).add(data)
    return doc_ref[1].id

# Função para buscar documento por ID
def get_document(collection_name, doc_id):
    doc = db.collection(collection_name).document(doc_id).get()
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None

# Função para buscar documentos por campo
def get_documents_by_field(collection_name, field, value):
    docs = db.collection(collection_name).where(field, '==', value).stream()
    return [{'id': doc.id, **doc.to_dict()} for doc in docs]

# Função para atualizar documento
def update_document(collection_name, doc_id, data):
    db.collection(collection_name).document(doc_id).update(data)

# Função para deletar documento
def delete_document(collection_name, doc_id):
    db.collection(collection_name).document(doc_id).delete()

# Inicializar dados padrão
def init_default_data():
    # Verificar se já existe professor padrão
    profs = get_documents_by_field('professores', 'email', 'prof@escola.com')
    if not profs:
        add_document('professores', {
            'nome': 'Professor Padrão',
            'email': 'prof@escola.com',
            'senha': '1234'
        })
    
    # Verificar se já existe admin
    admins = get_documents_by_field('professores', 'email', '01099080150')
    if not admins:
        add_document('professores', {
            'nome': 'Administrador',
            'email': '01099080150',
            'senha': 'brasilia85DF'
        }) 

# Página inicial (login do professor)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        admin_cpfs = ['01099080150', '010.990.801-50', '010.990.80150', '010990801-50']
        if email.replace('.', '').replace('-', '') == '01099080150':
            email = '01099080150'

        profs = get_documents_by_field('professores', 'email', email)
        prof = None
        if profs:
            prof = profs[0]
            if prof['senha'] == senha:
                session['professor_id'] = prof['id']
                session['professor_email'] = prof['email']
                # Corrigir para garantir que is_admin sempre é setado
                if prof['email'] == '01099080150' and prof['senha'] == 'brasilia85DF':
                    session['is_admin'] = True
                else:
                    session['is_admin'] = False
                return redirect(url_for('dashboard', professor_id=prof['id']))
        
        flash("Login inválido!", "danger")
        return render_template('index.html')

    return render_template('index.html')

# Dashboard do professor
@app.route('/dashboard/<professor_id>') 
def dashboard(professor_id):
    avaliacoes = get_documents_by_field('avaliacoes', 'professor_id', professor_id)
    professores = []
    if session.get('is_admin'):
        profs = get_collection('professores').stream()
        professores = [{'id': doc.id, **doc.to_dict()} for doc in profs if doc.to_dict().get('email') != '01099080150']
    return render_template('dashboard.html', professor_id=professor_id, avaliacoes=avaliacoes, professores=professores)

# Criar nova avaliação
@app.route('/novo/<professor_id>', methods=['GET', 'POST'])
def nova_avaliacao(professor_id):
    if request.method == 'POST':
        titulo = request.form['titulo']
        avaliacao_id = add_document('avaliacoes', {
            'professor_id': professor_id,
            'titulo': titulo,
            'data_criacao': datetime.now().isoformat()
        })
        return redirect(url_for('adicionar_questoes', avaliacao_id=avaliacao_id))
    return render_template('nova_avaliacao.html', professor_id=professor_id)

# Adicionar questões
@app.route('/avaliacao/<avaliacao_id>', methods=['GET', 'POST'])
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
        
        questao_id = add_document('questoes', {
            'avaliacao_id': avaliacao_id,
            'enunciado': enunciado,
            'suporte_texto': suporte_texto,
            'suporte_imagem': suporte_imagem,
            'comando': comando,
            'imagem': imagem,
            'valor': valor
        })
        
        alternativas = request.form.getlist('alternativa')
        corretas = request.form.getlist('correta')
        for i, alt in enumerate(alternativas):
            add_document('alternativas', {
                'questao_id': questao_id,
                'texto': alt,
                'correta': str(i) in corretas
            })
        
        flash('Questão adicionada!')
    
    # Buscar questões já adicionadas
    questoes = get_documents_by_field('questoes', 'avaliacao_id', avaliacao_id)
    return render_template('adicionar_questoes.html', avaliacao_id=avaliacao_id, questoes=questoes)

# Finalizar avaliação e gerar link
@app.route('/gerar_link/<avaliacao_id>')
def gerar_link(avaliacao_id):
    avaliacao = get_document('avaliacoes', avaliacao_id)
    professor_id = avaliacao['professor_id'] if avaliacao else '1'
    link = url_for('responder_avaliacao', avaliacao_id=avaliacao_id, _external=True)
    return render_template('gerar_link.html', link=link, professor_id=professor_id)

# Aluno responde avaliação
@app.route('/responder/<avaliacao_id>', methods=['GET', 'POST'])
def responder_avaliacao(avaliacao_id):
    avaliacao = get_document('avaliacoes', avaliacao_id)
    questoes = get_documents_by_field('questoes', 'avaliacao_id', avaliacao_id)
    questoes_com_alternativas = []
    
    for q in questoes:
        alternativas = get_documents_by_field('alternativas', 'questao_id', q['id'])
        questoes_com_alternativas.append({'questao': q, 'alternativas': alternativas})
    
    if request.method == 'POST':
        aluno_nome = request.form['aluno_nome']
        escola = request.form['escola']
        turma = request.form['turma']
        serie = request.form['serie']
        componente = request.form['componente']
        professor_nome = request.form['professor_nome']
        
        resposta_id = add_document('respostas', {
            'avaliacao_id': avaliacao_id,
            'aluno_nome': aluno_nome,
            'escola': escola,
            'turma': turma,
            'serie': serie,
            'componente': componente,
            'professor_nome': professor_nome,
            'data_envio': datetime.now().isoformat()
        })
        
        for q in questoes:
            alternativa_id = request.form.get(f'questao_{q["id"]}')
            if alternativa_id:
                add_document('respostas_questoes', {
                    'resposta_id': resposta_id,
                    'questao_id': q['id'],
                    'alternativa_id': alternativa_id
                })
        
        flash('Respostas enviadas com sucesso!')
        return redirect(url_for('resposta_enviada'))
    
    return render_template('responder_avaliacao.html', avaliacao=avaliacao, questoes=questoes_com_alternativas)

@app.route('/resposta_enviada')
def resposta_enviada():
    return '<h2>Respostas enviadas! Obrigado por participar.</h2>'

# Professor vê resultados
@app.route('/resultado/<avaliacao_id>')
def resultado(avaliacao_id):
    avaliacao = get_document('avaliacoes', avaliacao_id)
    professor_id = avaliacao['professor_id'] if avaliacao else '1'
    respostas = get_documents_by_field('respostas', 'avaliacao_id', avaliacao_id)
    
    resultados = []
    for resp in respostas:
        respostas_questoes = get_documents_by_field('respostas_questoes', 'resposta_id', resp['id'])
        acertos = 0
        total = 0
        
        for rq in respostas_questoes:
            alternativa = get_document('alternativas', rq['alternativa_id'])
            if alternativa and alternativa.get('correta'):
                questao = get_document('questoes', rq['questao_id'])
                if questao:
                    acertos += questao.get('valor', 0)
            if alternativa:
                questao = get_document('questoes', rq['questao_id'])
                if questao:
                    total += questao.get('valor', 0)
        
        resultados.append({'resposta': resp, 'acertos': acertos, 'total': total})
    
    return render_template('resultado.html', resultados=resultados, professor_id=professor_id, avaliacao_id=avaliacao_id)

# Servir imagens de upload
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_default_data()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 