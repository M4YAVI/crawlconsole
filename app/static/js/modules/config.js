export const modeOptions = {
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
