import {qrcode} from './qrcode.js?v=20261117-2';

const $ = id => document.getElementById(id);
const apiBase = document.querySelector('meta[name="sonoro-api-base"]')?.content.trim().replace(/\/$/, '') || '';
const validToken = token => /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(token);
const safeImageUrl = value => {
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password ? url.href : ''; }
  catch { return ''; }
};
const buttons = [...document.querySelectorAll('.slot-button')];
const pressed = new Set();
const ignoredClicks = new Set();
let token = '';
let state = {slots:{}, jobs:{}};
let activeSlot = null;
let qrVisible = false;
let frameLoaded = false;
let qrToken = '';
let controller = null;
let generation = 0;
let pollTimer = null;
let longPressTimer, comboTimer, comboClock, qrTimer, qrClock, resetHideTimer;
let comboStarted = false, comboCompleted = false, comboStartedAt = 0;
const imageCache = new Map();
const failedImages = new Set();
const mediaRequests = new Map();
const mediaControllers = new Map();
const previewAudio = $('preview-audio');
let playbackRequest = 0;

function getTokenFromUrl() {
  const fragment = new URLSearchParams(location.hash.slice(1));
  const query = new URLSearchParams(location.search);
  return fragment.get('token') || query.get('token') || '';
}
function itemAt(index) { return state.slots?.[`slot-${index}`] || null; }
function itemName(item) { return item?.title || (item?.kind === 'station' ? 'Emisora' : 'Selección'); }
function setStatus(message, kind = '') {
  const node = $('connection-status');
  node.textContent = message;
  node.dataset.kind = kind;
}
function displayIdle(message = 'Selecciona una de las tres opciones') {
  $('album-cover').hidden = true;
  $('album-cover').removeAttribute('src');
  $('screen-content').classList.remove('is-station');
  $('screen-idle').hidden = false;
  $('screen-message').textContent = message;
}
function ensureQr() {
  if (!token) return false;
  if (qrToken === token && $('qr-symbol').firstElementChild) return true;
  const target = `https://sonoro.zeliuk.xyz/#token=${encodeURIComponent(token)}`;
  try {
    const code = qrcode(0, 'M');
    code.addData(target, 'Byte');
    code.make();
    $('qr-symbol').innerHTML = code.createSvgTag({cellSize:3, margin:3, scalable:true, alt:'QR de configuración musical', title:'Escanea para elegir tu música'});
    qrToken = token;
    return true;
  } catch {
    setStatus('No se pudo generar el QR del cuadro.', 'error');
    return false;
  }
}
function renderScreen() {
  const allSlotsEmpty = frameLoaded && token && [0, 1, 2].every(index => !itemAt(index));
  if ((qrVisible || allSlotsEmpty) && ensureQr()) {
    $('album-cover').hidden = true;
    $('screen-idle').hidden = true;
    $('device-qr').hidden = false;
    $('qr-countdown').hidden = !qrVisible;
    return;
  }
  $('device-qr').hidden = true;
  const playing = activeSlot !== null && Boolean(itemAt(activeSlot));
  if (!playing) {
    displayIdle(token ? 'Selecciona una de las tres opciones' : 'Conecta un cuadro para cargar su portada');
    return;
  }
  const item = itemAt(activeSlot);
  const imageUrl = failedImages.has(item.id) ? '' : item.kind === 'station'
    ? safeImageUrl(item.favicon)
    : safeImageUrl(imageCache.get(item.id)?.image_url);
  if (imageUrl) {
    $('album-cover').src = imageUrl;
    $('album-cover').alt = `Portada de ${itemName(item)}`;
    $('album-cover').hidden = false;
    $('screen-idle').hidden = true;
    $('screen-content').classList.toggle('is-station', item.kind === 'station');
  } else {
    displayIdle(item.kind === 'station' ? 'Emisora seleccionada' : 'Portada no disponible');
    $('screen-idle').hidden = false;
    $('screen-idle').firstChild.textContent = itemName(item);
  }
}
function render() {
  const playing = activeSlot !== null && Boolean(itemAt(activeSlot));
  buttons.forEach((button, index) => {
    const item = itemAt(index);
    button.classList.toggle('is-playing', playing && index === activeSlot);
    button.setAttribute('aria-label', item ? `Pulsador ${index + 1}, ${itemName(item)}` : `Pulsador ${index + 1}, espacio vacío`);
  });
  renderScreen();
}

async function api(path, requestToken, currentGeneration, requestController) {
  if (!apiBase) throw new Error('Falta configurar la URL de la API en la página de la maqueta.');
  const response = await fetch(`${apiBase}${path}`, {
    headers: {Authorization: `Bearer ${requestToken}`},
    signal: requestController.signal,
  });
  if (currentGeneration !== generation) throw new DOMException('Solicitud anterior', 'AbortError');
  let data;
  try { data = await response.json(); }
  catch { throw new Error('La API no devolvió una respuesta JSON válida.'); }
  if (!response.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : `La API respondió con HTTP ${response.status}.`;
    throw new Error(detail);
  }
  return data;
}

async function syncFrame(currentGeneration = generation) {
  if (!token || currentGeneration !== generation) return;
  controller?.abort();
  controller = new AbortController();
  const requestController = controller;
  try {
    const next = await api('/state', token, currentGeneration, requestController);
    if (currentGeneration !== generation) return;
    const previousActiveId = activeSlot === null ? null : itemAt(activeSlot)?.id;
    state = next;
    frameLoaded = true;
    if (activeSlot !== null && itemAt(activeSlot)?.id !== previousActiveId) {
      stopBrowserAudio();
      activeSlot = null;
    }
    const filled = Object.keys(state.slots || {}).length;
    setStatus(`Datos cargados · ${filled} de 3 selecciones publicadas`, 'ok');
    render();

    // Resolve Firebase media URLs before a tap so playback can begin directly
    // from the user's gesture instead of waiting for another API request.
    for (const index of [0, 1, 2]) {
      if (itemAt(index)) loadMedia(index, currentGeneration).catch(() => {});
    }
    if (activeSlot !== null) loadMedia(activeSlot, currentGeneration).catch(() => {});
  } catch (error) {
    if (error.name !== 'AbortError' && currentGeneration === generation) {
      setStatus(`No se pudo consultar el cuadro: ${error.message}`, 'error');
    }
  } finally {
    if (currentGeneration === generation && token) pollTimer = setTimeout(() => syncFrame(currentGeneration), 3000);
  }
}

async function loadMedia(index, currentGeneration = generation) {
  const item = itemAt(index);
  if (!item) throw new Error('Este espacio no tiene música seleccionada.');
  if (imageCache.has(item.id)) return imageCache.get(item.id);
  if (mediaRequests.has(item.id)) return mediaRequests.get(item.id);
  const requestController = new AbortController();
  mediaControllers.set(item.id, requestController);
  const request = api(`/media/${index}`, token, currentGeneration, requestController)
    .then(media => {
      if (currentGeneration !== generation || itemAt(index)?.id !== item.id) throw new DOMException('Selección anterior', 'AbortError');
      imageCache.set(item.id, media);
      render();
      return media;
    })
    .finally(() => {
      mediaControllers.delete(item.id);
      mediaRequests.delete(item.id);
    });
  mediaRequests.set(item.id, request);
  return request;
}

function applyToken(value) {
  const nextToken = value.trim();
  if (!validToken(nextToken)) {
    generation += 1;
    clearTimeout(pollTimer);
    controller?.abort();
    playbackRequest += 1;
    for (const requestController of mediaControllers.values()) requestController.abort();
    mediaControllers.clear();
    mediaRequests.clear();
    stopBrowserAudio();
    token = '';
    state = {slots:{}, jobs:{}};
    frameLoaded = false;
    imageCache.clear();
    failedImages.clear();
    closeQr();
    activeSlot = null;
    sessionStorage.removeItem('sonoro-maqueta-token');
    render();
    setStatus('El ID debe tener entre 1 y 128 caracteres: letras, números, guion o guion bajo.', 'error');
    return;
  }
  generation += 1;
  clearTimeout(pollTimer);
  controller?.abort();
  playbackRequest += 1;
  for (const requestController of mediaControllers.values()) requestController.abort();
  mediaControllers.clear();
  mediaRequests.clear();
  stopBrowserAudio();
  token = nextToken;
  state = {slots:{}, jobs:{}};
  frameLoaded = false;
  imageCache.clear();
  failedImages.clear();
  closeQr();
  activeSlot = null;
  sessionStorage.setItem('sonoro-maqueta-token', token);
  setStatus('Consultando selecciones y portadas…');
  render();
  syncFrame(generation);
}


function chooseSlot(index) {
  if (!itemAt(index)) { setStatus(`El espacio ${index + 1} está vacío.`, 'error'); return; }
  if (activeSlot === index) {
    playbackRequest += 1;
    activeSlot = null;
    stopBrowserAudio();
    render();
    return;
  }
  const request = ++playbackRequest;
  activeSlot = index;
  previewAudio.pause();
  previewAudio.removeAttribute('src');
  previewAudio.load();
  render();
  playSelection(index, request, generation);
}
function stopBrowserAudio() {
  previewAudio.pause();
  previewAudio.removeAttribute('src');
  previewAudio.load();
}
async function playSelection(index, request, currentGeneration) {
  const item = itemAt(index);
  try {
    const media = await loadMedia(index, currentGeneration);
    if (request !== playbackRequest || currentGeneration !== generation || itemAt(index)?.id !== item?.id) return;
    if (!media.audio_url) throw new Error('No hay un enlace de audio para esta selección.');
    previewAudio.src = media.audio_url;
    previewAudio.volume = volumeLevel / 100;
    await previewAudio.play();
    render();
  } catch (error) {
    if (request !== playbackRequest || error.name === 'AbortError') return;
    setStatus(`No se pudo reproducir aquí: ${error.message}`, 'error');
    render();
  }
}

function showQr() {
  if (!token) {
    setStatus('Carga el ID del cuadro antes de mostrar su QR.', 'error');
    return;
  }
  if (!ensureQr()) return;
  qrVisible = true;
  renderScreen();
  clearInterval(qrClock);
  let left = 20;
  $('qr-countdown').hidden = false;
  $('qr-countdown').textContent = `${left} s`;
  qrClock = setInterval(() => {
    left -= 1;
    $('qr-countdown').textContent = `${left} s`;
    if (left <= 0) closeQr();
  }, 1000);
  clearTimeout(qrTimer);
  qrTimer = setTimeout(closeQr, 20000);
}
function closeQr() {
  const wasVisible = qrVisible;
  qrVisible = false;
  $('device-qr').hidden = true;
  if (wasVisible) renderScreen();
  clearInterval(qrClock);
  clearTimeout(qrTimer);
}
function showResetMessage(html, duration = 0) {
  $('reset-overlay').innerHTML = html;
  $('reset-overlay').hidden = false;
  clearTimeout(resetHideTimer);
  if (duration) resetHideTimer = setTimeout(() => { $('reset-overlay').hidden = true; }, duration);
}
function startCombo() {
  if (!pressed.has(1) || !pressed.has(2) || comboStarted) return;
  comboStarted = true;
  ignoredClicks.add(1);
  ignoredClicks.add(2);
  clearTimeout(longPressTimer);
  buttons[0].classList.remove('is-holding');
  comboStartedAt = Date.now();
  comboCompleted = false;
  showResetMessage('<strong>Restablecer Wi-Fi</strong>Mantén ambos botones · 5 s');
  comboClock = setInterval(() => {
    const left = Math.max(0, 5 - (Date.now() - comboStartedAt) / 1000);
    if (!comboCompleted) showResetMessage(`<strong>Restablecer Wi-Fi</strong>${left.toFixed(1)} s · suelta para cancelar`);
  }, 100);
  comboTimer = setTimeout(() => {
    comboCompleted = true;
    clearInterval(comboClock);
    showResetMessage('<strong>Wi-Fi restablecida</strong>Simulación · el cuadro real abriría su asistente local');
    resetHideTimer = setTimeout(() => { $('reset-overlay').hidden = true; }, 3800);
  }, 5000);
}
function cancelCombo() {
  if (!comboStarted || comboCompleted) return;
  clearTimeout(comboTimer);
  clearInterval(comboClock);
  comboStarted = false;
  showResetMessage('<strong>Acción cancelada</strong>La Wi-Fi no ha cambiado', 1500);
}
buttons.forEach((button, index) => {
  button.addEventListener('pointerdown', event => {
    button.setPointerCapture?.(event.pointerId);
    pressed.add(index);
    if (pressed.has(1) && pressed.has(2)) return startCombo();
    if (index === 0) {
      button.classList.add('is-holding');
      longPressTimer = setTimeout(() => {
        ignoredClicks.add(0);
        button.classList.remove('is-holding');
        showQr();
      }, 2000);
    }
  });
  const release = event => {
    pressed.delete(index);
    if (event?.type === 'pointercancel') ignoredClicks.delete(index);
    if (comboStarted) {
      cancelCombo();
      if (!pressed.size) { comboStarted = false; comboCompleted = false; }
    }
    if (index === 0) {
      clearTimeout(longPressTimer);
      button.classList.remove('is-holding');
    }
  };
  button.addEventListener('pointerup', release);
  button.addEventListener('pointercancel', release);
  button.addEventListener('click', event => {
    if (ignoredClicks.has(index)) {
      event.preventDefault();
      event.stopPropagation();
      ignoredClicks.delete(index);
      return;
    }
    chooseSlot(index);
  });
});
$('preview-audio').addEventListener('playing', render);
$('preview-audio').addEventListener('pause', render);
$('preview-audio').addEventListener('ended', () => { activeSlot = null; render(); });
$('album-cover').addEventListener('error', () => {
  const item = activeSlot === null ? null : itemAt(activeSlot);
  if (!item) return;
  failedImages.add(item.id);
  render();
});

let volumeLevel = 42;
let volumeMessageTimer;
function setVolume(value, announce = false) {
  volumeLevel = Math.max(0, Math.min(100, Math.round(value)));
  $('knob').style.setProperty('--turn', `${-135 + volumeLevel * 2.7}deg`);
  previewAudio.volume = volumeLevel / 100;
  $('knob').setAttribute('aria-label', `Rueda de volumen, ${volumeLevel} por ciento`);
  $('knob').title = `Volumen local: ${volumeLevel}%`;
  if (announce) {
    $('knob-value').textContent = `${volumeLevel}%`;
    $('knob-value').hidden = false;
    clearTimeout(volumeMessageTimer);
    volumeMessageTimer = setTimeout(() => { $('knob-value').hidden = true; }, 1100);
  }
}
const knob = $('knob');
knob.addEventListener('pointerdown', event => {
  event.preventDefault();
  knob.setPointerCapture(event.pointerId);
  const rect = knob.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  const update = pointer => {
    let angle = Math.atan2(pointer.clientY - centerY, pointer.clientX - centerX) * 180 / Math.PI + 90;
    if (angle > 180) angle -= 360;
    setVolume((Math.max(-135, Math.min(135, angle)) + 135) / 2.7, true);
  };
  update(event);
  const move = pointer => update(pointer);
  const end = () => {
    knob.removeEventListener('pointermove', move);
    knob.removeEventListener('pointerup', end);
    knob.removeEventListener('pointercancel', end);
  };
  knob.addEventListener('pointermove', move);
  knob.addEventListener('pointerup', end, {once:true});
  knob.addEventListener('pointercancel', end, {once:true});
});
knob.addEventListener('keydown', event => {
  if (event.key === 'ArrowUp' || event.key === 'ArrowRight') { event.preventDefault(); setVolume(volumeLevel + 5, true); }
  if (event.key === 'ArrowDown' || event.key === 'ArrowLeft') { event.preventDefault(); setVolume(volumeLevel - 5, true); }
});
setVolume(volumeLevel);
render();
const savedToken = getTokenFromUrl() || sessionStorage.getItem('sonoro-maqueta-token') || '';
if (savedToken) {
  applyToken(savedToken);
  if (location.hash) history.replaceState(history.state, '', `${location.pathname}${location.search}`);
} else {
  setStatus('Abre esta página con #token=<id-del-cuadro> para cargar su música.', 'error');
}
window.addEventListener('hashchange', () => {
  const linkedToken = getTokenFromUrl();
  if (!linkedToken) return;
  applyToken(linkedToken);
  history.replaceState(history.state, '', `${location.pathname}${location.search}`);
});
