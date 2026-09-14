/* Dùng Playwright đã có trong runtime Codex; không cài dependency cho ứng dụng. */
const path = require('node:path');
const os = require('node:os');
module.exports = require(process.env.KN_PLAYWRIGHT_MODULE || path.join(
  os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'));
