<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">归档浏览</h1>
      <p class="text-gray-600">按多个维度探索和筛选项目</p>
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

    <!-- Two Column Layout -->
    <div v-else-if="reportsStore.data" class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Left Sidebar: Category Tree -->
      <div class="lg:col-span-1">
        <CategoryTree
          :category-groups="categoryGroups"
          @select="handleCategorySelect"
        />
      </div>

      <!-- Right Content: Repo List -->
      <div class="lg:col-span-3">
        <!-- Results Header -->
        <div class="mb-4 flex items-center justify-between">
          <p class="text-gray-600">
            显示 <span class="font-semibold text-gray-900">{{ filteredRepos.length }}</span> 个项目
          </p>
        </div>

        <!-- Repo Cards -->
        <div v-if="filteredRepos.length > 0" class="space-y-4">
          <RepoCard
            v-for="repo in filteredRepos"
            :key="repo.full_name"
            :repo="repo"
          />
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-12 bg-gray-50 rounded-lg">
          <p class="text-gray-500">没有符合条件的项目</p>
          <p class="text-sm text-gray-400 mt-2">尝试调整筛选条件</p>
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
import type { Repo } from '../stores/reports'

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
