<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
  // Initialize favorites store on app load
  favoritesStore.init()
})
</script>
