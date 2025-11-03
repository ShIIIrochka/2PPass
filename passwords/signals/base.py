# -*- coding: utf-8 -*-


def connect_signal(signal, handler, sender):
	"""Единая точка подключения сигналов."""
	signal.connect(handler, sender=sender, weak=False)
