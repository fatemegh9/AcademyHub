from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    student_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    field_of_study = models.CharField(max_length=100, blank=False)
    semester = models.IntegerField(blank=True, null=True)
    profile_picture = models.ImageField(
    upload_to='profiles/', 
    blank=True, 
    null=True,
    default='profiles/default.png'  
)
    bio = models.TextField(max_length=500, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    github = models.CharField(max_length=100, blank=True, null=True)
    linkdin = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username
    
    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return 'no photo yet'
    

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
    