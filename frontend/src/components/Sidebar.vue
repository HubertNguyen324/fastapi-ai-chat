<template>
  <aside
    :class="[
      'bg-sidebar-bg-light dark:bg-sidebar-bg-dark text-gray-700 dark:text-gray-300 flex flex-col sidebar-transition overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-gray-400 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent',
      isMobileOpen ? 'fixed inset-y-0 left-0 z-40 w-64 shadow-xl lg:hidden' : 'hidden lg:flex',
      isCollapsed && !isMobileOpen ? 'w-20 sidebar-collapsed' : 'w-64'
    ]"
  >
    <div class="flex items-center h-16 px-4 shrink-0" :class="isCollapsed && !isMobileOpen ? 'justify-center' : 'justify-between'">
      <a href="#" class="flex items-center space-x-2 text-primary dark:text-primary-light">
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a4 4 0 00-5.656 0M14 10l-2.121-2.121a2 2 0 00-2.828 0L7 10m7 0l-2.121 2.121a2 2 0 01-2.828 0L7 10m7 0v5.586A2 2 0 0115.586 18H8.414A2 2 0 016.414 16L6.414 10m10.172-4.172a4 4 0 00-5.656 0L9 7.656m2.172-2.172a4 4 0 005.656 0L15 3.828M9 7.656L7.172 5.828m6.344 6.344L11.344 10"></path></svg>
        <span class="font-bold text-xl logo-text" v-if="!(isCollapsed && !isMobileOpen)">Fusion AI</span>
      </a>
      <button @click="$emit('close-mobile')" class="lg:hidden icon-button" v-if="isMobileOpen">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <div class="p-4" :class="isCollapsed && !isMobileOpen ? 'px-2' : 'px-4'">
      <div class="relative">
        <span class="absolute inset-y-0 left-0 flex items-center pl-3">
          <i class="fas fa-search text-gray-400 dark:text-gray-500"></i>
        </span>
        <input
          type="text"
          class="w-full pl-10 pr-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-700 border border-transparent focus:border-primary dark:focus:border-primary-light focus:ring-1 focus:ring-primary dark:focus:ring-primary-light focus:outline-none text-sm"
          :placeholder="isCollapsed && !isMobileOpen ? '' : 'Search...'"
        />
      </div>
    </div>

    <nav class="flex-1 px-2 space-y-1">
      <a
        v-for="item in navItems"
        :key="item.name"
        :href="item.href"
        :class="[
          'flex items-center py-2.5 px-4 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-primary dark:hover:text-primary-light group',
          item.current ? 'bg-gray-200 dark:bg-gray-700 text-primary dark:text-primary-light font-semibold' : '',
          isCollapsed && !isMobileOpen ? 'justify-center' : ''
        ]"
      >
        <i :class="[item.icon, 'w-6 h-6 mr-3 nav-icon group-hover:text-primary dark:group-hover:text-primary-light', isCollapsed && !isMobileOpen ? 'mr-0' : '']"></i>
        <span class="nav-text" v-if="!(isCollapsed && !isMobileOpen)">{{ item.name }}</span>
        <span
            v-if="item.count && !(isCollapsed && !isMobileOpen)"
            class="ml-auto text-xs font-medium bg-primary-light/20 dark:bg-primary-dark/30 text-primary dark:text-primary-light px-2 py-0.5 rounded-full"
        >
            {{ item.count }}
        </span>
      </a>

      <div :class="isCollapsed && !isMobileOpen ? 'px-0 py-2' : 'px-4 py-2'">
        <h3 :class="['text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider', isCollapsed && !isMobileOpen ? 'text-center nav-text' : '']">
          <span v-if="!(isCollapsed && !isMobileOpen)">Favorites</span>
          <i v-else class="fas fa-star"></i>
        </h3>
      </div>
      <a
        v-for="fav in favoriteItems"
        :key="fav.name"
        :href="fav.href"
        :class="[
          'flex items-center py-2.5 px-4 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-primary dark:hover:text-primary-light group',
          fav.current ? 'bg-gray-200 dark:bg-gray-700 text-primary dark:text-primary-light font-semibold' : '',
          isCollapsed && !isMobileOpen ? 'justify-center' : ''
        ]"
      >
        <i :class="[fav.icon, 'w-6 h-6 mr-3 nav-icon group-hover:text-primary dark:group-hover:text-primary-light', isCollapsed && !isMobileOpen ? 'mr-0' : '']"></i>
        <span class="nav-text" v-if="!(isCollapsed && !isMobileOpen)">{{ fav.name }}</span>
         <span
            v-if="fav.count && !(isCollapsed && !isMobileOpen)"
            class="ml-auto text-xs font-medium bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 px-2 py-0.5 rounded-full"
        >
            {{ fav.count }}
        </span>
      </a>
    </nav>

    <div class="p-4 mt-auto border-t border-gray-200 dark:border-gray-700">
       <div class="mb-4 p-3 bg-gradient-to-br from-purple-500 to-indigo-600 dark:from-purple-700 dark:to-indigo-800 rounded-lg text-white text-center" :class="isCollapsed && !isMobileOpen ? 'p-2' : 'p-3'">
        <div class="flex items-center" :class="isCollapsed && !isMobileOpen ? 'justify-center' : 'justify-between'">
            <div :class="isCollapsed && !isMobileOpen ? 'hidden' : ''">
                <p class="text-sm font-semibold upgrade-text">50% Completed</p>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
                    <div class="bg-yellow-400 h-1.5 rounded-full" style="width: 50%"></div>
                </div>
            </div>
            <button class="mt-2 upgrade-button bg-white text-purple-600 dark:bg-gray-100 dark:text-purple-700 text-xs font-bold py-1 px-3 rounded-full hover:bg-opacity-90 transition-colors" :class="isCollapsed && !isMobileOpen ? 'w-full py-2' : 'mt-2'">
                <i class="fas fa-arrow-up mr-1" v-if="!(isCollapsed && !isMobileOpen)"></i>
                <span v-if="!(isCollapsed && !isMobileOpen)">Upgrade</span>
                <i class="fas fa-arrow-up" v-else></i>
            </button>
        </div>
      </div>

      <div class="flex items-center" :class="isCollapsed && !isMobileOpen ? 'justify-center' : ''">
        <img
          class="h-10 w-10 rounded-full object-cover"
          src="https://placehold.co/100x100/6D28D9/FFFFFF?text=JB"
          alt="User Avatar"
        />
        <div class="ml-3 profile-info" v-if="!(isCollapsed && !isMobileOpen)">
          <p class="text-sm font-semibold text-gray-800 dark:text-gray-100">James Broeng</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">jamesbroeng.co.uk</p>
        </div>
         <button @click="toggleSidebar" class="ml-auto icon-button hidden lg:block" :title="isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'">
            <i :class="isCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left'"></i>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  isCollapsed: Boolean,
  isMobileOpen: Boolean,
});

const emit = defineEmits(['toggle-collapse', 'close-mobile']);

const toggleSidebar = () => {
  emit('toggle-collapse');
};

const navItems = ref([
  { name: 'Chats', href: '#', icon: 'fas fa-comments', current: true, count: null },
  { name: 'Updates & FAQ', href: '#', icon: 'fas fa-info-circle', current: false, count: null },
  { name: 'Subscriptions', href: '#', icon: 'fas fa-credit-card', current: false, count: null },
  { name: 'Settings', href: '#', icon: 'fas fa-cog', current: false, count: null },
]);

const favoriteItems = ref([
  { name: 'Welcome', href: '#', icon: 'fas fa-star', current: true, count: 1 },
  { name: 'Voice Tools', href: '#', icon: 'fas fa-microphone-alt', current: false, count: 1222 },
  { name: 'Video Generation', href: '#', icon: 'fas fa-video', current: false, count: 48 },
  { name: 'Photo Generation', href: '#', icon: 'fas fa-camera-retro', current: false, count: 7 },
  { name: 'Education & Science', href: '#', icon: 'fas fa-flask', current: false, count: 3 },
  { name: 'New List', href: '#', icon: 'fas fa-plus-circle', current: false, count: null },
]);

</script>

<style scoped>
/* Custom scrollbar for Webkit browsers */
.scrollbar-thin::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #a0aec0; /* gray-400 */
  border-radius: 10px;
  border: 2px solid transparent;
  background-clip: content-box;
}
.dark .scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #4a5568; /* gray-600 */
}
.scrollbar-thin::-webkit-scrollbar-track {
  background-color: transparent;
}
</style>
