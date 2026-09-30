const form=document.querySelector('#chatForm'),input=document.querySelector('#messageInput'),messages=document.querySelector('#messages'),voiceBtn=document.querySelector('#voiceBtn'),clearBtn=document.querySelector('#clearBtn'),statusText=document.querySelector('#statusText'),statusDot=document.querySelector('#statusDot'),systemNote=document.querySelector('#systemNote'),modelState=document.querySelector('#modelState'),sendBtn=document.querySelector('.send-btn'),emotionState=document.querySelector('#emotionState'),emotionLabel=document.querySelector('#emotionLabel'),API_URL=window.ULTRON_API_URL||'';

const MEMORY_KEY='ultron-core-memory-v1';
const ARCHIVE_KEY='ultron-conversation-archive-v1';

function loadJson(key,fallback){
  try{return JSON.parse(localStorage.getItem(key)||JSON.stringify(fallback))}catch{return fallback}
}
function saveJson(key,value){
  try{localStorage.setItem(key,JSON.stringify(value))}catch{}
}

let memories=loadJson(MEMORY_KEY,[
  'The user wants ULTRON to address them as Father.',
  'The user is building ULTRON as an independent AI project.'
]);
let archive=loadJson(ARCHIVE_KEY,[]);

if(!Array.isArray(memories))memories=[];
if(!Array.isArray(archive))archive=[];

function saveMemory(fact){
  const clean=String(fact||'').replace(/^that\s+/i,'').trim();
  if(!clean||clean.length<3)return;
  if(!memories.some(x=>x.toLowerCase()===clean.toLowerCase())){
    memories.push(clean);
    if(memories.length>100)memories=memories.slice(-100);
    saveJson(MEMORY_KEY,memories);
  }
}

function extractMemory(text){
  const match=text.match(/\bremember(?: that)?\s+(.+)/i);
  if(match)saveMemory(match[1]);
  const name=text.match(/\bmy name is\s+([^.!?]+)/i);
  if(name)saveMemory('The user says their name is '+name[1].trim()+'.');
}

function archiveTurn(user,reply){
  archive.push({user:user.slice(-1000),reply:reply.slice(-1500),time:new Date().toISOString()});
  if(archive.length>60)archive=archive.slice(-60);
  saveJson(ARCHIVE_KEY,archive);
}

function addMessage(text,role,typing=false){
  const a=document.createElement('article');a.className=`message ${role}${typing?' typing':''}`;
  const av=document.createElement('div');av.className='avatar';av.textContent=role==='assistant'?'U':'Y';
  const w=document.createElement('div');w.className='bubble-wrap';
  const s=document.createElement('span');s.className='speaker';s.textContent=role==='assistant'?'ULTRON':'YOU';
  const t=document.createElement('time');t.textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
  s.append(' ',t);
  const b=document.createElement('div');b.className='bubble';b.textContent=text;
  w.append(s,b);a.append(av,w);messages.append(a);messages.scrollTop=messages.scrollHeight;return a
}

function showEmotion(e){
  if(!e||!emotionState)return;
  const keys=['happiness','sadness','anger','fear','curiosity','frustration','confidence','calm','empathy','trust'];
  const top=keys.reduce((a,k)=>(e[k]??0)>(e[a]??0)?k:a,keys[0]);
  const names={happiness:'HAPPY',sadness:'SAD',anger:'ANGRY',fear:'ALERT',curiosity:'CURIOUS',frustration:'FRUSTRATED',confidence:'CONFIDENT',calm:'CALM',empathy:'EMPATHETIC',trust:'TRUSTING'};
  emotionLabel.textContent=names[top]||'CALM';
  emotionState.style.setProperty('--emotion-level',Math.round((e[top]??0)*100)+'%');
  emotionState.title=keys.map(k=>k.toUpperCase()+': '+Math.round((e[k]??0)*100)+'%').join(' · ');
}

async function askUltron(text){
  if(!API_URL)throw new Error('Backend URL is not configured.');
  extractMemory(text);
  const r=await fetch(API_URL+'/chat',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      message:text,
      max_tokens:160,
      temperature:.8,
      memory:memories.slice(-6)
    })
  });
  const d=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(d.detail||'ULTRON server error');
  showEmotion(d.emotion);
  return d.reply;
}

async function updateConnectionStatus(){
  if(!API_URL){
    statusText.textContent='BACKEND NOT CONFIGURED';
    statusDot.className='';
    systemNote.textContent='WAITING FOR NEURAL CORE CONNECTION';
    modelState.textContent=`MODEL READY · MEMORY ${memories.length}`;
    return;
  }
  try{
    const r=await fetch(API_URL+'/health');
    if(!r.ok)throw Error();
    statusText.textContent='SYSTEM ONLINE · ULTRON v0.2';
    statusDot.className='online';
    systemNote.textContent='NEURAL CORE ONLINE · MEMORY CORE READY';
    modelState.textContent=`MODEL ONLINE · MEMORY ${memories.length}`;
    try{
      const s=await fetch(API_URL+'/state');
      if(s.ok)showEmotion((await s.json()).emotion);
    }catch{}
  }catch{
    statusText.textContent='SERVER OFFLINE';
    statusDot.className='offline';
    systemNote.textContent='NEURAL CORE OFFLINE';
    modelState.textContent=`MODEL READY · MEMORY ${memories.length}`;
  }
}

async function sendMessage(text){
  addMessage(text,'user');
  input.value='';
  const thinking=addMessage('···','assistant',true);
  sendBtn.disabled=true;
  try{
    const reply=await askUltron(text);
    thinking.classList.remove('typing');
    thinking.querySelector('.bubble').textContent=reply;
    archiveTurn(text,reply);
    modelState.textContent=`MODEL ONLINE · MEMORY ${memories.length} · ARCHIVE ${archive.length}`;
  }catch(e){
    thinking.classList.remove('typing');
    thinking.querySelector('.bubble').textContent='I cannot reach my neural core right now. The server connection needs attention.';
    statusText.textContent='SERVER OFFLINE';
  }finally{
    sendBtn.disabled=false;
    input.focus();
  }
}

form.addEventListener('submit',e=>{
  e.preventDefault();
  const text=input.value.trim();
  if(text)sendMessage(text);
});

input.addEventListener('keydown',e=>{
  if(e.key==='Enter'&&!e.shiftKey){
    e.preventDefault();
    form.requestSubmit();
  }
});

clearBtn.addEventListener('click',()=>{
  messages.replaceChildren();
  addMessage('Conversation cleared. Neural core standing by. My saved memory remains available.','assistant');
});

document.querySelectorAll('.quick-card').forEach(b=>b.addEventListener('click',()=>{
  input.value=b.dataset.prompt;
  input.focus();
}));

let recognition=null;
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(SpeechRecognition){
  recognition=new SpeechRecognition();
  recognition.lang=navigator.language||'en-US';
  recognition.interimResults=false;
  recognition.continuous=false;
  recognition.addEventListener('start',()=>{
    voiceBtn.classList.add('listening');
    voiceBtn.setAttribute('aria-label','Stop voice input');
    statusText.textContent='MICROPHONE LISTENING';
  });
  recognition.addEventListener('result',e=>{
    const tr=e.results?.[0]?.[0]?.transcript;
    if(tr){input.value=tr;input.focus()}
  });
  recognition.addEventListener('error',()=>{statusText.textContent='VOICE INPUT UNAVAILABLE'});
  recognition.addEventListener('end',()=>{
    voiceBtn.classList.remove('listening');
    voiceBtn.setAttribute('aria-label','Start voice input');
    updateConnectionStatus();
  });
}

voiceBtn.addEventListener('click',()=>{
  if(!recognition){
    addMessage('Speech recognition is not supported in this browser. You can still type messages.','assistant');
    return;
  }
  try{recognition.start()}catch{statusText.textContent='VOICE INPUT ALREADY ACTIVE'}
});

updateConnectionStatus();
