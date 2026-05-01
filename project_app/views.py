from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm, ProjectSubmissionForm, TaskForm, TaskStatusForm, TaskSubmissionForm, UserRegistrationForm
from .models import Project, Task, ROLE_MEMBER, UserProfile


def get_user_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user, defaults={'role': ROLE_MEMBER})
    if user.is_superuser and profile.role != 'admin':
        profile.role = 'admin'
        profile.save()
    return profile


def debug_view(request):
    """Debug view to check system status"""
    import sys
    from django.conf import settings
    
    debug_info = {
        'python_version': sys.version,
        'django_version': settings.VERSION,
        'debug_mode': settings.DEBUG,
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'csrf_trusted_origins': settings.CSRF_TRUSTED_ORIGINS,
        'installed_apps': settings.INSTALLED_APPS,
    }
    
    # Test database connection
    from django.db import connection
    try:
        cursor = connection.cursor()
        debug_info['database_connection'] = 'OK'
    except Exception as e:
        debug_info['database_connection'] = f'ERROR: {e}'
    
    return JsonResponse(debug_info)


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                get_user_profile(user)
                messages.success(request, 'Account created successfully. You can now sign in.')
                return redirect('login')
            except Exception as e:
                messages.error(request, 'An error occurred during registration. Please try again.')
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Registration error: {e}')
    else:
        form = UserRegistrationForm()
    return render(request, 'project_app/register.html', {'form': form})


def home(request):
    return render(request, 'project_app/home.html')

@login_required
def dashboard(request):
    profile = get_user_profile(request.user)
    if profile.is_admin:
        projects = Project.objects.all()
        tasks = Task.objects.all()
    else:
        projects = Project.objects.filter(members=request.user) | Project.objects.filter(owner=request.user)
        tasks = Task.objects.filter(assignee=request.user)

    task_status_counts = tasks.values('status').annotate(count=Count('id'))
    status_summary = {
        'pending': 0,
        'in_progress': 0,
        'done': 0,
    }
    for row in task_status_counts:
        status_summary[row['status']] = row['count']

    overdue_tasks = tasks.filter(
        Q(due_date__lt=date.today()) & ~Q(status='done')
    )

    return render(request, 'project_app/dashboard.html', {
        'projects': projects.distinct(),
        'tasks': tasks.distinct(),
        'status_summary': status_summary,
        'overdue_tasks': overdue_tasks.distinct(),
    })

def _user_is_project_member(user, project):
    return project.owner == user or project.members.filter(pk=user.pk).exists()

@login_required
def project_list(request):
    profile = get_user_profile(request.user)
    if profile.is_admin:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(members=request.user) | Project.objects.filter(owner=request.user)
    return render(request, 'project_app/project_list.html', {'projects': projects.distinct()})

@login_required
def team_management(request):
    profile = get_user_profile(request.user)
    if not profile.is_admin:
        messages.error(request, 'Only admins can manage team members.')
        return redirect('dashboard')

    users = User.objects.all().order_by('username')
    for user in users:
        get_user_profile(user)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')
        if user_id and role in ['admin', 'member']:
            target_user = get_object_or_404(User, pk=user_id)
            target_profile = get_user_profile(target_user)
            target_profile.role = role
            target_profile.save()
            messages.success(request, f"{target_user.username} is now set to {role.capitalize()}.")
            return redirect('team_management')

    return render(request, 'project_app/team_management.html', {'users': users})

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    profile = get_user_profile(request.user)
    if not profile.is_admin and not _user_is_project_member(request.user, project):
        messages.error(request, 'You do not have access to that project.')
        return redirect('project_list')
    return render(request, 'project_app/project_detail.html', {
        'project': project,
        'user_profile': profile
    })

@login_required
def project_submit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    profile = get_user_profile(request.user)
    if not profile.is_member or not _user_is_project_member(request.user, project):
        messages.error(request, 'Only project members can submit project links and documentation.')
        return redirect('project_detail', project_id=project_id)

    if request.method == 'POST':
        form = ProjectSubmissionForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project submission updated successfully.')
            return redirect('project_detail', project_id=project_id)
    else:
        form = ProjectSubmissionForm(instance=project)
    return render(request, 'project_app/project_submit.html', {
        'form': form,
        'project': project,
        'title': f'Submit Links & Documentation for {project.name}'
    })

@login_required
def project_create(request):
    profile = get_user_profile(request.user)
    if not profile.is_admin:
        messages.error(request, 'Only admins can create projects.')
        return redirect('project_list')
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            form.save_m2m()
            messages.success(request, 'Project created successfully.')
            return redirect('project_detail', project_id=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'project_app/project_form.html', {'form': form, 'title': 'Create Project'})

@login_required
def project_update(request, project_id):
    profile = get_user_profile(request.user)
    if not profile.is_admin:
        messages.error(request, 'Only admins can update projects.')
        return redirect('project_list')
    project = get_object_or_404(Project, pk=project_id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('project_detail', project_id=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'project_app/project_form.html', {'form': form, 'title': 'Edit Project'})

@login_required
def project_delete(request, project_id):
    profile = get_user_profile(request.user)
    if not profile.is_admin:
        messages.error(request, 'Only admins can delete projects.')
        return redirect('project_list')
    project = get_object_or_404(Project, pk=project_id)
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully.')
        return redirect('project_list')
    return render(request, 'project_app/project_delete_confirm.html', {'project': project})

@login_required
def task_create(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    profile = get_user_profile(request.user)
    if not profile.is_admin:
        messages.error(request, 'Only admins can create tasks.')
        return redirect('project_detail', project_id=project.pk)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            messages.success(request, 'Task added successfully.')
            return redirect('project_detail', project_id=project.pk)
    else:
        form = TaskForm()
    return render(request, 'project_app/task_form.html', {'form': form, 'project': project, 'title': 'Create Task'})

@login_required
def task_update(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    project = task.project
    profile = get_user_profile(request.user)
    if not profile.is_admin and task.assignee != request.user:
        messages.error(request, 'You do not have permission to update this task.')
        return redirect('project_detail', project_id=project.pk)
    if request.method == 'POST':
        if profile.is_admin:
            form = TaskForm(request.POST, instance=task)
        else:
            form = TaskStatusForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('project_detail', project_id=project.pk)
    else:
        if profile.is_admin:
            form = TaskForm(instance=task)
        else:
            form = TaskStatusForm(instance=task)
    return render(request, 'project_app/task_form.html', {'form': form, 'project': project, 'title': 'Edit Task'})
    task = get_object_or_404(Task, pk=task_id)
    project = task.project
    profile = get_user_profile(request.user)
    if not profile.is_admin and task.assignee != request.user:
        messages.error(request, 'You do not have permission to update this task.')
        return redirect('project_detail', project_id=project.pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('project_detail', project_id=project.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, 'project_app/task_form.html', {'form': form, 'project': project, 'title': 'Edit Task'})

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    project = task.project
    profile = get_user_profile(request.user)
    if not profile.is_admin and not _user_is_project_member(request.user, project) and task.assignee != request.user:
        messages.error(request, 'You do not have access to this task.')
        return redirect('dashboard')
    return render(request, 'project_app/task_detail.html', {'task': task})

@login_required
def task_submit(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    project = task.project
    profile = get_user_profile(request.user)
    if not profile.is_member or task.assignee != request.user:
        messages.error(request, 'Only the assigned member can submit task deliverables.')
        return redirect('project_detail', project_id=project.pk)

    if request.method == 'POST':
        form = TaskSubmissionForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task deliverable submitted successfully.')
            return redirect('project_detail', project_id=project.pk)
    else:
        form = TaskSubmissionForm(instance=task)
    return render(request, 'project_app/task_submit.html', {
        'form': form,
        'task': task,
        'project': project,
        'title': f'Submit Deliverable for {task.title}'
    })
