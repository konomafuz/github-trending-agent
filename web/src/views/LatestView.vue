<template>
  <div class="px-2 sm:px-0">
    <!-- Header -->
    <div class="mb-10 text-center sm:text-left mt-4 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
      <div>
        <h1 class="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-3">最新分析</h1>
        <p v-if="reportsStore.data" class="text-slate-500 font-medium">
          {{ reportsStore.data.date }} · 共 <span class="text-indigo-600 font-bold bg-indigo-50 px-2 py-0.5 rounded-md">{{ reportsStore.data.metadata.total }}</span> 个高潜力项目
        </p>
      </div>
      <!-- Optional: Add a decoration element -->
      <div class="hidden sm:block text-slate-300">
        <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="reportsStore.loading" class="flex items-center justify-center py-20 min-h-[40vh]">
      <div class="text-center flex flex-col items-center">
        <div class="animate-spin rounded-full h-12 w-12 border-4 border-slate-100 border-t-indigo-600 mb-6 drop-shadow-sm"></div>
        <p class="text-slate-500 font-medium animate-pulse">正在加载最新分析数据...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="reportsStore.error" class="bg-rose-50 border border-rose-100 rounded-2xl p-8 text-center max-w-lg mx-auto mt-10 shadow-sm">
      <div class="w-12 h-12 bg-rose-100 text-rose-500 rounded-full flex items-center justify-center mx-auto mb-4">
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
      </div>
      <p class="text-rose-800 font-medium mb-6">{{ reportsStore.error }}</p>
      <button
        @click="reportsStore.fetchLatest()"
        class="px-6 py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-medium rounded-full transition-all shadow-md shadow-rose-200"
      >
        重新加载
      </button>
    </div>

    <!-- Filter Bar & Repo List -->
    <div v-else-if="reportsStore.data">
      <FilterBar :repos="reportsStore.data.repos" @filter="handleFilter" />

      <div class="grid grid-cols-1 gap-6 pb-20">
        <RepoCard
          v-for="repo in displayedRepos"
          :key="repo.full_name"
          :repo="repo"
        />
      </div>
      
      <!-- Empty Search Result -->
      <div v-if="displayedRepos.length === 0" class="text-center py-20 bg-white/50 backdrop-blur rounded-3xl border border-white/50 shadow-sm">
        <div class="text-slate-300 mb-4 flex justify-center">
          <svg class="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <h3 class="text-lg font-medium text-slate-800 mb-1">没有找到符合条件的项目</h3>
        <p class="text-slate-500 text-sm">请尝试放宽筛选条件，或者清除过滤选项。</p>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-20 min-h-[40vh] flex flex-col items-center justify-center">
      <p class="text-slate-400 font-medium text-lg">暂无数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useReportsStore } from '../stores/reports'
import RepoCard from '../components/RepoCard.vue'
import FilterBar from '../components/FilterBar.vue'
import type { Repo } from '../stores/reports'

const reportsStore = useReportsStore()
const displayedRepos = ref<Repo[]>([])

onMounted(() => {
  reportsStore.fetchLatest()
})

function handleFilter(repos: Repo[]) {
  displayedRepos.value = repos
}
</script>
