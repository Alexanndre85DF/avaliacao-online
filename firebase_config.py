import os
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    """Inicializa o Firebase com as credenciais apropriadas"""
    try:
        # Se já foi inicializado, não inicializa novamente
        firebase_admin.get_app()
        return firestore.client()
    except ValueError:
        # Para desenvolvimento local
        if os.path.exists('firebase-credentials.json'):
            cred = credentials.Certificate('firebase-credentials.json')
        elif os.getenv('FIREBASE_CREDENTIALS'):
            cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS'))
        else:
            # Use credenciais padrão para desenvolvimento
            cred = credentials.ApplicationDefault()
        
        firebase_admin.initialize_app(cred)
        return firestore.client()

def get_db():
    """Retorna a instância do Firestore"""
    return init_firebase() 