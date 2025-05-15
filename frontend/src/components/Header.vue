<template>
  <header class="flex items-center justify-between h-16 px-4 md:px-6 border-b border-gray-200 dark:border-gray-700 bg-chat-bg-light dark:bg-chat-bg-dark shrink-0">
    <div class="flex items-center">
      <button @click="$emit('toggle-mobile-sidebar')" class="lg:hidden icon-button mr-2 -ml-2">
        <i class="fas fa-bars text-xl"></i>
      </button>
      <h1 class="text-xl font-semibold text-gray-800 dark:text-gray-100">Welcome</h1>
    </div>

    <div class="hidden md:flex items-center space-x-1 bg-gray-200 dark:bg-gray-700 p-1 rounded-lg">
      <button
        v-for="mode in modes"
        :key="mode.id"
        @click="activeMode = mode.id"
        :class="[
          'px-4 py-1.5 rounded-md text-sm font-medium transition-colors',
          activeMode === mode.id
            ? 'bg-white dark:bg-gray-600 text-primary dark:text-primary-light shadow'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600/50',
        ]"
      >
        {{ mode.name }}
      </button>
    </div>

    <div class="flex items-center space-x-2 md:space-x-3">
      <button class="icon-button hidden sm:inline-flex" title="Star">
        <i class="far fa-star text-lg"></i>
      </button>
      <button class="icon-button hidden sm:inline-flex" title="Share">
        <i class="fas fa-share-alt text-lg"></i>
      </button>
       <button @click="$emit('toggle-dark-mode')" class="icon-button" :title="isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
        <i :class="isDarkMode ? 'fas fa-sun' : 'fas fa-moon'" class="text-lg"></i>
      </button>
      <button @click="$emit('toggle-right-sidebar')" class="icon-button" title="Toggle Conversation History">
        <i class="fas fa-history text-lg"></i> </button>
      <button class="icon-button" title="More options">
        <i class="fas fa-ellipsis-v text-lg"></i>
      </button>
      <button class="bg-primary hover:bg-primary-dark text-white font-medium py-2 px-4 rounded-lg text-sm flex items-center space-x-2 transition-colors">
        <i class="fas fa-plus"></i>
        <span>New Chat</span>
      </button>
      <button class="icon-button relative" title="Notifications">
        <i class="far fa-bell text-lg"></i>
        <span class="absolute top-0 right-0 block h-2 w-2 rounded-full bg-pink-500 ring-2 ring-white dark:ring-gray-800"></span>
      </button>
      <img
        class="h-8 w-8 rounded-full object-cover border-2 border-transparent hover:border-primary transition-colors"
        src="https://placehold.co/100x100/EC4899/FFFFFF?text=U"
        alt="User Avatar"
      />
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  isDarkMode: Boolean,
});
// Added 'toggle-right-sidebar' to emits
defineEmits(['toggle-mobile-sidebar', 'toggle-dark-mode', 'toggle-right-sidebar']);

const modes = ref([
  { id: 'balanced', name: 'Balanced' },
  { id: 'creative', name: 'Creative' },
  { id: 'precise', name: 'Precise' },
]);
const activeMode = ref('balanced');
</script>
