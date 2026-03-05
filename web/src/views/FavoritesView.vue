<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">我的收藏</h1>
      <p class="text-gray-600">管理您收藏的项目</p>
    </div>

    <!-- Not Authenticated -->
    <div v-if="!authStore.isAuthenticated" class="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
      <svg class="w-16 h-16 mx-auto mb-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
      </svg>
      <h3 class="text-lg font-semibold text-gray-900 mb-2">需要登录</h3>
      <p class="text-gray-600 mb-4">登录后可以收藏项目并在多设备间同步</p>
      <p class="text-sm text-gray-500">点击右上角的"GitHub 登录"按钮开始使用</p>
    </div>

    <!-- Authenticated -->
    <div v-else>
      <!-- Loading -->
      <div v-if="favoritesStore.loading" class="flex items-center justify-center py-12">
        <div class="text-center">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p class="text-gray-600">加载中...</p>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="favoritesStore.favorites.length === 0" class="text-center py-12 bg-gray-50 rounded-lg">
        <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
        </svg>
        <p class="text-gray-500 mb-2">还没有收藏任何项目</p>
        <p class="text-sm text-gray-400">在"最新"或"归档"页面点击收藏按钮添加项目</p>
      </div>

      <!-- Favorites List -->
      <div v-else class="space-y-4">
        <div
          v-for="favorite in sortedFavorites"
          :key="favorite.full_name"
          class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex-1">
              <a
                :href="`https://github.com/${favorite.full_name}`"
                target="_blank"
                rel="noopener noreferrer"
                class="text-lg font-semibold text-gray-900 hover:text-indigo-600 transition-colors"
              >
                {{ favorite.full_name }}
              </a>
              <p class="text-sm text-gray-500 mt-1">
                收藏于 {{ formatDate(favorite.starred_at) }}
              </p>
            </div>
            <button
              @click="handleRemove(favorite.full_name)"
              class="text-red-600 hover:text-red-700 hover:bg-red-50 p-2 rounded transition-colors"
              title="取消收藏"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>

          <!-- Note -->
          <div v-if="favorite.note" class="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-gray-700">
            <span class="font-medium">笔记：</span>{{ favorite.note }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useFavoritesStore } from '../stores/favorites'

const authStore = useAuthStore()
const favoritesStore = useFavoritesStore()

onMounted(async () => {
  await favoritesStore.init()
})

const sortedFavorites = computed(() => {
  return [...favoritesStore.favorites].sort((a, b) =>
    new Date(b.starred_at).getTime() - new Date(a.starred_at).getTime()
  )
})

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

async function handleRemove(fullName: string) {
  if (confirm('确定要取消收藏这个项目吗？')) {
    await favoritesStore.removeFavorite(fullName)
  }
}
</script>
