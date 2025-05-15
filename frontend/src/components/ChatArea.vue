<template>
  <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 bg-chat-bg-light dark:bg-chat-bg-dark scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent">
    <div v-if="messages.length === 0" class="text-center py-10">
      <svg class="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
      <h2 class="mt-2 text-xl font-semibold text-gray-700 dark:text-gray-300">Welcome to Fusion AI</h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Ask me anything, or try a suggestion below.</p>
      <div class="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-3xl mx-auto">
          <button v-for="prompt in suggestedPrompts" :key="prompt" @click="sendSuggestedPrompt(prompt)"
                  class="p-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-sm text-left transition-colors">
              {{ prompt }}
          </button>
      </div>
    </div>

    <div v-else v-for="message in messages" :key="message.id" class="flex" :class="message.sender === 'user' ? 'justify-end' : 'justify-start'">
      <Message :message="message" />
    </div>
    <div ref="endOfChat"></div> </div>
</template>

<script setup>
import { ref, inject, watch, nextTick, onMounted } from 'vue';
import Message from './Message.vue';

const messages = inject('messages'); // Injected from App.vue
const chatContainer = ref(null);
const endOfChat = ref(null); // Reference to the bottom of the chat

const suggestedPrompts = ref([
    "Explain quantum computing in simple terms.",
    "What are some healthy dinner recipes?",
    "Write a short story about a friendly robot."
]);

const scrollToBottom = () => {
  nextTick(() => {
    if (endOfChat.value) {
      endOfChat.value.scrollIntoView({ behavior: 'smooth' });
    }
  });
};

// Watch for new messages and scroll to bottom
watch(messages, () => {
  scrollToBottom();
}, { deep: true });

// Scroll to bottom on component mount if there are messages
onMounted(() => {
    if (messages.value.length > 0) {
        scrollToBottom();
    }
});

const sendSuggestedPrompt = (promptText) => {
    // This function would typically emit an event to App.vue to handle sending the message
    // For now, let's assume App.vue has a method to add messages
    // This is a simplified way, ideally, use emit.
    if (typeof window.handleSendMessage === 'function') { // Check if a global handler exists (not ideal)
        window.handleSendMessage(promptText);
    } else { // Or directly modify if App.vue provides a method via provide/inject for this
        messages.value.push({
            id: Date.now(),
            text: promptText,
            sender: 'user',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        });
        // Simulate AI response
        setTimeout(() => {
            messages.value.push({
            id: Date.now() + 1,
            text: `Okay, let's talk about: "${promptText.substring(0,30)}..."`,
            sender: 'ai',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            });
        }, 1000);
    }
};

</script>

<style scoped>
/* Custom scrollbar for Webkit browsers */
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #cbd5e0; /* gray-300 */
  border-radius: 10px;
}
.dark .scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #4a5568; /* gray-600 */
}
.scrollbar-thin::-webkit-scrollbar-track {
  background-color: transparent;
}
</style>
