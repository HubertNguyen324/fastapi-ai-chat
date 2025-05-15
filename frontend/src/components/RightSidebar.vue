<template>
  <aside
    :class="[
      'bg-sidebar-bg-light dark:bg-sidebar-bg-dark text-gray-700 dark:text-gray-300 flex-col border-l border-gray-200 dark:border-gray-700 sidebar-transition overflow-y-auto scrollbar-thin scrollbar-thumb-gray-400 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent',
      isOpen ? 'flex w-72 md:w-80 lg:w-96' : 'hidden'
    ]"
  >
    <div class="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
      <h2 class="text-lg font-semibold">Conversation History</h2>
      <button @click="$emit('toggle')" class="icon-button -mr-2" title="Close History">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <div class="flex-1 p-2 space-y-1">
      <div v-if="historyItems.length === 0" class="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
        No history yet. Start a new chat!
      </div>
      <div
        v-for="item in historyItems"
        :key="item.id"
        class="history-item group p-3 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 cursor-pointer transition-colors"
      >
        <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-800 dark:text-gray-100 truncate" :title="item.title">{{ item.title }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ item.subtitle }}</p>
        </div>
        <div class="ml-2 shrink-0 flex flex-col items-end">
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ item.time }}</span>
            <div class="mt-1 flex items-center space-x-1.5 text-gray-400 dark:text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
                <button class="hover:text-primary dark:hover:text-primary-light" title="Edit"><i class="fas fa-pencil-alt text-xs"></i></button>
                <button class="hover:text-red-500 dark:hover:text-red-400" title="Delete"><i class="fas fa-trash-alt text-xs"></i></button>
            </div>
        </div>
      </div>
    </div>

    <div class="p-4 border-t border-gray-200 dark:border-gray-700">
        <button class="w-full btn-primary text-sm">
            <i class="fas fa-archive mr-2"></i> View All Archives
        </button>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  isOpen: Boolean,
});
defineEmits(['toggle']);

const historyItems = ref([
  { id: 1, title: 'Shadow mask overflow pixel', subtitle: 'Free outline list figma line...', time: '10:32 AM' },
  { id: 2, title: 'Horizontal frame figjam component', subtitle: 'Frame comment scrolling overflow star...', time: 'Yesterday' },
  { id: 3, title: 'Arrow list undo inspect', subtitle: 'Arrange text union boolean subtract...', time: 'Just Now' },
  { id: 4, title: 'Duplicate subtract inspect rectangle', subtitle: 'Editor project frame subtract undo...', time: '2 days ago' },
  { id: 5, title: 'Welcome to the new platform!', subtitle: 'Figjam vertical share background...', time: 'Mar 10' },
  { id: 6, title: 'Exploring advanced AI features', subtitle: 'Prototype opacity effect opacity...', time: 'Mar 08' },
]);
</script>

<style scoped>
/* Custom scrollbar for Webkit browsers */
.scrollbar-thin::-webkit-scrollbar {
  width: 5px;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #a0aec0; /* gray-400 */
  border-radius: 10px;
}
.dark .scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #4a5568; /* gray-600 */
}
</style>
