const { createApp, ref, computed, watch, nextTick, onMounted, onUnmounted } =
  Vue;

const app = createApp({
  delimiters: ["[[", "]]"], // Use [[ ]] for Vue to avoid Jinja2 conflict
  setup() {
    // At the top of setup()
    function uuidv4() {
      // Make sure UUID function is available first
      return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, (c) =>
        (
          c ^
          (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))
        ).toString(16)
      );
    }

    // Persist client ID using localStorage
    const storedClientId = localStorage.getItem("aiAgentClientId");
    const clientId = ref(storedClientId || `user_${uuidv4()}`); // Use stored or generate new
    if (!storedClientId) {
      localStorage.setItem("aiAgentClientId", clientId.value); // Store if newly generated
      console.log("Generated and stored new client ID:", clientId.value);
    } else {
      console.log("Retrieved client ID from localStorage:", clientId.value);
    }
    // State
    const ws = ref(null);
    const isConnected = ref(false);
    const agents = ref([]); // {id: string, name: string}[]
    const topics = ref([]); // {id: string, agent_id: string, name: string}[]
    const chatInput = ref(null); // Ref for the textarea
    const loadingMessages = ref(false); // Optional loading state
    const currentTopicId = ref(null);
    const selectedAgentId = ref(null); // Agent selected in the dropdown
    const messages = ref({}); // { topic_id: Message[] }
    const taskResults = ref({}); // { topic_id: TaskResult[] }
    const newMessage = ref("");
    const messageArea = ref(null); // Template ref for message display div
    const isDarkMode = ref(false);
    const isLeftPanelOpen = ref(true); // Default open state
    const isRightPanelOpen = ref(true);
    const isMobile = ref(false); // Add mobile state checker

    // Function to apply the theme
    function applyTheme() {
      if (isDarkMode.value) {
        document.documentElement.classList.add("dark");
        localStorage.setItem("aiAgentTheme", "dark");
      } else {
        document.documentElement.classList.remove("dark");
        localStorage.setItem("aiAgentTheme", "light");
      }
    }

    // Function to toggle theme
    function toggleTheme() {
      isDarkMode.value = !isDarkMode.value;
      applyTheme();
    }

    // Watch for changes and apply theme
    watch(isDarkMode, applyTheme);

    // --- Computed Properties ---
    const currentMessages = computed(() => {
      return currentTopicId.value
        ? messages.value[currentTopicId.value] || []
        : [];
    });

    const currentTaskResults = computed(() => {
      return currentTopicId.value
        ? taskResults.value[currentTopicId.value] || []
        : [];
    });

    const currentTopicAgentId = computed(() => {
      const topic = topics.value.find((t) => t.id === currentTopicId.value);
      return topic ? topic.agent_id : null;
    });

    // --- Methods ---
    function uuidv4() {
      // Simple UUID generator
      return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, (c) =>
        (
          c ^
          (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))
        ).toString(16)
      );
    }

    function connectWebSocket() {
      // Determine WebSocket protocol based on window location protocol
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${wsProtocol}//${window.location.host}/ws/${clientId.value}`;
      console.log("Connecting to WebSocket:", wsUrl);

      ws.value = new WebSocket(wsUrl);

      ws.value.onopen = () => {
        console.log("WebSocket Connected");
        isConnected.value = true;
        // Optional: Implement ping/pong or keep-alive mechanism
      };

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("Message received:", data);
          handleWebSocketMessage(data);
        } catch (e) {
          console.error("Failed to parse WebSocket message:", event.data, e);
        }
      };

      ws.value.onerror = (error) => {
        console.error("WebSocket Error:", error);
        isConnected.value = false;
        // Optional: Implement reconnection logic here
      };

      ws.value.onclose = (event) => {
        console.log("WebSocket Closed:", event.reason, event.code);
        isConnected.value = false;
        // Optional: Implement reconnection logic or notify user
        if (event.code === 1008 && event.reason === "Session already active") {
          alert(
            "Another session is already active for this client. Please close the other tab/window."
          );
        } else if (event.code === 1011) {
          // Server error during setup
          alert(
            "Server error during connection setup. Please try again later."
          );
        }
      };
    }

    function handleWebSocketMessage(data) {
      const { type, payload } = data;
      console.log(`[WS Received] Type: ${type}, Payload:`, payload);

      loadingMessages.value = false; // Stop loading on any relevant message

      switch (type) {
        case "initial_state":
          agents.value = payload.agents || [];
          const initialActiveTopicId = payload.active_topic_id; // Can be null

          // Set currentTopicId *before* trying to set default agent
          currentTopicId.value = initialActiveTopicId;

          if (!selectedAgentId.value && payload.agents.length > 0) {
            // Set default agent based on active topic's agent OR first agent
            const activeTopic = topics.value.find(
              (t) => t.id === initialActiveTopicId
            ); // Need topics list first ideally
            const agentToSelect = activeTopic
              ? activeTopic.agent_id
              : getDefaultAgentId();
            selectedAgentId.value = agentToSelect;
          }

          // If starting with no active topic, focus input
          if (initialActiveTopicId === null) {
            console.log(
              "[Init] No active topic found, focusing input for new chat."
            );
            focusChatInput();
          }
          break;
        case "topic_list_update":
          topics.value = payload || [];
          // After getting topic list, ensure selectedAgentId is set if it wasn't during initial_state
          if (!selectedAgentId.value && agents.value.length > 0) {
            const activeTopic = topics.value.find(
              (t) => t.id === currentTopicId.value
            );
            const agentToSelect = activeTopic
              ? activeTopic.agent_id
              : getDefaultAgentId();
            selectedAgentId.value = agentToSelect;
            console.log(
              "[Topic List] Ensured selectedAgentId is set:",
              selectedAgentId.value
            );
          }
          break;
        case "topic_state":
          if (payload.topic_id) {
            messages.value[payload.topic_id] = payload.messages || [];
            taskResults.value[payload.topic_id] = payload.task_results || [];
            if (payload.topic_id === currentTopicId.value) {
              scrollToBottom();
            }
          }
          // Update selected agent if necessary
          if (
            payload.topic_id === currentTopicId.value &&
            selectedAgentId.value !== payload.agent_id
          ) {
            selectedAgentId.value = payload.agent_id;
          }
          break;
        case "new_message":
          if (payload.topic_id) {
            if (!messages.value[payload.topic_id]) {
              messages.value[payload.topic_id] = [];
            }
            if (
              !messages.value[payload.topic_id].some((m) => m.id === payload.id)
            ) {
              messages.value[payload.topic_id].push(payload);
              if (payload.topic_id === currentTopicId.value) {
                scrollToBottom();
              }
            } else {
              console.warn(
                `[Vue] Duplicate message ID ${payload.id} received, skipped.`
              );
            }
          }
          break;
        case "new_task_result":
          if (payload.topic_id) {
            if (!taskResults.value[payload.topic_id]) {
              taskResults.value[payload.topic_id] = [];
            }
            if (
              !taskResults.value[payload.topic_id].some(
                (r) => r.id === payload.id
              )
            ) {
              taskResults.value[payload.topic_id].push(payload);
            }
          }
          break;
        case "active_topic_update":
          if (payload.topic_id && payload.topic_id !== currentTopicId.value) {
            console.log(
              "[WS Received] Setting active topic from server:",
              payload.topic_id
            );
            currentTopicId.value = payload.topic_id;
            // Topic state should be requested or sent by server after this
            // We might want to set loading state here if server doesn't send state immediately
            // loadingMessages.value = true;
          } else if (
            payload.topic_id &&
            payload.topic_id === currentTopicId.value
          ) {
            console.log(
              "[WS Received] Active topic confirmation for current topic:",
              payload.topic_id
            );
            // Ensure loading is false if confirming current topic
            loadingMessages.value = false;
          }
          break;
        case "error":
          console.error("Server Error:", payload.detail);
          alert(`Server Error: ${payload.detail}`);
          break;
        case "pong":
          // console.log("Pong received");
          break;
        default:
          console.warn("Unknown message type:", type);
      }
    }

    function sendMessage() {
      if (
        !ws.value ||
        ws.value.readyState !== WebSocket.OPEN ||
        !newMessage.value.trim()
      ) {
        return;
      }

      // Determine the target topic ID
      // If currentTopicId exists, use it. Otherwise, it's the first message
      // for a new topic (backend will handle creation).
      const targetTopicId = currentTopicId.value; // Can be null for first message

      const message = {
        type: "send_message",
        payload: {
          content: newMessage.value.trim(),
          topic_id: targetTopicId, // Backend checks this
          current_agent_id: selectedAgentId.value, // Agent selected in UI
        },
      };
      console.log("Sending message:", message);
      ws.value.send(JSON.stringify(message));
      newMessage.value = ""; // Clear input after sending
      // Reset textarea height after sending
      const textarea = document.querySelector("textarea");
      if (textarea) {
        textarea.style.height = "40px";
      }
    }

    function selectTopic(topicId) {
      console.log("Selecting topic:", topicId);
      if (topicId === currentTopicId.value) return;

      loadingMessages.value = true; // Set loading state

      const message = { type: "select_topic", payload: { topic_id: topicId } };
      ws.value.send(JSON.stringify(message));

      // Optimistically set currentTopicId - might be updated by server confirmation
      currentTopicId.value = topicId;

      const topic = topics.value.find((t) => t.id === topicId);
      if (topic && topic.agent_id !== selectedAgentId.value) {
        selectedAgentId.value = topic.agent_id;
      }
      // Don't scroll until messages are loaded (via topic_state)
      // scrollToBottom(true);
    }

    function handleAgentChange() {
      console.log(`Agent dropdown changed to: ${selectedAgentId.value}`);
      // Important: Changing the agent via dropdown WHILE a topic is active
      // should *not* immediately create a new topic.
      // A new topic is only created when a *message is sent*
      // with an agent different from the current topic's agent.
      // This function mainly updates the `selectedAgentId` state.
      // If there's no active topic (e.g., first load), selecting an agent
      // prepares for the first message to create a topic with that agent.
    }

    function getAgentName(agentId) {
      const agent = agents.value.find((a) => a.id === agentId);
      return agent ? agent.name : "Unknown";
    }

    function formatTimestamp(isoString) {
      if (!isoString) return "";
      try {
        return new Date(isoString).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });
      } catch (e) {
        return "Invalid Date";
      }
    }

    function autoGrowTextarea(event) {
      const textarea = event.target;
      textarea.style.height = "auto"; // Reset height
      textarea.style.height = `${textarea.scrollHeight}px`; // Set to scroll height
    }

    function scrollToBottom(force = false) {
      // Use nextTick to wait for DOM update after state change
      nextTick(() => {
        console.log("[Scroll] Attempting scroll..."); // Log scroll attempt
        const el = messageArea.value;
        if (el) {
          console.log(
            `[Scroll] Message area found. ScrollHeight: ${el.scrollHeight}, ScrollTop: ${el.scrollTop}, ClientHeight: ${el.clientHeight}`
          ); // Log element state
          // Simplified: Always scroll to bottom for debugging
          el.scrollTop = el.scrollHeight;
          console.log(`[Scroll] Scrolled to bottom (${el.scrollTop}).`); // Log after scroll
        } else {
          console.warn("[Scroll] messageArea ref not available."); // Warning if ref is missing
        }
      });
    }

    function toggleLeftPanel() {
      isLeftPanelOpen.value = !isLeftPanelOpen.value;
    }

    function toggleRightPanel() {
      isRightPanelOpen.value = !isRightPanelOpen.value;
    }
    function getDefaultAgentId() {
      return agents.value.length > 0 ? agents.value[0].id : null;
    }

    function focusChatInput() {
      // Use nextTick to wait for potential DOM updates before focusing
      nextTick(() => {
        chatInput.value?.focus();
        console.log("[Focus] Attempted to focus chat input.");
      });
    }

    function startNewChat() {
      console.log("[Action] Starting new chat setup...");
      currentTopicId.value = null;
      newMessage.value = "";
      const textarea = chatInput.value; // Use template ref
      if (textarea) {
        textarea.style.height = "44px";
      }

      const defaultAgent = getDefaultAgentId();
      if (defaultAgent) {
        selectedAgentId.value = defaultAgent;
      } else if (agents.value.length > 0) {
        selectedAgentId.value = agents.value[0].id;
      } else {
        console.warn("[Action] No agents available.");
      }

      console.log("[Action] New chat setup complete. Focusing input.");
      focusChatInput(); // Focus after state updates
    }

    // --- Resize Handler ---
    const checkMobile = () => {
      // Tailwind's lg breakpoint is typically 1024px
      isMobile.value = window.innerWidth < 1024;
      // Optional: Automatically adjust panel state on resize
      // if (isMobile.value) {
      //   isLeftPanelOpen.value = false; // Auto-close on switch to mobile?
      // } else {
      //   isLeftPanelOpen.value = true; // Auto-open on switch to desktop?
      // }
      console.log(`[Resize] isMobile: ${isMobile.value}`);
    };

    // --- Lifecycle Hooks ---
    watch(currentTopicId, (newTopicId, oldTopicId) => {
      console.log(
        `Watched currentTopicId change: ${oldTopicId} -> ${newTopicId}`
      );
      // If the topic changes, we might need to scroll or update agent selector
      if (newTopicId) {
        const topic = topics.value.find((t) => t.id === newTopicId);
        if (topic && topic.agent_id !== selectedAgentId.value) {
          selectedAgentId.value = topic.agent_id;
        }
        // Ensure data for the new topic is loaded if needed (selectTopic handles this)
        scrollToBottom(true); // Scroll when topic ID changes
      }
    });

    onMounted(() => {
      // Check initial theme preference on load
      const storedTheme = localStorage.getItem("aiAgentTheme");
      if (storedTheme) {
        isDarkMode.value = storedTheme === "dark";
      } else {
        isDarkMode.value = window.matchMedia(
          "(prefers-color-scheme: dark)"
        ).matches;
      }
      // Apply initial theme immediately without waiting for watcher
      if (isDarkMode.value) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }

      // Initial mobile check
      checkMobile();
      // Add resize listener
      window.addEventListener("resize", checkMobile);

      // Initial panel state IS set here based on initial mobile status,
      // but this only runs ONCE on mount.
      if (isMobile.value) {
        isLeftPanelOpen.value = false;
      } else {
        isLeftPanelOpen.value = true;
      }
      console.log(
        `Initial theme set to: ${isDarkMode.value ? "dark" : "light"}`
      );
      console.log(`Initial mobile state: ${isMobile.value}`);
      console.log(
        `Initial left panel state: ${isLeftPanelOpen.value ? "open" : "closed"}`
      );
      console.log(
        `Initial right panel state: ${
          isRightPanelOpen.value ? "open" : "closed"
        }`
      );

      // Connect WebSocket
      connectWebSocket();
    });

    // Cleanup listener on component unmount
    onUnmounted(() => {
      window.removeEventListener("resize", checkMobile);
      console.log("[Lifecycle] Resize listener removed.");
    });

    return {
      // State
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

      // Computed
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
  },
});

app.mount("#app");
