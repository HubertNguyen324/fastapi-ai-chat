# **AI Agent Chat App \- Project Documentation & Next Steps**

Version: 0.1.0  
Date: April 29, 2025

## **1\. Project Overview**

This project provides a foundational skeleton for a web-based chat application designed to interact with different AI agents. It features a responsive user interface allowing users to manage multiple chat topics, select placeholder AI agents for each topic, and receive simulated asynchronous task results related to the conversation.

The core goal was to establish a robust structure incorporating:

- Real-time, bidirectional communication using WebSockets.
- A clear separation between backend logic (FastAPI) and frontend presentation (Vue.js via SSR/Jinja2).
- Persistent client sessions identified by a `client_id` stored in `localStorage`.
- Server-side session management with inactivity timeouts.
- A responsive UI with collapsible panels and light/dark mode theming.
- A modular backend architecture facilitating future expansion.

## **2\. Technology Stack**

- **Backend:**
  - Framework: FastAPI
  - Language: Python 3
  - WebSocket Server: Uvicorn with websockets library
  - Configuration: Pydantic-Settings (using .env file)
  - Templating: Jinja2
- **Frontend:**
  - Structure: Server-Side Rendering (via FastAPI/Jinja2) \+ Client-Side Hydration/Interaction
  - JavaScript Framework: Vue.js 3 (Composition API, via CDN)
  - Styling: Tailwind CSS v3
- **Database:** In-Memory Python Dictionaries (Placeholder for future DB integration)
- **Development Server:** Uvicorn

## **3\. Architecture & Modularity**

The backend application follows a standard modular structure:

- **main.py:** Initializes the FastAPI app, mounts static files, includes routers, and manages the application lifespan (startup/shutdown events, including starting/stopping the session cleanup task).
- **config.py:** Loads and provides access to application settings (e.g., session_timeout_minutes) from environment variables or a .env file using pydantic-settings.
- **models/:** Defines the data structures using Pydantic models (agent.py, chat.py) for agents, sessions, topics, messages, and task results. This ensures data integrity and clear schemas.
- **services/:** Contains the core application logic, decoupled from the web framework:
  - connection_manager.py: Manages the dictionary of active WebSocket connections, keyed by client_id. Handles connection/disconnection and provides methods for sending messages.
  - agent_manager.py: Manages the list of available AI agents (currently hardcoded placeholders).
  - chat_manager.py: The central service managing application state (sessions, topics, messages, results in memory). It handles session lifecycle, topic creation/selection, message processing orchestration, and runs the session cleanup task.
- **routers/:** Defines the web routes and WebSocket endpoint:
  - web.py: Serves the main index.html using Jinja2.
  - websocket.py: Handles the /ws/{client_id} WebSocket connection, manages the communication protocol, authenticates the connection via client_id, synchronizes initial state, and routes incoming messages to the ChatManager.
- **static/:** Contains client-side assets:
  - css/styles.css: Compiled Tailwind CSS.
  - js/app.js: The Vue.js application logic.
- **templates/:** Contains Jinja2 HTML templates, including reusable partials (\_left_panel.html, \_chat_area.html, etc.).

## **4\. Key Components & Logic**

- **Real-time Communication:** FastAPI's WebSocket support combined with the ConnectionManager enables real-time message passing between the server and specific clients. A simple JSON protocol ({"type": "...", "payload": ...}) facilitates communication.
- **State Management:**
  - **Backend:** ChatManager maintains the application state (sessions, topics) in Python dictionaries. This state is currently ephemeral and lost on server restart.
  - **Frontend:** Vue.js Composition API manages UI state (isMobile, isDarkMode, currentTopicId, etc.) and mirrors relevant data received from the backend (topics, messages, taskResults). localStorage persists the client_id and theme preference.
- **Session Handling:**
  - client_id (stored in localStorage) uniquely identifies a browser session.
  - The backend uses this client_id to associate data and manage WebSocket connections.
  - Refreshing the page uses the stored client_id to reconnect and retrieve existing session data from the ChatManager.
  - An asyncio background task in ChatManager removes data for sessions inactive beyond the configured timeout.
- **Responsive UI & UX:**
  - Tailwind CSS provides responsive design capabilities.
  - Vue dynamically adjusts classes based on isMobile state for different panel behaviors (overlay vs. push).
  - A fixed top-left button toggles the left panel.
  - Dark/Light mode is supported and persisted.
  - The "New Chat" flow provides a clear starting point, focusing the input and showing a welcome message. Topics are created implicitly on the first message send.

## **5\. Running the Application**

1. **Prerequisites:** Python 3.8+, Node.js & npm.
2. **Clone/Download:** Obtain the project code.
3. **Install Python Dependencies:**  
   pip install \-r requirements.txt

4. **Install Node Dependencies:**  
   npm install

5. **Build Tailwind CSS:**  
   npm run build:css

   (or npm run watch:css for development)

6. **Configure Environment (Optional):** Create .env file in the root and set SESSION_TIMEOUT_MINUTES=\<value\>.
7. **Run Server:**  
   uvicorn app.main:app \--reload \--host 0.0.0.0 \--port 8000

8. **Access:** Open browser to http://localhost:8000.

## **6\. Future Development & Next Steps**

This skeleton provides a strong starting point. Here's how to build upon it:

1. **Database Integration (Persistence):**
   - **Choose a Database:** MongoDB (using Motor driver for async operations) is a good fit given the document-like structure of topics and messages. PostgreSQL with JSONB fields is another option.
   - **Refactor ChatManager:** Modify all methods that currently interact with the in-memory dictionaries (self.sessions, self.topics) to perform asynchronous CRUD (Create, Read, Update, Delete) operations on the database.
     - handle_connect: Query DB for session by client_id. Create if not found. Query for topics associated with the client_id.
     - create_topic: Insert new topic document into DB.
     - get_topic: Fetch topic document by ID.
     - get_topics_for_client: Query topics collection filtered by client_id.
     - add_message_and_process: Append message to the topic's message array in the DB (or store messages in a separate collection linked by topic_id). Update last_activity on the session document.
     - \_run_cleanup_loop: Query sessions collection for documents where last_activity is older than the timeout. Delete associated topics and sessions.
   - **Data Models:** Ensure Pydantic models align with database schemas. Add indexes (e.g., on client_id, topic_id, timestamp) for performance.
2. **Real AI Agent Integration:**
   - **Abstract Agent Interaction:** Create a base class or interface for Agents in agent_manager.py or a new agents/ directory. Implement specific classes for different AI providers (OpenAI, Google Gemini, Anthropic Claude, local models via Ollama/Hugging Face).
   - **Replace Simulation:** In ChatManager.\_simulate_agent_response, instantiate the appropriate agent class based on topic.agent_id. Call its generation method, passing the message history (topic.messages).
   - **Configuration:** Store API keys, model names, system prompts securely (e.g., environment variables loaded via app.config, database).
   - **Streaming Responses:** For a better UX, modify the agent interaction and WebSocket communication to stream token responses back to the frontend as they are generated, updating the agent's message bubble incrementally. This requires changes in both backend (yielding chunks) and frontend (appending chunks). FastAPI supports StreamingResponse for HTTP, and similar chunking logic can be implemented for WebSockets.
3. **Real Task Execution:**
   - **Define Task Interface:** Create a system for defining and registering available tasks that agents can trigger.
   - **Replace Simulation:** In ChatManager.\_simulate_background_task, identify the requested task and execute it.
   - **Task Queues:** For non-trivial tasks, integrate Celery or arq. The add_message_and_process method would enqueue the task. A separate worker process would execute it and potentially send the result back via WebSocket (perhaps through a dedicated channel or by updating the database which triggers a notification).
   - **Right Panel Display:** Enhance the right panel to display task status (pending, running, completed, failed) and results more effectively.
4. **Authentication & Authorization:**
   - **Implement Login:** Add user accounts using a library like FastAPI-Users or rolling your own JWT-based authentication. Add login/registration pages/routes.
   - **Associate Data:** Link client_id / sessions to authenticated user IDs. Store user_id on Topic documents.
   - **Authorization:** Modify database queries and service logic to ensure users can only access their own topics and data. Update handle_connect to potentially require authentication.
5. **Frontend Enhancements:**
   - **Build System:** Migrate from CDN Vue to Vite for a modern build process, enabling Single File Components (.vue), TypeScript, better tooling, and optimizations.
   - **UI Library:** Consider adding a component library like Vuetify, Quasar, or PrimeVue (if using Vite) for pre-built UI elements.
   - **Chat Features:** Implement Markdown rendering, code highlighting, message editing/deletion, topic renaming/deletion, search, etc.
   - **Error Handling:** Display WebSocket connection errors or server-side processing errors more gracefully in the UI.
   - **State Management:** For more complex frontend state, consider Pinia (the official Vue state management library).
6. **Scalability & Deployment:**
   - **Database:** Choose a scalable database solution and configure connection pooling.
   - **Caching:** Implement caching (e.g., Redis) for frequently accessed data like agent lists or user profiles.
   - **Load Balancing:** Deploy multiple instances of the FastAPI application behind a load balancer (like Nginx or Traefik).
   - **WebSocket Scaling:** For large numbers of concurrent users, manage WebSocket connections across multiple instances using Redis Pub/Sub or a similar mechanism instead of the in-memory ConnectionManager.
   - **Containerization:** Use Docker and Docker Compose for consistent development and deployment environments. Deploy using Kubernetes or similar orchestration platforms.
7. **Testing:**
   - **Unit Tests:** Use pytest to test individual functions and methods in services and models. Mock external dependencies (database, AI APIs).
   - **Integration Tests:** Use FastAPI's TestClient to test HTTP endpoints and WebSocketTestClient to test WebSocket interactions.
   - **End-to-End Tests:** Use tools like Playwright or Cypress to simulate user interactions in a real browser.

By tackling these areas, this skeleton can evolve into a full-featured and robust AI chat application. Remember to prioritize based on your specific requirements and introduce complexity incrementally.
