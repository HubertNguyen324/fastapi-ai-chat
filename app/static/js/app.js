// app/static/js/app.js

// Import Vue Composition API functions from the global Vue object (provided by CDN)
const { createApp, ref, computed, watch, nextTick, onMounted, onUnmounted } =
  Vue;

const app = createApp({
  delimiters: ["[[", "]]"], // Avoid conflict with Jinja2/Flask default delimiters {{ }}
  setup() {
    // --- Utility ---
    function uuidv4() {
      // Simple UUID generator for client ID fallback
      try {
        // Use crypto API if available (preferred)
        return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, (c) =>
          (
            c ^
            (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))
          ).toString(16)
        );
      } catch (e) {
        // Fallback for environments without crypto.getRandomValues
        console.warn(
          "crypto.getRandomValues not available, using less random fallback for UUID."
        );
        return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
          /[xy]/g,
          function (c) {
            var r = (Math.random() * 16) | 0,
              v = c == "x" ? r : (r & 0x3) | 0x8;
            return v.toString(16);
          }
        );
      }
    }

    // --- Reactive State Definition ---

    // Session & Connection State
    const storedClientId = localStorage.getItem("aiAgentClientId");
    const clientId = ref(storedClientId || `user_${uuidv4()}`); // Persisted client identifier
    const ws = ref(null); // WebSocket connection instance
    const isConnected = ref(false); // Live status of the WebSocket connection

    // UI Control State
    const isDarkMode = ref(false); // Theme state
    const isLeftPanelOpen = ref(true); // Left sidebar visibility
    const isRightPanelOpen = ref(true); // Right sidebar visibility
    const isMobile = ref(false); // Flag for mobile layout breakpoint (< 1024px)
    const loadingMessages = ref(false); // Indicator shown when loading topic history

    // Application Data State
    const agents = ref([]); // List of available agents {id: string, name: string}
    const topics = ref([]); // List of chat topics for this client {id, agent_id, name}
    const currentTopicId = ref(null); // ID of the currently displayed topic (null for new chat screen)
    const selectedAgentId = ref(null); // Agent ID selected in the dropdown (for new chats or agent changes)
    const messages = ref({}); // Cache of messages per topic: { topic_id: Message[] }
    const taskResults = ref({}); // Cache of task results per topic: { topic_id: TaskResult[] }
    const newMessage = ref(""); // Model for the chat input textarea

    // Template Refs (links to DOM elements)
    const chatInput = ref(null); // Reference to the <textarea> element
    const messageArea = ref(null); // Reference to the scrollable message display <div>

    // --- Computed Properties (Derived State) ---

    const currentMessages = computed(() => {
      // Returns the array of messages for the currently selected topic, or an empty array.
      return currentTopicId.value
        ? messages.value[currentTopicId.value] || []
        : [];
    });

    const currentTaskResults = computed(() => {
      // Returns the array of task results for the currently selected topic.
      return currentTopicId.value
        ? taskResults.value[currentTopicId.value] || []
        : [];
    });

    const currentTopicAgentId = computed(() => {
      // Finds the agent ID associated with the currently active topic.
      const topic = topics.value.find((t) => t.id === currentTopicId.value);
      return topic ? topic.agent_id : null;
    });

    // --- Methods ---

    // Client ID Management
    function ensureClientId() {
      // Ensures a client ID exists in localStorage, generating one if necessary.
      if (!localStorage.getItem("aiAgentClientId")) {
        const newId = `user_${uuidv4()}`;
        clientId.value = newId;
        localStorage.setItem("aiAgentClientId", newId);
        console.log("Generated and stored new client ID:", newId);
      } else {
        // Update the ref just in case it was initialized differently (shouldn't happen often)
        clientId.value = localStorage.getItem("aiAgentClientId");
        console.log(
          "Using existing client ID from localStorage:",
          clientId.value
        );
      }
    }

    // WebSocket Connection Handling
    function connectWebSocket() {
      // Establishes the WebSocket connection if not already open.
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        console.log("WebSocket connection attempt skipped: Already connected.");
        return;
      }
      ensureClientId(); // Make sure client ID is set before connecting
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${wsProtocol}//${window.location.host}/ws/${clientId.value}`;
      console.log("Attempting WebSocket connection to:", wsUrl);

      try {
        ws.value = new WebSocket(wsUrl);
        setupWebSocketListeners(); // Attach event listeners
      } catch (error) {
        console.error("Failed to create WebSocket:", error);
        isConnected.value = false;
        // Consider showing an error message to the user
      }
    }

    function setupWebSocketListeners() {
      // Attaches event handlers to the WebSocket instance.
      if (!ws.value) return;

      ws.value.onopen = () => {
        console.log("WebSocket Connection Established.");
        isConnected.value = true;
        // Optional: Send a ping immediately upon connection if needed
        // sendPing();
      };

      ws.value.onmessage = (event) => {
        // Handles messages received from the server.
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data); // Delegate to the message handler
        } catch (e) {
          console.error(
            "Failed to parse incoming WebSocket message:",
            event.data,
            e
          );
        }
      };

      ws.value.onerror = (error) => {
        // Handles WebSocket errors (e.g., connection refused).
        console.error("WebSocket Error:", error);
        isConnected.value = false; // Update connection status
        // TODO: Implement more robust error handling/reconnection logic.
      };

      ws.value.onclose = (event) => {
        // Handles WebSocket connection closure.
        console.log(
          `WebSocket Connection Closed: Code=${event.code}, Reason="${event.reason}"`
        );
        isConnected.value = false; // Update connection status
        // Handle specific close codes for user feedback or reconnection attempts.
        if (event.code === 1008 && event.reason === "Session already active") {
          alert(
            "Session Conflict: This AI Agent Chat is already open in another tab or window. Please close the other instance."
          );
        } else if (event.code === 1011) {
          // Server error during connection
          alert(
            "Server Error: Connection closed unexpectedly. Please try refreshing the page."
          );
        }
        // TODO: Implement automatic reconnection logic with backoff strategy.
      };
    }

    // WebSocket Message Router
    function handleWebSocketMessage(data) {
      // Processes incoming messages based on their 'type'.
      const { type, payload } = data;
      console.log(`[WS Handle] Type: ${type}`);
      // console.debug(`[WS Handle] Payload:`, payload); // Uncomment for detailed payload logging

      loadingMessages.value = false; // Assume loading stops unless a specific action starts it

      switch (type) {
        case "initial_state":
          handleInitialState(payload);
          break;
        case "topic_list_update":
          handleTopicListUpdate(payload);
          break;
        case "topic_state":
          handleTopicState(payload);
          break;
        case "new_message":
          handleNewMessage(payload);
          break;
        case "new_task_result":
          handleNewTaskResult(payload);
          break;
        case "active_topic_update":
          handleActiveTopicUpdate(payload);
          break;
        case "error":
          handleServerError(payload);
          break;
        case "pong":
          // Optional: Handle server pong response for keepalive
          // console.debug("Pong received from server.");
          break;
        default:
          console.warn("[WS Handle] Unknown message type received:", type);
      }
    }

    // Specific Message Handlers
    function handleInitialState(payload) {
      console.log("[WS Handle] Processing initial state...");
      agents.value = payload.agents || [];
      const initialActiveTopicId = payload.active_topic_id; // This can be null

      // Set currentTopicId state *first*
      currentTopicId.value = initialActiveTopicId;

      // Set default agent for dropdown *after* setting topicId and getting agents
      if (!selectedAgentId.value && agents.value.length > 0) {
        // Try to use agent from active topic, fallback to first agent
        // Note: topics list might not be available yet, handled in topic_list_update too
        const activeTopicAgent = initialActiveTopicId
          ? topics.value.find((t) => t.id === initialActiveTopicId)?.agent_id
          : null;
        selectedAgentId.value = activeTopicAgent || getDefaultAgentId();
        console.log(
          `[WS Handle] Initial selected agent set to: ${selectedAgentId.value}`
        );
      }

      // If starting fresh (no active topic), focus the input field
      if (initialActiveTopicId === null) {
        console.log(
          "[WS Handle] Initial state has no active topic, focusing input."
        );
        focusChatInput();
      }
    }

    function handleTopicListUpdate(payload) {
      console.log(
        `[WS Handle] Updating topic list (${payload?.length || 0} topics)`
      );
      topics.value = payload || [];
      // Ensure an agent is selected if none was set during initial state
      // (e.g., if topic list arrived later or initial topic was null)
      if (!selectedAgentId.value && agents.value.length > 0) {
        const activeTopic = topics.value.find(
          (t) => t.id === currentTopicId.value
        );
        selectedAgentId.value = activeTopic
          ? activeTopic.agent_id
          : getDefaultAgentId();
        console.log(
          "[WS Handle] Ensured selected agent via topic list:",
          selectedAgentId.value
        );
      }
    }

    function handleTopicState(payload) {
      console.log(
        `[WS Handle] Receiving full state for topic: ${payload?.topic_id}`
      );
      if (payload.topic_id) {
        // Update the local cache for this topic's messages and results
        messages.value[payload.topic_id] = payload.messages || [];
        taskResults.value[payload.topic_id] = payload.task_results || [];
        // If this state is for the currently viewed topic, scroll to bottom
        if (payload.topic_id === currentTopicId.value) {
          scrollToBottom(true); // Force scroll when full state loads
        }
      }
      // Sync the agent dropdown if the state is for the current topic
      if (
        payload.topic_id === currentTopicId.value &&
        selectedAgentId.value !== payload.agent_id
      ) {
        console.log(
          `[WS Handle] Updating selected agent to match topic state: ${payload.agent_id}`
        );
        selectedAgentId.value = payload.agent_id;
      }
    }

    function handleNewMessage(payload) {
      console.log(
        `[WS Handle] New message received for topic ${payload?.topic_id}`
      );
      if (payload.topic_id) {
        // Ensure the message array exists for this topic
        if (!messages.value[payload.topic_id]) {
          messages.value[payload.topic_id] = [];
        }
        // Add the message only if its ID isn't already present
        if (
          !messages.value[payload.topic_id].some((m) => m.id === payload.id)
        ) {
          messages.value[payload.topic_id].push(payload);
          // If the message is for the topic currently being viewed, scroll
          if (payload.topic_id === currentTopicId.value) {
            scrollToBottom(); // Smooth scroll for new incoming messages
          }
        } else {
          // Log if a duplicate message ID is received (should be rare)
          console.warn(
            `[WS Handle] Duplicate message ID ${payload.id} received, skipped.`
          );
        }
      } else {
        console.warn(
          "[WS Handle] Received new_message without topic_id:",
          payload
        );
      }
    }

    function handleNewTaskResult(payload) {
      console.log(`[WS Handle] New task result for topic ${payload?.topic_id}`);
      if (payload.topic_id) {
        // Ensure the results array exists
        if (!taskResults.value[payload.topic_id]) {
          taskResults.value[payload.topic_id] = [];
        }
        // Add if not already present
        if (
          !taskResults.value[payload.topic_id].some((r) => r.id === payload.id)
        ) {
          taskResults.value[payload.topic_id].push(payload);
          // TODO: Optionally add visual feedback in the right panel (e.g., scroll, highlight)
        }
      } else {
        console.warn(
          "[WS Handle] Received new_task_result without topic_id:",
          payload
        );
      }
    }

    function handleActiveTopicUpdate(payload) {
      console.log(
        `[WS Handle] Active topic update received. New active topic: ${payload?.topic_id}`
      );
      const newActiveId = payload?.topic_id; // Can be null
      if (newActiveId !== currentTopicId.value) {
        // Update the central state if the active topic has changed
        currentTopicId.value = newActiveId;
        // If the new active topic is null, trigger the 'new chat' UI state
        if (newActiveId === null) {
          focusChatInput();
        } else {
          // If switching to a valid topic, ensure agent dropdown matches
          const topic = topics.value.find((t) => t.id === newActiveId);
          if (topic && topic.agent_id !== selectedAgentId.value) {
            selectedAgentId.value = topic.agent_id;
          }
          // Consider setting loadingMessages = true here if topic_state isn't guaranteed
          // to arrive immediately after this update.
        }
      } else {
        // Confirmation for the current topic, ensure loading is off
        loadingMessages.value = false;
      }
    }

    function handleServerError(payload) {
      // Display errors sent explicitly from the server
      console.error("[WS Handle] Server Error:", payload.detail);
      alert(`Server Error: ${payload.detail || "An unknown error occurred."}`);
    }

    // Chat Interaction Logic
    function sendMessage() {
      // Sends the content of the textarea as a message.
      if (!isConnected.value) {
        console.warn("Cannot send message: WebSocket not connected.");
        alert("Not connected to the server. Please wait or refresh.");
        return;
      }
      const messageContent = newMessage.value.trim();
      if (!messageContent) {
        return;
      } // Don't send empty messages
      if (!selectedAgentId.value) {
        console.warn("Cannot send message: No agent selected.");
        alert("Please select an agent before sending a message.");
        return;
      }

      // Prepare the message payload
      const messagePayload = {
        content: messageContent,
        topic_id: currentTopicId.value, // null if starting a new chat
        current_agent_id: selectedAgentId.value, // Agent selected in UI
      };

      console.log("[Action] Sending message:", messagePayload);
      // Send the message object via WebSocket
      ws.value.send(
        JSON.stringify({
          type: "send_message",
          payload: messagePayload,
        })
      );

      // Clear the input field and reset its height after sending
      newMessage.value = "";
      if (chatInput.value) {
        chatInput.value.style.height = "44px"; // Reset to default min-height
      }
    }

    function selectTopic(topicId) {
      // Handles the user clicking on a topic in the left panel.
      console.log("[Action] Selecting topic:", topicId);
      if (topicId === currentTopicId.value || !isConnected.value) {
        if (!isConnected.value)
          console.warn("Cannot select topic: Not connected.");
        return; // Do nothing if already selected or not connected
      }

      loadingMessages.value = true; // Show loading indicator

      // Request the full state for the selected topic from the backend
      ws.value.send(
        JSON.stringify({
          type: "select_topic",
          payload: { topic_id: topicId },
        })
      );

      // Note: We let the 'active_topic_update' and 'topic_state' messages from the server
      // handle the actual state changes (currentTopicId, messages, agent dropdown)
      // to keep the frontend state consistent with the backend confirmation.
    }

    function handleAgentChange() {
      // Handles the user changing the agent via the dropdown.
      console.log(
        `[UI Action] Agent dropdown changed to: ${selectedAgentId.value}`
      );
      // If currently in the "new chat" state (no active topic), this sets the agent
      // for the *next* chat initiated by sending a message.
      if (currentTopicId.value === null) {
        console.log("Agent selected for the next new chat.");
        focusChatInput(); // Keep focus on input
      }
      // If a topic *is* active, changing the agent here only updates the 'selectedAgentId'.
      // A new topic is only created if the user *sends a message* afterwards,
      // at which point the backend compares 'selectedAgentId' with the topic's agent.
    }

    function startNewChat() {
      // Resets the UI to the initial "start chat" state.
      console.log("[Action] Starting new chat setup...");
      currentTopicId.value = null; // Deselect topic -> triggers welcome screen via v-if
      newMessage.value = ""; // Clear input field

      // Reset textarea height
      if (chatInput.value) {
        chatInput.value.style.height = "44px";
      }

      // Reset agent dropdown to the default agent
      const defaultAgent = getDefaultAgentId();
      if (defaultAgent) {
        selectedAgentId.value = defaultAgent;
        console.log("[Action] Reset agent to default:", defaultAgent);
      } else {
        console.warn("[Action] No default agent available to select.");
      }

      console.log("[Action] New chat setup complete. Focusing input.");
      focusChatInput(); // Set focus to the input field
    }

    // UI Toggles and Helper Functions
    function toggleLeftPanel() {
      isLeftPanelOpen.value = !isLeftPanelOpen.value;
    }
    function toggleRightPanel() {
      isRightPanelOpen.value = !isRightPanelOpen.value;
    }
    function toggleTheme() {
      isDarkMode.value = !isDarkMode.value;
    } // Watcher applies the change

    function applyTheme() {
      // Applies the 'dark' class to the HTML element based on isDarkMode state.
      if (isDarkMode.value) {
        document.documentElement.classList.add("dark");
        localStorage.setItem("aiAgentTheme", "dark"); // Persist choice
      } else {
        document.documentElement.classList.remove("dark");
        localStorage.setItem("aiAgentTheme", "light");
      }
    }

    function getAgentName(agentId) {
      // Finds the agent name from the loaded agents list.
      const agent = agents.value.find((a) => a.id === agentId);
      return agent ? agent.name : "Unknown Agent";
    }

    function getDefaultAgentId() {
      // Gets the ID of the first agent in the list, considered the default.
      return agents.value.length > 0 ? agents.value[0].id : null;
    }

    function formatTimestamp(isoString) {
      // Formats an ISO timestamp string into a locale-specific time string (e.g., "3:45 PM").
      if (!isoString) return "";
      try {
        return new Date(isoString).toLocaleTimeString([], {
          hour: "numeric",
          minute: "2-digit",
        });
      } catch (e) {
        console.warn("Invalid timestamp format received:", isoString);
        return "Invalid Date";
      }
    }

    function autoGrowTextarea(event) {
      // Dynamically adjusts the height of the textarea based on content.
      const textarea = event.target;
      textarea.style.height = "auto"; // Reset height to recalculate scrollHeight
      // Clamp height between min (44px) and max (150px)
      const newHeight = Math.max(44, Math.min(textarea.scrollHeight, 150));
      textarea.style.height = `${newHeight}px`;
    }

    function focusChatInput() {
      // Sets focus to the chat input textarea, waiting for DOM updates if necessary.
      nextTick(() => {
        // Ensures element is available after potential v-if changes
        chatInput.value?.focus();
        console.log("[Focus] Attempted to focus chat input.");
      });
    }

    function scrollToBottom(force = false) {
      // Scrolls the message area to the bottom.
      // If 'force' is true, scrolls regardless of current position.
      // Otherwise, only scrolls if the user is already near the bottom.
      nextTick(() => {
        // Wait for DOM updates after new messages are added
        const el = messageArea.value;
        if (el) {
          const threshold = 150; // How many pixels from bottom to consider "near"
          const isNearBottom =
            el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
          if (force || isNearBottom) {
            el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
            console.log("[Scroll] Scrolled to bottom.");
          } else {
            console.log("[Scroll] User is scrolled up, auto-scroll skipped.");
          }
        }
      });
    }

    // Responsive Layout Check
    const checkMobile = () => {
      // Updates the isMobile state based on window width.
      const isNowMobile = window.innerWidth < 1024; // Tailwind 'lg' breakpoint
      if (isNowMobile !== isMobile.value) {
        isMobile.value = isNowMobile;
        console.log(
          `[Resize] Switched to ${isNowMobile ? "mobile" : "desktop"} view.`
        );
        // Note: We don't automatically change panel open state on resize
        // to preserve user's explicit toggle preference.
      }
    };

    // --- Lifecycle Hooks ---
    onMounted(() => {
      // Runs once after the component is mounted to the DOM.
      console.log("[Lifecycle] Component mounted.");

      // 1. Initialize Theme
      const storedTheme = localStorage.getItem("aiAgentTheme");
      if (storedTheme) {
        isDarkMode.value = storedTheme === "dark";
      } else {
        isDarkMode.value = window.matchMedia(
          "(prefers-color-scheme: dark)"
        ).matches;
      }
      applyTheme(); // Apply theme class to <html>
      console.log(
        `[Lifecycle] Initial theme set to: ${
          isDarkMode.value ? "dark" : "light"
        }`
      );

      // 2. Initialize Responsive State & Listener
      checkMobile(); // Check initial screen size
      window.addEventListener("resize", checkMobile); // Listen for changes
      console.log(`[Lifecycle] Initial mobile state: ${isMobile.value}`);

      // 3. Set Initial Panel Visibility
      // Default to closed on mobile, open on desktop. Could be enhanced with localStorage.
      if (isMobile.value) {
        isLeftPanelOpen.value = false;
        isRightPanelOpen.value = false;
      } else {
        isLeftPanelOpen.value = true;
        isRightPanelOpen.value = true;
      }
      console.log(
        `[Lifecycle] Initial left panel state: ${
          isLeftPanelOpen.value ? "open" : "closed"
        }`
      );
      console.log(
        `[Lifecycle] Initial right panel state: ${
          isRightPanelOpen.value ? "open" : "closed"
        }`
      );

      // 4. Establish WebSocket connection
      connectWebSocket();
    });

    onUnmounted(() => {
      // Runs when the component is about to be unmounted.
      console.log("[Lifecycle] Component unmounted.");
      // Cleanup: remove resize listener and close WebSocket connection.
      window.removeEventListener("resize", checkMobile);
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        console.log("Closing WebSocket connection on unmount.");
        ws.value.close(1000, "Client unmounting"); // Normal closure
      }
    });

    // --- Watchers (Reacting to State Changes) ---
    watch(isDarkMode, (newValue) => {
      // Apply theme whenever isDarkMode state changes.
      console.log(
        `[Watcher] Dark mode changed to: ${newValue}. Applying theme.`
      );
      applyTheme();
    });

    watch(currentTopicId, (newId, oldId) => {
      // React when the active topic changes.
      console.log(`[Watcher] currentTopicId changed from ${oldId} to ${newId}`);
      if (newId === null) {
        // If switching to the "new chat" state, ensure input focus.
        focusChatInput();
      } else {
        // If switching to a valid topic, sync the agent dropdown.
        const topic = topics.value.find((t) => t.id === newId);
        if (topic && topic.agent_id !== selectedAgentId.value) {
          selectedAgentId.value = topic.agent_id;
        }
        // Scrolling is handled when 'topic_state' or 'new_message' is received.
      }
    });

    // Return all reactive state and methods to be used in the template
    return {
      // State Refs
      clientId,
      isConnected,
      agents,
      topics,
      currentTopicId,
      selectedAgentId,
      newMessage,
      isLeftPanelOpen,
      isRightPanelOpen,
      messageArea,
      isDarkMode,
      isMobile,
      chatInput,
      loadingMessages,

      // Computed Refs
      currentMessages,
      currentTaskResults,
      currentTopicAgentId,

      // Methods
      sendMessage,
      selectTopic,
      handleAgentChange,
      getAgentName,
      formatTimestamp,
      autoGrowTextarea,
      toggleLeftPanel,
      toggleRightPanel,
      toggleTheme,
      startNewChat,
    };
  }, // End setup function
});

// Mount the Vue application to the element with id="app" in index.html
app.mount("#app");
console.log("Vue app mounted successfully.");
