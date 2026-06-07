async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || `Request failed: ${response.status}`);
  }
  return response.json();
}

async function postEmpty(url) {
  const response = await fetch(url, { method: "POST" });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || `Request failed: ${response.status}`);
  }
  return response.json();
}

function renderEvaluationSummary(summary) {
  const summaryNode = document.getElementById("eval-summary");
  if (!summaryNode) {
    return;
  }
  summaryNode.textContent = `${summary.passed}/${summary.total} passed`;
  summaryNode.className = `badge ${summary.failed === 0 ? "" : "neutral"}`.trim();
}

function renderEvaluationResults(results) {
  const resultsNode = document.getElementById("eval-results");
  if (!resultsNode) {
    return;
  }

  resultsNode.innerHTML = "";
  for (const result of results) {
    const article = document.createElement("article");
    article.className = "eval-card";

    const checks = Object.entries(result.checks)
      .map(([name, passed]) => `<span class="badge ${passed ? "" : "neutral"}">${name}: ${passed ? "PASS" : "FAIL"}</span>`)
      .join("");

    article.innerHTML = `
      <div class="panel-header">
        <div>
          <p class="eyebrow">Scenario</p>
          <h3>${result.scenario}</h3>
        </div>
        <span class="badge ${result.passed ? "" : "neutral"}">${result.passed ? "PASS" : "FAIL"}</span>
      </div>
      <p><strong>Incident:</strong> <a href="/incidents/${result.incident_id}">#${result.incident_id}</a></p>
      <p><strong>Severity:</strong> expected ${result.expected.expected_severity}, actual ${result.actual_severity}</p>
      <p><strong>Tools:</strong> expected ${result.expected.expected_tools.join(", ")}, actual ${result.actual_tools.join(", ")}</p>
      <p><strong>Approval:</strong> expected ${result.expected.expected_requires_approval}, actual ${result.actual_requires_approval}</p>
      <p><strong>Final status:</strong> expected ${result.expected.expected_final_status}, actual ${result.actual_final_status}</p>
      <p><strong>Diagnosis:</strong> ${result.diagnosis_text}</p>
      <div class="action-row">${checks}</div>
    `;
    resultsNode.appendChild(article);
  }
}

document.addEventListener("click", async (event) => {
  const runButton = event.target.closest("[data-run-agent]");
  if (runButton) {
    runButton.disabled = true;
    try {
      await postEmpty(`/api/incidents/${runButton.dataset.runAgent}/run-agent`);
      window.location.href = `/incidents/${runButton.dataset.runAgent}`;
    } catch (error) {
      alert(`Could not run agent: ${error.message}`);
      runButton.disabled = false;
    }
    return;
  }

  const demoButton = event.target.closest("[data-demo-scenario]");
  if (demoButton) {
    demoButton.disabled = true;
    try {
      const incident = await postEmpty(`/api/demo/incidents/${demoButton.dataset.demoScenario}`);
      window.location.href = `/incidents/${incident.id}`;
    } catch (error) {
      alert(`Could not create demo incident: ${error.message}`);
      demoButton.disabled = false;
    }
    return;
  }

  const approveButton = event.target.closest("[data-approve-id]");
  if (approveButton) {
    approveButton.disabled = true;
    try {
      await postJson(`/api/approvals/${approveButton.dataset.approveId}/approve`, {
        approved_by: "dashboard.operator",
      });
      window.location.reload();
    } catch (error) {
      alert(`Could not approve action: ${error.message}`);
      approveButton.disabled = false;
    }
    return;
  }

  const rejectButton = event.target.closest("[data-reject-id]");
  if (rejectButton) {
    rejectButton.disabled = true;
    try {
      await postJson(`/api/approvals/${rejectButton.dataset.rejectId}/reject`, {
        approved_by: "dashboard.operator",
      });
      window.location.reload();
    } catch (error) {
      alert(`Could not reject action: ${error.message}`);
      rejectButton.disabled = false;
    }
    return;
  }

  const evalButton = event.target.closest("[data-run-evals]");
  if (evalButton) {
    evalButton.disabled = true;
    try {
      const target = evalButton.dataset.runEvals;
      const response = target === "all"
        ? await postEmpty("/api/evals/run")
        : await postEmpty(`/api/evals/run/${target}`);
      const summary = target === "all"
        ? response
        : { total: 1, passed: response.passed ? 1 : 0, failed: response.passed ? 0 : 1 };
      const results = target === "all" ? response.results : [response];
      renderEvaluationSummary(summary);
      renderEvaluationResults(results);
    } catch (error) {
      alert(`Could not run evaluations: ${error.message}`);
    } finally {
      evalButton.disabled = false;
    }
  }
});
