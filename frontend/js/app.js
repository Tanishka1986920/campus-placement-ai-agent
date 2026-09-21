/* Frontend interactive logic for Campus Placement AI UI
   - Hooks mirror the Stitch-export structure
   - Provides resume upload client validation, fake backend integration stubs, loading and error states
   - Prepared to call real APIs: POST /api/query and POST /api/upload (examples)
*/

// Helper: element shortcuts
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

// --- AI Query / Assistant ---
function fillQuery(text) {
  const input = $('#ai-query-input');
  if (input) { input.value = text; input.focus(); }
}

async function executeAskAI() {
  const btn = $('#ask-ai-button');
  const input = $('#ai-query-input');
  const container = $('#ai-response-container');
  if (!input || !container || !btn) return;

  const query = input.value.trim();
  if (!query) {
    // show simple inline error
    const tmp = document.createElement('div');
    tmp.className = 'text-xs text-amber-400 mt-2';
    tmp.innerText = 'Please type a question before asking.';
    input.parentElement.appendChild(tmp);
    setTimeout(() => tmp.remove(), 3000);
    return;
  }

  btn.disabled = true;
  const origHTML = btn.innerHTML;
  btn.innerHTML = `<span class="material-symbols-outlined text-[16px] animate-spin">sync</span><span>Analyzing...</span>`;

  // Show local loading UI
  container.innerHTML = `
    <div class="p-6 rounded-xl bg-navy-950/90 border border-brand-electric/40 space-y-4">
      <div class="flex items-center justify-between">
        <span class="text-xs font-mono text-cyan-400 flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span><span>Synthesizing Placement Data...</span></span>
        <span class="text-xs font-mono text-slate-400">0%</span>
      </div>
      <div class="space-y-2">
        <div class="w-full h-3 bg-white/10 rounded animate-pulse"></div>
        <div class="w-5/6 h-3 bg-white/10 rounded animate-pulse"></div>
        <div class="w-2/3 h-3 bg-white/10 rounded animate-pulse"></div>
      </div>
    </div>
  `;

  // Attempt to call backend API if available. If it fails, show error state.
  try {
    // Example API: /api/query (POST JSON { query })
    const resp = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });

    if (!resp.ok) throw new Error('Server error');

    const data = await resp.json();
    // Expect data = { answer: string, highlights?: [], topics?: [] }
    renderAIResponse(data);
  } catch (err) {
    // Fallback: show simulated response and an error badge
    container.innerHTML = `
      <div class="p-5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-sm space-y-3">
        <div class="flex items-center gap-2 font-bold font-display text-amber-300">
          <span class="material-symbols-outlined text-[18px]">warning</span>
          <span>Unable to reach backend AI — showing cached guidance</span>
        </div>
        <p class="text-[13px] text-slate-200">${escapeHtml(query)} — here's a best-effort suggestion based on local heuristics.</p>
        <ul class="text-xs text-slate-300 mt-2 space-y-1">
          <li>• Review company-specific OA patterns (time per question, question types)</li>
          <li>• Focus on Graphs & DP: Topical exercises and time-boxed runs</li>
          <li>• Add demonstrable metrics to experience bullets</li>
        </ul>
      </div>
    `;
  } finally {
    btn.disabled = false;
    btn.innerHTML = origHTML;
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function renderAIResponse(data) {
  const container = $('#ai-response-container');
  const safeAnswer = escapeHtml(data.answer || 'No answer returned from AI.');
  const topics = (data.topics || []).map(t => `<li class="text-xs text-slate-300">• ${escapeHtml(t)}</li>`).join('');
  container.innerHTML = `
    <div class="flex flex-wrap items-center justify-between gap-3 bg-white/5 p-3.5 rounded-xl border border-white/5">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-lg bg-brand-electric/20 border border-brand-electric/40 flex items-center justify-center text-cyan-400">
          <span class="material-symbols-outlined text-[18px]">verified</span>
        </div>
        <div>
          <p class="text-xs font-bold text-white font-display">AI Response</p>
          <p class="text-[11px] text-slate-400 font-mono">Realtime result</p>
        </div>
      </div>
      <div>
        <button class="text-xs text-slate-300 hover:text-white bg-navy-900 border border-white/10 px-3 py-1.5 rounded-lg" onclick="copyAIData()">Copy to Notes</button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="p-4 rounded-xl bg-navy-950/70 border border-white/5 space-y-3"><div class="flex items-center gap-2 text-cyan-400"><span class="material-symbols-outlined text-[18px]">target</span><h4 class="text-xs font-bold font-mono uppercase tracking-wider">Answer Summary</h4></div><div class="text-xs text-slate-300">${safeAnswer}</div></div>
      <div class="p-4 rounded-xl bg-navy-950/70 border border-white/5 space-y-3"><div class="flex items-center gap-2 text-purple-400"><span class="material-symbols-outlined text-[18px]">psychology_alt</span><h4 class="text-xs font-bold font-mono uppercase tracking-wider">Action Steps</h4></div><div class="text-xs text-slate-300">${escapeHtml((data.actions||'').substring(0,400) || 'Practice mocks, add quantified results to resume.')}</div></div>
      <div class="p-4 rounded-xl bg-navy-950/70 border border-white/5 space-y-3"><div class="flex items-center gap-2 text-emerald-400"><span class="material-symbols-outlined text-[18px]">insights</span><h4 class="text-xs font-bold font-mono uppercase tracking-wider">Topics</h4></div><ul class="text-xs text-slate-300 space-y-1">${topics||'<li class="text-xs text-slate-300">• No topics</li>'}</ul></div>
    </div>
  `;
}

function copyAIData() {
  const btnText = $('#copy-btn-txt');
  try {
    // copy currently rendered AI container text
    const container = $('#ai-response-container');
    const text = container ? container.innerText : '';
    navigator.clipboard?.writeText(text || 'Campus Placement AI notes');
    if (btnText) { btnText.innerText = 'Copied to Clipboard!'; setTimeout(()=>btnText.innerText='Copy to Notes',2000); }
  } catch (err) { if (btnText) btnText.innerText = 'Copy Failed'; setTimeout(()=>btnText.innerText='Copy to Notes',2000); }
}

function startMockSim(){ alert('Initializing AI Mock Interview Simulation Environment with Proctoring Avatar...'); }

// --- Resume upload flow ---
const MAX_UPLOAD_BYTES = 2 * 1024 * 1024; // 2MB recommended for demo

function initResumeUpload(){
  const trigger = $('#btn-upload-trigger');
  const fileInput = $('#resume-file-input');
  const removeBtn = $('#btn-remove-file');
  const filenameEl = $('#upload-filename');
  const metaEl = $('#upload-meta');
  const errEl = $('#upload-error');
  const reanalyzeBtn = $('#reanalyze-btn');

  if (!trigger || !fileInput) return;

  trigger.addEventListener('click', ()=> fileInput.click());

  fileInput.addEventListener('change', () => handleFileSelect(fileInput.files));

  removeBtn.addEventListener('click', () => {
    fileInput.value = '';
    filenameEl.innerText = 'No file uploaded';
    metaEl.innerText = 'Maximum 2 MB · PDF only';
    removeBtn.disabled = true;
    $('#parse-status').innerText = '—';
    $('#score-number').innerText = '—';
    $('#strengths-list').innerText = 'No data';
    $('#gaps-list').innerText = 'No data';
    errEl.classList.add('hidden');
  });

  reanalyzeBtn.addEventListener('click', simulateScanAndUpload);
}

function handleFileSelect(fileList){
  const file = fileList && fileList[0];
  const filenameEl = $('#upload-filename');
  const metaEl = $('#upload-meta');
  const errEl = $('#upload-error');
  const removeBtn = $('#btn-remove-file');
  const input = $('#resume-file-input');

  errEl.classList.add('hidden');
  if (!file) return;

  if (file.type !== 'application/pdf'){
    errEl.innerText = 'Invalid file type. Please upload a PDF.';
    errEl.classList.remove('hidden');
    input.value = '';
    return;
  }

  if (file.size > MAX_UPLOAD_BYTES){
    errEl.innerText = 'File too large. Max allowed is 2 MB.';
    errEl.classList.remove('hidden');
    input.value = '';
    return;
  }

  filenameEl.innerText = file.name;
  metaEl.innerText = `${(file.size/1024).toFixed(0)} KB • PDF`;
  removeBtn.disabled = false;

  // Optionally show instant local parse status
  $('#parse-status').innerText = 'Queued';
}

async function simulateScanAndUpload(){
  const input = $('#resume-file-input');
  const file = input.files && input.files[0];
  const parseStatus = $('#parse-status');
  const scoreNum = $('#score-number');
  const strengths = $('#strengths-list');
  const gaps = $('#gaps-list');
  const uploadError = $('#upload-error');

  uploadError.classList.add('hidden');
  if (!file){ uploadError.innerText = 'Please choose a PDF file first.'; uploadError.classList.remove('hidden'); return; }

  // show scanning visual
  parseStatus.innerText = 'Scanning...';
  scoreNum.innerText = '...';

  // Prepare FormData for backend if available
  const form = new FormData();
  form.append('resume', file);

  try {
    // Example backend endpoint: /api/upload (expects multipart/form-data)
    const resp = await fetch('/api/upload', { method: 'POST', body: form });
    if (!resp.ok) throw new Error('Upload failed');
    const result = await resp.json();
    // Expect result: { score: number, strengths: [], gaps: [] }
    parseStatus.innerText = '100% Parsed';
    scoreNum.innerText = String(result.score || 88);
    strengths.innerText = (result.strengths && result.strengths.join(', ')) || 'Quantified metrics present';
    gaps.innerText = (result.gaps && result.gaps.join(', ')) || 'Docker / Redis missing';
  } catch (err) {
    // Fallback simulated analysis when backend unavailable
    await delay(1200);
    parseStatus.innerText = '100% Parsed (local)';
    scoreNum.innerText = '88';
    strengths.innerText = 'Clear quantifiable metrics framed.';
    gaps.innerText = 'Missing Docker / Kubernetes, Redis terms.';
    uploadError.innerText = 'Upload endpoint not reachable — local simulated results shown.';
    uploadError.classList.remove('hidden');
  }
}

// --- Utility & small helpers ---
function delay(ms){ return new Promise(res => setTimeout(res, ms)); }
function escapeHtml(str){ if(!str) return ''; return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

// Init bindings on DOM ready
window.addEventListener('DOMContentLoaded', ()=>{
  // Map UI buttons to functions
  const askBtn = $('#ask-ai-button');
  if (askBtn) askBtn.addEventListener('click', executeAskAI);

  initResumeUpload();

  // Quick suggestion chips (already wired via inline onclick in HTML)

  // Bind copy button fallback if clipboard not supported
  const copyBtn = document.getElementById('copy-btn-txt');
  if (copyBtn && !navigator.clipboard) copyBtn.innerText = 'Copy not supported';

  // Auto-save some state to sessionStorage for demo resilience
  const aiInput = $('#ai-query-input');
  if (aiInput){ aiInput.value = sessionStorage.getItem('ai_query') || '';
    aiInput.addEventListener('input', ()=> sessionStorage.setItem('ai_query', aiInput.value));
  }

  // Wire auto-fix buttons
  $$('.auto-fix-btn').forEach(btn => btn.addEventListener('click', (e)=>{
    btn.innerText = 'Applied ✓'; btn.disabled = true; btn.classList.add('bg-emerald-600');
  }));
});

// Expose a few functions for convenience in HTML that were in the stitch export
window.fillQuery = fillQuery;
window.executeAskAI = executeAskAI;
window.copyAIData = copyAIData;
window.simulateReanalysis = simulateScanAndUpload;
window.applyFix = function(btn){ btn.innerText = 'Applied ✓'; btn.disabled = true; btn.classList.add('bg-emerald-600'); };
window.startMockSim = startMockSim;
window.setSystemState = function(state){
  const responseCont = document.getElementById('ai-response-container');
  if(!responseCont) return;
  if(state === 'loading'){
    responseCont.innerHTML = `<div class="p-6 rounded-xl bg-navy-950/90 border border-brand-electric/40 space-y-4"><div class="flex items-center justify-between"><span class="text-xs font-mono text-cyan-400 flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span><span>Synthesizing Placement Data from 40 Recruiters...</span></span><span class="text-xs font-mono text-slate-400">72%</span></div><div class="space-y-2"><div class="w-full h-3 bg-white/10 rounded animate-pulse"></div><div class="w-5/6 h-3 bg-white/10 rounded animate-pulse"></div><div class="w-2/3 h-3 bg-white/10 rounded animate-pulse"></div></div></div>`;
  } else if(state === 'warning'){
    responseCont.innerHTML = `<div class="p-5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs space-y-2"><div class="flex items-center gap-2 font-bold font-display text-amber-300"><span class="material-symbols-outlined text-[18px]">warning</span><span>Non-fatal Format Warning Detected</span></div><p>Workday parser may not parse two-column LaTeX tables cleanly. We suggest utilizing the approved Harvard single-column template from Module 04.</p></div>`;
  } else {
    location.reload();
  }
};
