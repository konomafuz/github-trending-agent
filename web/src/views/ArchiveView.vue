<template>
  <div class="px-2 sm:px-0">
    <!-- Header -->
    <div class="mb-10 text-center sm:text-left mt-4 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
      <div>
        <h1 class="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-3">归档浏览</h1>
        <p class="text-slate-500 font-medium">按多个维度探索和筛选项目</p>
      </div>
      <div class="hidden sm:block text-slate-300">
        <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="reportsStore.loading" class="flex items-center justify-center py-20 min-h-[40vh]">
      <div class="text-center flex flex-col items-center">
        <div class="animate-spin rounded-full h-12 w-12 border-4 border-slate-100 border-t-indigo-600 mb-6 drop-shadow-sm"></div>
        <p class="text-slate-500 font-medium animate-pulse">加载中...</p>
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

    <!-- Two Column Layout -->
    <div v-else-if="reportsStore.data" class="grid grid-cols-1 lg:grid-cols-4 gap-8 pb-20">
      <!-- Left Sidebar: Category Tree -->
      <div class="lg:col-span-1">
        <div class="bg-white/50 backdrop-blur border border-white/50 rounded-2xl shadow-[0_2px_10px_rgb(0,0,0,0.02)] p-4 sticky top-24">
          <CategoryTree
            :category-groups="categoryGroups"
            @select="handleCategorySelect"
          />
        </div>
      </div>

      <!-- Right Content: Repo List -->
      <div class="lg:col-span-3">
        <!-- Results Header -->
        <div class="mb-6 flex items-center justify-between bg-white border border-slate-100 rounded-xl px-4 py-3 shadow-[0_2px_10px_rgb(0,0,0,0.01)]">
          <p class="text-sm font-medium text-slate-500">
            共找到 <span class="font-bold text-indigo-600">{{ filteredRepos.length }}</span> 个项目
          </p>
        </div>

        <!-- Repo Cards -->
        <div v-if="filteredRepos.length > 0" class="grid grid-cols-1 gap-6">
          <RepoCard
            v-for="repo in filteredRepos"
            :key="repo.full_name"
            :repo="repo"
          />
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-20 bg-white/50 backdrop-blur rounded-3xl border border-white/50 shadow-sm">
          <div class="text-slate-300 mb-4 flex justify-center">
            <svg class="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
          </div>
          <h3 class="text-lg font-medium text-slate-800 mb-1">没有符合条件的项目</h3>
          <p class="text-slate-500 text-sm">请尝试选择其他分类。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useReportsStore } from '../stores/reports'
import CategoryTree from '../components/CategoryTree.vue'
import RepoCard from '../components/RepoCard.vue'
import { getAllCategories } from '../utils/category'

const reportsStore = useReportsStore()
const selectedRepoNames = ref<Set<string>>(new Set())

onMounted(() => {
  if (!reportsStore.data) {
    reportsStore.fetchLatest()
  }
})

const categoryGroups = computed(() => {
  if (!reportsStore.data) return []
  return getAllCategories(reportsStore.data.repos)
})

const filteredRepos = computed(() => {
  if (!reportsStore.data) return []

  // If no categories selected, show all repos
  if (selectedRepoNames.value.size === 0) {
    return reportsStore.data.repos
  }

  // Filter repos by selected categories
  return reportsStore.data.repos.filter(repo =>
    selectedRepoNames.value.has(repo.full_name)
  )
})

function handleCategorySelect(repoNames: Set<string>) {
  selectedRepoNames.value = repoNames
}
</script>
