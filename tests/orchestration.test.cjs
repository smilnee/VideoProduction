const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const {
  approvedRoutes, parseFrontmatter, validateProfile, validateOrchestration,
} = require('../scripts/validate-orchestration.cjs');

const root = path.resolve(__dirname, '..');
function profile(name) {
  return parseFrontmatter(fs.readFileSync(path.join(root, '.github', 'agents', `${name}.agent.md`), 'utf8')).metadata;
}

test('all twelve approved routes, workflow entry points and local links validate', () => {
  assert.equal(validateOrchestration(root).profiles, 12);
});

for (const name of Object.keys(approvedRoutes)) {
  test(`${name} binds its exact approved model and reasoning`, () => {
    validateProfile(profile(name), name);
  });
}

test('required Astra modelling and Sol editing retain extra-high reasoning', () => {
  assert.deepEqual(approvedRoutes['vp-modelling'], ['gpt-6-astra', 'xhigh']);
  assert.deepEqual(approvedRoutes['vp-camtasia'], ['gpt-6.1-sol', 'xhigh']);
});

test('Auto, inherited models, fallback arrays and downgraded effort fail validation', () => {
  for (const model of ['auto', 'inherit', ['gpt-6-astra', 'gpt-6.1-sol'], undefined]) {
    assert.throws(() => validateProfile({ ...profile('vp-modelling'), model }, 'vp-modelling'));
  }
  assert.throws(() => validateProfile({
    ...profile('vp-modelling'), 'reasoning-effort': 'high',
  }, 'vp-modelling'));
});

test('coordinator cannot acquire shell, file-write or live MCP tools', () => {
  for (const tool of ['execute', 'edit', 'camtasia/*', 'bentley-mstn/*']) {
    const metadata = profile('vp-orchestrator');
    assert.throws(() => validateProfile({ ...metadata, tools: [...metadata.tools, tool] }, 'vp-orchestrator'));
  }
});

test('specialists cannot recursively delegate or acquire global wildcard tools', () => {
  const metadata = profile('vp-media');
  for (const tool of ['agent', '*']) {
    assert.throws(() => validateProfile({ ...metadata, tools: [...metadata.tools, tool] }, 'vp-media'));
  }
});

test('MicroStation roles cannot acquire shell or Camtasia access', () => {
  for (const name of ['vp-modelling', 'vp-camera', 'vp-geometry-qa']) {
    const metadata = profile(name);
    for (const tool of ['execute', 'camtasia/*']) {
      assert.throws(() => validateProfile({ ...metadata, tools: [...metadata.tools, tool] }, name));
    }
  }
});

test('capture and video QA cannot acquire broad Camtasia editing tools', () => {
  for (const name of ['vp-capture', 'vp-video-qa']) {
    const metadata = profile(name);
    for (const tool of ['camtasia/*', 'camtasia/camtasia_delete_clip']) {
      assert.throws(() => validateProfile({ ...metadata, tools: [...metadata.tools, tool] }, name));
    }
  }
});

test('duplicate keys, malformed frontmatter and unsupported syntax fail explicitly', () => {
  for (const text of [
    'No frontmatter',
    '---\nmodel: gpt-6-astra\nmodel: auto\n---\nBody',
    '---\ntools: [unquoted, values]\n---\nBody',
    '---\n  model: gpt-6-astra\n---\nBody',
  ]) {
    assert.throws(() => parseFrontmatter(text));
  }
});
