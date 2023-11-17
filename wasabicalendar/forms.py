# @file forms.py
# @brief A task form which is used to create and modify task with a 
#        clean function which cleans the input to prevent injection attack.

from django import forms
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone

from wasabicalendar.models import Tag, Task, Calendar, Profile

# task form used in create task page and modify task page which contains fields 
# including topic, tag, description, location, link, task date, start time and end time
class TaskForm(forms.Form):
    topic = forms.CharField(max_length = 50, label = "Topic", widget=forms.TextInput(attrs={'class': 'task_form', 'placeholder': 'Required'}))
    tag = forms.ChoiceField(widget=forms.Select(attrs={'class': 'choice_form'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':20,'rows':5,'class': 'task_form', 'placeholder':'Optional'}), required=False, max_length = 200, label = "Description")
    location = forms.CharField(required=False, max_length = 200, label = "Location", widget=forms.TextInput(attrs={'class': 'task_form', 'placeholder': 'Optional'}))
    link = forms.URLField(required=False, max_length = 1000, label = "Link", widget=forms.TextInput(attrs={'class': 'task_form', 'placeholder': 'Optional'}))
    taskDate = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date', 'class': 'time_form'}), label="Task Date")
    startTime = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'time_form'}), label="Start Time")
    endTime = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'time_form'}), label="End Time")
    
    # @brief initialize the choice field of tag in the task form
    # @param calendar: an instance of calendar object
    # @param initial: a dict of initial data that will be used to prefill
    #                 the form in modify task page
    def __init__(self, *args, calendar=None, initial=None):
        super().__init__(*args)
        L = [] # initialize choices
        for item in calendar.tags.all():
            L.append((item.id, item.name))
        self.fields['tag'].choices = tuple(L)

    # @brief: clean the input data while submitting and sanitize the strings
    # @returns: a dict contains cleaned data of all the fields
    def clean(self):
        cleaned_data = super().clean()
        startTime = cleaned_data.get('startTime')
        endTime = cleaned_data.get('endTime')
        topic = cleaned_data.get('topic')
        description = cleaned_data.get('description')
        tag = cleaned_data.get('tag')
        location = cleaned_data.get('location')
        link = cleaned_data.get('link')
        if not all(x.isalnum() or x.isspace() for x in topic):
            raise forms.ValidationError("Topic can only contain numbers, letters, and spaces.")
        if not all(x.isalnum() or x.isspace() for x in description):
            raise forms.ValidationError("Description can only contain numbers, letters, and spaces.")
        if not all(x.isalnum() or x.isspace() for x in location):
            raise forms.ValidationError("Location can only contain numbers, letters, and spaces.")
        if "<" in link or ">" in link or "'" in link or '"' in link:
            raise forms.ValidationError("Invalid link.")
        if "&lt;" in link or "&gt;" in link or "&#x27;" in link or "&quot;" in link:
            raise forms.ValidationError("Invalid link.")
        if startTime >= endTime:
            raise forms.ValidationError("Start time must be before end time.")
        return cleaned_data