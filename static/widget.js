(async function(){
  const tag=document.currentScript; const id=new URL(tag.src).searchParams.get('id');
  if(!id)return; const base=new URL(tag.src).origin;
  const cfg=await fetch(`${base}/widgets/${id}/config`).then(r=>r.json());
  const host=document.createElement('div'); host.id=`flyrank-widget-${id}`;
  const title=document.createElement('h3'); title.textContent=cfg.title; host.appendChild(title);
  const desc=document.createElement('p'); desc.textContent=cfg.description||''; host.appendChild(desc);
  const form=document.createElement('form');
  cfg.form_fields.forEach(name=>{const i=document.createElement('input');i.name=name;i.placeholder=name;i.required=true;form.appendChild(i);});
  const hp=document.createElement('input'); hp.name='hp'; hp.tabIndex=-1; hp.autocomplete='off'; hp.style.display='none'; form.appendChild(hp);
  const b=document.createElement('button');b.type='submit';b.textContent=cfg.button_text;form.appendChild(b);host.appendChild(form);tag.parentNode.insertBefore(host,tag.nextSibling);
  form.addEventListener('submit',async e=>{e.preventDefault();const data={};cfg.form_fields.forEach(n=>data[n]=form.elements[n].value);const res=await fetch(`${base}/submissions`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({widget_id:id,data,website_origin:location.origin,hp:form.elements.hp.value})}); if(res.ok){form.reset();b.textContent='Submitted';}else{b.textContent='Try again';}});
})();
