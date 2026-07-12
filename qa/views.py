from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Question, Answer, Vote
from notes.models import Note
from django.db import models
from social.models import Notification
from accounts.services.xp import add_xp


def question_list(request):
    questions = Question.objects.all().order_by('-created_at')

    query = request.GET.get('q', '')
    lesson_filter = request.GET.get('lesson', '')
    status_filter = request.GET.get('status', '')

    if query:
        questions = questions.filter(
            models.Q(title__icontains=query) | models.Q(body__icontains=query)
        )

    if lesson_filter:
        questions = questions.filter(lesson_name=lesson_filter)

    if status_filter == 'answered':
        questions = questions.filter(answers__isnull=False).distinct()
    elif status_filter == 'unanswered':
        questions = questions.filter(answers__isnull=True)

    lessons = Question.objects.exclude(lesson_name='').values_list('lesson_name', flat=True).distinct()

    return render(request, 'qa/question_list.html', {
        'questions': questions,
        'lessons': lessons,
        'search_query': query,
        'selected_lesson': lesson_filter,
        'selected_status': status_filter,
    })


@login_required
def ask_question(request):
    if request.method == 'POST':
        note_id = request.POST.get('note_id')
        note = Note.objects.filter(id=note_id).first() if note_id else None

        Question.objects.create(
            user=request.user,
            title=request.POST.get('title'),
            body=request.POST.get('body'),
            note=note,
            lesson_name=request.POST.get('lesson_name', ''),
        )
        messages.success(request, 'سوال شما با موفقیت ثبت شد.')
        return redirect('question_list')

    notes = Note.objects.all()
    return render(request, 'qa/ask_question.html', {'notes': notes})


def question_detail(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    answers = question.answers.annotate(vote_count=models.Count('votes')).order_by('-is_accepted', '-vote_count', '-created_at')
    return render(request, 'qa/question_detail.html', {
        'question': question,
        'answers': answers,
    })


@login_required
def add_answer(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            Answer.objects.create(question=question, user=request.user, body=body)
            messages.success(request, 'پاسخ شما ثبت شد.')
    return redirect('question_detail', question_id=question.id)


@login_required
def accept_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)
    if answer.question.user == request.user:
        answer.question.answers.update(is_accepted=False)
        answer.is_accepted = True
        answer.save()
        add_xp(answer.user, 20, "پاسخ پذیرفته شد")
        messages.success(request, 'پاسخ به عنوان بهترین پاسخ انتخاب شد.')
    return redirect('question_detail', question_id=answer.question.id)


@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id, user=request.user)
    question.delete()
    messages.success(request, 'سوال حذف شد.')
    return redirect('question_list')


@login_required
def delete_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id, user=request.user)
    question_id = answer.question.id
    answer.delete()
    messages.success(request, 'پاسخ حذف شد.')
    return redirect('question_detail', question_id=question_id)


@login_required
def vote_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)
    vote = Vote.objects.filter(user=request.user, answer=answer).first()

    if vote:
        vote.delete()
    else:
        Vote.objects.create(user=request.user, answer=answer)

    return redirect('question_detail', question_id=answer.question.id)

@login_required
def add_answer(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            Answer.objects.create(question=question, user=request.user, body=body)

            if request.user != question.user:
                Notification.objects.create(
                    user=question.user,
                    sender=request.user,
                    question_id=question.id,
                    notification_type='new_answer'
                )

            messages.success(request, 'پاسخ شما ثبت شد.')
    return redirect('question_detail', question_id=question.id)

