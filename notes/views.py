from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Note, Rating, Tag, SavedNote
from django.db.models import Q, Count
from .forms import NoteUploadForm
from django.db import models
import re
from social.models import SavedPost
from django.http import JsonResponse

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
    most_popular = notes.order_by('-downloads_count')[:10]
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
        form = NoteUploadForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.uploaded_by = request.user
            
            # دریافت فیلدهای جدید
            note.level = request.POST.get('level')
            note.note_type = request.POST.get('note_type')
            note.university = request.POST.get('university')
            
            note.save()
            
            # پردازش تگ‌ها
            tags_input = form.cleaned_data.get('tags_input', '')
            if tags_input:
                tags_input = re.sub(r'[،,]', ' ', tags_input) 
                tag_names = [tag.strip() for tag in re.split(r'[\n\s]+', tags_input) if tag.strip()]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    note.tags.add(tag)
            
            messages.success(request, 'جزوه با موفقیت آپلود شد.')
            return redirect('note_list')
    else:
        form = NoteUploadForm()
    return render(request, 'notes/upload_note.html', {'form': form})

@login_required
def download_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    note.downloads_count += 1
    note.save()
    return redirect(note.file.url)

@login_required
def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if note.uploaded_by != request.user:
        messages.error(request, 'شما اجازه ویرایش این جزوه را ندارید.')
        return redirect('note_list')
    
    if request.method == 'POST':
        note.title = request.POST.get('title')
        note.description = request.POST.get('description')
        note.save()
        messages.success(request, 'جزوه با موفقیت ویرایش شد.')
    return redirect('note_list')

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
def rate_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    if request.method == 'POST':
        score = int(request.POST.get('score', 0))
        if 1 <= score <= 5:
            rating, created = Rating.objects.get_or_create(
                user=request.user,
                note=note,
                defaults={'score': score}
            )
            if not created:
                rating.score = score
                rating.save()

            avg = note.ratings.aggregate(models.Avg('score'))['score__avg']
            note.average_rating = round(avg, 1)
            note.save()
            
            messages.success(request, f'امتیاز شما ثبت شد. میانگین: {note.average_rating}')
        else:
            messages.error(request, 'امتیاز نامعتبر است')
    
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
    return redirect('note_list')

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