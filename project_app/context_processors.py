from .models import ROLE_ADMIN, ROLE_MEMBER, UserProfile


def current_user_profile(request):
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': ROLE_MEMBER})
        if request.user.is_superuser and profile.role != ROLE_ADMIN:
            profile.role = ROLE_ADMIN
            profile.save()
        return {'user_profile': profile}
    return {}
