import firebase_admin
from firebase_admin import credentials, firestore, auth
import os

# Configuração do Firebase
FIREBASE_CONFIG = {
    "type": "service_account",
    "project_id": "testeon-1e5e4",
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n") if os.getenv("FIREBASE_PRIVATE_KEY") else None,
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
}

# Inicializar Firebase Admin SDK
def initialize_firebase():
    try:
        # Verificar se já foi inicializado
        firebase_admin.get_app()
    except ValueError:
        # Criar credenciais
        cred = credentials.Certificate(FIREBASE_CONFIG)
        firebase_admin.initialize_app(cred)

# Obter instância do Firestore
def get_firestore():
    initialize_firebase()
    return firestore.client()

# Validar token do Firebase
def verify_id_token(id_token):
    try:
        initialize_firebase()
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Erro ao verificar token: {e}")
        return None

# Verificar se usuário é admin
def is_admin(uid):
    try:
        db = get_firestore()
        user_doc = db.collection('users').document(uid).get()
        if user_doc.exists:
            return user_doc.to_dict().get('is_admin', False)
        return False
    except Exception as e:
        print(f"Erro ao verificar admin: {e}")
        return False

# Bootstrap do usuário no Firestore
def bootstrap_user(uid, user_data):
    try:
        db = get_firestore()
        user_ref = db.collection('users').document(uid)
        
        # Verificar se usuário já existe
        if not user_ref.get().exists:
            # Criar usuário com dados básicos
            user_ref.set({
                'uid': uid,
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'is_admin': False,  # Por padrão, não é admin
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_login': firestore.SERVER_TIMESTAMP
            })
            print(f"Usuário {uid} criado no Firestore")
        else:
            # Atualizar último login
            user_ref.update({
                'last_login': firestore.SERVER_TIMESTAMP
            })
            print(f"Usuário {uid} já existe, atualizado último login")
        
        return True
    except Exception as e:
        print(f"Erro ao bootstrap usuário: {e}")
        return False 