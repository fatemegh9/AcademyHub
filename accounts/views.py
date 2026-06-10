from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import User, Follow
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm
from notes.models import Note
from social.models import Post

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        student_id = request.POST['student_id']
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            student_id=student_id
        )
        login(request, user)
        return redirect('home')
    return render(request, 'accounts/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'نام کاربری یا رمز اشتباه است')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request, username=None):
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user
    
    user_notes = Note.objects.filter(uploaded_by=profile_user).order_by('-created_at')[:5]
    user_posts = Post.objects.filter(author=profile_user).order_by('-created_at')[:5]
    
    context = {
        'profile_user': profile_user,
        'user': request.user,
        'user_notes': Note.objects.filter(uploaded_by=profile_user)[:5],
        'user_posts': Post.objects.filter(author=profile_user)[:5],
        'is_owner': request.user == profile_user,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'پروفایل شما با موفقیت به‌روزرسانی شد.')
            return redirect('profile_view', username=request.user.username)
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    
    if request.user != user_to_follow:
        Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
        messages.success(request, f'شما {username} را دنبال می‌کنید.')
    else:
        messages.error(request, 'نمی‌توانید خودتان را دنبال کنید.')
    
    return redirect('profile_view', username=username)

@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    
    Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
    messages.success(request, f'دنبال کردن {username} را متوقف کردید.')
    
    return redirect('profile_view', username=username)