// Import the main App component
import App from "./App.vue";
// Import necessary functions from Vue
import { createApp } from "vue";

// Create the Vue application instance
const app = createApp(App);

// Mount the app to the #app element in index.html
app.mount("#app");
