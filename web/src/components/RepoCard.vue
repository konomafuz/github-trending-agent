<template>
  <div class="group bg-white rounded-2xl shadow-[0_2px_10px_rgb(0,0,0,0.02)] border border-slate-100 p-6 sm:p-8 hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] hover:border-indigo-100 transition-all duration-300 relative overflow-hidden">
    <!-- Optional gentle gradient background bloop -->
    <div class="absolute -top-10 -right-10 w-32 h-32 bg-indigo-50 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

    <!-- Header -->
    <div class="flex items-start justify-between mb-4 relative z-10">
      <div class="flex-1">
        <a
          :href="repo.html_url || `https://github.com/${repo.full_name}`"
          target="_blank"
          rel="noopener noreferrer"
          class="text-xl font-bold text-slate-900 group-hover:text-indigo-600 transition-colors flex items-center gap-2"
        >
          {{ repo.full_name }}
          <svg class="w-4 h-4 opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
        </a>
        
        <div class="flex flex-wrap items-center gap-4 mt-3 text-sm font-medium text-slate-500">
          <span v-if="repo.language" class="flex items-center gap-1.5 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-100">
            <span class="w-2.5 h-2.5 rounded-full shadow-sm" :style="{ backgroundColor: getLanguageColor(repo.language) }"></span>
            {{ repo.language }}
          </span>
          <span class="flex items-center gap-1.5">
            <svg class="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>
            {{ formatNumber(repo.stars) }}
          </span>
          <span v-if="repo.stars_today" class="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
            {{ formatNumber(repo.stars_today) }} today
          </span>
          <span class="flex items-center gap-1">
            <svg class="w-4 h-4 text-slate-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
            {{ formatNumber(repo.forks) }}
          </span>
        </div>
      </div>
      
      <!-- Commercialization Score Badge -->
      <div v-if="repo.analysis?.shang_ye_hua_qian_li !== undefined" class="flex-shrink-0 ml-4 relative z-10 flex flex-col items-center">
        <div class="text-xs text-slate-400 font-medium mb-1 tracking-wider uppercase">潜力指数</div>
        <div
          class="px-3 py-1 rounded-full text-sm font-bold tracking-wide border"
          :class="getPotentialClass(repo.analysis.shang_ye_hua_qian_li)"
        >
          {{ repo.analysis.shang_ye_hua_qian_li }} / 5
        </div>
      </div>
    </div>

    <!-- Description -->
    <p v-if="repo.description" class="text-slate-600 text-[15px] leading-relaxed mb-5 line-clamp-2 relative z-10">
      {{ repo.description }}
    </p>

    <!-- Analysis Summary (The Premium Part) -->
    <div v-if="repo.analysis" class="bg-gradient-to-r from-slate-50 to-white border border-slate-100/50 rounded-xl p-4 mb-5 space-y-3 relative z-10">
      <div class="flex items-start gap-3">
        <div class="mt-0.5 bg-indigo-100 p-1 rounded">
          <svg class="w-3.5 h-3.5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
        </div>
        <div>
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">功能定位</span>
          <span class="text-sm font-medium text-slate-700 leading-snug">{{ repo.analysis.gong_neng_ding_wei }}</span>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <div class="mt-0.5 bg-purple-100 p-1 rounded">
          <svg class="w-3.5 h-3.5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
        </div>
        <div>
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">目标客户</span>
          <span class="text-sm font-medium text-slate-700 leading-snug">{{ repo.analysis.mu_biao_ke_hu }}</span>
        </div>
      </div>
    </div>

    <!-- Topics -->
    <div v-if="repo.topics && repo.topics.length > 0" class="flex flex-wrap gap-2 mb-5 relative z-10">
      <span
        v-for="topic in repo.topics.slice(0, 5)"
        :key="topic"
        class="px-2.5 py-1 bg-white border border-slate-200 text-slate-500 text-[11px] font-medium rounded-full shadow-sm hover:border-indigo-200 hover:text-indigo-600 cursor-default transition-colors"
      >
        #{{ topic }}
      </span>
    </div>

    <!-- Footer Actions -->
    <div class="flex items-center justify-between pt-4 border-t border-slate-100 relative z-10">
      <div class="flex items-center gap-2 text-xs font-medium text-slate-400">
        <span v-if="repo.license" class="flex items-center gap-1">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
          {{ repo.license }}
        </span>
      </div>
      <button
        @click="handleFavorite"
        :class="isFavorited ? 'text-amber-500 bg-amber-50 hover:bg-amber-100 border-amber-200' : 'text-slate-500 bg-white hover:text-indigo-600 hover:bg-indigo-50 border-slate-200 hover:border-indigo-200'"
        class="px-4 py-1.5 text-sm font-medium rounded-full border shadow-sm transition-all flex items-center gap-1.5"
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
  if (score >= 4) return 'bg-gradient-to-r from-emerald-400 to-emerald-500 text-white shadow-sm border-transparent'
  if (score >= 2) return 'bg-gradient-to-r from-amber-400 to-amber-500 text-white shadow-sm border-transparent'
  return 'bg-slate-100 text-slate-500 border-slate-200'
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
