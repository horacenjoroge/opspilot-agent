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
  }
});
