/**
 * Universal function to clear all form field errors across scripts or within a given scope.
 * 
 * @param {string|HTMLElement|null} scope - Optional.
 *        Accepts:
 *         - a prefix string (like 'uploadDoc') to target elements starting with that ID,
 *         - a CSS selector (like '#myModal' or '.modal'),
 *         - or an HTMLElement reference to a form/container.
 *        If omitted, clears errors globally.
 */
function clearAllErrors(scope = null) {
    let container;

    // Determine scope container
    if (typeof scope === 'string') {
        // Try treating as selector first
        container = document.querySelector(scope);
        
        // If not a valid selector, treat as ID prefix
        if (!container) {
            const errorElements = document.querySelectorAll(`[id^="${scope}"]`);
            errorElements.forEach(el => clearElementErrors(el));
            return;
        }
    } else if (scope instanceof HTMLElement) {
        container = scope;
    } else {
        // Default to entire document
        container = document;
    }

    // 1️⃣ Clear input field error styling
    const errorInputs = container.querySelectorAll('.ucm-input-error, .input-error, .has-error');
    errorInputs.forEach(input => input.classList.remove('ucm-input-error', 'input-error', 'has-error'));

    // 2️⃣ Clear text-based error messages (using common conventions)
    const errorLabels = container.querySelectorAll(
        '[id$="Error"], .error-message, .form-error, .validation-error, .ucm-error'
    );
    errorLabels.forEach(label => {
        if (label instanceof HTMLElement) label.textContent = '';
    });

    // 3️⃣ Clear alert/notification containers (if any)
    const alertContainers = container.querySelectorAll(
        '.alert-container, .ucm-alert-container, .form-alert, .alert, [id$="AlertContainer"]'
    );
    alertContainers.forEach(alertBox => {
        alertBox.innerHTML = '';
    });
}

/**
 * Internal helper to clear error styling/messages for a single element or subtree.
 */
function clearElementErrors(element) {
    if (!element) return;

    // Clear error classes
    if (element.classList) {
        element.classList.remove('ucm-input-error', 'input-error', 'has-error');
    }

    // Clear error text if element has an associated "*Error" span or div
    const id = element.id;
    if (id) {
        const errorEl = document.getElementById(`${id}Error`);
        if (errorEl) errorEl.textContent = '';
    }

    // Also clear descendants
    const descendants = element.querySelectorAll('.ucm-input-error, .input-error, [id$="Error"]');
    descendants.forEach(child => {
        if (child.classList) child.classList.remove('ucm-input-error', 'input-error', 'has-error');
        if (child.id && child.id.endsWith('Error')) child.textContent = '';
    });
}
