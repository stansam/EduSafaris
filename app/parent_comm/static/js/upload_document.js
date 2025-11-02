// Upload Document Modal Script
let selectedFile = null;

// Open modal
function openUploadDocumentModal(childId) {
    const modal = document.getElementById('uploadDocumentModal');
    const child = getChildById(childId);
    
    if (child) {
        document.getElementById('uploadDocChildId').value = childId;
        document.getElementById('uploadDocChildName').textContent = `${child.first_name} ${child.last_name}`;
    }
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    resetUploadDocumentForm();
}

// Close modal
function closeUploadDocumentModal() {
    const modal = document.getElementById('uploadDocumentModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    resetUploadDocumentForm();
}

// Reset form
function resetUploadDocumentForm() {
    const form = document.getElementById('uploadDocumentForm');
    form.reset();
    clearAllErrors('uploadDoc');
    clearSelectedFile();
    document.getElementById('uploadDocProgress').style.display = 'none';
    document.getElementById('uploadDocProgressBar').style.width = '0%';
}

// Handle file selection
document.getElementById('uploadDocFile').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        handleFileSelection(file);
    }
});

// Handle drag and drop
const dropzone = document.getElementById('uploadDocDropzone');

dropzone.addEventListener('dragover', function(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.add('dragover');
});

dropzone.addEventListener('dragleave', function(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('dragover');
});

dropzone.addEventListener('drop', function(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelection(files[0]);
    }
});

// Handle file selection
function handleFileSelection(file) {
    // Validate file type
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 
                          'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    
    if (!allowedTypes.includes(file.type)) {
        showValidationError('uploadDocFile', 'Invalid file type. Please upload PDF, JPG, PNG, or DOC files.');
        return;
    }
    
    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
        showValidationError('uploadDocFile', 'File too large. Maximum size is 10MB.');
        return;
    }
    
    // Store selected file
    selectedFile = file;
    
    // Display selected file
    document.getElementById('uploadDocFileName').textContent = file.name;
    document.getElementById('uploadDocFileSize').textContent = formatFileSize(file.size);
    document.getElementById('uploadDocFileSelected').style.display = 'flex';
    document.getElementById('uploadDocDropzone').style.display = 'none';
    
    // Clear any previous errors
    document.getElementById('uploadDocFileError').textContent = '';
}

// Clear selected file
function clearSelectedFile() {
    selectedFile = null;
    document.getElementById('uploadDocFile').value = '';
    document.getElementById('uploadDocFileSelected').style.display = 'none';
    document.getElementById('uploadDocDropzone').style.display = 'block';
}

// Validate form
function validateUploadDocumentForm() {
    const errors = [];
    
    const title = document.getElementById('uploadDocTitle').value.trim();
    const docType = document.getElementById('uploadDocType').value;
    
    if (!title) {
        showValidationError('uploadDocTitle', 'Document title is required');
        errors.push('Missing title');
    }
    
    if (!docType) {
        showValidationError('uploadDocType', 'Document type is required');
        errors.push('Missing document type');
    }
    
    if (!selectedFile) {
        showValidationError('uploadDocFile', 'Please select a file to upload');
        errors.push('Missing file');
    }
    
    return errors;
}

// Handle form submission
document.getElementById('uploadDocumentForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Clear previous errors
    clearAllErrors('uploadDoc');
    
    // Validate form
    const validationErrors = validateUploadDocumentForm();
    if (validationErrors.length > 0) {
        showNotification('Please correct the errors in the form', 'error');
        return;
    }
    
    const childId = document.getElementById('uploadDocChildId').value;
    
    // Prepare form data
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('title', document.getElementById('uploadDocTitle').value.trim());
    formData.append('document_type', document.getElementById('uploadDocType').value);
    formData.append('description', document.getElementById('uploadDocDescription').value.trim());
    
    const expiryDate = document.getElementById('uploadDocExpiry').value;
    if (expiryDate) {
        formData.append('expiry_date', expiryDate);
    }
    
    // Show loading state
    const submitBtn = document.getElementById('uploadDocSubmitBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    
    // Show progress bar
    const progressDiv = document.getElementById('uploadDocProgress');
    const progressBar = document.getElementById('uploadDocProgressBar');
    const progressText = document.getElementById('uploadDocProgressText');
    progressDiv.style.display = 'block';
    
    try {
        const xhr = new XMLHttpRequest();
        
        // Track upload progress
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressBar.style.width = percentComplete + '%';
                progressText.textContent = `Uploading... ${Math.round(percentComplete)}%`;
            }
        });
        
        // Handle completion
        xhr.addEventListener('load', function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                const data = JSON.parse(xhr.responseText);
                if (data.success) {
                    showNotification('Document uploaded successfully!', 'success');
                    closeUploadDocumentModal();
                    refreshChildren();
                } else {
                    showNotification(data.error || 'Failed to upload document', 'error');
                }
            } else {
                showNotification('Upload failed. Please try again.', 'error');
            }
            
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        });
        
        // Handle errors
        xhr.addEventListener('error', function() {
            showNotification('Network error. Please check your connection.', 'error');
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        });
        
        // Send request
        xhr.open('POST', `/api/parent/children/${childId}/documents`);
        xhr.setRequestHeader('Authorization', `Bearer ${getAuthToken()}`);
        xhr.send(formData);
        
    } catch (error) {
        console.error('Error uploading document:', error);
        showNotification('Failed to upload document', 'error');
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
});

// Close modal when clicking outside
document.getElementById('uploadDocumentModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeUploadDocumentModal();
    }
});