const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const approvedRoutes = Object.freeze({
  'vp-orchestrator': ['gpt-6.1-sol', 'high'],
  'vp-modelling': ['gpt-6-astra', 'xhigh'],
  'vp-camtasia': ['gpt-6.1-sol', 'xhigh'],
  'vp-reference': ['gpt-6-astra', 'high'],
  'vp-camera': ['gpt-6-astra', 'xhigh'],
  'vp-capture': ['gpt-6.1-sol', 'medium'],
  'vp-media': ['gpt-6.1-sol', 'high'],
  'vp-geometry-qa': ['gpt-6-astra', 'xhigh'],
  'vp-video-qa': ['gpt-6.1-sol', 'xhigh'],
  'vp-integration': ['gpt-6.1-sol', 'high'],
  'vp-documentation': ['gpt-6.1-sol', 'medium'],
  'vp-publication': ['gpt-6.1-sol', 'medium'],
});

function parseFrontmatter(text) {
  const match = /^\uFEFF?---\r?\n([\s\S]*?)\r?\n---\r?\n/.exec(text);
  assert.ok(match, 'Missing YAML frontmatter');
  const metadata = {};
  for (const line of match[1].split(/\r?\n/)) {
    const field = /^([a-z][a-z-]*): (.+)$/.exec(line);
    assert.ok(field, `Use one JSON-compatible YAML value per line: ${line}`);
    const [, key, raw] = field;
    assert.ok(!Object.hasOwn(metadata, key), `Duplicate frontmatter key: ${key}`);
    if (/^(?:"|\[|true$|false$)/.test(raw)) {
      metadata[key] = JSON.parse(raw);
    } else {
      assert.match(raw, /^[a-z0-9][a-z0-9.-]*$/i, `Invalid plain scalar: ${raw}`);
      metadata[key] = raw;
    }
  }
  return { metadata, body: text.slice(match[0].length) };
}

function validateProfile(metadata, name) {
  assert.ok(Object.hasOwn(approvedRoutes, name), `Unknown production role: ${name}`);
  const [model, effort] = approvedRoutes[name];
  assert.equal(metadata.name, name, `Agent/file name mismatch: ${name}`);
  assert.ok(!Object.hasOwn(metadata, 'target'), `Do not emit the CLI-ignored target field: ${name}`);
  assert.equal(metadata.model, model, `Unapproved model or fallback: ${name}`);
  assert.equal(metadata['reasoning-effort'], effort, `Unapproved effort: ${name}`);
  assert.ok(typeof metadata.description === 'string' && metadata.description.length > 30);
  assert.ok(Array.isArray(metadata.tools) && metadata.tools.length > 0);
  assert.ok(metadata.tools.every((tool) => typeof tool === 'string' && tool !== '*'));
  const coordinator = name === 'vp-orchestrator';
  assert.equal(metadata['user-invocable'], coordinator);
  assert.equal(metadata.tools.includes('agent'), coordinator, `Delegation scope: ${name}`);
  const hasMcp = metadata.tools.some((tool) => tool.includes('/') && !tool.startsWith('vscode/'));
  if (coordinator) {
    assert.ok(!hasMcp && !metadata.tools.includes('execute') && !metadata.tools.includes('edit'),
      'Coordinator must not control applications, shell or file writes');
  }
  if (['vp-modelling', 'vp-camera', 'vp-geometry-qa'].includes(name)) {
    assert.ok(!metadata.tools.includes('execute'), `Native role has shell access: ${name}`);
    assert.ok(!metadata.tools.some((tool) => tool.startsWith('camtasia/')));
    assert.ok(metadata.tools.includes('bentley-mstn/*'));
    assert.ok(metadata.tools.includes('MicroStation MCP/*'));
  } else {
    assert.ok(!metadata.tools.some((tool) => /^(?:bentley-|MicroStation MCP\/)/.test(tool)),
      `Non-native role has MicroStation access: ${name}`);
  }
  if (['vp-reference', 'vp-media', 'vp-integration', 'vp-documentation', 'vp-publication'].includes(name)) {
    assert.ok(!hasMcp, `Offline role has live MCP access: ${name}`);
  }
  if (name === 'vp-camtasia') {
    assert.ok(metadata.tools.includes('camtasia/*'));
    assert.ok(!metadata.tools.includes('execute'));
  }
  if (['vp-capture', 'vp-video-qa'].includes(name)) {
    assert.ok(!metadata.tools.includes('camtasia/*'), `Unbounded Camtasia access: ${name}`);
    assert.ok(!metadata.tools.some((tool) => /^camtasia\/camtasia_(?:add|delete|update|set|restore|relink|create)_/.test(tool)));
  }
}

function markdownFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    if (['.git', '.venv', 'node_modules'].includes(entry.name)) return [];
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) return markdownFiles(fullPath);
    return entry.isFile() && entry.name.endsWith('.md') ? [fullPath] : [];
  });
}

function headingIds(text) {
  const ids = new Set();
  for (const match of text.matchAll(/^#{1,6}\s+(.+)$/gm)) {
    const base = match[1].trim().toLowerCase().replace(/[^\p{L}\p{N}_ -]/gu, '').replace(/ /g, '-');
    let id = base;
    let suffix = 0;
    while (ids.has(id)) id = `${base}-${++suffix}`;
    ids.add(id);
  }
  return ids;
}

function validateLinks(root) {
  let count = 0;
  for (const file of markdownFiles(root)) {
    const text = fs.readFileSync(file, 'utf8');
    for (const match of text.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)) {
      const target = match[1].replace(/^<|>$/g, '');
      if (/^[a-z][a-z0-9+.-]*:/i.test(target)) continue;
      const [relative, fragment] = target.split('#');
      const destination = relative
        ? path.resolve(path.dirname(file), relative.split('/').join(path.sep))
        : file;
      assert.ok(fs.existsSync(destination), `Broken link in ${path.relative(root, file)}: ${target}`);
      if (fragment && destination.endsWith('.md')) {
        assert.ok(headingIds(fs.readFileSync(destination, 'utf8')).has(fragment),
          `Broken heading in ${path.relative(root, file)}: ${target}`);
      }
      count++;
    }
  }
  return count;
}

function validateOrchestration(root) {
  const directory = path.join(root, '.github', 'agents');
  const filenames = fs.readdirSync(directory).filter((name) => /^vp-.*\.agent\.md$/.test(name));
  assert.deepEqual(filenames.map((name) => name.replace(/\.agent\.md$/, '')).sort(),
    Object.keys(approvedRoutes).sort(), 'Missing or unexpected production profile');
  const guide = fs.readFileSync(path.join(root, 'ORCHESTRATION.md'), 'utf8');
  for (const filename of filenames) {
    const name = filename.replace(/\.agent\.md$/, '');
    const { metadata, body } = parseFrontmatter(fs.readFileSync(path.join(directory, filename), 'utf8'));
    validateProfile(metadata, name);
    assert.ok(body.includes('../../ORCHESTRATION.md'), `Missing shared contract: ${name}`);
    const [model, effort] = approvedRoutes[name];
    assert.ok(guide.includes(`[${name}](.github/agents/${filename}) | ${model} | ${effort} |`),
      `Routing table disagrees with profile: ${name}`);
  }
  for (const filename of ['orchestrate-video.prompt.md', 'microstation-video.prompt.md']) {
    const { metadata } = parseFrontmatter(fs.readFileSync(path.join(root, '.github', 'prompts', filename), 'utf8'));
    assert.equal(metadata.agent, 'vp-orchestrator', `Prompt bypasses coordinator: ${filename}`);
    assert.ok(!Object.hasOwn(metadata, 'tools') && !Object.hasOwn(metadata, 'model'),
      `Prompt overrides coordinator configuration: ${filename}`);
  }
  const { metadata: skill } = parseFrontmatter(fs.readFileSync(
    path.join(root, '.github', 'skills', 'microstation-camtasia-video', 'SKILL.md'), 'utf8'));
  assert.equal(skill.name, 'microstation-camtasia-video');
  const links = validateLinks(root);
  return { profiles: filenames.length, links };
}

module.exports = { approvedRoutes, parseFrontmatter, validateProfile, validateLinks, validateOrchestration };

if (require.main === module) {
  try {
    const result = validateOrchestration(path.resolve(__dirname, '..'));
    console.log(`PASS: ${result.profiles} approved model/effort profiles; ${result.links} local links/headings; coordinator and worker scopes`);
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
