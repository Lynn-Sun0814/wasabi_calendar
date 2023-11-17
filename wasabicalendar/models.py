# @file: models.py
# @brief: defines model used in the database


from django.db import models
from django.contrib.auth.models import User

# save optional fields including location, link and text description inside a 
# description class
class Description(models.Model):
    location = models.CharField(blank=True, max_length=200)
    link = models.CharField(blank=True, max_length=200)
    text = models.CharField(blank=True, max_length=500)

class Calendar(models.Model):
    name = models.CharField(max_length=15)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="owned_calendar")
    members = models.ManyToManyField(User, default=None, related_name="shared_calendar")

class Tag(models.Model):
    name = models.CharField(max_length=15)
    calendar = models.ForeignKey(Calendar, default = None, on_delete=models.PROTECT, related_name="tags")
    color = models.CharField(max_length=7, default="#E3F1BA")

class Task(models.Model):
    topic = models.CharField(max_length=200)
    tag = models.ForeignKey(Tag, default=None, on_delete=models.PROTECT, related_name="tsk")
    description = models.OneToOneField(Description, on_delete=models.PROTECT)
    calendar = models.ForeignKey(Calendar, default = None, on_delete=models.PROTECT, related_name="tasks")
    taskDate = models.DateField()
    startTime = models.TimeField()
    endTime = models.TimeField()
    created_by = models.ForeignKey(User, default = None, on_delete=models.PROTECT, related_name="creators")
    creation_time = models.DateTimeField()
    updated_by = models.ForeignKey(User, default = None, on_delete=models.PROTECT, related_name="updaters")
    update_time = models.DateTimeField()

class Block(models.Model):
    date = models.CharField(max_length=20)
    slot = models.IntegerField()
    select_user = models.ManyToManyField(User, related_name="toblocks")
    calendar = models.ForeignKey(Calendar, on_delete=models.PROTECT, related_name="blocks")