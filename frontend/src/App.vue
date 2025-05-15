<template>
  <div :class="{ 'dark': isDarkMode }" class="flex h-screen w-screen overflow-hidden">
    <Sidebar :is-collapsed="isSidebarCollapsed" :is-mobile-open="isMobileSidebarOpen" @toggle-collapse="toggleSidebarCollapse" @close-mobile="isMobileSidebarOpen = false" />

    <div class="flex-1 flex flex-col overflow-hidden bg-chat-bg-light dark:bg-chat-bg-dark">
      <Header
        @toggle-mobile-sidebar="isMobileSidebarOpen = !isMobileSidebarOpen"
        @toggle-dark-mode="toggleDarkMode"
        @toggle-right-sidebar="toggleRightSidebar" :is-dark-mode="isDarkMode"
      />

      <ChatArea :messages="messages" class="flex-1 overflow-y-auto p-4 md:p-6 space-y-4" />

      <InputArea @send-message="handleSendMessage" />
    </div>

    <RightSidebar :is-open="isRightSidebarOpen" @toggle="isRightSidebarOpen = !isRightSidebarOpen" />

    <div v-if="isMobileSidebarOpen" @click="isMobileSidebarOpen = false" class="fixed inset-0 bg-black opacity-50 z-30 lg:hidden"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, provide } from 'vue';
import Sidebar from './components/Sidebar.vue';
import Header from './components/Header.vue';
import ChatArea from './components/ChatArea.vue';
import InputArea from './components/InputArea.vue';
import RightSidebar from './components/RightSidebar.vue';

// Reactive state for UI
const isSidebarCollapsed = ref(false);
const isMobileSidebarOpen = ref(false);
const isDarkMode = ref(false);
const isRightSidebarOpen = ref(true); // Default to open based on image

// Provide dark mode state to child components
provide('isDarkMode', isDarkMode);

// --- Dark Mode Logic ---
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value;
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark');
    localStorage.setItem('darkMode', 'enabled');
  } else {
    document.documentElement.classList.remove('dark');
    localStorage.setItem('darkMode', 'disabled');
  }
};

// --- Right Sidebar Toggle Logic ---
const toggleRightSidebar = () => {
  isRightSidebarOpen.value = !isRightSidebarOpen.value;
};

// --- Chat Logic with API Integration (Example from previous step) ---
const messages = ref([]);
provide('messages', messages);

async function fetchInitialMessages() {
  try {
    const response = await fetch('/api/v1/chat/history'); // Replace with your actual API
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    messages.value = data.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }));
  } catch (error) {
    console.error("Could not fetch chat history:", error);
    messages.value = [{ id: 'init_error', text: 'Welcome! Type a message to start.', sender: 'ai', timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }];
  }
}

const handleSendMessage = async (newMessageText) => {
  if (newMessageText.trim() === '') return;
  const userMessage = {
    text: newMessageText,
    sender: 'user',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  };
  messages.value.push(userMessage);

  try {
    const response = await fetch('/api/v1/chat/send', { // Replace with your actual API
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: newMessageText }),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const aiResponse = await response.json();
    messages.value.push({
        ...aiResponse,
        timestamp: new Date(aiResponse.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
  } catch (error) {
    console.error("Failed to send message or get AI response:", error);
    messages.value.push({
      text: "Sorry, I couldn't get a response. Please try again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
  }
};

// --- Lifecycle Hooks ---
onMounted(() => {
  if (localStorage.getItem('darkMode') === 'enabled' ||
     (localStorage.getItem('darkMode') === null && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDarkMode.value = true;
    document.documentElement.classList.add('dark');
  } else {
    isDarkMode.value = false;
    document.documentElement.classList.remove('dark');
  }
  checkScreenSize();
  window.addEventListener('resize', checkScreenSize);
  fetchInitialMessages();
});

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize);
});

// --- Sidebar and Screen Size Logic ---
const toggleSidebarCollapse = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
};

const checkScreenSize = () => {
  if (window.innerWidth < 1024) {
    isSidebarCollapsed.value = true;
    isMobileSidebarOpen.value = false;
  }
  // Check for right sidebar on initial load based on screen size
  // This logic can be adjusted: always open on desktop, or remember user preference
  if (window.innerWidth < 768) { // md breakpoint for right sidebar
      isRightSidebarOpen.value = false;
  } else {
      // For larger screens, you might want it to default to open,
      // or respect if it was previously closed by the user (requires localStorage).
      // For now, let's keep the existing behavior or default to true.
      // isRightSidebarOpen.value = true; // Or keep as is if you want it to remember its state across resizes
  }
};

</script>

<style>
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
:root {
  color-scheme: light dark;
}
body {
  transition: background-color 0.3s ease, color 0.3s ease;
}
</style>
