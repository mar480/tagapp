/* Offline browser diagnostics. Report text and images never go to stdout.
 * Invoked only through browser_probe.py's restricted worker.
 */
const fs = require('node:fs');
const { chromium } = require('/deps/node_modules/playwright');
const controlsOnly = process.env.PROBE_CONTROL_ONLY === '1';
const diagnose = process.env.PROBE_DIAGNOSE_SELECTION === '1';
const diagnostics = [];
const geometryControl = '<!doctype html><style>body{margin:0}.t{position:absolute;white-space:pre;font:36px sans-serif;letter-spacing:-.36px;transform:scale(.25);transform-origin:0 100%}</style><div data-page-no="1" style="width:600px;height:800px"><div class="t" style="left:31.515625px;top:30.25px">12345</div><div class="t" style="left:101.71875px;top:80.75px">1234.</div><div class="t" style="left:51.375px;top:130.125px">(12<span>,345</span>)</div><div class="t" style="left:211.5625px;top:180.5px;word-spacing:-.8px">-987.65 </div></div>';

const pages = controlsOnly ? [] : process.env.PROBE_PAGES.split(',').map(Number);
if ((!controlsOnly && !pages.length) || pages.some(p => !Number.isInteger(p) || p < 1 || p > 108)) throw new Error('invalid_page_configuration');

async function inspect(page, number, zoom) {
  return page.evaluate(({ number, zoom }) => {
    const report = document.querySelector(`[data-page-no="${number.toString(16)}"]`);
    report.style.zoom = String(zoom);
    const pageRect = report.getBoundingClientRect();
    const candidates = [];
    let clipped = 0, invisible = 0;
    for (const [lineIndex, line] of [...report.querySelectorAll('.t')].entries()) {
      const walker = document.createTreeWalker(line, NodeFilter.SHOW_TEXT);
      const nodes = [];
      let node, offset = 0;
      while ((node = walker.nextNode())) {
        nodes.push({ node, start: offset, end: offset + node.length });
        offset += node.length;
      }
      const value = line.textContent;
      for (const match of value.matchAll(/(?:\(-?\d[\d,]*(?:\.\d+)?%?\)|-?\d[\d,]*(?:\.\d+)?%?)/g)) {
        const start = match.index, end = start + match[0].length;
        const first = nodes.find(n => n.start <= start && n.end > start);
        const last = nodes.find(n => n.start < end && n.end >= end);
        if (!first || !last) continue;
        const range = document.createRange();
        range.setStart(first.node, start - first.start);
        range.setEnd(last.node, end - last.start);
        const rects = [...range.getClientRects()].filter(r => r.width > 0 && r.height > 0);
        if (!rects.length) { invisible++; continue; }
        if (rects.some(r => r.left < pageRect.left - 1 || r.top < pageRect.top - 1 || r.right > pageRect.right + 1 || r.bottom > pageRect.bottom + 1)) clipped++;
        // Character edges avoid accidentally dragging adjacent glyphs.
        const a = range.cloneRange(), z = range.cloneRange();
        a.setEnd(first.node, start - first.start + 1);
        z.setStart(last.node, end - last.start - 1);
        const ar = a.getBoundingClientRect(), zr = z.getBoundingClientRect();
        candidates.push({ lineIndex, start, end, firstRect: {left: ar.left, right: ar.right, top: ar.top, height: ar.height}, lastRect: {left: zr.left, right: zr.right, top: zr.top, height: zr.height}, expected: range.toString(), from: { x: ar.left + 0.2, y: ar.top + ar.height / 2 },
          to: { x: zr.right - 0.2, y: zr.top + zr.height / 2 }, rect: { x: ar.left - pageRect.left, y: ar.top - pageRect.top }, length: match[0].length });
      }
    }
    // Prefer longer numeric runs to exercise actual values, then sample across page.
    const useful = candidates.filter(c => c.length >= 3);
    const pool = useful.length ? useful : candidates;
    const selected = [];
    for (let i = 0; i < Math.min(8, pool.length); i++) selected.push(pool[Math.floor(i * pool.length / Math.min(8, pool.length))]);
    return { numericRanges: candidates.length, clipped, invisible, samples: selected,
      width: pageRect.width, height: pageRect.height };
  }, { number, zoom });
}

async function dragSamples(page, data, number, zoom, differences, scope) {
  let matched = 0;
        for (let i = 0; i < data.samples.length; i++) {
          const sample = data.samples[i];
          await page.evaluate(() => window.getSelection().removeAllRanges());
          await page.mouse.move(sample.from.x, sample.from.y);
          await page.mouse.down();
          await page.mouse.move(sample.to.x, sample.to.y, { steps: 8 });
          await page.mouse.up();
          const actual = await page.evaluate(() => window.getSelection().toString());
          const compact = s => s.normalize('NFKC').replace(/\s/g, '');
          if (compact(actual) === compact(sample.expected)) matched++;
          else {
            differences.push({ scope, page: number, zoom, sample: i, expected: sample.expected, actual, position: sample.rect });
          }
          if (diagnose) diagnostics.push({...await diagnoseSample(page, sample, number, zoom, i), scope, baselineMatched:compact(actual)===compact(sample.expected)});
        }

  return matched;
}

async function diagnoseSample(page, sample, number, zoom, index) {
  // Structural/caret metadata only. Expected and selected report text remain private.
  const metadata = await page.evaluate(({sample, number}) => {
    const report = document.querySelector(`[data-page-no="${number.toString(16)}"]`);
    const line = report.querySelectorAll('.t')[sample.lineIndex];
    const walker = document.createTreeWalker(line, NodeFilter.SHOW_TEXT);
    const nodes = []; let node, offset = 0;
    while ((node = walker.nextNode())) { nodes.push({node,start:offset,end:offset+node.length}); offset += node.length; }
    function caret(point) {
      const hit = document.caretPositionFromPoint(point.x, point.y);
      const entry = hit && nodes.find(n => n.node === hit.offsetNode);
      return entry ? entry.start + hit.offset : null;
    }
    function hit(point) {
      const element = document.elementFromPoint(point.x, point.y);
      return {withinLine: !!element && (element === line || line.contains(element)), tag: element?.tagName};
    }
    const style = getComputedStyle(line);
    const selection=window.getSelection();
    const locate=(node,offset) => {const entry=nodes.find(n=>n.node===node);return entry?entry.start+offset:null};
    const ancestors=[]; for(let e=line;e && e!==report.parentElement;e=e.parentElement) ancestors.push({tag:e.tagName,select:getComputedStyle(e).userSelect,draggable:e.draggable});
    return {start:sample.start,end:sample.end,fromCaret:caret(sample.from),toCaret:caret(sample.to),
      selectionAnchor:locate(selection.anchorNode,selection.anchorOffset),selectionFocus:locate(selection.focusNode,selection.focusOffset),ancestors,from:sample.from,to:sample.to,fromHit:hit(sample.from),toHit:hit(sample.to),lineLength:offset,
      userSelect:style.userSelect,unicodeBidi:style.unicodeBidi,
      lineWidth:line.getBoundingClientRect().width,endBeyondLine:sample.to.x-line.getBoundingClientRect().right,
      fontSize:style.fontSize,letterSpacing:style.letterSpacing,wordSpacing:style.wordSpacing,transform:style.transform,
      firstWidth:sample.firstRect.right-sample.firstRect.left,lastWidth:sample.lastRect.right-sample.lastRect.left};
  }, {sample,number});
  const variants = [];
  // Fixed coordinates chosen before looking at the selection outcome. No CSS,
  // DOM selection override, retries, snapping or report-content edits.
  await page.evaluate(() => window.getSelection().removeAllRanges());
  const first=sample.firstRect, last=sample.lastRect;
  await page.mouse.move(first.left+(first.right-first.left)*0.25, first.top+first.height/2);
  await page.mouse.down();
  await page.mouse.move(last.right-(last.right-last.left)*0.25,last.top+last.height/2,{steps:8});
  await page.mouse.up();
  const actual=await page.evaluate(() => window.getSelection().toString());
  variants.push({name:'inset_quarter_glyph',matched:actual.normalize('NFKC').replace(/\s/g,'')===sample.expected.normalize('NFKC').replace(/\s/g,''),length:actual.length});
  return {page:number,zoom,sample:index,...metadata,variants};
}

function stage(value) { fs.writeFileSync('/output/progress.json', JSON.stringify({ stage: value })); }
async function main() {
  stage('launch');
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1500, height: 2100 },
      javaScriptEnabled: true, serviceWorkers: 'block', offline: true });
    let blockedRequests = 0;
    await context.route('**/*', route => {
      if (['http://tagger.invalid/report', 'http://tagger.invalid/control', 'http://tagger.invalid/geometry'].includes(route.request().url())) return route.fulfill({
        status: 200, contentType: 'text/html; charset=utf-8', body: route.request().url().endsWith('/geometry') ? geometryControl : route.request().url().endsWith('/control') ? '<!doctype html><style>body{margin:0;font:22px monospace}.t{margin:20px;line-height:2}</style><div data-page-no="1" style="width:600px;height:800px"><div class="t">Revenue 1,<span>234</span>.50</div><div class="t">Loss (12.34)</div><div class="t">Comparative 987.00</div><div class="t">Negative -42.75</div></div><script>globalThis.__reportScriptExecuted=true;</script>' : fs.readFileSync('/input/report.html'),
        headers: { 'Content-Security-Policy': "default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:; base-uri 'none'; form-action 'none'; frame-src 'none'" }
      });
      blockedRequests++;
      return route.abort();
    });
    stage('new_page');
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    stage('synthetic_control');
    await page.goto('http://tagger.invalid/control', { waitUntil: 'load' });
    const control = [], controlDifferences = [];
    const scriptsBlocked = await page.evaluate(() => globalThis.__reportScriptExecuted !== true);
    for (const zoom of [1, 1.5]) {
      const data = await inspect(page, 1, zoom);
      const matched = await dragSamples(page, data, 1, zoom, controlDifferences, 'synthetic');
      control.push({ zoom, samples: data.samples.length, matched });
    }
    fs.writeFileSync('/output/synthetic-control.json', JSON.stringify({ scripts_blocked: scriptsBlocked, checks: control }));
    if (!scriptsBlocked || control.some(r => r.samples !== 4 || r.matched !== 4)) throw new Error('synthetic_control_failed');
    const geometry = [];
    if (diagnose) {
      await page.goto('http://tagger.invalid/geometry', {waitUntil:'load'});
      for (const zoom of [1,1.5]) {
        const data=await inspect(page,1,zoom);
        const matched=await dragSamples(page,data,1,zoom,[],'geometry');
        geometry.push({zoom,samples:data.samples.length,edge_matches:matched});
      }
      const rows=diagnostics.filter(r=>r.scope==='geometry');
      if (rows.length!==8 || rows.some(r=>!r.variants[0].matched)) throw new Error('geometry_control_failed');
    }
    if (controlsOnly) {
      const insetControls=diagnostics.filter(r=>r.scope==='synthetic');
      if (insetControls.length!==8 || insetControls.some(r=>!r.variants[0].matched)) throw new Error('inset_control_failed');
      fs.writeFileSync('/output/browser-result.json',JSON.stringify({
        schema_version:1,status:'synthetic_selection_checks_pass',browser_version:browser.version(),
        playwright_version:require('/deps/node_modules/playwright/package.json').version,
        synthetic_control:control,geometry_control:geometry,
        inset_control_samples:8,inset_control_matches:8,geometry_inset_samples:8,geometry_inset_matches:8,
        script_canary_blocked:scriptsBlocked,blocked_requests:blockedRequests,production_qualified:false,
        scope:'Public synthetic controls only; no report loaded'
      },null,2));
      return;
    }
    stage('load_report');
    await page.goto('http://tagger.invalid/report', { waitUntil: 'load' });
    // The converter viewer normally reveals .pc with JS. Keep scripts disabled;
    // only expose static pages and remove viewer chrome for measurement.
    stage('static_page_style');
    await page.evaluate(content => { const style = document.createElement("style"); style.textContent = content; document.head.appendChild(style); }, '#sidebar,.loading-indicator{display:none!important}#page-container{position:static!important;overflow:visible!important;background:white!important;margin:0!important;padding:0!important}html,body{margin:0!important;padding:0!important;background:white!important}.pf{display:none!important;margin:0!important;box-shadow:none!important}.pc{display:block!important}.pf.probe-active{display:block!important}');
    stage('font_wait');
    await page.evaluate(async () => { await Promise.race([document.fonts.ready, new Promise((_, reject) => setTimeout(() => reject(new Error('font_timeout')), 5000))]); });
    
    const results = [], differences = [];
    for (const number of pages) {
      stage('page_' + number);
      await page.evaluate(number => {
        document.querySelectorAll('.probe-active').forEach(p => p.classList.remove('probe-active'));
        document.querySelector(`[data-page-no="${number.toString(16)}"]`).classList.add('probe-active');
        window.scrollTo(0, 0);
      }, number);
      for (const zoom of [1, 1.5]) {
        await page.evaluate(async ({number, zoom}) => {
          document.querySelector(`[data-page-no="${number.toString(16)}"]`).style.zoom = String(zoom);
          await Promise.race([document.fonts.ready, new Promise((_, reject) => setTimeout(() => reject(new Error('font_timeout')), 5000))]);
        }, {number, zoom});
        const data = await inspect(page, number, zoom);
        const matched = await dragSamples(page, data, number, zoom, differences, 'report');
        await page.evaluate(() => window.getSelection().removeAllRanges());
        if (!diagnose && zoom === 1) await page.locator(`[data-page-no="${number.toString(16)}"]`).screenshot({ path: `/output/html-page-${number}.png`, animations: 'disabled' });
        results.push({ page: number, zoom, numeric_ranges: data.numericRanges, ranges_outside_page: data.clipped,
          ranges_without_rectangles: data.invisible, pointer_samples: data.samples.length, pointer_matches: matched,
          width: data.width, height: data.height });
      }
    }
    fs.writeFileSync('/output/private-selection-differences.json', JSON.stringify(differences, null, 2));
    const fonts = await page.evaluate(() => [...document.fonts].map(f => ({ status: f.status })));
    const issues = differences.length || results.some(r => r.ranges_outside_page || r.ranges_without_rectangles) || fonts.some(f => f.status === 'error');
    const result = { schema_version: 1, status: issues ? 'review_required' : 'sampled_pointer_checks_pass',
      browser_version: browser.version(), playwright_version: require('/deps/node_modules/playwright/package.json').version,
      network: 'OS network namespace disabled; browser offline; requests restricted', report_scripts: 'blocked by response Content-Security-Policy',
      blocked_requests: blockedRequests, fonts_loaded: fonts.filter(f => f.status === 'loaded').length,
      fonts_failed: fonts.filter(f => f.status === 'error').length, synthetic_control: control, script_canary_blocked: scriptsBlocked, pages: results, ...(diagnose ? {selection_diagnostics: diagnostics, geometry_control:geometry, geometry_inset_samples:diagnostics.filter(r=>r.scope==='geometry').length, geometry_inset_matches:diagnostics.filter(r=>r.scope==='geometry'&&r.variants[0].matched).length, inset_pointer_samples:diagnostics.filter(r=>r.scope==='report').length, inset_pointer_matches:diagnostics.filter(r=>r.scope==='report'&&r.variants[0].matched).length, inset_control_samples:diagnostics.filter(r=>r.scope==='synthetic').length, inset_control_matches:diagnostics.filter(r=>r.scope==='synthetic'&&r.variants[0].matched).length} : {}), production_qualified: false };
    fs.writeFileSync('/output/browser-result.json', JSON.stringify(result, null, 2));
  } finally { stage('closing'); await browser.close(); }
}

main().catch(error => {
  fs.writeFileSync('/output/private-browser-error.log', String(error.stack || error));
  // Playwright errors can include report text. Never print arbitrary exceptions.
  fs.writeFileSync('/output/browser-result.json', JSON.stringify({ schema_version: 1, status: 'unable_to_complete', reason: 'browser_worker_failed', production_qualified: false }));
  process.exitCode = 1;
});
