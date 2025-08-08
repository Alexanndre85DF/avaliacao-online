#!/usr/bin/env python3
"""
Script de teste para os endpoints REST do TesteOn Firebase
"""

import requests
import json
import sys

# Configuração
BASE_URL = "https://testeon-app.onrender.com"  # Substitua pela sua URL
TEST_EMAIL = "test@example.com"  # Email de teste

def print_separator(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def test_auth_endpoints():
    """Testar endpoints de autenticação"""
    print_separator("TESTE DE AUTENTICAÇÃO")
    
    # Teste 1: Verificar se a aplicação está rodando
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Aplicação rodando: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao acessar aplicação: {e}")
        return False
    
    # Teste 2: Verificar endpoint de check auth (deve retornar 401 sem token)
    try:
        response = requests.get(f"{BASE_URL}/api/auth/check")
        if response.status_code == 401:
            print("✅ Endpoint de verificação de auth funcionando (401 sem token)")
        else:
            print(f"⚠️ Status inesperado para check auth: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro no check auth: {e}")
    
    return True

def test_avaliacoes_endpoints():
    """Testar endpoints de avaliações (requer autenticação)"""
    print_separator("TESTE DE ENDPOINTS DE AVALIAÇÕES")
    
    # Teste sem autenticação (deve retornar 401)
    try:
        response = requests.get(f"{BASE_URL}/api/avaliacoes")
        if response.status_code == 401:
            print("✅ Proteção de autenticação funcionando (401 sem token)")
        else:
            print(f"⚠️ Status inesperado para avaliações sem auth: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar avaliações sem auth: {e}")

def test_redacoes_endpoints():
    """Testar endpoints de redações (requer autenticação)"""
    print_separator("TESTE DE ENDPOINTS DE REDAÇÕES")
    
    # Teste sem autenticação (deve retornar 401)
    try:
        response = requests.get(f"{BASE_URL}/api/redacoes")
        if response.status_code == 401:
            print("✅ Proteção de autenticação funcionando (401 sem token)")
        else:
            print(f"⚠️ Status inesperado para redações sem auth: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar redações sem auth: {e}")

def test_admin_endpoints():
    """Testar endpoints de admin (requer autenticação)"""
    print_separator("TESTE DE ENDPOINTS DE ADMIN")
    
    # Teste sem autenticação (deve retornar 401)
    try:
        response = requests.get(f"{BASE_URL}/api/admin/usuarios")
        if response.status_code == 401:
            print("✅ Proteção de autenticação funcionando (401 sem token)")
        else:
            print(f"⚠️ Status inesperado para admin sem auth: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar admin sem auth: {e}")

def test_with_session():
    """Testar com sessão simulada (requer configuração manual)"""
    print_separator("TESTE COM SESSÃO")
    
    print("⚠️ Para testar com autenticação, você precisa:")
    print("1. Fazer login manualmente no navegador")
    print("2. Copiar o cookie de sessão")
    print("3. Usar o cookie nos testes")
    print("\nExemplo de uso:")
    print("""
    # Com sessão válida
    cookies = {'session': 'seu_cookie_de_sessao_aqui'}
    
    # Testar listar avaliações
    response = requests.get(f"{BASE_URL}/api/avaliacoes", cookies=cookies)
    print(f"Avaliações: {response.json()}")
    
    # Testar criar avaliação
    data = {
        'titulo': 'Avaliação de Teste',
        'cabecalho': 'Instruções da avaliação'
    }
    response = requests.post(f"{BASE_URL}/api/avaliacoes", 
                           json=data, cookies=cookies)
    print(f"Criar avaliação: {response.json()}")
    """)

def generate_examples():
    """Gerar exemplos de uso dos endpoints"""
    print_separator("EXEMPLOS DE USO DOS ENDPOINTS")
    
    examples = {
        "Login com Google": """
// Frontend - Login
const idToken = await user.getIdToken();
const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idToken })
});
const data = await response.json();
""",
        
        "Criar Avaliação": """
// Criar avaliação
const response = await fetch('/api/avaliacoes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        titulo: 'Avaliação de Matemática',
        cabecalho: 'Instruções da avaliação'
    })
});
const data = await response.json();
console.log('Avaliação criada:', data.avaliacao_id);
""",
        
        "Listar Avaliações": """
// Listar avaliações do usuário
const response = await fetch('/api/avaliacoes');
const data = await response.json();
console.log('Avaliações:', data.avaliacoes);
""",
        
        "Criar Redação": """
// Criar redação
const response = await fetch('/api/redacoes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        titulo: 'Redação ENEM',
        texto_apoio: 'Texto de apoio...',
        comando: 'Comando da redação...',
        max_linhas: 30
    })
});
const data = await response.json();
console.log('Redação criada:', data.redacao_id);
""",
        
        "Ver Resultados": """
// Ver resultados de uma avaliação
const avaliacaoId = 'id_da_avaliacao';
const response = await fetch(`/api/avaliacoes/${avaliacaoId}/resultados`);
const data = await response.json();
console.log('Resultados:', data.resultados);
""",
        
        "Admin - Listar Usuários": """
// Listar usuários (apenas admin)
const response = await fetch('/api/admin/usuarios');
const data = await response.json();
console.log('Usuários:', data.usuarios);
""",
        
        "Admin - Tornar Usuário Admin": """
// Tornar usuário admin (apenas admin)
const userId = 'id_do_usuario';
const response = await fetch(`/api/admin/usuarios/${userId}/admin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_admin: true })
});
const data = await response.json();
console.log('Usuário atualizado:', data.success);
"""
    }
    
    for title, example in examples.items():
        print(f"\n📝 {title}")
        print(example)

def main():
    """Função principal"""
    print("🧪 TESTE DOS ENDPOINTS REST - TESTEON FIREBASE")
    print(f"URL Base: {BASE_URL}")
    
    # Executar testes
    if not test_auth_endpoints():
        print("❌ Testes de autenticação falharam")
        sys.exit(1)
    
    test_avaliacoes_endpoints()
    test_redacoes_endpoints()
    test_admin_endpoints()
    test_with_session()
    generate_examples()
    
    print_separator("RESUMO DOS TESTES")
    print("✅ Testes básicos de proteção de endpoints concluídos")
    print("⚠️ Para testes completos, configure autenticação manual")
    print("📚 Exemplos de uso gerados acima")
    print("\n🎯 Próximos passos:")
    print("1. Configure o Firebase seguindo o README_FIREBASE.md")
    print("2. Faça deploy no Render")
    print("3. Teste o login com Google")
    print("4. Teste os endpoints com autenticação")

if __name__ == "__main__":
    main() 