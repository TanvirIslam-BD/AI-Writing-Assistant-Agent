// Main JavaScript for AI Writing Assistant

$(document).ready(function() {
    // Initialize the application
    initializeApp();
});

function initializeApp() {
    // Bind event handlers
    bindEventHandlers();

    // Initialize UI components
    initializeUI();
}

function bindEventHandlers() {
    // Form submission for improving text
    $('#writing-form').on('submit', function(e) {
        e.preventDefault();
        improveText();
    });

    // Analyze text button
    $('#analyze-btn').on('click', function() {
        analyzeText();
    });

    // Clear button
    $('#clear-btn').on('click', function() {
        clearForm();
    });

    // Auto-resize textarea
    $('#input-text').on('input', function() {
        autoResizeTextarea(this);
    });
}

function initializeUI() {
    // Auto-resize textarea on load
    autoResizeTextarea(document.getElementById('input-text'));

    // Add fade-in animation to cards
    $('.card').addClass('fade-in');
}

function improveText() {
    const text = $('#input-text').val().trim();

    if (!text) {
        showAlert('Please enter some text to improve.', 'warning');
        return;
    }

    // Show loading state
    showLoading();
    hideResults();

    // Get selected tools
    const selectedTools = [];
    $('input[name="tools"]:checked').each(function() {
        selectedTools.push($(this).val());
    });

    // Get selected tone
    const tone = $('#tone-select').val();

    // Prepare form data
    const formData = new FormData();
    formData.append('text', text);
    formData.append('tone', tone);

    // Add selected tools
    selectedTools.forEach(tool => {
        formData.append('tools', tool);
    });

    // Add CSRF token
    formData.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val());

    // Make AJAX request
    $.ajax({
        url: '/improve/',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            hideLoading();
            displayResults(response);
            showAlert('Text improved successfully!', 'success');
        },
        error: function(xhr) {
            hideLoading();
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred';
            showAlert('Error: ' + error, 'danger');
        }
    });
}

function analyzeText() {
    const text = $('#input-text').val().trim();

    if (!text) {
        showAlert('Please enter some text to analyze.', 'warning');
        return;
    }

    // Show loading state
    showLoading();
    hideResults();

    // Prepare form data
    const formData = new FormData();
    formData.append('text', text);
    formData.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val());

    // Make AJAX request
    $.ajax({
        url: '/analyze/',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            hideLoading();
            displayAnalysis(response);
            showAlert('Text analyzed successfully!', 'info');
        },
        error: function(xhr) {
            hideLoading();
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred';
            showAlert('Error: ' + error, 'danger');
        }
    });
}

function displayResults(response) {
    const resultsSection = $('#results-section');
    const resultsContent = $('#results-content');

    let html = `
        <div class="row">
            <div class="col-md-6">
                <h6><strong>Original Text:</strong></h6>
                <div class="p-3 bg-light border rounded">
                    ${escapeHtml(response.original)}
                </div>
            </div>
            <div class="col-md-6">
                <h6><strong>Improved Text:</strong></h6>
                <div class="p-3 success-highlight border rounded">
                    ${escapeHtml(response.improved)}
                </div>
            </div>
        </div>
        <hr>
        <div class="mt-3">
            <h6><strong>Improvements Made:</strong></h6>
    `;

    if (response.improvements && response.improvements.length > 0) {
        html += '<div class="accordion" id="improvementsAccordion">';

        response.improvements.forEach((improvement, index) => {
            const toolName = formatToolName(improvement.tool);
            const toolIcon = getToolIcon(improvement.tool);

            html += `
                <div class="accordion-item">
                    <h2 class="accordion-header" id="heading${index}">
                        <button class="accordion-button ${index > 0 ? 'collapsed' : ''}" type="button"
                                data-bs-toggle="collapse" data-bs-target="#collapse${index}">
                            ${toolIcon} ${toolName}
                        </button>
                    </h2>
                    <div id="collapse${index}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}"
                         data-bs-parent="#improvementsAccordion">
                        <div class="accordion-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <strong>Before:</strong>
                                    <div class="p-2 bg-light border rounded mt-1">
                                        ${escapeHtml(improvement.before)}
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <strong>After:</strong>
                                    <div class="p-2 success-highlight border rounded mt-1">
                                        ${escapeHtml(improvement.after)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
    } else {
        html += '<p class="text-muted">No improvements were made to the text.</p>';
    }

    html += `
        </div>
        <div class="mt-3">
            <div class="row">
                <div class="col-md-6">
                    <small class="text-muted">
                        <i class="fas fa-tools me-1"></i>
                        Tools used: ${response.tools_used.map(formatToolName).join(', ') || 'None'}
                    </small>
                </div>
                <div class="col-md-6 text-end">
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>
                        Processing time: ${response.processing_time.toFixed(2)}s
                    </small>
                </div>
            </div>
        </div>
    `;

    resultsContent.html(html);
    resultsSection.removeClass('d-none').addClass('slide-in');
}

function displayAnalysis(response) {
    const analysisSection = $('#analysis-section');
    const analysisContent = $('#analysis-content');

    let html = `
        <div class="mb-3">
            <h6><strong>Text Analysis Results:</strong></h6>
            <div class="p-3 bg-light border rounded">
                ${escapeHtml(response.text)}
            </div>
        </div>
    `;

    html += `
        <div class="row">
            <div class="col-md-6">
                <h6><strong>Recommended Tools:</strong></h6>
                <div class="list-group">
    `;

    response.recommended_tools.forEach((tool, index) => {
        const toolName = formatToolName(tool);
        const toolIcon = getToolIcon(tool);
        const priority = index === 0 ? 'High' : index === 1 ? 'Medium' : 'Low';
        const priorityClass = index === 0 ? 'danger' : index === 1 ? 'warning' : 'secondary';

        html += `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    ${toolIcon} ${toolName}
                </div>
                <span class="badge bg-${priorityClass}">${priority} Priority</span>
            </div>
        `;
    });

    html += `
                </div>
            </div>
            <div class="col-md-6">
                <h6><strong>Analysis Details:</strong></h6>
                <div class="card">
                    <div class="card-body">
    `;

    for (const [toolName, analysis] of Object.entries(response.analysis)) {
        const formattedName = formatToolName(toolName);
        const toolIcon = getToolIcon(toolName);

        html += `
            <div class="mb-2">
                <strong>${toolIcon} ${formattedName}:</strong><br>
                <small class="text-muted">Analysis completed</small>
            </div>
        `;
    }

    html += `
                    </div>
                </div>
            </div>
        </div>
    `;

    analysisContent.html(html);
    analysisSection.removeClass('d-none').addClass('slide-in');
}

function clearForm() {
    $('#input-text').val('');
    $('input[name="tools"]').prop('checked', false);
    $('#tone-select').val('');
    hideResults();
    hideLoading();
    autoResizeTextarea(document.getElementById('input-text'));
}

function showLoading() {
    $('#loading').removeClass('d-none');
    $('#improve-btn').prop('disabled', true);
    $('#analyze-btn').prop('disabled', true);
}

function hideLoading() {
    $('#loading').addClass('d-none');
    $('#improve-btn').prop('disabled', false);
    $('#analyze-btn').prop('disabled', false);
}

function hideResults() {
    $('#results-section').addClass('d-none');
    $('#analysis-section').addClass('d-none');
}

function showAlert(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    // Remove existing alerts
    $('.alert').remove();

    // Add new alert at the top of the container
    $('main.container').prepend(alertHtml);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        $('.alert').alert('close');
    }, 5000);
}

function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

function formatToolName(toolName) {
    return toolName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getToolIcon(toolName) {
    const icons = {
        'grammar_corrector': '<i class="fas fa-spell-check text-success"></i>',
        'sentence_rewriter': '<i class="fas fa-pen-alt text-info"></i>',
        'vocabulary_enhancer': '<i class="fas fa-book text-warning"></i>',
        'tone_adjuster': '<i class="fas fa-adjust text-secondary"></i>'
    };
    return icons[toolName] || '<i class="fas fa-cog text-muted"></i>';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Additional utility functions for enhanced UX
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Text copied to clipboard!', 'success');
    }).catch(() => {
        showAlert('Failed to copy text', 'danger');
    });
}

// Initialize tooltips and popovers if needed
$(function () {
    $('[data-bs-toggle="tooltip"]').tooltip();
    $('[data-bs-toggle="popover"]').popover();
});