// ✅ Spinner controls
function showSpinner() {
  const spinner = document.getElementById("spinner");
  if (spinner) spinner.style.display = "block";
}

function hideSpinner() {
  const spinner = document.getElementById("spinner");
  if (spinner) spinner.style.display = "none";
}

// ✅ Render document cards on the page
function renderDocuments(data) {
  const container = document.getElementById("recent-container");
  container.innerHTML = "";

  if (!data || data.length === 0) {
    container.innerHTML = "<p>No documents found.</p>";
    return;
  }

  data.forEach((doc, index) => {
    const card = document.createElement("div");
    card.className = "document-card";

    const correctedTextId = `corrected-text-${index}`;
    const summaryTextId = `summary-text-${index}`;

    card.innerHTML = `
      <div class="doc-header">
        <strong>${doc.filename || "Untitled Document"}</strong>
      </div>

      <div class="doc-buttons">
        <button class="copy-btn light-blue" onclick="copyFromElement('${correctedTextId}')">Copy Text</button>
        ${doc.summary ? `<button class="copy-btn light-blue" onclick="copyFromElement('${summaryTextId}')">Copy Summary</button>` : ""}
        ${doc.id ? `<button class="copy-btn" onclick="viewImage('${doc.id}')">View Image</button>` : ""}
      </div>

      <p id="${correctedTextId}" style="display: none;">${doc.corrected_text || ""}</p>
      ${doc.summary ? `<p id="${summaryTextId}" style="display: none;">${doc.summary}</p>` : ""}
    `;

    container.appendChild(card);
  });
}

// ✅ Copy to clipboard
function copyFromElement(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;

  const text = el.innerText || el.textContent;

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text)
      .then(() => alert("Text copied to clipboard!"))
      .catch(err => {
        console.error("Clipboard API failed:", err);
        fallbackCopy(text);
      });
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.left = "-9999px";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    const successful = document.execCommand("copy");
    alert(successful ? "Text copied!" : "Copy command failed.");
  } catch (err) {
    console.error("Fallback copy failed:", err);
    alert("Copy failed.");
  }
  document.body.removeChild(textArea);
}

// ✅ Fetch recent documents
async function fetchRecentDocuments() {
  try {
    const response = await fetch("http://127.0.0.1:5000/recent");
    if (!response.ok) throw new Error("Failed to fetch recent documents");

    const data = await response.json();
    renderDocuments(data);
  } catch (error) {
    console.error("Error fetching recent documents:", error);
    document.getElementById("recent-container").innerHTML = "<p>Error loading documents.</p>";
  }
}

// ✅ Search functionality
async function performSearch() {
  const query = document.getElementById("searchInput").value.trim();
  if (!query) {
    fetchRecentDocuments();
    return;
  }

  try {
    const response = await fetch(`http://127.0.0.1:5000/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error("Search failed");

    const data = await response.json();
    renderDocuments(data);
  } catch (error) {
    console.error("Search error:", error);
    document.getElementById("recent-container").innerHTML = "<p>Search failed.</p>";
  }
}

// ✅ Upload logic
document.getElementById("extractBtn")?.addEventListener("click", async () => {
  const fileInput = document.getElementById("imageInput");
  const file = fileInput?.files[0];
  if (!file) {
    alert("Please select an image first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  showSpinner();

  try {
    const response = await fetch("http://127.0.0.1:5000/process", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();
    if (!response.ok) {
      alert("Error: " + (result.error || "Failed to process image"));
      return;
    }

    document.getElementById("correctedText").value = result.corrected_text || "";
    if (result.document_id) {
      document.getElementById("documentId").value = result.document_id;
    }

  } catch (error) {
    console.error("Error during extraction:", error);
    alert("Failed to extract text.");
  } finally {
    hideSpinner();
  }
});

// ✅ Summarization
document.getElementById("summarizeBtn")?.addEventListener("click", async () => {
  const text = document.getElementById("correctedText")?.value.trim();
  const docId = document.getElementById("documentId")?.value;

  if (!text) {
    alert("No corrected text to summarize.");
    return;
  }

  showSpinner();

  try {
    const response = await fetch("http://127.0.0.1:5000/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, document_id: docId }),
    });

    const result = await response.json();
    if (!response.ok) {
      alert("Error: " + (result.error || "Summarization failed"));
      return;
    }

    const summary = result.summary || "No summary returned";
    const summaryTextElem = document.getElementById("summaryText");
    if (summaryTextElem) {
      summaryTextElem.value = summary;
    } else {
      alert("Summary:\n" + summary);
    }

  } catch (error) {
    console.error("Error during summarization:", error);
    alert("Failed to summarize text.");
  } finally {
    hideSpinner();
  }
});

// ✅ View image in modal
function viewImage(documentId) {
  const modal = document.getElementById("imageModal");
  const modalImg = document.getElementById("modalImage");

  modalImg.src = `http://127.0.0.1:5000/image/${documentId}`;
  modal.style.display = "block";
}

function closeModal() {
  const modal = document.getElementById("imageModal");
  modal.style.display = "none";
}

// ✅ Auto-load recent documents on Recent page
document.addEventListener("DOMContentLoaded", () => {
  if (window.location.pathname.includes("recent.html")) {
    fetchRecentDocuments();
  }
});
