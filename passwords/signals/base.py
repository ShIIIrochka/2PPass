# -*- coding: utf-8 -*-

from django.db.models.signals import post_save, post_delete


def connect_signal(signal, handler, sender):
    """Единая точка подключения сигналов."""
    signal.connect(handler, sender=sender, weak=False)
