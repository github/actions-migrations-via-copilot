const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const { test } = require('node:test')
const { resolveMigrationSkills } = require('./migration-targets')
const submitRepositories = require('./submit-repositories')
const loadConfig = require('./load-config')
const createRepoVars = require('./create-repo-vars')

const expectedSkills = {
  'Azure DevOps': 'azure-devops-migration',
  Bamboo: 'bamboo-migration',
  Bitbucket: 'bitbucket-migration',
  CircleCI: 'circleci-migration',
  DroneCI: 'droneci-migration',
  GitLab: 'gitlab-migration',
  Jenkins: 'jenkins-migration',
  'Travis CI': 'travisci-migration',
}

test('accepts all eight explicit platform skills as objects or JSON', () => {
  assert.deepEqual(resolveMigrationSkills({ skills: expectedSkills }), expectedSkills)
  assert.deepEqual(resolveMigrationSkills({ skills: JSON.stringify(expectedSkills) }), expectedSkills)
})

test('translates known legacy filenames without reading prompt files', () => {
  const prompts = Object.fromEntries(Object.entries(expectedSkills).map(
    ([platform, skill]) => [platform, skill.replace(/-migration$/, '-migrator.md')]
  ))
  const warnings = []
  assert.deepEqual(resolveMigrationSkills({ prompts, warn: (message) => warnings.push(message) }), expectedSkills)
  assert.equal(warnings.length, 1)
  assert.match(warnings[0], /deprecated/)
})

test('accepts equivalent mappings but rejects conflicts and different platform sets', () => {
  assert.deepEqual(resolveMigrationSkills({
    skills: { Jenkins: 'jenkins-migration' },
    prompts: { Jenkins: 'jenkins-migrator.md' },
  }), { Jenkins: 'jenkins-migration' })
  assert.throws(() => resolveMigrationSkills({
    skills: expectedSkills,
    prompts: { Jenkins: 'jenkins-migrator.md' },
  }), /Conflicting/)
})

test('rejects missing, empty, malformed, and unsupported mappings', () => {
  assert.throws(() => resolveMigrationSkills({}), /Configure/)
  for (const skills of [null, {}, [], 'null', '[]', '', '{', 42, { Unknown: 'jenkins-migration' },
    { Jenkins: 'gitlab-migration' }, { Jenkins: '../jenkins-migration' },
    { Jenkins: 'jenkins-migrator.md' }]) {
    assert.throws(() => resolveMigrationSkills({ skills }))
  }
  for (const target of ['../../Jenkinsfile', 'custom-agent.md', 'jenkins-migration', null]) {
    assert.throws(() => resolveMigrationSkills({ prompts: { Jenkins: target } }))
  }
})

const submissionFixture = ({ repositories = [{ name: 'app', default_branch: 'develop' }], rejectIssue = false, env = {} } = {}) => {
  const calls = { searches: [], issues: [], properties: [], failures: [], warnings: [], auth: [] }
  const github = {
    rest: { search: { repos: 'search-repos' } },
    paginate: async (route, options) => {
      calls.searches.push({ route, options })
      return repositories
    },
    request: async (route, input) => { calls.properties.push({ route, input }) },
    constructor: class {
      constructor(options) { calls.auth.push(options) }
      async request(route, input) {
        calls.issues.push({ route, input })
        if (rejectIssue) throw new Error('Assignment rejected')
        return { data: { number: 10 } }
      }
    },
  }
  const options = {
    github,
    core: {
      info: () => {},
      warning: (message) => calls.warnings.push(message),
      setFailed: (message) => calls.failures.push(message),
    },
    process: { env: {
      MIGRATION_TYPE_SKILLS: JSON.stringify({ Jenkins: 'jenkins-migration' }),
      ISSUE_SUBMIT_TOKEN: 'synthetic-issue-token',
      ...env,
    } },
    org: 'test-org',
    batchSize: 1,
  }
  return { calls, options }
}

test('submits a short skill task with the default agent and correct user token', async () => {
  const { calls, options } = submissionFixture()
  const result = await submitRepositories(options)
  assert.equal(result.processedRepositories, 1)
  assert.equal(calls.issues.length, 1)
  const request = calls.issues[0].input
  assert.deepEqual(request.agent_assignment, { target_repo: 'test-org/app', base_branch: 'develop' })
  assert.deepEqual(request.assignees, ['copilot-swe-agent[bot]'])
  assert.deepEqual(calls.auth, [{ auth: 'synthetic-issue-token' }])
  assert.match(request.body, /migration-core, jenkins-migration, and actionlint/)
  assert.match(request.body, /stop without migration edits/)
  assert.doesNotMatch(request.body, /readPromptFile|MY_ORGANIZATION|knowledge\//)
  assert.ok(request.body.length < 1200)
  assert.equal(calls.properties.length, 1)
  assert.deepEqual(calls.properties[0].input.properties, [{ property_name: 'GH_MIGRATION_TYPE', value: 'None' }])
})

test('accepts legacy config without needing a checkout or prompt files', async () => {
  const { calls, options } = submissionFixture({ env: {
    MIGRATION_TYPE_SKILLS: '',
    MIGRATION_TYPE_PROMPTS: '{"Jenkins":"jenkins-migrator.md"}',
  } })
  await submitRepositories(options)
  assert.equal(calls.issues.length, 1)
  assert.ok(calls.warnings.some((message) => message.includes('deprecated')))
})

test('rejects malformed config before any repository search or issue creation', async () => {
  const { calls, options } = submissionFixture({ env: { MIGRATION_TYPE_SKILLS: '{' } })
  await assert.rejects(submitRepositories(options), /valid JSON/)
  assert.equal(calls.searches.length, 0)
  assert.equal(calls.issues.length, 0)
  assert.equal(calls.properties.length, 0)
})

test('failed assignments retain migration flags and are not counted as submitted', async () => {
  const { calls, options } = submissionFixture({ rejectIssue: true })
  const result = await submitRepositories(options)
  assert.equal(result.processedRepositories, 0)
  assert.equal(result.failedRepositories, 1)
  assert.deepEqual(result.repositoryNames, [])
  assert.equal(calls.properties.length, 0)
  assert.equal(calls.failures.length, 1)
})

test('honors batch limits and default branches', async () => {
  const { calls, options } = submissionFixture({ repositories: [{ name: 'first' }, { name: 'second' }] })
  await submitRepositories(options)
  assert.equal(calls.issues.length, 1)
  assert.equal(calls.issues[0].input.repo, 'first')
  assert.equal(calls.issues[0].input.agent_assignment.base_branch, 'main')
})

test('empty searches create no issues; missing credentials fail before writes', async () => {
  const empty = submissionFixture({ repositories: [] })
  assert.equal((await submitRepositories(empty.options)).processedRepositories, 0)
  assert.equal(empty.calls.issues.length, 0)
  const missingToken = submissionFixture({ env: { ISSUE_SUBMIT_TOKEN: '' } })
  await assert.rejects(submitRepositories(missingToken.options), /ISSUE_SUBMIT_TOKEN/)
  assert.equal(missingToken.calls.issues.length, 0)
  assert.equal(missingToken.calls.properties.length, 0)
})

test('rejects invalid batch sizes before searching', async () => {
  for (const batchSize of [0, -1, 1.5, NaN, '2']) {
    const { calls, options } = submissionFixture()
    await assert.rejects(submitRepositories({ ...options, batchSize }), /positive integer/)
    assert.equal(calls.searches.length, 0)
  }
})

const configFixture = (mapping) => ({
  gh_app_id: '123',
  gh_migration_type: { default_value: 'None' },
  organizations: ['test-org'],
  ...mapping,
})

test('configuration loader normalizes current and legacy mappings', async () => {
  for (const mapping of [
    { migration_type_skills: { Jenkins: 'jenkins-migration' } },
    { migration_type_prompts: { Jenkins: 'jenkins-migrator.md' } },
  ]) {
    const outputs = []
    const config = await loadConfig({
      core: { info: () => {}, warning: () => {}, setFailed: assert.fail, setOutput: (key, value) => outputs.push({ key, value }) },
      fs: { readFileSync: () => 'fixture' },
      yaml: { load: () => configFixture(mapping) },
    })
    assert.deepEqual(config.migration_type_skills, { Jenkins: 'jenkins-migration' })
    assert.equal(outputs.length, 1)
    assert.deepEqual(JSON.parse(outputs[0].value), config)
  }
})

test('configuration loader rejects invalid mappings without emitting config', async () => {
  const outputs = []
  await assert.rejects(loadConfig({
    core: { info: () => {}, warning: () => {}, setFailed: () => {}, setOutput: (...args) => outputs.push(args) },
    fs: { readFileSync: () => 'fixture' },
    yaml: { load: () => configFixture({ migration_type_skills: { Jenkins: 'wrong' } }) },
  }), /must map to/)
  assert.equal(outputs.length, 0)
})

test('repository setup writes normalized skill variables on create and update', async () => {
  for (const existing of [false, true]) {
    const writes = []
    await createRepoVars({
      github: { rest: { actions: {
        createRepoVariable: async (input) => {
          if (existing) throw Object.assign(new Error('Exists'), { status: 409 })
          writes.push(input)
        },
        updateRepoVariable: async (input) => writes.push(input),
      } } },
      context: { repo: { owner: 'test-org', repo: 'control' } },
      core: { info: () => {}, warning: () => {}, setFailed: assert.fail },
      config: configFixture({ migration_type_prompts: { Jenkins: 'jenkins-migrator.md' } }),
    })
    const skillVariable = writes.find((entry) => entry.name === 'MIGRATION_TYPE_SKILLS')
    assert.deepEqual(JSON.parse(skillVariable.value), { Jenkins: 'jenkins-migration' })
    assert.equal(writes.length, 4)
    assert.ok(writes.every((entry) => entry.name !== 'MIGRATION_TYPE_PROMPTS'))
  }
})

test('invalid configuration writes no repository variables', async () => {
  const writes = []
  await assert.rejects(createRepoVars({
    github: { rest: { actions: { createRepoVariable: async (input) => writes.push(input) } } },
    context: { repo: { owner: 'test-org', repo: 'control' } },
    core: { info: () => {}, warning: () => {}, setFailed: () => {} },
    config: configFixture({ migration_type_skills: {} }),
  }), /non-empty/)
  assert.equal(writes.length, 0)
})

test('configured skills and bundled Markdown references exist in the package', () => {
  const root = path.resolve(__dirname, '../..')
  const files = ['SKILL.md', 'workflow.md', 'standards.md', 'guardrails.md'].map(
    (name) => path.join(root, 'plugin/skills/migration-core', name)
  )
  for (const skill of Object.values(expectedSkills)) {
    const directory = path.join(root, 'plugin/skills', skill)
    const entry = fs.readFileSync(path.join(directory, 'SKILL.md'), 'utf8')
    assert.ok(entry.includes(`name: ${skill}\n`), `Declared skill name must match ${skill}`)
    files.push(path.join(directory, 'SKILL.md'), path.join(directory, 'secrets.md'))
  }
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8')
    for (const match of text.matchAll(/\]\(([^\s()]+\.md)(?:#[^)]*)?\)/g)) {
      const target = match[1]
      if (/^https?:/.test(target)) continue
      assert.ok(fs.existsSync(path.resolve(path.dirname(file), target)), `${file}: missing ${target}`)
    }
  }
})