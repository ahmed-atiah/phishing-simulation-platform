from django.contrib import admin
from django.urls import path, include  # <-- Make sure 'include' is imported

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Add this line:
    # This tells Django to include all URLs from 'phish_manager.urls'
    # when someone visits a path starting with '' (empty).
    path('', include('phish_manager.urls')), 
]