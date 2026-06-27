function getBanner() {
  return document.getElementById("app-banner");
}

function showBanner(message, tone = "info") {
  const banner = getBanner();
  if (!banner) {
    return;
  }
  banner.textContent = message;
  banner.className = `app-banner ${tone}`;
}

function clearBanner() {
  const banner = getBanner();
  if (!banner) {
    return;
  }
  banner.textContent = "";
  banner.className = "app-banner hidden";
}

function setButtonLoading(button, loadingText) {
  button.dataset.originalText = button.textContent;
  button.textContent = loadingText;
  button.disabled = true;
  button.classList.add("is-loading");
}

function resetButtonLoading(button) {
  if (button.dataset.originalText) {
    button.textContent = button.dataset.originalText;
  }
  button.disabled = false;
  button.classList.remove("is-loading");
}

async function parseError(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const payload = await response.json();
    const requestId = payload.request_id ? ` Request ID: ${payload.request_id}.` : "";
    return `${payload.detail || `Request failed: ${response.status}`}${requestId}`;
  }
  const text = await response.text();
  return text || `Request failed: ${response.status}`;
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

function getCurrentUserName() {
  return document.body.dataset.currentUser || "dashboard.operator";
}

async function postEmpty(url) {
  const response = await fetch(url, { method: "POST" });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

async function loginWithPassword(email, password) {
  return postJson("/api/auth/login", { email, password });
}

function renderEvaluationSummary(summary) {
  const summaryNode = document.getElementById("eval-summary");
  if (!summaryNode) {
    return;
  }
  const provider = document.body.dataset.provider || "Unknown";
  summaryNode.textContent = `${summary.passed}/${summary.total} passed · Provider: ${provider}`;
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
      <p><strong>Tools:</strong> expected ${result.expected.expected_tools.join(", ")}, actual ${result.actual_tools.join(", ") || "none"}</p>
      <p><strong>Approval:</strong> expected ${result.expected.expected_requires_approval}, actual ${result.actual_requires_approval}</p>
      <p><strong>Final status:</strong> expected ${result.expected.expected_final_status}, actual ${result.actual_final_status}</p>
      <p><strong>Diagnosis:</strong> ${result.diagnosis_text}</p>
      <div class="action-row">${checks}</div>
    `;
    resultsNode.appendChild(article);
  }
}

async function pollIncidentStatus(incidentId, onTick, intervalMs = 3000, maxWaitMs = 300000) {
  const deadline = Date.now() + maxWaitMs;
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
    if (onTick) onTick();
    try {
      const response = await fetch(`/api/incidents/${incidentId}`);
      if (response.ok) {
        const incident = await response.json();
        if (incident.status && incident.status !== "triaging") {
          return incident.status;
        }
      }
    } catch (_) {
      // network blip — keep polling
    }
  }
  return "unknown";
}

document.addEventListener("click", async (event) => {
  const passwordToggle = event.target.closest("[data-password-toggle]");
  if (passwordToggle) {
    const wrapper = passwordToggle.closest(".password-input");
    const passwordInput = wrapper ? wrapper.querySelector("input[name='password']") : null;
    if (passwordInput) {
      const reveal = passwordInput.type === "password";
      passwordInput.type = reveal ? "text" : "password";
      passwordToggle.textContent = reveal ? "Hide" : "Show";
      passwordToggle.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
    }
    return;
  }

  const runButton = event.target.closest("[data-run-agent]");
  if (runButton) {
    clearBanner();
    const incidentId = runButton.dataset.runAgent;
    setButtonLoading(runButton, "Running...");
    const startTime = Date.now();
    const elapsed = () => Math.floor((Date.now() - startTime) / 1000);
    const fmtTime = (s) => s >= 60 ? `${Math.floor(s / 60)}m ${s % 60}s` : `${s}s`;
    try {
      await postEmpty(`/api/incidents/${incidentId}/run-agent`);
      showBanner(`Agent started — Qwen is triaging the incident. (0s elapsed)`);
      const finalStatus = await pollIncidentStatus(incidentId, () => {
        showBanner(`Agent running — Qwen is reasoning through triage, evidence, and remediation. (${fmtTime(elapsed())} elapsed)`);
      });
      const totalSeconds = elapsed();
      showBanner(`Agent completed in ${fmtTime(totalSeconds)}. Opening incident detail…`, "success");
      window.location.href = `/incidents/${incidentId}?agent_just_ran=${finalStatus}&elapsed=${totalSeconds}`;
    } catch (error) {
      showBanner(`Could not run agent. ${error.message}`, "error");
      resetButtonLoading(runButton);
    }
    return;
  }

  const demoButton = event.target.closest("[data-demo-scenario]");
  if (demoButton) {
    clearBanner();
    setButtonLoading(demoButton, "Launching...");
    try {
      showBanner("Creating the seeded incident. Next step: open the incident detail page and run the agent.");
      const incident = await postEmpty(`/api/demo/incidents/${demoButton.dataset.demoScenario}`);
      showBanner("Demo incident created. Opening incident detail.", "success");
      window.location.href = `/incidents/${incident.id}?from_demo=1`;
    } catch (error) {
      showBanner(`Could not create demo incident. ${error.message}`, "error");
      resetButtonLoading(demoButton);
    }
    return;
  }

  const approveButton = event.target.closest("[data-approve-id]");
  if (approveButton) {
    clearBanner();
    setButtonLoading(approveButton, "Approving...");
    try {
      showBanner("Approving the risky remediation and waiting for the backend to record the execution path.");
      await postJson(`/api/approvals/${approveButton.dataset.approveId}/approve`, {
        approved_by: getCurrentUserName(),
      });
      showBanner("Approval recorded successfully.", "success");
      window.setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      showBanner(`Could not approve action. ${error.message}`, "error");
      resetButtonLoading(approveButton);
    }
    return;
  }

  const rejectButton = event.target.closest("[data-reject-id]");
  if (rejectButton) {
    clearBanner();
    setButtonLoading(rejectButton, "Rejecting...");
    try {
      showBanner("Rejecting the risky remediation request.");
      await postJson(`/api/approvals/${rejectButton.dataset.rejectId}/reject`, {
        approved_by: getCurrentUserName(),
      });
      showBanner("Rejection recorded successfully.", "success");
      window.setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      showBanner(`Could not reject action. ${error.message}`, "error");
      resetButtonLoading(rejectButton);
    }
    return;
  }

  const evalButton = event.target.closest("[data-run-evals]");
  if (evalButton) {
    clearBanner();
    setButtonLoading(evalButton, "Running...");
    try {
      const target = evalButton.dataset.runEvals;
      showBanner(
        target === "all"
          ? "Running the full evaluation suite against the real backend workflow."
          : `Running evaluation scenario: ${target}.`,
      );
      const response = target === "all"
        ? await postEmpty("/api/evals/run")
        : await postEmpty(`/api/evals/run/${target}`);
      const summary = target === "all"
        ? response
        : { total: 1, passed: response.passed ? 1 : 0, failed: response.passed ? 0 : 1 };
      const results = target === "all" ? response.results : [response];
      renderEvaluationSummary(summary);
      renderEvaluationResults(results);
      showBanner("Evaluation results updated below.", "success");
    } catch (error) {
      showBanner(`Could not run evaluations. ${error.message}`, "error");
    } finally {
      resetButtonLoading(evalButton);
    }
  }
});

document.addEventListener("submit", async (event) => {
  const loginForm = event.target.closest("#login-form");
  if (!loginForm) {
    return;
  }
  event.preventDefault();
  clearBanner();
  const submitButton = loginForm.querySelector("[data-login-submit]");
  const formData = new FormData(loginForm);
  const email = String(formData.get("email") || "");
  const password = String(formData.get("password") || "");
  setButtonLoading(submitButton, "Signing in...");
  try {
    showBanner("Signing in and creating a dashboard session.");
    await loginWithPassword(email, password);
    showBanner("Login successful. Redirecting to the dashboard.", "success");
    window.location.href = loginForm.dataset.nextPath || "/";
  } catch (error) {
    showBanner(`Could not sign in. ${error.message}`, "error");
    resetButtonLoading(submitButton);
  }
});
