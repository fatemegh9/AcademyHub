from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Note, NoteRating, Tag, SavedNote
from django.db.models import Q, Count
from .forms import NoteUploadForm
from django.db import models
import re
from django.db.models import Avg, Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.functions import Coalesce
from social.models import SavedPost, Post
from django.http import JsonResponse
from .services.ai_assistant import extract_text_from_pdf, summarize_note, extract_text_from_pdf, ask_question_about_note, generate_quiz_from_note
import json
from accounts.services.xp import add_xp


def note_list(request):
    query = request.GET.get('q', '')
    field_filter = request.GET.get('field', '')
    level_filter = request.GET.get('level', '')
    type_filter = request.GET.get('note_type', '')
    university_filter = request.GET.get('university', '')

    notes = Note.objects.all()
    
    # جستجو
    if query:
        notes = notes.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(lesson_name__icontains=query) |
            Q(professor_name__icontains=query)
        )
    
    # فیلتر بر اساس رشته
    if field_filter:
        notes = notes.filter(field_of_study=field_filter)
    
    # فیلتر مقطع
    if level_filter:
        notes = notes.filter(level=level_filter)
    
    # فیلتر نوع جزوه
    if type_filter:
        notes = notes.filter(note_type=type_filter)
    
    # فیلتر دانشگاه
    if university_filter:
        notes = notes.filter(university=university_filter)

    # دسته‌بندی‌ها
    most_popular = (
        Note.objects
        .annotate(
            avg_rating=Coalesce(
                Avg('ratings__score'),
                0.0),
                ratings_count=Count('ratings')
        )
        .filter(ratings_count__gt=0)
        .order_by('-avg_rating', '-ratings_count')[:10]
)
    newest = notes.order_by('-created_at')[:10]
    
    
    # لیست رشته‌های موجود
    fields = Note.objects.values_list('field_of_study', flat=True).distinct()
    
    context = {
        'most_popular': most_popular,
        'newest': newest,
        'notes' : notes,
        'fields': fields,
        'search_query': query,
        'selected_field': field_filter,
        'selected_level': level_filter,
        'selected_type': type_filter,
        'selected_university': university_filter,
    }
    return render(request, 'notes/note_list.html', context)

@login_required
def upload_note(request):
    if request.method == 'POST':
        note = Note.objects.create(
            uploaded_by=request.user,
            title=request.POST.get('title'),
            lesson_name=request.POST.get('lesson_name'),
            professor_name=request.POST.get('professor_name'),
            description=request.POST.get('description'),
            level=request.POST.get('level'),
            note_type=request.POST.get('note_type'),
            university=request.POST.get('university'),
            file=request.FILES.get('file'),
        )
        tags_input = request.POST.get('tags_input', '')
        if tags_input:
            tags_input = re.sub(r'[،,]', ' ', tags_input)
            tag_names = [t.strip() for t in tags_input.split() if t.strip()]
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                note.tags.add(tag)
        messages.success(request, 'جزوه با موفقیت آپلود شد.')
        add_xp(request.user, 10, "آپلود جزوه")
        return redirect('note_list')
    return render(request, 'notes/upload_note.html')


@login_required
def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, uploaded_by=request.user)

    if request.method == 'POST':
        note.title = request.POST.get('title')
        note.lesson_name = request.POST.get('lesson_name')
        note.professor_name = request.POST.get('professor_name')
        note.description = request.POST.get('description')
        note.level = request.POST.get('level')
        note.note_type = request.POST.get('note_type')
        note.university = request.POST.get('university')

        if request.FILES.get('file'):
            note.file = request.FILES['file']

        note.save()

        tags_input = request.POST.get('tags_input', '')
        note.tags.clear()
        if tags_input:
            tags_input = re.sub(r'[،,]', ' ', tags_input)
            tag_names = [t.strip() for t in tags_input.split() if t.strip()]
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                note.tags.add(tag)

        messages.success(request, 'جزوه با موفقیت ویرایش شد.')
        return redirect('note_list')
    return render(request, 'notes/upload_note.html', {'note': note})

@login_required
def download_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    note.downloads_count += 1
    note.save()
    return redirect(note.file.url)

@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if note.uploaded_by == request.user or request.user.is_superuser:
        note.delete()
        messages.success(request, 'جزوه حذف شد.')
    else:
        messages.error(request, 'شما اجازه حذف این جزوه را ندارید.')
    return redirect('note_list')

@login_required
def rate_note(request, note_id, score):

    note = get_object_or_404(Note, id=note_id)

    NoteRating.objects.update_or_create(
        note=note,
        user=request.user,
        defaults={
            'score': score
        }
    )

    return redirect('note_list')

def search_by_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    notes = Note.objects.filter(tags=tag).order_by('-created_at')
    return render(request, 'notes/note_list.html', {'notes': notes, 'tag': tag})

@login_required
def save_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    saved, created = SavedNote.objects.get_or_create(user=request.user, note=note)

    if created:
        messages.success(request, 'جزوه به لیست ذخیره شده‌ها اضافه شد.')
    else:
        messages.info(request, 'این جزوه قبلاً ذخیره شده است.')

    return redirect('note_list')

@login_required
def unsave_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    SavedNote.objects.filter(user=request.user, note=note).delete()
    messages.success(request, 'جزوه از لیست ذخیره شده‌ها حذف شد.')
    return redirect('saved_items')

@login_required
def saved_notes_list(request):
    saved_notes = request.user.saved_notes.select_related('note').order_by('-saved_at')
    saved_posts = request.user.saved_posts.select_related('post').order_by('-saved_at')

    context = {
        'saved_notes': saved_notes,
        'saved_posts': saved_posts,
    }
    return render(request, 'notes/saved_items.html', context)

@login_required
def saved_items(request):
    saved_notes = request.user.saved_notes.all().order_by('-saved_at')
    saved_posts = request.user.saved_posts.all().order_by('-saved_at')

    return render(request, 'notes/saved_items.html', {
        'saved_notes': saved_notes,
        'saved_posts': saved_posts,
    })



def get_note_json(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    return JsonResponse({
        'title': note.title,
        'lesson_name': note.lesson_name,
        'professor_name': note.professor_name,
        'description': note.description,
        'downloads_count': note.downloads_count,
        'average_rating': note.average_rating,
        'download_url': note.file.url,
    })


@login_required
def summarize_note_view(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    text = extract_text_from_pdf(note.file.path)

    if not text:
        return JsonResponse({'error': 'متن جزوه قابل استخراج نیست.'}, status=400)

    summary = summarize_note(text)

    return JsonResponse({'summary': summary})

@login_required
def ask_note_view(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    if request.method == 'POST':
        question = request.POST.get('question', '')
        if not question:
            return JsonResponse({'error': 'سوالی وارد نشده.'}, status=400)

        text = extract_text_from_pdf(note.file.path)
        if not text:
            return JsonResponse({'error': 'متن جزوه قابل استخراج نیست.'}, status=400)

        answer = ask_question_about_note(text, question)
        return JsonResponse({'answer': answer})

    return JsonResponse({'error': 'متد نامعتبر'}, status=400)

@login_required
def generate_quiz_view(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    text = extract_text_from_pdf(note.file.path)
    if not text:
        return JsonResponse({'error': 'متن جزوه قابل استخراج نیست.'}, status=400)

    quiz_raw = generate_quiz_from_note(text)

    try:
        # حذف بک‌تیک‌های احتمالی که مدل گاهی برمی‌گرداند
        clean = quiz_raw.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        quiz_data = json.loads(clean)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'خطا در پردازش خروجی AI.'}, status=500)

    return JsonResponse({'quiz': quiz_data})