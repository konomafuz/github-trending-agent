<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Language Filter -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          编程语言
        </label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="lang in availableLanguages"
            :key="lang"
            @click="toggleLanguage(lang)"
            class="px-3 py-1 text-sm rounded-full transition-colors"
            :class="selectedLanguages.includes(lang)
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
          >
            {{ lang }}
          </button>
        </div>
      </div>

      <!-- Stars Range Filter -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Stars 范围: {{ formatNumber(starsRange[0]) }} - {{ formatNumber(starsRange[1]) }}
        </label>
        <div class="flex items-center gap-4">
          <input
            type="range"
            v-model.number="starsRange[0]"
            :min="minStars"
            :max="maxStars"
            :step="1000"
            class="flex-1"
          />
          <input
            type="range"
            v-model.number="starsRange[1]"
            :min="minStars"
            :max="maxStars"
            :step="1000"
            class="flex-1"
          />
        </div>
      </div>
    </div>

    <!-- Active Filters & Clear -->
    <div v-if="hasActiveFilters" class="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
      <div class="text-sm text-gray-600">
        {{ filteredCount }} 个项目符合条件
      </div>
      <button
        @click="clearFilters"
        class="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
      >
        清除筛选
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Repo } from '../stores/reports'

const props = defineProps<{
  repos: Repo[]
}>()

const emit = defineEmits<{
  filter: [repos: Repo[]]
}>()

// Available languages from repos
const availableLanguages = computed(() => {
  const languages = new Set(props.repos.map(r => r.language).filter(Boolean))
  return Array.from(languages).sort()
})

// Filter state
const selectedLanguages = ref<string[]>([])
const minStars = computed(() => Math.min(...props.repos.map(r => r.stars)))
const maxStars = computed(() => Math.max(...props.repos.map(r => r.stars)))
const starsRange = ref<[number, number]>([minStars.value, maxStars.value])

// Update range when repos change
watch(() => props.repos, () => {
  starsRange.value = [minStars.value, maxStars.value]
}, { immediate: true })

// Filtered repos
const filteredRepos = computed(() => {
  return props.repos.filter(repo => {
    // Language filter
    if (selectedLanguages.value.length > 0 && !selectedLanguages.value.includes(repo.language)) {
      return false
    }
    // Stars range filter
    if (repo.stars < starsRange.value[0] || repo.stars > starsRange.value[1]) {
      return false
    }
    return true
  })
})

const filteredCount = computed(() => filteredRepos.value.length)
const hasActiveFilters = computed(() =>
  selectedLanguages.value.length > 0 ||
  starsRange.value[0] !== minStars.value ||
  starsRange.value[1] !== maxStars.value
)

// Emit filtered repos when filters change
watch(filteredRepos, (repos) => {
  emit('filter', repos)
}, { immediate: true })

function toggleLanguage(lang: string) {
  const index = selectedLanguages.value.indexOf(lang)
  if (index > -1) {
    selectedLanguages.value.splice(index, 1)
  } else {
    selectedLanguages.value.push(lang)
  }
}

function clearFilters() {
  selectedLanguages.value = []
  starsRange.value = [minStars.value, maxStars.value]
}

function formatNumber(num: number): string {
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}
</script>
