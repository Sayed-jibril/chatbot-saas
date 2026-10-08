// Dashboard JavaScript for BotSaaS

// ==================== UTILITY FUNCTIONS ====================

// Format file size
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// Format date
function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return "Today";
  } else if (diffDays === 1) {
    return "Yesterday";
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  } else {
    return date.toLocaleDateString();
  }
}

// Show toast notification
function showToast(message, type = "success", duration = 3000) {
  const toast = document.createElement("div");
  toast.className = `toast bg-white rounded-lg shadow-lg p-4 border-l-4 ${
    type === "success"
      ? "border-green-500"
      : type === "error"
        ? "border-red-500"
        : type === "warning"
          ? "border-yellow-500"
          : "border-blue-500"
  }`;

  const icon =
    type === "success"
      ? "check-circle"
      : type === "error"
        ? "exclamation-circle"
        : type === "warning"
          ? "exclamation-triangle"
          : "info-circle";

  const color =
    type === "success"
      ? "text-green-500"
      : type === "error"
        ? "text-red-500"
        : type === "warning"
          ? "text-yellow-500"
          : "text-blue-500";

  toast.innerHTML = `
        <div class="flex items-center">
            <div class="flex-shrink-0">
                <i class="fas fa-${icon} ${color}"></i>
            </div>
            <div class="ml-3 flex-1">
                <p class="text-sm font-medium text-gray-900">${message}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-gray-400 hover:text-gray-600">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("fade-out");
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Show confirmation dialog
async function showConfirm(message) {
  return new Promise((resolve) => {
    // Create modal
    const modal = document.createElement("div");
    modal.className =
      "fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50";
    modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-sm mx-4">
                <div class="flex items-center mb-4">
                    <div class="flex-shrink-0 w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center">
                        <i class="fas fa-exclamation-triangle text-yellow-600"></i>
                    </div>
                    <h3 class="ml-3 text-lg font-medium text-gray-900">Confirm Action</h3>
                </div>
                <p class="text-sm text-gray-500 mb-6">${message}</p>
                <div class="flex justify-end space-x-3">
                    <button class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 cancel-btn">
                        Cancel
                    </button>
                    <button class="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 confirm-btn">
                        Confirm
                    </button>
                </div>
            </div>
        `;

    document.body.appendChild(modal);

    // Handle buttons
    modal.querySelector(".confirm-btn").addEventListener("click", () => {
      modal.remove();
      resolve(true);
    });

    modal.querySelector(".cancel-btn").addEventListener("click", () => {
      modal.remove();
      resolve(false);
    });

    // Close on click outside
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.remove();
        resolve(false);
      }
    });
  });
}

// ==================== API CALLS ====================

// Generic API request
async function apiRequest(endpoint, method = "GET", data = null) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
    },
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(endpoint, options);
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || "API request failed");
    }

    return result;
  } catch (error) {
    showToast(error.message, "error");
    throw error;
  }
}

// ==================== BOT MANAGEMENT ====================

// Create new bot
async function createBot(formData) {
  try {
    const response = await fetch("/dashboard/api/bots", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (response.ok) {
      showToast("Bot created successfully!", "success");
      return data;
    } else {
      showToast(data.detail || "Error creating bot", "error");
      return null;
    }
  } catch (error) {
    showToast("Network error. Please try again.", "error");
    return null;
  }
}

// Update bot
async function updateBot(botId, data) {
  try {
    const response = await fetch(`/dashboard/api/bots/${botId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (response.ok) {
      showToast("Bot updated successfully!", "success");
      return result;
    } else {
      showToast(result.detail || "Error updating bot", "error");
      return null;
    }
  } catch (error) {
    showToast("Network error. Please try again.", "error");
    return null;
  }
}

// Delete bot
async function deleteBot(botId, botName) {
  const confirmed = await showConfirm(
    `Are you sure you want to delete "${botName}"? This will delete all associated documents and conversations.`,
  );

  if (!confirmed) return;

  try {
    const response = await fetch(`/dashboard/api/bots/${botId}`, {
      method: "DELETE",
    });

    if (response.ok) {
      showToast("Bot deleted successfully", "success");
      setTimeout(() => window.location.reload(), 1500);
    } else {
      const data = await response.json();
      showToast(data.detail || "Error deleting bot", "error");
    }
  } catch (error) {
    showToast("Network error. Please try again.", "error");
  }
}

// ==================== DOCUMENT MANAGEMENT ====================

// Upload document
async function uploadDocument(botId, file, onProgress) {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("bot_id", botId);
    formData.append("file", file);

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && onProgress) {
        const percent = Math.round((e.loaded / e.total) * 100);
        onProgress(percent);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 200) {
        const response = JSON.parse(xhr.responseText);
        resolve(response);
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || "Upload failed"));
        } catch {
          reject(new Error("Upload failed"));
        }
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Network error"));
    });

    xhr.open("POST", "/dashboard/api/documents/upload", true);
    xhr.send(formData);
  });
}

// Delete document
async function deleteDocument(docId, fileName) {
  const confirmed = await showConfirm(
    `Are you sure you want to delete "${fileName}"?`,
  );

  if (!confirmed) return;

  try {
    const response = await fetch(`/dashboard/api/documents/${docId}`, {
      method: "DELETE",
    });

    if (response.ok) {
      showToast("Document deleted successfully", "success");
      setTimeout(() => window.location.reload(), 1500);
    } else {
      const data = await response.json();
      showToast(data.detail || "Error deleting document", "error");
    }
  } catch (error) {
    showToast("Network error. Please try again.", "error");
  }
}

// ==================== ANALYTICS ====================

// Load dashboard stats
async function loadDashboardStats() {
  try {
    const response = await fetch("/dashboard/api/stats");
    const stats = await response.json();

    // Update UI with stats
    document.querySelectorAll("[data-stat]").forEach((el) => {
      const statName = el.dataset.stat;
      if (stats[statName] !== undefined) {
        el.textContent = stats[statName];
      }
    });
  } catch (error) {
    console.error("Error loading stats:", error);
  }
}

// ==================== CHAT WIDGET ====================

// Preview bot in widget
function previewBot(botId) {
  const preview = window.open("", "BotPreview", "width=400,height=600");
  preview.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bot Preview</title>
            <style>
                body { margin: 0; padding: 0; height: 100vh; }
                iframe { width: 100%; height: 100%; border: none; }
            </style>
        </head>
        <body>
            <iframe src="/widget/chat/${botId}"></iframe>
        </body>
        </html>
    `);
}

// ==================== INITIALIZATION ====================

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
  // Load stats if on dashboard
  if (document.querySelector("[data-stat]")) {
    loadDashboardStats();
  }

  // Initialize tooltips
  document.querySelectorAll("[data-tooltip]").forEach((el) => {
    el.classList.add("tooltip");
  });

  // Handle logout
  const logoutBtn = document.querySelector("[data-logout]");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      const confirmed = await showConfirm("Are you sure you want to logout?");
      if (confirmed) {
        window.location.href = "/auth/logout";
      }
    });
  }

  // Auto-hide alerts after 5 seconds
  document.querySelectorAll(".alert").forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.5s";
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });
});

// Export functions for use in other scripts
window.BotSaaS = {
  showToast,
  showConfirm,
  formatFileSize,
  formatDate,
  apiRequest,
  createBot,
  updateBot,
  deleteBot,
  uploadDocument,
  deleteDocument,
  previewBot,
};
