/* Multilingual Video Studio — local Whisper transcription, no paid APIs */
const $ = id => document.getElementById(id);
const MODEL = 'Xenova/whisper-tiny';
const TRANSFORMERS_CDN = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1/+esm';
let videoUrl = null;
let captions = [];
let active = false;
let cancelled = false;
let asr = null;
let modelLoading = null;
let captionId = 0;
let currentCaptureStop = null;
const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

function toast(msg){const t=$('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3200)}
function status(msg,percent){$('asrStatus').textContent=msg;if(Number.isFinite(percent)){$('asrProgress').classList.remove('hidden');$('asrProgress').value=Math.max(0,Math.min(100,percent))}}
function fmtSrt(s){const ms=Math.max(0,Math.round(Number(s||0)*1000));const h=Math.floor(ms/3600000),m=Math.floor(ms%3600000/60000),sec=Math.floor(ms%60000/1000),milli=ms%1000;return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')},${String(milli).padStart(3,'0')}`}
function validCaptions(){return captions.filter(c=>c.text.trim()&&Number.isFinite(c.start)&&Number.isFinite(c.end)&&c.end>c.start).sort((a,b)=>a.start-b.start)}
function render(){const host=$('captionList');host.innerHTML='';captions.forEach((c,i)=>{const row=document.createElement('div');row.className='caption-row';const start=document.createElement('input');start.type='number';start.min='0';start.step='.1';start.value=c.start.toFixed(2);start.title='Start time in seconds';start.setAttribute('aria-label',`Caption ${i+1} start seconds`);start.addEventListener('input',()=>c.start=Number(start.value));const end=document.createElement('input');end.type='number';end.min='0';end.step='.1';end.value=c.end.toFixed(2);end.title='End time in seconds';end.setAttribute('aria-label',`Caption ${i+1} end seconds`);end.addEventListener('input',()=>c.end=Number(end.value));const text=document.createElement('input');text.type='text';text.value=c.text;text.setAttribute('aria-label',`Caption ${i+1} text`);text.addEventListener('input',()=>c.text=text.value);const del=document.createElement('button');del.textContent='×';del.title='Delete caption';del.onclick=()=>{captions.splice(i,1);render()};row.append(start,end,text,del);host.append(row)});updateOverlay()}
function updateOverlay(){const v=$('video');const t=v.currentTime;const match=validCaptions().find(c=>t>=c.start&&t<c.end);const el=$('captionOverlay');el.textContent=match?.text||'';el.classList.toggle('hidden',!match)}
$('video').addEventListener('timeupdate',updateOverlay);
$('video').addEventListener('seeked',updateOverlay);
$('videoInput').addEventListener('change',e=>{const f=e.target.files?.[0];if(!f)return;if(videoUrl)URL.revokeObjectURL(videoUrl);videoUrl=URL.createObjectURL(f);$('video').src=videoUrl;$('videoWrap').classList.remove('hidden');$('videoName').textContent=`${f.name} · ${(f.size/1024/1024).toFixed(1)} MB`;captions=[];render();$('transcribeBtn').disabled=false;status('Ready. Tap Generate captions from video. This captures audio locally, then runs Whisper.');$('asrProgress').classList.add('hidden');toast('Video ready')});
$('addCaption').onclick=()=>{const last=captions[captions.length-1];const start=last?Number(last.end)+.1:0;captions.push({id:++captionId,start,end:start+3,text:''});render()};
function download(blob,name){const a=document.createElement('a');const u=URL.createObjectURL(blob);a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),30000)}
$('downloadSrt').onclick=()=>{const list=validCaptions();if(!list.length)return toast('No captions yet. Generate or add caption text first.');const srt=list.map((c,i)=>`${i+1}\n${fmtSrt(c.start)} --> ${fmtSrt(c.end)}\n${c.text.trim()}\n`).join('\n');download(new Blob(['\ufeff',srt],{type:'text/plain;charset=utf-8'}),'captions.srt');toast(`${list.length} caption(s) exported`)};
$('downloadNotes').onclick=()=>{download(new Blob([JSON.stringify({source_language:$('sourceLang').value,target_language:$('targetLang').value,model:MODEL,captions:validCaptions()},null,2)],{type:'application/json'}),'video-project.json')};
$('cancelBtn').onclick=()=>{cancelled=true;status('Stopping after the current operation...');if(currentCaptureStop)currentCaptureStop()};
function ensureRunning(){if(cancelled)throw new Error('Processing stopped by user')}
function downsample(samples,inputRate,outputRate=16000){if(inputRate===outputRate)return samples;const length=Math.round(samples.length*outputRate/inputRate);const result=new Float32Array(length);const ratio=inputRate/outputRate;for(let i=0;i<length;i++){const pos=i*ratio;const lo=Math.floor(pos);const hi=Math.min(lo+1,samples.length-1);result[i]=(samples[lo]||0)*(1-(pos-lo))+(samples[hi]||0)*(pos-lo)}return result}
function concatFloat32(chunks,total){const data=new Float32Array(total);let off=0;for(const chunk of chunks){data.set(chunk,off);off+=chunk.length}return data}

// Record the selected video's decoded audio via Web Audio. Unlike FFmpeg.wasm,
// this does not need a large WASM binary and works on many Android Chrome devices.
// Capture is real-time, so it takes as long as the video playback.
async function captureVideoAudio(){
  const file=$('videoInput').files?.[0];if(!file)throw new Error('Choose a video first');
  const maxSeconds=mobile?8*60:20*60;
  const preview=$('video');
  if(!Number.isFinite(preview.duration)||preview.duration<=0){await new Promise((resolve,reject)=>{const onReady=()=>{cleanup();resolve()};const onError=()=>{cleanup();reject(new Error('Unable to read video duration'))};const cleanup=()=>{preview.removeEventListener('loadedmetadata',onReady);preview.removeEventListener('error',onError)};preview.addEventListener('loadedmetadata',onReady,{once:true});preview.addEventListener('error',onError,{once:true});preview.load()})}
  if(preview.duration>maxSeconds)throw new Error(`Video is too long for this version (${Math.round(preview.duration)} seconds). Limit: ${maxSeconds/60} minutes.`);
  if(!window.AudioContext&&!window.webkitAudioContext)throw new Error('Web Audio is unavailable in this browser');
  const Context=window.AudioContext||window.webkitAudioContext;
  const ctx=new Context();
  const player=document.createElement('video');player.preload='auto';player.playsInline=true;player.src=videoUrl;player.crossOrigin='anonymous';player.volume=1;player.muted=false;
  const source=ctx.createMediaElementSource(player);
  const processor=ctx.createScriptProcessor(4096,2,1);
  const silent=ctx.createGain();silent.gain.value=0;
  source.connect(processor);processor.connect(silent);silent.connect(ctx.destination);
  const chunks=[];let total=0;let finished=false;
  processor.onaudioprocess=e=>{if(finished)return;const buffer=e.inputBuffer;const n=buffer.length;const mono=new Float32Array(n);const a=buffer.getChannelData(0);const b=buffer.numberOfChannels>1?buffer.getChannelData(1):null;for(let i=0;i<n;i++)mono[i]=b?(a[i]+b[i])*.5:a[i];chunks.push(mono);total+=n};
  let resolveEnd,rejectEnd;
  const ended=new Promise((resolve,reject)=>{resolveEnd=resolve;rejectEnd=reject});
  const finish=(error)=>{if(finished)return;finished=true;player.pause();player.removeAttribute('src');player.load();processor.disconnect();source.disconnect();silent.disconnect();ctx.close().catch(()=>{});currentCaptureStop=null;if(error)rejectEnd(error);else resolveEnd()};
  currentCaptureStop=()=>finish(new Error('Processing stopped by user'));
  player.addEventListener('ended',()=>finish(),{once:true});
  player.addEventListener('error',()=>finish(new Error('Browser could not decode this video. Try an MP4 with AAC audio.')),{once:true});
  const tick=setInterval(()=>{if(finished){clearInterval(tick);return}status(`Capturing audio locally: ${Math.round(player.currentTime)} / ${Math.round(preview.duration)} seconds. Keep this screen open.`,Math.min(48,48*player.currentTime/preview.duration))},1000);
  try{await ctx.resume();await player.play();await ended;}catch(err){finish(err);throw err}finally{clearInterval(tick)}
  ensureRunning();
  if(total<ctx.sampleRate*0.25)throw new Error('No audio was captured. Make sure the video contains an audio track.');
  const raw=concatFloat32(chunks,total);
  const peak=raw.reduce((m,v)=>Math.max(m,Math.abs(v)),0);
  if(peak<0.00005)throw new Error('Audio was silent or inaccessible. Try an MP4 with an AAC audio track.');
  return downsample(raw,ctx.sampleRate,16000)
}

async function loadASR(){
  if(asr)return asr;
  if(modelLoading)return modelLoading;
  modelLoading=(async()=>{
    status('Loading the Whisper engine. First use downloads model files; please wait.',52);
    const {pipeline,env}=await import(TRANSFORMERS_CDN);
    env.allowLocalModels=false;
    env.useBrowserCache=true;
    // WASM CPU works across more Android and Windows devices than WebGPU.
    asr=await pipeline('automatic-speech-recognition',MODEL,{device:'wasm',dtype:'q8',progress_callback:info=>{
      if(info.status==='progress'&&info.file){const pct=Number(info.progress);status(`Downloading AI model: ${info.file}${Number.isFinite(pct)?` (${pct.toFixed(0)}%)`:''}`,52)}else if(info.status==='ready')status('Whisper model ready.',55);
    }});
    return asr;
  })();
  try{return await modelLoading}catch(e){modelLoading=null;throw e}
}
function getLanguage(){const code=$('sourceLang').value;return ({tel:'telugu',hin:'hindi',eng:'english'})[code]||undefined}
function normalizeChunks(output,offset,chunkDuration){const list=[];if(Array.isArray(output.chunks)&&output.chunks.length){for(const c of output.chunks){const txt=(c.text||'').trim();if(!txt)continue;const t=c.timestamp||[];let start=Number.isFinite(t[0])?t[0]:0;let end=Number.isFinite(t[1])?t[1]:Math.min(chunkDuration,start+4);start=Math.max(0,Math.min(start,chunkDuration));end=Math.max(start+.15,Math.min(end,chunkDuration));list.push({id:++captionId,start:offset+start,end:offset+end,text:txt})}}else if((output.text||'').trim()){list.push({id:++captionId,start:offset,end:offset+chunkDuration,text:output.text.trim()})}return list}
async function transcribeAudio(samples){const model=await loadASR();ensureRunning();const segmentSeconds=20;const samplesPerChunk=segmentSeconds*16000;const count=Math.ceil(samples.length/samplesPerChunk);const lines=[];for(let i=0;i<count;i++){ensureRunning();const start=i*samplesPerChunk;const end=Math.min(samples.length,start+samplesPerChunk);const audio=samples.slice(start,end);const duration=audio.length/16000;const rms=Math.sqrt(audio.reduce((sum,x)=>sum+x*x,0)/audio.length);if(rms>0.001){status(`Transcribing part ${i+1} of ${count} on this device...`,55+Math.round(43*i/count));const opts={return_timestamps:true,task:'transcribe'};const lang=getLanguage();if(lang)opts.language=lang;const output=await model(audio,opts);lines.push(...normalizeChunks(output,start/16000,duration));captions=lines.slice();render()}else{status(`Skipping quiet part ${i+1} of ${count}...`,55+Math.round(43*i/count))}}
  return lines;
}
$('transcribeBtn').onclick=async()=>{if(active)return;active=true;cancelled=false;$('transcribeBtn').disabled=true;$('cancelBtn').classList.remove('hidden');$('asrProgress').classList.remove('hidden');captions=[];render();try{
  status('Preparing audio capture...',0);
  const samples=await captureVideoAudio();ensureRunning();status(`Audio captured (${(samples.length/16000).toFixed(1)} sec). Preparing local AI...`,50);
  const result=await transcribeAudio(samples);ensureRunning();status(result.length?`Complete: generated ${result.length} caption(s). Edit them below or download SRT.`:'Whisper did not detect speech. Try a clearer video or choose the correct spoken language.',100);toast(result.length?'Real captions generated':'No speech detected');
}catch(err){console.error(err);status(`Transcription failed: ${err.message||String(err)}\nTry a shorter MP4 with AAC audio and keep the app in the foreground.`);toast('Transcription not completed')}finally{active=false;currentCaptureStop=null;$('transcribeBtn').disabled=!videoUrl;$('cancelBtn').classList.add('hidden')}};
let promptEvent=null;window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();promptEvent=e;$('installBtn').classList.remove('hidden')});$('installBtn').onclick=async()=>{if(!promptEvent){toast('Use Chrome menu → Add to Home screen / Install app');return}promptEvent.prompt();await promptEvent.userChoice;promptEvent=null;$('installBtn').classList.add('hidden')};
if('serviceWorker' in navigator&&location.protocol!=='file:')window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(err=>console.warn('Service worker:',err)));
render();
