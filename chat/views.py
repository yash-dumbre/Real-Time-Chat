from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import RegisterForm
from .models import Message
import json
from django.conf import settings
from pywebpush import webpush, WebPushException
from .models import PushSubscription

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'chat/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'chat/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def index(request):
    return render(request, 'chat/index.html')

@login_required
def room(request, room_name):
    from django.db.models import Q
    messages = Message.objects.filter(
        room=room_name
    ).exclude(
        Q(msg_type__in=['image','video']) & Q(file='')
    ).order_by('timestamp')[:50]
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'messages': messages,
    })

@csrf_exempt
@login_required
def upload_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        room = request.POST.get('room', 'general')
        if not file:
            return JsonResponse({'error': 'No file'}, status=400)
        mime = file.content_type
        if mime.startswith('image/'):
            msg_type = 'image'
        elif mime.startswith('video/'):
            msg_type = 'video'
        else:
            return JsonResponse({'error': 'Only images and videos allowed'}, status=400)
        if file.size > 20 * 1024 * 1024:
            return JsonResponse({'error': 'File too large (max 20MB)'}, status=400)
        msg = Message.objects.create(
            username=request.user.username,
            room=room, msg_type=msg_type, file=file,
        )
        return JsonResponse({'url': msg.file.url, 'msg_type': msg_type, 'username': request.user.username})
    return JsonResponse({'error': 'Invalid method'}, status=405)



@login_required
def search_messages(request):
    query = request.GET.get('q', '').strip()
    room  = request.GET.get('room', '')
    if not query:
        return JsonResponse({'results': []})
    messages = Message.objects.filter(
        room=room,
        content__icontains=query,
        msg_type='text',
    ).order_by('-timestamp')[:20]
    results = [
        {'id': m.id, 'username': m.username, 'content': m.content,
         'timestamp': m.timestamp.strftime('%H:%M')}
        for m in messages
    ]
    return JsonResponse({'results': results})


@login_required
def push_public_key(request):
    return JsonResponse({'public_key': settings.VAPID_PUBLIC_KEY})

@csrf_exempt
@login_required
def push_subscribe(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        PushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=data['endpoint'],
            defaults={
                'p256dh': data['keys']['p256dh'],
                'auth':   data['keys']['auth'],
            }
        )
        return JsonResponse({'status': 'subscribed'})
    return JsonResponse({'error': 'POST only'}, status=405)

def send_push_to_room(room, sender, message):
    subs = PushSubscription.objects.exclude(user__username=sender)
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=json.dumps({'title': f'#{room}', 'body': f'{sender}: {message}'}),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=settings.VAPID_CLAIMS,
            )
        except WebPushException:
            sub.delete()  # remove dead subscriptions