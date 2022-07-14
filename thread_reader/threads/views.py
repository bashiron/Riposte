from django.shortcuts import render

def home(request):
    context = {
        'replies': {}
    }
    return render(request, 'threads/home.html', context)
