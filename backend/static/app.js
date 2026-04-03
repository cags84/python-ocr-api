document.addEventListener('DOMContentLoaded', () => {
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const uploadContent = document.querySelector('.upload-content');
    const uploadProgress = document.getElementById('upload-progress');
    const resultSection = document.getElementById('result-section');
    
    const copyBtn = document.getElementById('copy-btn');
    const downloadBtn = document.getElementById('download-btn');
    const newBtn = document.getElementById('new-btn');
    
    const markdownOutput = document.getElementById('markdown-output');
    const previewView = document.getElementById('preview-view');
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    const viewPanels = document.querySelectorAll('.view-panel');

    let currentFileName = "document.md";
    let currentMarkdown = "";

    let recaptchaSiteKey = null;

    // Inicializar configuración y captcha
    async function initConfig() {
        try {
            const res = await fetch("/api/config");
            const conf = await res.json();
            recaptchaSiteKey = conf.recaptcha_site_key;
            
            // Inyectar Script reCAPTCHA
            const script = document.createElement('script');
            script.src = `https://www.google.com/recaptcha/api.js?render=${recaptchaSiteKey}`;
            document.head.appendChild(script);
        } catch(err) {
            console.error("Error cargando la configuración: ", err);
        }
    }
    
    initConfig();

    // Abrir selector al hacer click
    uploadZone.addEventListener('click', () => fileInput.click());

    // Manejo de Drag & Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => uploadZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('dragover'), false);
    });

    uploadZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if(files.length) {
            handleFiles(files);
        }
    }

    fileInput.addEventListener('change', function() {
        if (this.files.length) {
            handleFiles(this.files);
        }
    });

    let currentPollInterval = null;

    async function handleFiles(files) {
        const file = files[0];
        if (file.type !== 'application/pdf') {
            alert('Por favor, selecciona un archivo PDF válido.');
            return;
        }

        // Mostrar progreso
        uploadContent.classList.add('hidden');
        uploadProgress.classList.remove('hidden');
        uploadZone.style.pointerEvents = 'none';
        
        // Reset progress bar
        document.getElementById('progress-bar').style.width = '0%';
        document.getElementById('progress-text').innerText = 'Procesando... 0%';

        // Prevenir subidas si no está cargado el antispam
        if (!recaptchaSiteKey || typeof grecaptcha === 'undefined') {
            alert("Validación de seguridad inicializándose. Por favor espera un momento e intenta de nuevo.");
            uploadContent.classList.remove('hidden');
            uploadProgress.classList.add('hidden');
            uploadZone.style.pointerEvents = 'auto';
            return;
        }

        // Ejecutar reCAPTCHA v3
        grecaptcha.ready(function() {
            grecaptcha.execute(recaptchaSiteKey, {action: 'upload_document'}).then(async function(token) {
                
                const formData = new FormData();
                formData.append('file', file);
                formData.append('recaptcha_token', token);

                try {
                    const response = await fetch('/api/process', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        const errData = await response.json();
                        throw new Error(errData.detail || 'Error procesando el archivo');
                    }

                    const data = await response.json();
                    const taskId = data.task_id;
                    
                    // Iniciar polling
                    pollStatus(taskId);
                    
                } catch (error) {
                    handleError(error);
                }
            }).catch(function(err) {
                 handleError(new Error("Error de reCAPTCHA: No pudimos validar tu sesión segura."));
            });
        });
    }
    
    function pollStatus(taskId) {
        if (currentPollInterval) clearInterval(currentPollInterval);
        
        currentPollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/status/${taskId}`);
                if (!res.ok) throw new Error("Error obteniendo estado");
                
                const data = await res.json();
                
                // Actualizar UI
                const pBar = document.getElementById('progress-bar');
                const pText = document.getElementById('progress-text');
                
                pBar.style.width = `${data.progress}%`;
                
                if (data.status_text) {
                    pText.innerText = `${data.status_text} ${data.progress}%`;
                } else {
                    pText.innerText = `Procesando... ${data.progress}%`;
                }
                
                if (data.status === 'completed') {
                    clearInterval(currentPollInterval);
                    setTimeout(() => {
                        showResult(data.result, data.filename, data.stats);
                    }, 500); // Pequeño retraso para que se vea el 100%
                } else if (data.status === 'error') {
                    clearInterval(currentPollInterval);
                    throw new Error(data.error);
                }
                
            } catch (err) {
                clearInterval(currentPollInterval);
                handleError(err);
            }
        }, 1000); // Poll cada segundo
    }
    
    function handleError(error) {
        alert(`${error.message}`);
        // Restaurar estado
        uploadContent.classList.remove('hidden');
        uploadProgress.classList.add('hidden');
        uploadZone.style.pointerEvents = 'auto';
    }

    function showResult(markdown, filename, stats) {
        currentMarkdown = markdown;
        currentFileName = filename.replace('.pdf', '.md');
        
        // Renderizar estadísticas si existen
        if (stats) {
            document.getElementById('stats-card').classList.remove('hidden');
            document.getElementById('stat-raw').innerText = stats.raw_len.toLocaleString();
            document.getElementById('stat-opt').innerText = stats.opt_len.toLocaleString();
            
            if (stats.raw_len > 0) {
                const saved = ((stats.raw_len - stats.opt_len) / stats.raw_len) * 100;
                document.getElementById('stat-saved').innerText = `${saved.toFixed(1)}%`;
            }
        } else {
            document.getElementById('stats-card').classList.add('hidden');
        }
        
        // Ocultar subida, mostrar resultado
        uploadZone.classList.add('hidden');
        resultSection.classList.remove('hidden');
        
        // Renderizar código raw y HTML final
        markdownOutput.textContent = markdown;
        previewView.innerHTML = marked.parse(markdown);
    }

    // Toggle Vista Markdown / Previa
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const viewType = e.target.getAttribute('data-view');
            
            toggleBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            viewPanels.forEach(panel => {
                panel.classList.remove('active');
            });
            document.getElementById(`${viewType}-view`).classList.add('active');
        });
    });

    // Botones de acción
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(currentMarkdown);
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copiado';
            setTimeout(() => { copyBtn.innerHTML = originalText; }, 2000);
        } catch (err) {
            console.error('Error al copiar: ', err);
        }
    });

    downloadBtn.addEventListener('click', () => {
        const blob = new Blob([currentMarkdown], { type: 'text/markdown' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = currentFileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    });

    newBtn.addEventListener('click', () => {
        fileInput.value = '';
        currentMarkdown = '';
        resultSection.classList.add('hidden');
        uploadZone.classList.remove('hidden');
        uploadContent.classList.remove('hidden');
        uploadProgress.classList.add('hidden');
        uploadZone.style.pointerEvents = 'auto';
    });
});
