/** CX platform UI — inbox, analytics, email, tickets, workflows, CSAT/NPS */
(function () {
  const API = '/api/v1';

  let selectedSessionId = null;
  let feedbackSessionId = null;
  let csatScore = 0;
  let npsScore = null;

  function authHeaders(extra = {}) {
    const headers = { 'Content-Type': 'application/json', ...extra };
    const token = localStorage.getItem('nexus_auth_token') || '';
    if (token) headers.Authorization = `Bearer ${token}`;
    return headers;
  }

  async function apiFetch(path, opts = {}) {
    const res = await fetch(`${API}${path}`, { ...opts, headers: authHeaders(opts.headers || {}) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || data.message || `Request failed (${res.status})`);
    return data;
  }

  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  }

  function channelLabel(ch) {
    const map = {
      chat: 'Chat', voice: 'Voice', whatsapp: 'WhatsApp', sms: 'SMS',
      email: 'Email', messenger: 'Messenger', instagram: 'Instagram',
    };
    return map[ch] || ch || 'unknown';
  }

  function renderTimelineChart(timeline) {
    if (!timeline?.length) return '<div class="cx-empty">No conversation volume data yet</div>';
    const max = Math.max(...timeline.map((t) => t.count || 0), 1);
    return `<div class="cx-chart">${timeline.map((t) => {
      const h = Math.round(((t.count || 0) / max) * 100);
      const label = (t.hour || '').slice(11, 16) || '?';
      return `<div class="cx-chart-bar" title="${esc(t.hour)}: ${t.count}"><div class="cx-chart-fill" style="height:${h}%"></div><span>${label}</span></div>`;
    }).join('')}</div>`;
  }

  async function loadInbox() {
    const list = document.getElementById('cxInboxList');
    if (!list) return;
    list.innerHTML = '<div class="cx-empty">Loading queue…</div>';
    try {
      const data = await apiFetch('/inbox');
      const items = data.inbox || [];
      if (!items.length) {
        list.innerHTML = '<div class="cx-empty">No escalated conversations — AI is handling Tier-1.</div>';
        document.getElementById('cxInboxDetail').innerHTML = '<div class="cx-empty">Select a conversation to take over.</div>';
        return;
      }
      list.innerHTML = items.map((s) => `
        <button type="button" class="cx-list-item${selectedSessionId === s.id ? ' active' : ''}" data-session="${esc(s.id)}">
          <strong>${esc(s.customer_info || s.id)}</strong>
          <span class="cx-badge ${esc(s.handoff_status)}">${esc(s.handoff_status)}</span>
          <div class="meta">${channelLabel(s.channel)} · ${s.message_count || 0} msgs · ${esc(s.escalation_reason || 'Escalated')}</div>
        </button>`).join('');
      list.querySelectorAll('[data-session]').forEach((btn) => {
        btn.addEventListener('click', () => openInboxSession(btn.dataset.session));
      });
      if (!selectedSessionId && items[0]) openInboxSession(items[0].id);
    } catch (err) {
      list.innerHTML = `<div class="cx-empty">${esc(err.message)}</div>`;
    }
  }

  async function openInboxSession(sessionId) {
    selectedSessionId = sessionId;
    document.querySelectorAll('#cxInboxList .cx-list-item').forEach((el) => {
      el.classList.toggle('active', el.dataset.session === sessionId);
    });
    const detail = document.getElementById('cxInboxDetail');
    if (!detail) return;
    detail.innerHTML = '<div class="cx-empty">Loading thread…</div>';
    try {
      const data = await apiFetch(`/sessions/${encodeURIComponent(sessionId)}/history`);
      const msgs = data.messages || [];
      const thread = msgs.map((m) => `<div class="cx-msg ${esc(m.role)}">${esc(m.content)}</div>`).join('');
      detail.innerHTML = `
        <div class="cx-detail">
          <div class="cx-thread" id="cxThread">${thread || '<div class="cx-empty">No messages yet</div>'}</div>
          <div class="cx-reply-bar">
            <textarea id="cxAgentReply" placeholder="Reply as human agent…" rows="2"></textarea>
            <button type="button" class="btn btn-primary" id="cxSendReply">Send</button>
            <button type="button" class="btn btn-ghost" id="cxClaimBtn">Claim</button>
            <button type="button" class="btn btn-success" id="cxResolveBtn">Resolve</button>
          </div>
        </div>`;
      document.getElementById('cxSendReply')?.addEventListener('click', () => sendAgentReply(sessionId));
      document.getElementById('cxClaimBtn')?.addEventListener('click', () => claimSession(sessionId));
      document.getElementById('cxResolveBtn')?.addEventListener('click', () => resolveSession(sessionId));
    } catch (err) {
      detail.innerHTML = `<div class="cx-empty">${esc(err.message)}</div>`;
    }
  }

  async function claimSession(sessionId) {
    try {
      await apiFetch(`/inbox/${encodeURIComponent(sessionId)}/claim`, { method: 'POST' });
      window.showToast?.('Conversation claimed', 'success');
      await loadInbox();
      await openInboxSession(sessionId);
    } catch (err) { window.showToast?.(err.message, 'error'); }
  }

  async function sendAgentReply(sessionId) {
    const ta = document.getElementById('cxAgentReply');
    const msg = (ta?.value || '').trim();
    if (!msg) return;
    try {
      await apiFetch(`/inbox/${encodeURIComponent(sessionId)}/reply`, { method: 'POST', body: JSON.stringify({ message: msg }) });
      ta.value = '';
      await openInboxSession(sessionId);
      window.showToast?.('Reply sent', 'success');
    } catch (err) { window.showToast?.(err.message, 'error'); }
  }

  async function resolveSession(sessionId) {
    try {
      await apiFetch(`/inbox/${encodeURIComponent(sessionId)}/resolve`, { method: 'POST' });
      selectedSessionId = null;
      window.showToast?.('Conversation resolved', 'success');
      await loadInbox();
    } catch (err) { window.showToast?.(err.message, 'error'); }
  }

  async function loadDashboard() {
    const root = document.getElementById('cxAnalyticsRoot');
    if (!root) return;
    root.innerHTML = '<div class="cx-empty">Loading metrics…</div>';
    try {
      const d = await apiFetch('/cx/dashboard?hours=168');
      const c = d.conversations || {};
      const csat = d.csat || {};
      const nps = d.nps || {};
      const h = d.handoff || {};
      const mf = d.message_feedback || {};
      const agents = (d.agents?.agents || []).slice(0, 6);
      root.innerHTML = `
        <div class="cx-grid">
          <div class="cx-stat"><div class="cx-stat-label">Conversations (7d)</div><div class="cx-stat-value">${c.total_conversations || 0}</div></div>
          <div class="cx-stat"><div class="cx-stat-label">Containment</div><div class="cx-stat-value">${Math.round((c.containment_rate || 0) * 100)}%</div></div>
          <div class="cx-stat"><div class="cx-stat-label">Avg response</div><div class="cx-stat-value">${c.avg_response_time_ms || 0}ms</div></div>
          <div class="cx-stat"><div class="cx-stat-label">Avg CSAT</div><div class="cx-stat-value">${csat.avg_score || '—'}</div></div>
          <div class="cx-stat"><div class="cx-stat-label">NPS</div><div class="cx-stat-value">${nps.nps ?? '—'}</div></div>
          <div class="cx-stat"><div class="cx-stat-label">👍 rate</div><div class="cx-stat-value">${Math.round((mf.satisfaction_rate || 0) * 100)}%</div></div>
          <div class="cx-stat"><div class="cx-stat-label">Escalations</div><div class="cx-stat-value">${h.escalated || 0}</div></div>
          <div class="cx-stat"><div class="cx-stat-label">Open tickets</div><div class="cx-stat-value">${h.open_tickets || 0}</div></div>
        </div>
        <h3 class="cx-section-title">Conversation volume</h3>
        ${renderTimelineChart(d.timeline)}
        <h3 class="cx-section-title">Agent scorecard</h3>
        <div class="cx-list" style="max-height:220px">
          ${agents.length ? agents.map((a) => `
            <div class="cx-list-item" style="cursor:default">
              <strong>${esc(a.agent_id)}</strong>
              <div class="meta">${a.sessions} sessions · ${Math.round((a.containment_rate || 0) * 100)}% contained · CSAT ${a.avg_csat || '—'}</div>
            </div>`).join('') : '<div class="cx-empty">No agent data yet</div>'}
        </div>`;
    } catch (err) {
      root.innerHTML = `<div class="cx-empty">${esc(err.message)}</div>`;
    }
  }

  async function loadTickets() {
    const root = document.getElementById('cxTicketsRoot');
    if (!root) return;
    root.innerHTML = '<div class="cx-empty">Loading tickets…</div>';
    try {
      const data = await apiFetch('/tickets');
      const tickets = data.tickets || [];
      if (!tickets.length) {
        root.innerHTML = '<div class="cx-empty">No tickets yet. AI creates them via the create_ticket tool.</div>';
        return;
      }
      root.innerHTML = `<div class="cx-list">${tickets.map((t) => `
        <div class="cx-list-item cx-ticket-row" data-id="${t.id}">
          <div class="cx-ticket-head">
            <strong>#${t.id} ${esc(t.subject)}</strong>
            <select class="cx-ticket-status" data-id="${t.id}">
              ${['open', 'pending', 'resolved', 'closed'].map((s) => `<option value="${s}"${t.status === s ? ' selected' : ''}>${s}</option>`).join('')}
            </select>
          </div>
          <div class="meta">${esc(t.priority)} · ${esc(t.assigned_to || 'unassigned')} · ${esc((t.description || '').slice(0, 80))}</div>
        </div>`).join('')}</div>`;
      root.querySelectorAll('.cx-ticket-status').forEach((sel) => {
        sel.addEventListener('change', async () => {
          try {
            await apiFetch(`/tickets/${sel.dataset.id}`, { method: 'PATCH', body: JSON.stringify({ status: sel.value }) });
            window.showToast?.('Ticket updated', 'success');
          } catch (err) { window.showToast?.(err.message, 'error'); }
        });
      });
    } catch (err) {
      root.innerHTML = `<div class="cx-empty">${esc(err.message)}</div>`;
    }
  }

  async function createTicketPrompt() {
    const subject = prompt('Ticket subject:');
    if (!subject) return;
    const description = prompt('Description:') || '';
    try {
      await apiFetch('/tickets', { method: 'POST', body: JSON.stringify({ subject, description }) });
      window.showToast?.('Ticket created', 'success');
      await loadTickets();
    } catch (err) { window.showToast?.(err.message, 'error'); }
  }

  const TRIGGERS = [
    'conversation.started', 'conversation.ended', 'conversation.escalated', 'ticket.created',
  ];
  const ACTIONS = ['send_webhook', 'create_ticket', 'escalate', 'notify_slack'];

  async function loadWorkflows() {
    const root = document.getElementById('cxWorkflowsRoot');
    if (!root) return;
    root.innerHTML = '<div class="cx-empty">Loading flows…</div>';
    try {
      const data = await apiFetch('/workflows');
      const flows = data.workflows || [];
      const listHtml = flows.length ? flows.map((w) => `
        <div class="cx-flow-card" data-id="${w.id}">
          <strong>${esc(w.name)}</strong>
          <div class="meta">When <code>${esc(w.trigger_event)}</code> → ${(w.actions || []).length} action(s)</div>
          <button type="button" class="btn btn-ghost cx-flow-del" data-id="${w.id}">Delete</button>
        </div>`).join('') : '<div class="cx-empty">No flows yet — create one below.</div>';

      root.innerHTML = `
        <div class="cx-flow-builder">
          <div class="cx-flow-node trigger">① Trigger</div>
          <div class="cx-flow-arrow">→</div>
          <div class="cx-flow-node condition">② Condition</div>
          <div class="cx-flow-arrow">→</div>
          <div class="cx-flow-node action">③ Action</div>
        </div>
        <div class="cx-flow-form">
          <div class="field"><label>Name</label><input type="text" id="cxWfName" placeholder="Escalate VIP customers" /></div>
          <div class="field"><label>Trigger</label><select id="cxWfTrigger">${TRIGGERS.map((t) => `<option value="${t}">${t}</option>`).join('')}</select></div>
          <div class="field"><label>Condition (channel)</label><select id="cxWfChannel"><option value="">Any</option><option value="chat">Chat</option><option value="voice">Voice</option><option value="email">Email</option><option value="whatsapp">WhatsApp</option><option value="messenger">Messenger</option><option value="instagram">Instagram</option></select></div>
          <div class="field"><label>Action</label><select id="cxWfAction">${ACTIONS.map((a) => `<option value="${a}">${a}</option>`).join('')}</select></div>
          <div class="field"><label>Webhook URL (optional)</label><input type="url" id="cxWfUrl" placeholder="https://hooks.n8n.io/..." /></div>
          <button type="button" class="btn btn-primary" id="cxWfSave">Save flow</button>
        </div>
        <h3 class="cx-section-title">Saved flows</h3>
        <div class="cx-flow-list">${listHtml}</div>`;

      document.getElementById('cxWfSave')?.addEventListener('click', saveWorkflow);
      root.querySelectorAll('.cx-flow-del').forEach((btn) => {
        btn.addEventListener('click', async () => {
          if (!confirm('Delete this flow?')) return;
          await apiFetch(`/workflows/${btn.dataset.id}`, { method: 'DELETE' });
          await loadWorkflows();
        });
      });
    } catch (err) {
      root.innerHTML = `<div class="cx-empty">${esc(err.message)}</div>`;
    }
  }

  async function saveWorkflow() {
    const name = document.getElementById('cxWfName')?.value?.trim();
    if (!name) { window.showToast?.('Enter a flow name', 'error'); return; }
    const trigger = document.getElementById('cxWfTrigger')?.value;
    const channel = document.getElementById('cxWfChannel')?.value;
    const action = document.getElementById('cxWfAction')?.value;
    const url = document.getElementById('cxWfUrl')?.value?.trim();
    const conditions = channel ? { channel } : {};
    const actions = [{ type: action, url: url || undefined }];
    try {
      await apiFetch('/workflows', { method: 'POST', body: JSON.stringify({ name, trigger_event: trigger, conditions, actions }) });
      window.showToast?.('Flow saved', 'success');
      await loadWorkflows();
    } catch (err) { window.showToast?.(err.message, 'error'); }
  }

  async function sendEmail() {
    const to = document.getElementById('cxEmailTo')?.value?.trim();
    const subject = document.getElementById('cxEmailSubject')?.value?.trim();
    const body = document.getElementById('cxEmailBody')?.value?.trim();
    if (!to || !subject || !body) { window.showToast?.('Fill in to, subject, and body', 'error'); return; }
    try {
      const res = await apiFetch('/email/send', { method: 'POST', body: JSON.stringify({ to, subject, body }) });
      window.showToast?.(`Email ${res.status || 'sent'}`, 'success');
    } catch (err) { window.showToast?.(err.message, 'error'); }
  }

  function showFeedbackModal(sessionId) {
    feedbackSessionId = sessionId;
    csatScore = 0;
    npsScore = null;
    const modal = document.getElementById('cxFeedbackModal');
    if (!modal) return;
    modal.hidden = false;
    document.querySelectorAll('.cx-star-btn').forEach((b) => b.classList.remove('active'));
    document.querySelectorAll('.cx-nps-btn').forEach((b) => b.classList.remove('active'));
    document.getElementById('cxFeedbackComment').value = '';
  }

  function hideFeedbackModal() {
    document.getElementById('cxFeedbackModal').hidden = true;
    feedbackSessionId = null;
  }

  async function submitFeedback() {
    if (!feedbackSessionId) return hideFeedbackModal();
    const comment = document.getElementById('cxFeedbackComment')?.value || '';
    try {
      if (csatScore >= 1) {
        await apiFetch('/csat', { method: 'POST', body: JSON.stringify({ session_id: feedbackSessionId, score: csatScore, feedback: comment }) });
      }
      if (npsScore !== null) {
        await apiFetch('/nps', { method: 'POST', body: JSON.stringify({ session_id: feedbackSessionId, score: npsScore, feedback: comment }) });
      }
      window.showToast?.('Thanks for your feedback!', 'success');
    } catch (err) { window.showToast?.(err.message, 'error'); }
    hideFeedbackModal();
  }

  function onModeChange(mode) {
    if (mode === 'inbox') loadInbox();
    if (mode === 'analytics') loadDashboard();
    if (mode === 'tickets') loadTickets();
    if (mode === 'workflows') loadWorkflows();
  }

  function init() {
    document.getElementById('cxInboxRefresh')?.addEventListener('click', loadInbox);
    document.getElementById('cxAnalyticsRefresh')?.addEventListener('click', loadDashboard);
    document.getElementById('cxEmailSend')?.addEventListener('click', sendEmail);
    document.getElementById('cxTicketsRefresh')?.addEventListener('click', loadTickets);
    document.getElementById('cxTicketNew')?.addEventListener('click', createTicketPrompt);
    document.getElementById('cxWorkflowsRefresh')?.addEventListener('click', loadWorkflows);
    document.getElementById('cxWorkflowNew')?.addEventListener('click', () => document.getElementById('cxWfName')?.focus());

    document.querySelectorAll('.cx-star-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        csatScore = Number(btn.dataset.score);
        document.querySelectorAll('.cx-star-btn').forEach((b) => b.classList.toggle('active', Number(b.dataset.score) <= csatScore));
      });
    });
    document.querySelectorAll('.cx-nps-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        npsScore = Number(btn.dataset.score);
        document.querySelectorAll('.cx-nps-btn').forEach((b) => b.classList.toggle('active', b === btn));
      });
    });
    document.getElementById('cxFeedbackSkip')?.addEventListener('click', hideFeedbackModal);
    document.getElementById('cxFeedbackSubmit')?.addEventListener('click', submitFeedback);
    document.getElementById('cxFeedbackBackdrop')?.addEventListener('click', hideFeedbackModal);

    const obs = new MutationObserver(() => onModeChange(document.body.dataset.mode || 'chat'));
    obs.observe(document.body, { attributes: true, attributeFilter: ['data-mode'] });

    setInterval(() => {
      if (document.body.dataset.mode === 'inbox') loadInbox();
    }, 15000);
  }

  window.CX = { promptFeedback: showFeedbackModal, loadInbox, loadDashboard, loadTickets, loadWorkflows };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
