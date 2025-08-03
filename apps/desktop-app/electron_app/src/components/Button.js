function Button({ id, text, onClick }) {
  const button = document.createElement('button');
  button.id = id;
  button.textContent = text;
  button.classList.add('action-button');
  button.addEventListener('click', onClick);
  return button;
}
