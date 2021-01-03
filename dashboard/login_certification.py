from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import authenticate


class MyBackend(BaseBackend):
    def authenticate(self, request, token=None, file_path=None):
        pass

    def login(self, request, token=None, file_path=None):
        pass
