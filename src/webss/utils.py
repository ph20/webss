#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Messanger:
    def __init__(self, verbose=0):
        self._verbose = verbose

    def set_verbosity(self, verbose):
        self._verbose = verbose

    def send(self, msg):
        if self._verbose:
            print(msg)

    def __call__(self, *args, **kwargs):
        self.send(*args, **kwargs)
