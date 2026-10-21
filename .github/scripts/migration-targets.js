const PLATFORM_SKILLS = Object.freeze({
  'Azure DevOps': 'azure-devops-migration',
  Bamboo: 'bamboo-migration',
  Bitbucket: 'bitbucket-migration',
  CircleCI: 'circleci-migration',
  DroneCI: 'droneci-migration',
  GitLab: 'gitlab-migration',
  Jenkins: 'jenkins-migration',
  'Travis CI': 'travisci-migration',
})

const validateMapping = (input, name, legacy) => {
  let mapping = input
  if (typeof input === 'string') {
    try {
      mapping = JSON.parse(input)
    } catch {
      throw new Error(`${name} must contain a valid JSON object`)
    }
  }

  if (!mapping || typeof mapping !== 'object' || Array.isArray(mapping) ||
      Object.keys(mapping).length === 0) {
    throw new Error(`${name} must be a non-empty platform mapping`)
  }

  const resolved = {}
  for (const [platform, target] of Object.entries(mapping)) {
    if (!Object.hasOwn(PLATFORM_SKILLS, platform)) {
      throw new Error(`Unsupported migration platform: ${platform}`)
    }
    const skill = PLATFORM_SKILLS[platform]
    const expected = legacy ? skill.replace(/-migration$/, '-migrator.md') : skill
    if (target !== expected) {
      throw new Error(`${name}: ${platform} must map to ${expected}`)
    }
    resolved[platform] = skill
  }
  return resolved
}

const resolveMigrationSkills = ({ skills, prompts, warn = () => {} }) => {
  const current = skills === undefined ? undefined :
    validateMapping(skills, 'migration_type_skills / MIGRATION_TYPE_SKILLS', false)
  const legacy = prompts === undefined ? undefined :
    validateMapping(prompts, 'migration_type_prompts / MIGRATION_TYPE_PROMPTS', true)

  if (!current && !legacy) {
    throw new Error('Configure migration_type_skills / MIGRATION_TYPE_SKILLS before submitting migrations')
  }
  if (current && legacy) {
    const platforms = Object.keys(current)
    if (platforms.length !== Object.keys(legacy).length ||
        platforms.some((platform) => current[platform] !== legacy[platform])) {
      throw new Error('Conflicting skill and legacy prompt mappings; update or remove the legacy mapping')
    }
  }
  if (legacy) {
    warn('Legacy prompt mappings are deprecated; use migration_type_skills / MIGRATION_TYPE_SKILLS. Legacy values select installed skills, not prompt files.')
  }
  return current || legacy
}

module.exports = { resolveMigrationSkills }