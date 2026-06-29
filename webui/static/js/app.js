/* AstroSurge — Client-side application logic */

(function () {
  'use strict';

  // ─── State ────────────────────────────────────────────────────────────
  const state = {
    candidates: [],
    stats: null,
    health: null,
    fleet: [],
    missions: [],
  };

  // ─── Helpers ──────────────────────────────────────────────────────────
  const API_BASE = '/api';

  async function api(path, opts = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Accept': 'application/json', ...opts.headers },
      ...opts,
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${body}`);
    }
    return res.json();
  }

  function fmtMoney(v) {
    if (v == null || isNaN(v)) return '—';
    if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
    if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
    if (Math.abs(v) >= 1e3) return `$${(v / 1e3).toFixed(1)}K`;
    return `$${v.toFixed(0)}`;
  }

  function fmtPct(v) {
    if (v == null || isNaN(v)) return '—';
    return `${(v * 100).toFixed(1)}%`;
  }

  function fmtNum(v, decimals = 1) {
    if (v == null || isNaN(v)) return '—';
    return Number(v).toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function renderName(c) {
    if (c.name) return escapeHtml(c.name);
    return `<span class="text-muted">(unnamed spkid-${c.spkid})</span>`;
  }

  // ─── View switching ───────────────────────────────────────────────────
  function switchView(viewId) {
    document.querySelectorAll('.view-panel').forEach(el => el.classList.add('d-none'));
    const panel = document.getElementById(`view-${viewId}`);
    if (panel) panel.classList.remove('d-none');

    // Update active state on both desktop sidebar and mobile tab bar
    function updateActive(selector) {
      document.querySelectorAll(selector).forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === viewId);
      });
    }
    updateActive('#view-tabs-desktop .list-group-item');
    updateActive('#view-tabs-mobile .btn');

    // Load data on view switch
    if (viewId === 'dashboard') loadDashboard();
    if (viewId === 'asteroids') loadAsteroids();
    if (viewId === 'fleet') loadFleet();
    if (viewId === 'missions') loadMissions();
    if (viewId === 'simulate') populateSimTargets();
  }

  // ─── Status bar ───────────────────────────────────────────────────────
  async function updateStatus() {
    try {
      state.health = await api('/health');
      const el = document.getElementById('mongo-status');
      if (state.health.mongodb) {
        el.innerHTML = `<span class="text-success">●</span> MongoDB · ${state.health.ship_count} ships`;
      } else {
        el.innerHTML = `<span class="text-danger">●</span> DB offline`;
      }
    } catch (e) {
      document.getElementById('mongo-status').innerHTML =
        `<span class="text-danger">●</span> API error`;
    }
  }

  // ─── Stats card ────────────────────────────────────────────────────────
  async function updateStats() {
    try {
      state.stats = await api('/stats');
      // Load fleet stats too
      let fleetInfo = '';
      try {
        const fleet = await api('/fleet/ships');
        const missions = await api('/missions');
        const ships = fleet.ships || [];
        const totalProfit = (missions.missions || []).reduce(
          (s, m) => s + ((m.metrics && m.metrics.net_profit_usd) || 0), 0);
        fleetInfo = `
        <div class="d-flex justify-content-between mt-1 pt-1 border-top border-secondary"><span>🚢 Ships</span><span class="fw-bold text-info">${ships.length}</span></div>
        <div class="d-flex justify-content-between"><span>📋 Missions</span><span class="fw-bold text-success">${missions.count || 0}</span></div>
        <div class="d-flex justify-content-between"><span>💰 Profit</span><span class="fw-bold text-warning">${fmtMoney(totalProfit)}</span></div>`;
      } catch (_) {}
      const el = document.getElementById('stats-content');
      el.innerHTML = `
        <div class="d-flex justify-content-between"><span>Total</span><span class="fw-bold">${state.stats.total_asteroids.toLocaleString()}</span></div>
        <div class="d-flex justify-content-between"><span>NEOs</span><span class="fw-bold text-info">${state.stats.neos.toLocaleString()}</span></div>
        <div class="d-flex justify-content-between"><span>M-class</span><span class="fw-bold text-warning">${state.stats.class_m.toLocaleString()}</span></div>
        <div class="d-flex justify-content-between"><span>C-class</span><span class="fw-bold text-success">${state.stats.class_c.toLocaleString()}</span></div>
        ${fleetInfo}
      `;
    } catch (e) {
      document.getElementById('stats-content').innerHTML =
        `<span class="text-danger">Stats unavailable</span>`;
    }
  }

  // ─── Dashboard ─────────────────────────────────────────────────────────
  async function loadDashboard() {
    try {
      const data = await api('/asteroids/candidates?limit=10');
      state.candidates = data.candidates || [];

      const tbody = document.getElementById('dashboard-targets-body');
      if (state.candidates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-muted text-center">No candidates found</td></tr>';
        return;
      }

      // Top candidate
      const top = state.candidates[0];
      document.getElementById('dash-top-name').textContent = top.name || `spkid-${top.spkid}`;
      document.getElementById('dash-top-score').textContent = `Score: ${top.score.toFixed(4)}`;

      // Fastest transit
      const fastest = state.candidates.reduce((a, b) => a.transit_days_one_way < b.transit_days_one_way ? a : b);
      document.getElementById('dash-fastest-name').textContent = fastest.name || `spkid-${fastest.spkid}`;
      document.getElementById('dash-fastest-days').textContent = `${fastest.transit_days_one_way} days one-way`;

      // Load fleet stats for dashboard
      try {
        const [fleetData, missionData] = await Promise.all([
          api('/fleet/ships'),
          api('/missions'),
        ]);
        const ships = fleetData.ships || [];
        const missionList = missionData.missions || [];
        const shipsEl = document.getElementById('dash-ships');
        const shipsSubEl = document.getElementById('dash-ships-sub');
        const missionsEl = document.getElementById('dash-missions');
        const missionsSubEl = document.getElementById('dash-missions-sub');
        if (shipsEl) shipsEl.textContent = ships.length;
        if (shipsSubEl) shipsSubEl.textContent =
          ships.filter(s => s.status === 'active').length + ' active';
        const totalMissions = missionList.length;
        const totalProfit = missionList.reduce(
          (sum, m) => sum + (m.metrics?.net_profit_usd || 0), 0);
        if (missionsEl) missionsEl.textContent = totalMissions;
        if (missionsSubEl) missionsSubEl.textContent =
          fmtMoney(totalProfit) + ' total profit';
      } catch (_) {}

      // Table
      tbody.innerHTML = state.candidates.map(c => `
        <tr class="clickable" data-spkid="${c.spkid}" onclick="window.viewAsteroid(${c.spkid})">
          <td class="fw-bold">${renderName(c)}</td>
          <td><span class="badge ${c.class === 'M' ? 'bg-warning text-dark' : c.class === 'C' ? 'bg-info text-dark' : 'bg-secondary'}">${c.class}</span></td>
          <td>${c.diameter_km.toFixed(2)}</td>
          <td class="text-info">${c.moid_au.toFixed(4)}</td>
          <td>${c.hazard ? '⚠️' : '✅'}</td>
          <td>${c.transit_days_one_way}d</td>
          <td class="text-money">${fmtMoney(c.estimated_value_usd)}</td>
          <td class="text-score">${c.score.toFixed(4)}</td>
        </tr>
      `).join('');
    } catch (e) {
      document.getElementById('dashboard-targets-body').innerHTML =
        `<tr><td colspan="8" class="text-danger text-center">Failed to load: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  // ─── Asteroids view ────────────────────────────────────────────────────
  async function loadAsteroids() {
    const moid = document.getElementById('f-moid').value || 0.10;
    const dia = document.getElementById('f-diameter').value || 3.0;

    try {
      const data = await api(`/asteroids/candidates?max_moid=${moid}&min_diameter=${dia}&limit=50`);
      state.candidates = data.candidates || [];

      const tbody = document.getElementById('asteroid-table-body');
      if (state.candidates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="text-muted text-center">No candidates match these filters</td></tr>';
        return;
      }

      tbody.innerHTML = state.candidates.map(c => `
        <tr class="clickable" onclick="window.viewAsteroid(${c.spkid})">
          <td class="fw-bold">${renderName(c)}</td>
          <td>${c.spkid}</td>
          <td><span class="badge ${c.class === 'M' ? 'bg-warning text-dark' : c.class === 'C' ? 'bg-info text-dark' : 'bg-secondary'}">${c.class}</span></td>
          <td>${c.diameter_km.toFixed(2)}</td>
          <td class="text-info">${c.moid_au.toFixed(4)}</td>
          <td>${c.hazard ? '⚠️' : '✅'}</td>
          <td>${c.transit_days_one_way}d</td>
          <td class="text-money">${fmtMoney(c.estimated_value_usd)}</td>
          <td class="text-money">${fmtMoney(c.estimated_cost_usd)}</td>
          <td class="text-score">${c.score.toFixed(4)}</td>
          <td><button class="btn btn-sm btn-outline-warning simulate-btn" data-spkid="${c.spkid}">🚀</button></td>
        </tr>
      `).join('');

      // Wire up simulate buttons
      tbody.querySelectorAll('.simulate-btn').forEach(btn => {
        btn.addEventListener('click', e => {
          e.stopPropagation();
          const spkid = parseInt(btn.dataset.spkid);
          document.getElementById('sim-spkid').value = spkid;
          switchView('simulate');
        });
      });
    } catch (e) {
      document.getElementById('asteroid-table-body').innerHTML =
        `<tr><td colspan="11" class="text-danger text-center">Failed to load: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  // ─── Fleet view ────────────────────────────────────────────────────────
  async function loadFleet() {
    const el = document.getElementById('fleet-content');
    try {
      state.fleet = await api('/fleet/ships');
      const ships = state.fleet.ships || [];
      if (ships.length === 0) {
        el.innerHTML = '<div class="text-center py-5 text-muted"><div class="fs-1 mb-2">🚢</div><p>No ships in fleet. Build one via the API.</p></div>';
        return;
      }
      el.innerHTML = ships.map(s => `
        <div class="card bg-dark border-secondary mb-2">
          <div class="card-body py-2">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <span class="fw-bold fs-5">${escapeHtml(s.name)}</span>
                <span class="badge ${s.status === 'in_port' ? 'bg-success' : s.status === 'active' ? 'bg-info text-dark' : 'bg-secondary'} ms-2">${s.status}</span>
                <span class="badge bg-warning text-dark ms-1">Tier ${s.tier}</span>
              </div>
              <small class="text-muted">${s.ship_id}</small>
            </div>
            <div class="row mt-2 g-2 small">
              <div class="col-auto">🚀 <span class="text-info">${s.mission_count}</span> missions</div>
              <div class="col-auto">🔧 ${(s.upgrades || []).length} upgrades</div>
              <div class="col-auto">📦 ${fmtNum(s.cargo_capacity_kg, 0)} kg capacity</div>
              <div class="col-auto">🛡️ ${s.shielding_type}</div>
              ${(s.retained_earnings || 0) > 0 ? `<div class="col-auto">💰 $${fmtNum(s.retained_earnings, 0)}</div>` : ''}
            </div>
            ${(s.upgrades || []).length ? '<div class="mt-1 small text-muted">Upgrades: ' + s.upgrades.map(u =>
              `<span class="badge bg-secondary me-1">${u.module_id}</span>`
            ).join('') + '</div>' : ''}
            <button class="btn btn-sm btn-outline-info mt-1" style="font-size:0.65rem" onclick="toggleShipEvents('${s.ship_id}')">📋 Show Events</button>
            <div id="ship-events-${s.ship_id}" style="display:none;max-height:200px;overflow-y:auto" class="mt-1"></div>
          </div>
        </div>
      `).join('');
    } catch (e) {
      el.innerHTML = `<div class="text-center py-5 text-danger">Failed to load fleet: ${escapeHtml(e.message)}</div>`;
    }
  }

  // ─── Missions view ─────────────────────────────────────────────────────
  async function loadMissions() {
    const el = document.getElementById('missions-content');
    try {
      state.missions = await api('/missions');
      const list = state.missions.missions || [];
      if (list.length === 0) {
        el.innerHTML = '<div class="text-center py-5 text-muted"><div class="fs-1 mb-2">📋</div><p>No missions completed yet. Launch a mission to see results here.</p></div>';
        return;
      }
      const typeLabels = {
        mining_fast_roi: '⚡ Fast ROI', mining_ice: '🧊 Ice Farming',
        hazard_hunter: '☢️ Hazard Hunter', precision_extraction: '🎯 Precision Extraction',
      };
      el.innerHTML = list.map(m => {
        const metrics = m.metrics || {};
        const profit = metrics.net_profit_usd || 0;
        const roi = ((metrics.roi || 0) * 100).toFixed(1);
        const statusIcon = m.status === 'completed' ? '✅' : m.status === 'failed' ? '❌' : '⏳';
        return `
        <div class="card bg-dark border-secondary mb-2 mission-card" data-mission="${escapeHtml(m.mission_id)}" style="cursor:pointer">
          <div class="card-body py-2">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <span class="fw-bold">${statusIcon} ${escapeHtml(m.asteroid_name || 'Unknown')}</span>
                <span class="badge ${m.status === 'completed' ? 'bg-success' : 'bg-warning text-dark'} ms-2">${m.status}</span>
                <span class="text-muted small ms-2">${typeLabels[m.mission_type] || m.mission_type}</span>
              </div>
              <small class="text-muted">${m.mission_id} ▶</small>
            </div>
            <div class="row mt-2 g-2 small">
              <div class="col-auto">💰 <span class="text-money">${fmtMoney(profit)}</span></div>
              <div class="col-auto">📈 <span class="text-score">${roi}%</span> ROI</div>
              <div class="col-auto">⏱️ ${m.round_trip_days || '?'} days</div>
              <div class="col-auto">🚢 ${escapeHtml(m.ship_id || '?')}</div>
            </div>
            ${m.status === 'completed' ? `<div class="mt-1 text-end"><button class="btn btn-sm btn-outline-success py-0" style="font-size:0.7rem" onclick="event.stopPropagation();relaunchShip('${escapeHtml(m.ship_id)}')">🔄 Relaunch ${escapeHtml(m.ship_id)}</button></div>` : ''}
          </div>
        </div>
      `}).join('');
      // Wire up click handlers
      el.querySelectorAll('.mission-card').forEach(card => {
        card.addEventListener('click', () => {
          showMissionDetail(card.dataset.mission);
        });
      });
    } catch (e) {
      el.innerHTML = `<div class="text-center py-5 text-danger">Failed to load missions: ${escapeHtml(e.message)}</div>`;
    }
  }

  // ─── Mission Detail view ───────────────────────────────────────────────
  async function showMissionDetail(missionId) {
    const el = document.getElementById('missions-content');
    el.innerHTML = '<div class="text-center py-4 text-muted"><div class="spinner-border text-warning mb-2"></div><p>Loading mission detail...</p></div>';
    try {
      const [mission, ticksData] = await Promise.all([
        api('/missions/' + missionId),
        api('/missions/' + missionId + '/ticks?page=1&per_page=100'),
      ]);
      const metrics = mission.metrics || {};
      const profit = metrics.net_profit_usd || 0;
      const roi = ((metrics.roi || 0) * 100).toFixed(1);
      const ticks = ticksData.ticks || [];
      const totalTicks = ticksData.total || 0;
      const typeLabels = {
        mining_fast_roi: '⚡ Fast ROI', mining_ice: '🧊 Ice Farming',
        hazard_hunter: '☢️ Hazard Hunter', precision_extraction: '🎯 Precision Extraction',
      };
      const phaseIcons = {5:'🛸',6:'🏗️',7:'⛏️',8:'📦',9:'🏠'};

      // Calc phase stats from ticks
      let miningDays = ticks.filter(t => t.phase === 7).length;
      let totalMined = ticks.filter(t => t.mined_kg).reduce((s, t) => s + t.mined_kg, 0);
      let events = ticks.reduce((s, t) => s + ((t.events && t.events.length) || 0), 0);

      // Check break-even day
      let beDay = null;
      for (const t of ticks) {
        if (t.is_break_even) { beDay = t.day; break; }
      }

      let shipInfo = '';
      if (mission.ship_id) {
        try {
          const ship = await api('/fleet/ships/' + mission.ship_id);
          shipInfo = `
            <div class="card bg-dark border-secondary mb-2">
              <div class="card-body py-2">
                <div class="d-flex justify-content-between">
                  <span class="fw-bold">🚢 ${escapeHtml(ship.name || mission.ship_id)}</span>
                  <span class="badge ${ship.status === 'in_port' ? 'bg-success' : 'bg-secondary'} ms-2">${ship.status}</span>
                </div>
                <div class="small text-muted mt-1">
                  ${ship.class} · Tier ${ship.tier} · ${ship.mission_count} missions · ${(ship.upgrades || []).length} upgrades
                </div>
              </div>
            </div>`;
        } catch (_) {}
      }

      let html = `
        <div class="mb-2">
          <button class="btn btn-sm btn-outline-secondary" onclick="window.loadMissions()">← Back to Missions</button>
        </div>
        <div class="card bg-dark border-secondary mb-2">
          <div class="card-body py-2">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <span class="fw-bold fs-5">${typeLabels[mission.mission_type] || mission.mission_type}</span>
                <span class="badge ${mission.status === 'completed' ? 'bg-success' : 'bg-warning text-dark'} ms-2">${mission.status}</span>
              </div>
              <small class="text-muted">${mission.mission_id}</small>
            </div>
            <div class="mt-1 text-muted small">${escapeHtml(mission.asteroid_name || 'Unknown')} · spkid ${mission.spkid} · ${mission.round_trip_days || '?'} days</div>
          </div>
        </div>
        ${shipInfo}
        <div class="row g-1 mb-2">
          <div class="col-3"><div class="card bg-dark border-secondary text-center py-1"><div class="text-money fw-bold small">${fmtMoney(profit)}</div><div class="text-muted" style="font-size:0.6rem">Profit</div></div></div>
          <div class="col-3"><div class="card bg-dark border-secondary text-center py-1"><div class="text-score fw-bold small">${roi}%</div><div class="text-muted" style="font-size:0.6rem">ROI</div></div></div>
          <div class="col-3"><div class="card bg-dark border-secondary text-center py-1"><div class="text-info fw-bold small">${fmtMoney(metrics.total_revenue_usd || 0)}</div><div class="text-muted" style="font-size:0.6rem">Revenue</div></div></div>
          <div class="col-3"><div class="card bg-dark border-secondary text-center py-1"><div class="fw-bold small text-secondary">${fmtMoney(metrics.total_cost_usd || 0)}</div><div class="text-muted" style="font-size:0.6rem">Cost</div></div></div>
        </div>
        <div class="row g-1 mb-3">
          <div class="col-3"><div class="card bg-dark border-secondary text-center py-1"><div class="fw-bold small">${totalTicks}</div><div class="text-muted" style="font-size:0.6rem">Days</div></div></div>
          <div class="col-3"><div class="card bg-dark border-secondary text-center py-1"><div class="fw-bold small">${fmtNum(totalMined, 0)} kg</div><div class="text-muted" style="font-size:0.6rem">Mined</div></div></div>
          <div class="col-3"><div class="card bg-dark border-secondary text-center py-1"><div class="fw-bold small">${miningDays}</div><div class="text-muted" style="font-size:0.6rem">Mining Days</div></div></div>
          <div class="col-3"><div class="card bg-dark border-secondary text-center py-1"><div class="fw-bold small">${events} ⚡</div><div class="text-muted" style="font-size:0.6rem">Events</div></div></div>
        </div>`;

      // Tick timeline
      html += `<h6 class="text-secondary mb-2">📅 Daily Timeline (${totalTicks} days)</h6>
      <div class="tick-timeline" style="max-height: 55vh; overflow-y: auto;">`;
      for (const t of ticks) {
        const isRepo = t.repositioning;
        const pIcon = isRepo ? '🚚' : (phaseIcons[t.phase] || '❓');
        const pName = isRepo ? 'repositioning' : (t.phase_name || '').replace(/_/g,' ');
        const fundPct = t.funding_pool > 0 ? (t.funding_remaining / t.funding_pool * 100) : 0;
        const barColor = fundPct > 50 ? 'bg-success' : fundPct > 20 ? 'bg-warning' : 'bg-danger';
        const roiColor = t.daily_roi >= 0 ? 'text-success' : 'text-danger';
        const evList = t.events || [];

        html += `<div class="tick-row d-flex align-items-start py-1 px-2 border-bottom border-secondary ${isRepo ? 'bg-dark' : ''}" style="font-size:0.78rem; min-height:2.2rem;">
          <div class="me-2 text-center" style="width:2.2rem; flex-shrink:0;">
            <div class="fw-bold" style="font-size:0.65rem">D${t.day}</div>
            <div style="font-size:0.85rem">${pIcon}</div>
          </div>
          <div class="flex-grow-1" style="min-width:0;">
            <div class="d-flex justify-content-between small">
              <span class="text-muted" style="font-size:0.65rem">${pName}</span>
              <span class="${roiColor} fw-bold" style="font-size:0.65rem">${(t.daily_roi*100).toFixed(1)}%</span>
            </div>
            <div class="progress" style="height:4px;">
              <div class="progress-bar ${barColor}" style="width:${Math.max(0, fundPct)}%"></div>
            </div>
            <div class="d-flex justify-content-between text-muted" style="font-size:0.6rem">
              <span>💵 ${fmtMoney(t.funding_remaining)}</span>
              <span>💰 ${fmtMoney(t.cargo_value)}</span>
              <span>📊 ${fmtMoney(t.debt_owed)}</span>
            </div>`;

        // Mining yield inline
        if (t.mined_kg) {
          html += `<div class="text-muted" style="font-size:0.6rem">⛏️ ${fmtNum(t.mined_kg, 1)} kg · $${fmtNum(t.daily_revenue, 0)} rev`;
          if (t.top_elements && t.top_elements.length) {
            html += ` · ${t.top_elements.map(e => e.name).join(', ')}`;
          }
          html += `</div>`;
        }

        // Event badges (0-N events per day)
        for (const ev of evList) {
          const sev = ev.severity || 'info';
          const icon = sev === 'critical' ? '🔴' : sev === 'warning' ? '⚠️' : 'ℹ️';
          html += `<div class="text-${sev === 'critical' ? 'danger' : sev === 'warning' ? 'warning' : 'info'}" style="font-size:0.6rem">${icon} ${escapeHtml(ev.description || ev.type || 'event')}</div>`;
        }

        html += `</div></div>`;
      }
      html += '</div>';

      // Pagination
      if (ticksData.total_pages > 1) {
        html += `<div class="mt-2 text-center small tick-pagination">
          <button class="btn btn-sm btn-outline-secondary" id="ticks-prev" ${ticksData.page <= 1 ? 'disabled' : ''}>← Prev</button>
          <span class="mx-2 text-muted">Page ${ticksData.page} of ${ticksData.total_pages}</span>
          <button class="btn btn-sm btn-outline-secondary" id="ticks-next" ${ticksData.page >= ticksData.total_pages ? 'disabled' : ''}>Next →</button>
        </div>`;
      }

      el.innerHTML = html;

      // Wire pagination
      const nextBtn = document.getElementById('ticks-next');
      const prevBtn = document.getElementById('ticks-prev');
      if (nextBtn) nextBtn.addEventListener('click', () => loadTicksPage(missionId, ticksData.page + 1));
      if (prevBtn) prevBtn.addEventListener('click', () => loadTicksPage(missionId, ticksData.page - 1));
    } catch (e) {
      el.innerHTML = `<div class="text-center py-5 text-danger">Failed to load mission detail: ${escapeHtml(e.message)}</div>`;
    }
  }

  // ─── Tick pagination (replaces only the ticks section) ─────────────────
  async function loadTicksPage(missionId, page) {
    const el = document.getElementById('missions-content');
    const timeline = el.querySelector('.tick-timeline');
    const paginationDiv = el.querySelector('.tick-pagination');
    if (!timeline) return; // not in detail view
    
    try {
      const ticksData = await api('/missions/' + missionId + '/ticks?page=' + page + '&per_page=100');
      const phaseIcons = {5:'🛸',6:'🏗️',7:'⛏️',8:'📦',9:'🏠'};
      let html = `<h6 class="text-secondary mb-2">📅 Daily Timeline (${ticksData.total} days)</h6>
      <div class="tick-timeline" style="max-height: 55vh; overflow-y: auto;">`;
      for (const t of (ticksData.ticks || [])) {
        const isRepo = t.repositioning;
        const pIcon = isRepo ? '🚚' : (phaseIcons[t.phase] || '❓');
        const pName = isRepo ? 'repositioning' : (t.phase_name || '').replace(/_/g,' ');
        const fundPct = t.funding_pool > 0 ? (t.funding_remaining / t.funding_pool * 100) : 0;
        const barColor = fundPct > 50 ? 'bg-success' : fundPct > 20 ? 'bg-warning' : 'bg-danger';
        const roiColor = t.daily_roi >= 0 ? 'text-success' : 'text-danger';
        const evList = t.events || [];
        html += `<div class="tick-row d-flex align-items-start py-1 px-2 border-bottom border-secondary ${isRepo ? 'bg-dark' : ''}" style="font-size:0.78rem; min-height:2.2rem;">
          <div class="me-2 text-center" style="width:2.2rem; flex-shrink:0;">
            <div class="fw-bold" style="font-size:0.65rem">D${t.day}</div>
            <div style="font-size:0.85rem">${pIcon}</div>
          </div>
          <div class="flex-grow-1" style="min-width:0;">
            <div class="d-flex justify-content-between small">
              <span class="text-muted" style="font-size:0.65rem">${pName}</span>
              <span class="${roiColor} fw-bold" style="font-size:0.65rem">${(t.daily_roi*100).toFixed(1)}%</span>
            </div>
            <div class="progress" style="height:4px;">
              <div class="progress-bar ${barColor}" style="width:${Math.max(0, fundPct)}%"></div>
            </div>
            <div class="d-flex justify-content-between text-muted" style="font-size:0.6rem">
              <span>💵 ${fmtMoney(t.funding_remaining)}</span>
              <span>💰 ${fmtMoney(t.cargo_value)}</span>
              <span>📊 ${fmtMoney(t.debt_owed)}</span>
            </div>`;
        if (t.mined_kg) {
          html += `<div class="text-muted" style="font-size:0.6rem">⛏️ ${fmtNum(t.mined_kg, 1)} kg · $${fmtNum(t.daily_revenue, 0)} rev`;
          if (t.top_elements && t.top_elements.length) {
            html += ` · ${t.top_elements.map(e => e.name).join(', ')}`;
          }
          html += `</div>`;
        }
        for (const ev of evList) {
          const sev = ev.severity || 'info';
          const icon = sev === 'critical' ? '🔴' : sev === 'warning' ? '⚠️' : 'ℹ️';
          html += `<div class="text-${sev === 'critical' ? 'danger' : sev === 'warning' ? 'warning' : 'info'}" style="font-size:0.6rem">${icon} ${escapeHtml(ev.description || ev.type || 'event')}</div>`;
        }
        html += `</div></div>`;
      }
      html += '</div>';
      html += `<div class="mt-2 text-center small tick-pagination">
        <button class="btn btn-sm btn-outline-secondary" id="ticks-prev" ${page <= 1 ? 'disabled' : ''}>← Prev</button>
        <span class="mx-2 text-muted">Page ${page} of ${ticksData.total_pages}</span>
        <button class="btn btn-sm btn-outline-secondary" id="ticks-next" ${page >= ticksData.total_pages ? 'disabled' : ''}>Next →</button>
      </div>`;
      
      // Replace timeline + pagination in-place
      const temp = document.createElement('div');
      temp.innerHTML = html;
      timeline.parentNode.replaceChild(temp.querySelector('.tick-timeline'), timeline);
      const oldPag = el.querySelector('.tick-pagination');
      if (oldPag) oldPag.parentNode.replaceChild(temp.querySelector('.tick-pagination'), oldPag);
      
      // Re-wire pagination buttons
      document.getElementById('ticks-next')?.addEventListener('click', () => loadTicksPage(missionId, page + 1));
      document.getElementById('ticks-prev')?.addEventListener('click', () => loadTicksPage(missionId, page - 1));
    } catch (_) {}
  }

  // ─── Simulate view ─────────────────────────────────────────────────────
  async function populateSimTargets() {
    const select = document.getElementById('sim-spkid');
    if (select.options.length > 1) return; // already populated

    try {
      const data = await api('/asteroids/candidates?limit=20');
      select.innerHTML = '<option value="">Select a target...</option>' +
        data.candidates.map(c =>
          `<option value="${c.spkid}">${c.name ? escapeHtml(c.name) : `spkid-${c.spkid}`} — ${c.class} ${c.diameter_km.toFixed(1)}km MOID:${c.moid_au.toFixed(4)}</option>`
        ).join('');
    } catch (e) {
      select.innerHTML = '<option value="">Failed to load targets</option>';
    }
  }

  async function runSimulation() {
    const spkid = parseInt(document.getElementById('sim-spkid').value);
    if (!spkid) {
      alert('Please select a target asteroid.');
      return;
    }

    const shipCost = parseFloat(document.getElementById('sim-ship-cost').value) || 50000000;
    const reusable = document.getElementById('sim-reusable').checked;
    const refinery = document.getElementById('sim-refinery').checked;

    // Show loading, hide empty/results
    document.getElementById('sim-empty').classList.add('d-none');
    document.getElementById('sim-results').classList.add('d-none');
    document.getElementById('sim-loading').classList.remove('d-none');

    try {
      const result = await api('/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          spkid,
          ship_cost: shipCost,
          reusable,
          refinery,
          seed: Math.floor(Math.random() * 99999),
        }),
      });

      displayResults(result);
    } catch (e) {
      document.getElementById('sim-loading').classList.add('d-none');
      document.getElementById('sim-empty').classList.remove('d-none');
      document.getElementById('sim-empty').innerHTML =
        `<div class="fs-1 mb-2">❌</div><p class="text-danger">${escapeHtml(e.message)}</p>`;
    }
  }

  function displayResults(result) {
    document.getElementById('sim-loading').classList.add('d-none');
    document.getElementById('sim-results').classList.remove('d-none');

    const status = result.status || 'unknown';
    const statusBadge = document.getElementById('sim-status-badge');
    statusBadge.textContent = status;
    statusBadge.className = `badge ${status === 'completed' ? 'bg-success' : status === 'failed' ? 'bg-danger' : 'bg-warning text-dark'}`;

    document.getElementById('sim-result-title').textContent =
      `Mission to ${result.asteroid_name} (spkid ${result.spkid})`;

    // Financials
    const fin = result.financials || {};
    document.getElementById('sim-cost').textContent = fmtMoney(fin.total_cost_usd);
    document.getElementById('sim-revenue').textContent = fmtMoney(fin.total_revenue_usd);
    document.getElementById('sim-roi').textContent = fmtPct(fin.roi);
    document.getElementById('sim-debt').textContent = fmtMoney(fin.debt_repaid);
    document.getElementById('sim-retained').textContent = fmtMoney(fin.retained_profit);

    // Duration
    document.getElementById('sim-duration').textContent =
      result.transit ? `${result.transit.round_trip_days} days` : '—';
    document.getElementById('sim-oneway').textContent =
      result.transit ? `${result.transit.one_way_days} days` : '—';
    document.getElementById('sim-roundtrip').textContent =
      result.transit ? `${result.transit.round_trip_days} days` : '—';

    // Mining
    const mining = result.mining || {};
    document.getElementById('sim-mined').textContent = mining.total_mined_kg ? fmtNum(mining.total_mined_kg, 0) + ' kg' : '—';
    document.getElementById('sim-ore').textContent = mining.total_ore_kg ? fmtNum(mining.total_ore_kg, 1) + ' kg' : '—';
    document.getElementById('sim-mining-days').textContent = mining.days_mined ? `${mining.days_mined} days` : '—';

    // Phase log
    const log = document.getElementById('sim-phase-log');
    if (result.phase_results) {
      const phaseNames = [
        '', 'Asteroid Identification', 'Survey Planning', 'Mission Design',
        'Spacecraft Assembly', 'Transit Execution', 'Site Establishment',
        'Mining Operations', 'Cargo Sealing', 'Return Transit',
        'Market Sale', 'Financial Analysis'
      ];
      log.innerHTML = result.phase_results.map((p, i) => `
        <div class="phase-item ${p.status} d-flex justify-content-between align-items-center">
          <div>
            <span class="badge bg-secondary me-2">${p.phase}</span>
            <span>${phaseNames[p.phase] || p.phase_name}</span>
          </div>
          <span class="badge ${p.status === 'completed' ? 'bg-success' : 'bg-danger'}">${p.status}</span>
        </div>
      `).join('');
    } else {
      log.innerHTML = '<div class="text-muted text-center p-3">No phase data available</div>';
    }

    // Error
    if (result.error) {
      log.innerHTML += `<div class="alert alert-danger m-2">⚠️ ${escapeHtml(result.error)}</div>`;
    }
  }

  // ─── Global asteroid viewer (from table clicks) ────────────────────────
  window.viewAsteroid = function (spkid) {
    // Switch to simulate view with this asteroid pre-selected
    document.getElementById('sim-spkid').value = spkid;
    switchView('simulate');
  };

  // ─── Event wiring ──────────────────────────────────────────────────────

  // Tab switching (desktop sidebar + mobile bottom bar)
  function wireTabs(selector) {
    document.querySelectorAll(selector).forEach(btn => {
      btn.addEventListener('click', () => switchView(btn.dataset.view));
    });
  }
  wireTabs('#view-tabs-desktop .list-group-item');
  wireTabs('#view-tabs-mobile .btn');

  // Refresh asteroids
  document.getElementById('refresh-asteroids').addEventListener('click', loadAsteroids);

  // ─── Build Ship Modal ────────────────────────────────────────────────
  window.showBuildShipModal = function() {
    document.getElementById('shipNameInput').value = '';
    document.getElementById('buildShipError').classList.add('d-none');
    const modal = new bootstrap.Modal(document.getElementById('buildShipModal'));
    modal.show();
  };

  window.buildShip = async function() {
    const name = document.getElementById('shipNameInput').value.trim();
    const cls = document.getElementById('shipClassInput').value;
    const errEl = document.getElementById('buildShipError');
    const btn = document.getElementById('buildShipBtn');
    if (!name) {
      errEl.textContent = 'Ship name is required';
      errEl.classList.remove('d-none');
      return;
    }
    btn.disabled = true;
    btn.textContent = 'Building...';
    try {
      const result = await api('/fleet/ships', { method: 'POST', body: JSON.stringify({ name, class_: cls }), headers: { 'Content-Type': 'application/json' } });
      const modal = bootstrap.Modal.getInstance(document.getElementById('buildShipModal'));
      modal.hide();
      loadFleet();
    } catch (e) {
      errEl.textContent = e.message;
      errEl.classList.remove('d-none');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Build';
    }
  };

  // ─── Relaunch ────────────────────────────────────────────────────────
  window.relaunchShip = async function(shipId) {
    if (!confirm('Relaunch ' + shipId + ' on a new mission?')) return;
    try {
      const result = await api('/ships/' + shipId + '/relaunch', { method: 'POST', body: '{}', headers: { 'Content-Type': 'application/json' } });
      loadMissions();
      loadFleet();
    } catch (e) {
      alert('Relaunch failed: ' + e.message);
    }
  };

  // ─── Ship Event Timeline ──────────────────────────────────────────────
  window.toggleShipEvents = async function(shipId) {
    const detailsEl = document.getElementById('ship-events-' + shipId);
    if (!detailsEl) return;
    if (detailsEl.style.display === 'none') {
      detailsEl.style.display = 'block';
      if (!detailsEl.hasChildNodes() || detailsEl.children.length === 0) {
        detailsEl.innerHTML = '<div class="text-center text-muted py-2"><div class="spinner-border spinner-border-sm"></div></div>';
        try {
          const ship = await api('/fleet/ships/' + shipId);
          const events = (ship.events || []).slice(0, 30);
          if (events.length === 0) {
            detailsEl.innerHTML = '<div class="text-muted small py-2 text-center">No events recorded</div>';
            return;
          }
          const eventIcons = {
            built: '🏗️', launched: '🚀', upgraded: '⬆️', auto_upgraded: '🤖',
            mission_complete: '✅', earnings_updated: '💰', disabled: '❌',
          };
          detailsEl.innerHTML = events.map(ev => {
            const icon = eventIcons[ev.event_type] || '📌';
            const time = ev.created_at ? new Date(ev.created_at).toLocaleDateString() : '';
            const desc = ev.data ? (ev.data.status || ev.data.module_id || ev.data.name || JSON.stringify(ev.data).slice(0, 80)) : '';
            return `<div class="d-flex small px-2 py-1 border-bottom border-secondary">
              <span class="me-2">${icon}</span>
              <span class="text-muted me-2" style="font-size:0.6rem;white-space:nowrap">${time}</span>
              <span class="text-info">${escapeHtml(ev.event_type)}</span>
              <span class="text-muted ms-1">${escapeHtml(desc)}</span>
            </div>`;
          }).join('');
        } catch (e) {
          detailsEl.innerHTML = `<div class="text-danger small py-2">Failed to load events: ${escapeHtml(e.message)}</div>`;
        }
      }
    } else {
      detailsEl.style.display = 'none';
    }
  };

  // Filter change auto-reload
  document.getElementById('f-moid').addEventListener('change', loadAsteroids);
  document.getElementById('f-diameter').addEventListener('change', loadAsteroids);

  // Run simulation
  document.getElementById('sim-run').addEventListener('click', runSimulation);

  // ─── Init ──────────────────────────────────────────────────────────────
  async function init() {
    try {
      const health = await api('/health');
      document.getElementById('version-badge').textContent = 'v' + (health.version || '0.3.0');
    } catch (_) {
      document.getElementById('version-badge').textContent = 'v0.3.0';
    }
    await updateStatus();
    await updateStats();
    loadDashboard();
    setInterval(updateStatus, 30000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
