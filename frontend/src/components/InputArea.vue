<template>
  <div class="p-4 md:p-6 border-t border-gray-200 dark:border-gray-700 bg-input-bg-light dark:bg-input-bg-dark shrink-0">
    <div class="flex items-center space-x-2 mb-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
        <button v-for="action in suggestedActions" :key="action.label"
                @click="handleSuggestedAction(action)"
                class="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 rounded-lg whitespace-nowrap transition-colors">
            <i :class="action.icon" class="mr-1.5 opacity-80"></i>
            {{ action.label }}
        </button>
    </div>

    <div class="flex items-end space-x-2 md:space-x-3">
      <button class="icon-button p-2.5 text-gray-500 dark:text-gray-400 hover:text-primary dark:hover:text-primary-light" title="Attach file">
        <i class="fas fa-paperclip text-lg"></i>
      </button>
      <button class="icon-button p-2.5 text-gray-500 dark:text-gray-400 hover:text-primary dark:hover:text-primary-light" title="Use microphone">
        <i class="fas fa-microphone text-lg"></i>
      </button>
      <textarea
        ref="textarea"
        v-model="newMessage"
        @keydown.enter.exact.prevent="sendMessage"
        @input="adjustTextareaHeight"
        rows="1"
        class="flex-1 p-3 pr-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:ring-2 focus:ring-primary dark:focus:ring-primary-light focus:border-transparent outline-none resize-none placeholder-gray-400 dark:placeholder-gray-500 text-sm scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600"
        placeholder="Ask me anything..."
      ></textarea>
      <button
        @click="sendMessage"
        :disabled="newMessage.trim() === ''"
        class="p-2.5 rounded-lg text-white transition-colors"
        :class="newMessage.trim() === '' ? 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed' : 'bg-primary hover:bg-primary-dark'"
        title="Send message"
      >
        <i class="fas fa-paper-plane text-lg"></i>
      </button>
    </div>
     <p class="text-xs text-gray-400 dark:text-gray-500 mt-2 text-center md:text-left">
        Fusion AI can make mistakes. Consider checking important information.
    </p>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';

const emit = defineEmits(['send-message']);
const newMessage = ref('');
const textarea = ref(null);

const suggestedActions = ref([
    { label: "Summarize this", icon: "fas fa-align-left", actionType: "summarize" },
    { label: "Explain like I'm 5", icon: "fas fa-child", actionType: "explain_simple" },
    { label: "Translate to Spanish", icon: "fas fa-language", actionType: "translate", targetLang: "es" },
    { label: "Check grammar", icon: "fas fa-check-double", actionType: "grammar_check" },
]);

const sendMessage = () => {
  if (newMessage.value.trim() !== '') {
    emit('send-message', newMessage.value);
    newMessage.value = '';
    nextTick(() => {
      adjustTextareaHeight(); // Reset height after sending
    });
  }
};

const adjustTextareaHeight = () => {
  if (textarea.value) {
    textarea.value.style.height = 'auto'; // Reset height
    textarea.value.style.height = `${textarea.value.scrollHeight}px`; // Set to scroll height
  }
};

const handleSuggestedAction = (action) => {
    // Example: Prepend action to message or directly send a command
    // This is a placeholder for more complex logic
    newMessage.value = `/${action.actionType} ${action.targetLang || ''} ${newMessage.value}`;
    textarea.value.focus();
    nextTick(() => {
      adjustTextareaHeight();
    });
};

</script>

<style scoped>
textarea {
  min-height: 44px; /* Ensure it aligns with buttons roughly */
  max-height: 150px; /* Prevent excessive growth */
}
.scrollbar-thin::-webkit-scrollbar {
  width: 5px;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #cbd5e0; /* gray-300 */
  border-radius: 10px;
}
.dark .scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #4a5568; /* gray-600 */
}
</style>
