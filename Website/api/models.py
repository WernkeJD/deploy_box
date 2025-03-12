from django.db import models
from django.contrib.auth.models import User


class Stacks(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10)
    variant = models.CharField(max_length=10)
    version = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + " - " + self.type


class Deployments(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    stack = models.ForeignKey(Stacks, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + " - " + self.stack_type

    def __dict__(self):
        return {
            "id": self.id,
            "name": self.name,
            "stack": self.stack.__dict__(),
            "created_at": self.created_at,
        }


class DeploymentFrontend(models.Model):
    deployment = models.ForeignKey(Deployments, on_delete=models.CASCADE)
    url = models.URLField()
    image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url

    def __dict__(self):
        return {
            "id": self.id,
            "url": self.url,
            "image_url": self.image_url,
            "created_at": self.created_at,
        }


class DeploymentBackend(models.Model):
    deployment = models.ForeignKey(Deployments, on_delete=models.CASCADE)
    url = models.URLField()
    image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url

    def __dict__(self):
        return {
            "id": self.id,
            "url": self.url,
            "image_url": self.image_url,
            "created_at": self.created_at,
        }


class DeploymentDatabase(models.Model):
    deployment = models.ForeignKey(Deployments, on_delete=models.CASCADE)
    uri = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url

    def __dict__(self):
        return {
            "id": self.id,
            "uri": self.uri,
            "created_at": self.created_at,
        }
