/** Enterprise CC features: team status, IVR designer, supervisor, QM, SaaS */
(function () {
  const API = '/api/v1';
  let entSection = 'team';
  let heartbeatTimer = null;

  function authHeaders() {
    const h = { 'Content-Type': 'application/json' };
    const t = localStorage.getItem('nexus_auth_token');
    if (t) h.Authorization = `Bearer ${t}`;
    return h;
  }

  async function api(path, opts = {}) {
    const res = await fetch(`${API}${path}`, { ...opts, headers: authHeaders() });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
  }

  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  }

  function navHtml() {
    const tabs = [
      ['team', 'Team status'], ['ivr', 'IVR designer'], ['supervisor', 'Supervisor'],
      ['qm', 'Quality'], ['cobrowse', 'Co-browse'], ['saas', 'Hosted SaaS'],
    ];
    return `<div class="ent-nav">${tabs.map(([k, l]) =>
      `<button type="button" class="ent-nav-btn${entSection === k ? ' active' : ''}" data-ent="${k}">${l}</button>`).join('')}</div>`;
  }

  async function renderTeam(root) {
    const data = await api('/agents/team');
    const team = data.team || [];
    root.innerHTML = navHtml() + `
      <div class="ent-toolbar">
        <span>Your status:</span>
        ${['available', 'away', 'break', 'offline'].map((s) =>
          `<button type="button" class="btn btn-ghost ent-status-btn" data-status="${s}">${s}</button>`).join('')}
      </div>
      <div class="cx-list">${team.length ? team.map((a) => `
        <div class="cx-list-item" style="cursor:default">
          <strong>${esc(a.name || a.email)}</strong>
          <span class="cx-badge ${esc(a.status)}">${esc(a.status)}</span>
          <div class="meta">${esc(a.role)} · ${esc(a.skills || 'general')}</div>
        </div>`).join('') : '<div class="cx-empty">No agents online — set your status above.</div>'}
      </div>`;
    bindNav(root);
    root.querySelectorAll('.ent-status-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        await api('/agents/status', { method: 'POST', body: JSON.stringify({ status: btn.dataset.status }) });
        window.showToast?.('Status updated', 'success');
        renderTeam(root);
      });
    });
  }

  async function renderIvr(root) {
    const data = await api('/ivr/flows');
    const flows = data.flows || [];
    const active = flows.find((f) => f.active);
    root.innerHTML = navHtml() + `
      <div class="cx-flow-builder">
        <div class="cx-flow-node trigger">① Greeting</div><div class="cx-flow-arrow">→</div>
        <div class="cx-flow-node condition">② Menu (DTMF)</div><div class="cx-flow-arrow">→</div>
        <div class="cx-flow-node action">③ AI / Transfer</div>
      </div>
      <div class="cx-flow-form">
        <div class="field"><label>Flow name</label><input id="ivrName" value="${esc(active?.name || 'Main IVR')}" /></div>
        <div class="field"><label>Greeting</label><input id="ivrGreeting" value="Thank you for calling. Press 1 for support, 2 for billing." /></div>
        <div class="field"><label>Transfer number (opt 2)</label><input id="ivrTransfer" placeholder="+15551234567" /></div>
        <button type="button" class="btn btn-primary" id="ivrSave">Save & activate</button>
      </div>
      <h3 class="cx-section-title">Saved flows (${flows.length})</h3>
      <div class="cx-list">${flows.map((f) => `<div class="cx-list-item">${esc(f.name)} ${f.active ? '✓ active' : ''}</div>`).join('') || '<div class="cx-empty">No flows yet</div>'}</div>`;
    bindNav(root);
    document.getElementById('ivrSave')?.addEventListener('click', async () => {
      const nodes = [
        { id: 'start', type: 'prompt', text: document.getElementById('ivrGreeting').value, next: 'menu' },
        { id: 'menu', type: 'menu', text: '', options: {
          '1': { label: 'Support', next: 'ai' },
          '2': { label: 'Billing', next: 'transfer' },
        }},
        { id: 'ai', type: 'ai', agent_id: 'voice_support', next: '' },
        { id: 'transfer', type: 'transfer', transfer_number: document.getElementById('ivrTransfer').value },
      ];
      await api('/ivr/flows', { method: 'POST', body: JSON.stringify({
        name: document.getElementById('ivrName').value, nodes, edges: [], entry_node: 'start', active: true,
      })});
      window.showToast?.('IVR flow saved', 'success');
      renderIvr(root);
    });
  }

  async function renderSupervisor(root) {
    const inbox = await api('/inbox');
    const sessions = inbox.inbox || [];
    root.innerHTML = navHtml() + `
      <p class="call-info">Monitor, whisper (coach agent only), or barge (join customer-visible).</p>
      <div class="field"><label>Session ID</label><input id="supSession" list="supSessions" placeholder="session-…" />
        <datalist id="supSessions">${sessions.map((s) => `<option value="${esc(s.id)}">`).join('')}</datalist></div>
      <div class="field"><label>Message</label><textarea id="supMsg" rows="2" placeholder="Whisper or barge message…"></textarea></div>
      <div class="ent-toolbar">
        <button type="button" class="btn btn-ghost" data-mode="monitor">Monitor</button>
        <button type="button" class="btn btn-primary" data-mode="whisper">Whisper</button>
        <button type="button" class="btn btn-success" data-mode="barge">Barge</button>
      </div>`;
    bindNav(root);
    root.querySelectorAll('[data-mode]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const sid = document.getElementById('supSession').value.trim();
        if (!sid) return;
        await api('/supervisor/action', { method: 'POST', body: JSON.stringify({
          session_id: sid, mode: btn.dataset.mode, message: document.getElementById('supMsg').value,
        })});
        window.showToast?.(`${btn.dataset.mode} logged`, 'success');
      });
    });
  }

  async function renderQm(root) {
    const [reviews, pending] = await Promise.all([api('/qm/reviews'), api('/qm/pending')]);
    root.innerHTML = navHtml() + `
      <div class="cx-grid">
        <div class="cx-stat"><div class="cx-stat-label">Reviews</div><div class="cx-stat-value">${(reviews.reviews || []).length}</div></div>
        <div class="cx-stat"><div class="cx-stat-label">Pending queue</div><div class="cx-stat-value">${pending.count || 0}</div></div>
      </div>
      <div class="field"><label>Session to score</label><input id="qmSession" placeholder="session-id" /></div>
      <div class="field"><label>Score (1-5)</label><input type="number" id="qmScore" min="1" max="5" value="4" /></div>
      <div class="field"><label>Notes</label><textarea id="qmNotes" rows="2"></textarea></div>
      <button type="button" class="btn btn-primary" id="qmSubmit">Submit review</button>
      <h3 class="cx-section-title">Recent reviews</h3>
      <div class="cx-list">${(reviews.reviews || []).slice(0, 8).map((r) =>
        `<div class="cx-list-item">${esc(r.session_id)} · ${r.overall_score}/5</div>`).join('') || '<div class="cx-empty">No reviews yet</div>'}
      </div>`;
    bindNav(root);
    document.getElementById('qmSubmit')?.addEventListener('click', async () => {
      await api('/qm/reviews', { method: 'POST', body: JSON.stringify({
        session_id: document.getElementById('qmSession').value,
        overall_score: Number(document.getElementById('qmScore').value),
        notes: document.getElementById('qmNotes').value,
        rubric: { empathy: 4, accuracy: 4, compliance: 5 },
      })});
      window.showToast?.('QM review saved', 'success');
      renderQm(root);
    });
  }

  async function renderCobrowse(root) {
    root.innerHTML = navHtml() + `
      <p class="call-info">Join a customer co-browse session from the <a href="/portal" target="_blank">customer portal</a>.</p>
      <div class="field"><label>Co-browse session ID</label><input id="cbJoinId" placeholder="cb-…" /></div>
      <button type="button" class="btn btn-primary" id="cbJoin">Join session</button>
      <button type="button" class="btn btn-ghost" id="cbShare">Share my screen</button>
      <div class="result cx-empty" id="cbLog">WebSocket relay active when joined.</div>`;
    bindNav(root);
    let ws = null;
    document.getElementById('cbJoin')?.addEventListener('click', async () => {
      const sid = document.getElementById('cbJoinId').value.trim();
      await api(`/cobrowse/${encodeURIComponent(sid)}/join`, { method: 'POST' });
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      ws = new WebSocket(`${proto}://${location.host}/api/v1/cobrowse/ws/${sid}`);
      ws.onmessage = (e) => { document.getElementById('cbLog').textContent += '\n' + e.data; };
      window.showToast?.('Joined co-browse', 'success');
    });
    document.getElementById('cbShare')?.addEventListener('click', async () => {
      try {
        const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
        document.getElementById('cbLog').textContent = 'Screen sharing started (' + stream.getVideoTracks().length + ' track)';
        if (ws && ws.readyState === 1) ws.send('Agent started screen share');
      } catch (err) {
        window.showToast?.(err.message, 'error');
      }
    });
  }

  async function renderSaas(root) {
    const data = await api('/saas/subscription');
    const sub = data.subscription || {};
    root.innerHTML = navHtml() + `
      <p class="call-info">Nexus Cloud — managed hosting with SLA, upgrades, and compliance add-ons.</p>
      <div class="cx-grid">${(data.plans || []).map((p) => `
        <div class="cx-stat">
          <div class="cx-stat-label">${esc(p.name)}</div>
          <div class="cx-stat-value">$${p.price_monthly}</div>
          <div class="meta">${p.agents} agents · ${Array.isArray(p.channels) ? p.channels.join(', ') : p.channels}</div>
        </div>`).join('')}
      </div>
      <p>Current plan: <strong>${esc(sub.plan_id || 'starter')}</strong> (${esc(sub.status || 'active')})</p>
      <div class="ent-toolbar">${(data.plans || []).map((p) =>
        `<button type="button" class="btn btn-ghost" data-plan="${p.id}">Switch to ${esc(p.name)}</button>`).join('')}
      </div>`;
    bindNav(root);
    root.querySelectorAll('[data-plan]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        await api('/saas/subscribe', { method: 'POST', body: JSON.stringify({ plan_id: btn.dataset.plan }) });
        window.showToast?.('Plan updated', 'success');
        renderSaas(root);
      });
    });
  }

  function bindNav(root) {
    root.querySelectorAll('.ent-nav-btn').forEach((btn) => {
      btn.addEventListener('click', () => { entSection = btn.dataset.ent; loadEnterprise(); });
    });
  }

  async function loadEnterprise() {
    const root = document.getElementById('cxEnterpriseRoot');
    if (!root) return;
    root.innerHTML = '<div class="cx-empty">Loading…</div>';
    try {
      if (entSection === 'team') await renderTeam(root);
      else if (entSection === 'ivr') await renderIvr(root);
      else if (entSection === 'supervisor') await renderSupervisor(root);
      else if (entSection === 'qm') await renderQm(root);
      else if (entSection === 'cobrowse') await renderCobrowse(root);
      else if (entSection === 'saas') await renderSaas(root);
    } catch (err) {
      root.innerHTML = navHtml() + `<div class="cx-empty">${esc(err.message)}</div>`;
      bindNav(root);
    }
  }

  function startHeartbeat() {
    if (heartbeatTimer) return;
    heartbeatTimer = setInterval(async () => {
      if (!localStorage.getItem('nexus_auth_token')) return;
      try {
        await api('/agents/status', { method: 'POST', body: JSON.stringify({ status: 'available' }) });
      } catch {}
    }, 45000);
  }

  function onModeChange(mode) {
    if (mode === 'enterprise') loadEnterprise();
  }

  function init() {
    startHeartbeat();
    const obs = new MutationObserver(() => onModeChange(document.body.dataset.mode || 'chat'));
    obs.observe(document.body, { attributes: true, attributeFilter: ['data-mode'] });
  }

  window.Enterprise = { load: loadEnterprise };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
