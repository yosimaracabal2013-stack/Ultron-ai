const bootScreen=document.querySelector('#bootScreen'),bootProgress=document.querySelector('#bootProgress'),bootStatus=document.querySelector('#bootStatus');
const bootMessages=['INITIALIZING NEURAL CORE','LOADING MEMORY MATRIX','CONNECTING LOCAL MODEL','SYSTEM CHECK COMPLETE','ULTRON ONLINE'];
let bootIndex=0;
const bootTimer=setInterval(()=>{bootIndex=Math.min(bootIndex+1,bootMessages.length-1);if(bootStatus)bootStatus.textContent=bootMessages[bootIndex]},520);
setTimeout(()=>{clearInterval(bootTimer);if(bootProgress)bootProgress.style.width='100%';if(bootStatus)bootStatus.textContent='ULTRON ONLINE';setTimeout(()=>bootScreen?.classList.add('done'),450)},2850);

const form=document.querySelector('#chatForm'),input=document.querySelector('#messageInput'),messages=document.querySelector('#messages'),voiceBtn=document.querySelector('#voiceBtn'),clearBtn=document.querySelector('#clearBtn'),statusText=document.querySelector('#statusText'),statusDot=document.querySelector('#statusDot'),systemNote=document.querySelector('#systemNote'),modelState=document.querySelector('#modelState'),sendBtn=document.querySelector('.send-btn'),head=document.querySelector('#ultronHead'),emotionState=document.querySelector('#emotionState'),emotionLabel=document.querySelector('#emotionLabel'),researchForm=document.querySelector('#researchForm'),researchInput=document.querySelector('#researchInput'),researchResults=document.querySelector('#researchResults'),memoryForm=document.querySelector('#memoryForm'),memoryInput=document.querySelector('#memoryInput'),memoryList=document.querySelector('#memoryList'),memoryCount=document.querySelector('#memoryCount'),speakToggle=document.querySelector('#speakToggle'),API_URL=window.ULTRON_API_URL||window.location.origin;

const MEMORY_KEY='ultron-core-memory-v1',ARCHIVE_KEY='ultron-conversation-archive-v1';
let memories=loadJson(MEMORY_KEY,['The user wants ULTRON to address them as Father.','The user is building ULTRON as an independent AI project.','The user prefers direct answers and practical actions over unnecessary explanations.','The user values honest reporting about what works and what remains broken.','The user prefers efficient mobile-friendly workflows.','The user is interested in artificial intelligence, creativity, and futuristic technology.']);
let archive=loadJson(ARCHIVE_KEY,[]);
let voiceEnabled=loadJson('ultron-voice-enabled-v1',true);
if(!Array.isArray(memories))memories=[];if(!Array.isArray(archive))archive=[];

function loadJson(key,fallback){try{return JSON.parse(localStorage.getItem(key)||JSON.stringify(fallback))}catch{return fallback}}
function saveJson(key,value){try{localStorage.setItem(key,JSON.stringify(value))}catch{}}
function saveMemory(fact){const clean=String(fact||'').replace(/^that\s+/i,'').trim();if(!clean||clean.length<3)return;if(!memories.some(x=>x.toLowerCase()===clean.toLowerCase())){memories.push(clean);if(memories.length>100)memories=memories.slice(-100);saveJson(MEMORY_KEY,memories)}renderMemory()}
function extractMemory(text){const match=text.match(/\bremember(?: that)?\s+(.+)/i);if(match)saveMemory(match[1])}
function archiveTurn(user,reply){archive.push({user:user.slice(-1000),reply:reply.slice(-1500),time:new Date().toISOString()});if(archive.length>60)archive=archive.slice(-60);saveJson(ARCHIVE_KEY,archive)}

function renderMemory(){memoryCount.textContent=String(memories.length);memoryList.replaceChildren();if(!memories.length){const e=document.createElement('div');e.className='empty-state';e.textContent='MEMORY EMPTY';memoryList.append(e);return}memories.slice(-5).reverse().forEach(f=>{const x=document.createElement('div');x.className='memory-item';x.textContent=f;memoryList.append(x)})}

function addMessage(text,role,typing=false){const a=document.createElement('article');a.className='message '+role+(typing?' typing':'');const tag=document.createElement('div');tag.className='message-tag';tag.textContent=role==='assistant'?'ULTRON · '+(typing?'THINKING':'READY'):'YOU';const b=document.createElement('div');b.className='bubble';b.textContent=text;a.append(tag,b);messages.append(a);messages.scrollTop=messages.scrollHeight;return a}

function showEmotion(e){if(!e)return;const keys=['happiness','sadness','anger','fear','curiosity','frustration','confidence','calm','empathy','trust'];const top=keys.reduce((a,k)=>(e[k]??0)>(e[a]??0)?k:a,keys[0]);const names={happiness:'HAPPY',sadness:'SAD',anger:'ANGRY',fear:'ALERT',curiosity:'CURIOUS',frustration:'FRUSTRATED',confidence:'CONFIDENT',calm:'CALM',empathy:'EMPATHETIC',trust:'TRUSTING'};emotionLabel.textContent=names[top]||'CALM';emotionState.title=keys.map(k=>k.toUpperCase()+': '+Math.round((e[k]??0)*100)+'%').join(' · ')}

function setSpeaking(on){head.classList.toggle('speaking',!!on);systemNote.textContent=on?'SPEAKING':'NEURAL CORE ONLINE'}
function speak(text){if(!voiceEnabled||!('speechSynthesis'in window)||!text)return;window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text.replace(/^Father,\s*/i,''));u.rate=.96;u.pitch=.72;u.volume=1;u.onstart=()=>setSpeaking(true);u.onend=()=>setSpeaking(false);u.onerror=()=>setSpeaking(false);window.speechSynthesis.speak(u)}
function toggleVoice(){voiceEnabled=!voiceEnabled;saveJson('ultron-voice-enabled-v1',voiceEnabled);speakToggle.textContent=voiceEnabled?'VOICE ON':'VOICE OFF';speakToggle.classList.toggle('active',voiceEnabled);if(!voiceEnabled&&'speechSynthesis'in window){window.speechSynthesis.cancel();setSpeaking(false)}}
speakToggle.addEventListener('click',toggleVoice);speakToggle.textContent=voiceEnabled?'VOICE ON':'VOICE OFF';speakToggle.classList.toggle('active',voiceEnabled);

async function askUltron(text){extractMemory(text);const r=await fetch(API_URL+'/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,max_tokens:56,temperature:.8,memory:memories.slice(-6)})});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||'ULTRON server error');showEmotion(d.emotion);return d.reply}

async function research(query){researchResults.innerHTML='<div class="empty-state">RESEARCHING…</div>';const r=await fetch(API_URL+'/research?q='+encodeURIComponent(query));const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||'Research failed');researchResults.replaceChildren();if(!d.results?.length){const e=document.createElement('div');e.className='empty-state';e.textContent='NO SOURCES FOUND';researchResults.append(e);return}d.results.forEach(item=>{const card=document.createElement('a');card.className='research-card';card.href=item.url;card.target='_blank';card.rel='noopener noreferrer';const title=document.createElement('strong');title.textContent=item.title;const desc=document.createElement('small');desc.textContent=(item.description||'Source available on Wikipedia').replace(/<[^>]*>/g,'').slice(0,220);const source=document.createElement('em');source.textContent=String(item.source||'SOURCE').toUpperCase();card.append(title,desc,source);researchResults.append(card)})}

async function updateConnectionStatus(){try{const r=await fetch(API_URL+'/health');if(!r.ok)throw Error();statusText.textContent='SYSTEM ONLINE';statusDot.className='online';systemNote.textContent='NEURAL CORE ONLINE';modelState.textContent='LOCAL MODEL READY';try{const s=await fetch(API_URL+'/state');if(s.ok)showEmotion((await s.json()).emotion)}catch{}}catch{statusText.textContent='SERVER OFFLINE';statusDot.className='offline';systemNote.textContent='NEURAL CORE OFFLINE';modelState.textContent='WAITING FOR SERVER'}}

async function sendMessage(text){addMessage(text,'user');input.value='';const thinking=addMessage('···','assistant',true);sendBtn.disabled=true;setSpeaking(false);try{const reply=await askUltron(text);thinking.classList.remove('typing');thinking.querySelector('.message-tag').textContent='ULTRON · NOW';thinking.querySelector('.bubble').textContent=reply;archiveTurn(text,reply);modelState.textContent='LOCAL MODEL · '+memories.length+' MEMORIES';speak(reply)}catch(e){thinking.classList.remove('typing');thinking.querySelector('.message-tag').textContent='ULTRON · ERROR';thinking.querySelector('.bubble').textContent='I cannot reach my neural core right now. The server connection needs attention.';statusText.textContent='SERVER OFFLINE'}finally{sendBtn.disabled=false;input.focus()}}

form.addEventListener('submit',e=>{e.preventDefault();const text=input.value.trim();if(text)sendMessage(text)});
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();form.requestSubmit()}});

researchForm?.addEventListener('submit',async e=>{e.preventDefault();const q=researchInput.value.trim();if(!q)return;try{await research(q)}catch{researchResults.innerHTML='<div class="empty-state">RESEARCH OFFLINE</div>'}});
memoryForm?.addEventListener('submit',e=>{e.preventDefault();const fact=memoryInput.value.trim();if(!fact)return;saveMemory(fact);memoryInput.value=''});

clearBtn.addEventListener('click',()=>{messages.replaceChildren();addMessage('Conversation cleared. Neural core standing by. Saved memory remains available.','assistant')});
document.querySelectorAll('.quick-card').forEach(()=>{});

let recognition=null;const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(SpeechRecognition){recognition=new SpeechRecognition();recognition.lang=navigator.language||'en-US';recognition.interimResults=false;recognition.continuous=false;recognition.addEventListener('start',()=>{voiceBtn.classList.add('listening');head.classList.add('listening');statusText.textContent='MIC LISTENING';systemNote.textContent='LISTENING'});recognition.addEventListener('result',e=>{const tr=e.results?.[0]?.[0]?.transcript;if(tr){input.value=tr;input.focus();form.requestSubmit()}});recognition.addEventListener('error',()=>{statusText.textContent='MIC UNAVAILABLE';head.classList.remove('listening')});recognition.addEventListener('end',()=>{voiceBtn.classList.remove('listening');head.classList.remove('listening');updateConnectionStatus()})}
voiceBtn.addEventListener('click',()=>{if(!recognition){addMessage('Speech recognition is not supported in this browser. You can still type messages.','assistant');return}try{recognition.start()}catch{}});

renderMemory();updateConnectionStatus();
