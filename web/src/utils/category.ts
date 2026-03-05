import type { Repo } from '../stores/reports'

export interface Category {
  id: string
  label: string
  count: number
  repos: string[] // full_name list
}

export interface CategoryGroup {
  id: string
  label: string
  categories: Category[]
}

/**
 * Categorize repos by commercialization potential
 */
export function categorizeByPotential(repos: Repo[]): CategoryGroup {
  const high: string[] = []
  const medium: string[] = []
  const low: string[] = []

  repos.forEach(repo => {
    const score = repo.analysis?.shang_ye_hua_qian_li
    if (score === undefined) {
      low.push(repo.full_name)
    } else if (score >= 4) {
      high.push(repo.full_name)
    } else if (score >= 2) {
      medium.push(repo.full_name)
    } else {
      low.push(repo.full_name)
    }
  })

  return {
    id: 'potential',
    label: '商业化潜力',
    categories: [
      { id: 'high', label: '🔥 高潜力 (4-5分)', count: high.length, repos: high },
      { id: 'medium', label: '💡 中等潜力 (2-3分)', count: medium.length, repos: medium },
      { id: 'low', label: '📊 观察中 (0-1分)', count: low.length, repos: low },
    ]
  }
}

/**
 * Categorize repos by target customer
 */
export function categorizeByCustomer(repos: Repo[]): CategoryGroup {
  const categories = new Map<string, string[]>([
    ['developers', []],
    ['enterprise', []],
    ['ai-ml', []],
    ['consumer', []],
    ['infrastructure', []],
    ['other', []]
  ])

  repos.forEach(repo => {
    const customer = repo.analysis?.mu_biao_ke_hu?.toLowerCase() || ''
    let matched = false

    if (customer.includes('开发者') || customer.includes('程序员')) {
      categories.get('developers')!.push(repo.full_name)
      matched = true
    }
    if (customer.includes('企业') || customer.includes('公司') || customer.includes('团队')) {
      categories.get('enterprise')!.push(repo.full_name)
      matched = true
    }
    if (customer.includes('ai') || customer.includes('机器学习') || customer.includes('人工智能')) {
      categories.get('ai-ml')!.push(repo.full_name)
      matched = true
    }
    if (customer.includes('消费者') || customer.includes('用户') || customer.includes('个人')) {
      categories.get('consumer')!.push(repo.full_name)
      matched = true
    }
    if (customer.includes('基础设施') || customer.includes('运维') || customer.includes('devops')) {
      categories.get('infrastructure')!.push(repo.full_name)
      matched = true
    }
    if (!matched) {
      categories.get('other')!.push(repo.full_name)
    }
  })

  return {
    id: 'customer',
    label: '目标客户',
    categories: [
      { id: 'developers', label: '👨‍💻 开发者工具', count: categories.get('developers')!.length, repos: categories.get('developers')! },
      { id: 'enterprise', label: '🏢 企业服务', count: categories.get('enterprise')!.length, repos: categories.get('enterprise')! },
      { id: 'ai-ml', label: '🤖 AI/ML 应用', count: categories.get('ai-ml')!.length, repos: categories.get('ai-ml')! },
      { id: 'consumer', label: '📱 消费者应用', count: categories.get('consumer')!.length, repos: categories.get('consumer')! },
      { id: 'infrastructure', label: '🔧 基础设施', count: categories.get('infrastructure')!.length, repos: categories.get('infrastructure')! },
      { id: 'other', label: '📦 其他', count: categories.get('other')!.length, repos: categories.get('other')! },
    ].filter(c => c.count > 0)
  }
}

/**
 * Categorize repos by programming language
 */
export function categorizeByLanguage(repos: Repo[]): CategoryGroup {
  const languageMap = new Map<string, string[]>()

  repos.forEach(repo => {
    const lang = repo.language || 'Unknown'
    if (!languageMap.has(lang)) {
      languageMap.set(lang, [])
    }
    languageMap.get(lang)!.push(repo.full_name)
  })

  const categories = Array.from(languageMap.entries())
    .map(([lang, repos]) => ({
      id: lang.toLowerCase().replace(/[^a-z0-9]/g, '-'),
      label: lang,
      count: repos.length,
      repos
    }))
    .sort((a, b) => b.count - a.count)

  return {
    id: 'language',
    label: '编程语言',
    categories
  }
}

/**
 * Categorize repos by stars popularity
 */
export function categorizeByStars(repos: Repo[]): CategoryGroup {
  const ultra: string[] = []
  const hot: string[] = []
  const popular: string[] = []
  const emerging: string[] = []

  repos.forEach(repo => {
    if (repo.stars >= 50000) {
      ultra.push(repo.full_name)
    } else if (repo.stars >= 10000) {
      hot.push(repo.full_name)
    } else if (repo.stars >= 5000) {
      popular.push(repo.full_name)
    } else {
      emerging.push(repo.full_name)
    }
  })

  return {
    id: 'stars',
    label: 'Stars 热度',
    categories: [
      { id: 'ultra', label: '🌟 超热门 (50k+)', count: ultra.length, repos: ultra },
      { id: 'hot', label: '⭐ 热门 (10k-50k)', count: hot.length, repos: hot },
      { id: 'popular', label: '✨ 流行 (5k-10k)', count: popular.length, repos: popular },
      { id: 'emerging', label: '💫 新兴 (1k-5k)', count: emerging.length, repos: emerging },
    ].filter(c => c.count > 0)
  }
}

/**
 * Categorize repos by technical complexity
 */
export function categorizeByComplexity(repos: Repo[]): CategoryGroup {
  const simple: string[] = []
  const medium: string[] = []
  const complex: string[] = []

  repos.forEach(repo => {
    const complexity = repo.analysis?.ji_shu_fu_za_du?.toLowerCase() || ''
    if (complexity.includes('简单') || complexity.includes('易')) {
      simple.push(repo.full_name)
    } else if (complexity.includes('复杂') || complexity.includes('困难') || complexity.includes('陡峭')) {
      complex.push(repo.full_name)
    } else {
      medium.push(repo.full_name)
    }
  })

  return {
    id: 'complexity',
    label: '技术复杂度',
    categories: [
      { id: 'simple', label: '🟢 简单', count: simple.length, repos: simple },
      { id: 'medium', label: '🟡 中等', count: medium.length, repos: medium },
      { id: 'complex', label: '🔴 复杂', count: complex.length, repos: complex },
    ].filter(c => c.count > 0)
  }
}

/**
 * Get all category groups
 */
export function getAllCategories(repos: Repo[]): CategoryGroup[] {
  return [
    categorizeByPotential(repos),
    categorizeByCustomer(repos),
    categorizeByLanguage(repos),
    categorizeByStars(repos),
    categorizeByComplexity(repos),
  ]
}
