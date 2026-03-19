frappe.require('/assets/ichat/css/ichat.css');

frappe.pages['ichat'].on_page_load = function (wrapper) {

    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'PDF AI Assistant',
        single_column: true
    });

    $(wrapper).find('.layout-main-section')
        .html(frappe.render_template('ichat', {}));

    const API_BASE = "http://127.0.0.1:8003";

    const chatOutput = $(wrapper).find('#chat-output');
    const chatInput = $(wrapper).find('#chat-input');
    const uploadStatus = $(wrapper).find('#upload-status');
    const selectedFilesDiv = $(wrapper).find('#selected-files');
    const uploadedFilesDiv = $(wrapper).find('#uploaded-files');
    const uploadedContainer = $(wrapper).find('#uploaded-container');

    // ===============================
    // Chat Helpers
    // ===============================
    function addMessage(text, type) {
        chatOutput.append(`<div class="chat-msg ${type}">${text}</div>`);
        chatOutput.scrollTop(chatOutput[0].scrollHeight);
    }

    function formatAnswer(text) {
        return text
            .replace(/## (.*)/g, "<h4>$1</h4>")
            .replace(/\\(.?)\\*/g, "<strong>$1</strong>")
            .replace(/- (.*)/g, "<li>$1</li>")
            .replace(/\n/g, "<br>");
    }

    function showTyping() {
        chatOutput.append(`<div class="chat-msg ai typing">Typing...</div>`);
    }

    function removeTyping() {
        chatOutput.find('.typing').remove();
    }

    // ===============================
    // Open File Picker
    // ===============================
    $(wrapper).on('click', '#drop-zone', function () {
        const fileInput = $(wrapper).find('#pdf-files');
        if (fileInput.length) {
            fileInput[0].click();
        }
    });

    // ===============================
    // Show Selected Files Immediately
    // ===============================
    $(wrapper).on('change', '#pdf-files', function () {

        const files = this.files;
        selectedFilesDiv.empty();

        if (!files.length) return;

        selectedFilesDiv.append("<strong>Selected Files:</strong>");

        Array.from(files).forEach(file => {
            selectedFilesDiv.append(`
                <div class="file-item pending">
                    ${file.name}
                </div>
            `);
        });
    });

    // ===============================
    // Upload Files
    // ===============================
    $(wrapper).on('click', '#btn-upload', async function () {

        const files = $(wrapper).find('#pdf-files')[0]?.files;

        if (!files || !files.length) {
            frappe.msgprint("Select PDFs first.");
            return;
        }

        let formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }

        uploadStatus.text("Uploading...");

        try {
            let response = await fetch(`${API_BASE}/upload-pdfs`, {
                method: 'POST',
                body: formData
            });

            let result = await response.json();

            if (result.error) {
                uploadStatus.text(result.error);
                return;
            }

            uploadStatus.text("Indexed successfully.");

            // Show Uploaded Section
            uploadedContainer.show();

            // Move files to Uploaded list
            Array.from(files).forEach(file => {
                uploadedFilesDiv.append(`
                    <div class="file-item uploaded">
                        ${file.name}
                    </div>
                `);
            });

            // Clear selected files area
            selectedFilesDiv.empty();

            // Reset file input
            $(wrapper).find('#pdf-files').val('');

            addMessage("Documents indexed successfully. You can now ask questions.", "ai");

        } catch (err) {
            uploadStatus.text("Upload failed.");
        }
    });

    // ===============================
    // Send Query
    // ===============================
    async function sendQuery() {

        const question = chatInput.val()?.trim();
        if (!question) return;

        addMessage(question, "user");
        chatInput.val('');
        showTyping();

        let formData = new FormData();
        formData.append('question', question);

        try {
            let response = await fetch(`${API_BASE}/ask`, {
                method: 'POST',
                body: formData
            });

            let result = await response.json();
            removeTyping();

            if (result.error) {
                addMessage(result.error, "ai");
                return;
            }

            addMessage(formatAnswer(result.answer), "ai");

        } catch (err) {
            removeTyping();
            addMessage("Error communicating with server.", "ai");
        }
    }

    $(wrapper).on('click', '#btn-query', sendQuery);

    $(wrapper).on('keypress', '#chat-input', function (e) {
        if (e.which === 13) {
            e.preventDefault();
            sendQuery();
        }
    });
};