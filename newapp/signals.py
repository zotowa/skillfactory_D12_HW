from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from newapp.models import PostCategory
from newapp.tascs import new_post_subscriptions


@receiver(m2m_changed, sender=PostCategory)
def notify_subscribers(sender, instance, **kwargs):
    if kwargs['action'] == 'post_add':
        new_post_subscriptions(instance)