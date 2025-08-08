# 🚀 Deploy no Render - TesteOn Firebase

## 📋 Passos para Deploy

### 1. **Criar conta no Render**
- Acesse: https://render.com
- Faça login com GitHub
- Conecte seu repositório

### 2. **Criar novo Web Service**
- Clique em "New +" → "Web Service"
- Conecte seu repositório GitHub
- Nome: `testeon-app`
- Branch: `main`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app_firebase:app`

### 3. **Configurar Variáveis de Ambiente**
No Render Dashboard, vá em "Environment" e adicione:

```
SECRET_KEY = sua_chave_secreta_aqui
FIREBASE_PRIVATE_KEY_ID = AIzaSyB01EzL2foQZZtuRYtzk0DWQOadUhORw1s
FIREBASE_PRIVATE_KEY = -----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA_AQUI\n-----END PRIVATE KEY-----\n
FIREBASE_CLIENT_EMAIL = firebase-adminsdk-xxxxx@testeon-1e5e4.iam.gserviceaccount.com
FIREBASE_CLIENT_ID = 123456789012345678901
FIREBASE_CLIENT_X509_CERT_URL = https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40testeon-1e5e4.iam.gserviceaccount.com
```

### 4. **Obter as credenciais do Firebase**
1. Vá em: https://console.firebase.google.com/
2. Selecione: `testeon-1e5e4`
3. Vá em: Project Settings → Service Accounts
4. Clique em: "Generate new private key"
5. Baixe o JSON e copie os valores

### 5. **Fazer Deploy**
- Clique em "Create Web Service"
- Aguarde o build (2-3 minutos)
- O app ficará disponível em: `https://testeon-app.onrender.com`

## 🔧 Configuração do Firebase

### **Adicionar domínio autorizado:**
1. Firebase Console → Authentication → Settings
2. Adicione: `testeon-app.onrender.com`

### **Testar:**
1. Acesse: `https://testeon-app.onrender.com`
2. Clique em "Entrar com Google"
3. Deve funcionar perfeitamente!

## ✅ Vantagens do Render:
- HTTPS automático
- Domínio público
- Sem restrições de localhost
- Firebase aceita automaticamente

## 🎯 Próximos passos:
1. Fazer deploy
2. Testar login Google
3. Se funcionar, configurar domínio personalizado
4. Produção completa! 