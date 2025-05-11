const chatEl = document.getElementById('chat');
chatEl.innerHTML = '';
const socket = io({ transports:['websocket'] });

function scrollDown(){ chatEl.scrollTop = chatEl.scrollHeight; }

function addMsg(d){
  const div = document.createElement('div');
  div.className='message'; div.dataset.id=d.id;
  div.innerHTML=`<strong>${d.username}</strong> [${d.timestamp}]: ${d.content}`;
  if(IS_ADMIN||IS_MOD){
    const btn = document.createElement('button');
    btn.textContent='Delete';
    btn.onclick = ()=>del(d.id,div);
    div.append(' ',btn);
  }
  chatEl.append(div);
  scrollDown();
}

function del(id,el){
  fetch(`/delete_message/${id}`,{method:'POST'})
    .then(r=>r.ok&&el.remove());
}

socket.on('status', d=>{
  const s=document.createElement('div');
  s.className='status'; s.innerText=d.msg;
  chatEl.append(s); scrollDown();
});
socket.on('message', addMsg);
socket.on('delete_message', o=>{
  const el=document.querySelector(`.message[data-id="${o.id}"]`);
  if(el) el.remove();
});

document.getElementById('send').onclick = ()=>{
  const m=document.getElementById('msg');
  const v=m.value.trim();
  if(v){
    socket.emit('message',{username:USERNAME,msg:v,room:ROOM});
    m.value='';
  }
};

socket.emit('join',{username:USERNAME,room:ROOM});
fetch(`/get_messages/${ROOM}`)
  .then(r=>r.json())
  .then(arr=>arr.forEach(addMsg));
