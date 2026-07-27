(function(){
  // 简单工具
  const $ = sel => document.querySelector(sel);
  const log = (el, msg) => { el.textContent = (typeof msg==='string'? msg : JSON.stringify(msg,null,2)); };
  const val = (sel) => { const el = $(sel); return el ? el.value.trim() : ''; };
  const toList = (s) => (s||'').trim().split(/[\s,，]+/).filter(Boolean);

  // 选项卡
  document.querySelectorAll('.tab').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
      btn.classList.add('active');
      $('#'+btn.dataset.tab).classList.add('active');
    });
  });

  // 上传通用
  async function uploadFile(input){
    if(!input.files || input.files.length===0) return null;
    const file = input.files[0];
    const fd = new FormData();
    fd.append('file', file, file.name || 'upload.bin');
    const r = await fetch('/upload',{method:'POST', body: fd});
    const js = await r.json();
    if(!r.ok) throw new Error(js.error||'上传失败');
    return js.path;
  }

  async function pollExtractJob(jobId, logEl){
    async function tick(){
      try{
        const r = await fetch('/jobs/'+encodeURIComponent(jobId));
        const js = await r.json();
        if(!r.ok) throw new Error(js.error||'任务状态获取失败');
        log(logEl, js);
        if(js.status === 'running'){
          setTimeout(tick, 3000);
        }
      }catch(e){
        log(logEl, '错误: '+e.message);
      }
    }
    tick();
  }

  // 抽取
  $('#btn-extract').addEventListener('click', async ()=>{
    const logEl = $('#ext-log'); log(logEl,'处理中...');
    try{
      let iclPath = $('#ext-icl').value.trim();
      const iclFile = $('#ext-icl-file');
      if(!iclPath && iclFile.files.length){
        iclPath = await uploadFile(iclFile);
      }
      const payload = {
        elsevier_key: $('#ext-els-key').value.trim(),
        elsevier_insttoken: val('#ext-insttoken')||null,
        keyword: $('#ext-keyword').value.trim(),
        count: parseInt($('#ext-count').value,10)||20,
        workers: parseInt(val('#ext-workers'),10)||1,
        out: val('#ext-out')||null,
        resume: $('#ext-resume') ? $('#ext-resume').checked : true,
        background: $('#ext-background') ? $('#ext-background').checked : true,
        chunk_chars: parseInt(val('#ext-chunk-chars'),10)||14000,
        chunk_overlap: parseInt(val('#ext-chunk-overlap'),10)||1000,
        max_chunks: parseInt(val('#ext-max-chunks'),10)||8,
        metrics: toList($('#ext-metrics').value),
        icl_path: iclPath||null,
        schema_path: val('#ext-schema')||null,
        icl_bank_path: val('#ext-icl-bank')||null,
        icl_top_k: parseInt(val('#ext-icl-top-k'),10)||3,
        domain: val('#ext-domain')||null,
        llm_key: $('#ext-llm-key').value.trim()||null,
        llm_base: $('#ext-llm-base').value.trim()||null,
        llm_model: $('#ext-llm-model').value.trim()||null
      };
      const r = await fetch('/extract',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      const js = await r.json();
      if(!r.ok) throw new Error(js.error||'抽取失败');
      if(js.job_id){
        log(logEl, {message:'后台抽取已启动', job_id: js.job_id, status: js.status});
        pollExtractJob(js.job_id, logEl);
      }else{
        log(logEl, {message:'抽取完成', output_csv: js.output_csv});
      }
    }catch(e){ log(logEl, '错误: '+e.message); }
  });

  // 清洗
  $('#cln-file').addEventListener('change', async (e)=>{
    try{
      const p = await uploadFile(e.target);
      if(p) $('#cln-csv').value = p;
    }catch(err){ alert(err.message); }
  });
  $('#btn-clean').addEventListener('click', async ()=>{
    const logEl=$('#cln-log'); log(logEl,'处理中...');
    try{
      const payload = {
        csv_path: $('#cln-csv').value.trim(),
        grouping: toList($('#cln-grouping').value),
        keys: toList($('#cln-keys').value),
        required: toList($('#cln-required').value),
        nonzero: toList($('#cln-nonzero').value)
      };
      const r = await fetch('/clean',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      const js = await r.json();
      if(!r.ok) throw new Error(js.error||'清洗失败');
      log(logEl, {message:'清洗完成', rows: js.rows, output_csv: js.output_csv, entity_map: js.entity_map, entity_summary: js.entity_summary});
    }catch(e){ log(logEl, '错误: '+e.message); }
  });

  // 插补评估
  $('#btn-imp-eval').addEventListener('click', async ()=>{
    $('#imp-summary').textContent='处理中...'; $('#imp-table').innerHTML='';
    try{
      const payload = {
        csv_path: $('#imp-csv').value.trim(),
        use_columns: toList($('#imp-cols').value),
        llm_key: $('#imp-llm-key').value.trim()||null,
        llm_base: $('#imp-llm-base').value.trim()||null,
        llm_model: $('#imp-llm-model').value.trim()||null,
        mask_frac: parseFloat($('#imp-mask').value)||0.1,
        repeats: parseInt($('#imp-repeats').value,10)||3,
        seed: parseInt($('#imp-seed').value,10)||42
      };
      const r = await fetch('/impute/evaluate',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      const js = await r.json();
      if(!r.ok) throw new Error(js.error||'评估失败');
      $('#imp-summary').textContent = `缺失: mean=${js.missingness.mean.toFixed(4)} median=${js.missingness.median.toFixed(4)} p90=${js.missingness.p90.toFixed(4)}; 摘要CSV=${js.summary_csv}`;
      const rows = js.report||[];
      const cols = ['method','params','overall_nrmse','score'];
      const table = document.createElement('table');
      const thead = document.createElement('thead');
      thead.innerHTML = '<tr>'+cols.map(c=>`<th>${c}</th>`).join('')+'</tr>';
      table.appendChild(thead);
      const tbody = document.createElement('tbody');
      rows.forEach(r=>{
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${r.method}</td><td><code>${JSON.stringify(r.params)}</code></td><td>${r.overall_nrmse?.toFixed?.(6)??r.overall_nrmse}</td><td>${r.score?.toFixed?.(6)??r.score}</td>`;
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      $('#imp-table').appendChild(table);
    }catch(e){ $('#imp-summary').textContent='错误: '+e.message; }
  });

  // 应用插补
  $('#btn-imp-apply').addEventListener('click', async ()=>{
    const logEl = $('#imp-log'); logEl.textContent='处理中...';
    try{
      const payload = {
        csv_path: $('#imp-csv').value.trim(),
        method: $('#imp-apply-method').value,
        params: $('#imp-apply-params').value.trim()||'{}'
      };
      const r = await fetch('/impute/apply',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      const js = await r.json();
      if(!r.ok) throw new Error(js.error||'应用失败');
      log(logEl, {message:'完成', output_csv: js.output_csv});
    }catch(e){ log(logEl, '错误: '+e.message); }
  });

  // 优化建议
  $('#btn-opt').addEventListener('click', async ()=>{
    $('#opt-log').textContent='处理中...'; $('#opt-table').innerHTML='';
    try{
      const cols = {
        T: $('#opt-col-T').value.trim(), P: $('#opt-col-P').value.trim(), conv: $('#opt-col-conv').value.trim(), sel: $('#opt-col-sel').value.trim(), yld: $('#opt-col-yld').value.trim()
      };
      const payload = {
        csv_path: $('#opt-csv').value.trim(), columns: cols,
        top_k: parseInt($('#opt-topk').value,10)||5,
        n_candidates: parseInt($('#opt-nc').value,10)||2000,
        objective: $('#opt-objective').value.trim()||null,
        weights: { sel: parseFloat($('#opt-w-sel').value)||0, conv: parseFloat($('#opt-w-conv').value)||0, yld: parseFloat($('#opt-w-yld').value)||0 }
      };
      const r = await fetch('/suggest',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      const js = await r.json();
      if(!r.ok) throw new Error(js.error||'优化失败');
      const rows = js.suggestions||[];
      if(!rows.length){ $('#opt-log').textContent='无候选结果'; return; }
      const colsKeys = Object.keys(rows[0]);
      const table = document.createElement('table');
      const thead = document.createElement('thead');
      thead.innerHTML='<tr>'+colsKeys.map(k=>`<th>${k}</th>`).join('')+'</tr>';
      table.appendChild(thead);
      const tbody = document.createElement('tbody');
      rows.forEach(rw=>{
        const tr = document.createElement('tr');
        tr.innerHTML = colsKeys.map(k=>`<td>${rw[k]}</td>`).join('');
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      $('#opt-table').appendChild(table);
      $('#opt-log').textContent='完成';
    }catch(e){ $('#opt-log').textContent='错误: '+e.message; }
  });

  // 纠错：查看记录
  $('#cor-file').addEventListener('change', async (e)=>{
    try{
      const p = await uploadFile(e.target);
      if(p) $('#cor-csv').value = p; //加一些测试行，文件成功读取时打印一些输出
    }catch(err){ alert(err.message); }
  });

  document.getElementById('btn-cor-view').addEventListener('click', async ()=>{
    const csv = document.getElementById('cor-csv').value.trim();
    const idx = parseInt(document.getElementById('cor-row-index').value,10)||0;
    const logEl = document.getElementById('cor-view');
    logEl.textContent='处理中...';
    try{
      const r = await fetch('/record',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({csv_path: csv, row_index: idx})});
      const js = await r.json();
      if(!r.ok) throw new Error(js.error||'查看失败');
      logEl.textContent = JSON.stringify(js, null, 2);
      // 如果有 DOI 自动填入
      const row = js.row || {};
      if(row.doi){ document.getElementById('cor-doi').value = String(row.doi); }
    }catch(e){ logEl.textContent = '错误: '+e.message; }
  });

  // 纠错：提交修订
  document.getElementById('btn-cor-apply').addEventListener('click', async ()=>{
    const csv = document.getElementById('cor-csv').value.trim();
    const doi = document.getElementById('cor-doi').value.trim();
    const metric = document.getElementById('cor-metric').value.trim();
    const value = document.getElementById('cor-value').value.trim();
    const unit = document.getElementById('cor-unit').value.trim();
    const note = document.getElementById('cor-note').value.trim();
    const logEl = document.getElementById('cor-log');
    logEl.textContent='处理中...';
    try{
      const payload = {csv_path: csv, doi: doi||null, metric, value, unit, note};
      const r = await fetch('/correct',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const js = await r.json();
      if(!r.ok) throw new Error(js.error||'修订失败');
      logEl.textContent = '修订已保存: ' + JSON.stringify(payload);
    }catch(e){ logEl.textContent = '错误: '+e.message; }
  });
})();
