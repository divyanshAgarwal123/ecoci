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

function activate(context) {
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
