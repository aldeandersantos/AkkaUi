# Manual QA Test Guide - Cart & Toast Integration

## Objetivo
Validar a integração do sistema de notificações toast e melhorias no carrinho de compras.

## Pré-requisitos
- Navegador moderno (Chrome, Firefox, Safari, Edge)
- Console do desenvolvedor aberto para verificar erros
- LocalStorage limpo (opcional, para testar migração)

---

## 1. Testes do Sistema de Toast

### 1.1 Toast de Sucesso
**Passos:**
1. Navegar para página Home ou Explore
2. Clicar em "Adicionar ao Carrinho" em qualquer item
3. **Esperado:** Toast verde aparece no canto superior direito com mensagem "Item adicionado ao carrinho!"
4. **Verificar:** 
   - Animação suave de entrada (desliza da direita)
   - Ícone de check verde
   - Botão X para fechar
   - Toast desaparece automaticamente após 3 segundos

### 1.2 Toast de Erro
**Passos:**
1. Abrir página de administração (se admin)
2. Tentar copiar um SVG inválido
3. **Esperado:** Toast vermelho com mensagem de erro
4. **Verificar:** Ícone de erro e cor vermelha

### 1.3 Toast de Info/Warning
**Passos:**
1. Clicar no ícone de busca no header
2. **Esperado:** Toast azul com "Funcionalidade de busca em desenvolvimento"
3. Ir para checkout com carrinho vazio
4. **Esperado:** Toast amarelo/laranja de aviso

### 1.4 Acessibilidade
**Passos:**
1. Usar leitor de tela (NVDA/JAWS/VoiceOver)
2. Triggerar um toast
3. **Esperado:** Toast é anunciado automaticamente
4. Navegar com Tab até o botão X
5. **Esperado:** Botão é focável e tem label "Fechar notificação"

---

## 2. Testes do Carrinho de Compras

### 2.1 Adicionar Item ao Carrinho
**Passos:**
1. Navegar para Home ou Explore
2. Clicar em "Adicionar" em um SVG pago
3. **Esperado:**
   - Toast de sucesso aparece
   - Badge do carrinho no header mostra "1"
   - LocalStorage tem chave `akkaui_cart_v1`
4. Adicionar mais 2 itens diferentes
5. **Esperado:** Badge mostra "3"

### 2.2 Badge de Contagem
**Passos:**
1. Com itens no carrinho, verificar badge no header
2. **Esperado:**
   - Badge circular roxo (#7460F3) com número
   - Posicionado no canto superior direito do ícone do carrinho
   - Número atualiza em tempo real
3. Abrir carrinho e adicionar +1 quantidade
4. **Esperado:** Badge atualiza para "4"

### 2.3 Visualizar Carrinho
**Passos:**
1. Clicar em "Cart" no header
2. **Esperado:**
   - Lista de itens com thumbnail, nome, preço
   - Botões +/- para ajustar quantidade
   - Botão "Remove" para cada item
   - Total calculado corretamente
   - Botões "Clear Cart" e "Proceed to Checkout"

### 2.4 Aumentar/Diminuir Quantidade
**Passos:**
1. Na página do carrinho, clicar em "+" em um item
2. **Esperado:**
   - Quantidade aumenta imediatamente
   - Subtotal do item atualiza
   - Total geral atualiza
   - Badge no header atualiza
   - LocalStorage atualizado
3. Clicar em "-" até chegar em 1
4. **Esperado:** Quantidade mínima é 1 (não vai para 0)

### 2.5 Remover Item
**Passos:**
1. Clicar em "Remove" em um item
2. **Esperado:**
   - Toast "Item removido do carrinho" aparece
   - Item desaparece da lista
   - Total recalculado
   - Badge atualizado
   - LocalStorage atualizado
3. Remover todos os itens
4. **Esperado:**
   - Mensagem "Your cart is empty" aparece
   - Ícone grande de sacola vazia
   - Botão "Browse SVGs"
   - Badge desaparece (display: none)

### 2.6 Limpar Carrinho
**Passos:**
1. Com itens no carrinho, clicar "Clear Cart"
2. Confirmar no popup
3. **Esperado:**
   - Toast "Carrinho limpo" aparece
   - Todos itens removidos
   - Estado vazio exibido
   - Badge desaparece

### 2.7 Persistência do Carrinho
**Passos:**
1. Adicionar 2-3 itens ao carrinho
2. Recarregar a página (F5)
3. **Esperado:**
   - Badge mostra contagem correta
   - Carrinho mantém todos os itens
4. Fechar e reabrir o navegador
5. **Esperado:** Carrinho persiste

### 2.8 Migração de Dados Antigos
**Passos:**
1. Abrir DevTools → Application → LocalStorage
2. Criar manualmente chave `akka_cart` com dados: `[{"id":"test","name":"Test","price":10,"quantity":1}]`
3. Recarregar página
4. **Esperado:**
   - Dados migrados para `akkaui_cart_v1`
   - Chave antiga `akka_cart` removida
   - Badge mostra "1"
   - Carrinho funcional

---

## 3. Testes do Checkout

### 3.1 Fluxo de Checkout Completo
**Passos:**
1. Adicionar itens ao carrinho
2. Ir para carrinho e clicar "Proceed to Checkout"
3. **Esperado:**
   - Página de checkout carrega
   - Order Summary mostra todos os itens
   - Total correto exibido
4. Selecionar método de pagamento
5. **Esperado:** Opção selecionada destaca com borda roxa
6. Clicar "Complete Purchase"
7. **Esperado:**
   - Sem alert() antigo
   - Modal de sucesso aparece (se pagamento OK)
   - Carrinho é limpo após sucesso
   - Badge volta para 0

### 3.2 Validações de Checkout
**Passos:**
1. Ir para checkout com carrinho vazio (via URL direta)
2. **Esperado:** Redireciona para carrinho ou mostra toast de erro
3. Tentar finalizar sem selecionar método de pagamento
4. **Esperado:** Toast "Please select a payment method" (amarelo)

---

## 4. Testes de Responsividade

### 4.1 Mobile (< 480px)
**Passos:**
1. Redimensionar navegador para 375px de largura
2. **Esperado:**
   - Toasts ocupam largura total (com margens)
   - Cards do carrinho empilham verticalmente
   - Badge do carrinho visível e posicionado corretamente
   - Botões grandes e clicáveis

### 4.2 Tablet (768px)
**Passos:**
1. Redimensionar para 768px
2. **Esperado:**
   - Grid de produtos mostra 2 colunas
   - Carrinho mantém layout responsivo
   - Toasts no canto direito

### 4.3 Desktop (1280px+)
**Passos:**
1. Tela completa
2. **Esperado:**
   - Grid mostra 4 colunas
   - Toast max-width de 400px
   - Layout espaçado e confortável

---

## 5. Testes de Navegadores

### 5.1 Chrome/Edge
- [ ] Todos os testes acima
- [ ] LocalStorage funcional
- [ ] Animações suaves

### 5.2 Firefox
- [ ] Todos os testes acima
- [ ] Clipboard API funcional

### 5.3 Safari
- [ ] Todos os testes acima
- [ ] Backdrop-filter no header

---

## 6. Testes de Console

**Durante todos os testes, verificar:**
- [ ] Sem erros no console
- [ ] Sem warnings críticos
- [ ] Eventos `cartUpdated` disparados corretamente
- [ ] LocalStorage atualizado após cada ação

---

## 7. Checklist Final

### Funcionalidades
- [ ] Toast system funcionando (4 tipos)
- [ ] Cart badge atualiza em tempo real
- [ ] Adicionar ao carrinho funciona
- [ ] Quantidade +/- funciona
- [ ] Remover item funciona
- [ ] Limpar carrinho funciona
- [ ] Checkout flow sem alerts
- [ ] Persistência do carrinho
- [ ] Migração de dados antigos

### Design
- [ ] Paleta de cores mantida (#7460F3, #0c0c0c, #e7e7e7)
- [ ] Animações suaves
- [ ] Layout responsivo
- [ ] Tipografia consistente

### Acessibilidade
- [ ] ARIA labels presentes
- [ ] Navegação por teclado
- [ ] Foco visível
- [ ] Leitores de tela compatíveis
- [ ] Suporte a prefers-reduced-motion

### Performance
- [ ] LocalStorage usado eficientemente
- [ ] Sem vazamentos de memória
- [ ] Animações performáticas

---

## Bugs Conhecidos / Limitações

Nenhum bug conhecido no momento. Reportar qualquer issue encontrado.

---

## Notas para Desenvolvedores

### Debug do Cart
```javascript
// Console do navegador
console.log(cartManager.getCart());
console.log(cartManager.calculateTotals());
```

### Debug do Toast
```javascript
// Testar diferentes tipos
showToast('Test success', 'success');
showToast('Test error', 'error');
showToast('Test warning', 'warning');
showToast('Test info', 'info');
```

### Limpar LocalStorage
```javascript
// Console do navegador
localStorage.clear();
location.reload();
```

---

**Última atualização:** 2025-10-27  
**Versão:** 1.0  
**Testador:** _______________  
**Data do Teste:** _______________  
**Status:** [ ] Passou [ ] Falhou (detalhar abaixo)

**Observações:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
