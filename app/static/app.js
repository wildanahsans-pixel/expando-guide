const API_BASE_URL = 'https://expando-guide.onrender.com';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const state={token:localStorage.getItem('expando_token'),user:null,page:'landing',projectId:null,assessmentStep:0,assessment:{},assessmentQuestions:[],country:'SG',countryCategory:'general',shippingResult:null};
const api=async(path,opts={})=>{const headers={...(opts.headers||{})};if(state.token)headers.Authorization='Bearer '+state.token;if(opts.body&&!(opts.body instanceof FormData))headers['Content-Type']='application/json';const res=await fetch(path,{...opts,headers});const type=res.headers.get('content-type')||'';const data=type.includes('json')?await res.json():await res.text();if(!res.ok){let msg=data.detail||data.message||'Terjadi kesalahan';if(Array.isArray(msg))msg=msg.map(x=>x.msg||JSON.stringify(x)).join('; ');const err=new Error(msg);err.status=res.status;throw err}return data};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=n=>new Intl.NumberFormat('id-ID',{style:'currency',currency:'IDR',maximumFractionDigits:0}).format(n||0);
function toast(m,err=false){let x=$('#toast');if(!x){x=document.createElement('div');x.id='toast';document.body.append(x)}x.textContent=m;x.className='toast '+(err?'error':'');x.classList.add('show');setTimeout(()=>x.classList.remove('show'),3600)}
function logo(){return `<div class="brand"><span class="mark">⌖</span><span>Expando<span>.</span></span></div>`}
function landing() {
    return `
    <header class="container topbar">
        ${logo()}
        <div class="top-actions">
            <a class="btn btn-outline" href="#features">Features</a>
            <a class="btn btn-outline" href="#pricing">Pricing</a>
            <button class="btn btn-outline" onclick="showAuth('login')">Log In</button>
            <button class="btn btn-primary" onclick="showAuth('register')">Get Started</button>
        </div>
    </header>

    <section class="hero">
        <div class="container hero-grid">
            <div>
                <span class="eyebrow">EXPORT GUIDANCE WORKSPACE</span>
                <h1>From Local Business to Global Markets.</h1>
                <p>
                    Navigate export readiness, explore international markets,
                    manage shipping decisions, and prepare your export documents
                    — all in one workspace.
                </p>

                <div class="hero-actions">
                    <button class="btn btn-primary" onclick="showAuth('register')">
                        Get Started →
                    </button>
                    <a class="btn btn-outline" href="#features">
                        Explore Features
                    </a>
                </div>

                <p class="tiny" style="color:#a8b6ca;margin-top:20px">
                    Structured guidance. Practical workflows.
                    Better export decisions.
                </p>
            </div>

            <div class="hero-visual">
                <div class="globe">◎</div>
                <div class="mini-stat">
                    <div><strong>01</strong><small>Assess</small></div>
                    <div><strong>02</strong><small>Validate</small></div>
                    <div><strong>03</strong><small>Execute</small></div>
                </div>
            </div>
        </div>
    </section>

    <section class="section" id="features">
        <div class="container">
            <div class="section-head">
                <h2>Everything You Need to Navigate Global Trade</h2>
                <p>
                    From assessing your business readiness to preparing
                    your first international shipment.
                </p>
            </div>

            <div class="feature-grid">
                ${feature('◈','Guided Readiness','Assess your export capabilities through a structured, step-by-step evaluation.')}
                ${feature('▤','Action Roadmap','Turn export requirements into actionable steps, deliverables, and measurable progress.')}
                ${feature('◎','Country Intelligence','Explore market requirements, trade information, and official regulatory sources.')}
                ${feature('⇢','Shipping Decisions','Understand shipping responsibilities and choose suitable Incoterms.')}
                ${feature('▣','Document Intelligence','Upload export documents and review their completeness using rule-based checks.')}
                ${feature('▦','Export Cost Calculator','Estimate export expenses and understand your potential landed costs.')}
            </div>
        </div>
    </section>

    <section class="section" id="pricing" style="background:#f1f5f9">
        <div class="container">
            <div class="section-head">
                <h2>Choose Your Workspace</h2>
                <p>
                    Start with the essentials and unlock more capabilities
                    as your business grows.
                </p>
            </div>

            <div class="pricing-grid">
                <div class="price-card">
                    <span class="badge">FREE</span>
                    <div class="price">Rp0 <small>/ forever</small></div>
                    <ul class="check-list">
                        <li>1 project</li>
                        <li>1 readiness assessment</li>
                        <li>2 destination countries</li>
                        <li>1 cost calculation/month</li>
                        <li>100 MB document storage</li>
                    </ul>
                    <button class="btn btn-outline" style="width:100%"
                        onclick="showAuth('register')">
                        Get Started Free
                    </button>
                </div>

                <div class="price-card popular">
                    <span class="badge green">PREMIUM</span>
                    <div class="price">Rp49,000 <small>/ month</small></div>
                    <ul class="check-list">
                        <li>Up to 10 projects</li>
                        <li>Unlimited assessments</li>
                        <li>All destination countries</li>
                        <li>Full workspace features</li>
                        <li>2 GB document storage</li>
                    </ul>
                    <button class="btn btn-primary" style="width:100%"
                        onclick="showAuth('register')">
                        Choose Premium
                    </button>
                </div>
                <div class="price-card">
    <span class="badge green">PREMIUM ANNUAL</span>

    <div class="price">
        Rp490,000 <small>/ year</small>
    </div>

    <ul class="check-list">
        <li>Up to 10 projects</li>
        <li>Unlimited assessments</li>
        <li>All destination countries</li>
        <li>Full workspace features</li>
        <li>2 GB document storage</li>
    </ul>

    <button class="btn btn-primary" style="width:100%"
        onclick="showAuth('register')">
        Choose Annual
    </button>
</div>
            </div>
        </div>
    </section>

    <footer class="footer">
        <div class="container"
            style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap">
            ${logo()}
            <span>© ${new Date().getFullYear()} Expando · Export with clarity.</span>
        </div>
    </footer>
    `;
}[]
function feature(i,t,d){return `<article class="feature"><div class="feature-icon">${i}</div><h3>${t}</h3><p>${d}</p></article>`}
function showAuth(p){state.page=p;render()}
function authPage(mode) {
    return `
    <div class="auth-wrap">
        <aside class="auth-side">
            ${logo()}

            <div>
                <span class="eyebrow">YOUR EXPORT WORKSPACE</span>
                <h1>Make global expansion less uncertain.</h1>
                <p>
                    Access your workspace to turn export research,
                    regulations, and operational readiness into
                    actionable decisions.
                </p>
            </div>

            <small>© ${new Date().getFullYear()} Expando</small>
        </aside>

        <main class="auth-main">
            <div class="auth-card">
                <button class="btn btn-outline btn-small"
                    onclick="state.page='landing';render()">
                    ← Back
                </button>

                <h2>
                    ${mode === 'login'
                        ? 'Welcome back'
                        : 'Create your Expando account'}
                </h2>

                <p class="muted">
                    ${mode === 'login'
                        ? 'Sign in with your email and password.'
                        : 'Get started with a Free account.'}
                </p>

                <form id="authForm">
                    ${mode === 'register'
                        ? `
                        <div class="field">
                            <label>Full name</label>
                            <input
                                name="name"
                                required
                                minlength="2"
                                placeholder="Your name">
                        </div>
                        `
                        : ''}

                    <div class="field">
                        <label>Email</label>
                        <input
                            name="email"
                            type="email"
                            required
                            placeholder="name@email.com">
                    </div>

                    <div class="field">
                        <label>Password</label>
                        <input
                            name="password"
                            type="password"
                            required
                            minlength="8"
                            placeholder="At least 8 characters">
                    </div>

                    <button class="btn btn-primary" style="width:100%">
                        ${mode === 'login'
                            ? 'Sign In'
                            : 'Create Free Account'}
                    </button>
                </form>

                <p class="muted tiny" style="margin-top:18px">
                    ${mode === 'login'
                        ? `Don't have an account?
                           <a href="#" onclick="showAuth('register');return false">
                               <b>Sign up</b>
                           </a>`
                        : `Already have an account?
                           <a href="#" onclick="showAuth('login');return false">
                               <b>Sign in</b>
                           </a>`}
                </p>
            </div>
        </main>
    </div>
    `;
}
const navUser=[['dashboard','▦','Dashboard'],['projects','▤','Proyek'],['readiness','◈','Readiness interview'],['checklist','☷','Roadmap'],['countries','◎','Country intelligence'],['calculator','▦','Cost calculator'],['shipping','⇢','Shipping decision'],['documents','▣','Document center'],['subscription','◇','Subscription']];
const navAdmin=[['admin-dashboard','▦','Overview'],['admin-payments','▤','Pembayaran'],['admin-users','♙','Pengguna'],['admin-settings','⚙','Pengaturan']];
function labelFor(p){return [...navUser,...navAdmin].find(x=>x[0]===p)?.[2]||'Workspace'}
function shell(content){let admin=state.user.role==='admin',nav=admin?navAdmin:navUser;return `<div class="app-shell"><aside class="sidebar">${logo()}<div><div class="nav-label">${admin?'ADMINISTRATION':'WORKSPACE'}</div><nav>${nav.map(([id,ic,l])=>`<div class="nav-link ${state.page===id?'active':''}" onclick="go('${id}')"><span>${ic}</span>${l}</div>`).join('')}</nav></div><div class="sidebar-bottom"><div style="padding:12px;color:#94a3b8;font-size:12px">${esc(state.user.name)}<br><b style="color:white">${state.user.plan.toUpperCase()} PLAN</b></div><div class="nav-link" onclick="logout()">↗ Keluar</div></div></aside><main class="main-area"><header class="app-top"><div><b>${admin?'Admin Console':'Expando Workspace'}</b><span class="muted tiny"> / ${labelFor(state.page)}</span></div><div class="top-user"><span class="badge ${state.user.plan==='premium'?'green':''}">${state.user.plan.toUpperCase()}</span><span class="tiny muted">${esc(state.user.name)}</span></div></header><section class="main-content">${content}</section></main></div>`}
function go(p){state.page=p;render()}
function title(t,d,a=''){return `<div class="page-title"><div><h1>${t}</h1><p>${d}</p></div>${a}</div>`}
function stat(t,v,s){return `<div class="stat"><small>${t}</small><strong>${v}</strong><span class="tiny muted">${s||''}</span></div>`}
async function dashboard(){const d=await api('/api/dashboard');return `${title('Dashboard ekspor','Ringkasan aktivitas dan langkah kerja bisnis Anda.',`<button class="btn btn-primary" onclick="go('projects')">＋ Kelola proyek</button>`)}<div class="stats-grid">${stat('Proyek',d.project_count,'Ruang kerja aktif')}${stat('Readiness score',d.latest_score??'—','Penilaian terakhir')}${stat('Kapasitas proyek',d.project_count+'/'+d.project_limit,'Batas paket saat ini')}${stat('Estimasi biaya',d.cost_count,'Tersimpan')}</div><div class="content-grid"><div class="panel"><h3>Mulai dari keputusan penting</h3><div class="action-cards"><button class="action-card" onclick="go('readiness')"><b>01 · Pahami posisi bisnis</b><span>Jawab pertanyaan readiness satu per satu dan dapatkan prioritas perbaikan.</span></button><button class="action-card" onclick="go('countries')"><b>02 · Validasi pasar tujuan</b><span>Baca ringkasan persyaratan berdasarkan negara dan kategori produk.</span></button><button class="action-card" onclick="go('shipping')"><b>03 · Rancang penyerahan barang</b><span>Bandingkan tanggung jawab seller dan buyer sebelum menyepakati Incoterms.</span></button></div></div><div class="panel"><h3>Prinsip penggunaan</h3><p>Angka readiness adalah hasil self-assessment. Country intelligence merupakan ringkasan referensi, bukan data real-time. Rule engine dokumen hanya memeriksa indikator teks awal.</p><div class="notice warn">Selalu validasi HS code, tarif, lartas, sertifikat, dan prosedur pada sumber resmi sebelum transaksi.</div></div></div>`}
async function projectsPage(){const rows=await api('/api/projects');state.projects=rows;return `${title('Proyek ekspor','Satu proyek mewakili satu produk dan satu pasar tujuan.',`<button class="btn btn-primary" onclick="newProject()">＋ Buat proyek</button>`)}<div class="project-grid">${rows.map(p=>`<article class="project-card"><span class="badge">${esc(p.status||'planning')}</span><h3>${esc(p.name)}</h3><p>${esc(p.product||'Produk belum diisi')} · ${esc(p.destination||'Pasar belum ditentukan')}</p><div class="project-actions"><button class="btn btn-primary btn-small" onclick="openRoadmap(${p.id})">Buka roadmap</button><button class="btn btn-outline btn-small" onclick="editProject(${p.id})">Edit</button><button class="btn btn-outline btn-small" onclick="deleteProject(${p.id})">Hapus</button></div></article>`).join('')||'<div class="panel empty">Belum ada proyek. Buat proyek pertama untuk memulai workspace.</div>'}</div>`}
function newProject(){modal(`<h3>Buat proyek ekspor</h3><form id="projectForm"><div class="field"><label>Nama proyek</label><input name="name" required placeholder="Contoh: Ekspor kopi roasted bean ke Singapura"></div><div class="field"><label>Nama produk</label><input name="product" required placeholder="Kopi roasted bean"></div><div class="field"><label>Kategori</label><select name="category"><option value="fnb">Makanan & minuman</option><option value="agriculture">Pertanian</option><option value="wood">Kayu & furnitur</option><option value="manufacturing">Manufaktur</option><option value="general">Lainnya</option></select></div><div class="field"><label>Negara tujuan</label><select name="destination"><option>Singapura</option><option>Malaysia</option><option>Jepang</option><option>Australia</option><option>Belanda</option><option>Amerika Serikat</option></select></div><div class="field"><label>Catatan awal</label><textarea name="notes"></textarea></div><button class="btn btn-primary">Simpan proyek</button></form>`);$('#projectForm').onsubmit=async e=>{e.preventDefault();try{await api('/api/projects',{method:'POST',body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});closeModal();toast('Proyek dibuat.');render()}catch(x){toast(x.message,true)}}}
function modal(html){$('#modalRoot')?.remove();let x=document.createElement('div');x.id='modalRoot';x.className='modal-backdrop';x.innerHTML=`<div class="modal"><div class="modal-head"><span></span><button class="btn btn-outline btn-small" onclick="closeModal()">Tutup ×</button></div>${html}</div>`;x.onclick=e=>{if(e.target===x)closeModal()};document.body.append(x)}function closeModal(){$('#modalRoot')?.remove()}
async function editProject(id){let p=state.projects.find(x=>x.id===id);if(!p)return;modal(`<h3>Edit proyek</h3><form id="editProjectForm"><div class="field"><label>Nama proyek</label><input name="name" value="${esc(p.name)}" required></div><div class="field"><label>Produk</label><input name="product" value="${esc(p.product)}"></div><div class="field"><label>Negara tujuan</label><input name="destination" value="${esc(p.destination)}"></div><div class="field"><label>Catatan</label><textarea name="notes">${esc(p.notes)}</textarea></div><button class="btn btn-primary">Simpan perubahan</button></form>`);$('#editProjectForm').onsubmit=async e=>{e.preventDefault();try{await api('/api/projects/'+id,{method:'PATCH',body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});closeModal();render()}catch(x){toast(x.message,true)}}}
async function deleteProject(id){if(!confirm('Hapus proyek dan data turunannya?'))return;try{await api('/api/projects/'+id,{method:'DELETE'});render()}catch(e){toast(e.message,true)}}
async function readinessPage(){const q=await api('/api/guided/assessment/questions');state.assessmentQuestions=q.steps;state.assessmentStep=0;state.assessment={};const projects=await api('/api/projects');if(!projects.length)return `${title('Guided readiness interview','Buat proyek terlebih dahulu agar hasil penilaian terhubung ke produk dan pasar tujuan.')}<button class="btn btn-primary" onclick="go('projects')">Buat proyek</button>`;return `${title('Guided readiness interview','Jawab satu per satu. Setiap pertanyaan disertai konteks dan panduan agar penilaian tidak sekadar centang.') }<div class="wizard-layout"><div class="panel wizard-main" id="assessmentWizard"></div><aside class="panel wizard-aside"><span class="eyebrow-dark">ASSESSMENT GUIDE</span><h3>Bagaimana skor dibaca?</h3><p>0–39: Belum siap</p><p>40–69: Perlu penguatan</p><p>70–89: Mendekati siap</p><p>90–100: Siap untuk validasi akhir</p><div class="notice warn">Skor ini bukan sertifikasi atau jaminan izin ekspor. Jawab berdasarkan bukti yang benar-benar tersedia.</div></aside></div>`}
function renderAssessmentStep(){const q=state.assessmentQuestions[state.assessmentStep],n=state.assessmentQuestions.length,idx=state.assessmentStep;$('#assessmentWizard').innerHTML=`<div class="wizard-progress"><span>PERTANYAAN ${idx+1} DARI ${n}</span><div class="progress"><span style="width:${(idx+1)/n*100}%"></span></div></div><h2>${esc(q.title)}</h2><h3>${esc(q.question)}</h3><div class="guide-box"><b>Mengapa ini penting?</b><p>${esc(q.guide)}</p></div><div class="answer-options">${q.options.map(o=>`<label class="answer-option ${state.assessment[q.key]===o.value?'selected':''}"><input type="radio" name="assessmentAnswer" value="${o.value}" ${state.assessment[q.key]===o.value?'checked':''}><span><b>${o.value+1}. ${esc(o.label)}</b></span></label>`).join('')}</div><div class="wizard-actions"><button class="btn btn-outline" ${idx===0?'disabled':''} onclick="assessmentPrev()">Sebelumnya</button><button class="btn btn-primary" onclick="assessmentNext()">${idx===n-1?'Lihat hasil':'Lanjutkan'}</button></div>`;$$('input[name=assessmentAnswer]').forEach(i=>i.onchange=()=>{state.assessment[q.key]=Number(i.value);renderAssessmentStep()})}
function assessmentPrev(){state.assessmentStep=Math.max(0,state.assessmentStep-1);renderAssessmentStep()}
async function assessmentNext(){const q=state.assessmentQuestions[state.assessmentStep];if(state.assessment[q.key]===undefined)return toast('Pilih jawaban sebelum lanjut.',true);if(state.assessmentStep<state.assessmentQuestions.length-1){state.assessmentStep++;renderAssessmentStep();return}const ps=await api('/api/projects');modal(`<h3>Simpan hasil readiness</h3><p>Pilih proyek yang dinilai.</p><select id="assessmentProject" class="full-select">${ps.map(p=>`<option value="${p.id}">${esc(p.name)}</option>`).join('')}</select><button class="btn btn-primary" style="margin-top:16px" onclick="submitGuidedAssessment()">Hitung readiness</button>`)}
async function submitGuidedAssessment(){try{const r=await api('/api/guided/assessment/submit',{method:'POST',body:JSON.stringify({project_id:Number($('#assessmentProject').value),answers:state.assessment})});const selectedProject=Number($('#assessmentProject').value);state.projectId=selectedProject;closeModal();modal(`<div class="result-score">${r.score}<small>/100</small></div><span class="badge green">${esc(r.band)}</span><h2>Hasil readiness Anda</h2><p>${esc(r.disclaimer)}</p><h3>Prioritas perbaikan</h3>${r.recommendations.map(x=>`<div class="recommendation"><b>${esc(x.priority)} · ${esc(x.area)}</b><p>${esc(x.action)}</p></div>`).join('')||'<p>Fondasi awal cukup baik. Lanjutkan validasi bukti dan ketentuan pasar tujuan.</p>'}<button class="btn btn-primary" onclick="closeModal();go('checklist')">Bangun roadmap tindakan</button>`);}catch(e){toast(e.message,true)}}
async function checklistPage(){const ps=await api('/api/projects');if(!ps.length)return `${title('Roadmap tindakan','Roadmap dibuat berdasarkan tahapan ekspor dan keluaran yang perlu dibuktikan.')}<button class="btn btn-primary" onclick="go('projects')">Buat proyek</button>`;return `${title('Roadmap tindakan','Bukan sekadar centang: pahami alasan, cara mengerjakan, dan bukti yang harus dihasilkan.')}<div class="toolbar"><label>Proyek</label><select id="roadmapProject" class="compact-select">${ps.map(p=>`<option value="${p.id}" ${state.projectId===p.id?'selected':''}>${esc(p.name)}</option>`).join('')}</select></div><div id="roadmapContent"></div>`}
async function openRoadmap(id){state.projectId=id;state.page='checklist';await render()}
async function loadRoadmap(){const id=Number($('#roadmapProject')?.value||state.projectId);state.projectId=id;const r=await api('/api/guided/roadmap/'+id);$('#roadmapContent').innerHTML=`<div class="panel roadmap-summary"><div><b>${esc(r.project.name)}</b><p>${r.progress}% tahapan selesai</p></div><div class="progress"><span style="width:${r.progress}%"></span></div></div><div class="roadmap-list">${r.items.map((x,i)=>`<article class="roadmap-item"><div class="roadmap-number">${String(i+1).padStart(2,'0')}</div><div class="roadmap-body"><div class="roadmap-meta"><span class="badge">${esc(x.stage)}</span><span class="badge ${x.status==='done'?'green':x.status==='blocked'?'red':''}">${statusLabel(x.status)}</span></div><h3>${esc(x.title)}</h3><p>${esc(x.why)}</p><details><summary>Panduan pelaksanaan & bukti keluaran</summary><p>${esc(x.how)}</p><div class="notice"><b>Bukti yang diharapkan:</b> ${esc(x.evidence)}</div></details><div class="roadmap-controls"><select onchange="setRoadmapStatus(${x.id},this.value)"><option value="not_started" ${x.status==='not_started'?'selected':''}>Belum dimulai</option><option value="in_progress" ${x.status==='in_progress'?'selected':''}>Sedang dikerjakan</option><option value="blocked" ${x.status==='blocked'?'selected':''}>Terhambat</option><option value="done" ${x.status==='done'?'selected':''}>Selesai</option></select></div></div></article>`).join('')}</div>`}
function statusLabel(s){return ({not_started:'Belum dimulai',in_progress:'Sedang dikerjakan',blocked:'Terhambat',done:'Selesai'})[s]||s}
async function setRoadmapStatus(id,status){try{await api('/api/guided/roadmap/items/'+id,{method:'PATCH',body:JSON.stringify({status})});loadRoadmap()}catch(e){toast(e.message,true)}}
async function countriesPage(){return `${title('Country intelligence','Pilih pasar dan kategori produk untuk melihat ringkasan persyaratan serta sumber resmi.')}<div class="intel-layout"><div class="panel"><div class="field"><label>Negara tujuan</label><select id="countrySelect"><option value="SG">Singapura</option><option value="MY">Malaysia</option><option value="JP">Jepang</option><option value="AU">Australia</option><option value="NL">Belanda</option><option value="US">Amerika Serikat</option></select></div><div class="field"><label>Kategori produk</label><select id="countryCategory"><option value="general">Umum / manufaktur</option><option value="fnb">Makanan & minuman</option><option value="agriculture">Pertanian</option><option value="wood">Kayu & furnitur</option></select></div><button class="btn btn-primary" onclick="loadCountryIntel()">Tampilkan intelijen</button><p class="tiny muted">Akun Free: Singapura dan Malaysia. Premium: seluruh negara yang tersedia.</p></div><div id="countryResult" class="panel"><div class="empty">Pilih negara dan kategori produk untuk memuat ringkasan.</div></div></div>`}
async function loadCountryIntel(){const code=$('#countrySelect').value,cat=$('#countryCategory').value;try{const d=await api(`/api/country-intel?code=${code}&product_category=${cat}`);$('#countryResult').innerHTML=`<div class="country-heading"><span class="badge green">${esc(d.region)}</span><h2>${esc(d.name)}</h2><p class="muted">Mata uang: ${esc(d.currency)}</p></div><h3>Gambaran pasar</h3><p>${esc(d.market)}</p><h3>Prosedur kepabeanan</h3><p>${esc(d.customs)}</p><h3>Catatan sektoral</h3><div class="guide-box"><p>${esc(d.sector_guidance)}</p></div><h3>Sumber otoritas & referensi</h3><div class="source-list">${d.sources.map(s=>`<a href="${esc(s.url)}" target="_blank" rel="noopener"><b>${esc(s.name)}</b><span>${esc(s.url)}</span></a>`).join('')}</div><div class="notice warn">${esc(d.data_note)}</div>`}catch(e){toast(e.message,true)}}
async function shippingPage(){return `${title('Shipping & Incoterms decision','Jawab beberapa pertanyaan operasional untuk memperoleh rekomendasi awal, pembagian tanggung jawab, dan wording kontrak.')}<div class="shipping-layout"><div class="panel"><form id="shippingForm"><div class="field"><label>Moda pengiriman</label><select name="mode"><option value="sea">Laut</option><option value="air">Udara</option><option value="road">Darat</option><option value="multimodal">Multimoda</option></select></div><div class="field"><label>Jenis pengiriman</label><select name="container"><option value="true">Kontainer / cargo diserahkan ke terminal</option><option value="false">Breakbulk / general cargo</option></select></div><div class="field"><label>Seberapa besar kontrol yang ingin diambil seller?</label><select name="seller_control"><option value="low">Rendah — fokus menyiapkan barang dan ekspor</option><option value="medium" selected>Menengah — bisa mengatur angkutan utama</option><option value="high">Tinggi — mengatur sampai tujuan</option></select></div><div class="field"><label>Apakah buyer siap menjadi importir dan mengurus clearance?</label><select name="buyer_import"><option value="true">Ya, buyer/importir siap</option><option value="false">Belum / seller diminta mengurus</option></select></div><div class="field"><label>Tempat/pelabuhan tujuan (harus spesifik)</label><input name="destination" placeholder="Contoh: Port of Singapore, Singapore" required></div><button class="btn btn-primary">Analisis opsi Incoterms</button></form></div><div id="shippingResult" class="panel"><div class="empty">Hasil rekomendasi dan pembagian tanggung jawab akan muncul di sini.</div></div></div>`}
async function runShipping(e){e.preventDefault();const fd=Object.fromEntries(new FormData(e.target));fd.container=fd.container==='true';fd.buyer_import=fd.buyer_import==='true';try{const r=await api('/api/shipping/recommend',{method:'POST',body:JSON.stringify(fd)});state.shippingResult=r;const t=r.term;$('#shippingResult').innerHTML=`<span class="badge green">REKOMENDASI AWAL</span><div class="incoterm-code">${r.recommended}</div><h2>${esc(t.name)}</h2><p>${esc(r.reason)}</p><div class="notice"><b>Contract wording:</b><br>${esc(r.contract_wording)}</div><div class="responsibility-grid"><div><b>Seller</b><p>${esc(t.seller)}</p></div><div><b>Buyer</b><p>${esc(t.buyer)}</p></div><div><b>Perpindahan risiko</b><p>${esc(t.risk)}</p></div><div><b>Asuransi</b><p>${esc(t.insurance)}</p></div></div><h3>Catatan penting</h3><p>${esc(t.note)}</p><div class="notice warn">${esc(r.warning)}</div><button class="btn btn-outline" onclick="showIncotermsTable()">Bandingkan 11 Incoterms</button>`}catch(x){toast(x.message,true)}}
async function showIncotermsTable(){try{const d=await api('/api/guides/incoterms/full');modal(`<h3>Perbandingan Incoterms 2020</h3><div class="table-wrap"><table><thead><tr><th>Kode</th><th>Nama</th><th>Moda</th><th>Catatan</th></tr></thead><tbody>${Object.entries(d).map(([k,v])=>`<tr><td><b>${k}</b></td><td>${esc(v.name)}</td><td>${esc(v.mode)}</td><td>${esc(v.note)}</td></tr>`).join('')}</tbody></table></div><p class="tiny muted">Gunakan publikasi resmi ICC untuk interpretasi lengkap dan wording kontrak.</p>`)}catch(e){toast(e.message,true)}}
async function documentsPage(){const [docs,ps]=await Promise.all([api('/api/documents'),api('/api/projects')]);return `${title('Document center','Unggah dokumen, pilih tipenya, lalu jalankan pemeriksaan rule engine untuk indikator kelengkapan awal.')}<div class="panel"><form id="docForm" class="upload-grid"><div class="field"><label>File</label><input type="file" name="file" accept=".pdf,.docx,.txt,.csv,.xlsx,.jpg,.jpeg,.png" required></div><div class="field"><label>Tipe dokumen</label><select name="doc_type"><option value="commercial_invoice">Commercial Invoice</option><option value="packing_list">Packing List</option><option value="certificate_origin">Certificate of Origin / SKA</option><option value="bill_lading">Bill of Lading / AWB</option><option value="health_certificate">Health Certificate</option><option value="phytosanitary">Phytosanitary Certificate</option><option value="fumigation">Fumigation Certificate</option><option value="product_spec">Product Specification</option><option value="export_permit">Export Permit</option><option value="general">Dokumen umum</option></select></div><div class="field"><label>Proyek terkait</label><select name="project_id"><option value="">Tidak terkait proyek</option>${ps.map(p=>`<option value="${p.id}">${esc(p.name)}</option>`).join('')}</select></div><div class="field"><label>Negara tujuan</label><select name="destination"><option value="">Belum ditentukan</option><option>Singapura</option><option>Malaysia</option><option>Jepang</option><option>Australia</option><option>Belanda</option><option>Amerika Serikat</option></select></div><div class="field"><label>Kategori produk</label><select name="product_category"><option value="general">Umum</option><option value="fnb">Makanan & minuman</option><option value="agriculture">Pertanian</option><option value="wood">Kayu & furnitur</option></select></div><button class="btn btn-primary upload-button">Upload & periksa dokumen</button></form></div><div id="docAnalysis"></div><div class="panel" style="margin-top:18px"><h3>Dokumen tersimpan</h3><div class="table-wrap"><table><thead><tr><th>Nama</th><th>Ukuran</th><th>Hasil rule engine</th><th>Tanggal</th><th>Aksi</th></tr></thead><tbody>${docs.map(d=>`<tr><td>${esc(d.filename)}</td><td>${(d.size/1024).toFixed(1)} KB</td><td><span class="badge ${d.analysis?.status==='preliminary_pass'?'green':'amber'}">${esc(d.analysis?.status_label||'Belum dianalisis')}</span></td><td>${new Date(d.created_at).toLocaleDateString('id-ID')}</td><td><a href="${d.url}" target="_blank">Unduh</a> · <button class="text-button" onclick="showDocAnalysis(${d.id})">Detail</button></td></tr>`).join('')||'<tr><td colspan="5" class="empty">Belum ada dokumen.</td></tr>'}</tbody></table></div></div>`}
async function uploadDoc(e){e.preventDefault();const fd=new FormData(e.target);if(!fd.get('project_id'))fd.delete('project_id');try{const r=await api('/api/documents',{method:'POST',body:fd});showAnalysisResult(r.analysis);toast(r.message);setTimeout(()=>render(),500)}catch(x){toast(x.message,true)}}
function showAnalysisResult(a){$('#docAnalysis').innerHTML=`<div class="panel analysis-panel"><div class="analysis-head"><div><span class="badge ${a.status==='preliminary_pass'?'green':'amber'}">${esc(a.status_label)}</span><h2>${esc(a.document_type)}</h2></div><span class="tiny muted">Rule engine · preliminary</span></div><p>${esc(a.guidance)}</p><div class="check-results">${a.checks.map(c=>`<div class="check-result"><span class="badge ${c.status==='pass'?'green':c.status==='manual'?'amber':'red'}">${c.status==='pass'?'Ditemukan':c.status==='manual'?'Manual':'Review'}</span><b>${esc(c.item)}</b><small>${esc(c.detail)}</small></div>`).join('')}</div>${a.missing?.length?`<div class="notice warn">Indikator yang belum ditemukan: ${a.missing.map(esc).join(', ')}</div>`:''}<div class="notice warn">${esc(a.limitations)}</div></div>`}
async function showDocAnalysis(id){const docs=await api('/api/documents');const d=docs.find(x=>x.id===id);if(d?.analysis){modal(`<h3>Hasil pemeriksaan: ${esc(d.filename)}</h3><p>${esc(d.analysis.status_label)}</p>${d.analysis.checks.map(c=>`<div class="check-result"><b>${esc(c.item)}</b><small>${esc(c.detail)}</small></div>`).join('')}<div class="notice warn">${esc(d.analysis.limitations)}</div>`)}else toast('Laporan analisis tidak tersedia.',true)}
async function calculatorPage(){const ps=await api('/api/projects'),costs=await api('/api/cost-estimates');return `${title('Export cost calculator','Masukkan komponen biaya untuk menghitung estimasi biaya ekspor per pengiriman.')}<div class="content-grid"><div class="panel"><form id="costForm"><div class="field"><label>Nama estimasi</label><input name="title" value="Estimasi pengiriman ekspor" required></div><div class="field"><label>Proyek</label><select name="project_id"><option value="">Tidak terkait</option>${ps.map(p=>`<option value="${p.id}">${esc(p.name)}</option>`).join('')}</select></div><div class="form-grid">${['production','packaging','inland','freight','insurance','customs','other'].map(k=>`<div class="field"><label>${({production:'Biaya produk',packaging:'Kemasan',inland:'Transport domestik',freight:'Freight internasional',insurance:'Asuransi',customs:'Bea & pajak estimasi',other:'Biaya lain'})[k]}</label><input name="${k}" type="number" min="0" step="1000" value="0"></div>`).join('')}</div><button class="btn btn-primary">Hitung dan simpan estimasi</button></form></div><div class="panel"><h3>Riwayat estimasi</h3>${costs.map(c=>`<div class="history-row"><b>${esc(c.title)}</b><strong>${money(c.total)}</strong><small>${new Date(c.created_at).toLocaleDateString('id-ID')}</small></div>`).join('')||'<p class="muted">Belum ada estimasi.</p>'}<div class="notice warn">Perhitungan ini tidak otomatis mengambil tarif bea, pajak, kurs, atau freight pasar. Masukkan angka berdasarkan quotation dan sumber yang sudah diverifikasi.</div></div></div>`}
async function submitCost(e){e.preventDefault();let d=Object.fromEntries(new FormData(e.target));['production','packaging','inland','freight','insurance','customs','other'].forEach(k=>d[k]=Number(d[k]||0));d.project_id=d.project_id?Number(d.project_id):null;try{let r=await api('/api/cost-estimates',{method:'POST',body:JSON.stringify(d)});toast('Estimasi tersimpan: '+money(r.total));render()}catch(x){toast(x.message,true)}}
async function subscriptionPage(){const [p,pay]=await Promise.all([api('/api/plans'),api('/api/payments/mine')]);return `${title('Subscription','Kelola akses dan riwayat pembayaran.')}<div class="pricing-grid"><div class="price-card"><span class="badge">CURRENT · ${state.user.plan.toUpperCase()}</span><h2>Free</h2><p>1 proyek, 1 assessment, 2 negara, 1 kalkulasi per bulan.</p></div><div class="price-card popular"><span class="badge green">PREMIUM</span><h2>${money(p.premium.monthly)} / bulan</h2><p>10 proyek, seluruh negara, assessment dan kalkulasi tanpa batas.</p><button class="btn btn-primary" onclick="checkout('monthly')">Upgrade bulanan</button></div><div class="price-card"><h2>${money(p.premium.yearly)} / tahun</h2><p>Semua fitur Premium.</p><button class="btn btn-dark" onclick="checkout('yearly')">Upgrade tahunan</button></div></div><div class="panel" style="margin-top:18px"><h3>Riwayat pembayaran</h3>${pay.map(x=>`<p>${esc(x.invoice)} · ${money(x.amount)} · ${esc(x.status)}</p>`).join('')||'<p class="muted">Belum ada pembayaran.</p>'}</div>`}
async function checkout(period){try{const p=await api('/api/payments/create',{method:'POST',body:JSON.stringify({period})});modal(`<h3>Upgrade Premium</h3><div class="notice warn">Invoice ${esc(p.invoice)} · ${money(p.amount)}. Akses aktif setelah diverifikasi admin.</div><p>QRIS dapat diatur admin melalui Pengaturan. Untuk demo lokal, admin dapat mengunggah QRIS milik merchant.</p><form id="proofForm"><input type="file" name="file" accept=".jpg,.jpeg,.png,.pdf" required><button class="btn btn-primary" style="margin-top:12px">Kirim bukti</button></form>`);$('#proofForm').onsubmit=async e=>{e.preventDefault();try{await api(`/api/payments/${p.id}/proof`,{method:'POST',body:new FormData(e.target)});closeModal();toast('Bukti terkirim.');render()}catch(x){toast(x.message,true)}}}catch(e){toast(e.message,true)}}
async function adminDashboard() {
    const d = await api('/api/admin/summary');

    return `
        ${title(
            'Admin overview',
            'Ringkasan penggunaan dan transaksi platform.'
        )}

        <div class="stats-grid">
            ${stat('Pengguna', d.users, 'Akun terdaftar')}
            ${stat('Premium aktif', d.premium, 'Subscription')}
            ${stat('Menunggu verifikasi', d.pending_payments, 'Pembayaran')}
            ${stat('Pendapatan disetujui', money(d.approved_revenue), 'Total')}
        </div>
    `;
}
async function adminPayments(){const rows=await api('/api/admin/payments');return `${title('Verifikasi pembayaran','Periksa bukti dan cocokkan dengan catatan merchant/settlement QRIS.')}<div class="panel table-wrap"><table><thead><tr><th>Invoice</th><th>User</th><th>Jumlah</th><th>Bukti</th><th>Status</th><th>Aksi</th></tr></thead><tbody>${rows.map(p=>`<tr><td>${esc(p.invoice)}</td><td>${esc(p.name)}<br>${esc(p.user)}</td><td>${money(p.amount)}</td><td>${p.proof?`<a href="/uploads/${encodeURIComponent(p.proof)}" target="_blank">Lihat</a>`:'Belum ada'}</td><td>${esc(p.status)}</td><td>${p.status==='pending'&&p.proof?`<button class="btn btn-primary btn-small" onclick="reviewPayment(${p.id},'approve')">Setujui</button> <button class="btn btn-danger btn-small" onclick="reviewPayment(${p.id},'reject')">Tolak</button>`:'—'}</td></tr>`).join('')}</tbody></table></div>`}
async function reviewPayment(id,action){let note=prompt('Catatan verifikasi:','');if(note===null)return;try{await api(`/api/admin/payments/${id}/review`,{method:'POST',body:JSON.stringify({action,note})});render()}catch(e){toast(e.message,true)}}
async function adminUsers(){const users=await api('/api/admin/users');return `${title('Pengguna','Pantau akun dan paket pengguna.')}<div class="panel table-wrap"><table><thead><tr><th>Nama</th><th>Email</th><th>Role</th><th>Plan</th><th>Terdaftar</th></tr></thead><tbody>${users.map(u=>`<tr><td>${esc(u.name)}</td><td>${esc(u.email)}</td><td>${esc(u.role)}</td><td>${esc(u.plan)}</td><td>${new Date(u.created_at).toLocaleDateString('id-ID')}</td></tr>`).join('')}</tbody></table></div>`}
async function adminSettings(){const s=await api('/api/admin/settings');return `${title('Pengaturan','Atur harga dan QRIS merchant.')}<div class="content-grid"><div class="panel"><form id="priceForm"><div class="field"><label>Harga bulanan</label><input name="monthly" type="number" value="${s.monthly}"></div><div class="field"><label>Harga tahunan</label><input name="yearly" type="number" value="${s.yearly}"></div><button class="btn btn-primary">Simpan</button></form></div><div class="panel"><h3>QRIS</h3>${s.qris_url?`<img class="qris" src="${s.qris_url}">`:'<p>QRIS belum diunggah.</p>'}<form id="qrisForm"><input type="file" name="file" accept="image/*" required><button class="btn btn-primary" style="margin-top:12px">Upload QRIS</button></form></div></div>`}
async function authSubmit(e){e.preventDefault();const d=Object.fromEntries(new FormData(e.target));try{const r=await api('/api/auth/'+(state.page==='login'?'login':'register'),{method:'POST',body:JSON.stringify(d)});state.token=r.token;state.user=r.user;localStorage.setItem('expando_token',r.token);state.page=r.user.role==='admin'?'admin-dashboard':'dashboard';toast('Berhasil masuk.');render()}catch(x){toast(x.message,true)}}
function logout(){state.token=null;state.user=null;localStorage.removeItem('expando_token');state.page='landing';render()}
async function render(){const root=$('#app');try{if(state.page==='landing'){root.innerHTML=landing();return}if(['login','register'].includes(state.page)){root.innerHTML=authPage(state.page);$('#authForm').onsubmit=authSubmit;return}if(!state.token){state.page='landing';root.innerHTML=landing();return}if(!state.user)state.user=await api('/api/auth/me');if(state.user.role==='admin'&&!state.page.startsWith('admin-'))state.page='admin-dashboard';if(state.user.role!=='admin'&&state.page.startsWith('admin-'))state.page='dashboard';let c='';switch(state.page){case'dashboard':c=await dashboard();break;case'projects':c=await projectsPage();break;case'readiness':c=await readinessPage();break;case'checklist':c=await checklistPage();break;case'countries':c=await countriesPage();break;case'shipping':c=await shippingPage();break;case'documents':c=await documentsPage();break;case'calculator':c=await calculatorPage();break;case'subscription':c=await subscriptionPage();break;case'admin-dashboard':c=await adminDashboard();break;case'admin-payments':c=await adminPayments();break;case'admin-users':c=await adminUsers();break;case'admin-settings':c=await adminSettings();break;default:state.page='dashboard';c=await dashboard()}root.innerHTML=shell(c);if($('#projectForm'))$('#projectForm').onsubmit; if($('#assessmentWizard'))renderAssessmentStep();if($('#roadmapProject')){$('#roadmapProject').onchange=loadRoadmap;loadRoadmap()}if($('#countrySelect')){if(state.user.plan==='free'){$('#countrySelect').innerHTML='<option value="SG">Singapura</option><option value="MY">Malaysia</option>'}$('#countrySelect').value=state.country;$('#countryCategory').value=state.countryCategory}if($('#shippingForm'))$('#shippingForm').onsubmit=runShipping;if($('#docForm'))$('#docForm').onsubmit=uploadDoc;if($('#costForm'))$('#costForm').onsubmit=submitCost;if($('#priceForm'))$('#priceForm').onsubmit=async e=>{e.preventDefault();let d=Object.fromEntries(new FormData(e.target));try{await api('/api/admin/settings/prices',{method:'POST',body:JSON.stringify(d)});toast('Harga diperbarui')}catch(x){toast(x.message,true)}};if($('#qrisForm'))$('#qrisForm').onsubmit=async e=>{e.preventDefault();try{const r=await api('/api/admin/settings/qris',{method:'POST',body:new FormData(e.target)});toast(r.message);render()}catch(x){toast(x.message,true)}}}catch(e){if(e.status===401){state.token=null;state.user=null;localStorage.removeItem('expando_token');state.page='landing';root.innerHTML=landing();return}root.innerHTML=`<div class="container" style="padding:60px"><h2>Terjadi kesalahan</h2><p>${esc(e.message)}</p><button class="btn btn-primary" onclick="render()">Coba lagi</button></div>`}}
window.addEventListener('hashchange',()=>{if(location.hash==='#pricing')$('#pricing')?.scrollIntoView()});render();
