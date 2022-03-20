# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 11:03:44 2022

@author: Chenyu Lue
"""

def extension(cls):
    '''
    A class decorator which extends the class's methods.
    '''
    def update(extension):
        for k, v in extension.__dict__.items():
            if k != '__dict__':
                setattr(cls, k, v)
        return cls
    return update