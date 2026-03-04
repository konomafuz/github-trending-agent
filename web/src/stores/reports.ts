import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Repo {
  owner: string
  name: string
  full_name: string
  description: string
  language: string
  stars: number
  stars_today: number
  forks: number
  license: string
  topics: string[]
  readme_excerpt: string
  analysis: {
    gong_neng_ding_wei: string
    shang_ye_hua_qian_li: number
    jing_pin_saas: string
    er_ci_kai_fa: string[]
    mu_biao_ke_hu: string
    ji_shu_fu_za_du: string
    tui_jian_xing_dong: string
  }
}

export interface ReportData {
  latest: string
  date: string
  repos: Repo[]
  metadata: {
    total: number
    generated_at: string
  }
}

export const useReportsStore = defineStore('reports', () => {
  const data = ref<ReportData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchLatest() {
    loading.value = true
    error.value = null
    try {
      const basePath = import.meta.env.BASE_URL
      const response = await fetch(`${basePath}data/latest.json`)
      if (!response.ok) throw new Error('Failed to fetch data')
      data.value = await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetchLatest }
})

