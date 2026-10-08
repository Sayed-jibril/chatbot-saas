/**
 * BotSaaS Widget - Professional Embeddable Chat Widget
 * Version: 1.0.0
 *
 * Usage:
 * <script src="https://yourdomain.com/widget.js" data-bot-id="YOUR_BOT_ID"></script>
 */

(function () {
  "use strict";

  // Configuration
  const config = {
    apiUrl: "https://yourdomain.com", // Change to your domain
    botId: null,
    primaryColor: "#3B82F6",
    position: "bottom-right",
    buttonSize: 60,
    mobileBreakpoint: 640,
    debug: false,
  };

  // State
  let widget = null;
  let isOpen = false;
  let sessionId = null;
  let unreadCount = 0;

  // Get bot ID from script tag
  const scripts = document.getElementsByTagName("script");
  const currentScript = scripts[scripts.length - 1];

  if (currentScript) {
    config.botId = currentScript.getAttribute("data-bot-id");
    config.primaryColor =
      currentScript.getAttribute("data-color") || config.primaryColor;
    config.position =
      currentScript.getAttribute("data-position") || config.position;

    // Allow custom API URL for development
    if (currentScript.getAttribute("data-api-url")) {
      config.apiUrl = currentScript.getAttribute("data-api-url");
    }

    // Debug mode
    config.debug = currentScript.getAttribute("data-debug") === "true";
  }

  // Log if debug mode
  function log(...args) {
    if (config.debug) {
      console.log("[BotSaaS Widget]", ...args);
    }
  }

  // Validate bot ID
  if (!config.botId) {
    console.error(
      '[BotSaaS Widget] Error: No bot ID provided. Please add data-bot-id="YOUR_BOT_ID" to the script tag.',
    );
    return;
  }

  log("Initializing with bot ID:", config.botId);

  // Load session from localStorage
  try {
    sessionId = localStorage.getItem("botsaas_session_" + config.botId);
    log("Loaded session:", sessionId);
  } catch (e) {
    log("Could not access localStorage:", e);
  }

  // Create styles
  const styles = `
        #botsaas-widget-container {
            all: initial;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            position: fixed;
            z-index: 999999;
            bottom: 20px;
            right: 20px;
            left: auto;
        }
        
        #botsaas-widget-container.position-bottom-left {
            right: auto;
            left: 20px;
        }
        
        #botsaas-widget-button {
            width: ${config.buttonSize}px;
            height: ${config.buttonSize}px;
            border-radius: 50%;
            background: ${config.primaryColor};
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s, box-shadow 0.2s;
            position: relative;
            margin-left: auto;
        }
        
        #botsaas-widget-button:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
        }
        
        #botsaas-widget-button:active {
            transform: scale(0.95);
        }
        
        #botsaas-widget-button-icon {
            width: 28px;
            height: 28px;
            fill: white;
        }
        
        #botsaas-widget-button-close {
            width: 20px;
            height: 20px;
            fill: white;
            display: none;
        }
        
        #botsaas-widget-button.open #botsaas-widget-button-icon {
            display: none;
        }
        
        #botsaas-widget-button.open #botsaas-widget-button-close {
            display: block;
        }
        
        #botsaas-widget-unread {
            position: absolute;
            top: -5px;
            right: -5px;
            background: #ef4444;
            color: white;
            font-size: 12px;
            font-weight: bold;
            min-width: 20px;
            height: 20px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 6px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            border: 2px solid white;
            display: none;
        }
        
        #botsaas-widget-unread.visible {
            display: flex;
        }
        
        #botsaas-widget-iframe-container {
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 380px;
            height: 600px;
            max-width: calc(100vw - 40px);
            max-height: calc(100vh - 110px);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.25);
            display: none;
            background: white;
            transform-origin: bottom right;
            animation: botsaas-slide-in 0.2s ease-out;
        }
        
        #botsaas-widget-container.position-bottom-left #botsaas-widget-iframe-container {
            right: auto;
            left: 20px;
            transform-origin: bottom left;
        }
        
        #botsaas-widget-iframe-container.open {
            display: block;
        }
        
        @keyframes botsaas-slide-in {
            from {
                opacity: 0;
                transform: scale(0.8);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        #botsaas-widget-iframe {
            width: 100%;
            height: 100%;
            border: none;
            background: white;
        }
        
        #botsaas-widget-powered-by {
            text-align: center;
            padding: 8px;
            font-size: 11px;
            color: #9ca3af;
            background: #f9fafb;
            border-top: 1px solid #e5e7eb;
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
        }
        
        #botsaas-widget-powered-by a {
            color: ${config.primaryColor};
            text-decoration: none;
        }
        
        #botsaas-widget-powered-by a:hover {
            text-decoration: underline;
        }
        
        /* Mobile styles */
        @media (max-width: 640px) {
            #botsaas-widget-iframe-container {
                width: 100vw;
                height: 100vh;
                max-width: 100vw;
                max-height: 100vh;
                bottom: 0;
                right: 0;
                left: 0;
                border-radius: 0;
                top: 0;
                position: fixed;
            }
            
            #botsaas-widget-container.position-bottom-left #botsaas-widget-iframe-container {
                left: 0;
            }
            
            #botsaas-widget-button {
                margin-bottom: env(safe-area-inset-bottom, 0);
            }
        }
    `;

  // Inject styles
  const styleElement = document.createElement("style");
  styleElement.textContent = styles;
  document.head.appendChild(styleElement);

  // Create widget HTML
  widget = document.createElement("div");
  widget.id = "botsaas-widget-container";
  widget.className = `position-${config.position}`;

  widget.innerHTML = `
        <div id="botsaas-widget-iframe-container">
            <iframe id="botsaas-widget-iframe" 
                    src="${config.apiUrl}/widget/chat/${config.botId}${sessionId ? "?session=" + sessionId : ""}"
                    allow="microphone">
            </iframe>
            <div id="botsaas-widget-powered-by">
                Powered by <a href="${config.apiUrl}" target="_blank">BotSaaS</a>
            </div>
        </div>
        <button id="botsaas-widget-button">
            <svg id="botsaas-widget-button-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
            </svg>
            <svg id="botsaas-widget-button-close" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
            <span id="botsaas-widget-unread"></span>
        </button>
    `;

  document.body.appendChild(widget);

  // Get elements
  const button = document.getElementById("botsaas-widget-button");
  const iframeContainer = document.getElementById(
    "botsaas-widget-iframe-container",
  );
  const iframe = document.getElementById("botsaas-widget-iframe");
  const unreadBadge = document.getElementById("botsaas-widget-unread");

  // Toggle chat
  function toggleChat() {
    isOpen = !isOpen;

    if (isOpen) {
      iframeContainer.classList.add("open");
      button.classList.add("open");
      unreadBadge.classList.remove("visible");
      unreadCount = 0;

      // Focus iframe
      iframe.focus();

      // Send open event to iframe
      iframe.contentWindow.postMessage(
        {
          type: "widget",
          event: "open",
        },
        "*",
      );

      log("Chat opened");
    } else {
      iframeContainer.classList.remove("open");
      button.classList.remove("open");

      // Send close event to iframe
      iframe.contentWindow.postMessage(
        {
          type: "widget",
          event: "close",
        },
        "*",
      );

      log("Chat closed");
    }
  }

  // Handle button click
  button.addEventListener("click", toggleChat);

  // Handle messages from iframe
  window.addEventListener("message", function (event) {
    // Verify origin
    if (!event.data || event.data.type !== "widget") return;

    log("Received message from iframe:", event.data);

    switch (event.data.event) {
      case "loaded":
        log("Chat iframe loaded");
        break;

      case "message":
        // New message from visitor (not from user)
        if (event.data.role === "assistant" && !isOpen) {
          unreadCount++;
          unreadBadge.textContent = unreadCount;
          unreadBadge.classList.add("visible");
        }
        break;

      case "session":
        // Save session ID
        if (event.data.sessionId) {
          sessionId = event.data.sessionId;
          try {
            localStorage.setItem("botsaas_session_" + config.botId, sessionId);
            log("Saved session:", sessionId);
          } catch (e) {
            log("Could not save session:", e);
          }
        }
        break;

      case "close":
        // Request to close from iframe
        if (isOpen) {
          toggleChat();
        }
        break;

      case "resize":
        // Handle resize if needed
        break;
    }
  });

  // Handle escape key
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && isOpen) {
      toggleChat();
    }
  });

  // Handle click outside (optional - uncomment if desired)
  /*
    document.addEventListener('click', function(event) {
        if (isOpen && !widget.contains(event.target)) {
            toggleChat();
        }
    });
    */

  // Send ready message to iframe when it loads
  iframe.addEventListener("load", function () {
    iframe.contentWindow.postMessage(
      {
        type: "widget",
        event: "ready",
        config: {
          botId: config.botId,
          primaryColor: config.primaryColor,
          position: config.position,
        },
      },
      "*",
    );

    log("Widget ready, sent to iframe");
  });

  // Check if there was an existing session
  if (sessionId) {
    log("Restored session:", sessionId);
  }

  // Add support for programmatic control
  window.BotSaaS = window.BotSaaS || {};
  window.BotSaaS.widget = {
    open: function () {
      if (!isOpen) toggleChat();
    },
    close: function () {
      if (isOpen) toggleChat();
    },
    toggle: toggleChat,
    setColor: function (color) {
      config.primaryColor = color;
      button.style.background = color;
      document
        .getElementById("botsaas-widget-powered-by")
        .querySelector("a").style.color = color;
    },
    resetSession: function () {
      try {
        localStorage.removeItem("botsaas_session_" + config.botId);
        sessionId = null;
        iframe.src = iframe.src.split("?")[0];
        log("Session reset");
      } catch (e) {
        log("Could not reset session:", e);
      }
    },
  };

  log("Widget initialized successfully");
})();
