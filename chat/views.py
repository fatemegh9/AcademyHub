from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from .models import Conversation, Message
from django.contrib import messages
from social.models import Notification
import uuid
from django.db.models import Max


User = get_user_model()


@login_required
def inbox(request):
    conversations = (
        request.user.conversations
        .annotate(last_message_at=Max('messages__created_at'))
        .order_by('-last_message_at')
        .distinct()
    )

    conv_list = []
    for conv in conversations:
        if conv.is_group:
            other_user = None
        else:
            other_user = conv.participants.exclude(id=request.user.id).first()
        last_message = conv.messages.last()
        unread_count = conv.messages.filter(is_read=False).exclude(sender=request.user).count()
        conv_list.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })

    return render(request, 'chat/inbox.html', {'conversations': conv_list})


@login_required
def start_conversation(request, username):
    print("START CONVERSATION CALLED")

    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        return redirect('inbox')

    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()

    if not conversation:
        print("CREATING PRIVATE CONVERSATION")
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)

    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

    if conversation.is_group:
        other_user = None
    else:
        other_user = conversation.participants.exclude(id=request.user.id).first()

    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    messages_list = conversation.messages.all()

    return render(request, 'chat/conversation_detail.html', {
        'conversation': conversation,
        'other_user': other_user,
        'messages_list': messages_list,
    })


@login_required
def send_message(request, conversation_id):
    print("========== SEND_MESSAGE ==========")
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(conversation=conversation, sender=request.user, text=text)

            # برای گروه‌ها، به همه‌ی اعضا (به‌جز خود فرستنده) نوتیف پیام جدید فرستاده می‌شه
            if conversation.is_group:
                recipients = conversation.participants.exclude(id=request.user.id)
                Notification.objects.bulk_create([
                    Notification(
                        user=recipient,
                        sender=request.user,
                        conversation=conversation,
                        notification_type='new_message',
                    )
                    for recipient in recipients
                ])
    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required
def search_users(request):
    """
    جستجوی کاربران واقعی سایت برای انتخاب اعضای گروه (autocomplete).
    اگه conversation_id پاس داده بشه، اعضای فعلی همون گفتگو هم exclude می‌شن.
    خروجی JSON: {"results": [{"id": 1, "username": "sara.k", "full_name": "...", "avatar_url": "..."}]}
    """
    query = request.GET.get('q', '').strip()
    conversation_id = request.GET.get('conversation_id')

    if len(query) < 2:
        return JsonResponse({'results': []})

    exclude_ids = [request.user.id]

    if conversation_id:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )
        exclude_ids += list(conversation.participants.values_list('id', flat=True))

    users = (
        User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
        .exclude(id__in=exclude_ids)
        .order_by('username')[:10]
    )

    results = []
    for u in users:
        full_name = u.get_full_name().strip() if hasattr(u, 'get_full_name') else ''
        avatar_url = None
        if getattr(u, 'profile_picture', None):
            try:
                avatar_url = u.profile_picture.url
            except ValueError:
                avatar_url = None

        results.append({
            'id': u.id,
            'username': u.username,
            'full_name': full_name,
            'avatar_url': avatar_url,
        })

    return JsonResponse({'results': results})


@login_required
def create_group(request):
    print("PATH:", request.path)
    print("POST:", request.POST)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        member_ids = request.POST.getlist('member_ids')

        if not name:
            messages.error(request, 'نام گروه نمی‌تواند خالی باشد.')
            return render(request, 'chat/create_group.html')

        group = Conversation.objects.create(is_group=True, name=name, created_by=request.user)
        group.participants.add(request.user)

        if member_ids:
            # فقط کاربرهای واقعی موجود در سایت اضافه می‌شن، بر اساس id
            members = User.objects.filter(id__in=member_ids)
            group.participants.add(*members)

        # یه پیام سیستمی ساخته می‌شه تا گروه فوراً توی صفحه‌ی پیام‌های همه‌ی اعضا بالا بیاد
        # و به‌جای «شروع گفتگو»، یه پیش‌نمایش معنادار نشون داده بشه
        Message.objects.create(
            conversation=group,
            sender=request.user,
            text=f'{request.user.username} گروه «{name}» را ایجاد کرد.',
            is_system=True,
        )

        return redirect('conversation_detail', conversation_id=group.id)

    return render(request, 'chat/create_group.html')


@login_required
def delete_group(request, pk):

    group = get_object_or_404(
        Conversation,
        pk=pk,
        is_group=True
    )

    if group.created_by != request.user:
        return redirect("inbox")

    if request.method == 'POST':
        group_name = group.name
        group.delete()
        messages.success(request, f'گروه «{group_name}» حذف شد.')

    return redirect("inbox")

@login_required
def clear_chat(request, conversation_id):
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    if request.method == "POST":
        conversation.messages.all().delete()
        messages.success(request, 'گفتگو پاک شد.')

    return redirect("inbox")

@login_required
def delete_conversation(request, pk):
    conversation = get_object_or_404(
        Conversation,
        pk=pk,
        participants=request.user,
        is_group=False,
    )

    if request.method == "POST":
        conversation.delete()
        messages.success(request, 'گفتگو حذف شد.')

    return redirect("inbox")


@login_required
def add_group_members(request, conversation_id):
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user,
        is_group=True
    )

    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        if user_ids:
            existing_ids = set(conversation.participants.values_list('id', flat=True))
            users_to_add = User.objects.filter(id__in=user_ids).exclude(id__in=existing_ids)

            for user in users_to_add:
                conversation.participants.add(user)
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    text=f'{request.user.username} کاربر {user.username} را به گروه اضافه کرد.',
                    is_system=True,
                )
            messages.success(request, 'اعضای جدید به گروه اضافه شدند.')

    return redirect('conversation_detail', conversation_id=conversation.id)

@login_required
def remove_group_member(request, conversation_id, user_id):
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        is_group=True
    )

    # فقط سازنده‌ی گروه اجازه‌ی حذف عضو رو داره
    if conversation.created_by_id != request.user.id:
        return HttpResponseForbidden()

    user_to_remove = get_object_or_404(User, id=user_id)

    # سازنده نمی‌تونه خودش رو حذف کنه (باید گروه رو حذف کنه یا فیچر جدا بسازیم)
    if user_to_remove.id == conversation.created_by_id:
        messages.error(request, 'سازنده‌ی گروه قابل حذف نیست.')
        return redirect('conversation_detail', conversation_id=conversation.id)

    if request.method == 'POST':
        conversation.participants.remove(user_to_remove)
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            text=f'{request.user.username} کاربر {user_to_remove.username} را از گروه حذف کرد.',
            is_system=True,
        )
        messages.success(request, f'{user_to_remove.username} از گروه حذف شد.')

    return redirect('conversation_detail', conversation_id=conversation.id)