/**
 * Initialize password strength indicator
 * @param {string} passwordInputId - ID of the password input field
 * @param {Object} options - Configuration options
 */
function initPasswordStrength(passwordInputId = 'password', options = {}) {
    // Default configuration
    const config = {
        minLength: 8,
        showDetails: true,
        customMessages: {
            weak: 'Weak',
            fair: 'Fair',
            good: 'Good',
            strong: 'Strong',
            veryStrong: 'Very Strong'
        },
        ...options
    };

    // Get DOM elements
    const passwordInput = document.getElementById(passwordInputId);
    const strengthBar = document.getElementById('strengthBar');
    const strengthLevel = document.getElementById('strengthLevel');
    const strengthText = document.getElementById('strengthText');

    if (!passwordInput || !strengthBar || !strengthLevel) {
        console.error('Password strength: Required elements not found');
        return;
    }

    // Password strength criteria
    const criteria = {
        length: (password) => password.length >= config.minLength,
        lowercase: (password) => /[a-z]/.test(password),
        uppercase: (password) => /[A-Z]/.test(password),
        numbers: (password) => /\d/.test(password),
        symbols: (password) => /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`]/.test(password),
        noRepeating: (password) => !/(.)\1{2,}/.test(password),
        noSequential: (password) => {
            const sequences = ['012', '123', '234', '345', '456', '567', '678', '789', '890',
                             'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij', 'ijk',
                             'jkl', 'klm', 'lmn', 'mno', 'nop', 'opq', 'pqr', 'qrs', 'rst',
                             'stu', 'tuv', 'uvw', 'vwx', 'wxy', 'xyz'];
            const lowerPassword = password.toLowerCase();
            return !sequences.some(seq => lowerPassword.includes(seq));
        }
    };

    /**
     * Calculate password strength score
     * @param {string} password 
     * @returns {Object} Score and breakdown
     */
    function calculateStrength(password) {
        if (!password) {
            return { score: 0, level: 'Enter password', percentage: 0, feedback: [] };
        }

        let score = 0;
        const feedback = [];
        const passed = {};

        // Basic criteria scoring
        Object.keys(criteria).forEach(key => {
            passed[key] = criteria[key](password);
            if (passed[key]) {
                score += getScoreForCriteria(key, password);
            }
        });

        // Length bonus
        if (password.length > config.minLength) {
                
        }

        // Entropy bonus for character variety
        const uniqueChars = new Set(password).size;
        score += Math.min(uniqueChars * 2, 20);

        // Generate feedback
        if (!passed.length) feedback.push(`Use at least ${config.minLength} characters`);
        if (!passed.lowercase) feedback.push('Add lowercase letters');
        if (!passed.uppercase) feedback.push('Add uppercase letters');
        if (!passed.numbers) feedback.push('Add numbers');
        if (!passed.symbols) feedback.push('Add special characters');
        if (!passed.noRepeating) feedback.push('Avoid repeating characters');
        if (!passed.noSequential) feedback.push('Avoid sequential patterns');

        // Determine strength level
        const { level, percentage } = getStrengthLevel(score);

        return { score, level, percentage, feedback, passed };
    }

    /**
     * Get score for specific criteria
     * @param {string} criteria 
     * @param {string} password 
     * @returns {number}
     */
    function getScoreForCriteria(criteria, password) {
        const scores = {
            length: 20,
            lowercase: 10,
            uppercase: 10,
            numbers: 10,
            symbols: 15,
            noRepeating: 10,
            noSequential: 5
        };
        return scores[criteria] || 0;
    }

    /**
     * Determine strength level and percentage
     * @param {number} score 
     * @returns {Object}
     */
    function getStrengthLevel(score) {
        if (score >= 80) return { level: config.customMessages.veryStrong, percentage: 100 };
        if (score >= 60) return { level: config.customMessages.strong, percentage: 80 };
        if (score >= 40) return { level: config.customMessages.good, percentage: 60 };
        if (score >= 20) return { level: config.customMessages.fair, percentage: 40 };
        return { level: config.customMessages.weak, percentage: 20 };
    }

    /**
     * Update UI elements
     * @param {Object} strength 
     */
    function updateUI(strength) {
        const { level, percentage, feedback } = strength;

        // Update progress bar
        strengthBar.style.width = `${percentage}%`;
        strengthBar.setAttribute('aria-valuenow', percentage);

        // Update color based on strength
        strengthBar.className = 'progress-bar ' + getColorClass(percentage);

        // Update text
        strengthLevel.textContent = level;

        // Add feedback if enabled
        if (config.showDetails && feedback.length > 0 && percentage < 100) {
            const feedbackText = feedback.slice(0, 2).join(', ');
            strengthText.innerHTML = `Password strength: <span id="strengthLevel">${level}</span><br><small class="text-muted">${feedbackText}</small>`;
        } else {
            strengthText.innerHTML = `Password strength: <span id="strengthLevel">${level}</span>`;
        }

        // Dispatch custom event for integration
        passwordInput.dispatchEvent(new CustomEvent('passwordStrengthChanged', {
            detail: strength
        }));
    }

    /**
     * Get Bootstrap color class based on percentage
     * @param {number} percentage 
     * @returns {string}
     */
    function getColorClass(percentage) {
        if (percentage >= 80) return 'bg-success';
        if (percentage >= 60) return 'bg-info';
        if (percentage >= 40) return 'bg-warning';
        return 'bg-danger';
    }

    /**
     * Debounce function for performance
     * @param {Function} func 
     * @param {number} delay 
     * @returns {Function}
     */
    function debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // Initialize event listener with debouncing
    const debouncedUpdate = debounce((password) => {
        const strength = calculateStrength(password);
        updateUI(strength);
    }, 150);

    passwordInput.addEventListener('input', (event) => {
        debouncedUpdate(event.target.value);
    });

    passwordInput.addEventListener('focus', () => {
        const strength = calculateStrength(passwordInput.value);
        updateUI(strength);
    });

    // Initial state
    updateUI({ level: 'Enter password', percentage: 0, feedback: [] });

    // Return API for external access
    return {
        checkPassword: (password) => calculateStrength(password),
        updateConfig: (newConfig) => Object.assign(config, newConfig),
        getConfig: () => ({ ...config })
    };
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = initPasswordStrength;
}