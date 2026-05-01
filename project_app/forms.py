from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Project, Task

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'members']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'members': forms.SelectMultiple(attrs={'size': 6}),
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assignee', 'status', 'due_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ProjectSubmissionForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['github_link', 'live_project_link', 'project_documentation']
        widgets = {
            'project_documentation': forms.ClearableFileInput(attrs={'accept': '.pdf', 'class': 'form-control'}),
            'github_link': forms.URLInput(attrs={'placeholder': 'https://github.com/username/repo', 'class': 'form-control'}),
            'live_project_link': forms.URLInput(attrs={'placeholder': 'https://your-project-domain.com', 'class': 'form-control'}),
        }

class TaskStatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status']

class TaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['task_deliverable']
        widgets = {
            'task_deliverable': forms.ClearableFileInput(attrs={'accept': '.pdf', 'class': 'form-control'}),
        }
