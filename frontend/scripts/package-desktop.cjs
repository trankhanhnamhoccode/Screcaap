const { spawnSync } = require('node:child_process');
const path = require('node:path');

// npm can prepend an unrelated parent node_modules/node/bin to PATH.
// Use the runtime that launched npm rather than that shadowed node executable.
const node = process.env.npm_node_execpath || process.execPath;
const result = spawnSync(node, [
  path.join(__dirname, '../node_modules/electron-builder/cli.js'),
  ...process.argv.slice(2),
], { stdio: 'inherit' });
if (result.error) {
  console.error('Unable to launch desktop packaging:', result.error.message);
}
process.exit(result.status ?? 1);
