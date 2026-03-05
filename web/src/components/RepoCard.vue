<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
    <!-- Header -->
    <div class="flex items-start justify-between mb-3">
      <div class="flex-1">
        <a
          :href="repo.html_url || `https://github.com/${repo.full_name}`"
          target="_blank"
          rel="noopener noreferrer"
          class="text-lg font-semibold text-gray-900 hover:text-indigo-600 transition-colors"
        >
          {{ repo.full_name }}
        </a>
        <div class="flex items-center gap-3 mt-2 text-sm text-gray-600">
          <span v-if="repo.language" class="flex items-center gap-1">
            <span class="w-3 h-3 rounded-full" :style="{ backgroundColor: getLanguageColor(repo.language) }"></span>
            {{ repo.language }}
          </span>
          <span class="flex items-center gap-1">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>
            {{ formatNumber(repo.stars) }}
          </span>
          <span v-if="repo.stars_today" class="flex items-center gap-1 text-green-600">
            +{{ formatNumber(repo.stars_today) }} today
          </span>
          <span class="flex items-center gap-1">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
            {{ formatNumber(repo.forks) }}
          </span>
        </div>
      </div>
      <!-- Commercialization Score Badge -->
      <div v-if="repo.analysis?.shang_ye_hua_qian_li !== undefined" class="flex-shrink-0 ml-4">
        <div
          class="px-3 py-1 rounded-full text-sm font-semibold"
          :class="getPotentialClass(repo.analysis.shang_ye_hua_qian_li)"
        >
          {{ repo.analysis.shang_ye_hua_qian_li }}/5
        </div>
      </div>
    </div>

    <!-- Description -->
    <p v-if="repo.description" class="text-gray-700 text-sm mb-3 line-clamp-2">
      {{ repo.description }}
    </p>

    <!-- Analysis Summary -->
    <div v-if="repo.analysis" class="space-y-2 mb-4">
      <div class="text-sm">
        <span class="font-medium text-gray-700">功能定位：</span>
        <span class="text-gray-600">{{ repo.analysis.gong_neng_ding_wei }}</span>
      </div>
      <div class="text-sm">
        <span class="font-medium text-gray-700">目标客户：</span>
        <span class="text-gray-600">{{ repo.analysis.mu_biao_ke_hu }}</span>
      </div>
    </div>

    <!-- Topics -->
    <div v-if="repo.topics && repo.topics.length > 0" class="flex flex-wrap gap-2 mb-4">
      <span
        v-for="topic in repo.topics.slice(0, 5)"
        :key="topic"
        class="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
      >
        {{ topic }}
      </span>
    </div>

    <!-- Footer Actions -->
    <div class="flex items-center justify-between pt-3 border-t border-gray-100">
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <span v-if="repo.license">{{ repo.license }}</span>
      </div>
      <button
        @click="handleFavorite"
        :class="isFavorited ? 'text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50' : 'text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50'"
        class="px-3 py-1 text-sm rounded transition-colors flex items-center gap-1"
      >
        <svg class="w-4 h-4" :fill="isFavorited ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
        </svg>
        {{ isFavorited ? '已收藏' : '收藏' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFavoritesStore } from '../stores/favorites'
import type { Repo } from '../stores/reports'

const props = defineProps<{
  repo: Repo
}>()

const favoritesStore = useFavoritesStore()

const isFavorited = computed(() => favoritesStore.isFavorited(props.repo.full_name))

async function handleFavorite() {
  if (isFavorited.value) {
    await favoritesStore.removeFavorite(props.repo.full_name)
  } else {
    await favoritesStore.addFavorite(props.repo)
  }
}

function formatNumber(num: number): string {
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

function getPotentialClass(score: number): string {
  if (score >= 4) return 'bg-green-100 text-green-800'
  if (score >= 2) return 'bg-yellow-100 text-yellow-800'
  return 'bg-gray-100 text-gray-800'
}

function getLanguageColor(language: string): string {
  const colors: Record<string, string> = {
    JavaScript: '#f1e05a',
    TypeScript: '#3178c6',
    Python: '#3572A5',
    Java: '#b07219',
    Go: '#00ADD8',
    Rust: '#dea584',
    Ruby: '#701516',
    PHP: '#4F5D95',
    C: '#555555',
    'C++': '#f34b7d',
    'C#': '#178600',
    Swift: '#ffac45',
    Kotlin: '#A97BFF',
    Shell: '#89e051',
  }
  return colors[language] || '#8b949e'
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
