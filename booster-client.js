/**
 * ╔══════════════════════════════════════════════════════════════════════════════╗
 * ║  FalconFX Booster — Production Frontend Integration  v3.0                  ║
 * ║  booster-client.js                                                          ║
 * ║                                                                              ║
 * ║  Runs alongside Yango / Bolt / Uber / Hubtel as a SECONDARY COMPANION MAP. ║
 * ║  This file wires the rider's live GPS into the Booster API and renders      ║
 * ║  Hot Spot Centroids + Drift Vectors onto any map surface (Google Maps,       ║
 * ║  Leaflet, Mapbox, or a native canvas widget).                               ║
 * ║                                                                              ║
 * ║  Usage:                                                                     ║
 * ║    import { BoosterClient } from './booster-client.js';                     ║
 * ║    const client = new BoosterClient({ baseUrl: 'https://your-domain' });    ║
 * ║    client.start(onResult);   // → calls onResult(BoosterOutput) each cycle  ║
 * ║    client.stop();            // → gracefully stops polling                  ║
 * ╚══════════════════════════════════════════════════════════════════════════════╝
 */

'use strict';

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 1 — CONFIGURATION
// ─────────────────────────────────────────────────────────────────────────────

const BOOSTER_DEFAULTS = {
  baseUrl:          '',            // Set to your deployed API domain (no trailing slash)
  searchRadiusKm:   5.0,
  defaultPollMs:    30_000,        // fallback if no next_poll_interval_seconds returned
  minPollMs:        8_000,         // hard floor — never hammer the API faster than 8s
  maxPollMs:        120_000,       // hard ceiling — never wait more than 120s
  simulateHotspots: [],            // inject platform API cart spikes if available
  rainActiveZones:  [],            // flood zones — populate from your weather feed
  enableLogging:    true,
};

// Colour palette for acceleration band rendering
const BAND_COLOURS = {
  'EMERGING':               '#00FF88',   // bright green — pre-checkout explosion
  'PEAKING':                '#FFA500',   // orange — near peak, move fast
  'GHOST (already peaked — mainstream sees it)': '#FF3B30',  // red — avoid
  'QUIET':                  '#8E8E93',   // grey — low signal
  'N/A':                    '#8E8E93',
};

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 2 — GPS TELEMETRY TRACKER
// Reads the device's GPS and computes speed + heading between samples.
// ─────────────────────────────────────────────────────────────────────────────

class GPSTracker {
  constructor() {
    this._watchId    = null;
    this._prev       = null;       // { lat, lng, timestamp }
    this._current    = null;       // { lat, lng, speed_kmh, heading_deg, timestamp }
    this._onUpdate   = null;
  }

  /**
   * Start watching GPS. Calls onUpdate(telemetry) on each fix.
   * @param {Function} onUpdate - callback({ lat, lng, speed_kmh, heading_deg })
   */
  start(onUpdate) {
    if (!navigator.geolocation) {
      console.warn('[BoosterGPS] Geolocation not available — using mock position.');
      this._startMock(onUpdate);
      return;
    }
    this._onUpdate = onUpdate;
    this._watchId = navigator.geolocation.watchPosition(
      (pos) => this._handleFix(pos),
      (err) => console.warn('[BoosterGPS] Error:', err.message),
      { enableHighAccuracy: true, timeout: 10_000, maximumAge: 2_000 },
    );
  }

  stop() {
    if (this._watchId !== null) {
      navigator.geolocation.clearWatch(this._watchId);
      this._watchId = null;
    }
  }

  _handleFix(pos) {
    const { latitude: lat, longitude: lng, speed, heading } = pos.coords;
    const now = pos.timestamp;

    // Use device-provided speed/heading if available; otherwise derive from track
    let speed_kmh    = (speed != null && speed >= 0) ? speed * 3.6 : 0;
    let heading_deg  = (heading != null && heading >= 0) ? heading : 0;

    if (this._prev) {
      const dt_s   = (now - this._prev.timestamp) / 1000;
      if (dt_s > 0.5) {
        const dist_km = _haversineKm(this._prev.lat, this._prev.lng, lat, lng);
        if (speed == null) speed_kmh = (dist_km / dt_s) * 3600;
        if (heading == null) heading_deg = _bearingDeg(this._prev.lat, this._prev.lng, lat, lng);
      }
    }

    this._prev    = { lat, lng, timestamp: now };
    this._current = { lat, lng, speed_kmh: Math.round(speed_kmh), heading_deg: Math.round(heading_deg) };

    if (this._onUpdate) this._onUpdate(this._current);
  }

  /** Fallback mock GPS for development / desktop testing (Accra centre). */
  _startMock(onUpdate) {
    let t = 0;
    const MOCK_ROUTE = [
      { lat: 5.605, lng: -0.173, speed_kmh: 28, heading_deg: 135 },
      { lat: 5.595, lng: -0.179, speed_kmh: 32, heading_deg: 180 },
      { lat: 5.580, lng: -0.185, speed_kmh: 22, heading_deg: 200 },
      { lat: 5.570, lng: -0.178, speed_kmh: 18, heading_deg: 90  },
      { lat: 5.568, lng: -0.170, speed_kmh: 0,  heading_deg: 90  },
    ];
    this._watchId = setInterval(() => {
      const fix = MOCK_ROUTE[t % MOCK_ROUTE.length];
      this._current = fix;
      onUpdate(fix);
      t++;
    }, 5_000);
  }

  get current() { return this._current; }
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 3 — BOOSTER API CLIENT
// Core fetch loop with adaptive polling driven by next_poll_interval_seconds.
// ─────────────────────────────────────────────────────────────────────────────

class BoosterClient {
  /**
   * @param {object} options — merged with BOOSTER_DEFAULTS
   * @param {string} options.baseUrl           — API base URL
   * @param {number} options.searchRadiusKm    — km radius to scan
   * @param {Array}  options.simulateHotspots  — [{lat,lng,intensity}] platform spikes
   * @param {Array}  options.rainActiveZones   — ['Accra Central', ...]
   * @param {boolean} options.enableLogging
   */
  constructor(options = {}) {
    this._cfg      = { ...BOOSTER_DEFAULTS, ...options };
    this._gps      = new GPSTracker();
    this._timer    = null;
    this._running  = false;
    this._lastGps  = null;
    this._onResult = null;
    this._onError  = null;

    // Rider metadata (optional — set before start() if delivery is active)
    this.activeDelivery  = false;
    this.dropoffLat      = null;
    this.dropoffLng      = null;
    this.fuelLevelPct    = 100;
  }

  /**
   * Start polling. Calls onResult(BoosterOutput) each cycle.
   * @param {Function} onResult  — required: receives BoosterOutput JSON
   * @param {Function} [onError] — optional: receives (error, gpsSnapshot)
   */
  start(onResult, onError = null) {
    if (this._running) return;
    this._running  = true;
    this._onResult = onResult;
    this._onError  = onError;

    this._log('BoosterClient starting...');
    this._gps.start((fix) => { this._lastGps = fix; });

    // First call immediately, then schedule adaptively
    setTimeout(() => this._poll(), 1_500);
  }

  stop() {
    this._running = false;
    this._gps.stop();
    if (this._timer) { clearTimeout(this._timer); this._timer = null; }
    this._log('BoosterClient stopped.');
  }

  /** Manually inject active delivery state between polls. */
  setDelivery({ active, dropoffLat, dropoffLng, fuelLevelPct }) {
    this.activeDelivery = active;
    this.dropoffLat     = dropoffLat   ?? this.dropoffLat;
    this.dropoffLng     = dropoffLng   ?? this.dropoffLng;
    this.fuelLevelPct   = fuelLevelPct ?? this.fuelLevelPct;
  }

  // ── Internal poll loop ────────────────────────────────────────────────────

  async _poll() {
    if (!this._running) return;

    const gps = this._lastGps || { lat: ACCRA_FALLBACK.lat, lng: ACCRA_FALLBACK.lng,
                                    speed_kmh: 0, heading_deg: 0 };
    let nextMs = this._cfg.defaultPollMs;

    try {
      const result = await this._fetchBooster(gps);

      // ── Read adaptive interval from backend response
      const rawSecs = result?.next_poll_interval_seconds;
      if (typeof rawSecs === 'number' && rawSecs > 0) {
        nextMs = Math.min(
          this._cfg.maxPollMs,
          Math.max(this._cfg.minPollMs, rawSecs * 1000),
        );
      }

      this._log(`Poll OK | interval=${rawSecs}s | band=${result?.grid_stats?.top_zone_band}`);
      if (this._onResult) this._onResult(result, gps);

    } catch (err) {
      this._log(`Poll ERROR: ${err.message}`, 'warn');
      if (this._onError) this._onError(err, gps);
      // Back off on error
      nextMs = Math.min(60_000, nextMs * 2);
    }

    if (this._running) {
      this._timer = setTimeout(() => this._poll(), nextMs);
    }
  }

  async _fetchBooster(gps) {
    const url     = `${this._cfg.baseUrl}/booster/compute`;
    const payload = {
      rider: {
        lat:                 gps.lat,
        lng:                 gps.lng,
        speed_kmh:           gps.speed_kmh,
        heading_deg:         gps.heading_deg,
        has_active_delivery: this.activeDelivery,
        dropoff_lat:         this.dropoffLat,
        dropoff_lng:         this.dropoffLng,
        fuel_level_pct:      this.fuelLevelPct,
      },
      search_radius_km:  this._cfg.searchRadiusKm,
      simulate_hotspots: this._cfg.simulateHotspots,
      rain_active_zones: this._cfg.rainActiveZones,
    };

    const res = await fetch(url, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
      signal:  AbortSignal.timeout(15_000),   // 15s hard timeout per request
    });

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`HTTP ${res.status}: ${text.slice(0, 120)}`);
    }

    return res.json();
  }

  _log(msg, level = 'log') {
    if (this._cfg.enableLogging) console[level](`[Booster] ${msg}`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 4 — MAP RENDERER
// Framework-agnostic renderer. Supports Google Maps, Leaflet, and Mapbox.
// Pass in an adapter object that implements the MapAdapter interface below.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * MapAdapter interface (implement one of these for your map library):
 *
 *   adapter.clearLayer(layerId)                   — remove all shapes in a named layer
 *   adapter.drawCircle({ lat, lng, radiusM, color, opacity, layerId, label })
 *   adapter.drawPolyline({ points: [{lat,lng}], color, weight, opacity, layerId })
 *   adapter.drawArrow({ fromLat, fromLng, toLat, toLng, color, weight, layerId })
 *   adapter.showToast(message, durationMs)         — heads-up notification
 *   adapter.panTo(lat, lng)                        — optional: keep rider centred
 *
 * See Section 6 below for ready-made adapters for Google Maps, Leaflet, and Mapbox.
 */

class BoosterMapRenderer {
  /**
   * @param {object} mapAdapter — implements the MapAdapter interface above
   */
  constructor(mapAdapter) {
    this._map = mapAdapter;
  }

  /**
   * Main entry point. Call this inside the BoosterClient onResult callback.
   * @param {object} boosterOutput — full BoosterOutput JSON from /booster/compute
   * @param {{ lat, lng }} riderGps — current rider GPS fix
   */
  render(boosterOutput, riderGps) {
    this._clearAll();

    const {
      hotspots, primary_vector, leapfrog_vector,
      waybill_alert, weather_advisory,
      hold_recommended, hold_reason, grid_stats,
    } = boosterOutput;

    // ── 1. Hot Spot Centroids ─────────────────────────────────────────────
    //    Loop through top-3 centroid objects and draw demand halos.
    if (Array.isArray(hotspots)) {
      hotspots.forEach((hs, idx) => {
        const colour = BAND_COLOURS[hs.acceleration_band] ?? '#FFA500';
        const radiusM = Math.round(hs.radius_km * 1000);

        // Outer demand halo (translucent)
        this._map.drawCircle({
          lat: hs.lat, lng: hs.lng,
          radiusM: radiusM * 2.5,
          color: colour,
          opacity: 0.15 - idx * 0.04,
          layerId: 'booster-hotspots',
          label: null,
        });

        // Inner pulse ring
        this._map.drawCircle({
          lat: hs.lat, lng: hs.lng,
          radiusM: radiusM,
          color: colour,
          opacity: 0.55 - idx * 0.12,
          layerId: 'booster-hotspots',
          label: `#${idx + 1} ${hs.label.slice(0, 28)} | ${hs.acceleration_band} | ETA ${hs.checkout_eta_min}min`,
        });
      });
    }

    // ── 2. Primary Drift Vector ───────────────────────────────────────────
    //    Draw an arrow from rider's position to the top intercept target.
    if (primary_vector && riderGps) {
      const targetColour = hold_recommended ? '#FF9500' : '#30D158';

      this._map.drawArrow({
        fromLat: riderGps.lat,
        fromLng: riderGps.lng,
        toLat:   primary_vector.target_lat,
        toLng:   primary_vector.target_lng,
        color:   targetColour,
        weight:  4,
        layerId: 'booster-vector',
      });

      // Dotted corridor path (rider → target)
      this._map.drawPolyline({
        points: [
          { lat: riderGps.lat,              lng: riderGps.lng              },
          { lat: primary_vector.target_lat, lng: primary_vector.target_lng },
        ],
        color:   targetColour,
        weight:  2,
        opacity: 0.45,
        dashed:  true,
        layerId: 'booster-vector',
      });
    }

    // ── 3. Leapfrog Vector (active delivery only) ─────────────────────────
    if (leapfrog_vector) {
      this._map.drawArrow({
        fromLat: boosterOutput.rider.dropoff_lat ?? riderGps.lat,
        fromLng: boosterOutput.rider.dropoff_lng ?? riderGps.lng,
        toLat:   leapfrog_vector.target_lat,
        toLng:   leapfrog_vector.target_lng,
        color:   '#0A84FF',
        weight:  3,
        layerId: 'booster-leapfrog',
      });
    }

    // ── 4. Waybill Intercept Marker ───────────────────────────────────────
    if (waybill_alert) {
      this._map.drawCircle({
        lat:     waybill_alert.hub_lat,
        lng:     waybill_alert.hub_lng,
        radiusM: 200,
        color:   '#FFD60A',
        opacity: 0.80,
        layerId: 'booster-waybill',
        label:   `⚡ Bus in ${waybill_alert.next_arrival_min}min — ${waybill_alert.hub}`,
      });
    }

    // ── 5. Rain Dry-Edge Advisory ─────────────────────────────────────────
    if (weather_advisory) {
      this._map.drawCircle({
        lat:     weather_advisory.dry_edge_lat,
        lng:     weather_advisory.dry_edge_lng,
        radiusM: 500,
        color:   '#00CFFF',
        opacity: 0.55,
        layerId: 'booster-weather',
        label:   `🌧 Dry edge — demand ×2`,
      });
    }

    // ── 6. Hold / Move Toast ──────────────────────────────────────────────
    const pollLabel = grid_stats?.poll_mode ?? '';
    if (hold_recommended) {
      this._map.showToast?.(
        `🛑 HOLD — ${hold_reason?.slice(0, 80)}`,
        8_000,
      );
    } else if (primary_vector) {
      const bearing = primary_vector.bearing_deg;
      const dir     = _compassLabel(bearing);
      this._map.showToast?.(
        `✅ MOVE ${dir} ${primary_vector.distance_km}km → GHS ${primary_vector.expected_yield_ghs.toFixed(2)} | ${pollLabel}`,
        6_000,
      );
    }
  }

  _clearAll() {
    ['booster-hotspots', 'booster-vector', 'booster-leapfrog',
     'booster-waybill', 'booster-weather'].forEach((id) => {
      this._map.clearLayer?.(id);
    });
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 5 — COMPLETE INTEGRATION EXAMPLE
// Copy-paste this into your app entry point and swap the map adapter.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * initBooster — full integration bootstrap.
 *
 * @param {object} mapAdapter   — any adapter from Section 6 (or your own)
 * @param {string} apiBaseUrl   — your deployed /booster API root URL
 * @returns {{ client: BoosterClient, renderer: BoosterMapRenderer }}
 *
 * Example usage:
 *
 *   // In your app startup (after map is ready):
 *   const { client, renderer } = initBooster(
 *     createLeafletAdapter(myLeafletMapInstance),
 *     'https://my-falconfx-api.replit.app',
 *   );
 *
 *   // Update delivery state dynamically:
 *   client.setDelivery({ active: true, dropoffLat: 5.706, dropoffLng: -0.163, fuelLevelPct: 72 });
 *
 *   // Inject platform API cart-spike signals (Bolt/Yango pre-checkout webhook):
 *   client._cfg.simulateHotspots = [{ lat: 5.570, lng: -0.170, intensity: 65 }];
 *
 *   // Stop when user backgrounds the app:
 *   document.addEventListener('visibilitychange', () => {
 *     if (document.hidden) client.stop(); else client.start(onResult);
 *   });
 */
function initBooster(mapAdapter, apiBaseUrl = '') {
  const renderer = new BoosterMapRenderer(mapAdapter);

  const client = new BoosterClient({
    baseUrl:         apiBaseUrl,
    searchRadiusKm:  5.0,
    enableLogging:   true,
  });

  function onResult(boosterOutput, gps) {
    renderer.render(boosterOutput, gps);

    // ── You can also feed the raw JSON into your own UI components:
    // updateHUDWidget(boosterOutput);
    // updateDriftArrow(boosterOutput.primary_vector);
    // updateHotspotList(boosterOutput.hotspots);
    // updatePollTimer(boosterOutput.next_poll_interval_seconds);
  }

  function onError(err, gps) {
    console.error('[Booster] API error:', err.message, 'GPS:', gps);
    // Optionally show a subtle offline indicator in the UI
  }

  client.start(onResult, onError);

  return { client, renderer };
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 6 — MAP ADAPTERS (ready-made for Google Maps, Leaflet, Mapbox)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * createLeafletAdapter — wraps a Leaflet map instance.
 * @param {L.Map} map — Leaflet map instance
 */
function createLeafletAdapter(map) {
  const layers = {};

  function getLayer(id) {
    if (!layers[id]) {
      layers[id] = window.L.layerGroup().addTo(map);
    }
    return layers[id];
  }

  return {
    clearLayer(layerId) {
      if (layers[layerId]) layers[layerId].clearLayers();
    },

    drawCircle({ lat, lng, radiusM, color, opacity, layerId, label }) {
      const circle = window.L.circle([lat, lng], {
        radius:      radiusM,
        color:       color,
        fillColor:   color,
        fillOpacity: opacity,
        weight:      1,
      });
      if (label) circle.bindPopup(label);
      circle.addTo(getLayer(layerId));
    },

    drawPolyline({ points, color, weight, opacity, dashed, layerId }) {
      const latlngs = points.map((p) => [p.lat, p.lng]);
      const line = window.L.polyline(latlngs, {
        color,
        weight,
        opacity,
        dashArray: dashed ? '8 6' : null,
      });
      line.addTo(getLayer(layerId));
    },

    drawArrow({ fromLat, fromLng, toLat, toLng, color, weight, layerId }) {
      const latlngs = [[fromLat, fromLng], [toLat, toLng]];
      const arrow = window.L.polyline(latlngs, {
        color,
        weight,
        opacity: 0.85,
      });
      // Use leaflet-arrowheads if available; else plain polyline
      if (arrow.arrowheads) arrow.arrowheads({ size: '12px', frequency: 'endonly' });
      arrow.addTo(getLayer(layerId));
    },

    showToast(message, durationMs) {
      // Simple toast: append a div, auto-remove
      const el = document.createElement('div');
      el.style.cssText = `
        position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
        background: rgba(0,0,0,0.82); color: #fff; padding: 10px 18px;
        border-radius: 20px; font-size: 13px; font-weight: 600;
        z-index: 9999; max-width: 90vw; text-align: center; pointer-events: none;
      `;
      el.textContent = message;
      document.body.appendChild(el);
      setTimeout(() => el.remove(), durationMs);
    },

    panTo(lat, lng) { map.panTo([lat, lng]); },
  };
}

/**
 * createGoogleMapsAdapter — wraps a Google Maps map instance.
 * @param {google.maps.Map} map
 */
function createGoogleMapsAdapter(map) {
  const layers = {};   // layerId → [google.maps.MVCObject]

  function getLayer(id) {
    if (!layers[id]) layers[id] = [];
    return layers[id];
  }

  return {
    clearLayer(layerId) {
      (layers[layerId] || []).forEach((shape) => shape.setMap(null));
      layers[layerId] = [];
    },

    drawCircle({ lat, lng, radiusM, color, opacity, layerId, label }) {
      const circle = new window.google.maps.Circle({
        map,
        center:      { lat, lng },
        radius:      radiusM,
        strokeColor: color,
        strokeWeight: 1,
        fillColor:   color,
        fillOpacity: opacity,
      });
      if (label) {
        const iw = new window.google.maps.InfoWindow({ content: label });
        circle.addListener('click', () => iw.setPosition({ lat, lng }) && iw.open(map));
      }
      getLayer(layerId).push(circle);
    },

    drawPolyline({ points, color, weight, opacity, dashed, layerId }) {
      const path   = points.map((p) => ({ lat: p.lat, lng: p.lng }));
      const icons  = dashed ? [{ icon: { path: 'M 0,-1 0,1', strokeOpacity: 1, scale: 3 },
                                  offset: '0', repeat: '12px' }] : [];
      const line = new window.google.maps.Polyline({
        map, path, strokeColor: color,
        strokeWeight: weight, strokeOpacity: opacity,
        icons,
      });
      getLayer(layerId).push(line);
    },

    drawArrow({ fromLat, fromLng, toLat, toLng, color, weight, layerId }) {
      const ARROW = window.google.maps.SymbolPath.FORWARD_CLOSED_ARROW;
      const line  = new window.google.maps.Polyline({
        map,
        path: [{ lat: fromLat, lng: fromLng }, { lat: toLat, lng: toLng }],
        strokeColor: color,
        strokeWeight: weight,
        icons: [{ icon: { path: ARROW, scale: 4 }, offset: '100%' }],
      });
      getLayer(layerId).push(line);
    },

    showToast(message, durationMs) {
      const el = document.createElement('div');
      el.style.cssText = `
        position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
        background: rgba(0,0,0,0.82); color: #fff; padding: 10px 18px;
        border-radius: 20px; font-size: 13px; font-weight: 600;
        z-index: 9999; max-width: 90vw; text-align: center; pointer-events: none;
      `;
      el.textContent = message;
      document.body.appendChild(el);
      setTimeout(() => el.remove(), durationMs);
    },

    panTo(lat, lng) { map.panTo({ lat, lng }); },
  };
}

/**
 * createMapboxAdapter — wraps a Mapbox GL JS map instance.
 * @param {mapboxgl.Map} map
 */
function createMapboxAdapter(map) {
  const layerIds = new Set();

  function ensureSource(id, geoJson) {
    if (map.getSource(id)) {
      map.getSource(id).setData(geoJson);
    } else {
      map.addSource(id, { type: 'geojson', data: geoJson });
    }
  }

  return {
    clearLayer(layerId) {
      if (layerIds.has(layerId)) {
        try { map.removeLayer(layerId); } catch (_) {}
        try { map.removeSource(layerId); } catch (_) {}
        layerIds.delete(layerId);
      }
    },

    drawCircle({ lat, lng, radiusM, color, opacity, layerId, label }) {
      const id = `${layerId}-circle-${Date.now()}`;
      ensureSource(id, { type: 'Feature', geometry: { type: 'Point', coordinates: [lng, lat] } });
      map.addLayer({
        id, type: 'circle', source: id,
        paint: {
          'circle-radius':   radiusM / 8,
          'circle-color':    color,
          'circle-opacity':  opacity,
          'circle-stroke-width': 1,
          'circle-stroke-color': color,
        },
      });
      layerIds.add(id);
    },

    drawPolyline({ points, color, weight, opacity, dashed, layerId }) {
      const coords = points.map((p) => [p.lng, p.lat]);
      const id = `${layerId}-line-${Date.now()}`;
      ensureSource(id, { type: 'Feature', geometry: { type: 'LineString', coordinates: coords } });
      map.addLayer({
        id, type: 'line', source: id,
        paint: {
          'line-color':   color,
          'line-width':   weight,
          'line-opacity': opacity,
          'line-dasharray': dashed ? [2, 2] : [1],
        },
      });
      layerIds.add(id);
    },

    drawArrow({ fromLat, fromLng, toLat, toLng, color, weight, layerId }) {
      this.drawPolyline({
        points: [{ lat: fromLat, lng: fromLng }, { lat: toLat, lng: toLng }],
        color, weight, opacity: 0.85, dashed: false, layerId,
      });
    },

    showToast(message, durationMs) {
      const el = document.createElement('div');
      el.style.cssText = `
        position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
        background: rgba(0,0,0,0.82); color: #fff; padding: 10px 18px;
        border-radius: 20px; font-size: 13px; font-weight: 600;
        z-index: 9999; max-width: 90vw; text-align: center; pointer-events: none;
      `;
      el.textContent = message;
      document.body.appendChild(el);
      setTimeout(() => el.remove(), durationMs);
    },

    panTo(lat, lng) { map.flyTo({ center: [lng, lat] }); },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 7 — HEALTH CHECK & SHADOW MATRIX UTILITIES
// ─────────────────────────────────────────────────────────────────────────────

/**
 * checkHealth — confirm the Booster API is alive and loaded.
 * @param {string} baseUrl
 * @returns {Promise<object>}  — { status, grid_cells, places_loaded, shadow_matrix_zones, ... }
 */
async function checkHealth(baseUrl = '') {
  const res = await fetch(`${baseUrl}/booster/health`);
  if (!res.ok) throw new Error(`Health check failed: HTTP ${res.status}`);
  return res.json();
}

/**
 * getShadowWindows — fetch which offline chop bar / canteen windows are firing.
 * @param {string} baseUrl
 * @param {number} [hour]    — override hour (default: server time / Accra GMT+0)
 * @param {number} [minute]
 * @returns {Promise<{ active_windows: string[], count: number }>}
 */
async function getShadowWindows(baseUrl = '', hour = null, minute = null) {
  let url = `${baseUrl}/booster/shadow`;
  const params = [];
  if (hour   != null) params.push(`hour=${hour}`);
  if (minute != null) params.push(`minute=${minute}`);
  if (params.length)  url += '?' + params.join('&');
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Shadow check failed: HTTP ${res.status}`);
  return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 8 — SPATIAL HELPER FUNCTIONS  (pure JS, no dependencies)
// ─────────────────────────────────────────────────────────────────────────────

const ACCRA_FALLBACK = { lat: 5.60, lng: -0.18 };
const EARTH_R = 6371.0;

function _haversineKm(lat1, lng1, lat2, lng2) {
  const toRad = (x) => (x * Math.PI) / 180;
  const dphi  = toRad(lat2 - lat1);
  const dlng  = toRad(lng2 - lng1);
  const phi1  = toRad(lat1);
  const phi2  = toRad(lat2);
  const a = Math.sin(dphi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(dlng / 2) ** 2;
  return 2 * EARTH_R * Math.asin(Math.sqrt(a));
}

function _bearingDeg(lat1, lng1, lat2, lng2) {
  const toRad = (x) => (x * Math.PI) / 180;
  const phi1  = toRad(lat1);
  const phi2  = toRad(lat2);
  const dlng  = toRad(lng2 - lng1);
  const x = Math.sin(dlng) * Math.cos(phi2);
  const y = Math.cos(phi1) * Math.sin(phi2) - Math.sin(phi1) * Math.cos(phi2) * Math.cos(dlng);
  return ((Math.atan2(x, y) * 180) / Math.PI + 360) % 360;
}

function _compassLabel(deg) {
  const dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE',
                 'S','SSW','SW','WSW','W','WNW','NW','NNW'];
  return dirs[Math.round(deg / 22.5) % 16];
}

// ─────────────────────────────────────────────────────────────────────────────
// EXPORTS  (works as ESM module, CommonJS, or plain script)
// ─────────────────────────────────────────────────────────────────────────────

if (typeof module !== 'undefined' && module.exports) {
  // CommonJS / Node.js
  module.exports = {
    BoosterClient,
    BoosterMapRenderer,
    GPSTracker,
    initBooster,
    createLeafletAdapter,
    createGoogleMapsAdapter,
    createMapboxAdapter,
    checkHealth,
    getShadowWindows,
    BAND_COLOURS,
    BOOSTER_DEFAULTS,
  };
} else if (typeof window !== 'undefined') {
  // Browser global
  window.FalconFX = {
    BoosterClient,
    BoosterMapRenderer,
    GPSTracker,
    initBooster,
    createLeafletAdapter,
    createGoogleMapsAdapter,
    createMapboxAdapter,
    checkHealth,
    getShadowWindows,
    BAND_COLOURS,
  };
}

// ESM export (bundlers / Vite / Metro)
export {
  BoosterClient,
  BoosterMapRenderer,
  GPSTracker,
  initBooster,
  createLeafletAdapter,
  createGoogleMapsAdapter,
  createMapboxAdapter,
  checkHealth,
  getShadowWindows,
  BAND_COLOURS,
  BOOSTER_DEFAULTS,
};
