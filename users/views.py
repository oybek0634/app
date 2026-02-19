import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.conf import settings
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Post, Message

# Sizning formangiz (Email qo'shildi)
class EasySignupForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=True) # Email maydoni shart

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = ""

    def clean(self):
        cleaned_data = super().clean()
        for field in self.errors:
            for i, error in enumerate(self.errors[field]):
                if "too short" in error.lower():
                    self.errors[field][i] = "Parol juda qisqa (kamida 4 ta belgi bo'lsin)!"
                if "entirely numeric" in error.lower():
                    self.errors[field][i] = "Parol faqat raqamlardan iborat bo'lmasin!"
                if "common" in error.lower():
                    self.errors[field][i] = "Bu parol juda oddiy!"
        return cleaned_data

# POST LIST
def post_list(request):
    posts = Post.objects.filter(status='global').order_by('-created_at')
    return render(request, 'post_list.html', {'posts': posts})

# POST DETAIL
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'post_detail.html', {'post': post})

# MY POSTS
def my_posts(request):
    if not request.user.is_authenticated:
        return redirect('login') 
    posts = Post.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'my_posts.html', {'posts': posts})

# CREATE
def post_create(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == "POST":
        title = request.POST.get('title')
        content = request.POST.get('content')
        status = request.POST.get('status')
        Post.objects.create(author=request.user, title=title, content=content, status=status)
        return redirect('my_posts') 
    return render(request, 'post_form.html', {'title': 'Yangi post'})

# UPDATE
def post_update(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return HttpResponseForbidden("Siz faqat o'z postingizni tahrirlay olasiz!")
    if request.method == "POST":
        post.title = request.POST.get('title')
        post.content = request.POST.get('content')
        post.status = request.POST.get('status')
        post.save()
        return redirect('my_posts')
    return render(request, 'post_form.html', {'post': post, 'title': 'Postni tahrirlash'})

# DELETE
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return HttpResponseForbidden("Sizda o'chirish huquqi yo'q!")
    if request.method == "POST":
        post.delete()
        return redirect('my_posts')
    return render(request, 'post_confirm_delete.html', {'post': post})

# SIGNUP (Email kod yuborish bilan)
def signup(request):
    if request.method == "POST":
        form = EasySignupForm(request.POST)
        if form.is_valid():
            # Ma'lumotlarni vaqtinchalik sessionga saqlaymiz
            request.session['signup_data'] = request.POST.dict()
            
            # Tasdiqlash kodi
            verification_code = str(random.randint(100000, 999999))
            request.session['verification_code'] = verification_code
            
            # Email yuborish
            subject = "Sizning tasdiqlash kodingiz"
            message = f"Tasdiqlash kodingiz: {verification_code}"
            from_email = settings.EMAIL_HOST_USER
            to_email = form.cleaned_data['email']
            
            try:
                send_mail(subject, message, from_email, [to_email])
                return redirect('verify_email')
            except:
                messages.error(request, "Email yuborishda xatolik!")
    else:
        form = EasySignupForm()
    return render(request, 'signup.html', {'form': form})

# VERIFY EMAIL
def verify_email(request):
    if request.method == "POST":
        entered_code = request.POST.get('code')
        correct_code = request.session.get('verification_code')
        signup_data = request.session.get('signup_data')

        if entered_code == correct_code:
            form = EasySignupForm(signup_data)
            if form.is_valid():
                user = form.save()
                # Emailni foydalanuvchiga biriktirish
                user.email = signup_data.get('email')
                user.save()
                auth_login(request, user)
                # Sessionni tozalash
                del request.session['verification_code']
                del request.session['signup_data']
                return redirect('post_list')
        else:
            messages.error(request, "Kod noto'g'ri!")
    return render(request, 'verify_email.html')





def _chat_logic(request, other_user):
    current_user = request.user

    if other_user == current_user:
        messages.warning(request, "O'zingiz bilan chat qila olmaysiz.")
        return redirect('post_list')

    chat_messages = Message.objects.filter(
        Q(sender=current_user, recipient=other_user) |
        Q(sender=other_user, recipient=current_user)
    ).order_by('timestamp')

    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            Message.objects.create(
                sender=current_user,
                recipient=other_user,
                text=text
            )
            return redirect(request.path)

    return render(request, 'chat.html', {
        'other_user': other_user,
        'messages': chat_messages,
    })

@login_required
def chat_view(request, user_id):
    """Foydalanuvchi ID orqali chatga kirish"""
    other_user = get_object_or_404(User, id=user_id)
    return _chat_logic(request, other_user)

@login_required
def chat_view_post(request, post_id):
    """Post orqali muallif bilan chatga kirish"""
    post = get_object_or_404(Post, id=post_id)
    return _chat_logic(request, post.author)

