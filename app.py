from flask import Flask, request, send_file, render_template_string
from gtts import gTTS
import pyttsx3
import uuid, os

app = Flask(__name__)

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Echo Tone TTS</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');

body { margin:0; font-family: Arial,sans-serif; background:#111; color:white; transition:0.3s; }
h1 { text-align:center; font-family:'Orbitron', sans-serif; font-size:48px; color:#0f0; margin-top:20px; }

.container { display:flex; justify-content:center; flex-wrap:wrap; gap:40px; padding:20px; max-width:1200px; margin:auto;}
.box { flex:1 1 300px; background:#222; padding:20px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.4); min-width:300px; transition:0.3s;}
textarea { width:100%; height:150px; border:none; border-radius:10px; padding:10px; font-size:16px; resize:none; }
.controls { display:flex; gap:15px; margin-top:15px; flex-wrap:wrap; justify-content:center;}
button { padding:10px 15px; border:none; border-radius:8px; cursor:pointer; background:#0f0; color:#111; transition:0.2s; }
button:hover { transform:scale(1.05); }
select,input[type=range] { width:100%; margin-top:10px; padding:5px; border-radius:5px; border:none; }
label { margin-top:10px; display:block; }
.toggle { position: relative; width:50px; height:25px; background:#444; border-radius:30px; cursor:pointer; margin-top:10px; }
.toggle-circle { position:absolute; width:20px; height:20px; background:yellow; border-radius:50%; top:2.5px; left:3px; transition:0.3s; }
canvas { width:100%; height:50px; border-radius:5px; margin-top:15px; background:#222; display:block; }
audio { margin-top:15px; width:100%; border-radius:5px; }
</style>
</head>
<body>
<h1>ECHO TONE</h1>
<div class="container">
  <!-- Left: Text + Audio -->
  <div class="box">
    <h2>Enter Text</h2>
    <textarea id="ttsText" placeholder="Type something..."></textarea>
    <div class="controls">
      <button onclick="playTTS()">▶ Play</button>
      <button onclick="pauseTTS()">⏸ Pause</button>
      <button onclick="downloadAudio()">📥 Download</button>
    </div>
    <audio id="audio" controls></audio>
    <canvas id="waveform"></canvas>
  </div>

  <!-- Right: Settings -->
  <div class="box">
    <h2>Settings</h2>
    <label>Language</label>
    <select id="language">
      <option value="en">English</option>
      <option value="hi">Hindi</option>
      <option value="te">Telugu</option>
      <option value="ta">Tamil</option>
      <option value="ml">Malayalam</option>
      <option value="kn">Kannada</option>
    </select>
    <label>Voice</label>
    <select id="voice">
      <option value="male">Male</option>
      <option value="female">Female</option>
    </select>
    <label>Volume</label>
    <input type="range" id="volume" min="0" max="1" step="0.01" value="1">
    <label>Speed</label>
    <input type="range" id="rate" min="0.5" max="2" step="0.05" value="1">
    <label>Dark / Light</label>
    <div class="toggle" id="themeToggle"><div class="toggle-circle" id="circle"></div></div>
  </div>
</div>

<script>
let audio = document.getElementById("audio");
let lastFile = "";

// Play TTS
async function playTTS(){
    const text = document.getElementById("ttsText").value;
    const voice = document.getElementById("voice").value;
    const lang = document.getElementById("language").value;
    if(!text) return alert("Enter some text!");
    const res = await fetch(`/speak?text=${encodeURIComponent(text)}&voice=${voice}&lang=${lang}`);
    const blob = await res.blob();
    lastFile = URL.createObjectURL(blob);
    audio.src = lastFile;
    audio.volume = document.getElementById("volume").value;
    audio.playbackRate = document.getElementById("rate").value;
    audio.play();
}

// Pause TTS
function pauseTTS(){ if(audio.paused) audio.play(); else audio.pause(); }

// Download
function downloadAudio(){
    if(!lastFile) return alert("Generate speech first!");
    const link = document.createElement("a");
    link.href = lastFile;
    link.download = "speech.mp3";
    link.click();
}

// Live volume & speed
document.getElementById("volume").addEventListener("input", ()=>{ audio.volume = document.getElementById("volume").value; });
document.getElementById("rate").addEventListener("input", ()=>{ audio.playbackRate = document.getElementById("rate").value; });

// Theme toggle
const toggle = document.getElementById("themeToggle");
const circle = document.getElementById("circle");
toggle.addEventListener("click", ()=>{
    toggle.classList.toggle("active");
    circle.style.left = toggle.classList.contains("active")?"27px":"3px";
    const dark = !toggle.classList.contains("active");
    document.body.style.background = dark?"#111":"#eee";
    document.body.style.color = dark?"#fff":"#111";
    document.querySelectorAll(".box").forEach(b=>b.style.background = dark?"#222":"#ddd");
});

// Waveform using Web Audio API
const canvas = document.getElementById("waveform");
const ctx = canvas.getContext("2d");
const audioCtx = new (window.AudioContext||window.webkitAudioContext)();
const analyser = audioCtx.createAnalyser();
let source;

audio.addEventListener("play", ()=>{
    if(!source){
        source = audioCtx.createMediaElementSource(audio);
        source.connect(analyser);
        analyser.connect(audioCtx.destination);
        analyser.fftSize = 64;
    }
});

function drawWaveform(){
    requestAnimationFrame(drawWaveform);
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteFrequencyData(dataArray);
    ctx.clearRect(0,0,canvas.width,canvas.height);
    const barWidth = canvas.width / bufferLength;
    for(let i=0;i<bufferLength;i++){
        const barHeight = dataArray[i]/2;
        ctx.fillStyle="#0f0";
        ctx.fillRect(i*barWidth, canvas.height-barHeight, barWidth*0.6, barHeight);
    }
}
drawWaveform();
</script>
</body>
</html>
"""

def generate_tts(text, voice_type, lang, filename):
    os.makedirs("static", exist_ok=True)
    if voice_type=="female" or lang!="en":
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
    else:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[0].id if voices else None)
        engine.save_to_file(text, filename)
        engine.runAndWait()

@app.route('/')
def index(): return render_template_string(html_template)

@app.route('/speak')
def speak():
    text = request.args.get("text","")
    voice = request.args.get("voice","male")
    lang = request.args.get("lang","en")
    filename = f"static/temp_{uuid.uuid4().hex}.mp3"
    generate_tts(text, voice, lang, filename)
    return send_file(filename, mimetype="audio/mpeg", as_attachment=False)

@app.route('/download')
def download():
    text = request.args.get("text","")
    voice = request.args.get("voice","male")
    lang = request.args.get("lang","en")
    filename = f"static/tts_{uuid.uuid4().hex}.mp3"
    generate_tts(text, voice, lang, filename)
    return send_file(filename, mimetype="audio/mpeg", as_attachment=True, download_name="speech.mp3")

if __name__=="__main__":
    app.run(debug=True, port=5001)

