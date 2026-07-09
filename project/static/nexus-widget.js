/** Nexus embeddable chat widget — drop-in for web and WebView shells */
(function (global) {
  const defaults = { apiBase: '/api/v1', sessionId: 'widget-' + Date.now(), position: 'bottom-right', token: '' };

  function NexusChat(opts) {
    this.cfg = { ...defaults, ...opts };
    this._el = null;
  }

  NexusChat.prototype.init = function () {
    if (this._el) return;
    const box = document.createElement('div');
    box.id = 'nexus-widget';
    box.innerHTML = `
      <style>
        #nexus-widget { position:fixed;${this.cfg.position.includes('right') ? 'right:16px' : 'left:16px'};bottom:16px;z-index:9999;font-family:system-ui,sans-serif; }
        #nexus-widget .nw-btn { width:56px;height:56px;border-radius:50%;background:#38bdf8;border:none;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,.35);font-size:1.4rem; }
        #nexus-widget .nw-panel { display:none;width:320px;height:420px;background:#0c0c12;border:1px solid rgba(255,255,255,.12);border-radius:16px;margin-bottom:8px;flex-direction:column;overflow:hidden; }
        #nexus-widget.open .nw-panel { display:flex; }
        #nexus-widget .nw-msgs { flex:1;overflow-y:auto;padding:12px;font-size:13px;color:#f4f4f5; }
        #nexus-widget .nw-row { display:flex;gap:6px;padding:8px;border-top:1px solid rgba(255,255,255,.1); }
        #nexus-widget input { flex:1;border-radius:8px;border:1px solid rgba(255,255,255,.15);background:#050508;color:#fff;padding:8px; }
        #nexus-widget button.send { background:#38bdf8;border:none;border-radius:8px;padding:0 12px; }
      </style>
      <div class="nw-panel"><div class="nw-msgs" id="nwMsgs"></div>
        <div class="nw-row"><input id="nwInput" placeholder="Message…" /><button class="send" type="button">→</button></div></div>
      <button class="nw-btn" type="button" aria-label="Chat">💬</button>`;
    document.body.appendChild(box);
    this._el = box;
    box.querySelector('.nw-btn').onclick = () => box.classList.toggle('open');
    const send = async () => {
      const input = box.querySelector('#nwInput');
      const text = input.value.trim();
      if (!text) return;
      const msgs = box.querySelector('#nwMsgs');
      msgs.innerHTML += `<div><b>You:</b> ${text}</div>`;
      input.value = '';
      const res = await fetch(this.cfg.apiBase + '/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + this.cfg.token },
        body: JSON.stringify({ message: text, session_id: this.cfg.sessionId, agent_id: 'chat_support' }),
      });
      const data = await res.json();
      msgs.innerHTML += `<div><b>AI:</b> ${data.response || data.detail || 'Error'}</div>`;
      msgs.scrollTop = msgs.scrollHeight;
    };
    box.querySelector('.send').onclick = send;
    box.querySelector('#nwInput').onkeydown = (e) => { if (e.key === 'Enter') send(); };
  };

  global.NexusChat = {
    init: function (opts) {
      const c = new NexusChat(opts);
      c.init();
      return c;
    },
  };
})(typeof window !== 'undefined' ? window : globalThis);
