export async function callApi(mode, data) {
    const res = await fetch(`/api/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
    }

    return await res.json();
}
