const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const load = (storage, key, fallback) => { try { return JSON.parse(storage.getItem(key)) ?? fallback; } catch { return fallback; } };
const deploymentApiBase = document.querySelector('meta[name="sonoro-api-base"]')?.content.trim() || '';
const validFrameIdentifier = identifier => /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(identifier);
function consumeFrameToken() {
  const fragment = new URLSearchParams(location.hash.slice(1));
  if (!fragment.has('token')) return {present:false, token:''};
  const token = fragment.get('token') || '';
  history.replaceState(history.state, '', location.pathname + location.search);
  return {present:true, token};
}
const initialFrameLink = consumeFrameToken();
let config = load(localStorage, 'sonoro-config', {mode:'locked'});
config.url = deploymentApiBase;
config.token = sessionStorage.getItem('sonoro-token') || '';
let accessMessage = '';
if (initialFrameLink.present) {
  sessionStorage.removeItem('sonoro-token');
  config.token = '';
  if (validFrameIdentifier(initialFrameLink.token)) {
    config.token = initialFrameLink.token;
    sessionStorage.setItem('sonoro-token', config.token);
    config.url = deploymentApiBase || config.url;
    config.mode = config.url ? 'real' : 'locked';
    if (!config.url) accessMessage = 'Este sitio todavía no tiene configurada la dirección del servicio del cuadro.';
  } else {
    config.mode = 'locked';
    accessMessage = 'El identificador debe tener entre 1 y 128 caracteres: letras, números, guion o guion bajo.';
  }
} else if (config.mode === 'demo') {
  sessionStorage.removeItem('sonoro-token');
  config.token = '';
} else if (!validFrameIdentifier(config.token)) {
  sessionStorage.removeItem('sonoro-token');
  config.token = '';
  config.mode = 'locked';
  accessMessage = 'No hay un enlace de acceso activo. Abre el enlace del cuadro o prueba la demostración.';
} else if (config.mode === 'locked') {
  if(config.token&&config.url)config.mode='real';
  else accessMessage = config.token?'El identificador está guardado en esta pestaña, pero este sitio no tiene configurada la dirección del servicio.':'No hay un enlace de acceso activo. Abre el enlace del cuadro o prueba la demostración.';
} else if (!config.url) {
  config.mode = 'locked';
  accessMessage = 'Este sitio todavía no tiene configurada la dirección del servicio del cuadro.';
}
localStorage.setItem('sonoro-config', JSON.stringify({mode:config.mode,url:config.url}));
let demo = load(localStorage, 'sonoro-demo', {slots:{},jobs:{}});
for (const j of Object.values(demo.jobs)) if (['queued','downloading','processing','uploading'].includes(j.status)) Object.assign(j,{status:'error',message:'La demostración se interrumpió. Puedes reintentar.'});
let state = config.mode === 'demo' ? demo : {slots:{},jobs:{}};
let currentSlot = 0, searchController, searchVersion = 0, toastTimeout, pollingTimer = null, polling = false, lastPollError = false, frameGeneration = 0;
let playingTrackId = null;
const apiControllers = new Set();
const active = new Set(['queued','downloading','processing','uploading']);
const demoTimers = new Map();
const mediaCache = new Map();
const stages = ['queued','downloading','processing','uploading'];
const saveDemo = () => localStorage.setItem('sonoro-demo', JSON.stringify(demo));
function toast(message) { $('toast').textContent=message; $('toast').classList.add('show'); clearTimeout(toastTimeout); toastTimeout=setTimeout(()=>$('toast').classList.remove('show'),4400); }
function showError(id,message) { $(id).textContent=message; $(id).hidden=!message; }
function stopPlayback(updateView=true) {
  const audio=$('audio');audio.pause();audio.removeAttribute('src');audio.load();playingTrackId=null;
  if(updateView)render();
}
async function api(path,options={}) {
  const generation=frameGeneration, externalSignal=options.signal;
  if(!config.token)throw new ApiError(401,'Falta el identificador del cuadro. Abre el enlace del cuadro.');
  const base=config.url||deploymentApiBase;
  if(!base)throw new Error('Este sitio no tiene configurada la dirección del servicio del cuadro.');
  const controller=new AbortController();apiControllers.add(controller);
  const abort=()=>controller.abort();
  const timeout=setTimeout(abort,90000);
  externalSignal?.addEventListener('abort',abort,{once:true});
  try{
    const {signal,...requestOptions}=options;
    const response=await fetch(base.replace(/\/$/,'')+path,{...requestOptions,headers:{'Content-Type':'application/json',Authorization:'Bearer '+config.token,...options.headers},signal:controller.signal});
    if(generation!==frameGeneration)throw abortError();
    if(response.status===401){
      const message='El identificador falta o no tiene un formato válido para el cuadro.';
      lockFrameAccess(message,generation);
      throw new ApiError(401,message);
    }
    let data; try {data=await response.json();} catch {throw new Error('El servicio no respondió como se esperaba. Si está arrancando, espera un momento y reintenta.');}
    if(generation!==frameGeneration)throw abortError();
    if(!response.ok)throw new ApiError(response.status,typeof data.detail==='string'?data.detail:'No se pudo completar la operación.');
    return data;
  }finally{
    clearTimeout(timeout);externalSignal?.removeEventListener('abort',abort);apiControllers.delete(controller);
  }
}
class ApiError extends Error { constructor(status,message){super(message);this.status=status;} }
function abortError(){const error=new Error('La solicitud anterior se canceló al cambiar de cuadro.');error.name='AbortError';return error;}
function resetFrameContext(closeSettings=true){
  frameGeneration++;
  if(pollingTimer)clearTimeout(pollingTimer);
  pollingTimer=null;polling=false;lastPollError=false;
  searchController?.abort();searchController=null;searchVersion++;
  for(const controller of apiControllers)controller.abort();
  apiControllers.clear();mediaCache.clear();state={slots:{},jobs:{}};currentSlot=0;
  if($('picker').open)$('picker').close();
  $('audio').pause();$('audio').removeAttribute('src');$('audio').load();playingTrackId=null;
}
function lockFrameAccess(message,generation=frameGeneration){
  if(generation!==frameGeneration)return;
  resetFrameContext();sessionStorage.removeItem('sonoro-token');config.token='';config.mode='locked';
  localStorage.setItem('sonoro-config',JSON.stringify({mode:config.mode,url:config.url}));accessMessage=message;render();
}
function applyFrameLink(token){
  resetFrameContext();sessionStorage.removeItem('sonoro-token');config.token='';
  if(validFrameIdentifier(token)){
    config.token=token;sessionStorage.setItem('sonoro-token',token);
    config.url=deploymentApiBase||config.url||'';
    config.mode=config.url?'real':'locked';
    accessMessage=config.url?'':'El enlace se ha leído, pero este sitio no tiene una URL predeterminada para la API.';
  }else{
    config.mode='locked';accessMessage='El identificador debe tener entre 1 y 128 caracteres: letras, números, guion o guion bajo.';
  }
  localStorage.setItem('sonoro-config',JSON.stringify({mode:config.mode,url:config.url}));
  render();if(config.mode==='real')startPolling();
}
window.addEventListener('hashchange',()=>{const link=consumeFrameToken();if(link.present)applyFrameLink(link.token);});
window.addEventListener('pagehide',()=>resetFrameContext());
window.addEventListener('pageshow',event=>{if(event.persisted&&config.mode==='real')startPolling();});
function slotJob(i) { return Object.values(state.jobs||{}).filter(j=>j.slot===i).sort((a,b)=>b.created_at-a.created_at)[0]; }
function render() {
  const demoMode=config.mode==='demo';
  $('mode-button').innerHTML=demoMode?'Salir de demostración <span>↗</span>':config.mode==='real'?'Cuadro conectado':'Probar demostración <span>↗</span>';
  $('mode-button').disabled=config.mode==='real';
  $('access-error').textContent=accessMessage;$('access-error').hidden=!accessMessage;
  $('demo-note').hidden=!demoMode;
  $('picker-demo').hidden=!demoMode;
  $('count').textContent=String(Object.keys(state.slots||{}).length).padStart(2,'0')+' / 03 espacios ocupados';
  $('slots').innerHTML=[0,1,2].map(i=>{
    const item=state.slots?.['slot-'+i], job=slotJob(i), number=String(i+1).padStart(2,'0');
    const running=job&&active.has(job.status), failed=job?.status==='error';
    let content,caption;
    if(running){
      const stage=stages.indexOf(job.status);
      const percent=Number.isFinite(job.percent)?Math.max(0,Math.min(100,job.percent)):null;
      content=`<div class="busy-art"><div class="disc" aria-hidden="true"></div><p class="busy-title">${esc(job.message)}</p><div class="progressbar ${percent===null?'indeterminate':''}" role="progressbar" aria-label="${esc(job.message)}" ${percent===null?'':`aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100"`}><span style="width:${percent===null?'30':percent}%"></span></div><div class="progress-label"><span>${demoMode?'Progreso simulado':`Etapa ${stage+1} de 4`}</span><span>${percent===null?'En curso':`${job.estimated?'≈ ':''}${percent}%`}</span></div><div class="steps" aria-hidden="true">${stages.map((_,s)=>`<i class="${s<stage?'done':s===stage?'current':''}"></i>`).join('')}</div><button class="cancel-link" data-action="cancel" data-slot="${i}">Cancelar</button></div>`;
      caption=`<div><h3>${esc(job.title)}</h3><p class="artist-line">${esc(job.artist)}</p></div><span class="caption-mark">${number}</span>`;
    }else if(failed){
      content=`<div class="error-art"><span class="error-symbol">↻</span><p>${esc(job.message)}</p><button class="small-button" data-action="retry" data-slot="${i}">Reintentar</button><button class="cancel-link" data-action="dismiss" data-slot="${i}">${item?'Volver al favorito':'Elegir otra canción'}</button></div>`;
      caption=`<div><h3>${esc(job.title)}</h3><p class="artist-line">Importación pendiente</p></div><span class="caption-mark">${number}</span>`;
    }else if(item){
      const image=mediaCache.get(item.id)?.image_url;
      const isPlaying=playingTrackId===item.id;
      content=`<div class="art v${i}">${image?`<img src="${esc(image)}" alt="Imagen de ${esc(item.title)}" loading="lazy">`:''}<span class="art-badge">${demoMode?'DEMO · ':''}${item.kind==='station'?'EN DIRECTO':'TU CANCIÓN'}</span><span class="art-title">${esc(item.title)}</span><button class="art-play ${isPlaying?'is-playing':''}" data-action="toggle-playback" data-slot="${i}" aria-label="${isPlaying?'Detener':'Reproducir'} ${esc(item.title)}" aria-pressed="${isPlaying}" title="${isPlaying?'Detener':'Reproducir'}"><span aria-hidden="true">${isPlaying?'■':'▶'}</span></button></div>`;
      caption=`<div style="min-width:0"><h3>${esc(item.title)}</h3><p class="artist-line">${esc(item.artist)}</p></div><div class="slot-actions"><button data-action="edit" data-slot="${i}" aria-label="Cambiar favorito ${number}">↗</button><button data-action="remove" data-slot="${i}" aria-label="Vaciar espacio ${number}">×</button></div>`;
    }else{
      content=`<button class="empty" data-action="add" data-slot="${i}"><span class="plus" aria-hidden="true">+</span><span class="empty-title">Añade tu música</span><span class="empty-detail">Una canción o una emisora</span></button>`;
      caption=`<span class="slot-label">ESPACIO ${number}</span><span class="caption-mark">Aún por descubrir</span>`;
    }
    return `<article class="slot" aria-label="Espacio ${number}"><div class="frame">${content}</div><div class="slot-caption">${caption}</div></article>`;
  }).join('');
}
function setTab(type){const song=type==='song';$('song-tab').setAttribute('aria-selected',song);$('radio-tab').setAttribute('aria-selected',!song);$('search-form').hidden=!song;$('radio-form').hidden=song;$('results').replaceChildren();showError('search-error','');$('search-status').hidden=true;searchController?.abort();searchVersion++;}
function openPicker(i){currentSlot=i;$('slot-label').textContent='ESPACIO '+String(i+1).padStart(2,'0');$('search-form').reset();$('radio-form').reset();setTab('song');$('picker').showModal();setTimeout(()=>$('artist').focus(),30);}
$('song-tab').onclick=()=>setTab('song');$('radio-tab').onclick=()=>setTab('station');
$('picker').addEventListener('close',()=>{searchController?.abort();searchVersion++;$('search-button').disabled=false;});
$('search-form').onsubmit=async event=>{
  event.preventDefault(); const artist=$('artist').value.trim(), title=$('song').value.trim();if(!artist||!title)return;
  const version=++searchVersion;searchController?.abort();searchController=new AbortController();
  $('search-button').disabled=true;$('search-status').hidden=false;$('results').replaceChildren();showError('search-error','');
  try{
    let results;
    if(config.mode==='demo'){
      await new Promise(resolve=>setTimeout(resolve,1100));
      results=[{id:'demo-'+Date.now(),title,artist,duration:214},{id:'demo-'+Date.now()+'-live',title:title+' · En directo',artist,duration:248}];
    }else{results=(await api('/search',{method:'POST',body:JSON.stringify({artist,title}),signal:searchController.signal})).results;}
    if(version!==searchVersion)return;
    const heading=document.createElement('p');heading.className='result-heading';heading.textContent=results.length?'Elige la versión que quieres guardar.':'No encontramos coincidencias. Prueba con otro título.';$('results').append(heading);
    for(const result of results){
      const button=document.createElement('button');button.type='button';button.className='result';
      button.innerHTML=`${result.image?`<img class="result-image" alt="" src="${esc(result.image)}">`:'<span class="result-image" aria-hidden="true"></span>'}<span class="result-info"><strong>${esc(result.title)}</strong><small>${esc(result.artist)}${result.duration?' · '+Math.floor(result.duration/60)+':'+String(Math.floor(result.duration%60)).padStart(2,'0'):''}</small></span><span class="result-add" aria-hidden="true">+</span>`;
      button.onclick=async()=>{button.disabled=true;try{await importSong(result);$('picker').close();}catch(error){showError('search-error',error.message);button.disabled=false;}};
      $('results').append(button);
    }
  }catch(error){if(version===searchVersion&&error.name!=='AbortError')showError('search-error',error.message);}
  finally{if(version===searchVersion){$('search-button').disabled=false;$('search-status').hidden=true;}}
};
async function importSong(result,slot=currentSlot){
  if(config.mode==='demo'){startDemo(result,slot);return;}
  const generation=frameGeneration;
  const job=await api('/imports',{method:'POST',body:JSON.stringify({slot,source_id:result.id,title:result.title,artist:result.artist})});
  if(generation!==frameGeneration)return;
  state.jobs[job.id]=job;render();
}
function startDemo(result,slot){
  const id=crypto.randomUUID();const job={id,slot,title:result.title,artist:result.artist,source_id:result.id,status:'queued',percent:null,message:'En la cola de demostración',created_at:Date.now()/1000};demo.jobs[id]=job;state=demo;
  const updates=[
    [600,'downloading',0,'Descargando audio · demo'],[1100,'downloading',25,'Descargando audio · demo'],[1600,'downloading',60,'Descargando audio · demo'],[2100,'downloading',100,'Descargando audio · demo'],
    [2500,'processing',null,'Preparando audio e imagen · demo'],[3800,'uploading',0,'Guardando en la biblioteca · demo'],[4200,'uploading',45,'Guardando en la biblioteca · demo'],[4800,'uploading',85,'Guardando en la biblioteca · demo'],[5300,'ready',100,'Disponible · demo']
  ];
  demoTimers.set(id,updates.map(([delay,status,percent,message])=>setTimeout(()=>{
    if(!demo.jobs[id]||demo.jobs[id].status==='cancelled')return;
    Object.assign(job,{status,percent,message});
    if(status==='ready'){demo.slots['slot-'+slot]={id,kind:'song',title:result.title,artist:result.artist};demoTimers.delete(id);toast('Favorito de demostración añadido. No se ha descargado audio.');}
    saveDemo();if(config.mode==='demo')render();
  },delay)));
  saveDemo();render();
}
$('radio-form').onsubmit=async event=>{
  event.preventDefault();const generation=frameGeneration,title=$('radio-name').value.trim(),url=$('radio-url').value.trim();
  try{
    if(new URL(url).protocol!=='https:')throw new Error('Utiliza un enlace de streaming HTTPS.');
    if(config.mode==='demo'){demo.slots['slot-'+currentSlot]={id:crypto.randomUUID(),kind:'station',title,artist:'Radio en directo',url};for(const [id,job]of Object.entries(demo.jobs))if(job.slot===currentSlot)delete demo.jobs[id];saveDemo();state=demo;}
    else{await api('/stations',{method:'POST',body:JSON.stringify({slot:currentSlot,title,url})});if(generation!==frameGeneration)return;await refresh(generation);}
    if(generation!==frameGeneration)return;
    $('picker').close();render();toast(config.mode==='demo'?'Emisora de ejemplo guardada en este navegador.':'Emisora guardada.');
  }catch(error){if(generation===frameGeneration&&error.name!=='AbortError')showError('search-error',error.message);}
};
$('slots').onclick=async event=>{
  const button=event.target.closest('button[data-action]');if(!button)return;const generation=frameGeneration,i=Number(button.dataset.slot),action=button.dataset.action,job=slotJob(i);
  try{
    if(action==='add'||action==='edit')return openPicker(i);
    if(action==='retry'){await importSong({id:job.source_id,title:job.title,artist:job.artist},i);return;}
    if(action==='cancel'){
      if(config.mode==='demo'){(demoTimers.get(job.id)||[]).forEach(clearTimeout);demoTimers.delete(job.id);job.status='cancelled';saveDemo();}
      else{await api('/jobs/'+job.id+'/cancel',{method:'POST'});if(generation!==frameGeneration)return;await refresh(generation);}if(generation!==frameGeneration)return;render();return;
    }
    if(action==='dismiss'){
      if(config.mode==='demo'){delete demo.jobs[job.id];saveDemo();render();}
      else{job.status='cancelled';render();openPicker(i);}return;
    }
    if(action==='remove'){
      if(!confirm('¿Vaciar este espacio?'))return;
      if(config.mode==='demo'){delete demo.slots['slot-'+i];for(const [id,j]of Object.entries(demo.jobs))if(j.slot===i)delete demo.jobs[id];saveDemo();}
      else{const removed=state.slots?.['slot-'+i];if(removed&&removed.id===playingTrackId)stopPlayback();const result=await api('/slots/'+i,{method:'DELETE'});if(generation!==frameGeneration)return;await refresh(generation);if(result.cleanup_pending)toast('El hueco se vació; algunos archivos siguen pendientes de limpieza.');else if(result.deleted_objects)toast('El favorito y sus archivos se eliminaron definitivamente.');}if(generation!==frameGeneration)return;render();return;
    }
    if(action==='toggle-playback'){
      if(config.mode==='demo'){toast('El favorito de demostración no tiene audio real. Abre un enlace de cuadro para escuchar canciones.');return;}
      const item=state.slots?.['slot-'+i];if(!item)return;
      if(playingTrackId===item.id){stopPlayback();return;}
      const media=await api('/media/'+i);if(generation!==frameGeneration||state.slots?.['slot-'+i]?.id!==item.id)return;
      const audio=$('audio');audio.src=media.audio_url;playingTrackId=item.id;render();
      try{await audio.play();}catch(error){stopPlayback();throw error;}
    }
  }catch(error){if(generation===frameGeneration&&error.name!=='AbortError')toast(error.message||'No se pudo completar la acción.');}
};
 $('audio').addEventListener('ended',()=>stopPlayback());
$('mode-button').onclick=()=>{
  if(config.mode==='real')return;
  resetFrameContext();sessionStorage.removeItem('sonoro-token');config.token='';
  config.mode=config.mode==='demo'?'locked':'demo';
  state=config.mode==='demo'?demo:{slots:{},jobs:{}};
  accessMessage=config.mode==='demo'?'':'Abre el enlace del cuadro para acceder a su colección.';
  localStorage.setItem('sonoro-config',JSON.stringify({mode:config.mode}));render();
};
async function refresh(generation=frameGeneration){
  if(generation!==frameGeneration||config.mode!=='real'||!config.token)return;
  const next=await api('/state');if(generation!==frameGeneration||config.mode!=='real')return;if(playingTrackId&&!Object.values(next.slots||{}).some(track=>track.id===playingTrackId))stopPlayback(false);state=next;render();
  for(const [key,item]of Object.entries(state.slots||{}))if(item.image_key&&!mediaCache.has(item.id)){
    mediaCache.set(item.id,{});try{const media=await api('/media/'+Number(key.replace('slot-','')));if(generation!==frameGeneration||state.slots?.[key]?.id!==item.id)return;mediaCache.set(item.id,media);render();}catch(error){mediaCache.delete(item.id);if(error.name!=='AbortError'&&generation===frameGeneration)throw error;}
  }
}
function startPolling(){
  if(pollingTimer)clearTimeout(pollingTimer);pollingTimer=null;
  const generation=frameGeneration;
  const poll=async()=>{
    if(generation!==frameGeneration||config.mode!=='real'||!config.token)return;
    polling=true;
    try{await refresh(generation);lastPollError=false;}
    catch(error){if(generation===frameGeneration&&error.name!=='AbortError'&&!lastPollError)toast('Se perdió la conexión. Reintentando…');if(generation===frameGeneration)lastPollError=true;}
    finally{if(generation===frameGeneration){polling=false;if(config.mode==='real'&&config.token)pollingTimer=setTimeout(poll,1500);}}
  };
  poll();
}
render();if(config.mode==='real')startPolling();
