function Notification({ type, message }) {
  const notification = document.createElement('div');
  notification.classList.add('notification', `notification-${type}`);
  notification.textContent = message;
  return notification;
}
