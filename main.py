import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

API_BASE = "https://api.deepai.org/api/"
ENDPOINTS = {
    "text2img": "text2img",
    "image-editor": "image-editor",
    "background-remover": "background-remover",
    "colorizer": "colorizer",
    "torch-srgan": "torch-srgan",
    "waifu2x": "waifu2x",
    "creative-upscale": "creative-upscale",
    "image-replace": "image-replace",
    "text2video": "text2video",
    "img2video": "img2video",
}

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DeepAI Feature Tester</title>
<style>
:root{color-scheme:dark}
body{background:#0f172a;color:#f8fafc;font-family:system-ui,sans-serif;margin:0;padding:16px}
.wrap{max-width:1050px;margin:auto;display:grid;grid-template-columns:1fr 1.2fr;gap:16px}
@media(max-width:800px){.wrap{grid-template-columns:1fr}}
.box{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:16px}
input,select,textarea,button{width:100%;padding:9px;margin-top:6px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#fff;box-sizing:border-box}
button{background:#3b82f6;border:0;font-weight:700;cursor:pointer;margin-top:10px}
button.sec{background:#475569}
button.grn{background:#10b981;color:#022c22}
button:disabled{opacity:.5;cursor:not-allowed}
pre{background:#020617;padding:12px;border-radius:6px;overflow:auto;max-height:460px;color:#38bdf8;font-size:12px;white-space:pre-wrap;word-break:break-all}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;z-index:9}
.modal-in{background:#1e293b;padding:24px;border-radius:10px;width:90%;max-width:380px}
.hide{display:none!important}
.row{display:flex;justify-content:space-between;padding:6px 8px;border-bottom:1px solid #334155;font-size:13px;cursor:pointer}
.row:hover{background:#0f172a}
.ok{color:#10b981;font-weight:700}.err{color:#ef4444;font-weight:700}
img,video{max-width:100%;border-radius:6px;margin-top:10px}
</style>
</head>
<body>
<div id="keyModal" class="modal">
  <div class="modal-in">
    <h3>Enter DeepAI API Key</h3>
    <input type="password" id="keyInput" placeholder="Paste API key" autocomplete="off">
    <button onclick="setKey(false)">Save &amp; Open</button>
    <button class="sec" onclick="setKey(true)">Verify Key</button>
    <p id="keyMsg" style="font-size:13px"></p>
  </div>
</div>

<div class="wrap">
  <div class="box">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <b>DeepAI Tester</b>
      <button class="sec" style="width:auto;margin:0;padding:5px 10px"
        onclick="document.getElementById('keyModal').classList.remove('hide')">API Key</button>
    </div>
    <button class="grn" id="allBtn" onclick="testAll()">Run All 10 Features Auto-Test</button>
    <div id="suiteList" style="margin-top:10px"></div>

    <hr style="border-color:#334155;margin:16px 0">
    <b>Single Feature Manual Test</b>
    <select id="ep" onchange="toggleFields()">
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

    <form onsubmit="runRequest(event)">
      <div id="fTxt"><textarea id="txt" rows="2" placeholder="Prompt / text"></textarea></div>
      <div id="fImg" class="hide">
        <input type="file" id="imgF" accept="image/*">
        <input type="url" id="imgU" placeholder="Or image URL">
      </div>
      <div id="fMsk" class="hide">
        <input type="file" id="mskF" accept="image/*">
        <input type="url" id="mskU" placeholder="Or mask URL">
      </div>
      <div id="fImgOpt">
        <select id="ver">
          <option value="">version (default)</option><option>standard</option><option>hd</option>
          <option>genius</option><option>super_genius</option>
        </select>
        <select id="res">
          <option value="">resolution (default)</option><option>2k</option><option>4k</option>
        </select>
        <input type="number" id="w" placeholder="width">
        <input type="number" id="h" placeholder="height">
        <input type="text" id="neg" placeholder="negative_prompt">
      </div>
      <div id="fVidOpt" class="hide">
        <select id="mode"><option value="">mode (default)</option><option>hd</option><option>hollywood</option></select>
        <input type="number" id="dur" placeholder="duration (5-15)">
        <input type="text" id="shp" placeholder="shape (16:9)">
      </div>
      <button id="singleBtn">Send Single Request</button>
    </form>

    <div id="vidBox" class="hide" style="margin-top:10px">
      <input type="text" id="jobId" placeholder="Video Job ID">
      <button class="sec" type="button" onclick="videoStatus()">Check Video Status</button>
    </div>
  </div>

  <div class="box">
    <b>Raw API Response (click any test row to inspect)</b>
    <pre id="out">Ready.</pre>
    <div id="media"></div>
  </div>
</div>

<script>
let K = sessionStorage.getItem("deepai_key") || "";
const RESULTS = {};
const EPS = [
  "text2img", "image-editor", "background-remover", "colorizer",
  "torch-srgan", "waifu2x", "creative-upscale", "image-replace",
  "text2video", "img2video"
];

if (K) document.getElementById("keyModal").classList.add("hide");
toggleFields();

function toggleFields() {
  const ep = document.getElementById("ep").value;
  const textEndpoints = ["text2img", "image-editor", "image-replace", "text2video", "img2video"];
  const video = ["text2video", "img2video"].includes(ep);
  document.getElementById("fTxt").classList.toggle("hide", !textEndpoints.includes(ep));
  document.getElementById("fImg").classList.toggle("hide", ep === "text2img" || ep === "text2video");
  document.getElementById("fMsk").classList.toggle("hide", ep !== "image-replace");
  document.getElementById("fImgOpt").classList.toggle("hide", !["text2img", "image-editor"].includes(ep));
  document.getElementById("fVidOpt").classList.toggle("hide", !video);
  document.getElementById("vidBox").classList.toggle("hide", !video);
}

async function setKey(verify) {
  const value = document.getElementById("keyInput").value.trim();
  if (!value) return;
  K = value;
  sessionStorage.setItem("deepai_key", K);

  if (!verify) {
    document.getElementById("keyModal").classList.add("hide");
    return;
  }

  const msg = document.getElementById("keyMsg");
  msg.textContent = "Testing...";
  try {
    const response = await fetch("/verify", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({key: K})
    });
    const data = await response.json();
    document.getElementById("out").textContent = JSON.stringify(data, null, 2);
    msg.textContent = "HTTP " + data.status;
    if (data.status >= 200 && data.status < 300) {
      document.getElementById("keyModal").classList.add("hide");
    }
  } catch (err) {
    msg.textContent = String(err);
  }
}

async function sendProxy(ep, fields) {
  const fd = new FormData();
  fd.append("key", K);
  fd.append("ep", ep);
  for (const [key, value] of Object.entries(fields)) {
    if (value !== undefined && value !== null && value !== "") fd.append(key, value);
  }
  const response = await fetch("/proxy", {method: "POST", body: fd});
  return await response.json();
}

async function testAll() {
  if (!K) {
    document.getElementById("keyModal").classList.remove("hide");
    return;
  }

  const button = document.getElementById("allBtn");
  button.disabled = true;
  button.textContent = "Running tests...";
  for (const key of Object.keys(RESULTS)) delete RESULTS[key];

  const list = document.getElementById("suiteList");
  list.innerHTML = EPS.map(ep =>
    `<div class="row" id="r_${ep}" onclick="inspectResult('${ep}')">
      <span>${ep}</span><span id="s_${ep}">Queued</span></div>`
  ).join("");

  try {
    setRow("text2img", "Running...");
    const generated = await sendProxy("text2img", {text: "a red apple on a wooden table"});
    RESULTS["text2img"] = generated;
    updateRow("text2img", generated);
    inspectResult("text2img");

    const seedUrl = generated.body && generated.body.output_url;
    if (!seedUrl) {
      for (const ep of EPS.slice(1)) setRow(ep, "Skipped (no seed image)");
      return;
    }

    const jobs = [
      ["image-editor", {image_url: seedUrl, text: "make it blue"}],
      ["background-remover", {image_url: seedUrl}],
      ["colorizer", {image_url: seedUrl}],
      ["torch-srgan", {image_url: seedUrl}],
      ["waifu2x", {image_url: seedUrl}],
      ["creative-upscale", {image_url: seedUrl}],
      ["image-replace", {image_url: seedUrl, mask_url: seedUrl, text: "golden apple"}],
      ["text2video", {prompt: "a red apple spinning", duration: "5"}],
      ["img2video", {image_url: seedUrl, prompt: "camera zoom in", duration: "5"}]
    ];

    for (const [ep, params] of jobs) {
      setRow(ep, "Running...");
      try {
        const result = await sendProxy(ep, params);
        RESULTS[ep] = result;
        updateRow(ep, result);
      } catch (err) {
        const result = {status: 0, body: String(err)};
        RESULTS[ep] = result;
        updateRow(ep, result);
      }
    }
  } finally {
    button.disabled = false;
    button.textContent = "Run All 10 Features Auto-Test";
  }
}

function setRow(ep, text) {
  const el = document.getElementById("s_" + ep);
  if (el) el.textContent = text;
}

function updateRow(ep, result) {
  const el = document.getElementById("s_" + ep);
  if (!el) return;
  el.textContent = "HTTP " + result.status;
  el.className = result.status >= 200 && result.status < 300 ? "ok" : "err";
}

function inspectResult(ep) {
  const result = RESULTS[ep];
  if (!result) return;
  document.getElementById("out").textContent = JSON.stringify(result, null, 2);
  if (result.body && result.body.id && ["text2video", "img2video"].includes(ep)) {
    document.getElementById("ep").value = ep;
    toggleFields();
    document.getElementById("jobId").value = result.body.id;
  }
  showMedia(result.body && result.body.output_url);
}

async function runRequest(event) {
  event.preventDefault();
  if (!K) {
    document.getElementById("keyModal").classList.remove("hide");
    return;
  }

  const button = document.getElementById("singleBtn");
  button.disabled = true;
  button.textContent = "Loading...";
  const ep = document.getElementById("ep").value;
  const fields = {};
  const text = document.getElementById("txt").value.trim();

  if (text) fields[["text2video", "img2video"].includes(ep) ? "prompt" : "text"] = text;

  const imageFile = document.getElementById("imgF").files[0];
  if (imageFile) fields.image_file = imageFile;
  else if (document.getElementById("imgU").value.trim()) {
    fields.image_url = document.getElementById("imgU").value.trim();
  }

  const maskFile = document.getElementById("mskF").files[0];
  if (maskFile) fields.mask_file = maskFile;
  else if (document.getElementById("mskU").value.trim()) {
    fields.mask_url = document.getElementById("mskU").value.trim();
  }

  const options = {
    image_generator_version: "ver", resolution: "res", width: "w", height: "h",
    negative_prompt: "neg", mode: "mode", duration: "dur", shape: "shp"
  };
  for (const [field, id] of Object.entries(options)) {
    const value = document.getElementById(id).value;
    if (value) fields[field] = value;
  }

  try {
    const result = await sendProxy(ep, fields);
    document.getElementById("out").textContent = JSON.stringify(result, null, 2);
    if (result.body && result.body.id) document.getElementById("jobId").value = result.body.id;
    showMedia(result.body && result.body.output_url);
  } catch (err) {
    document.getElementById("out").textContent = String(err);
  } finally {
    button.disabled = false;
    button.textContent = "Send Single Request";
  }
}

async function videoStatus() {
  const id = document.getElementById("jobId").value.trim();
  if (!id || !K) return;
  try {
    const response = await fetch("/status", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({key: K, id})
    });
    const result = await response.json();
    document.getElementById("out").textContent = JSON.stringify(result, null, 2);
    showMedia(result.body && result.body.output_url);
  } catch (err) {
    document.getElementById("out").textContent = String(err);
  }
}

function showMedia(url) {
  const media = document.getElementById("media");
  media.replaceChildren();
  if (!url) return;
  const isVideo = /\.mp4(?:$|[?#])/i.test(url);
  const element = document.createElement(isVideo ? "video" : "img");
  element.src = url;
  if (isVideo) {
    element.controls = true;
    element.autoplay = true;
    element.loop = true;
  }
  media.appendChild(element);
}
</script>
</body>
</html>
"""


def response_payload(response):
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return {"status": response.status_code, "body": body}


def api_headers(key):
    return {"Api-key": key}


def call_api(endpoint, key, data=None, files=None, timeout=120):
    url = API_BASE + ENDPOINTS[endpoint]
    response = requests.post(
        url,
        headers=api_headers(key),
        data=data or {},
        files=files or None,
        timeout=timeout,
    )
    return response_payload(response)


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/verify", methods=["POST"])
def verify():
    payload = request.get_json(silent=True) or {}
    key = payload.get("key", "").strip()
    if not key:
        return jsonify({"status": 400, "body": "API key is required"}), 400

    try:
        result = call_api("text2img", key, {"text": "test"}, timeout=30)
        return jsonify(result)
    except requests.RequestException as exc:
        return jsonify({"status": 502, "body": str(exc)}), 502


@app.route("/proxy", methods=["POST"])
def proxy():
    key = request.form.get("key", "").strip()
    endpoint = request.form.get("ep", "")
    if not key:
        return jsonify({"status": 400, "body": "API key is required"}), 400
    if endpoint not in ENDPOINTS:
        return jsonify({"status": 400, "body": "Unknown endpoint"}), 400

    allowed = [
        "text", "prompt", "image_generator_version", "resolution", "width",
        "height", "negative_prompt", "mode", "duration", "shape",
    ]
    data = {name: request.form[name] for name in allowed if request.form.get(name)}

    files = {}
    image_file = request.files.get("image_file")
    if image_file and image_file.filename:
        files["image"] = (image_file.filename, image_file.stream, image_file.mimetype)
    elif request.form.get("image_url"):
        data["image"] = request.form["image_url"]

    mask_file = request.files.get("mask_file")
    if mask_file and mask_file.filename:
        files["mask"] = (mask_file.filename, mask_file.stream, mask_file.mimetype)
    elif request.form.get("mask_url"):
        data["mask"] = request.form["mask_url"]

    try:
        return jsonify(call_api(endpoint, key, data=data, files=files))
    except requests.RequestException as exc:
        return jsonify({"status": 502, "body": str(exc)}), 502


@app.route("/status", methods=["POST"])
def status():
    payload = request.get_json(silent=True) or {}
    key = str(payload.get("key", "")).strip()
    job_id = str(payload.get("id", "")).strip()

    if not key or not job_id:
        return jsonify({"status": 400, "body": "API key and job ID are required"}), 400

    # DeepAI video job IDs are expected to be queried via its video-status API.
    url = "https://api.deepai.org/api/video-generator-status"
    try:
        response = requests.get(
            url,
            headers=api_headers(key),
            params={"id": job_id},
            timeout=30,
        )
        return jsonify(response_payload(response))
    except requests.RequestException as exc:
        return jsonify({"status": 502, "body": str(exc)}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=False)
