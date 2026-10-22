fetch('data/tools.json').then(r=>r.json()).then(d=>{
 const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
 const lb=document.getElementById('lb');
 if(lb&&!lb.children.length){const b=d.leaderboards[0];document.getElementById('lbnote').textContent=b.note;
  lb.innerHTML=b.tools.map(t=>`<tr><td><a href="${esc(t.url)}" rel="noopener" target="_blank"><b>${esc(t.name)}</b></a><div class="mut">${esc(t.description)}</div>${t.referral_url?`<div class="sm"><a href="${esc(t.referral_url)}" rel="sponsored noopener" target="_blank">Try ${esc(t.name)} (referral)</a></div><div class="mut sm">${esc(t.referral_note||'')}</div>`:''}</td><td class="${t.free_tier==='Yes'?'yes':'no'}">${esc(t.free_tier)}</td><td class="hide-sm mut">${esc(t.pricing)}</td><td class="mut">Not yet tested</td></tr>`).join('');}
 const nw=document.getElementById('new');
 if(nw){const cut=new Date(new Date(d.updated+'T00:00:00Z')-6*864e5).toISOString().slice(0,10);const nl=d.new_this_week.filter(t=>String(t.found||'')>=cut).sort((a,b)=>String(b.found||'').localeCompare(String(a.found||'')));nw.innerHTML=nl.length?nl.map(t=>{
   const found=t.found?`<div class="mut sm">Found ${esc(t.found)}</div>`:'';
   return `<div class="card"><a href="${esc(t.url)}" rel="noopener" target="_blank"><b>${esc(t.name)}</b></a><div class="mut">${esc(t.description)}</div>${found}</div>`;
 }).join(''):'<p class="mut">Our discovery agents start scanning launches this week. New tools will appear here, with the date we found them.</p>';}
 const u=document.getElementById('upd');if(u)u.textContent=d.updated;
});
