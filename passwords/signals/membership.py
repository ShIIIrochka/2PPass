# -*- coding: utf-8 -*-

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from passwords.models.password_group import GroupMembership
from passwords.services.membership import sync_user_django_groups


@receiver(post_save, sender=GroupMembership)
def handle_membership_save(sender, instance: GroupMembership, **kwargs):
	"""Синхронизируем Django-группы при добавлении/изменении членства."""
	sync_user_django_groups(instance.user)


@receiver(post_delete, sender=GroupMembership)
def handle_membership_delete(sender, instance: GroupMembership, **kwargs):
	"""Синхронизируем Django-группы при удалении членства."""
	sync_user_django_groups(instance.user)
