import { $, $$, highlightJson } from './modules/utils.js';
import { modeOptions } from './modules/config.js?v=2';
import { callApi } from './modules/api.js';

let currentMode = 'scrape';
let lastResult = null;

// Render Options Panel
function renderOptions() {
    const options = modeOptions[currentMode];
    $('#optionsTitle').textContent = currentMode.charAt(0).toUpperCase() + currentMode.slice(1) + ' Options';

    let html = '';
    options.forEach(opt => {
        html += `<div class="option-group">`;
        html += `<label class="option-label">${opt.label}</label>`;

        if (opt.type === 'select') {
            html += `<select id="opt-${opt.id}" class="option-select">`;
            opt.options.forEach(o => {
                html += `<option value="${o}" ${o === opt.default ? 'selected' : ''}>${o}</option>`;
            });
            html += `</select>`;
        } else if (opt.type === 'textarea') {
            html += `<textarea id="opt-${opt.id}" class="option-input" placeholder="${opt.placeholder || ''}">${opt.default}</textarea>`;
        } else {
            html += `<input type="${opt.type}" id="opt-${opt.id}" class="option-input" value="${opt.default}" placeholder="${opt.placeholder || ''}"/>`;
        }
        html += `</div>`;
    });

    $('#optionsGrid').innerHTML = html;
}

function getOptionValue(id) {
    const el = $(`#opt-${id}`);
    return el ? el.value : null;
}

function buildRequest() {
    const url = $('#urlInput').value.trim();

    switch (currentMode) {
        case 'scrape':
            return {
                url,
                format: getOptionValue('format'),
                include_links: getOptionValue('includeLinks') === 'true',
                include_images: getOptionValue('includeImages') === 'true',
                use_browser: true
            };
        case 'search':
            return {
                url,
                query: getOptionValue('query') || 'main content',
                top_k: parseInt(getOptionValue('topK')) || 10
            };
        case 'agent':
            return {
                url,
                instruction: getOptionValue('instruction') || 'Extract key information',
                model: getOptionValue('model')
            };
        case 'map':
            return {
                url,
                max_depth: parseInt(getOptionValue('maxDepth')) || 2,
                max_pages: parseInt(getOptionValue('maxPages')) || 50,
                same_domain: getOptionValue('sameDomain') === 'true'
            };
        case 'crawl':
            const urls = (getOptionValue('urls') || url).split('\n').filter(u => u.trim());
            return {
                urls: urls.length ? urls : [url],
                batch_size: parseInt(getOptionValue('batchSize')) || 3,
                format: getOptionValue('format')
            };
        default:
            return { url };
    }
}

function displayResult(result, view = 'json') {
    if (!result) return;

    const output = $('#codeOutput');

    if (view === 'json') {
        output.innerHTML = highlightJson(result);
    } else if (view === 'markdown') {
        output.textContent = result.content || result.markdown ||
            (result.results ? result.results.map(r => r.content || r.text || '').join('\n\n---\n\n') : 'No markdown content');
    } else if (view === 'text') {
        output.textContent = result.content ||
            (result.results ? result.results.map(r => `${r.url}\n${r.content || r.text || ''}`).join('\n\n---\n\n') : 'No text content');
    }
}

async function handleSubmit() {
    const url = $('#urlInput').value.trim();
    if (!url && currentMode !== 'crawl') {
        alert('Please enter a URL');
        return;
    }

    const btn = $('#submitBtn');
    btn.disabled = true;
    btn.innerHTML = '<div class="loading-spinner"></div>';

    $('#resultsSection').classList.add('visible');
    $('#statusBadge').className = 'status-badge loading';
    $('#statusBadge').textContent = '⏳ Processing...';
    $('#modeBadge').textContent = 'Mode: ' + currentMode;
    $('#codeOutput').textContent = '// Fetching data...';

    try {
        const request = buildRequest();
        const data = await callApi(currentMode, request);
        lastResult = data;

        if (data.success) {
            $('#statusBadge').className = 'status-badge success';
            $('#statusBadge').textContent = '✅ Success';
        } else {
            $('#statusBadge').className = 'status-badge error';
            $('#statusBadge').textContent = '❌ Error';
        }

        displayResult(data, 'json');

    } catch (e) {
        $('#statusBadge').className = 'status-badge error';
        $('#statusBadge').textContent = '❌ Failed';
        $('#codeOutput').textContent = 'Error: ' + e.message;
        lastResult = { error: e.message };
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    }
}

// Global functions for HTML onclick
window.copyOutput = () => {
    const text = $('#codeOutput').textContent;
    navigator.clipboard.writeText(text).then(() => alert('Copied!'));
};

window.downloadOutput = () => {
    if (!lastResult) return;
    const blob = new Blob([JSON.stringify(lastResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `crawl-${currentMode}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
};

// Event Listeners
$$('.mode-tab').forEach(tab => {
    tab.onclick = () => {
        $$('.mode-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentMode = tab.dataset.mode;
        renderOptions();
        $('#optionsPanel').classList.add('visible');
        $('#urlInput').placeholder = currentMode === 'crawl' ? 'Enter URLs in options below' : 'https://example.com';
    };
});

$$('.code-tab').forEach(tab => {
    tab.onclick = () => {
        $$('.code-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        displayResult(lastResult, tab.dataset.view);
    };
});

$('#submitBtn').onclick = handleSubmit;
$('#urlInput').onkeypress = (e) => { if (e.key === 'Enter') handleSubmit(); };

// Initialization
renderOptions();
$('#optionsPanel').classList.add('visible');
console.log('🚀 CrawlConsole Frontend Initialized');
