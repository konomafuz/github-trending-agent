import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from './auth'
import type { Repo } from './reports'

export interface Favorite {
  full_name: string
  starred_at: string
  note?: string
}

const GIST_DESCRIPTION = 'GitHub Trending Favorites'
const GIST_FILENAME = 'favorites.json'

export const useFavoritesStore = defineStore('favorites', () => {
  const authStore = useAuthStore()
  const favorites = ref<Favorite[]>([])
  const loading = ref(false)
  const gistId = ref<string | null>(null)

  const favoriteNames = computed(() => new Set(favorites.value.map(f => f.full_name)))

  // Initialize from localStorage or Gist
  async function init() {
    console.log('Initializing favorites store...')
    // Try localStorage first
    const saved = localStorage.getItem('favorites')
    if (saved) {
      try {
        favorites.value = JSON.parse(saved)
        console.log('Loaded favorites from localStorage:', favorites.value.length)
      } catch (e) {
        console.error('Failed to parse favorites:', e)
      }
    } else {
      console.log('No favorites in localStorage')
    }

    // If authenticated, sync with Gist
    if (authStore.isAuthenticated) {
      console.log('User authenticated, syncing from Gist...')
      await syncFromGist()
    }
  }

  // Sync from Gist
  async function syncFromGist() {
    if (!authStore.token) return

    loading.value = true
    try {
      // Find existing gist
      const gistsResponse = await fetch('https://api.github.com/gists', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      })

      if (!gistsResponse.ok) throw new Error('Failed to fetch gists')

      const gists = await gistsResponse.json()
      const existingGist = gists.find((g: any) => g.description === GIST_DESCRIPTION)

      if (existingGist) {
        gistId.value = existingGist.id
        const file = existingGist.files[GIST_FILENAME]
        if (file && file.content) {
          const data = JSON.parse(file.content)
          favorites.value = data.favorites || []
          saveToLocalStorage()
        }
      }
    } catch (error) {
      console.error('Failed to sync from Gist:', error)
    } finally {
      loading.value = false
    }
  }

  // Save to Gist
  async function saveToGist() {
    if (!authStore.token) return

    loading.value = true
    try {
      const content = JSON.stringify({ favorites: favorites.value }, null, 2)

      if (gistId.value) {
        // Update existing gist
        await fetch(`https://api.github.com/gists/${gistId.value}`, {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${authStore.token}`,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            files: {
              [GIST_FILENAME]: { content }
            }
          })
        })
      } else {
        // Create new gist
        const response = await fetch('https://api.github.com/gists', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authStore.token}`,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            description: GIST_DESCRIPTION,
            public: false,
            files: {
              [GIST_FILENAME]: { content }
            }
          })
        })

        if (response.ok) {
          const gist = await response.json()
          gistId.value = gist.id
        }
      }
    } catch (error) {
      console.error('Failed to save to Gist:', error)
    } finally {
      loading.value = false
    }
  }

  // Save to localStorage
  function saveToLocalStorage() {
    localStorage.setItem('favorites', JSON.stringify(favorites.value))
  }

  // Add favorite
  async function addFavorite(repo: Repo, note?: string) {
    const favorite: Favorite = {
      full_name: repo.full_name,
      starred_at: new Date().toISOString(),
      note
    }

    favorites.value.push(favorite)
    console.log('Added favorite:', favorite)
    console.log('Total favorites:', favorites.value.length)
    saveToLocalStorage()

    if (authStore.isAuthenticated) {
      await saveToGist()
    }
  }

  // Remove favorite
  async function removeFavorite(fullName: string) {
    favorites.value = favorites.value.filter(f => f.full_name !== fullName)
    saveToLocalStorage()

    if (authStore.isAuthenticated) {
      await saveToGist()
    }
  }

  // Update note
  async function updateNote(fullName: string, note: string) {
    const favorite = favorites.value.find(f => f.full_name === fullName)
    if (favorite) {
      favorite.note = note
      saveToLocalStorage()

      if (authStore.isAuthenticated) {
        await saveToGist()
      }
    }
  }

  // Check if favorited
  function isFavorited(fullName: string): boolean {
    return favoriteNames.value.has(fullName)
  }

  return {
    favorites,
    loading,
    favoriteNames,
    init,
    syncFromGist,
    addFavorite,
    removeFavorite,
    updateNote,
    isFavorited
  }
})