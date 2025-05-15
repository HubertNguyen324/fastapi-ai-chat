<template>
  <div class="flex items-end space-x-2 max-w-xl" :class="{'ml-auto': message.sender === 'user'}">
    <img
      v-if="message.sender === 'ai'"
      class="w-8 h-8 rounded-full object-cover self-start shrink-0"
      src="https://placehold.co/40x40/8B5CF6/FFFFFF?text=AI"
      alt="AI Avatar"
    />

    <div
      :class="[
        'chat-bubble p-3 md:p-4 rounded-xl shadow-sm',
        message.sender === 'user'
          ? 'bg-primary text-white user-bubble rounded-br-none'
          : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 ai-bubble rounded-bl-none'
      ]"
    >
      <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ message.text }}</p>
      <div :class="['text-xs mt-1.5', message.sender === 'user' ? 'text-indigo-200 dark:text-indigo-300 text-right' : 'text-gray-400 dark:text-gray-500 text-left']">
        {{ message.timestamp }}
      </div>

      <div v-if="message.sender === 'ai' && message.actions" class="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600 flex items-center space-x-2">
        <button v-for="action in message.actions" :key="action.label"
                class="text-xs px-2 py-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
          <i :class="action.icon" class="mr-1"></i>{{ action.label }}
        </button>
      </div>

      <div v-if="message.sender === 'ai' && message.suggestedMedia" class="mt-3">
        <p class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">Suggested Media</p>
        <div class="grid grid-cols-2 gap-2">
            <div v-for="(media, index) in message.suggestedMedia" :key="index" class="relative group aspect-square">
                <img :src="media.url" :alt="media.alt || 'Suggested media'" class="rounded-lg object-cover w-full h-full">
                <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity flex items-center justify-center">
                    <button class="p-1.5 bg-white/80 dark:bg-black/80 rounded-full text-gray-700 dark:text-gray-200 opacity-0 group-hover:opacity-100 transition-opacity">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </div>
        </div>
         <p class="text-xs text-gray-400 dark:text-gray-500 mt-1.5">You have the rights to use the suggested media.</p>
         <div class="mt-3 flex space-x-2">
            <button class="flex-1 text-xs bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 py-1.5 px-2 rounded-md transition-colors">Share Now</button>
            <button class="flex-1 text-xs bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 py-1.5 px-2 rounded-md transition-colors">Create variation</button>
            <button class="text-xs p-1.5 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 rounded-md transition-colors"><i class="fas fa-sliders-h"></i></button>
            <button class="text-xs p-1.5 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 rounded-md transition-colors"><i class="far fa-copy"></i></button>
         </div>
      </div>
    </div>

    </div>
</template>

<script setup>
defineProps({
  message: {
    type: Object,
    required: true,
    default: () => ({
        id: 0,
        text: 'Default message',
        sender: 'ai', // 'ai' or 'user'
        timestamp: '12:00 PM',
        actions: [], // Optional: e.g. [{label: 'Copy', icon: 'far fa-copy'}]
        suggestedMedia: [] // Optional: e.g. [{url: '...', alt: '...'}]
    })
  }
});
</script>

<style scoped>
/* Add any specific styles for messages if Tailwind classes are not enough */
.user-bubble {
  /* Example: if you need a specific tail for user bubbles */
}
.ai-bubble {
  /* Example: if you need a specific tail for AI bubbles */
}
.whitespace-pre-wrap {
    white-space: pre-wrap; /* Ensures line breaks in messages are respected */
}
</style>
