"""
web.py
------
Flask phone companion. Runs in a daemon thread; pygame stays on the
main thread. The main loop reads COMMANDS and writes STATE each frame.

Routes:
  GET /           mobile HTML control page
  GET /api/state  JSON snapshot of current kiosk state
  GET /api/cmd    enqueue a command (param: c=<command>)

Commands accepted:
  pause           stop auto-rotation
  resume          restart auto-rotation
  next            advance one page
  prev            go back one page
  goto:<n>        jump to page index n
  brightness:<pct> set brightness 0-100 (manual hold 30 min)
"""

import queue
import threading

import config

COMMANDS: "queue.Queue[str]" = queue.Queue()
STATE: dict = {}
_lock = threading.Lock()

_MOBILE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SpaceX HUD</title>
<style>
body{background:#080a0e;color:#dce6f0;font-family:monospace;
     padding:1rem;max-width:480px;margin:0 auto}
h1{color:#00c8ff;font-size:1.2rem;margin:0 0 1rem}
.row{display:flex;gap:.5rem;margin:.4rem 0}
button{background:#0e1218;color:#dce6f0;border:1px solid #28466e;
       padding:.6rem 1rem;border-radius:4px;cursor:pointer;
       font-family:monospace;flex:1}
button:active{background:#00c8ff;color:#080a0e}
.status{font-size:.75rem;color:#6e7d8c;margin:.4rem 0}
.paused{color:#ffb428}
label{font-size:.8rem;color:#6e7d8c;display:block;margin:.6rem 0 .1rem}
input[type=range]{width:100%;accent-color:#00c8ff}
.pages{display:flex;flex-wrap:wrap;gap:.3rem;margin:.4rem 0}
.pages button{flex:none;padding:.4rem .7rem;font-size:.75rem}
</style>
</head>
<body>
<h1>SPACEX HUD</h1>
<div class="status" id="st">connecting...</div>
<div class="row">
  <button onclick="cmd('pause')">PAUSE</button>
  <button onclick="cmd('resume')">RESUME</button>
</div>
<div class="row">
  <button onclick="cmd('prev')">&lt; PREV</button>
  <button onclick="cmd('next')">NEXT &gt;</button>
</div>
<label>BRIGHTNESS <span id="bv">-</span>%</label>
<input type="range" id="br" min="0" max="100" value="50"
       oninput="document.getElementById('bv').textContent=this.value"
       onchange="cmd('brightness:'+this.value)">
<label>GO TO PAGE</label>
<div class="pages" id="pgbtns"></div>
<script>
function cmd(c){fetch('/api/cmd?c='+encodeURIComponent(c))}
function poll(){
  fetch('/api/state').then(function(r){return r.json()}).then(function(s){
    var el=document.getElementById('st');
    el.textContent='Page: '+(s.page||'?')+(s.paused?' | PAUSED':'');
    el.className='status'+(s.paused?' paused':'');
    var br=document.getElementById('br');
    if(document.activeElement!==br&&s.brightness!=null)br.value=s.brightness;
    document.getElementById('bv').textContent=s.brightness!=null?s.brightness:'-';
    var pb=document.getElementById('pgbtns');
    if(pb.children.length===0&&s.pages){
      s.pages.forEach(function(p,i){
        var b=document.createElement('button');
        b.textContent=p;b.onclick=function(){cmd('goto:'+i)};
        pb.appendChild(b);
      });
    }
  }).catch(function(){});
}
setInterval(poll,2000);poll();
</script>
</body>
</html>"""


def update_state(**kwargs):
    with _lock:
        STATE.update(kwargs)


def start_background():
    if not config.WEB_ENABLED:
        return
    try:
        from flask import Flask, Response, jsonify, request
    except ImportError:
        return

    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    app = Flask(__name__)
    app.logger.disabled = True

    @app.route("/")
    def index():
        return Response(_MOBILE_HTML, mimetype="text/html")

    @app.route("/api/state")
    def api_state():
        with _lock:
            return jsonify(dict(STATE))

    @app.route("/api/cmd")
    def api_cmd():
        c = request.args.get("c", "").strip()
        if c:
            COMMANDS.put(c)
        return ("", 204)

    def _run():
        app.run(host="0.0.0.0", port=config.WEB_PORT,
                threaded=True, use_reloader=False)

    threading.Thread(target=_run, daemon=True, name="web").start()
