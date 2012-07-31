'''
File: actions.py
Author: Rinat F Sabitov
Description:
'''

from objectpack import ObjectPack
from models import Person

class PersonObjectPack(ObjectPack):
    """docstring for PersonObjectPack"""

    model = Person
    add_to_desktop = True
    add_to_menu = True

