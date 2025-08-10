# TesteOn - Versão Firebase

Esta é a versão de produção do TesteOn com autenticação Google e Firestore seguro.

## 🚀 Funcionalidades

- ✅ Login com Google (Firebase Auth)
- ✅ Autenticação segura com idToken
- ✅ Firestore com regras de segurança por usuário
- ✅ Cada usuário só vê seus próprios dados
- ✅ Admin pode ver e editar tudo
- ✅ Endpoints REST para CRUD completo
- ✅ Hospedagem no Render

## 📋 Pré-requisitos

1. **Conta no Firebase Console**
2. **Conta no Render** (para hospedagem)
3. **Python 3.8+**

## 🔧 Configuração do Firebase

### 1. Criar Projeto Firebase

1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Clique em "Adicionar projeto"
3. Nome: `testeon-app`
4. Ative o Google Analytics (opcional)
5. Clique em "Criar projeto"

### 2. Configurar Authentication

1. No Firebase Console, vá em "Authentication"
2. Clique em "Get started"
3. Vá na aba "Sign-in method"
4. Ative o "Google"
5. Configure o domínio autorizado (seu domínio do Render)

### 3. Configurar Firestore

1. No Firebase Console, vá em "Firestore Database"
2. Clique em "Create database"
3. Escolha "Start in test mode" (depois aplicaremos as regras)
4. Escolha a localização mais próxima (ex: us-central1)

### 4. Configurar Service Account

1. No Firebase Console, vá em "Project settings"
2. Vá na aba "Service accounts"
3. Clique em "Generate new private key"
4. Baixe o arquivo JSON
5. Copie os valores para as variáveis de ambiente

### 5. Aplicar Regras de Segurança

1. No Firebase Console, vá em "Firestore Database"
2. Clique na aba "Rules"
3. Substitua as regras pelo conteúdo do arquivo `firestore.rules`
4. Clique em "Publish"

## 🔑 Variáveis de Ambiente

Configure as seguintes variáveis no Render:

```bash
SECRET_KEY=sua_chave_secreta_muito_segura
FIREBASE_PRIVATE_KEY_ID=seu_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@testeon-app.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=123456789012345678901
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40testeon-app.iam.gserviceaccount.com
```

## 🚀 Deploy no Render

### 1. Conectar Repositório

1. Acesse [Render Dashboard](https://dashboard.render.com/)
2. Clique em "New +"
3. Escolha "Web Service"
4. Conecte seu repositório GitHub/GitLab

### 2. Configurar Serviço

- **Name**: `testeon-app`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app_firebase:app`

### 3. Configurar Variáveis

Adicione todas as variáveis de ambiente listadas acima.

### 4. Deploy

Clique em "Create Web Service" e aguarde o deploy.

## 📚 Estrutura do Projeto

```
TesteOn/
├── app_firebase.py          # App principal com Firebase
├── firebase_config.py       # Configuração do Firebase
├── firestore.rules          # Regras de segurança
├── templates/
│   ├── index_firebase.html  # Login com Google
│   └── dashboard_firebase.html # Dashboard
├── static/                  # Arquivos estáticos
├── requirements.txt         # Dependências
└── render.yaml             # Configuração Render
```

## 🔌 Endpoints REST

### Autenticação
- `POST /api/auth/login` - Login com Google
- `POST /api/auth/logout` - Logout
- `GET /api/auth/check` - Verificar autenticação
- `GET /api/auth/user` - Dados do usuário

### Avaliações
- `GET /api/avaliacoes` - Listar avaliações
- `POST /api/avaliacoes` - Criar avaliação
- `GET /api/avaliacoes/{id}` - Obter avaliação
- `PUT /api/avaliacoes/{id}` - Atualizar avaliação
- `DELETE /api/avaliacoes/{id}` - Excluir avaliação

### Redações
- `GET /api/redacoes` - Listar redações
- `POST /api/redacoes` - Criar redação
- `GET /api/redacoes/{id}` - Obter redação
- `PUT /api/redacoes/{id}` - Atualizar redação
- `DELETE /api/redacoes/{id}` - Excluir redação

### Respostas
- `GET /api/avaliacoes/{id}/respostas` - Respostas da avaliação
- `GET /api/redacoes/{id}/respostas` - Respostas da redação

### Resultados
- `GET /api/avaliacoes/{id}/resultados` - Resultados da avaliação
- `GET /api/redacoes/{id}/resultados` - Resultados da redação

### Admin (apenas admin)
- `GET /api/admin/usuarios` - Listar usuários
- `POST /api/admin/usuarios/{id}/admin` - Tornar usuário admin

## 🧪 Exemplos de Requisição

### Login
```javascript
// Frontend
const idToken = await user.getIdToken();
const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idToken })
});
```

### Criar Avaliação
```javascript
const response = await fetch('/api/avaliacoes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        titulo: 'Avaliação de Matemática',
        cabecalho: 'Instruções da avaliação'
    })
});
```

### Listar Avaliações
```javascript
const response = await fetch('/api/avaliacoes');
const data = await response.json();
console.log(data.avaliacoes);
```

### Criar Redação
```javascript
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
```

## 🔒 Segurança

### Regras do Firestore

- ✅ Apenas usuários logados acessam
- ✅ Usuário comum só acessa docs com `ownerId = uid`
- ✅ Admin acessa tudo
- ✅ Validação de permissões em cascata

### Autenticação

- ✅ Token JWT do Firebase
- ✅ Validação no backend
- ✅ Sessão segura
- ✅ Logout automático

## 👥 Controle de Acesso

### Usuário Comum
- ✅ Vê apenas suas avaliações/redações
- ✅ Cria avaliações/redações
- ✅ Vê resultados de suas avaliações
- ❌ Não vê dados de outros usuários

### Admin
- ✅ Vê todas as avaliações/redações
- ✅ Pode editar qualquer avaliação/redação
- ✅ Gerencia usuários
- ✅ Define outros admins

## 🐛 Troubleshooting

### Erro de Autenticação
- Verifique se o Firebase está configurado corretamente
- Confirme se as variáveis de ambiente estão setadas
- Verifique se o domínio está autorizado no Firebase

### Erro de Permissão
- Verifique se as regras do Firestore foram aplicadas
- Confirme se o usuário tem as permissões corretas
- Verifique se o `ownerId` está sendo setado corretamente

### Erro de Deploy
- Verifique se todas as dependências estão no `requirements.txt`
- Confirme se o comando de start está correto
- Verifique os logs do Render

## 📞 Suporte

Para dúvidas ou problemas:
- 📧 Email: tolentinoalexandre534@gmail.com
- 📱 WhatsApp: (63) 98500-9703

## 🎯 Próximos Passos

1. **Configurar Firebase** seguindo as instruções acima
2. **Configurar variáveis de ambiente** no Render
3. **Fazer deploy** usando o `render.yaml`
4. **Testar autenticação** e funcionalidades
5. **Configurar domínio personalizado** (opcional)

---

**Desenvolvido por Alexandre Tolentino**  
*TesteOn - Sua avaliação conectada ao futuro* 