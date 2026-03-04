<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
    <!-- Header -->
    <div class="flex items-start justify-between mb-3">
      <div class="flex-1">
        <a
          :href="`https://github.com/${repo.full_name}`"
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
            ⭐ {{ formatNumber(repo.stars) }}
          </span>
          <span v-if="repo.stars_today" class="flex items-center gap-1 text-green-600">
            +{{ formatNumber(repo.stars_today) }} today
          </span>
          <span class="flex items-center gap-1">
            🍴 {{ formatNumber(repo.forks) }}
          </span>
        </div>
      </div>
      <!-- Commercialization Score Badge -->
      <div v-if="repo.analysis?.shang_ye_hua_qian_li" class="flex-shrink-0 ml-4">
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
        class="px-3 py-1 text-sm text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 rounded transition-colors"
        @click="$emit('favorite', repo)"
      >
        ⭐ 收藏
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Repo } from '../stores/reports'

defineProps<{
  repo: Repo
}>()

defineEmits<{
  favorite: [repo: Repo]
}>()

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
