<template>
  <div class="bg-transparent">
    <div class="flex items-center gap-2 mb-6">
      <div class="w-1.5 h-6 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></div>
      <h3 class="text-lg font-bold text-slate-800 tracking-wide">按分类发现</h3>
    </div>

    <div class="space-y-6">
      <div v-for="group in categoryGroups" :key="group.id">
        <!-- Group Header -->
        <button
          @click="toggleGroup(group.id)"
          class="w-full flex items-center justify-between text-left py-2 group/btn"
        >
          <span class="font-semibold text-sm text-slate-600 uppercase tracking-wider group-hover/btn:text-indigo-600 transition-colors">{{ group.label }}</span>
          <svg
            class="w-4 h-4 text-slate-400 transition-transform duration-300"
            :class="{ 'rotate-180': expandedGroups.has(group.id) }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Categories -->
        <div v-show="expandedGroups.has(group.id)" class="mt-2 space-y-1.5">
          <button
            v-for="category in group.categories"
            :key="category.id"
            @click="selectCategory(group.id, category.id)"
            class="w-full flex items-center justify-between px-3 py-2 text-sm rounded-xl transition-all border border-transparent"
            :class="isSelected(group.id, category.id)
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200 font-medium scale-[1.02]'
              : 'text-slate-600 hover:bg-white hover:border-indigo-100 hover:text-indigo-600 hover:shadow-sm'"
          >
            <span class="truncate pr-2">{{ category.label }}</span>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-black/10 transition-colors"
                  :class="isSelected(group.id, category.id) ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500'">
              {{ category.count }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- Clear Filters -->
    <button
      v-if="selectedCategories.size > 0"
      @click="clearAll"
      class="w-full mt-8 px-4 py-2.5 text-sm font-bold text-rose-600 bg-rose-50 hover:bg-rose-100 border border-rose-100 rounded-xl transition-colors flex items-center justify-center gap-2"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
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