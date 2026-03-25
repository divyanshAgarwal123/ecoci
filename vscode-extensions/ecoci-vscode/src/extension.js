const vscode = require('vscode');
const { exec } = require('child_process');

function runEcoci(command, cwd) {
  return new Promise((resolve, reject) => {
    exec(command, { cwd }, (error, stdout, stderr) => {
      if (error) {
        reject(new Error(stderr || error.message));
        return;
      }
      resolve(stdout || stderr || '');
    });
  });
}

async function pickWorkspaceRoot() {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    vscode.window.showErrorMessage('No workspace folder found. Open a repository first.');
    return undefined;
  }
  return folders[0].uri.fsPath;
}

async function showOutput(title, content) {
  const doc = await vscode.workspace.openTextDocument({
    language: 'markdown',
    content: `# ${title}\n\n\`\`\`\n${content}\n\`\`\`\n`,
  });
  await vscode.window.showTextDocument(doc, { preview: true });
}

function extractMetrics(analysisPayload) {
  const metrics = analysisPayload?.metrics || {};
  return {
    duration: metrics.total_duration_seconds ?? 'N/A',
    cost: metrics.total_cost_usd ?? 'N/A',
    energy: metrics.total_kwh ?? 'N/A',
    co2: metrics.total_co2_kg ?? 'N/A',
  };
}

class EcoCIDashboardViewProvider {
  constructor(context) {
    this.context = context;
    this.view = undefined;
  }

  resolveWebviewView(webviewView) {
    this.view = webviewView;
    const webview = webviewView.webview;
    webview.options = { enableScripts: true };
    webview.html = this.getHtml();

    webview.onDidReceiveMessage(async (msg) => {
      if (!msg || !msg.command) return;

      const cwd = await pickWorkspaceRoot();
      if (!cwd) return;

      try {
        if (msg.command === 'analyze') {
          const out = await runEcoci('ecoci analyze --provider github --json', cwd);
          const parsed = JSON.parse(out);
          const analysis = parsed.analysis || {};
          const findings = analysis.findings || [];
          const priority = analysis.prioritized_recommendations || [];
          const quality = analysis.quality_gate || {};
          const m = extractMetrics(parsed);

          webview.postMessage({
            type: 'analysis',
            data: {
              repo: parsed.repo || 'N/A',
              workflow: parsed.workflow || 'N/A',
              findingsCount: findings.length,
              topFindings: findings.slice(0, 5),
              topFixes: priority.slice(0, 5),
              qualityGate: quality,
              metrics: m,
            },
          });
          return;
        }

        if (msg.command === 'optimize') {
          const out = await runEcoci('ecoci optimize --provider github --json', cwd);
          const parsed = JSON.parse(out);
          webview.postMessage({
            type: 'optimize',
            data: {
              workflow: parsed.workflow || 'N/A',
              changeCount: (parsed.changes || []).length,
              changes: (parsed.changes || []).slice(0, 8),
              fixes: (parsed.fixes || []).slice(0, 8),
            },
          });
          return;
        }

        if (msg.command === 'pr') {
          const out = await runEcoci('ecoci pr create --provider github --dry-run --json', cwd);
          const parsed = JSON.parse(out);
          webview.postMessage({
            type: 'pr',
            data: {
              repo: parsed.repo || 'N/A',
              workflow: parsed.workflow || 'N/A',
              title: parsed.title || 'N/A',
              base: parsed.base || 'N/A',
              branch: parsed.branch || 'N/A',
              changeCount: (parsed.changes || []).length,
            },
          });
          return;
        }
      } catch (e) {
        webview.postMessage({
          type: 'error',
          message: e.message || String(e),
        });
      }
    });
  }

  getHtml() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body { font-family: var(--vscode-font-family); padding: 12px; color: var(--vscode-foreground); }
    .row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
    button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: 0; padding: 6px 10px; border-radius: 4px; cursor: pointer; }
    button:hover { background: var(--vscode-button-hoverBackground); }
    .card { border: 1px solid var(--vscode-panel-border); border-radius: 6px; padding: 10px; margin-bottom: 10px; }
    .muted { opacity: 0.8; font-size: 12px; }
    ul { margin: 6px 0 0 16px; padding: 0; }
    code { font-family: var(--vscode-editor-font-family); }
  </style>
</head>
<body>
  <h3>EcoCI Dashboard</h3>
  <div class="row">
    <button id="analyze">Analyze</button>
    <button id="optimize">Optimize</button>
    <button id="pr">PR Dry Run</button>
  </div>
  <div id="content" class="card">
    <div>Run an action to populate CI insights.</div>
    <div class="muted">Requires <code>ecoci</code> CLI in PATH.</div>
  </div>

  <script>
    const vscode = acquireVsCodeApi();
    const content = document.getElementById('content');

    document.getElementById('analyze').addEventListener('click', () => {
      vscode.postMessage({ command: 'analyze' });
    });
    document.getElementById('optimize').addEventListener('click', () => {
      vscode.postMessage({ command: 'optimize' });
    });
    document.getElementById('pr').addEventListener('click', () => {
      vscode.postMessage({ command: 'pr' });
    });

    window.addEventListener('message', event => {
      const msg = event.data;
      if (msg.type === 'error') {
        content.innerHTML = '<div><strong>Error:</strong> ' + msg.message + '</div>';
        return;
      }
      if (msg.type === 'analysis') {
        const d = msg.data;
        const findings = (d.topFindings || []).map(f => '<li>[' + (f.severity || 'info') + '] ' + (f.message || '') + '</li>').join('');
        const fixes = (d.topFixes || []).map(f => '<li>[' + (f.severity || 'low') + '] ' + (f.fix || '') + '</li>').join('');
        content.innerHTML =
          '<div><strong>Repo:</strong> ' + d.repo + '</div>' +
          '<div><strong>Workflow:</strong> ' + d.workflow + '</div>' +
          '<div><strong>Findings:</strong> ' + d.findingsCount + '</div>' +
          '<div><strong>Quality Gate:</strong> ' + (d.qualityGate.status || 'unknown').toUpperCase() + '</div>' +
          '<div class="muted">Duration: ' + d.metrics.duration + 's • Cost: $' + d.metrics.cost + ' • Energy: ' + d.metrics.energy + ' kWh • CO2: ' + d.metrics.co2 + ' kg</div>' +
          '<div class="card"><strong>Top Findings</strong><ul>' + (findings || '<li>None</li>') + '</ul></div>' +
          '<div class="card"><strong>Priority Fixes</strong><ul>' + (fixes || '<li>None</li>') + '</ul></div>';
        return;
      }
      if (msg.type === 'optimize') {
        const d = msg.data;
        const changes = (d.changes || []).map(c => '<li>' + c + '</li>').join('');
        content.innerHTML =
          '<div><strong>Workflow:</strong> ' + d.workflow + '</div>' +
          '<div><strong>Changes:</strong> ' + d.changeCount + '</div>' +
          '<div class="card"><strong>Planned Changes</strong><ul>' + (changes || '<li>No changes</li>') + '</ul></div>';
        return;
      }
      if (msg.type === 'pr') {
        const d = msg.data;
        content.innerHTML =
          '<div><strong>Repo:</strong> ' + d.repo + '</div>' +
          '<div><strong>Workflow:</strong> ' + d.workflow + '</div>' +
          '<div><strong>Title:</strong> ' + d.title + '</div>' +
          '<div><strong>Base → Branch:</strong> ' + d.base + ' → ' + d.branch + '</div>' +
          '<div><strong>Planned Changes:</strong> ' + d.changeCount + '</div>' +
          '<div class="muted">Dry-run only. No commit or PR created.</div>';
      }
    });
  </script>
</body>
</html>`;
  }
}

function activate(context) {
  const dashboard = new EcoCIDashboardViewProvider(context);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider('ecoci.dashboard', dashboard)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('ecoci.openDashboard', async () => {
      await vscode.commands.executeCommand('workbench.view.extension.ecoci');
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('ecoci.analyzeRepo', async () => {
      const cwd = await pickWorkspaceRoot();
      if (!cwd) return;
      try {
        const out = await runEcoci('ecoci analyze --provider github --json', cwd);
        await showOutput('EcoCI Analyze Current Repo', out);
      } catch (e) {
        vscode.window.showErrorMessage(`EcoCI analyze failed: ${e.message}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('ecoci.optimizeWorkflows', async () => {
      const cwd = await pickWorkspaceRoot();
      if (!cwd) return;
      try {
        const out = await runEcoci('ecoci optimize --provider github --json', cwd);
        await showOutput('EcoCI Optimize CI Workflows', out);
      } catch (e) {
        vscode.window.showErrorMessage(`EcoCI optimize failed: ${e.message}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('ecoci.createOptimizationPR', async () => {
      const cwd = await pickWorkspaceRoot();
      if (!cwd) return;
      const title = await vscode.window.showInputBox({
        prompt: 'Pull request title',
        value: 'EcoCI: Optimize GitHub Actions workflow',
      });
      if (!title) return;
      try {
        const safeTitle = title.replace(/"/g, '\\"');
        const out = await runEcoci(`ecoci pr create --provider github --title "${safeTitle}" --json`, cwd);
        await showOutput('EcoCI Create Optimization PR', out);
      } catch (e) {
        vscode.window.showErrorMessage(`EcoCI PR creation failed: ${e.message}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('ecoci.showCarbonCostSummary', async () => {
      const cwd = await pickWorkspaceRoot();
      if (!cwd) return;
      try {
        const out = await runEcoci('ecoci analyze --provider github --json', cwd);
        await showOutput('EcoCI Carbon & Cost Summary', out);
      } catch (e) {
        vscode.window.showErrorMessage(`EcoCI summary failed: ${e.message}`);
      }
    })
  );
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
