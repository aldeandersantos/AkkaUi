# Configuração de Internacionalização (i18n)

## Problema Identificado

Se você está recebendo um erro ao tentar fazer login em páginas com idiomas diferentes (como italiano, espanhol, etc.), o problema NÃO é relacionado ao CSRF, mas sim à falta de migrações do banco de dados.

### Erro Típico:
```
OperationalError at /it/usuario/signin/
no such table: usuario_customuser
```

## Solução

Execute os seguintes comandos para criar e aplicar as migrações necessárias:

```bash
# 1. Ativar o ambiente virtual (se estiver usando)
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 2. Criar as migrações do app usuario
python manage.py makemigrations usuario

# 3. Criar as migrações do app core
python manage.py makemigrations core

# 4. Aplicar todas as migrações
python manage.py migrate
```

## Funcionalidades Implementadas

✅ **5 idiomas suportados:**
- 🇺🇸 English (EN) - padrão
- 🇧🇷 Português (Brasil) (PT-BR)
- 🇪🇸 Español (ES)
- 🇮🇹 Italiano (IT)
- 🇨🇳 中文 (简体) (ZH-HANS)

✅ **Seletor de idioma no header** - Clique no botão 🌐 para trocar de idioma

✅ **URLs automáticas** - Cada idioma tem seu prefixo:
- Inglês: `/en/`
- Português: `/pt-br/`
- Espanhol: `/es/`
- Italiano: `/it/`
- Chinês: `/zh-hans/`

✅ **Traduções aplicadas** em:
- Navegação (Home, Explore, Pricing, FAQ)
- Botões (Sign In/Entrar/Iniciar sesión/Accedi)
- Footer
- Conteúdo da página inicial

## Como Usar

1. **Acesse a aplicação** - O idioma padrão é inglês
2. **Clique no botão 🌐** no canto superior direito
3. **Selecione o idioma desejado** no dropdown
4. **A página será recarregada** no idioma escolhido

## Para Desenvolvedores

### Adicionar novas traduções em templates existentes

1. Adicione `{% load i18n %}` no topo do template
2. Envolva textos traduzíveis em `{% trans "texto" %}`
3. Execute: `python manage.py makemessages -l pt_BR -l es -l it -l zh_Hans`
4. Edite os arquivos `.po` em `locale/[idioma]/LC_MESSAGES/django.po`
5. Compile: `python manage.py compilemessages`

### Verificar configuração

O sistema de i18n está configurado em:
- `server/settings.py` - Configurações de idioma e locale
- `server/urls.py` - URLs internacionalizadas com `i18n_patterns`
- `templates/core/base.html` - Seletor de idioma
- `locale/` - Arquivos de tradução

## Observações

- As migrations estão no `.gitignore` por padrão neste projeto
- Os arquivos `.mo` (compilados) também estão no `.gitignore`
- Cada desenvolvedor precisa executar `makemigrations` e `migrate` localmente
- Os arquivos `.po` (texto de traduções) SIM estão versionados no Git
