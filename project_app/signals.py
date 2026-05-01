from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ROLE_ADMIN, ROLE_MEMBER, UserProfile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        role = ROLE_ADMIN if instance.is_superuser else ROLE_MEMBER
        UserProfile.objects.create(user=instance, role=role)
