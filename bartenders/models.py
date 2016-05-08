from django.db import models


# Create your models here.
class Bartender(models.Model):
    name = models.CharField(max_length=140)
    username = models.CharField(max_length=140)
    email = models.CharField(max_length=255, blank=True, null=True)
    studentNumber = models.IntegerField(blank=True, null=True)
    phoneNumber = models.IntegerField(blank=True, null=True)
    isActiveBartender = models.BooleanField(default=True)
    isBoardMember = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class BoardMember(models.Model):
    bartender = models.ForeignKey(Bartender, null=False, blank=False)
    title = models.CharField(max_length=255)
    responsibilities = models.CharField(max_length=255)

    def __str__(self):
        return self.bartender.username
