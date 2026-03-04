<template>
  <nav class="bg-white shadow-sm border-b">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex">
          <div class="flex-shrink-0 flex items-center">
            <h1 class="text-xl font-bold text-gray-900">
              GitHub Trending 商业化分析
            </h1>
          </div>
          <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
            <router-link
              to="/"
              class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              :class="isActive('/') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'"
            >
              最新
            </router-link>
            <router-link
              to="/archive"
              class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              :class="isActive('/archive') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'"
            >
              归档
            </router-link>
            <router-link
              to="/favorites"
              class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              :class="isActive('/favorites') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'"
            >
              收藏
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
const isActive = (path: string) => route.path === path
</script>

