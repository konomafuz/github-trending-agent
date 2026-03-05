<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">分类浏览</h3>

    <div class="space-y-4">
      <div v-for="group in categoryGroups" :key="group.id" class="border-b border-gray-100 pb-4 last:border-b-0">
        <!-- Group Header -->
        <button
          @click="toggleGroup(group.id)"
          class="w-full flex items-center justify-between text-left py-2 hover:bg-gray-50 rounded transition-colors"
        >
          <span class="font-medium text-gray-900">{{ group.label }}</span>
          <svg
            class="w-5 h-5 text-gray-500 transition-transform"
            :class="{ 'rotate-180': expandedGroups.has(group.id) }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Categories -->
        <div v-show="expandedGroups.has(group.id)" class="mt-2 space-y-1 pl-2">
          <button
            v-for="category in group.categories"
            :key="category.id"
            @click="selectCategory(group.id, category.id)"
            class="w-full flex items-center justify-between px-3 py-2 text-sm rounded transition-colors"
            :class="isSelected(group.id, category.id)
              ? 'bg-indigo-50 text-indigo-700 font-medium'
              : 'text-gray-700 hover:bg-gray-50'"
          >
            <span>{{ category.label }}</span>
            <span class="text-xs text-gray-500">{{ category.count }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Clear Filters -->
    <button
      v-if="selectedCategories.size > 0"
      @click="clearAll"
      class="w-full mt-4 px-4 py-2 text-sm text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 rounded transition-colors font-medium"
    >
      清除所有筛选
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { CategoryGroup } from '../utils/category'

const props = defineProps<{
  categoryGroups: CategoryGroup[]
}>()

const emit = defineEmits<{
  select: [selectedRepos: Set<string>]
}>()

// Expanded groups (all expanded by default)
const expandedGroups = ref(new Set(props.categoryGroups.map(g => g.id)))

// Selected categories: Map<groupId, categoryId>
const selectedCategories = ref(new Map<string, string>())

function toggleGroup(groupId: string) {
  if (expandedGroups.value.has(groupId)) {
    expandedGroups.value.delete(groupId)
  } else {
    expandedGroups.value.add(groupId)
  }
}

function isSelected(groupId: string, categoryId: string): boolean {
  return selectedCategories.value.get(groupId) === categoryId
}

function selectCategory(groupId: string, categoryId: string) {
  // Toggle selection
  if (selectedCategories.value.get(groupId) === categoryId) {
    selectedCategories.value.delete(groupId)
  } else {
    selectedCategories.value.set(groupId, categoryId)
  }

  emitSelection()
}

function clearAll() {
  selectedCategories.value.clear()
  emitSelection()
}

function emitSelection() {
  if (selectedCategories.value.size === 0) {
    // No filters, return empty set to show all
    emit('select', new Set())
    return
  }

  // Get repos from all selected categories
  const repoSets: Set<string>[] = []

  selectedCategories.value.forEach((categoryId, groupId) => {
    const group = props.categoryGroups.find(g => g.id === groupId)
    const category = group?.categories.find(c => c.id === categoryId)
    if (category) {
      repoSets.push(new Set(category.repos))
    }
  })

  // Intersect all sets (repos must match ALL selected categories)
  if (repoSets.length === 0) {
    emit('select', new Set())
    return
  }

  let result: Set<string> = repoSets[0]!
  for (let i = 1; i < repoSets.length; i++) {
    const currentSet = repoSets[i]
    if (currentSet) {
      result = new Set([...result].filter(x => currentSet.has(x)))
    }
  }

  emit('select', result)
}
</script>