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
    default='media/profiles/default.png'   
)
    university = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    bio = models.TextField(max_length=500, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    github = models.CharField(max_length=100, blank=True, null=True)
    linkdin = models.CharField(max_length=100, blank=True, null=True)
    xp = models.IntegerField(default=0)

    def get_level(self):
        if self.xp < 50:
            return "تازه‌وارد"
        elif self.xp < 150:
            return "دانشجوی فعال"
        elif self.xp < 400:
            return "متخصص"
        elif self.xp < 1000:
            return "استاد"
        else:
            return "افسانه"

    def xp_to_next_level(self):
        thresholds = [50, 150, 400, 1000]
        for t in thresholds:
            if self.xp < t:
                return t - self.xp
        return 0
    
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
    
    def xp_percent(self):
        thresholds = [0, 50, 150, 400, 1000]
        for i in range(len(thresholds) - 1):
            if thresholds[i] <= self.xp < thresholds[i + 1]:
                range_size = thresholds[i + 1] - thresholds[i]
                progress = self.xp - thresholds[i]
                return int((progress / range_size) * 100)
        return 100
    

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
    