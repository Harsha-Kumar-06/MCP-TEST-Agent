// DOM Elements - Get after DOM loads
let processBtn, chatMessages, toggleUpload, toggleUrl, uploadSection, urlSection;
let dropZone, fileInput, fileInfo, fileName, clearFile, extractedPreview, previewText;
let urlInput, urlStatus, urlStatusIcon, urlStatusText, filesList;

// State
let uploadedFiles = []; // Changed to array for multiple files
let uploadedFilesText = []; // Store text for each file
let inputMode = 'url';

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Get DOM elements
    processBtn = document.getElementById('processBtn');
    chatMessages = document.getElementById('chatMessages');
    toggleUpload = document.getElementById('toggleUpload');
    toggleUrl = document.getElementById('toggleUrl');
    uploadSection = document.getElementById('uploadSection');
    urlSection = document.getElementById('urlSection');
    dropZone = document.getElementById('dropZone');
    fileInput = document.getElementById('fileInput');
    fileInfo = document.getElementById('fileInfo');
    fileName = document.getElementById('fileName');
    filesList = document.getElementById('filesList');
    clearFile = document.getElementById('clearFile');
    extractedPreview = document.getElementById('extractedPreview');
    previewText = document.getElementById('previewText');
    urlInput = document.getElementById('urlInput');
    urlStatus = document.getElementById('urlStatus');
    urlStatusIcon = document.getElementById('urlStatusIcon');
    urlStatusText = document.getElementById('urlStatusText');
    
    // Check if elements exist
    console.log('processBtn:', processBtn);
    console.log('toggleUrl:', toggleUrl);
    console.log('toggleUpload:', toggleUpload);
    
    // Add event listeners with null checks
    if (processBtn) {
        processBtn.addEventListener('click', handleProcess);
        console.log('Process button listener added');
    } else {
        console.error('processBtn not found!');
    }
    
    if (toggleUpload) {
        toggleUpload.addEventListener('click', function() {
            console.log('Upload toggle clicked');
            switchMode('upload');
        });
    } else {
        console.error('toggleUpload not found!');
    }
    
    if (toggleUrl) {
        toggleUrl.addEventListener('click', function() {
            console.log('URL toggle clicked');
            switchMode('url');
        });
    } else {
        console.error('toggleUrl not found!');
    }
    
    if (dropZone && fileInput) {
        console.log('Setting up dropZone click handler');
        
        dropZone.addEventListener('click', function(e) {
            console.log('Drop zone clicked!');
            fileInput.click();
        });
        
        dropZone.addEventListener('dragover', handleDragOver);
        dropZone.addEventListener('dragleave', handleDragLeave);
        dropZone.addEventListener('drop', handleDrop);
    } else {
        console.error('dropZone or fileInput not found!');
        console.log('dropZone:', dropZone);
        console.log('fileInput:', fileInput);
    }
    
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    if (clearFile) {
        clearFile.addEventListener('click', clearUploadedFile);
    }
    
    if (urlInput) {
        urlInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleProcess();
            }
        });
    } else {
        console.error('urlInput not found!');
    }
    
    console.log('Initialization complete!');
});

// Switch between upload and url mode
function switchMode(mode) {
    console.log('Switching to mode:', mode);
    inputMode = mode;
    
    if (toggleUpload) toggleUpload.classList.remove('active');
    if (toggleUrl) toggleUrl.classList.remove('active');
    if (uploadSection) uploadSection.classList.add('hidden');
    if (urlSection) urlSection.classList.add('hidden');
    
    if (mode === 'upload') {
        if (toggleUpload) toggleUpload.classList.add('active');
        if (uploadSection) uploadSection.classList.remove('hidden');
    } else if (mode === 'url') {
        if (toggleUrl) toggleUrl.classList.add('active');
        if (urlSection) urlSection.classList.remove('hidden');
    }
}

// Fetch URL content
async function fetchUrlContent(url) {
    showUrlStatus('loading', '⏳', 'Fetching content from URL...');
    
    try {
        const response = await fetch('/api/fetch-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showUrlStatus('success', '✅', `Fetched ${result.text.length} characters`);
            return result.text;
        } else {
            showUrlStatus('error', '❌', result.error || 'Failed to fetch URL');
            return null;
        }
    } catch (error) {
        showUrlStatus('error', '❌', 'Network error: ' + error.message);
        return null;
    }
}

function showUrlStatus(type, icon, message) {
    if (urlStatus) {
        urlStatus.classList.remove('hidden', 'loading', 'success', 'error');
        urlStatus.classList.add(type);
    }
    if (urlStatusIcon) urlStatusIcon.textContent = icon;
    if (urlStatusText) urlStatusText.textContent = message;
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    if (dropZone) dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    if (dropZone) dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    if (dropZone) dropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        // Process multiple files
        for (let file of files) {
            processFile(file);
        }
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        // Process multiple files
        for (let file of files) {
            processFile(file);
        }
    }
}

// Process uploaded file - accepts ANY file type
async function processFile(file) {
    console.log('Processing file:', file.name);
    
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    const textExtensions = ['.txt', '.csv', '.md', '.json', '.xml', '.html', '.htm', '.css', '.js', '.ts', '.py', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.rs', '.sql', '.sh', '.bat', '.ps1', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.log', '.rst'];
    
    addChatMessage('system', '📂', `Processing file: ${file.name}...`, 'File Upload');
    
    try {
        let fileText = '';
        
        // For text files, read directly
        if (textExtensions.includes(fileExt)) {
            fileText = await readTextFile(file);
        } else {
            // For other files, send to backend
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                fileText = result.text;
            } else {
                throw new Error(result.error || 'Failed to process file');
            }
        }
        
        // Add to uploaded files
        uploadedFiles.push(file);
        uploadedFilesText.push(fileText);
        
        // Update UI
        updateFilesList();
        if (fileInfo) fileInfo.classList.remove('hidden');
        if (dropZone) dropZone.style.display = 'none';
        
        addChatMessage('system', '✅', `File processed! ${file.name} - ${fileText.length} characters.`, 'File Upload');
    } catch (error) {
        addChatMessage('error', '❌', `Failed to process ${file.name}: ${error.message}`, 'File Upload');
    }
}

function updateFilesList() {
    if (!filesList) return;
    
    filesList.innerHTML = '';
    uploadedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span class="file-icon">📄</span>
            <span class="file-name">${file.name}</span>
            <span class="file-size">(${formatFileSize(file.size)})</span>
            <button type="button" class="remove-file-btn" data-index="${index}">✕</button>
        `;
        filesList.appendChild(fileItem);
        
        // Add event listener to remove button
        const removeBtn = fileItem.querySelector('.remove-file-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => removeFile(index));
        }
    });
    
    if (extractedPreview) {
        extractedPreview.classList.remove('hidden');
        if (previewText) previewText.textContent = `${uploadedFiles.length} file(s) ready for analysis`;
    }
}

function removeFile(index) {
    uploadedFiles.splice(index, 1);
    uploadedFilesText.splice(index, 1);
    
    if (uploadedFiles.length === 0) {
        clearUploadedFile();
    } else {
        updateFilesList();
    }
}

// For other files, send to backend
async function uploadFileToBackend(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            return result.text;
        } else {
            throw new Error(result.error || 'Failed to process file');
        }
    } catch (error) {
        throw error;
    }
}

function readTextFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

function showExtractedPreview(text) {
    const preview = text.length > 500 ? text.substring(0, 500) + '...' : text;
    if (previewText) previewText.textContent = preview;
    if (extractedPreview) extractedPreview.classList.remove('hidden');
}

function clearUploadedFile() {
    uploadedFiles = [];
    uploadedFilesText = [];
    if (fileInput) fileInput.value = '';
    if (filesList) filesList.innerHTML = '';
    if (fileInfo) fileInfo.classList.add('hidden');
    if (extractedPreview) extractedPreview.classList.add('hidden');
    if (dropZone) dropZone.style.display = 'block';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Main process function - Fully Automated Analysis
async function handleProcess() {
    console.log('handleProcess called, mode:', inputMode);
    
    let documentContent = '';
    let sourceUrl = '';
    
    if (inputMode === 'upload') {
        if (uploadedFiles.length === 0) {
            addChatMessage('error', '❌', 'Please upload at least one file first!', 'Validation');
            return;
        }
        
        // If multiple files, combine them with separators
        if (uploadedFiles.length > 1) {
            documentContent = uploadedFilesText.map((text, index) => {
                return `\n\n━━━━━━━ DOCUMENT ${index + 1}: ${uploadedFiles[index].name} ━━━━━━━\n\n${text}`;
            }).join('\n\n');
            
            addChatMessage('system', '📚', `Processing ${uploadedFiles.length} documents...`, 'Analysis');
        } else {
            documentContent = uploadedFilesText[0];
        }
    } else if (inputMode === 'url') {
        const url = urlInput ? urlInput.value.trim() : '';
        sourceUrl = url;
        
        if (!url) {
            addChatMessage('error', '❌', 'Please enter a URL to analyze!', 'Validation');
            if (urlInput) urlInput.focus();
            return;
        }
        
        // Validate URL
        try {
            new URL(url);
        } catch {
            addChatMessage('error', '❌', 'Invalid URL format.', 'Validation');
            if (urlInput) urlInput.focus();
            return;
        }
        
        // Fetch URL content
        addChatMessage('system', '🔗', `Fetching: ${url}...`, 'URL Fetch');
        
        documentContent = await fetchUrlContent(url);
        
        if (!documentContent) {
            addChatMessage('error', '❌', 'Failed to fetch URL content.', 'Error');
            return;
        }
        
        addChatMessage('system', '✅', `Fetched ${documentContent.length} characters!`, 'URL Fetch');
    }
    
    // Disable button
    if (processBtn) {
        processBtn.disabled = true;
        processBtn.textContent = '⏳ Analyzing...';
    }
    
    resetPipelineViz();
    
    const sourceIndicator = inputMode === 'url' ? `🔗 ${sourceUrl}` : '📁 Uploaded File';
    addChatMessage('user', '👤', `<strong>Analyzing:</strong> ${sourceIndicator}<br><em>${documentContent.length} chars</em><br><span style="color: #00d9ff;">🌐 Web Search: Enabled</span>`, 'You');
    addChatMessage('system', '🚀', 'Starting analysis: Summary → Literature Review → Competitive Analysis', 'System');
    
    try {
        const response = await fetch('/api/research/enhanced', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                question: "[AUTO-COMPREHENSIVE-ANALYSIS]",
                document: documentContent,
                enable_web_search: true,
                source_url: sourceUrl
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (result.web_search_used) {
                addChatMessage('system', '🌐', 'Web search integrated!', 'Web Search');
            }
            displayPipelineResults(result);
        } else {
            addChatMessage('error', '❌', `Analysis failed: ${result.error}`, 'Error');
        }
        
    } catch (error) {
        addChatMessage('error', '❌', `Connection error: ${error.message}`, 'Error');
    } finally {
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.textContent = '🚀 Analyze Now';
        }
    }
}

// Display Pipeline Results
function displayPipelineResults(result) {
    const steps = result.steps || [];
    
    steps.forEach((step, index) => {
        setTimeout(() => {
            updatePipelineViz(index);
            
            const icon = step.status === 'success' ? '🤖' : '❌';
            const type = step.status === 'success' ? 'agent' : 'error';
            
            let message = `<strong>${step.agent}</strong><br>`;
            message += `Status: <span style="color: ${step.status === 'success' ? '#00ff88' : '#ff6b6b'}">${step.status}</span><br>`;
            message += `Time: ${step.processing_time?.toFixed(2)}s`;
            
            if (step.output_preview) {
                message += `<br><em>${escapeHtml(step.output_preview.substring(0, 200))}...</em>`;
            }
            
            addChatMessage(type, icon, message, step.agent);
            
        }, index * 800);
    });
    
    setTimeout(() => {
        displayFinalResult(result.final_output);
        
        for (let i = 0; i <= 4; i++) {
            const step = document.getElementById(`step${i}`);
            if (step) {
                step.classList.remove('active');
                step.classList.add('completed');
            }
        }
        
    }, steps.length * 800 + 500);
}

// Display Final Result
function displayFinalResult(finalOutput) {
    if (!finalOutput) {
        addChatMessage('error', '❌', 'No output received', 'Error');
        return;
    }
    
    if (finalOutput.status === 'no_data') {
        addChatMessage('error', '📭', `<h3>⚠️ ${finalOutput.answer}</h3><p>${finalOutput.explanation}</p>`, 'Result');
        return;
    }
    
    let resultMsg = `<strong>✅ Analysis Complete!</strong><br><br>`;
    if (finalOutput.answer) {
        // Parse the answer into sections for the three categories
        const sections = parseAnalysisCategories(finalOutput.answer);
        
        resultMsg += `<div class="research-answer">`;
        
        // Display categorized results
        if (sections.summary) {
            resultMsg += `
                <div class="analysis-category summary-category">
                    <div class="category-header">
                        <span class="category-icon">📝</span>
                        <span class="category-title">Summary Analysis</span>
                    </div>
                    <div class="category-content">${formatSummary(sections.summary)}</div>
                </div>
            `;
        }
        
        if (sections.literature) {
            resultMsg += `
                <div class="analysis-category literature-category">
                    <div class="category-header">
                        <span class="category-icon">📚</span>
                        <span class="category-title">Literature Review</span>
                    </div>
                    <div class="category-content">${formatSummary(sections.literature)}</div>
                </div>
            `;
        }
        
        if (sections.competitive) {
            resultMsg += `
                <div class="analysis-category competitive-category">
                    <div class="category-header">
                        <span class="category-icon">🏆</span>
                        <span class="category-title">Competitive Analysis</span>
                    </div>
                    <div class="category-content">${formatSummary(sections.competitive)}</div>
                </div>
            `;
        }
        
        // If no specific categories found, show full answer
        if (!sections.summary && !sections.literature && !sections.competitive) {
            resultMsg += formatSummary(finalOutput.answer);
        }
        
        resultMsg += `</div>`;
        
        // Store the full result globally for export functions
        window.lastAnalysisResult = finalOutput.answer;
        
        // Add action buttons for viewing/downloading
        resultMsg += `
            <div class="result-actions">
                <button id="viewInNewTabBtn" class="action-btn view-btn">
                    <span class="btn-icon">📄</span>
                    <span>View in New Tab</span>
                </button>
                <button id="downloadHTMLBtn" class="action-btn download-btn">
                    <span class="btn-icon">⬇️</span>
                    <span>Download HTML</span>
                </button>
                <button id="downloadMarkdownBtn" class="action-btn download-btn">
                    <span class="btn-icon">📝</span>
                    <span>Download Markdown</span>
                </button>
            </div>
        `;
    }
    
    addChatMessage('success', '🎉', resultMsg, 'Result');
    
    // Add event listeners after the message is added to DOM
    setTimeout(() => {
        const viewBtn = document.getElementById('viewInNewTabBtn');
        const htmlBtn = document.getElementById('downloadHTMLBtn');
        const mdBtn = document.getElementById('downloadMarkdownBtn');
        
        if (viewBtn) viewBtn.addEventListener('click', viewInNewTab);
        if (htmlBtn) htmlBtn.addEventListener('click', downloadAsHTML);
        if (mdBtn) mdBtn.addEventListener('click', downloadAsMarkdown);
    }, 100);
}

function formatSummary(text) {
    // Convert markdown tables to HTML tables
    text = convertMarkdownTables(text);
    
    // Convert other markdown formatting
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

function convertMarkdownTables(text) {
    // Match markdown tables (lines with |)
    const lines = text.split('\n');
    let result = [];
    let tableLines = [];
    let inTable = false;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Check if line is part of a table (contains | and has content)
        if (line.includes('|') && line.length > 1) {
            // Skip separator lines (|---|---|)
            if (/^\|?[\s\-:|]+\|?$/.test(line)) {
                if (!inTable && tableLines.length > 0) {
                    inTable = true;
                }
                continue;
            }
            tableLines.push(line);
            inTable = true;
        } else {
            // End of table, convert accumulated lines
            if (tableLines.length > 0) {
                result.push(buildHtmlTable(tableLines));
                tableLines = [];
                inTable = false;
            }
            result.push(line);
        }
    }
    
    // Handle table at end of text
    if (tableLines.length > 0) {
        result.push(buildHtmlTable(tableLines));
    }
    
    return result.join('\n');
}

function buildHtmlTable(tableLines) {
    if (tableLines.length === 0) return '';
    
    let html = '<div class="table-wrapper"><table class="comparison-table">';
    
    tableLines.forEach((line, index) => {
        // Remove leading/trailing pipes and split by |
        const cells = line.replace(/^\||\|$/g, '').split('|').map(cell => cell.trim());
        
        if (index === 0) {
            // Header row
            html += '<thead><tr>';
            cells.forEach(cell => {
                html += `<th>${cell.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</th>`;
            });
            html += '</tr></thead><tbody>';
        } else {
            // Data rows
            html += '<tr>';
            cells.forEach((cell, cellIndex) => {
                // Add special styling for score cells
                let cellContent = cell.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                
                // Check for ratings/scores (numbers, percentages, stars)
                if (/^\d+(\.\d+)?\/\d+$/.test(cell) || /^\d+%$/.test(cell) || /^[⭐★☆]+$/.test(cell)) {
                    html += `<td class="score-cell">${cellContent}</td>`;
                } else if (cellIndex === 0) {
                    html += `<td class="feature-cell">${cellContent}</td>`;
                } else {
                    html += `<td>${cellContent}</td>`;
                }
            });
            html += '</tr>';
        }
    });
    
    html += '</tbody></table></div>';
    return html;
}

// Add Chat Message
function addChatMessage(type, icon, content, sender) {
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    
    const time = new Date().toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <div class="message-icon">${icon}</div>
        <div class="message-content">
            <p>${content}</p>
            <span class="message-time">${sender} • ${time}</span>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Pipeline Visualization
function resetPipelineViz() {
    for (let i = 0; i <= 4; i++) {
        const step = document.getElementById(`step${i}`);
        if (step) {
            step.classList.remove('active', 'completed');
        }
    }
}

function updatePipelineViz(stepNum) {
    for (let i = 0; i < stepNum; i++) {
        const step = document.getElementById(`step${i}`);
        if (step) {
            step.classList.remove('active');
            step.classList.add('completed');
        }
    }
    const currentStep = document.getElementById(`step${stepNum}`);
    if (currentStep) {
        currentStep.classList.add('active');
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Parse analysis into three categories
function parseAnalysisCategories(text) {
    const sections = {
        summary: '',
        literature: '',
        competitive: ''
    };
    
    // Try to identify sections by keywords and patterns
    const lines = text.split('\n');
    let currentSection = null;
    let currentContent = [];
    
    for (const line of lines) {
        const lowerLine = line.toLowerCase();
        
        // Detect section headers
        if (lowerLine.includes('summary') || lowerLine.includes('key finding') || lowerLine.includes('overview')) {
            if (currentSection && currentContent.length > 0) {
                sections[currentSection] = currentContent.join('\n');
            }
            currentSection = 'summary';
            currentContent = [line];
        } else if (lowerLine.includes('literature') || lowerLine.includes('review') || lowerLine.includes('thematic') || lowerLine.includes('research gap')) {
            if (currentSection && currentContent.length > 0) {
                sections[currentSection] = currentContent.join('\n');
            }
            currentSection = 'literature';
            currentContent = [line];
        } else if (lowerLine.includes('competitive') || lowerLine.includes('comparison') || lowerLine.includes('scoring') || lowerLine.includes('winner')) {
            if (currentSection && currentContent.length > 0) {
                sections[currentSection] = currentContent.join('\n');
            }
            currentSection = 'competitive';
            currentContent = [line];
        } else if (currentSection) {
            currentContent.push(line);
        } else {
            // Before any section detected, add to summary
            if (!sections.summary) sections.summary = '';
            sections.summary += line + '\n';
        }
    }
    
    // Save remaining content
    if (currentSection && currentContent.length > 0) {
        sections[currentSection] = currentContent.join('\n');
    }
    
    return sections;
}

// View analysis in new tab
function viewInNewTab() {
    if (!window.lastAnalysisResult) {
        alert('No analysis result available');
        return;
    }
    
    const htmlContent = generateHTMLDocument(window.lastAnalysisResult);
    const newWindow = window.open();
    newWindow.document.write(htmlContent);
    newWindow.document.close();
}

// Download as HTML
function downloadAsHTML() {
    if (!window.lastAnalysisResult) {
        alert('No analysis result available');
        return;
    }
    
    const htmlContent = generateHTMLDocument(window.lastAnalysisResult);
    downloadFile(htmlContent, 'analysis-report.html', 'text/html');
}

// Download as Markdown
function downloadAsMarkdown() {
    if (!window.lastAnalysisResult) {
        alert('No analysis result available');
        return;
    }
    
    downloadFile(window.lastAnalysisResult, 'analysis-report.md', 'text/markdown');
}

// Generate full HTML document for export
function generateHTMLDocument(content) {
    const sections = parseAnalysisCategories(content);
    const timestamp = new Date().toLocaleString();
    
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Research Analysis Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 40px 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #00d9ff;
        }
        .header h1 {
            color: #1a1a3e;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        .header .timestamp {
            color: #666;
            font-size: 0.9rem;
        }
        .analysis-section {
            margin-bottom: 40px;
            padding: 30px;
            border-radius: 8px;
            border-left: 4px solid #00d9ff;
        }
        .summary-section { background: #e3f2fd; border-left-color: #2196f3; }
        .literature-section { background: #f3e5f5; border-left-color: #9c27b0; }
        .competitive-section { background: #fff3e0; border-left-color: #ff9800; }
        .section-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            font-size: 1.8rem;
            color: #1a1a3e;
        }
        .section-icon { font-size: 2rem; }
        .section-content {
            color: #333;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }
        th {
            background: #1a1a3e;
            color: white;
            font-weight: 600;
        }
        tr:nth-child(even) { background: #f9f9f9; }
        strong { color: #1a1a3e; }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 AI Research Analysis Report</h1>
            <div class="timestamp">Generated on: ${timestamp}</div>
        </div>
        
        ${sections.summary ? `
        <div class="analysis-section summary-section">
            <div class="section-header">
                <span class="section-icon">📝</span>
                <span>Summary Analysis</span>
            </div>
            <div class="section-content">
                ${formatSummaryForHTML(sections.summary)}
            </div>
        </div>
        ` : ''}
        
        ${sections.literature ? `
        <div class="analysis-section literature-section">
            <div class="section-header">
                <span class="section-icon">📚</span>
                <span>Literature Review</span>
            </div>
            <div class="section-content">
                ${formatSummaryForHTML(sections.literature)}
            </div>
        </div>
        ` : ''}
        
        ${sections.competitive ? `
        <div class="analysis-section competitive-section">
            <div class="section-header">
                <span class="section-icon">🏆</span>
                <span>Competitive Analysis</span>
            </div>
            <div class="section-content">
                ${formatSummaryForHTML(sections.competitive)}
            </div>
        </div>
        ` : ''}
        
        <div class="footer">
            <p>📊 Generated by AI Research Assistant</p>
            <p>Powered by Google ADK & Gemini AI</p>
        </div>
    </div>
</body>
</html>`;
}

// Format summary for HTML export
function formatSummaryForHTML(text) {
    text = convertMarkdownTables(text);
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

// Download file helper
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
