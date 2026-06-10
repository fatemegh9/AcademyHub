from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post, Like, Comment, Notification, CommentLike, Story, SavedPost
from django.db import models
from django.db.models import Q
from notes.models import Tag, Note
from accounts.models import User
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse


@login_required
def timeline(request):
    if not request.user.is_authenticated:
        # کاربر وارد نشده → لندینگ ساده
        context = {
            'total_notes': Note.objects.count(),
            'total_users': User.objects.count(),
            'total_posts': Post.objects.count(),
            'top_notes': Note.objects.order_by('-downloads_count')[:5],
            'popular_tags': Tag.objects.all()[:10],
        }
        return render(request, 'landing.html', context)
    
    # کاربر وارد شده → تایم‌لاین واقعی
    following_users = request.user.following.values_list('following', flat=True)
    posts = Post.objects.filter(
        models.Q(author=request.user) |
        models.Q(author__in=following_users)
    ).order_by('-created_at').distinct()
    
    recent_posts = Post.objects.all().order_by('-created_at')[:5]
    suggestions = User.objects.exclude(id=request.user.id)[:3]
    popular_tags = Tag.objects.annotate(note_count=models.Count('notes')).order_by('-note_count')[:10]
    
    context = {
        'posts': posts,
        'recent_posts': recent_posts,
        'suggestions': suggestions,
        'popular_tags': popular_tags,
    }
    return render(request, 'social/timeline.html', context)


@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        text = request.POST.get('text')
        if text:
            Comment.objects.create(user=request.user, post=post, text=text)
            messages.success(request, 'کامنت شما ثبت شد.')

            if request.user != post.author:
                Notification.objects.create(
                    user=post.author,
                    sender=request.user,
                    post=post,
                    notification_type='comment'
                )

    return redirect('timeline')

@login_required
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content', '')
        image = request.FILES.get('image')
        
        # حالا عکس اجباری است
        if not image:
            messages.error(request, 'لطفاً یک عکس برای پست خود انتخاب کنید.')
            return render(request, 'social/create_post.html')
        
        # ایجاد پست با عکس و متن (کپشن)
        post = Post.objects.create(
            author=request.user,
            content=content,  # این همان کپشن است
            image=image
        )
        messages.success(request, 'پست شما با موفقیت منتشر شد.')
        return redirect('timeline')
    
    return render(request, 'social/create_post.html')

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    if request.method == 'POST':
        # ویرایش متن
        content = request.POST.get('content')
        if content:
            post.content = content
        
        # حذف عکس اگر کاربر تیک زده باشد
        if request.POST.get('delete_image') == 'on':
            if post.image:
                post.image.delete()
                post.image = None
        
        # آپلود عکس جدید
        if request.FILES.get('image'):
            # حذف عکس قدیمی
            if post.image:
                post.image.delete()
            post.image = request.FILES['image']
        
        post.save()
        messages.success(request, 'پست با موفقیت ویرایش شد.')
        return redirect('timeline')
    
    return render(request, 'social/edit_post.html', {'post': post})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author == request.user or request.user.is_superuser:
        post.delete()
        messages.success(request, 'پست حذف شد.')
    else:
        messages.error(request, 'شما اجازه حذف این پست را ندارید.')
    return redirect('timeline')


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # بررسی اینکه آیا کاربر قبلاً لایک کرده یا نه
    existing_like = Like.objects.filter(user=request.user, post=post).first()
    
    if existing_like:
        # اگر قبلاً لایک کرده بود، لایک را بردار
        existing_like.delete()
        # حذف نوتیفیکیشن مربوطه
        Notification.objects.filter(
            user=post.author,
            sender=request.user,
            post=post,
            notification_type='like'
        ).delete()
    else:
        # لایک جدید
        Like.objects.create(user=request.user, post=post)
        # ایجاد نوتیفیکیشن (اگر لایک‌کننده خود نویسنده نباشد)
        if request.user != post.author:
            Notification.objects.create(
                user=post.author,
                sender=request.user,
                post=post,
                notification_type='like'
            )
    
    return redirect('timeline')

@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    return render(request, 'social/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')

@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # بررسی اینکه آیا کاربر قبلاً لایک کرده یا نه
    existing_like = CommentLike.objects.filter(user=request.user, comment=comment).first()
    
    if existing_like:
        existing_like.delete()  # حذف لایک
    else:
        CommentLike.objects.create(user=request.user, comment=comment)  # اضافه کردن لایک
        # (اختیاری) ایجاد نوتیفیکیشن برای نویسنده کامنت
        if request.user != comment.user:
            Notification.objects.create(
                user=comment.user,
                sender=request.user,
                post=comment.post,
                notification_type='comment_like'
            )
    
    return redirect('timeline')

@login_required
def create_story(request):
    if request.method == "POST":
        text = request.POST.get('text', '')
        image = request.FILES.get('image')

        if image or text:
            story = Story.objects.create(
                user=request.user,
                text=text,
                image=image,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            messages.success(request, 'استوری با موفقیت منتشر شد.')
        else:
            messages.error(request, 'حداقل یک متن یا عکس برای استوری وارد کنید.')  

    
    return redirect('timeline')

@login_required
def story_list_api(request):
    following_users = list(request.user.following.values_list('following', flat=True))
    
    if request.user.id not in following_users:
        following_users.append(request.user.id)
    
    # فقط استوری‌های ۲۴ ساعت اخیر
    time_threshold = timezone.now() - timedelta(hours=24)
    
    stories = Story.objects.filter(
        user_id__in=following_users,
        created_at__gte=time_threshold  # ← این خط را حتماً اضافه کن
    ).select_related('user').order_by('-created_at')
    
    stories_by_user = {}
    for story in stories:
        if story.user.id not in stories_by_user:
            stories_by_user[story.user.id] = {
                'user': {
                    'username': story.user.username,
                    'profile_picture': story.user.profile_picture.url if story.user.profile_picture else '/media/profiles/default.png',
                },
                'stories': []
            }
        stories_by_user[story.user.id]['stories'].append({
            'image': story.image.url if story.image else None,
            'text': story.text,
            'id': story.id,
            'created_at': story.created_at.isoformat(),
        })
    
    return JsonResponse(stories_by_user, safe=False)


@login_required
def my_stories_api(request):
    time_threshold = timezone.now() - timedelta(hours=24)
    
    stories = Story.objects.filter(
        user=request.user,
        created_at__gte=time_threshold
    ).order_by('-created_at')
    
    stories_data = []
    for story in stories:
        stories_data.append({
            'image': story.image.url if story.image else None,
            'text': story.text,
            'created_at': story.created_at.isoformat(),
            'id': story.id,
        })
    
    return JsonResponse({
        'stories': stories_data,
        'username': request.user.username,
        'profile_picture': request.user.profile_picture.url if request.user.profile_picture else '/media/profiles/default.png'
    })
    
@login_required
def delete_story(request, story_id):
    if request.method == 'POST':
        story = get_object_or_404(Story, id=story_id)
        
        # فقط صاحب استوری می‌تواند حذف کند
        if story.user == request.user:
            # حذف فایل عکس از سرور
            if story.image:
                story.image.delete()
            story.delete()
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


@login_required
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    saved, created = SavedPost.objects.get_or_create(user=request.user, post=post)
    
    if created:
        messages.success(request, 'پست به لیست ذخیره شده‌ها اضافه شد.')
    else:
        messages.info(request, 'این پست قبلاً ذخیره شده است.')
    
    return redirect('timeline')

@login_required
def unsave_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    SavedPost.objects.filter(user=request.user, post=post).delete()
    messages.success(request, 'پست از لیست ذخیره شده‌ها حذف شد.')
    return redirect('timeline')


def get_post_json(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return JsonResponse({
        'content': post.content,
        'image': post.image.url if post.image else None,
        'author_name': post.author.username,
        'author_avatar': post.author.profile_picture.url if post.author.profile_picture else '/media/profiles/default.png',
        'likes_count': post.likes.count(),
        'comments_count': post.comments.count(),
        'created_at': post.created_at.strftime('%Y/%m/%d %H:%M'),
    })

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    related_posts = Post.objects.filter(
        author=post.author
    ).exclude(id=post.id)[:6]
    context = {
        'post': post
    }


    return render(request, "social/post.html" , context)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user:
        return JsonResponse({"error": "forbidden"}, status=403)

    comment.delete()
    return JsonResponse({"success": True})