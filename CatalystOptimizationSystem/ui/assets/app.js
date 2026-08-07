(function () {
  const $ = (sel) => document.querySelector(sel);
  const log = (el, msg) => {
    if (!el) return;
    el.textContent = typeof msg === "string" ? msg : JSON.stringify(msg, null, 2);
  };
  const val = (sel) => {
    const el = $(sel);
    return el ? el.value.trim() : "";
  };
  const checked = (sel) => {
    const el = $(sel);
    return el ? Boolean(el.checked) : false;
  };
  const toList = (s) => (s || "").trim().split(/[\s,;]+/).filter(Boolean);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));

  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const panel = $("#" + btn.dataset.tab);
      if (panel) panel.classList.add("active");
    });
  });

  async function postJson(url, payload) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const js = await r.json();
    if (!r.ok) throw new Error(js.error || "request failed");
    return js;
  }

  async function uploadFile(input) {
    if (!input || !input.files || input.files.length === 0) return null;
    const file = input.files[0];
    const fd = new FormData();
    fd.append("file", file, file.name || "upload.bin");
    const r = await fetch("/upload", { method: "POST", body: fd });
    const js = await r.json();
    if (!r.ok) throw new Error(js.error || "upload failed");
    return js.path;
  }

  async function pollExtractJob(jobId, logEl) {
    async function tick() {
      try {
        const r = await fetch("/jobs/" + encodeURIComponent(jobId));
        const js = await r.json();
        if (!r.ok) throw new Error(js.error || "failed to get job status");
        log(logEl, js);
        if (js.status === "running") setTimeout(tick, 3000);
      } catch (e) {
        log(logEl, "Error: " + e.message);
      }
    }
    tick();
  }

  function renderTable(container, rows) {
    if (!container) return;
    container.innerHTML = "";
    if (!rows || !rows.length) {
      container.textContent = "No rows.";
      return;
    }
    const cols = Object.keys(rows[0]);
    const table = document.createElement("table");
    table.innerHTML = "<thead><tr>" + cols.map((c) => `<th>${esc(c)}</th>`).join("") + "</tr></thead>";
    const tbody = document.createElement("tbody");
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = cols.map((c) => `<td>${esc(row[c])}</td>`).join("");
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    container.appendChild(table);
  }

  const btnExtract = $("#btn-extract");
  if (btnExtract) {
    btnExtract.addEventListener("click", async () => {
      const logEl = $("#ext-log");
      log(logEl, "Running...");
      try {
        let iclPath = val("#ext-icl");
        const iclFile = $("#ext-icl-file");
        if (!iclPath && iclFile && iclFile.files.length) iclPath = await uploadFile(iclFile);
        const payload = {
          elsevier_key: val("#ext-els-key"),
          elsevier_insttoken: val("#ext-insttoken") || null,
          keyword: val("#ext-keyword"),
          count: parseInt(val("#ext-count"), 10) || 20,
          workers: parseInt(val("#ext-workers"), 10) || 1,
          out: val("#ext-out") || null,
          resume: checked("#ext-resume"),
          background: checked("#ext-background"),
          chunk_chars: parseInt(val("#ext-chunk-chars"), 10) || 14000,
          chunk_overlap: parseInt(val("#ext-chunk-overlap"), 10) || 1000,
          max_chunks: parseInt(val("#ext-max-chunks"), 10) || 8,
          metrics: toList(val("#ext-metrics")),
          icl_path: iclPath || null,
          schema_path: val("#ext-schema") || null,
          icl_bank_path: val("#ext-icl-bank") || null,
          icl_top_k: parseInt(val("#ext-icl-top-k"), 10) || 3,
          domain: val("#ext-domain") || null,
          llm_key: val("#ext-llm-key") || null,
          llm_base: val("#ext-llm-base") || null,
          llm_model: val("#ext-llm-model") || null,
        };
        const js = await postJson("/extract", payload);
        if (js.job_id) {
          log(logEl, { message: "background extraction started", job_id: js.job_id, status: js.status });
          pollExtractJob(js.job_id, logEl);
        } else {
          log(logEl, { message: "extraction completed", output_csv: js.output_csv });
        }
      } catch (e) {
        log(logEl, "Error: " + e.message);
      }
    });
  }

  const clnFile = $("#cln-file");
  if (clnFile) {
    clnFile.addEventListener("change", async (e) => {
      try {
        const p = await uploadFile(e.target);
        if (p) $("#cln-csv").value = p;
      } catch (err) {
        alert(err.message);
      }
    });
  }

  const btnClean = $("#btn-clean");
  if (btnClean) {
    btnClean.addEventListener("click", async () => {
      const logEl = $("#cln-log");
      log(logEl, "Running...");
      try {
        const js = await postJson("/clean", {
          csv_path: val("#cln-csv"),
          grouping: toList(val("#cln-grouping")),
          keys: toList(val("#cln-keys")),
          required: toList(val("#cln-required")),
          nonzero: toList(val("#cln-nonzero")),
        });
        log(logEl, { message: "cleaning completed", rows: js.rows, output_csv: js.output_csv, entity_map: js.entity_map, entity_summary: js.entity_summary });
      } catch (e) {
        log(logEl, "Error: " + e.message);
      }
    });
  }

  const btnImpEval = $("#btn-imp-eval");
  if (btnImpEval) {
    btnImpEval.addEventListener("click", async () => {
      $("#imp-summary").textContent = "Running...";
      $("#imp-table").innerHTML = "";
      try {
        const js = await postJson("/impute/evaluate", {
          csv_path: val("#imp-csv"),
          use_columns: toList(val("#imp-cols")),
          llm_key: val("#imp-llm-key") || null,
          llm_base: val("#imp-llm-base") || null,
          llm_model: val("#imp-llm-model") || null,
          mask_frac: parseFloat(val("#imp-mask")) || 0.1,
          repeats: parseInt(val("#imp-repeats"), 10) || 3,
          seed: parseInt(val("#imp-seed"), 10) || 42,
        });
        const m = js.missingness || {};
        $("#imp-summary").textContent = `Missingness: mean=${Number(m.mean || 0).toFixed(4)} median=${Number(m.median || 0).toFixed(4)} p90=${Number(m.p90 || 0).toFixed(4)}; summary CSV=${js.summary_csv}`;
        renderTable($("#imp-table"), js.report || []);
      } catch (e) {
        $("#imp-summary").textContent = "Error: " + e.message;
      }
    });
  }

  const btnImpApply = $("#btn-imp-apply");
  if (btnImpApply) {
    btnImpApply.addEventListener("click", async () => {
      const logEl = $("#imp-log");
      log(logEl, "Running...");
      try {
        const js = await postJson("/impute/apply", {
          csv_path: val("#imp-csv"),
          method: val("#imp-apply-method"),
          params: val("#imp-apply-params") || "{}",
        });
        log(logEl, { message: "completed", output_csv: js.output_csv });
      } catch (e) {
        log(logEl, "Error: " + e.message);
      }
    });
  }

  const btnOpt = $("#btn-opt");
  if (btnOpt) {
    btnOpt.addEventListener("click", async () => {
      $("#opt-log").textContent = "Running...";
      $("#opt-table").innerHTML = "";
      try {
        const js = await postJson("/suggest", {
          csv_path: val("#opt-csv"),
          columns: {
            T: val("#opt-col-T"),
            P: val("#opt-col-P"),
            conv: val("#opt-col-conv"),
            sel: val("#opt-col-sel"),
            yld: val("#opt-col-yld"),
          },
          top_k: parseInt(val("#opt-topk"), 10) || 5,
          n_candidates: parseInt(val("#opt-nc"), 10) || 2000,
          objective: val("#opt-objective") || null,
          weights: {
            sel: parseFloat(val("#opt-w-sel")) || 0,
            conv: parseFloat(val("#opt-w-conv")) || 0,
            yld: parseFloat(val("#opt-w-yld")) || 0,
          },
        });
        renderTable($("#opt-table"), js.suggestions || []);
        $("#opt-log").textContent = "Completed";
      } catch (e) {
        $("#opt-log").textContent = "Error: " + e.message;
      }
    });
  }

  const corFile = $("#cor-file");
  if (corFile) {
    corFile.addEventListener("change", async (e) => {
      try {
        const p = await uploadFile(e.target);
        if (p) $("#cor-csv").value = p;
      } catch (err) {
        alert(err.message);
      }
    });
  }

  const btnCorView = $("#btn-cor-view");
  if (btnCorView) {
    btnCorView.addEventListener("click", async () => {
      const logEl = $("#cor-view");
      log(logEl, "Running...");
      try {
        const js = await postJson("/record", {
          csv_path: val("#cor-csv"),
          row_index: parseInt(val("#cor-row-index"), 10) || 0,
        });
        log(logEl, js);
        if (js.row && js.row.doi) $("#cor-doi").value = String(js.row.doi);
      } catch (e) {
        log(logEl, "Error: " + e.message);
      }
    });
  }

  const btnCorApply = $("#btn-cor-apply");
  if (btnCorApply) {
    btnCorApply.addEventListener("click", async () => {
      const logEl = $("#cor-log");
      log(logEl, "Running...");
      try {
        const payload = {
          csv_path: val("#cor-csv"),
          doi: val("#cor-doi") || null,
          metric: val("#cor-metric"),
          value: val("#cor-value"),
          unit: val("#cor-unit"),
          note: val("#cor-note"),
        };
        const js = await postJson("/correct", payload);
        log(logEl, js);
      } catch (e) {
        log(logEl, "Error: " + e.message);
      }
    });
  }

  function renderQaResult(js) {
    const answer = $("#qa-answer");
    const evidence = $("#qa-evidence");
    if (!answer || !evidence) return;
    const interp = js.query_interpretation || {};
    const list = (title, items) => items && items.length
      ? `<h4>${esc(title)}</h4><ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`
      : "";
    answer.innerHTML = `
      <h3>Decision Support</h3>
      <p class="qa-meta">Answer source: ${js.llm_used ? `DeepSeek grounded answer (${esc(js.llm_model || "model")})` : "local retrieval + rules"}</p>
      <p>${esc(js.answer)}</p>
      <p class="qa-meta">Mode: ${esc(interp.mode || "")} | Matched rows: ${esc(interp.matched_rows || 0)} | Evidence hits: ${esc(interp.evidence_hits || 0)}</p>
      ${js.llm_error ? `<p class="qa-error">LLM fallback: ${esc(js.llm_error)}</p>` : ""}
      ${list("Recommendations", js.recommendations || [])}
      ${list("Risks", js.risks || [])}
      ${list("Suggested next experiments", js.suggested_next_experiments || [])}
    `;
    const hits = js.evidence || [];
    evidence.innerHTML = hits.map((h) => `
      <article class="evidence-card">
        <div class="evidence-head">
          <strong>Row ${esc(h.row_index)}</strong>
          <span>score ${esc(h.score)}</span>
        </div>
        <p class="evidence-title">${esc(h.title || "Untitled")}</p>
        <p><b>DOI:</b> ${esc(h.doi || "NA")}</p>
        <p><b>Tier:</b> ${esc(h.project_tier || "NA")}</p>
        <p><b>Metric:</b> ${esc(h.primary_result_metric || "NA")} ${esc(h.primary_result_value || "")} ${esc(h.primary_result_unit || "")}</p>
        <p><b>Evidence:</b> ${esc(h.evidence || "NA")}</p>
        <p><b>Design:</b> ${esc(h.design_action_tags || "NA")}</p>
        <p><b>Risk:</b> ${esc(h.defect_risk_tags || "NA")}</p>
      </article>
    `).join("");
  }

  const btnQa = $("#btn-qa");
  if (btnQa) {
    btnQa.addEventListener("click", async () => {
      const logEl = $("#qa-log");
      log(logEl, "Searching evidence...");
      $("#qa-answer").innerHTML = "";
      $("#qa-evidence").innerHTML = "";
      try {
        const js = await postJson("/literature-qa", {
          question: val("#qa-question"),
          evidence_csv: val("#qa-csv") || null,
          top_k: parseInt(val("#qa-topk"), 10) || 8,
          filters: {
            project_only: checked("#qa-project-only"),
            yeast: checked("#qa-yeast"),
            llps: checked("#qa-llps"),
            glabridin: checked("#qa-glabridin"),
            high_transfer_llps: checked("#qa-high-transfer"),
          },
          llm: {
            use_llm: checked("#qa-use-llm"),
            api_key: val("#qa-llm-key") || null,
            base_url: val("#qa-llm-base") || null,
            model: val("#qa-llm-model") || null,
            temperature: parseFloat(val("#qa-llm-temp")) || 0.15,
          },
        });
        renderQaResult(js);
        log(logEl, { evidence_csv: js.evidence_csv, provenance_note: js.provenance_note });
      } catch (e) {
        log(logEl, "Error: " + e.message);
      }
    });
  }

  function parseJsonOrEmpty(sel) {
    const text = val(sel);
    if (!text) return {};
    return JSON.parse(text);
  }

  function renderAgentTrace(js) {
    const summary = $("#agent-summary");
    const trace = $("#agent-trace");
    if (!summary || !trace) return;
    const final = js.final_answer || {};
    const missing = final.missing_inputs || [];
    summary.innerHTML = `
      <h3>Agent Result</h3>
      <p class="qa-meta">Mode: ${esc(js.mode || "")} | Trace steps: ${esc((js.trace || []).length)} | External execution: ${esc(js.run_external)}</p>
      <p>${esc(final.evidence_summary || "No evidence summary returned.")}</p>
      ${missing.length ? `<h4>Missing strict inputs</h4><ul>${missing.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
      <h4>Agentic behavior</h4>
      <ul>${(js.agentic_features || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
    `;
    trace.innerHTML = (js.trace || []).map((t) => `
      <article class="evidence-card agent-trace-card">
        <div class="evidence-head">
          <strong>Step ${esc(t.step)} - ${esc(t.module)}</strong>
          <span>${esc(t.decision)}</span>
        </div>
        <p class="evidence-title">${esc(t.action)}</p>
        <pre>${esc(JSON.stringify(t.observation || {}, null, 2))}</pre>
      </article>
    `).join("");
  }

  const btnAgentHealth = $("#btn-agent-health");
  if (btnAgentHealth) {
    btnAgentHealth.addEventListener("click", async () => {
      const logEl = $("#agent-log");
      log(logEl, "Checking tools...");
      try {
        const js = await postJson("/agent/external-tools", {
          network: checked("#agent-network-check"),
        });
        const probes = js.external_tool_probes || {};
        const summary = Object.fromEntries(Object.entries(probes).map(([k, v]) => [k, {
          available: v.available,
          callable: v.callable,
          status: v.status,
        }]));
        log(logEl, {
          external_tool_probes: summary,
          python_packages: js.python_packages,
          network_services: js.network_services || {},
        });
      } catch (e) {
        log(logEl, "Error: " + e.message);
      }
    });
  }

  const btnAgentRun = $("#btn-agent-run");
  if (btnAgentRun) {
    btnAgentRun.addEventListener("click", async () => {
      const logEl = $("#agent-log");
      $("#agent-summary").innerHTML = "";
      $("#agent-trace").innerHTML = "";
      log(logEl, "Running agent...");
      try {
        const js = await postJson("/agent/run", {
          goal: val("#agent-goal"),
          top_k: parseInt(val("#agent-topk"), 10) || 5,
          max_steps: parseInt(val("#agent-max-steps"), 10) || 10,
          run_external: checked("#agent-run-external"),
          network_check: checked("#agent-network-check"),
          tool_inputs: parseJsonOrEmpty("#agent-tool-inputs"),
        });
        renderAgentTrace(js);
        log(logEl, {
          agent: js.agent,
          trace_steps: (js.trace || []).length,
          external_results: (js.final_answer || {}).external_results || {},
        });
      } catch (e) {
        log(logEl, "Error: " + e.message);
      }
    });
  }
})();
