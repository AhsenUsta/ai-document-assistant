const uploadButton = document.getElementById("uploadButton");
const documentInput = document.getElementById("documentInput");
const uploadStatus = document.getElementById("uploadStatus");
const selectedFiles = document.getElementById("selectedFiles");

const questionForm = document.getElementById("questionForm");
const questionInput = document.getElementById("questionInput");
const chatMessages = document.getElementById("chatMessages");
const sendButton = document.getElementById("sendButton");
const clearChatButton = document.getElementById("clearChatButton");

const exampleButtons = document.querySelectorAll(".example-question");

const clearDocumentsButton = document.getElementById(
    "clearDocumentsButton"
);

const documentList = document.getElementById("documentList");

let isIndexing = false;
let isAnswering = false;


/* ---------------------------------------------------------
   INITIAL STATE
--------------------------------------------------------- */

uploadButton.disabled = true;
clearDocumentsButton.disabled = true;


/* ---------------------------------------------------------
   FILE SELECTION
--------------------------------------------------------- */

documentInput.addEventListener("change", () => {
    renderSelectedFiles();

    uploadButton.disabled =
        documentInput.files.length === 0 || isIndexing;
});


function renderSelectedFiles() {
    selectedFiles.innerHTML = "";

    const files = Array.from(documentInput.files);

    if (files.length === 0) {
        const emptyMessage = document.createElement("div");

        emptyMessage.className = "selected-files-empty";
        emptyMessage.textContent = "No file selected.";

        selectedFiles.appendChild(emptyMessage);
        return;
    }

    const header = document.createElement("div");

    header.className = "selected-files-header";
    header.textContent =
        `${files.length} file(s) selected`;

    selectedFiles.appendChild(header);

    for (const file of files) {
        const item = document.createElement("div");
        const icon = document.createElement("span");
        const information = document.createElement("div");
        const fileName = document.createElement("div");
        const fileSize = document.createElement("div");

        item.className = "file-item";
        icon.className = "file-item-icon";
        information.className = "file-item-information";
        fileName.className = "file-item-name";
        fileSize.className = "file-item-size";

        icon.textContent = getFileIcon(file.name);
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);

        fileName.title = file.name;

        information.appendChild(fileName);
        information.appendChild(fileSize);

        item.appendChild(icon);
        item.appendChild(information);

        selectedFiles.appendChild(item);
    }
}


/* ---------------------------------------------------------
   DOCUMENT UPLOAD AND INDEXING
--------------------------------------------------------- */

uploadButton.addEventListener("click", async () => {
    const files = Array.from(documentInput.files);

    if (files.length === 0) {
        setUploadStatus(
            "Please select at least one file.",
            "error"
        );
        return;
    }

    if (isIndexing) {
        return;
    }

    const formData = new FormData();

    for (const file of files) {
        formData.append("files", file);
    }

    setIndexingState(true);

    setUploadStatus(
        "Uploading documents and rebuilding the index. Please wait...",
        ""
    );

    try {
        const response = await fetch("/documents", {
            method: "POST",
            body: formData,
        });

        const result = await readJsonResponse(response);

        if (!response.ok) {
            throw new Error(
                result.detail || "Upload failed."
            );
        }

        const uploadedFiles =
            result.uploaded_files ?? [];

        const indexedFiles =
            result.indexed_files ?? [];

        const chunkCount =
            result.chunk_count ?? 0;

        const duration =
            result.duration ?? 0;

        setUploadStatus(
            `${uploadedFiles.length} file(s) uploaded. ` +
            `${indexedFiles.length} file(s) indexed. ` +
            `${chunkCount} chunk(s) created in ${duration} seconds.`,
            "success"
        );

        showIndexedDocuments(indexedFiles);
		clearDocumentsButton.disabled = indexedFiles.length === 0;
		
        documentInput.value = "";
        selectedFiles.innerHTML = "";

        const emptyMessage =
            document.createElement("div");

        emptyMessage.className =
            "selected-files-empty";

        emptyMessage.textContent =
            "Upload completed. You can select new documents.";

        selectedFiles.appendChild(emptyMessage);

    } catch (error) {
        setUploadStatus(
            error.message || "Upload failed.",
            "error"
        );

        console.error("Upload error:", error);

    } finally {
        setIndexingState(false);

        uploadButton.disabled =
            documentInput.files.length === 0;
    }
});


function setIndexingState(indexing) {
    isIndexing = indexing;

    uploadButton.disabled = indexing;
    documentInput.disabled = indexing;

    questionInput.disabled = indexing;
    sendButton.disabled = indexing;
    clearChatButton.disabled = indexing;

    for (const button of exampleButtons) {
        button.disabled = indexing;
    }

    if (indexing) {
        questionInput.placeholder =
            "Documents are being indexed. Please wait...";

        uploadButton.textContent =
            "Indexing...";

    } else {
        questionInput.placeholder =
            "Ask a question about your documents...";

        uploadButton.textContent =
            "Upload & Index";

        questionInput.focus();
    }
}


/* ---------------------------------------------------------
   QUESTION SUBMISSION
--------------------------------------------------------- */

questionForm.addEventListener("submit", async event => {
    event.preventDefault();

    if (isIndexing) {
        addMessage(
            "assistant",
            "Documents are currently being indexed. Please wait until indexing is complete."
        );

        return;
    }

    if (isAnswering) {
        return;
    }

    const question = questionInput.value.trim();

    if (!question) {
        return;
    }

    removeWelcomeCard();
    addMessage("user", question);

    questionInput.value = "";
    resizeQuestionInput();

    setAnsweringState(true);

    const typingMessage = addTypingIndicator();

    const formData = new FormData();
    formData.append("question", question);

    try {
        const response = await fetch("/ask", {
            method: "POST",
            body: formData,
        });

        const result = await readJsonResponse(response);

        if (!response.ok) {
            throw new Error(
                result.detail ||
                "The question could not be answered."
            );
        }

        typingMessage.remove();

        addMessage(
            "assistant",
            result.answer ||
            "No answer could be generated.",
            result.sources ?? []
        );

    } catch (error) {
        typingMessage.remove();

        addMessage(
            "assistant",
            error.message ||
            "The question could not be answered."
        );

        console.error("Question error:", error);

    } finally {
        setAnsweringState(false);
    }
});


function setAnsweringState(answering) {
    isAnswering = answering;

    sendButton.disabled = answering;
    questionInput.disabled = answering;

    if (answering) {
        sendButton.textContent = "Waiting...";
        questionInput.placeholder =
            "Searching documents and generating an answer...";
    } else {
        sendButton.textContent = "Send";
        questionInput.placeholder =
            "Ask a question about your documents...";
        questionInput.focus();
    }
}


/* ---------------------------------------------------------
   QUESTION INPUT
--------------------------------------------------------- */

questionInput.addEventListener(
    "input",
    resizeQuestionInput
);


questionInput.addEventListener("keydown", event => {
    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {
        event.preventDefault();

        if (!isIndexing && !isAnswering) {
            questionForm.requestSubmit();
        }
    }
});


/* ---------------------------------------------------------
   CLEAR CHAT
--------------------------------------------------------- */

clearChatButton.addEventListener("click", () => {
    if (isIndexing || isAnswering) {
        return;
    }

    chatMessages.innerHTML = "";
    addWelcomeCard();
});


/* ---------------------------------------------------------
   EXAMPLE QUESTIONS
--------------------------------------------------------- */

for (const button of exampleButtons) {
    button.addEventListener("click", () => {
        if (isIndexing || isAnswering) {
            return;
        }

        questionInput.value =
            button.dataset.question || "";

        questionInput.focus();
        resizeQuestionInput();
    });
}


/* ---------------------------------------------------------
   CHAT MESSAGE
--------------------------------------------------------- */

function addMessage(
    role,
    content,
    sources = []
) {
    const row = document.createElement("div");
    const bubble = document.createElement("div");
    const contentElement = document.createElement("div");

    row.className = `message-row ${role}`;
    bubble.className = "message-bubble";
    contentElement.className = "message-content";

    contentElement.textContent = content;

    bubble.appendChild(contentElement);

    if (
        role === "assistant" &&
        Array.isArray(sources) &&
        sources.length > 0
    ) {
        const meta = document.createElement("div");
        const sourceTitle =
            document.createElement("strong");
        const sourceList =
            document.createElement("div");

        meta.className = "message-meta";
        sourceList.className = "message-source-list";

        sourceTitle.textContent = "Sources";

        const uniqueSources =
            [...new Set(sources)];

        sourceList.textContent =
            uniqueSources.join(", ");

        meta.appendChild(sourceTitle);
        meta.appendChild(sourceList);

        bubble.appendChild(meta);
    }

    row.appendChild(bubble);
    chatMessages.appendChild(row);

    scrollChatToBottom();

    return row;
}


/* ---------------------------------------------------------
   TYPING INDICATOR
--------------------------------------------------------- */

function addTypingIndicator() {
    const row = document.createElement("div");
    const indicator = document.createElement("div");

    row.className = "message-row assistant";

    indicator.className =
        "message-bubble typing-indicator";

    indicator.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;

    row.appendChild(indicator);
    chatMessages.appendChild(row);

    scrollChatToBottom();

    return row;
}


/* ---------------------------------------------------------
   UPLOAD STATUS
--------------------------------------------------------- */

function setUploadStatus(message, state) {
    uploadStatus.textContent = message;
    uploadStatus.className = "status-message";

    if (state) {
        uploadStatus.classList.add(state);
    }
}


/* ---------------------------------------------------------
   INDEXED DOCUMENT MESSAGE
--------------------------------------------------------- */

function showIndexedDocuments(indexedFiles) {
    if (
        !Array.isArray(indexedFiles) ||
        indexedFiles.length === 0
    ) {
        return;
    }

    removeWelcomeCard();

    const documentNames = indexedFiles
        .map(fileName => `• ${fileName}`)
        .join("\n");

    addMessage(
        "assistant",
        `Index is ready.\n\nIndexed documents:\n${documentNames}`
    );
}


/* ---------------------------------------------------------
   TEXTAREA SIZE
--------------------------------------------------------- */

function resizeQuestionInput() {
    questionInput.style.height = "auto";

    questionInput.style.height =
        `${Math.min(
            questionInput.scrollHeight,
            170
        )}px`;
}


/* ---------------------------------------------------------
   CHAT SCROLL
--------------------------------------------------------- */

function scrollChatToBottom() {
    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


/* ---------------------------------------------------------
   WELCOME CARD
--------------------------------------------------------- */

function removeWelcomeCard() {
    const welcomeCard =
        chatMessages.querySelector(".welcome-card");

    if (welcomeCard) {
        welcomeCard.remove();
    }
}


function addWelcomeCard() {
    chatMessages.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-icon">✦</div>

            <h3>
                Ask a question about your documents
            </h3>

            <p>
                Upload one or more documents, wait for
                indexing to finish, and ask questions
                in Turkish or English.
            </p>
        </div>
    `;

    const dynamicButtons =
        chatMessages.querySelectorAll(
            ".dynamic-example"
        );

    for (const button of dynamicButtons) {
        button.addEventListener("click", () => {
            if (isIndexing || isAnswering) {
                return;
            }

            questionInput.value =
                button.dataset.question || "";

            questionInput.focus();
            resizeQuestionInput();
        });
    }
}


/* ---------------------------------------------------------
   FILE HELPERS
--------------------------------------------------------- */

function formatFileSize(bytes) {
    if (!Number.isFinite(bytes) || bytes < 0) {
        return "Unknown size";
    }

    if (bytes < 1024) {
        return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
        return `${(
            bytes / 1024
        ).toFixed(1)} KB`;
    }

    return `${(
        bytes / (1024 * 1024)
    ).toFixed(1)} MB`;
}


function getFileIcon(fileName) {
    const extension = fileName
        .split(".")
        .pop()
        .toLowerCase();

    if (extension === "pdf") {
        return "PDF";
    }

    if (
        extension === "png" ||
        extension === "jpg" ||
        extension === "jpeg"
    ) {
        return "IMG";
    }

    return "FILE";
}


/* ---------------------------------------------------------
   RESPONSE HELPER
--------------------------------------------------------- */

async function readJsonResponse(response) {
    const contentType =
        response.headers.get("content-type") || "";

    if (
        contentType.includes(
            "application/json"
        )
    ) {
        return await response.json();
    }

    const responseText = await response.text();

    return {
        detail:
            responseText ||
            `Server returned HTTP ${response.status}.`,
    };
}

function setApplicationBusy(isBusy) {
    if (clearDocumentsButton) {
        clearDocumentsButton.disabled = isBusy;
    }

    if (questionInput) {
        questionInput.disabled = isBusy;
    }

    if (sendButton) {
        sendButton.disabled = isBusy;
    }

    if (documentInput) {
        documentInput.disabled = isBusy;
    }

    if (uploadButton) {
        uploadButton.disabled = isBusy;
    }
}

/* ---------------------------------------------------------
   CLEAR DOCUMENTS
--------------------------------------------------------- */

function setApplicationBusy(isBusy) {
    clearDocumentsButton.disabled = isBusy;
    documentInput.disabled = isBusy;
    questionInput.disabled = isBusy;
    sendButton.disabled = isBusy;
    clearChatButton.disabled = isBusy;

    if (isBusy) {
        clearDocumentsButton.textContent = "Clearing...";
    } else {
        clearDocumentsButton.textContent = "Clear Documents";

        uploadButton.disabled =
            documentInput.files.length === 0;
    }

    for (const button of exampleButtons) {
        button.disabled = isBusy;
    }
}


async function clearDocuments() {
    if (isIndexing || isAnswering) {
        return;
    }

    const confirmed = window.confirm(
        "All uploaded documents and generated indexes will be deleted. Continue?"
    );

    if (!confirmed) {
        return;
    }

    setApplicationBusy(true);

    setUploadStatus(
        "Clearing documents and indexes...",
        ""
    );

    try {
        const response = await fetch("/documents/clear", {
            method: "DELETE",
            headers: {
                Accept: "application/json",
            },
        });

        const result = await readJsonResponse(response);

        if (!response.ok) {
            throw new Error(
                result.detail ||
                "Documents could not be cleared."
            );
        }

        documentInput.value = "";
        selectedFiles.innerHTML = "";

        const emptyMessage =
            document.createElement("div");

        emptyMessage.className =
            "selected-files-empty";

        emptyMessage.textContent =
            "No file selected.";

        selectedFiles.appendChild(emptyMessage);

        setUploadStatus(
            `${result.deleted_documents ?? 0} document(s) cleared successfully.`,
            "success"
        );
		clearDocumentsButton.disabled = true;
		
        chatMessages.innerHTML = "";
        addWelcomeCard();

    } catch (error) {
        console.error(
            "Clear documents error:",
            error
        );

        setUploadStatus(
            error.message ||
            "An unexpected error occurred.",
            "error"
        );

    } finally {
        setApplicationBusy(false);
    }
}


if (clearDocumentsButton) {
    clearDocumentsButton.addEventListener(
        "click",
        clearDocuments
    );
}