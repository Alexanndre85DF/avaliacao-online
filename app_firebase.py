import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify
from werkzeug.utils import secure_filename
from firebase_config import get_firestore, verify_id_token, is_admin, bootstrap_user
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'sua_chave_secreta_producao')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Garante que a pasta de uploads existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Decorator para verificar autenticação
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se há token na sessão
        if 'id_token' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        
        # Verificar token
        decoded_token = verify_id_token(session['id_token'])
        if not decoded_token:
            session.clear()
            return jsonify({'error': 'Token inválido'}), 401
        
        # Adicionar dados do usuário ao request
        request.user_uid = decoded_token['uid']
        request.user_email = decoded_token.get('email', '')
        request.user_name = decoded_token.get('name', '')
        request.is_admin = is_admin(decoded_token['uid'])
        
        return f(*args, **kwargs)
    return decorated_function

# Decorator para verificar se é admin
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'is_admin') or not request.is_admin:
            return jsonify({'error': 'Acesso negado - Admin necessário'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Página inicial com login Google
@app.route('/')
def index():
    return render_template('index_firebase.html')

# Rota para testar Firebase
@app.route('/test')
def test_firebase():
    return send_from_directory('.', 'test_firebase.html')

# Rota para testar backend simples
@app.route('/test-simple')
def test_simple():
    return send_from_directory('.', 'test_login_simple.html')

# Endpoint para autenticação
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        
        if not id_token:
            return jsonify({'error': 'Token não fornecido'}), 400
        
        # Verificar token
        decoded_token = verify_id_token(id_token)
        if not decoded_token:
            return jsonify({'error': 'Token inválido'}), 401
        
        uid = decoded_token['uid']
        user_data = {
            'email': decoded_token.get('email', ''),
            'name': decoded_token.get('name', ''),
            'picture': decoded_token.get('picture', '')
        }
        
        # Bootstrap do usuário no Firestore
        bootstrap_user(uid, user_data)
        
        # Criar sessão
        session['id_token'] = id_token
        session['user_uid'] = uid
        session['user_email'] = user_data['email']
        session['user_name'] = user_data['name']
        session['is_admin'] = is_admin(uid)
        
        return jsonify({
            'success': True,
            'user': {
                'uid': uid,
                'email': user_data['email'],
                'name': user_data['name'],
                'is_admin': session['is_admin']
            }
        })
        
    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Logout
@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

# Verificar autenticação
@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    if 'id_token' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    decoded_token = verify_id_token(session['id_token'])
    if not decoded_token:
        session.clear()
        return jsonify({'error': 'Token inválido'}), 401
    
    return jsonify({'success': True})

# Obter dados do usuário
@app.route('/api/auth/user', methods=['GET'])
@require_auth
def get_user():
    return jsonify({
        'user': {
            'uid': request.user_uid,
            'email': request.user_email,
            'name': request.user_name,
            'is_admin': request.is_admin
        }
    })

# Dashboard
@app.route('/dashboard')
@require_auth
def dashboard():
    return render_template('dashboard_firebase.html')

# Estatísticas
@app.route('/api/stats', methods=['GET'])
@require_auth
def get_stats():
    try:
        db = get_firestore()
        user_uid = request.user_uid
        
        # Contar respostas
        total_respostas = 0
        if request.is_admin:
            # Admin vê todas as respostas
            respostas_ref = db.collection('respostas')
            total_respostas += len(list(respostas_ref.stream()))
            
            respostas_redacao_ref = db.collection('respostas_redacao')
            total_respostas += len(list(respostas_redacao_ref.stream()))
        else:
            # Usuário vê apenas suas respostas
            avaliacoes_ref = db.collection('avaliacoes').where('ownerId', '==', user_uid)
            avaliacao_ids = [doc.id for doc in avaliacoes_ref.stream()]
            
            for avaliacao_id in avaliacao_ids:
                respostas_ref = db.collection('respostas').where('avaliacaoId', '==', avaliacao_id)
                total_respostas += len(list(respostas_ref.stream()))
            
            redacoes_ref = db.collection('redacoes').where('ownerId', '==', user_uid)
            redacao_ids = [doc.id for doc in redacoes_ref.stream()]
            
            for redacao_id in redacao_ids:
                respostas_ref = db.collection('respostas_redacao').where('redacaoId', '==', redacao_id)
                total_respostas += len(list(respostas_ref.stream()))
        
        # Contar usuários (apenas admin)
        total_usuarios = 0
        if request.is_admin:
            usuarios_ref = db.collection('users')
            total_usuarios = len(list(usuarios_ref.stream()))
        
        return jsonify({
            'total_respostas': total_respostas,
            'total_usuarios': total_usuarios
        })
        
    except Exception as e:
        print(f"Erro ao obter estatísticas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ===== ENDPOINTS REST PARA AVALIAÇÕES =====

# Listar avaliações do usuário
@app.route('/api/avaliacoes', methods=['GET'])
@require_auth
def list_avaliacoes():
    try:
        db = get_firestore()
        user_uid = request.user_uid
        
        # Se for admin, buscar todas as avaliações
        if request.is_admin:
            avaliacoes_ref = db.collection('avaliacoes')
        else:
            # Buscar apenas avaliações do usuário
            avaliacoes_ref = db.collection('avaliacoes').where('ownerId', '==', user_uid)
        
        avaliacoes = []
        for doc in avaliacoes_ref.stream():
            avaliacao = doc.to_dict()
            avaliacao['id'] = doc.id
            avaliacoes.append(avaliacao)
        
        return jsonify({'avaliacoes': avaliacoes})
        
    except Exception as e:
        print(f"Erro ao listar avaliações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Criar nova avaliação
@app.route('/api/avaliacoes', methods=['POST'])
@require_auth
def create_avaliacao():
    try:
        data = request.get_json()
        db = get_firestore()
        
        avaliacao_data = {
            'titulo': data.get('titulo', ''),
            'cabecalho': data.get('cabecalho', ''),
            'ownerId': request.user_uid,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        doc_ref = db.collection('avaliacoes').add(avaliacao_data)
        
        return jsonify({
            'success': True,
            'avaliacao_id': doc_ref[1].id
        })
        
    except Exception as e:
        print(f"Erro ao criar avaliação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Obter avaliação específica
@app.route('/api/avaliacoes/<avaliacao_id>', methods=['GET'])
@require_auth
def get_avaliacao(avaliacao_id):
    try:
        db = get_firestore()
        doc_ref = db.collection('avaliacoes').document(avaliacao_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Avaliação não encontrada'}), 404
        
        avaliacao = doc.to_dict()
        
        # Verificar permissão (admin pode ver tudo, usuário só suas)
        if not request.is_admin and avaliacao.get('ownerId') != request.user_uid:
            return jsonify({'error': 'Acesso negado'}), 403
        
        avaliacao['id'] = doc.id
        return jsonify({'avaliacao': avaliacao})
        
    except Exception as e:
        print(f"Erro ao obter avaliação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Atualizar avaliação
@app.route('/api/avaliacoes/<avaliacao_id>', methods=['PUT'])
@require_auth
def update_avaliacao(avaliacao_id):
    try:
        data = request.get_json()
        db = get_firestore()
        doc_ref = db.collection('avaliacoes').document(avaliacao_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Avaliação não encontrada'}), 404
        
        avaliacao = doc.to_dict()
        
        # Verificar permissão
        if not request.is_admin and avaliacao.get('ownerId') != request.user_uid:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Atualizar dados
        update_data = {
            'titulo': data.get('titulo', avaliacao.get('titulo', '')),
            'cabecalho': data.get('cabecalho', avaliacao.get('cabecalho', '')),
            'updated_at': datetime.now()
        }
        
        doc_ref.update(update_data)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Erro ao atualizar avaliação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Excluir avaliação
@app.route('/api/avaliacoes/<avaliacao_id>', methods=['DELETE'])
@require_auth
def delete_avaliacao(avaliacao_id):
    try:
        db = get_firestore()
        doc_ref = db.collection('avaliacoes').document(avaliacao_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Avaliação não encontrada'}), 404
        
        avaliacao = doc.to_dict()
        
        # Verificar permissão
        if not request.is_admin and avaliacao.get('ownerId') != request.user_uid:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Excluir avaliação e todas as questões relacionadas
        doc_ref.delete()
        
        # Excluir questões da avaliação
        questoes_ref = db.collection('questoes').where('avaliacaoId', '==', avaliacao_id)
        for questao_doc in questoes_ref.stream():
            questao_doc.reference.delete()
        
        # Excluir respostas da avaliação
        respostas_ref = db.collection('respostas').where('avaliacaoId', '==', avaliacao_id)
        for resposta_doc in respostas_ref.stream():
            resposta_doc.reference.delete()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Erro ao excluir avaliação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ===== ENDPOINTS REST PARA REDAÇÕES =====

# Listar redações do usuário
@app.route('/api/redacoes', methods=['GET'])
@require_auth
def list_redacoes():
    try:
        db = get_firestore()
        user_uid = request.user_uid
        
        # Se for admin, buscar todas as redações
        if request.is_admin:
            redacoes_ref = db.collection('redacoes')
        else:
            # Buscar apenas redações do usuário
            redacoes_ref = db.collection('redacoes').where('ownerId', '==', user_uid)
        
        redacoes = []
        for doc in redacoes_ref.stream():
            redacao = doc.to_dict()
            redacao['id'] = doc.id
            redacoes.append(redacao)
        
        return jsonify({'redacoes': redacoes})
        
    except Exception as e:
        print(f"Erro ao listar redações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Criar nova redação
@app.route('/api/redacoes', methods=['POST'])
@require_auth
def create_redacao():
    try:
        data = request.get_json()
        db = get_firestore()
        
        redacao_data = {
            'titulo': data.get('titulo', ''),
            'texto_apoio': data.get('texto_apoio', ''),
            'arquivo_apoio': data.get('arquivo_apoio', ''),
            'cabecalho': data.get('cabecalho', ''),
            'comando': data.get('comando', ''),
            'max_linhas': data.get('max_linhas', 30),
            'ownerId': request.user_uid,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        doc_ref = db.collection('redacoes').add(redacao_data)
        
        return jsonify({
            'success': True,
            'redacao_id': doc_ref[1].id
        })
        
    except Exception as e:
        print(f"Erro ao criar redação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Obter redação específica
@app.route('/api/redacoes/<redacao_id>', methods=['GET'])
@require_auth
def get_redacao(redacao_id):
    try:
        db = get_firestore()
        doc_ref = db.collection('redacoes').document(redacao_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Redação não encontrada'}), 404
        
        redacao = doc.to_dict()
        
        # Verificar permissão
        if not request.is_admin and redacao.get('ownerId') != request.user_uid:
            return jsonify({'error': 'Acesso negado'}), 403
        
        redacao['id'] = doc.id
        return jsonify({'redacao': redacao})
        
    except Exception as e:
        print(f"Erro ao obter redação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Atualizar redação
@app.route('/api/redacoes/<redacao_id>', methods=['PUT'])
@require_auth
def update_redacao(redacao_id):
    try:
        data = request.get_json()
        db = get_firestore()
        doc_ref = db.collection('redacoes').document(redacao_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Redação não encontrada'}), 404
        
        redacao = doc.to_dict()
        
        # Verificar permissão
        if not request.is_admin and redacao.get('ownerId') != request.user_uid:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Atualizar dados
        update_data = {
            'titulo': data.get('titulo', redacao.get('titulo', '')),
            'texto_apoio': data.get('texto_apoio', redacao.get('texto_apoio', '')),
            'arquivo_apoio': data.get('arquivo_apoio', redacao.get('arquivo_apoio', '')),
            'cabecalho': data.get('cabecalho', redacao.get('cabecalho', '')),
            'comando': data.get('comando', redacao.get('comando', '')),
            'max_linhas': data.get('max_linhas', redacao.get('max_linhas', 30)),
            'updated_at': datetime.now()
        }
        
        doc_ref.update(update_data)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Erro ao atualizar redação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Excluir redação
@app.route('/api/redacoes/<redacao_id>', methods=['DELETE'])
@require_auth
def delete_redacao(redacao_id):
    try:
        db = get_firestore()
        doc_ref = db.collection('redacoes').document(redacao_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Redação não encontrada'}), 404
        
        redacao = doc.to_dict()
        
        # Verificar permissão
        if not request.is_admin and redacao.get('ownerId') != request.user_uid:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Excluir redação e todas as respostas relacionadas
        doc_ref.delete()
        
        # Excluir respostas da redação
        respostas_ref = db.collection('respostas_redacao').where('redacaoId', '==', redacao_id)
        for resposta_doc in respostas_ref.stream():
            resposta_doc.reference.delete()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Erro ao excluir redação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ===== ENDPOINTS REST PARA RESPOSTAS =====

# Listar respostas de uma avaliação
@app.route('/api/avaliacoes/<avaliacao_id>/respostas', methods=['GET'])
@require_auth
def list_respostas_avaliacao(avaliacao_id):
    try:
        db = get_firestore()
        
        # Verificar se avaliação existe e usuário tem acesso
        avaliacao_ref = db.collection('avaliacoes').document(avaliacao_id)
        avaliacao_doc = avaliacao_ref.get()
        
        if not avaliacao_doc.exists:
            return jsonify({'error': 'Avaliação não encontrada'}), 404
        
        avaliacao = avaliacao_doc.to_dict()
        
        # Verificar permissão
        if not request.is_admin and avaliacao.get('ownerId') != request.user_uid:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Buscar respostas
        respostas_ref = db.collection('respostas').where('avaliacaoId', '==', avaliacao_id)
        respostas = []
        for doc in respostas_ref.stream():
            resposta = doc.to_dict()
            resposta['id'] = doc.id
            respostas.append(resposta)
        
        return jsonify({'respostas': respostas})
        
    except Exception as e:
        print(f"Erro ao listar respostas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Listar respostas de uma redação
@app.route('/api/redacoes/<redacao_id>/respostas', methods=['GET'])
@require_auth
def list_respostas_redacao(redacao_id):
    try:
        db = get_firestore()
        
        # Verificar se redação existe e usuário tem acesso
        redacao_ref = db.collection('redacoes').document(redacao_id)
        redacao_doc = redacao_ref.get()
        
        if not redacao_doc.exists:
            return jsonify({'error': 'Redação não encontrada'}), 404
        
        redacao = redacao_doc.to_dict()
        
        # Verificar permissão
        if not request.is_admin and redacao.get('ownerId') != request.user_uid:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Buscar respostas
        respostas_ref = db.collection('respostas_redacao').where('redacaoId', '==', redacao_id)
        respostas = []
        for doc in respostas_ref.stream():
            resposta = doc.to_dict()
            resposta['id'] = doc.id
            respostas.append(resposta)
        
        return jsonify({'respostas': respostas})
        
    except Exception as e:
        print(f"Erro ao listar respostas da redação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ===== ENDPOINTS REST PARA RESULTADOS =====

# Obter resultados de uma avaliação
@app.route('/api/avaliacoes/<avaliacao_id>/resultados', methods=['GET'])
@require_auth
def get_resultados_avaliacao(avaliacao_id):
    try:
        db = get_firestore()
        
        # Verificar se avaliação existe e usuário tem acesso
        avaliacao_ref = db.collection('avaliacoes').document(avaliacao_id)
        avaliacao_doc = avaliacao_ref.get()
        
        if not avaliacao_doc.exists:
            return jsonify({'error': 'Avaliação não encontrada'}), 404
        
        avaliacao = avaliacao_doc.to_dict()
        
        # Verificar permissão
        if not request.is_admin and avaliacao.get('ownerId') != request.user_uid:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Buscar respostas e calcular resultados
        respostas_ref = db.collection('respostas').where('avaliacaoId', '==', avaliacao_id)
        resultados = []
        
        for resposta_doc in respostas_ref.stream():
            resposta = resposta_doc.to_dict()
            
            # Buscar respostas das questões
            respostas_questoes_ref = db.collection('respostas_questoes').where('respostaId', '==', resposta_doc.id)
            acertos = 0
            total = 0
            
            for rq_doc in respostas_questoes_ref.stream():
                rq = rq_doc.to_dict()
                if rq.get('alternativaId'):  # questão objetiva
                    # Buscar alternativa para verificar se está correta
                    alt_ref = db.collection('alternativas').document(rq['alternativaId'])
                    alt_doc = alt_ref.get()
                    if alt_doc.exists and alt_doc.to_dict().get('correta'):
                        acertos += rq.get('valor', 0)
                    total += rq.get('valor', 0)
                else:  # questão subjetiva
                    if rq.get('corrigida') and rq.get('correta'):
                        acertos += rq.get('valor', 0)
                    total += rq.get('valor', 0)
            
            resultado = {
                'resposta_id': resposta_doc.id,
                'aluno_nome': resposta.get('aluno_nome'),
                'escola': resposta.get('escola'),
                'turma': resposta.get('turma'),
                'serie': resposta.get('serie'),
                'acertos': acertos,
                'total': total,
                'percentual': (acertos / total * 100) if total > 0 else 0
            }
            resultados.append(resultado)
        
        return jsonify({'resultados': resultados})
        
    except Exception as e:
        print(f"Erro ao obter resultados: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Obter resultados de uma redação
@app.route('/api/redacoes/<redacao_id>/resultados', methods=['GET'])
@require_auth
def get_resultados_redacao(redacao_id):
    try:
        db = get_firestore()
        
        # Verificar se redação existe e usuário tem acesso
        redacao_ref = db.collection('redacoes').document(redacao_id)
        redacao_doc = redacao_ref.get()
        
        if not redacao_doc.exists:
            return jsonify({'error': 'Redação não encontrada'}), 404
        
        redacao = redacao_doc.to_dict()
        
        # Verificar permissão
        if not request.is_admin and redacao.get('ownerId') != request.user_uid:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Buscar respostas da redação
        respostas_ref = db.collection('respostas_redacao').where('redacaoId', '==', redacao_id)
        resultados = []
        
        for doc in respostas_ref.stream():
            resposta = doc.to_dict()
            resposta['id'] = doc.id
            
            # Calcular nota final se corrigida
            if resposta.get('corrigida'):
                competencias = [
                    resposta.get('competencia1', 0),
                    resposta.get('competencia2', 0),
                    resposta.get('competencia3', 0),
                    resposta.get('competencia4', 0),
                    resposta.get('competencia5', 0)
                ]
                nota_final = sum(competencias)
                resposta['nota_final'] = nota_final
                resposta['competencias'] = competencias
            
            resultados.append(resposta)
        
        return jsonify({'resultados': resultados})
        
    except Exception as e:
        print(f"Erro ao obter resultados da redação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ===== ENDPOINTS ADMIN =====

# Listar todos os usuários (apenas admin)
@app.route('/api/admin/usuarios', methods=['GET'])
@require_auth
@require_admin
def list_usuarios():
    try:
        db = get_firestore()
        usuarios_ref = db.collection('users')
        usuarios = []
        
        for doc in usuarios_ref.stream():
            usuario = doc.to_dict()
            usuario['id'] = doc.id
            # Não retornar dados sensíveis
            usuario.pop('uid', None)
            usuarios.append(usuario)
        
        return jsonify({'usuarios': usuarios})
        
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Tornar usuário admin (apenas admin)
@app.route('/api/admin/usuarios/<user_id>/admin', methods=['POST'])
@require_auth
@require_admin
def set_user_admin(user_id):
    try:
        data = request.get_json()
        is_admin_user = data.get('is_admin', False)
        
        db = get_firestore()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        user_ref.update({
            'is_admin': is_admin_user,
            'updated_at': datetime.now()
        })
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Erro ao atualizar status admin: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Servir arquivos estáticos
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False) 