from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length = 100)
    birthdate = models.DateField()    

    def __str__(self):
        return self.user.username

class Stacks(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10)
    variant = models.CharField(max_length=10)
    version = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + " - " + self.type
    
class DeployedStacks(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    stack_type = models.CharField(max_length=4)
    frontend_id = models.CharField(max_length=100)
    backend_id = models.CharField(max_length=100)
    database_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + " - " + self.stack_type