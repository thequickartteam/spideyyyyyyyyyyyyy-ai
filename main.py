#!/usr/bin/env python3
"""Local DeepAI API dashboard. Start with: python deepai_key_dashboard.py"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json, urllib.request, urllib.error

HOST, PORT = "0.0.0.0", 8080

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>DeepAI Key Dashboard</title>
<style>
:root{color-scheme:dark;--bg:#090c14;--panel:#121827;--line:#273249;--muted:#98a6bd;--accent:#8b7cff;--good:#45d6a1;--bad:#ff7385}*{box-sizing:border-box}body{margin:0;background:radial-gradient(900px 500px at 10% -10%,#22224a,transparent),var(--bg);font:15px system-ui,-apple-system,Segoe UI,sans-serif;color:#f4f6ff}.wrap{max-width:1020px;margin:auto;padding:38px 20px 70px}h1{font-size:clamp(27px,4vw,39px);margin:0 0 8px;letter-spacing:-1px}.sub{color:var(--muted);margin:0 0 26px}.card{background:linear-gradient(145deg,#151d2d,#101622);border:1px solid var(--line);border-radius:16px;padding:22px;margin:16px 0;box-shadow:0 12px 40px #0003}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}label{display:block;font-weight:650;margin-bottom:8px}input,select,textarea{background:#0b111d;color:#f6f7ff;border:1px solid #34415a;border-radius:9px;padding:12px;font:inherit;outline:none}input:focus,select:focus,textarea:focus{border-color:var(--accent)}input[type=password]{flex:1;min-width:230px}button{border:0;border-radius:9px;background:var(--accent);color:white;padding:12px 17px;font:700 14px inherit;cursor:pointer}button.secondary{background:#26334b}button:hover{filter:brightness(1.1)}button:disabled{opacity:.55;cursor:wait}.hint,.muted{color:var(--muted);font-size:13px}.status{margin-top:13px;white-space:pre-wrap}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}.metric{padding:15px;background:#0c1320;border:1px solid #26334b;border-radius:12px}.metric .k{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}.metric .v{font-size:18px;font-weight:700;margin-top:7px;overflow-wrap:anywhere}.pill{font-size:12px;border:1px solid #3b4964;border-radius:99px;padding:5px 9px;color:#cad4e6}.service{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:start;border-top:1px solid var(--line);padding:16px 0}.service:first-of-type{border-top:0}.service h3{margin:0 0 4px}.service p{margin:0;color:var(--muted);font-size:13px}.service button{white-space:nowrap}textarea{width:100%;min-height:85px;resize:vertical}.result{margin-top:12px;white-space:pre-wrap;overflow-wrap:anywhere;background:#09101a;border:1px solid #26334b;border-radius:10px;padding:12px;max-height:380px;overflow:auto}.hidden{display:none}.notice{border-left:3px solid #e8b85c;padding:10px 13px;background:#201a12;color:#e9d4ab;border-radius:5px;font-size:13px}
</style></head><body><main class="wrap"><h1>DeepAI API dashboard</h1><p class="sub">A small local interface for checking your key and trying supported DeepAI endpoints.</p>
<section class="card"><label for="key">DeepAI API key</label><div class="row"><input id="key" type="password" autocomplete="off" placeholder="Paste your API key"><button id="check">Check key</button><button class="secondary" id="forget">Forget</button></div><p class="hint">Key is kept only in this page's memory and sent to the local Python service, which forwards it to DeepAI over HTTPS. It is not saved to disk.</p><div id="keyStatus" class="status muted"></div></section>
<section id="infoCard" class="card hidden"><h2 style="margin-top:0">Key / account information</h2><div id="metrics" class="grid"></div><p class="hint" style="margin-bottom:0">DeepAI may not provide account plan, billing, quota, or usage details through its public API. Fields unavailable from the provider are shown as unreported—not guessed. Check your DeepAI account dashboard for authoritative billing details.</p></section>
<section class="card"><h2 style="margin-top:0">Try an API feature</h2><p class="muted">Requests run through Python, which sends them to DeepAI’s unified /ai endpoint. Feature/model support depends on your account.</p><div class="service"><div><h3>Chat</h3><p>Send a prompt to DeepAI's chat endpoint.</p></div><button onclick="run('chat')">Open</button></div><div id="chatBox" class="hidden"><label for="chatPrompt">Prompt</label><textarea id="chatPrompt" placeholder="Ask something..."></textarea><div class="row" style="margin-top:9px"><button onclick="run('chat')">Send chat</button></div><div id="chatResult" class="result hidden"></div></div>
<div class="service"><div><h3>Image generation</h3><p>Generate an image from a text prompt. Result may include a URL.</p></div><button onclick="run('image')">Generate</button></div><div id="imageBox" class="hidden"><label for="imagePrompt">Image prompt</label><textarea id="imagePrompt" placeholder="Describe the image..."></textarea><div class="row" style="margin-top:9px"><button onclick="run('image')">Generate image</button></div><div id="imageResult" class="result hidden"></div></div>
<div class="service"><div><h3>Image editing</h3><p>Upload an image plus an edit prompt. Availability/model behavior depends on DeepAI.</p></div><button onclick="run('edit')">Edit</button></div><div id="editBox" class="hidden"><label for="editPrompt">Edit instruction</label><textarea id="editPrompt" placeholder="What should change?"></textarea><label for="editFile" style="margin-top:10px">Image file</label><input id="editFile" type="file" accept="image/*"><div class="row" style="margin-top:9px"><button onclick="run('edit')">Edit image</button></div><div id="editResult" class="result hidden"></div></div>
<div class="service"><div><h3>Video / music generation</h3><p>DeepAI may not expose these as public API endpoints. Use the hosted generator links where available.</p></div><span class="pill">Provider availability varies</span></div><div class="row"><a href="https://deepai.org/video" target="_blank" rel="noopener" style="color:#bdb3ff">AI Video Generator ↗</a><span class="muted">·</span><a href="https://deepai.org" target="_blank" rel="noopener" style="color:#bdb3ff">DeepAI ↗</a></div>
</section><p class="hint">This is a local utility, not an official DeepAI product. It cannot reveal a secret key's full value or access private billing records unless DeepAI provides an authenticated endpoint for them.</p></main>
<script>
const keyEl=document.getElementById('key'), statusEl=document.getElementById('keyStatus');let key='';
document.getElementById('check').onclick=checkKey;document.getElementById('forget').onclick=()=>{key='';keyEl.value='';document.getElementById('infoCard').classList.add('hidden');statusEl.textContent='Key cleared from page memory.'};
async function req(path,body){let r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,key})});let j=await r.json();if(!r.ok)throw new Error(j.error||'Request failed');return j}
async function checkKey(){key=keyEl.value.trim();if(!key){statusEl.textContent='Enter a key first.';return}statusEl.textContent='Checking key with DeepAI…';try{const d=await req('/api/check',{});statusEl.textContent=d.message||'Provider accepted the key.';const fields=[['Key status',d.valid?'Accepted':'Not confirmed'],['Plan / subscription',d.plan||'Not reported by public API'],['Usage / quota',d.usage||'Not reported by public API'],['Account details',d.account||'Not reported by public API']];document.getElementById('metrics').innerHTML=fields.map(x=>`<div class="metric"><div class="k">${esc(x[0])}</div><div class="v">${esc(x[1])}</div></div>`).join('');document.getElementById('infoCard').classList.remove('hidden')}catch(e){statusEl.textContent='Could not confirm key: '+e.message;document.getElementById('infoCard').classList.add('hidden')}}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function run(kind){if(!key)key=keyEl.value.trim();if(!key){statusEl.textContent='Enter and check your API key first.';keyEl.focus();return}const bx=document.getElementById(kind+'Box');bx.classList.remove('hidden');let out=document.getElementById(kind+'Result');if(!out)return;out.classList.remove('hidden');out.textContent='Working…';try{let body={};if(kind==='chat')body.prompt=document.getElementById('chatPrompt').value.trim();if(kind==='image')body.prompt=document.getElementById('imagePrompt').value.trim();if(kind==='edit'){body.prompt=document.getElementById('editPrompt').value.trim();let f=document.getElementById('editFile').files[0];if(!f)throw new Error('Choose an image file.');body.filename=f.name;body.image=await fileData(f)}if(!body.prompt)throw new Error('Enter a prompt.');let d=await req('/api/'+kind,body);out.innerHTML=render(d)}catch(e){out.textContent='Error: '+e.message}}
function fileData(f){return new Promise((ok,no)=>{let r=new FileReader();r.onload=()=>ok(r.result);r.onerror=no;r.readAsDataURL(f)})}
function render(d){let s=esc(JSON.stringify(d,null,2));let urls=[];function scan(x){if(typeof x==='string'&&/^https?:\/\//.test(x)&&/\.(png|jpe?g|gif|webp)(\?|$)/i.test(x))urls.push(x);else if(Array.isArray(x))x.forEach(scan);else if(x&&typeof x==='object')Object.values(x).forEach(scan)}scan(d);return (urls.length?urls.map(u=>`<img src="${esc(u)}" alt="Generated result" style="max-width:100%;border-radius:10px;margin:4px 0">`).join(''):'')+'<pre style="white-space:pre-wrap;margin:0">'+s+'</pre>'}
</script></body></html>'''

# Public API calls are proxied here so browser CORS does not block the page.
def deepai_ai(key, fields=None, file_data=None, filename=None):
    """Send every provider request through DeepAI's unified /ai endpoint."""
    import base64, re
    url='https://api.deepai.org/ai'
    headers={'api-key':key,'User-Agent':'Local-DeepAI-Dashboard/1.0'}
    if file_data is not None:
        m=re.match(r'data:([^;]+);base64,(.*)',file_data,re.S)
        if not m: raise ValueError('Invalid image data')
        content=base64.b64decode(m.group(2))
        boundary='----deepai-local-boundary'
        pieces=[]
        for name,val in (fields or {}).items():
            pieces.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n').encode())
        safe_name=(filename or 'upload.png').replace('"','')
        pieces.append((f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{safe_name}"\r\nContent-Type: {m.group(1)}\r\n\r\n').encode()+content+b'\r\n')
        pieces.append(f'--{boundary}--\r\n'.encode())
        data=b''.join(pieces);headers['Content-Type']='multipart/form-data; boundary='+boundary
    else:
        from urllib.parse import urlencode
        data=urlencode(fields or {}).encode()
        headers['Content-Type']='application/x-www-form-urlencoded'
    req=urllib.request.Request(url,data=data,headers=headers,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=120) as r:
            raw=r.read();ct=r.headers.get('Content-Type','')
            if 'json' in ct:
                try:return json.loads(raw.decode('utf-8'))
                except Exception:pass
            return {'http_status':r.status,'content_type':ct,'body':raw.decode('utf-8','replace')[:12000]}
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','replace')[:4000]
        raise RuntimeError(f'DeepAI returned HTTP {e.code}: {detail}')

class Handler(BaseHTTPRequestHandler):
    def send_json(self,status,obj):
        b=json.dumps(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
    def do_GET(self):
        if urlparse(self.path).path not in ('/','/index.html'):
            self.send_error(404);return
        b=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
    def do_POST(self):
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n>18*1024*1024: return self.send_json(413,{'error':'Request too large (18 MB limit).'})
            d=json.loads(self.rfile.read(n) or b'{}');key=str(d.get('key','')).strip()
            if not key:return self.send_json(400,{'error':'API key is required.'})
            route=urlparse(self.path).path
            if route=='/api/check':
                try:
                    deepai_ai(key,{'model':'chat','messages':[{'role':'user','content':'Reply with OK.'}]})
                    return self.send_json(200,{'valid':True,'message':'DeepAI accepted the key for a test request. Plan, billing, and usage metadata are only shown if the provider returns them.'})
                except Exception as e:
                    return self.send_json(401,{'valid':False,'error':str(e)})
            prompt=str(d.get('prompt','')).strip()
            if not prompt:return self.send_json(400,{'error':'Enter a prompt.'})
            if route=='/api/chat':
                result=deepai_ai(key,{'model':'chat','messages':[{'role':'user','content':prompt}]})
            elif route=='/api/image':
                result=deepai_ai(key,{'model':'image','prompt':prompt})
            elif route=='/api/edit':
                result=deepai_ai(key,{'model':'image-edit','prompt':prompt},d.get('image'),d.get('filename'))
            else:return self.send_json(404,{'error':'Unknown endpoint.'})
            return self.send_json(200,{'result':result})
        except Exception as e:return self.send_json(502,{'error':str(e)})
    def log_message(self,fmt,*args): print('%s - %s'%(self.address_string(),fmt%args))

if __name__=='__main__':
    print(f'Open http://127.0.0.1:{PORT} in your browser (or this machine’s address). Press Ctrl+C to stop.')
    HTTPServer((HOST,PORT),Handler).serve_forever()
