<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>LoLドラフト</title>
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>

<style>
body{
 background:#0a1428;
 color:white;
 text-align:center;
 font-family:sans-serif;
}
.pack{
 display:flex;
 justify-content:center;
 gap:10px;
 margin:20px;
}
.card{
 width:80px;
 height:100px;
 position:relative;
 cursor:pointer;
}
.card img{
 width:100%;
 height:100%;
 border-radius:8px;
}
.lock{
 position:absolute;
 top:0;
 left:0;
 width:100%;
 height:100%;
 background:rgba(0,0,0,0.6);
}
</style>
</head>

<body>

<h1>LoLドラフト</h1>
<h2 id="turn"></h2>
<div>ラウンド: <span id="round"></span></div>
<div>残り時間: <span id="time"></span></div>

<button onclick="startGame()">スタート</button>

<div class="pack" id="pack"></div>

<h3>ブルー</h3>
<div id="blue"></div>

<h3>レッド</h3>
<div id="red"></div>

<script>
const socket = io();
const role = "{{ role }}";
let state = {};
let order = [];

function imgUrl(champ){
 return `https://ddragon.leagueoflegends.com/cdn/13.24.1/img/champion/${champ.image}.png`;
}

function startGame(){
 socket.emit("start");
}

socket.on("state", s=>{
 state = s;
 render();
});

function render(){
 if(!state.started){
   document.getElementById("turn").innerText = "待機中";
   return;
 }

 order = [
  ["blue","red","red","blue","blue","red","red","blue","blue","red"],
  ["red","blue","blue","red","red","blue","blue","red","red","blue"],
  ["blue","red","red","blue","blue","red","red","blue","blue","red"]
 ][state.round-1];

 const current = order[state.turn];

 document.getElementById("turn").innerText =
  current==="blue" ? "ブルーのターン" : "レッドのターン";

 document.getElementById("round").innerText = state.round;
 document.getElementById("time").innerText = state.time;

 // パック
 const pack = document.getElementById("pack");
 pack.innerHTML = "";

 state.pack.forEach(champ=>{
  const div = document.createElement("div");
  div.className = "card";

  const clickable = role === current;

  div.innerHTML = `
   <img src="${imgUrl(champ)}"
        onerror="this.src='https://via.placeholder.com/80x100'">
   ${!clickable ? '<div class="lock"></div>' : ''}
  `;

  if(clickable){
   div.onclick = ()=>pick(champ.name);
  }

  pack.appendChild(div);
 });

 // ピック表示
 ["blue","red"].forEach(team=>{
  const el = document.getElementById(team);
  el.innerHTML = "";

  state.picks[team].forEach(c=>{
   el.innerHTML += `<img src="${imgUrl(c)}" width="50">`;
  });
 });
}

function pick(name){
 socket.emit("pick", {role: role, champ: name});
}
</script>

</body>
</html>
