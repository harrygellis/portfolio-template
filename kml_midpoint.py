<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bed Points</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: system-ui, sans-serif;
    background: #fff;
    color: #111;
    padding: 32px 20px;
    max-width: 420px;
    margin: 0 auto;
  }

  h1 { font-size: 18px; font-weight: 600; margin-bottom: 28px; }

  .row { margin-bottom: 20px; }

  label { display: block; font-size: 13px; color: #666; margin-bottom: 6px; }

  input[type="file"] { font-size: 15px; width: 100%; }

  input[type="number"] {
    width: 100%;
    font-size: 24px;
    font-weight: 600;
    padding: 10px 12px;
    border: 1.5px solid #ccc;
    border-radius: 6px;
    outline: none;
    -moz-appearance: textfield;
  }
  input[type="number"]::-webkit-inner-spin-button,
  input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; }
  input[type="number"]:focus { border-color: #333; }

  .hint { font-size: 12px; color: #888; margin-top: 5px; min-height: 16px; }

  .error { font-size: 13px; color: #c00; margin-bottom: 16px; display: none; }
  .error.show { display: block; }

  button {
    width: 100%;
    background: #111;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 600;
    padding: 14px;
    cursor: pointer;
  }
  button:disabled { background: #ccc; cursor: not-allowed; }

  .result { display: none; margin-top: 20px; text-align: center; }
  .result.show { display: block; }
  .result-num { font-size: 48px; font-weight: 700; line-height: 1; }
  .result-label { font-size: 13px; color: #666; margin-top: 4px; }
  .result-spacing { font-size: 13px; color: #444; margin-top: 6px; }

  a.dl {
    display: inline-block;
    margin-top: 16px;
    background: #111;
    color: #fff;
    text-decoration: none;
    border-radius: 6px;
    font-size: 15px;
    font-weight: 600;
    padding: 12px 28px;
  }
</style>
</head>
<body>

<h1>Bed Points</h1>

<div class="row">
  <label>KML file (2 points)</label>
  <input type="file" id="fileInput" accept=".kml">
  <div class="hint" id="fileHint"></div>
</div>

<div class="row">
  <label>Number of beds</label>
  <input type="number" id="bedCount" min="2" placeholder="e.g. 12" inputmode="numeric">
  <div class="hint" id="bedHint"></div>
</div>

<div class="error" id="errorBox"></div>

<button id="generateBtn" disabled>Generate</button>

<div class="result" id="result">
  <div class="result-num" id="resultNum"></div>
  <div class="result-label">points generated</div>
  <div class="result-spacing" id="resultSpacing"></div>
  <a class="dl" id="downloadLink" href="#">Download KML</a>
</div>

<script>
  let points = null, outName = '';

  const fileInput     = document.getElementById('fileInput');
  const fileHint      = document.getElementById('fileHint');
  const bedCount      = document.getElementById('bedCount');
  const bedHint       = document.getElementById('bedHint');
  const generateBtn   = document.getElementById('generateBtn');
  const errorBox      = document.getElementById('errorBox');
  const result        = document.getElementById('result');
  const resultNum     = document.getElementById('resultNum');
  const resultSpacing = document.getElementById('resultSpacing');
  const downloadLink  = document.getElementById('downloadLink');

  function parseKML(text) {
    const re = /<coordinates>\s*([-\d.]+)\s*,\s*([-\d.]+)(?:\s*,\s*([-\d.]+))?\s*<\/coordinates>/g;
    const pts = []; let m;
    while ((m = re.exec(text)) !== null)
      pts.push({ lon: +m[1], lat: +m[2], alt: m[3] ? +m[3] : 0 });
    return pts;
  }

  function haversine(a, b) {
    const R = 6371000, toR = Math.PI / 180;
    const dLat = (b.lat - a.lat) * toR, dLon = (b.lon - a.lon) * toR;
    const x = Math.sin(dLat/2)**2 + Math.cos(a.lat*toR)*Math.cos(b.lat*toR)*Math.sin(dLon/2)**2;
    return R * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1-x));
  }

  function interpolate(a, b, n) {
    return Array.from({length: n}, (_, i) => {
      const t = i / (n - 1);
      return { lon: a.lon + t*(b.lon-a.lon), lat: a.lat + t*(b.lat-a.lat), alt: a.alt + t*(b.alt-a.alt) };
    });
  }

  function buildKML(pts) {
    const pm = pts.map(p => `  <Placemark><Point><coordinates>${p.lon},${p.lat},${p.alt}</coordinates></Point></Placemark>`).join('\n');
    return `<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n  <Document>\n${pm}\n  </Document>\n</kml>`;
  }

  function fmtDist(m) { return m >= 1000 ? (m/1000).toFixed(2)+'km' : Math.round(m)+'m'; }
  function fmtSpacing(m) { return m >= 1 ? m.toFixed(2)+'m' : (m*100).toFixed(1)+'cm'; }
  function checkReady() { generateBtn.disabled = !(points && parseInt(bedCount.value) >= 2); }

  fileInput.addEventListener('change', e => {
    const file = e.target.files[0];
    if (!file) return;
    outName = file.name.replace(/\.kml$/i, '') + '_beds.kml';
    const reader = new FileReader();
    reader.onload = ev => {
      const parsed = parseKML(ev.target.result);
      if (parsed.length !== 2) {
        errorBox.textContent = `Need exactly 2 points — found ${parsed.length}.`;
        errorBox.classList.add('show');
        fileHint.textContent = '';
        points = null;
      } else {
        errorBox.classList.remove('show');
        points = parsed;
        fileHint.textContent = `✓ ${fmtDist(haversine(points[0], points[1]))} between points`;
      }
      checkReady();
    };
    reader.readAsText(file);
  });

  bedCount.addEventListener('input', () => {
    const n = parseInt(bedCount.value);
    if (n >= 2 && points) {
      bedHint.textContent = fmtSpacing(haversine(points[0], points[1]) / (n - 1)) + ' spacing';
    } else {
      bedHint.textContent = '';
    }
    checkReady();
  });

  generateBtn.addEventListener('click', () => {
    const n = parseInt(bedCount.value);
    if (!points || n < 2) return;
    const pts = interpolate(points[0], points[1], n);
    const blob = new Blob([buildKML(pts)], { type: 'application/vnd.google-earth.kml+xml' });
    downloadLink.href = URL.createObjectURL(blob);
    downloadLink.download = outName;
    resultNum.textContent = n;
    resultSpacing.textContent = fmtSpacing(haversine(points[0], points[1]) / (n - 1)) + ' between each point';
    result.classList.add('show');
  });
</script>
</body>
</html>