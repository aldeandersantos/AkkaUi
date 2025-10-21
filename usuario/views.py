from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import CustomUser

@require_http_methods(["GET", "POST"])
def signup(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Validation
        errors = []
        
        if not username:
            errors.append('Nome de usuário é obrigatório.')
        elif len(username) < 3:
            errors.append('Nome de usuário deve ter no mínimo 3 caracteres.')
        elif CustomUser.objects.filter(username=username).exists():
            errors.append('Este nome de usuário já está em uso.')
            
        if not email:
            errors.append('Email é obrigatório.')
        elif CustomUser.objects.filter(email=email).exists():
            errors.append('Este email já está cadastrado.')
            
        if not password:
            errors.append('Senha é obrigatória.')
        elif len(password) < 6:
            errors.append('A senha deve ter no mínimo 6 caracteres.')
            
        if password != password_confirm:
            errors.append('As senhas não coincidem.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'usuario/signup.html', {
                'username': username,
                'email': email,
                'phone': phone,
            })
        
        # Create user
        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            if phone:
                user.phone = phone
                user.save()
            
            # Log the user in
            login(request, user)
            messages.success(request, f'Bem-vindo, {username}! Sua conta foi criada com sucesso.')
            return redirect('core:home')
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {str(e)}')
    
    return render(request, 'usuario/signup.html')

@require_http_methods(["GET", "POST"])
def signin(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return render(request, 'usuario/signin.html', {'username': username})
        
        # Authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo de volta, {username}!')
            # Redirect to next parameter or home (with validation)
            next_url = request.GET.get('next', '')
            # Only allow relative URLs to prevent open redirect vulnerability
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('core:home')
        else:
            messages.error(request, 'Nome de usuário ou senha incorretos.')
            return render(request, 'usuario/signin.html', {'username': username})
    
    return render(request, 'usuario/signin.html')

def signout(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'Você saiu da sua conta com sucesso.')
    return redirect('core:home')

@login_required
def profile(request):
    """User profile view."""
    return render(request, 'usuario/profile.html')
