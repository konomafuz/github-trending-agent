<template>
  <div class="min-h-screen bg-slate-50 selection:bg-indigo-100 selection:text-indigo-900 flex flex-col items-center">
    <NavBar />
    <main class="w-full max-w-[1000px] px-4 sm:px-6 lg:px-8 py-10 mt-16 z-10 flex-1">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import NavBar from './components/NavBar.vue'
import { useFavoritesStore } from './stores/favorites'

const favoritesStore = useFavoritesStore()

onMounted(() => {
  favoritesStore.init()
})
</script>

<style>
body {
  font-family: 'Inter', sans-serif;
  background-color: #f8fafc;
  color: #0f172a;
}
</style>
