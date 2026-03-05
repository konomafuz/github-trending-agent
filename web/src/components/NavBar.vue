<template>
  <nav class="fixed top-0 left-0 right-0 z-50 flex justify-center mt-0 sm:mt-4 px-0 sm:px-4">
    <div class="w-full max-w-[1000px] bg-white/70 backdrop-blur-md rounded-none sm:rounded-2xl border border-white/20 shadow-[0_8px_30px_rgb(0,0,0,0.04)] px-4 sm:px-6 py-2 flex items-center justify-between transition-all duration-300">
      
      <!-- Brand & Links -->
      <div class="flex items-center gap-8">
        <h1 class="text-lg sm:text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent transform transition hover:scale-105">
          GitHub Trending
        </h1>
        
        <div class="hidden md:flex items-center space-x-1 border border-slate-200/50 bg-slate-100/50 rounded-full p-1">
          <router-link
            to="/"
            class="px-4 py-1.5 rounded-full text-sm font-medium transition-all"
            :class="isActive('/') ? 'bg-white shadow-sm text-indigo-700' : 'text-slate-500 hover:text-slate-800'"
          >
            最新
          </router-link>
          <router-link
            to="/archive"
            class="px-4 py-1.5 rounded-full text-sm font-medium transition-all"
            :class="isActive('/archive') ? 'bg-white shadow-sm text-indigo-700' : 'text-slate-500 hover:text-slate-800'"
          >
            归档
          </router-link>
          <router-link
            to="/favorites"
            class="px-4 py-1.5 rounded-full text-sm font-medium transition-all"
            :class="isActive('/favorites') ? 'bg-white shadow-sm text-indigo-700' : 'text-slate-500 hover:text-slate-800'"
          >
            收藏
          </router-link>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-3">
        <div class="md:hidden flex items-center space-x-2 mr-2">
          <router-link to="/" class="text-sm font-medium" :class="isActive('/') ? 'text-indigo-600' : 'text-slate-500'">最新</router-link>
          <router-link to="/archive" class="text-sm font-medium" :class="isActive('/archive') ? 'text-indigo-600' : 'text-slate-500'">归档</router-link>
          <router-link to="/favorites" class="text-sm font-medium" :class="isActive('/favorites') ? 'text-indigo-600' : 'text-slate-500'">收藏</router-link>
        </div>
        <LoginButton />
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import LoginButton from './LoginButton.vue'

const route = useRoute()
const isActive = (path: string) => route.path === path
</script>

