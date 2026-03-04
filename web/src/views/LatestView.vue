<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">最新分析</h1>
      <p v-if="reportsStore.data" class="text-gray-600">
        {{ reportsStore.data.date }} · 共 {{ reportsStore.data.metadata.total }} 个项目
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="reportsStore.loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
        <p class="text-gray-600">加载中...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="reportsStore.error" class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
      <p class="text-red-800 mb-4">{{ reportsStore.error }}</p>
      <button
        @click="reportsStore.fetchLatest()"
        class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
      >
        重试
      </button>
    </div>

    <!-- Filter Bar & Repo List -->
    <div v-else-if="reportsStore.data">
      <FilterBar :repos="reportsStore.data.repos" @filter="handleFilter" />

      <div class="space-y-4">
        <RepoCard
          v-for="repo in displayedRepos"
          :key="repo.full_name"
          :repo="repo"
          @favorite="handleFavorite"
        />
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12 text-gray-500">
      暂无数据
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

function handleFavorite(repo: Repo) {
  // TODO: Implement favorites functionality
  console.log('Favorite:', repo.full_name)
}
</script>
