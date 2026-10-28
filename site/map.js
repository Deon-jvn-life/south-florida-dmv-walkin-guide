/* Office map. Leaflet 1.9.4 is loaded from /vendor/leaflet/ only after the map is near the screen. */
(function () {
  if (window.__officeMaps) return;
  window.__officeMaps = 1;
  var nodes = document.querySelectorAll(".office-map");
  if (!nodes.length) return;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function directionsLink(pin) {
    var href = String(pin.directions || "");
    if (href.indexOf("https://www.google.com/maps/dir/?api=1&destination=") !== 0) return "";
    return '<a href="' + esc(href) + '" target="_blank" rel="noopener">Get directions<span class="sr-only"> to ' + esc(pin.name) + " (opens in a new tab)</span></a>";
  }

  function popupHtml(group) {
    var html = "";
    if (group.length > 1) {
      html += "<p>These offices are close together on this view. Zoom in to separate the pins.</p>";
    }
    for (var i = 0; i < group.length; i++) {
      var pin = group[i];
      html += '<p class="pin-name"><strong>' + esc(pin.name) + "</strong><br>" + esc(pin.address) + "<br>" + directionsLink(pin) + "</p>";
    }
    return html;
  }

  function accessName(group) {
    if (group.length === 1) return group[0].name + ", " + group[0].address;
    var names = [];
    for (var i = 0; i < group.length; i++) names.push(group[i].name);
    return group.length + " offices close together: " + names.join(", ");
  }

  /* Group pins whose dots would sit on top of each other. Each pin keeps its own coordinates. */
  function clusters(pins, map) {
    var pts = [];
    for (var i = 0; i < pins.length; i++) {
      var p = map.latLngToContainerPoint([pins[i].lat, pins[i].lon]);
      pts.push({ pin: pins[i], x: p.x, y: p.y });
    }
    var parent = [];
    for (var n = 0; n < pts.length; n++) parent.push(n);
    function find(a) {
      while (parent[a] !== a) a = parent[a];
      return a;
    }
    for (var a = 0; a < pts.length; a++) {
      for (var b = a + 1; b < pts.length; b++) {
        var dx = pts[a].x - pts[b].x;
        var dy = pts[a].y - pts[b].y;
        if (dx * dx + dy * dy < 46 * 46) parent[find(b)] = find(a);
      }
    }
    var groups = {};
    for (var k = 0; k < pts.length; k++) {
      var root = find(k);
      if (!groups[root]) groups[root] = [];
      groups[root].push(pts[k]);
    }
    var out = [];
    for (var key in groups) if (groups.hasOwnProperty(key)) out.push(groups[key]);
    return out;
  }

  function anchorOf(group) {
    if (group.length === 1) return group[0].pin;
    var ax = 0;
    var ay = 0;
    for (var i = 0; i < group.length; i++) { ax += group[i].x; ay += group[i].y; }
    ax /= group.length;
    ay /= group.length;
    var best = group[0];
    var bestD = Infinity;
    for (var j = 0; j < group.length; j++) {
      var ddx = group[j].x - ax;
      var ddy = group[j].y - ay;
      var d = ddx * ddx + ddy * ddy;
      if (d < bestD) { bestD = d; best = group[j]; }
    }
    return best.pin;
  }

  function initOne(el) {
    if (el.getAttribute("data-map-ready") === "1" || !window.L) return;
    var raw = el.getAttribute("data-pins") || "[]";
    var pins = [];
    try { pins = JSON.parse(raw); } catch (err) { return; }
    if (!pins.length) return;
    el.setAttribute("data-map-ready", "1");
    var label = el.getAttribute("data-label") || "";
    var described = el.getAttribute("data-describedby") || "";
    var fallback = el.querySelector(".map-fallback");
    if (fallback) fallback.remove();
    var reduce = false;
    try { reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (err) { reduce = false; }
    var map = L.map(el, {
      scrollWheelZoom: false,
      keyboard: false,
      zoomControl: true,
      attributionControl: true,
      zoomAnimation: !reduce,
      fadeAnimation: !reduce,
      markerZoomAnimation: !reduce
    });
    if (label) el.setAttribute("aria-label", label);
    el.setAttribute("role", "region");
    el.setAttribute("tabindex", "-1");
    if (described) el.setAttribute("aria-describedby", described);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a> contributors'
    }).addTo(map);
    var placed = [];
    for (var i = 0; i < pins.length; i++) {
      if (typeof pins[i].lat !== "number" || typeof pins[i].lon !== "number") continue;
      placed.push(pins[i]);
    }
    var layer = L.layerGroup().addTo(map);
    function renderPins() {
      layer.clearLayers();
      var groups = clusters(placed, map);
      for (var g = 0; g < groups.length; g++) {
        var group = groups[g];
        var offices = [];
        for (var p = 0; p < group.length; p++) offices.push(group[p].pin);
        var at = anchorOf(group);
        var name = accessName(offices);
        var count = offices.length > 1 ? String(offices.length) : "";
        var icon = L.divIcon({
          className: "pin-icon",
          html: '<span class="pin-btn">' + esc(count) + "</span>",
          iconSize: [44, 44],
          iconAnchor: [22, 22],
          popupAnchor: [0, -24]
        });
        var marker = L.marker([at.lat, at.lon], {
          icon: icon,
          title: name,
          keyboard: true,
          riseOnHover: false
        });
        marker.bindPopup(popupHtml(offices), { maxWidth: 320, minWidth: 220, maxHeight: 240, autoPanPadding: [56, 56] });
        marker.addTo(layer);
        var node = marker.getElement();
        if (node) node.setAttribute("aria-label", name);
      }
    }
    var bounds = [];
    for (var b = 0; b < placed.length; b++) bounds.push([placed[b].lat, placed[b].lon]);
    if (bounds.length === 1) map.setView(bounds[0], 15, { animate: false });
    else if (bounds.length) map.fitBounds(bounds, { padding: [48, 48], maxZoom: 14, animate: false });
    renderPins();
    map.on("zoomend", renderPins);
    function disarm() { map.scrollWheelZoom.disable(); }
    el.addEventListener("click", function () { map.scrollWheelZoom.enable(); });
    el.addEventListener("mouseleave", disarm);
    el.addEventListener("focusout", function (e) {
      if (!el.contains(e.relatedTarget)) disarm();
    });
    map.on("popupopen", function () {
      var root = el.querySelector(".leaflet-popup");
      if (!root) return;
      var closeBtn = root.querySelector(".leaflet-popup-close-button");
      if (closeBtn && !closeBtn.getAttribute("aria-label")) closeBtn.setAttribute("aria-label", "Close popup");
      var content = root.querySelector(".leaflet-popup-content");
      if (content && content.scrollHeight > content.clientHeight + 4) {
        content.setAttribute("tabindex", "0");
        content.setAttribute("aria-label", "Offices at this pin");
      }
    });
  }

  function initAll() {
    for (var i = 0; i < nodes.length; i++) initOne(nodes[i]);
  }

  var started = false;
  function boot() {
    if (started) return;
    started = true;
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/vendor/leaflet/leaflet.css";
    document.head.appendChild(link);
    var script = document.createElement("script");
    script.src = "/vendor/leaflet/leaflet.js";
    script.onload = initAll;
    document.head.appendChild(script);
  }

  if (!("IntersectionObserver" in window)) {
    boot();
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].isIntersecting) {
        io.disconnect();
        boot();
        return;
      }
    }
  }, { rootMargin: "240px 0px" });
  for (var n = 0; n < nodes.length; n++) io.observe(nodes[n]);
})();
