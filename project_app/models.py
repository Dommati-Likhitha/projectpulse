from django.contrib.auth.models import User
from django.db import models

ROLE_ADMIN = 'admin'
ROLE_MEMBER = 'member'
ROLE_CHOICES = [
    (ROLE_ADMIN, 'Admin'),
    (ROLE_MEMBER, 'Member'),
]

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CHOICES = [
    (STATUS_PENDING, 'Pending'),
    (STATUS_IN_PROGRESS, 'In Progress'),
    (STATUS_DONE, 'Done'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_MEMBER)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN

    @property
    def is_member(self):
        return self.role == ROLE_MEMBER

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    members = models.ManyToManyField(User, related_name='projects', blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    github_link = models.URLField(blank=True, help_text="GitHub repository URL")
    live_project_link = models.URLField(blank=True, help_text="Live project URL")
    project_documentation = models.FileField(upload_to='project_docs/', blank=True, null=True, help_text="Project documentation PDF")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='tasks', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    due_date = models.DateField(null=True, blank=True)
    task_deliverable = models.FileField(upload_to='task_deliverables/', blank=True, null=True, help_text="Task deliverable PDF")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['status', '-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'
