from django.core.management.base import BaseCommand, CommandError

from app.models import Payment

import json
import os
import requests


class Command(BaseCommand):
    help = 'Populates WinTotals Table'
    
    def handle(self, *args, **options):        
        pass