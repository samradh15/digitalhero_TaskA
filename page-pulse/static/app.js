document.addEventListener('DOMContentLoaded', () => {
    const screens = {
        intake: document.getElementById('intake-screen'),
        loading: document.getElementById('loading-screen'),
        error: document.getElementById('error-screen'),
        report: document.getElementById('report-screen')
    };

    const form = document.getElementById('audit-form');
    const urlInput = document.getElementById('url-input');
    const resetButtons = [document.getElementById('reset-button-error'), document.getElementById('reset-button-success')];
    
    // Elements for updating
    const loadingStatus = document.getElementById('loading-status');
    const loadingPulseWrapper = document.getElementById('loading-pulse-wrapper');
    const reportPulseWrapper = document.getElementById('report-pulse-wrapper');
    const errorMessage = document.getElementById('error-message');

    // Show a specific screen
    function showScreen(screenName) {
        Object.values(screens).forEach(el => {
            el.style.display = 'none';
        });
        screens[screenName].style.display = 'block';
        
        if (screenName === 'report') {
            document.body.classList.add('state-success');
        } else {
            document.body.classList.remove('state-success');
        }
    }

    // Reset app state
    function resetApp() {
        urlInput.value = '';
        showScreen('intake');
        urlInput.focus();
    }

    resetButtons.forEach(btn => btn.addEventListener('click', resetApp));

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const url = urlInput.value.trim();
        if (!url) return;

        // Basic client validation before submitting
        try {
            new URL(url);
        } catch (err) {
            showError("Malformed URL — please enter a valid web address starting with http:// or https://");
            return;
        }

        startLoading(url);

        try {
            const response = await fetch('/api/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                const errMsg = data.error ? data.error.message : "An unexpected error occurred.";
                showError(errMsg);
                return;
            }

            showReport(data);
        } catch (err) {
            showError("Network error — couldn't connect to the Pulse API.");
        }
    });

    function startLoading(url) {
        loadingStatus.textContent = `Scanning ${url}...`;
        loadingPulseWrapper.innerHTML = generatePulseSVG('loading');
        showScreen('loading');
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        showScreen('error');
    }

    // Thresholds
    function determineStatus(value, thresholds) {
        // thresholds is an object with { stable: function, attention: function, critical: function }
        if (thresholds.critical(value)) return 'critical';
        if (thresholds.attention(value)) return 'attention';
        return 'stable';
    }

    function updateRow(id, value, statusClass, format = (v) => v) {
        const valEl = document.getElementById(`val-${id}`);
        const dotEl = document.getElementById(`dot-${id}`);
        
        if (value === null || value === undefined) {
            valEl.textContent = 'Not found';
            valEl.style.opacity = '0.5';
        } else {
            valEl.textContent = format(value);
            valEl.style.opacity = '1';
        }

        dotEl.className = 'status-dot'; // reset
        if (statusClass) {
            dotEl.classList.add(statusClass);
        }
    }

    function showReport(data) {
        document.getElementById('report-url').textContent = data.url;
        document.getElementById('report-timestamp').textContent = data.scanned_at;

        // Vitals
        const statusClass = determineStatus(data.status_code, {
            critical: v => v >= 400,
            attention: v => v >= 300 && v < 400,
            stable: v => v < 300
        });
        updateRow('status', data.status_code, statusClass);

        const timeClass = determineStatus(data.response_time_ms, {
            critical: v => v > 3000,
            attention: v => v > 1000,
            stable: v => v <= 1000
        });
        updateRow('time', data.response_time_ms, timeClass, v => `${v}ms`);

        const typeClass = data.content_type.includes('text/html') ? 'stable' : 'critical';
        updateRow('type', data.content_type, typeClass);

        // Findings
        updateRow('title', data.title, data.title ? 'stable' : 'critical');
        updateRow('meta', data.meta_description, data.meta_description ? 'stable' : 'attention');
        
        const h1Class = determineStatus(data.h1_count, {
            critical: v => v === 0,
            attention: v => v > 1,
            stable: v => v === 1
        });
        updateRow('h1', data.h1_count, h1Class);

        const altClass = determineStatus(data.images_missing_alt, {
            critical: v => v > 5 || (data.images_total > 0 && (v / data.images_total) > 0.5),
            attention: v => v > 0,
            stable: v => v === 0
        });
        const altText = data.images_total === 0 ? '0 (No images)' : `${data.images_missing_alt} of ${data.images_total}`;
        updateRow('alt', data.images_missing_alt, altClass, () => altText);

        updateRow('words', data.word_count, 'stable'); // Word count is neutral

        // Report Pulse
        // overall health driven by status and response time
        let overallHealth = 'stable';
        if (statusClass === 'critical' || timeClass === 'critical' || h1Class === 'critical' || altClass === 'critical') {
            overallHealth = 'critical';
        } else if (statusClass === 'attention' || timeClass === 'attention' || altClass === 'attention') {
            overallHealth = 'attention';
        }

        reportPulseWrapper.innerHTML = generatePulseSVG('result', overallHealth);

        showScreen('report');
    }

    // Generate Pulse SVG
    function generatePulseSVG(mode, health = 'stable') {
        const width = 640;
        const height = mode === 'loading' ? 80 : 40;
        const cy = height / 2;
        
        let points = [];
        let strokeClass = 'stable';
        
        if (mode === 'loading') {
            // Calm, steady animated pulse
            points = `0,${cy} 100,${cy} 110,${cy-20} 120,${cy+30} 130,${cy-10} 140,${cy} 640,${cy}`;
            strokeClass = 'stable';
        } else {
            // Result pulse, varied by health
            strokeClass = health;
            
            if (health === 'stable') {
                // steady
                points = `0,${cy} 100,${cy} 110,${cy-10} 120,${cy+15} 130,${cy-5} 140,${cy} 300,${cy} 310,${cy-10} 320,${cy+15} 330,${cy-5} 340,${cy} 640,${cy}`;
            } else if (health === 'attention') {
                // jittery
                points = `0,${cy} 50,${cy} 60,${cy-15} 70,${cy+25} 80,${cy-10} 90,${cy+5} 100,${cy} 250,${cy} 260,${cy-15} 270,${cy+25} 280,${cy-10} 290,${cy+5} 300,${cy} 640,${cy}`;
            } else {
                // chaotic
                points = `0,${cy} 30,${cy-20} 40,${cy+30} 50,${cy-15} 60,${cy+35} 70,${cy-25} 80,${cy+10} 90,${cy} 150,${cy} 160,${cy-20} 170,${cy+30} 180,${cy-15} 190,${cy+35} 200,${cy-25} 210,${cy+10} 220,${cy} 640,${cy}`;
            }
        }

        const animationClass = mode === 'loading' ? 'animate' : '';

        return `
            <svg width="100%" height="100%" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
                <polyline 
                    points="${points}" 
                    class="pulse-line ${strokeClass} ${animationClass}"
                />
            </svg>
        `;
    }
});
