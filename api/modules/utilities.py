# -*- coding: utf-8 -*-

from locale import LC_ALL, format, setlocale

setlocale(LC_ALL, 'en_US.UTF-8')


def get_float(value):
    return format('%.2f', value, grouping=True)


def get_integer(value):
    return format('%d', value, grouping=True)
