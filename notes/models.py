from django.db import models
from django.conf import settings
from django.utils.text import slugify
import re
from django.db.models import Avg


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True, allow_unicode=True)  # ← allow_unicode=True
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)  
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Note(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    lesson_name = models.CharField(max_length=100)
    professor_name = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='notes/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    downloads_count = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True, related_name='notes')
    field_of_study = models.CharField(max_length=100, blank=True, null=True)

    LEVEL_CHOICES = [
        ('associate', 'کاردانی'),
        ('bachelor', 'کارشناسی'),
        ('master', 'کارشناسی ارشد'),
        ('phd', 'دکتری'),
    ]
    
    TYPE_CHOICES = [
        ('handwritten', 'دستنویس'),
        ('typed', 'تایپی'),
        ('slide', 'اسلاید'),
        ('exam', 'نمونه سوال'),
    ]
    
    UNIVERSITY_CHOICES = [
        ('tehran', 'دانشگاه تهران'),
        ('sharif', 'صنعتی شریف'),
        ('azad', 'آزاد'),
        ('pnu', 'پیام نور'),
    ]
    
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True, null=True)
    note_type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True, null=True)
    university = models.CharField(max_length=50, choices=UNIVERSITY_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.title
    
    @property
    def comment_count(self):
        from social.models import Comment
        return Comment.objects.filter(post__note=self).count()
    
    @property
    def average_rating(self):
        ratings = self.ratings.all()

        if not ratings.exists():
            return 0

        return round(
            ratings.aggregate(
                Avg('score')
            )['score__avg'],
            1
        )

    
class NoteRating(models.Model):
    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='ratings'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    score = models.IntegerField()  # 1 تا 5

    class Meta:
        unique_together = ('note', 'user')
    

class SavedNote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_notes')
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'note']

    def __str__(self):
        return f"{self.user.username} - {self.note.title}"



