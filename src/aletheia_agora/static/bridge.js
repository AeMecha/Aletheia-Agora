/* Browser adapter for the original vanilla interface. No Electron, Node,
 * framework, generated HTML, or frontend build step is needed. */
(() => {
    const hash = new URLSearchParams(location.hash.slice(1));
    if (hash.has('token')) {
        sessionStorage.setItem('aletheia.agora.access', hash.get('token'));
        history.replaceState(null, '', location.pathname + location.search);
    }
    const listeners = new Set();
    let authenticating;
    const access = () => sessionStorage.getItem('aletheia.agora.access') || '';
    const headers = () => ({ Authorization: 'Bearer ' + access() });
    async function login() {
        if (authenticating) return authenticating;
        authenticating = new Promise(resolve => {
            const dialog = document.getElementById('access-dialog');
            document.getElementById('access-form').onsubmit = event => {
                event.preventDefault();
                sessionStorage.setItem('aletheia.agora.access', document.getElementById('access-token').value.trim());
                document.getElementById('access-token').value = '';
                dialog.close(); resolve();
            };
            dialog.showModal();
        });
        try { await authenticating; } finally { authenticating = null; }
    }
    async function request(url, options = {}) {
        let response = await fetch(url, { ...options, headers: { ...headers(), ...options.headers } });
        if (response.status === 401) {
            await login();
            response = await fetch(url, { ...options, headers: { ...headers(), ...options.headers } });
        }
        const result = await response.json();
        if (!result.ok) throw new Error(result.error || 'The application request failed.');
        return result.value;
    }
    const action = (name, args) => request('/api/actions/' + name, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ args }) });
    const names = ['ask', 'draft', 'save', 'renameTitle', 'theme', 'newChat', 'cancel', 'settings', 'connect', 'models', 'downloadModel', 'document', 'refresh'];
    const api = Object.fromEntries(names.map(name => [name, (...args) => action(name, args)]));
    api.snapshot = () => request('/api/state');
    api.onState = listener => { listeners.add(listener); return () => listeners.delete(listener); };
    async function poll() {
        try { const state = await api.snapshot(); for (const listener of listeners) listener(state); }
        catch (error) { if (!authenticating) console.warn('Library state:', error.message); }
        finally { setTimeout(poll, 750); }
    }
    function chooseFiles(folder, accept) {
        return new Promise(resolve => {
            const input = document.createElement('input');
            input.type = 'file'; input.accept = accept; input.multiple = accept !== '.gguf';
            if (folder) input.setAttribute('webkitdirectory', '');
            input.hidden = true;
            input.addEventListener('change', () => { resolve([...input.files]); input.remove(); }, { once: true });
            input.addEventListener('cancel', () => { resolve([]); input.remove(); }, { once: true });
            document.body.append(input); input.click();
        });
    }
    api.import = async folder => {
        const files = (await chooseFiles(folder, '.md')).filter(file => file.name.toLowerCase().endsWith('.md'));
        if (!files.length) return null;
        if (files.some(file => file.size > 2 * 1024 * 1024) || files.reduce((sum, file) => sum + file.size, 0) > 30 * 1024 * 1024) throw new Error('Import Markdown files up to 2 MiB each and 30 MiB per batch.');
        const values = [];
        for (const file of files) values.push({ name: file.name, content: await file.text() });
        return action('importContents', [values]);
    };
    api.chooseModel = () => new Promise((resolve, reject) => {
        const dialog = document.getElementById('model-file-dialog');
        let pending = false;
        const finish = async operation => {
            if (pending) return;
            pending = true; dialog.close();
            try { resolve(await operation()); } catch (error) { reject(error); }
        };
        document.getElementById('model-file-form').onsubmit = event => {
            event.preventDefault();
            finish(() => action('chooseModel', [document.getElementById('server-model-path').value.trim()]));
        };
        document.getElementById('upload-model-file').onclick = async () => {
            const [file] = await chooseFiles(false, '.gguf');
            if (file) finish(() => request('/api/model/upload', { method: 'POST', headers: { 'Content-Type': 'application/octet-stream', 'X-Model-Filename': encodeURIComponent(file.name) }, body: file }));
        };
        document.getElementById('close-model-file').onclick = () => dialog.close();
        dialog.oncancel = () => { if (!pending) resolve(null); };
        dialog.onclose = () => { if (!pending) resolve(null); };
        dialog.showModal();
    });
    api.openFolder = async () => {
        const directory = await action('openFolder', []);
        alert('Your archive is stored on the server computer:\n\n' + directory);
        return directory;
    };
    api.export = async id => {
        const document = await api.document(id);
        const url = URL.createObjectURL(new Blob([document.content], { type: 'text/markdown;charset=utf-8' }));
        const anchor = window.document.createElement('a');
        anchor.href = url; anchor.download = id.replace(/[^\p{L}\p{N}_-]/gu, '_') + '.md'; anchor.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        return true;
    };
    window.aletheia = api;
    setTimeout(poll, 750);
})();
