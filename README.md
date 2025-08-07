# Sistema de Avaliação Online - TesteOn

Sistema de criação e aplicação de avaliações online com Firebase e deploy no Netlify.

## 🚀 Configuração

### 1. Configurar Firebase

1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Crie um novo projeto
3. Ative o Firestore Database
4. Vá em Configurações do Projeto > Contas de serviço
5. Gere uma nova chave privada (JSON)
6. Salve o arquivo como `firebase-credentials.json` na raiz do projeto

### 2. Configurar Variáveis de Ambiente

Para produção (Netlify), configure as variáveis de ambiente:
- `FIREBASE_CREDENTIALS`: Conteúdo do arquivo JSON do Firebase

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Executar Localmente

```bash
python app_firebase.py
```

Acesse: `http://localhost:5000`

## 🔐 Credenciais de Acesso

### Professor Padrão:
- **Email:** `prof@escola.com`
- **Senha:** `1234`

### Administrador:
- **Email:** `01099080150`
- **Senha:** `brasilia85DF`

## 📦 Deploy no Netlify

1. Conecte seu repositório GitHub ao Netlify
2. Configure as variáveis de ambiente no Netlify:
   - `FIREBASE_CREDENTIALS`: Conteúdo do arquivo JSON do Firebase
3. Deploy automático será feito a cada push

## 🗄️ Estrutura do Banco (Firestore)

### Collections:
- `professores`: Dados dos professores
- `avaliacoes`: Avaliações criadas
- `questoes`: Questões das avaliações
- `alternativas`: Alternativas das questões
- `respostas`: Respostas dos alunos
- `respostas_questoes`: Relacionamento entre respostas e questões

## 🔧 Funcionalidades

- ✅ Login de professores
- ✅ Criação de avaliações
- ✅ Adição de questões com imagens
- ✅ Geração de links para alunos
- ✅ Sistema de respostas
- ✅ Visualização de resultados
- ✅ Análise de questões
- ✅ Gráficos de desempenho
- ✅ Upload de imagens
- ✅ Interface responsiva 