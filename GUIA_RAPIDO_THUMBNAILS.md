# 🚀 GUIA RÁPIDO: Como Ver Thumbnails com PROD=True

## ✅ Solução Rápida (Funciona AGORA)

Para ver thumbnails funcionando **imediatamente** com `PROD=True`:

### Passo 1: Configure o arquivo `.env`

Crie ou edite `env/.env`:

```bash
PROD=True
USE_NGINX=False
SECRET_KEY=sua-chave-secreta-aqui
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Passo 2: Execute o script de verificação

```bash
python test_thumbnails.py
```

Este script mostra:
- ✓ Configuração atual
- ✓ Quantos SVGs têm thumbnails
- ✓ Se os arquivos existem
- ✓ URLs de exemplo

### Passo 3: Inicie o servidor

```bash
python manage.py runserver
```

### Passo 4: Teste no navegador

1. Acesse: `http://localhost:8000/`
2. Faça login
3. **Thumbnails devem aparecer!** 🎉

### O Que Você Verá nos Logs

```
WARNING - AVISO DE SEGURANÇA: Servindo thumbnail diretamente via Django em produção
(SVG ID: 123). Configure Nginx + X-Accel-Redirect para máxima segurança e performance.
```

Este warning é **normal** quando `USE_NGINX=False`. Ele indica que:
- ✅ Thumbnails estão funcionando
- ⚠️ Você deve configurar Nginx para produção final

---

## 🔒 Configuração de Produção Final (Máxima Segurança)

Depois de confirmar que thumbnails funcionam, configure o Nginx para segurança máxima:

### Passo 1: Configure o Nginx

```bash
# Copie o arquivo de configuração
sudo cp nginx_protected_media.conf /etc/nginx/sites-available/akkaui

# Edite e ajuste os caminhos
sudo nano /etc/nginx/sites-available/akkaui
# Altere: alias /path/to/your/project/media/;
# Para seu caminho real

# Ative a configuração
sudo ln -s /etc/nginx/sites-available/akkaui /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Passo 2: Atualize o `.env`

```bash
PROD=True
# Remove a linha USE_NGINX=False (ou deixe em branco)
```

### Passo 3: Restart

```bash
# Restart do servidor Django
# Thumbnails agora são servidas via Nginx (máxima segurança e performance)
```

---

## 📊 Comparação das Opções

| Aspecto | USE_NGINX=False | USE_NGINX=True |
|---------|----------------|----------------|
| **Funciona?** | ✅ Sim | ✅ Sim (com Nginx) |
| **Segurança** | ⚠️ Média | ✅ Máxima |
| **Performance** | ⚠️ Média | ✅ Alta |
| **Escalabilidade** | ⚠️ Limitada | ✅ Excelente |
| **Configuração** | ✅ Simples | ⚠️ Requer Nginx |
| **Recomendado para** | Teste/Debug | Produção |

---

## 🔍 Troubleshooting

### Thumbnails ainda não aparecem com USE_NGINX=False?

1. **Execute o script de diagnóstico:**
   ```bash
   python test_thumbnails.py
   ```

2. **Verifique se há SVGs com thumbnails:**
   - Acesse: `/admin/core/svgfile/`
   - Verifique se há SVGs cadastrados
   - Verifique se thumbnails foram enviadas

3. **Verifique permissões:**
   ```bash
   ls -la media/private/thumbnails/
   # Arquivos devem ser legíveis
   ```

4. **Verifique logs do Django:**
   ```bash
   # Procure por:
   # "Thumbnail servida diretamente via FileResponse"
   # ou
   # "AVISO DE SEGURANÇA"
   ```

### Erro 404 ou 403?

- **404**: Thumbnail não existe fisicamente
  - Verifique: `ls media/private/thumbnails/`
  - Faça upload de novos SVGs com thumbnails

- **403**: Problema de permissões
  - Verifique: `ls -la media/private/thumbnails/`
  - Corrija: `chmod 755 media/private/thumbnails/`

---

## 💡 Perguntas Frequentes

**P: Por que USE_NGINX=False funciona mas não é recomendado?**

R: Funciona perfeitamente para testes e pequenas aplicações, mas:
- Django não é otimizado para servir arquivos estáticos
- Consome recursos (workers) do Django
- Menos seguro (sem camada adicional do Nginx)
- Não escala bem com muitos usuários

**P: Posso usar USE_NGINX=False em produção?**

R: Tecnicamente sim, mas **não é recomendado**. Use apenas:
- Para testes
- Em aplicações pequenas (< 100 usuários)
- Temporariamente até configurar Nginx

**P: Como sei se Nginx está funcionando corretamente?**

R: Com `USE_NGINX=True`, verifique logs Django:
```
DEBUG - Thumbnail servida via X-Accel-Redirect para SVG ID: 123
```

Se ver este log mas thumbnails não aparecem, o Nginx não está configurado corretamente.

---

## 📞 Ajuda

- **Documentação completa**: Ver `guardian/README.md`
- **Configuração Nginx**: Ver `nginx_protected_media.conf`
- **Script de diagnóstico**: `python test_thumbnails.py`
