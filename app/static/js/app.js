const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

let currentMode = 'scrape';
let lastResult = null;

// Mode configurations
const modeOptions = {
    scrape: [
        { id: 'format', label: 'Format', type: 'select', options: ['markdown', 'text', 'html'], default: 'markdown' },
        { id: 'includeLinks', label: 'Include Links', type: 'select', options: ['true', 'false'], default: 'true' },
        { id: 'includeImages', label: 'Include Images', type: 'select', options: ['true', 'false'], default: 'true' }
    ],
    search: [
        { id: 'query', label: 'Search Query', type: 'text', placeholder: 'main content', default: '' },
        { id: 'topK', label: 'Top Results', type: 'number', default: '10' }
    ],
    agent: [
        { id: 'instruction', label: 'Instruction', type: 'textarea', placeholder: 'Extract product names and prices', default: '' },
        { id: 'model', label: 'AI Model', type: 'select', options: ['xiaomi/mimo-v2-flash:free', 'mistralai/devstral-2512:free'], default: 'xiaomi/mimo-v2-flash:free' }
    ],
    map: [
        { id: 'maxDepth', label: 'Max Depth', type: 'number', default: '2' },
        { id: 'maxPages', label: 'Max Pages', type: 'number', default: '50' },
        { id: 'sameDomain', label: 'Same Domain', type: 'select', options: ['true', 'false'], default: 'true' }
    ],
    crawl: [
        { id: 'urls', label: 'URLs (one per line)', type: 'textarea', placeholder: 'https://example.com\nhttps://another.com', default: '' },
        { id: 'batchSize', label: 'Batch Size', type: 'number', default: '3' },
        { id: 'format', label: 'Format', type: 'select', options: ['markdown', 'text', 'html'], default: 'markdown' }
    ]
};

// Mode tabs
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

// Output tabs
$$('.code-tab').forEach(tab => {
    tab.onclick = () => {
        $$('.code-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        displayResult(lastResult, tab.dataset.view);
    };
});

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

function highlightJson(obj) {
    const json = JSON.stringify(obj, null, 2);
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        let cls = 'json-number';
        if (/^"/.test(match)) {
            cls = /:$/.test(match) ? 'json-key' : 'json-string';
        } else if (/true|false/.test(match)) {
            cls = 'json-boolean';
        } else if (/null/.test(match)) {
            cls = 'json-null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
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

async function submit() {
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
        const res = await fetch(`/api/${currentMode}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });

        const data = await res.json();
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

function copyOutput() {
    const text = $('#codeOutput').textContent;
    navigator.clipboard.writeText(text).then(() => alert('Copied!'));
}

function downloadOutput() {
    if (!lastResult) return;
    const blob = new Blob([JSON.stringify(lastResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `crawl-${currentMode}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// Events
$('#submitBtn').onclick = submit;
$('#urlInput').onkeypress = (e) => { if (e.key === 'Enter') submit(); };

// Init
renderOptions();
$('#optionsPanel').classList.add('visible');
