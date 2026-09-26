/* CordovaOS entity graph: records as nodes, shared identifiers as edges.
 *
 * Data comes from the server (demo/entity_graph.py). This file lays it out and
 * draws it as SVG with plain DOM events. No graph library on purpose: the
 * graphs here are small, a few dozen to ~150 nodes, so a seeded force layout
 * in a few lines is enough, the picture is the same on every machine, the
 * stack keeps its no-CDN promise without vendoring another 400KB, and every
 * node and edge is an ordinary DOM element the console can address. */
(function () {
  'use strict';

  var PALETTE = ['#0A2342', '#2CA58D', '#F0A500', '#7B61FF', '#E4572E', '#17BEBB', '#A23B72', '#4F6D7A', '#C8963E', '#3D5A80'];
  var EDGE_COLOUR = { person: '#0A2342', business: '#2CA58D', place: '#F0A500', value: '#9aa5b1' };
  var NS = 'http://www.w3.org/2000/svg';
  var registry = {};

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function colours(legend) {
    var map = {};
    legend.forEach(function (d, i) { map[d] = PALETTE[i % PALETTE.length]; });
    return map;
  }
  function el(tag, attrs, text) {
    var e = document.createElementNS(NS, tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text != null) e.textContent = text;
    return e;
  }

  // Deterministic: seeded by the node ids, so the same result draws the same picture every time.
  function seeded(seedText) {
    var h = 1779033703 ^ seedText.length;
    for (var i = 0; i < seedText.length; i++) { h = Math.imul(h ^ seedText.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); }
    return function () { h = Math.imul(h ^ (h >>> 16), 2246822507); h = Math.imul(h ^ (h >>> 13), 3266489909); h ^= h >>> 16; return (h >>> 0) / 4294967296; };
  }

  // Fruchterman-Reingold with gravity on the connected part, then rescaled to
  // fit its box; a few hundred iterations over <=150 nodes is instant. Records
  // that share no identifier with any other are not thrown at the walls: they
  // sit in a band below, so the picture says "these are here, and unlinked".
  function forceLayout(nodes, edges, w, h) {
    var n = nodes.length; if (!n) return {};
    var rnd = seeded(nodes.map(function (x) { return x.id; }).join('|'));
    var idx = {}; nodes.forEach(function (x, i) { idx[x.id] = i; });
    var px = [], py = [], deg = [];
    for (var i = 0; i < n; i++) { px.push(w * (0.2 + 0.6 * rnd())); py.push(h * (0.2 + 0.6 * rnd())); deg.push(0); }
    var E = edges.map(function (e) { deg[idx[e.source]]++; deg[idx[e.target]]++; return [idx[e.source], idx[e.target]]; });
    var k = Math.max(40, Math.min(110, Math.sqrt((w * h) / n) * 0.9)), t = Math.max(w, h) / 8, iters = 300;
    for (var it = 0; it < iters; it++) {
      var dx = new Array(n).fill(0), dy = new Array(n).fill(0);
      for (var a = 0; a < n; a++) {
        for (var b = a + 1; b < n; b++) {
          var ddx = px[a] - px[b], ddy = py[a] - py[b]; var d = Math.sqrt(ddx * ddx + ddy * ddy + 0.01);
          var f = (k * k) / d;
          dx[a] += ddx / d * f; dy[a] += ddy / d * f; dx[b] -= ddx / d * f; dy[b] -= ddy / d * f;
        }
      }
      E.forEach(function (e) {
        var a = e[0], b = e[1]; var ddx = px[a] - px[b], ddy = py[a] - py[b]; var d = Math.sqrt(ddx * ddx + ddy * ddy) + 0.01;
        var f = (d * d) / k;
        dx[a] -= ddx / d * f; dy[a] -= ddy / d * f; dx[b] += ddx / d * f; dy[b] += ddy / d * f;
      });
      for (var c = 0; c < n; c++) {
        var g = 0.04 * (1 + Math.min(deg[c], 20) / 10);
        dx[c] += (w / 2 - px[c]) * g; dy[c] += (h / 2 - py[c]) * g;
        var len = Math.sqrt(dx[c] * dx[c] + dy[c] * dy[c]) || 1; var step = Math.min(len, t);
        px[c] += dx[c] / len * step; py[c] += dy[c] / len * step;
      }
      t *= 0.985;
    }
    var out = {}; nodes.forEach(function (x, i) { out[x.id] = { x: px[i], y: py[i] }; });
    return out;
  }

  function fitInto(positions, x0, y0, w, h, pad) {
    var ids = Object.keys(positions); if (!ids.length) return positions;
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    ids.forEach(function (id) { var p = positions[id]; minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x); minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y); });
    var bw = Math.max(maxX - minX, 1), bh = Math.max(maxY - minY, 1);
    var sc = Math.min((w - 2 * pad) / bw, (h - 2 * pad) / bh, 1.6);
    var ox = x0 + (w - bw * sc) / 2, oy = y0 + (h - bh * sc) / 2, out = {};
    ids.forEach(function (id) { out[id] = { x: (positions[id].x - minX) * sc + ox, y: (positions[id].y - minY) * sc + oy }; });
    return out;
  }

  // Each connected component is laid out on its own and the components are
  // packed side by side, so two unrelated clusters do not fling each other to
  // the corners and then shrink to fit.
  function components(nodes, edges) {
    var parent = {}; nodes.forEach(function (n) { parent[n.id] = n.id; });
    function find(x) { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; }
    edges.forEach(function (e) { if (parent[e.source] !== undefined && parent[e.target] !== undefined) parent[find(e.source)] = find(e.target); });
    var groups = {}; nodes.forEach(function (n) { var r = find(n.id); (groups[r] = groups[r] || []).push(n); });
    return Object.keys(groups).map(function (k) { return groups[k]; }).sort(function (a, b) { return b.length - a.length; });
  }

  function layout(nodes, edges, w, h) {
    var linked = {}; edges.forEach(function (e) { linked[e.source] = true; linked[e.target] = true; });
    var connected = nodes.filter(function (n) { return linked[n.id]; });
    var isolated = nodes.filter(function (n) { return !linked[n.id]; });
    var cols = Math.max(1, Math.floor((w - 40) / 26)), rows = Math.ceil(isolated.length / cols);
    var band = isolated.length ? Math.min(h * 0.4, 34 + rows * 24) : 0;
    var mainH = h - band, pos = {};

    // Boxes per component, sized by node count; shelf-packed left to right.
    var comps = components(connected, edges), boxes = [], x = 0, y = 0, rowH = 0, maxX = 0;
    comps.forEach(function (comp) {
      var side = Math.max(220, Math.min(Math.max(w, mainH), 34 * Math.sqrt(comp.length) + 60));
      if (x + side > w && x > 0) { x = 0; y += rowH; rowH = 0; }
      boxes.push({ comp: comp, x: x, y: y, w: side, h: side });
      x += side; rowH = Math.max(rowH, side); maxX = Math.max(maxX, x);
    });
    // A single small cluster may grow to fill the space; many clusters shrink to fit.
    var totalH = y + rowH, scale = Math.min(2.2, (w - 16) / Math.max(maxX, 1), (mainH - 16) / Math.max(totalH, 1));
    var ox = (w - maxX * scale) / 2, oy = (mainH - totalH * scale) / 2;
    boxes.forEach(function (b) {
      var ids = {}; b.comp.forEach(function (n) { ids[n.id] = true; });
      var es = edges.filter(function (e) { return ids[e.source] && ids[e.target]; });
      var local = fitInto(forceLayout(b.comp, es, b.w, b.h), 0, 0, b.w, b.h, 30);
      Object.keys(local).forEach(function (id) { pos[id] = { x: ox + (b.x + local[id].x) * scale, y: oy + (b.y + local[id].y) * scale }; });
    });
    isolated.forEach(function (n, i) {
      pos[n.id] = { x: 20 + (i % cols) * 26 + 13, y: mainH + 30 + Math.floor(i / cols) * 24 };
    });
    return { positions: pos, band: band, isolated: isolated.length };
  }

  function badge(status) {
    var cls = status === 'valid' ? 'success' : (status === 'invalid' ? 'danger' : 'secondary');
    return '<span class="badge bg-' + cls + '">' + esc(status) + '</span>';
  }

  function describeRecord(uid, node, data, byId) {
    var side = document.getElementById('side-' + uid); if (!side) return;
    var edges = data.edges.filter(function (e) { return e.source === node.id; });
    var links = edges.map(function (e) {
      var idn = byId[e.target];
      return '<li class="mb-1"><span class="fw-semibold">' + esc(idn ? idn.title : e.target) + '</span>' +
        '<br><small class="text-muted">' + esc(e.label) + '</small>' +
        (idn ? '<br><small>shared by ' + idn.degree + ' records here</small>' : '') + '</li>';
    }).join('');
    side.innerHTML = '<div class="small">' +
      '<div class="text-muted text-uppercase" style="font-size:.7rem;letter-spacing:.05em">' + esc(node.domain) + '</div>' +
      '<div class="fs-6 fw-semibold mb-1">' + esc(node.title) + '</div>' +
      '<div class="mb-2">' + badge(node.status) + ' <code class="small">' + esc(node.instance_id) + '</code></div>' +
      (node.console_url ? '<a class="btn btn-sm btn-primary me-1 mb-2" target="_blank" rel="noopener" href="' + esc(node.console_url) + '"><i class="bi bi-file-earmark-text me-1"></i>Open record</a>' : '') +
      '<a class="btn btn-sm btn-outline-secondary mb-2" target="_blank" rel="noopener" href="' + esc(node.workbench_url) + '"><i class="bi bi-diagram-2 me-1"></i>Open in Workbench</a>' +
      '<div class="text-muted mt-2 mb-1">' + (edges.length ? edges.length + ' shared identifier' + (edges.length === 1 ? '' : 's') : 'No identifier shared with another record in this result') + '</div>' +
      '<ul class="list-unstyled mb-0">' + links + '</ul></div>';
  }

  function describeIdentifier(uid, node, data, byId) {
    var side = document.getElementById('side-' + uid); if (!side) return;
    var recs = data.edges.filter(function (e) { return e.target === node.id; }).map(function (e) {
      var r = byId[e.source];
      return '<li class="mb-1">' + (r && r.console_url ? '<a target="_blank" rel="noopener" href="' + esc(r.console_url) + '">' : '') +
        esc(r ? r.domain + ': ' + r.title : e.source) + (r && r.console_url ? '</a>' : '') +
        '<br><small class="text-muted">' + esc(e.label) + '</small></li>';
    }).join('');
    side.innerHTML = '<div class="small">' +
      '<div class="text-muted text-uppercase" style="font-size:.7rem;letter-spacing:.05em">shared ' + esc(node.kind) + ' identifier</div>' +
      '<div class="fs-6 fw-semibold mb-1">' + esc(node.title) + (node.name ? ' <span class="fw-normal text-muted">' + esc(node.name) + '</span>' : '') + '</div>' +
      '<div class="text-muted mb-2">Component' + (node.components.length === 1 ? '' : 's') + ': ' + esc(node.components.join(', ')) + '</div>' +
      '<div class="text-muted mb-1">Carried by ' + node.degree + ' records in this result. The shared component is the join; no mapping table produced it.</div>' +
      '<ul class="list-unstyled mb-0">' + recs + '</ul></div>';
  }

  function draw(uid) {
    var host = document.getElementById('cy-' + uid);
    var dataEl = document.getElementById('graph-data-' + uid);
    if (!host || !dataEl || host.dataset.drawn) return;
    var data = JSON.parse(dataEl.textContent);
    var colour = colours(data.legend);
    var byId = {}; data.nodes.forEach(function (n) { byId[n.id] = n; });
    var W = host.clientWidth || 600, H = host.clientHeight || 520;
    var lay = layout(data.nodes, data.edges, W, H), pos = lay.positions;
    var isolatedIds = {}; data.nodes.forEach(function (n) { if (!data.edges.some(function (e) { return e.source === n.id || e.target === n.id; })) isolatedIds[n.id] = true; });
    var hubDegree = {}; data.edges.forEach(function (e) { hubDegree[e.target] = (hubDegree[e.target] || 0) + 1; });

    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, width: '100%', height: '100%', 'class': 'cordova-svg' });
    var view = el('g'); svg.appendChild(view);
    var gEdges = el('g', { 'class': 'edges' }), gNodes = el('g', { 'class': 'nodes' });
    view.appendChild(gEdges); view.appendChild(gNodes);

    data.edges.forEach(function (e) {
      var a = pos[e.source], b = pos[e.target]; if (!a || !b) return;
      var g = el('g', { 'class': 'edge', 'data-source': e.source, 'data-target': e.target });
      g.appendChild(el('line', { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: EDGE_COLOUR[e.kind] || EDGE_COLOUR.value, 'stroke-width': 1.4, 'stroke-opacity': 0.55 }));
      // On a busy hub the label repeats dozens of times; the hub node names the component instead.
      if ((hubDegree[e.target] || 0) <= 8) g.appendChild(el('text', { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 - 3, 'text-anchor': 'middle', 'class': 'edge-label' }, e.label));
      gEdges.appendChild(g);
    });

    data.nodes.forEach(function (n) {
      var p = pos[n.id]; if (!p) return;
      var g = el('g', { 'class': 'node ' + (n.type === 'identifier' ? 'identifier ' + (n.kind || '') : 'record'), transform: 'translate(' + p.x + ',' + p.y + ')', 'data-id': n.id });
      if (n.type === 'identifier') {
        var stroke = EDGE_COLOUR[n.kind] || '#4F6D7A';
        if (n.kind === 'place') g.appendChild(el('rect', { x: -12, y: -7, width: 24, height: 14, rx: 3, fill: '#fff', stroke: stroke, 'stroke-width': 1.6 }));
        else g.appendChild(el('rect', { x: -8, y: -8, width: 16, height: 16, transform: 'rotate(45)', fill: '#fff', stroke: stroke, 'stroke-width': 1.6 }));
        g.appendChild(el('text', { y: -13, 'text-anchor': 'middle', 'class': 'id-label' }, n.title + ((hubDegree[n.id] || 0) > 8 ? '  (' + n.components[0] + ', ' + n.degree + ' records)' : '')));
      } else if (isolatedIds[n.id]) {
        g.appendChild(el('circle', { r: 6, fill: colour[n.domain] || '#999', stroke: '#fff', 'stroke-width': 1.5 }));
      } else {
        g.appendChild(el('circle', { r: 9, fill: colour[n.domain] || '#999', stroke: '#fff', 'stroke-width': 2 }));
        g.appendChild(el('text', { y: 21, 'text-anchor': 'middle', 'class': 'node-label' }, n.title));
      }
      g.appendChild(el('title', {}, (n.type === 'identifier' ? 'shared ' + n.kind + ' identifier ' : n.domain + ': ') + n.title));
      g.addEventListener('click', function (ev) {
        ev.stopPropagation();
        gNodes.querySelectorAll('.node.selected').forEach(function (x) { x.classList.remove('selected'); });
        g.classList.add('selected');
        gEdges.querySelectorAll('.edge.lit').forEach(function (x) { x.classList.remove('lit'); });
        gEdges.querySelectorAll('.edge[data-source="' + CSS.escape(n.id) + '"], .edge[data-target="' + CSS.escape(n.id) + '"]').forEach(function (x) { x.classList.add('lit'); });
        if (n.type === 'identifier') describeIdentifier(uid, n, data, byId); else describeRecord(uid, n, data, byId);
      });
      gNodes.appendChild(g);
    });

    // Pan by dragging the background, zoom with the wheel, double-click to reset. All on the viewBox.
    var vb = { x: 0, y: 0, w: W, h: H }, drag = null;
    function apply() { svg.setAttribute('viewBox', vb.x + ' ' + vb.y + ' ' + vb.w + ' ' + vb.h); }
    svg.addEventListener('wheel', function (ev) {
      ev.preventDefault();
      var f = ev.deltaY > 0 ? 1.15 : 1 / 1.15; var r = svg.getBoundingClientRect();
      var mx = vb.x + (ev.clientX - r.left) / r.width * vb.w, my = vb.y + (ev.clientY - r.top) / r.height * vb.h;
      vb.w *= f; vb.h *= f; vb.x = mx - (ev.clientX - r.left) / r.width * vb.w; vb.y = my - (ev.clientY - r.top) / r.height * vb.h; apply();
    }, { passive: false });
    svg.addEventListener('mousedown', function (ev) { drag = { x: ev.clientX, y: ev.clientY, vx: vb.x, vy: vb.y }; });
    window.addEventListener('mousemove', function (ev) {
      if (!drag) return; var r = svg.getBoundingClientRect();
      vb.x = drag.vx - (ev.clientX - drag.x) / r.width * vb.w; vb.y = drag.vy - (ev.clientY - drag.y) / r.height * vb.h; apply();
    });
    window.addEventListener('mouseup', function () { drag = null; });
    svg.addEventListener('dblclick', function () { vb = { x: 0, y: 0, w: W, h: H }; apply(); });

    if (lay.isolated) {
      view.appendChild(el('line', { x1: 12, y1: H - lay.band + 8, x2: W - 12, y2: H - lay.band + 8, stroke: '#dfe4ea', 'stroke-width': 1 }));
      view.appendChild(el('text', { x: 16, y: H - lay.band + 20, 'class': 'band-label' },
        lay.isolated + ' record' + (lay.isolated === 1 ? '' : 's') + ' in this result share' + (lay.isolated === 1 ? 's' : '') + ' no identifier with another here. Hover for the name, click to open.'));
    }
    host.innerHTML = ''; host.appendChild(svg);
    var legend = document.getElementById('legend-' + uid);
    if (legend) {
      legend.innerHTML = data.legend.map(function (d) {
        return '<span class="me-3"><span class="cordova-swatch" style="background:' + colour[d] + '"></span>' + esc(d) + '</span>';
      }).join('') + '<span class="text-muted">&#9670; shared identifier &middot; <span style="color:#0A2342">&#9644;</span> person &middot; <span style="color:#2CA58D">&#9644;</span> business &middot; <span style="color:#F0A500">&#9644;</span> place &middot; drag to pan, wheel to zoom, double-click to reset</span>';
    }
    host.dataset.drawn = '1';
    registry[uid] = { svg: svg, positions: pos, data: data };
  }

  function register(uid) {
    // The graph pane starts hidden, so the host has no size. Draw on first show.
    var btn = document.querySelector('[data-cordova-graph="' + uid + '"]');
    if (!btn) return;
    btn.addEventListener('shown.bs.tab', function () { draw(uid); });
  }

  window.CordovaGraph = { register: register, draw: draw, instances: registry, layout: layout };
})();
