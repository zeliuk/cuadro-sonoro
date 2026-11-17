const frame = document.getElementById('object-wrap');

frame.addEventListener('click', async event => {
  if (event.target.closest('button')) return;
  if (document.fullscreenElement || !document.documentElement.requestFullscreen) return;
  try {
    await document.documentElement.requestFullscreen();
  } catch {
    // Some tablet browsers only allow fullscreen from their own menu.
  }
});
