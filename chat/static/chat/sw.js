self.addEventListener('push', function(event) {
  const data = event.data.json();
  self.registration.showNotification(data.title, {
    body: data.body,
    icon: '/static/chat/icon.png',
    badge: '/static/chat/icon.png',
    vibrate: [200, 100, 200],
  });
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(clients.openWindow('/chat/'));
});