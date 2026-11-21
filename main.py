python
import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

ENDPOINTS = {
    "text2img": "https://deepai.org",
    "image-editor": "https://deepai.org",
    "background-remover": "https://deepai.org",
    "colorizer": "https://deepai.org",
    "torch-srgan": "https://deepai.org",
    "waifu2x": "https://deepai.org",
    "creative-upscale": "https://deepai.org",
    "image-replace": "https://deepai.org",
    "text2video": "https://deepai.org",
    "img2video": "https://deepai.org",
}

HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DeepAI Console</title>
<style>
body{background:#0f172a;color:#f8fafc;font-family:system-ui,sans-serif;margin:0;padding:20px}
.wrap{max-width:960px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:768px){.wrap{grid-template-columns:1fr}}
.box{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:16px}
input,select,textarea,button{width:100%;padding:9px;margin-top:6px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#fff;box-sizing:border-box}
button{background:#3b82f6;border:none;font-weight:700;cursor:pointer;margin-top:12px}
button.sec{background:#475569}
pre{background:#020617;padding:12px;border-radius:6px;overflow:auto;max-height:420px;color:#38bdf8;font-size:12px;white-space:pre-wrap;word-break:break-all}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;z-index:9}
.modal-in{background:#1e293b;padding:24px;border-radius:10px;width:90%;max-width:380px}
.hide{display:none!important}
img,video{max-width:100%;border-radius:6px;margin-top:10px}
</style>
</head>
<body>
<div id="keyModal" class="modal">
<div class="modal-in">
<h3>Enter DeepAI API Key</h3>
<input type="password" id="keyInput" placeholder="Paste API key">
<button onclick="setKey(false)">Save & Open</button>
<button class="sec" onclick="setKey(true)">Verify Key</button>
<p id="keyMsg" style="font-size:13px"></p>
</div>
</div>

<div class="wrap">
<div class="box">
<div style="display:flex;justify-content:space-between;align-items:center">
<b>DeepAI API</b>
<button class="sec" style="width:auto;margin:0;padding:5px 10px" onclick="document.getElementById('keyModal').classList.remove('hide')">API Key</button>
</div>
<select id="ep" onchange="toggle()">
<option value="text2img">text2img</option>
<option value="image-editor">image-editor</option>
<option value="background-remover">background-remover</option>
<option value="colorizer">colorizer</option>
<option value="torch-srgan">torch-srgan</option>
<option value="waifu2x">waifu2x</option>
<option value="creative-upscale">creative-upscale</option>
<option value="image-replace">image-replace</option>
<option value="text2video">text2video</option>
<option value="img2video">img2video</option>
</select>
<form onsubmit="runReq(event)">
<div id="fTxt"><textarea id="txt" rows="3" placeholder="Prompt / text"></textarea></div>
<div id="fImg" class="hide">
<input type="file" id="imgF" accept="image/*">
<input type="text" id="imgU" placeholder="Or Image URL">
</div>
<div id="fMsk" class="hide">
<input type="file" id="mskF" accept="image/*">
<input type="text" id="mskU" placeholder="Or Mask URL">
</div>
<div id="fImgOpt">
<select id="ver"><option value="">version (default)</option><option>standard</option><option>hd</option><option>genius</option><option>super_genius</option></select>
<select id="res"><option value="">resolution (default)</option><option>2k</option><option>4k</option></select>
<input type="number" id="w" placeholder="width">
<input type="number" id="h" placeholder="height">
<input type="text" id="neg" placeholder="negative_prompt">
</div>
<div id="fVidOpt" class="hide">
<select id="mode"><option value="">mode (default)</option><option>hd</option><option>hollywood</option></select>
<input type="number" id="dur" placeholder="duration (5-15)">
<input type="text" id="shp" placeholder="shape (16:9)">
</div>
<button id="btn">Send Request</button>
</form>
<div id="vidBox" class="hide" style="margin-top:12px">
<input type="text" id="jobId" placeholder="Video Job ID">
<button class="sec" type="button" onclick="vidStatus()">Check Video Status</button>
</div>
</div>

<div class="box">
<b>Raw Response</b>
<pre id="out">Ready.</pre>
<div id="media"></div>
</div>
</div>

<script>
let K=sessionStorage.getItem("k")||"";
if(K)document.getElementById("keyModal").classList.add("hide");
toggle();

function toggle(){
const e=document.getElementById("ep").value;
document.getElementById("fTxt").classList.toggle("hide",!["text2img","image-editor","image-replace","text2video","img2video"].includes(e));
document.getElementById("fImg").classList.toggle("hide",e==="text2img"||e==="text2video");
document.getElementById("fMsk").classList.toggle("hide",e!=="image-replace");
document.getElementById("fImgOpt").classList.toggle("hide",!["text2img","image-editor"].includes(e));
const v=["text2video","img2video"].includes(e);
document.getElementById("fVidOpt").classList.toggle("hide",!v);
document.getElementById("vidBox").classList.toggle("hide",!v);
}

async function setKey(test){
const v=document.getElementById("keyInput").value.trim();
if(!v)return;
K=v;sessionStorage.setItem("k",K);
if(!test){document.getElementById("keyModal").classList.add("hide");return;}
document.getElementById("keyMsg").innerText="Testing...";
const r=await fetch("/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({k:K})});
const d=await r.json();
document.getElementById("out").textContent=JSON.stringify(d,null,2);
document.getElementById("keyMsg").innerText="HTTP "+d.status;
if(d.status===200)document.getElementById("keyModal").classList.add("hide");
}

async function runReq(ev){
ev.preventDefault();
if(!K)return document.getElementById("keyModal").classList.remove("hide");
const b=document.getElementById("btn");b.disabled=true;b.innerText="Loading...";
const e=document.getElementById("ep").value;
const fd=new FormData();
fd.append("k",K);fd.append("ep",e);
const t=document.getElementById("txt").value.trim();
if(t)fd.append(["text2video","img2video"].includes(e)?"prompt":"text",t);
if(document.getElementById("imgF").files)fd.append("image_file",document.getElementById("imgF").files);
else if(document.getElementById("imgU").value)fd.append("image_url",document.getElementById("imgU").value);
if(document.getElementById("mskF").files)fd.append("mask_file",document.getElementById("mskF").files);
else if(document.getElementById("mskU").value)fd.append("mask_url",document.getElementById("mskU").value);
[["image_generator_version","ver"],["resolution","res"],["width","w"],["height","h"],["negative_prompt","neg"],["mode","mode"],["duration","dur"],["shape","shp"]].forEach(([k,id])=>{
const val=document.getElementById(id).value;if(val)fd.append(k,val);
});
try{
const r=await fetch("/proxy",{method:"POST",body:fd});
const d=await r.json();
document.getElementById("out").textContent=JSON.stringify(d,null,2);
if(d.body&&d.body.id)document.getElementById("jobId").value=d.body.id;
showMedia(d.body&&d.body.output_url);
}catch(err){document.getElementById("out").textContent=err;}
b.disabled=false;b.innerText="Send Request";
}

async function vidStatus(){
const id=document.getElementById("jobId").value.trim();
if(!id||!K)return;
const r=await fetch("/status",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({k:K,id:id})});
const d=await r.json();
document.getElementById("out").textContent=JSON.stringify(d,null,2);
showMedia(d.body&&d.body.output_url);
}

function showMedia(u){
const m=document.getElementById("media");
if(!u){m.innerHTML="";return;}
m.innerHTML=u.includes(".mp4")?`<video src="${u}" controls autoplay loop></video>`:`<img src="${u}">`;
}
</script>
</body>
</html>"""

def fmt(r):
    try:
        b = r.json()
    except Exception:
        b = r.text
    return {"status": r.status_code, "body": b}

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/verify", methods=["POST"])
def verify():
    k = (request.get_json(silent=True) or {}).get("k", "")
    r = requests.post(ENDPOINTS["text2img"], headers={"api-key": k}, data={"text": "test"}, timeout=30)
    return jsonify(fmt(r))

@app.route("/proxy", methods=["POST"])
def proxy():
    k = request.form.get("k", "")
    ep = request.form.get("ep", "")
    url = ENDPOINTS.get(ep)
    if not url:
        return jsonify({"status": 400, "body": "bad endpoint"}), 400
    data = {f: request.form[f] for f in ["text", "prompt", "image_generator_version", "resolution", "width", "height", "negative_prompt", "mode", "duration", "shape"] if request.form.get(f)}
    files = {}
    if "image_file" in request.files and request.files["image_file"].filename:
        f = request.files["image_file"]
        files["image"] = (f.filename, f.stream, f.mimetype)
    elif request.form.get("image_url"):
        data["image"] = request.form["image_url"]
    if "mask_file" in request.files and request.files["mask_file"].filename:
        m = request.files["mask_file"]
        files["mask"] = (m.filename, m.stream, m.mimetype)
    elif request.form.get("mask_url"):
        data["mask"] = request.form["mask_url"]
    r = requests.post(url, headers={"api-key": k}, data=data, files=files or None, timeout=120)
    return jsonify(fmt(r))

@app.route("/status", methods=["POST"])
def status():
    j = request.get_json(silent=True) or {}
    r = requests.get(f"https://deepai.org{j.get('id', '')}", headers={"api-key": j.get("k", "")}, timeout=30)
    return jsonify(fmt(r))

if __name__ == "__main__":
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
