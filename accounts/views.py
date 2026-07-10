from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from .models import User, Follow
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm
from notes.models import Note
from social.models import Post
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from datetime import datetime, timedelta
from django.utils import timezone
import json


def register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        university = request.POST.get('university', '')
        major = request.POST.get('major', '')
        student_id = request.POST.get('student_id', '') or None
        bio = request.POST.get('bio', '')
        phone = request.POST.get('phone', '')

        if password1 != password2:
            messages.error(request, 'رمزهای عبور یکسان نیستند.')
            return render(request, 'register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'این ایمیل قبلاً ثبت شده.')
            return render(request, 'register.html')

        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=username,
            password=password1,
            email=email,
            first_name=first_name,
            last_name=last_name,
            student_id=student_id,
            field_of_study=major,
            bio=bio,
            university=university,
            phone=phone,
        )

        if 'avatar' in request.FILES:
            user.profile_picture = request.FILES['avatar']
            user.save()

        login(request, user)
        request.session.set_expiry(60 * 60 * 24 * 30)
        return redirect('timeline')

    return render(request, 'register.html')


def landing_view(request):
    if request.user.is_authenticated:
        return redirect('timeline')
    return render(request, 'landing.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('timeline')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            request.session.set_expiry(60 * 60 * 24 * 30)
            return redirect('timeline')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request, username=None):
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user

    user_notes = Note.objects.filter(uploaded_by=profile_user)[:5]
    user_posts = Post.objects.filter(author=profile_user)

    # ✅ نقشه فعالیت — 26 هفته گذشته
    today = timezone.now().date()
    start_date = today - timedelta(weeks=26)

    posts_by_date = {}
    notes_by_date = {}

    for post in Post.objects.filter(author=profile_user, created_at__date__gte=start_date):
        d = str(post.created_at.date())
        posts_by_date[d] = posts_by_date.get(d, 0) + 1

    for note in Note.objects.filter(uploaded_by=profile_user, created_at__date__gte=start_date):
        d = str(note.created_at.date())
        notes_by_date[d] = notes_by_date.get(d, 0) + 1

    activity_data = {}
    current = start_date
    while current <= today:
        d = str(current)
        activity_data[d] = posts_by_date.get(d, 0) + notes_by_date.get(d, 0)
        current += timedelta(days=1)

    context = {
        'profile_user': profile_user,
        'user': request.user,
        'user_notes': user_notes,
        'user_posts': user_posts,
        'is_owner': request.user == profile_user,
        'activity_data': json.dumps(activity_data),  # ✅
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        print("FILES =", request.FILES)

        form = UserProfileForm(request.POST, request.FILES, instance=request.user)

        print("VALID =", form.is_valid())
        print(form.errors)

        if form.is_valid():
            user = form.save()

            print("Saved:", user.profile_picture)
            print("Name:", user.profile_picture.name)
            print("URL:", user.profile_picture.url)

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


User = get_user_model()


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(f'/accounts/reset/{uid}/{token}/')
            send_mail(
                'بازیابی رمز عبور',
                f'برای تغییر رمز عبور خود روی لینک زیر کلیک کنید:\n{reset_link}',
                'noreply@academichub.com',
                [email],
            )
        messages.success(request, 'اگر این ایمیل ثبت شده باشد، لینک بازیابی ارسال شد.')
        return redirect('login')
    return render(request, 'accounts/forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            user.set_password(password)
            user.save()
            messages.success(request, 'رمز عبور با موفقیت تغییر یافت.')
            return redirect('login')
        return render(request, 'accounts/reset_password.html')

    messages.error(request, 'لینک نامعتبر یا منقضی شده است.')
    return redirect('login')


@login_required
def leaderboard(request):
    top_users = User.objects.all().order_by('-xp')[:50]
    return render(request, 'accounts/leaderboard.html', {'top_users': top_users})


import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseForbidden

User = get_user_model()


def create_superuser(request):
    token = request.GET.get("token")

    if token != settings.SUPERUSER_SETUP_TOKEN:
        return HttpResponseForbidden("403 Forbidden")

    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse("A superuser already exists.")

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

    User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
    )

    return HttpResponse("Superuser created successfully.")