// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global state
let documents = [];
let currentDocument = null;
let authToken = null;
let currentUser = null;

// ========== AUTHENTICATION FUNCTIONS ==========

function saveAuthToken(token) {
    authToken = token;
    localStorage.setItem('authToken', token);
}

function getAuthToken() {
    if (!authToken) {
        authToken = localStorage.getItem('authToken');
    }
    return authToken;
}

function clearAuthToken() {
    authToken = null;
    localStorage.removeItem('authToken');
}

function isAuthenticated() {
    return !!getAuthToken();
}

async function handleRegister(event) {
    event.preventDefault();
    
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                full_name: name,
                email: email,
                password: password
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Registration failed');
        }
        
        const userData = await response.json();
        showNotification('Registration successful! Please login.', 'success');
        showLoginForm();
        
        // Pre-fill login email
        document.getElementById('loginEmail').value = email;
        
    } catch (error) {
        showNotification(`Registration failed: ${error.message}`, 'error');
    }
}

async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const form = new URLSearchParams();
        form.append("username", email);
        form.append("password", password);

        const response = await fetch(`${API_BASE_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: form
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail);
        }

        const data = await response.json();
        saveAuthToken(data.access_token);

        await fetchCurrentUser();

        document.getElementById('loginScreen').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');

        showNotification('Login successful!', 'success');
        loadDocuments();
        
    } catch (error) {
        showNotification(`Login failed: ${error.message}`, 'error');
    }
}


async function fetchCurrentUser() {
    try {
        currentUser = await apiCall('/me');
        document.getElementById('userEmail').textContent = currentUser.email;
    } catch (error) {
        console.error('Failed to fetch user:', error);
    }
}

function handleLogout() {
    clearAuthToken();
    currentUser = null;
    documents = [];
    
    // Hide app, show login
    document.getElementById('app').classList.add('hidden');
    document.getElementById('loginScreen').classList.remove('hidden');
    
    // Reset forms
    document.getElementById('loginForm').querySelector('form').reset();
    document.getElementById('registerForm').querySelector('form').reset();
    
    showNotification('Logged out successfully', 'info');
}

function showLoginForm() {
    document.getElementById('registerForm').classList.add('hidden');
    document.getElementById('loginForm').classList.remove('hidden');
}

function showRegisterForm() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('registerForm').classList.remove('hidden');
}

// Check authentication on page load
function checkAuthOnLoad() {
    if (isAuthenticated()) {
        fetchCurrentUser().then(() => {
            document.getElementById('loginScreen').classList.add('hidden');
            document.getElementById('app').classList.remove('hidden');
            loadDocuments();
        }).catch(() => {
            // Token invalid, clear it
            clearAuthToken();
        });
    }
}

// ========== UTILITY FUNCTIONS ==========

function showNotification(message, type = 'info') {
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusBadge(status, processingCompleted) {
    if (!processingCompleted) {
        return '<span class="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">Processing</span>';
    }
    
    switch (status) {
        case 'success':
            return '<span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">Completed</span>';
        case 'error':
            return '<span class="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">Error</span>';
        default:
            return '<span class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">Unknown</span>';
    }
}

// ========== API FUNCTIONS WITH AUTH ==========

async function apiCall(endpoint, options = {}) {
    try {
        const token = getAuthToken();
        
        if (!token && !endpoint.includes('/login') && !endpoint.includes('/register')) {
            throw new Error('Not authenticated');
        }
        
        const headers = {
            ...options.headers
        };
        
        // Add auth token if available
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Add Content-Type for JSON requests
        if (options.body && typeof options.body === 'string') {
            headers['Content-Type'] = 'application/json';
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });
        
        // Handle 401 - token expired or invalid
        if (response.status === 401) {
            clearAuthToken();
            document.getElementById('app').classList.add('hidden');
            document.getElementById('loginScreen').classList.remove('hidden');
            showNotification('Session expired. Please login again.', 'warning');
            throw new Error('Authentication expired');
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function loadDocuments() {
    try {
        const statementId = document.getElementById('statementIdFilter').value;
        
        let url = '/documents/';
        const params = new URLSearchParams();
        if (statementId) params.append('statement_id', statementId);
        if (params.toString()) url += '?' + params.toString();
        
        documents = await apiCall(url);
        updateDocumentsTable();
        updateDashboardStats();
    } catch (error) {
        showNotification(`Failed to load documents: ${error.message}`, 'error');
    }
}

async function uploadDocument(formData) {
    try {
        const token = getAuthToken();
        
        const response = await fetch(`${API_BASE_URL}/upload-document/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (response.status === 401) {
            clearAuthToken();
            document.getElementById('app').classList.add('hidden');
            document.getElementById('loginScreen').classList.remove('hidden');
            showNotification('Session expired. Please login again.', 'warning');
            throw new Error('Authentication expired');
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        showNotification('Document uploaded successfully! Processing started in background.', 'success');
        hideUploadModal();
        loadDocuments();
        return result;
    } catch (error) {
        console.error('Upload error:', error);
        showNotification(`Upload failed: ${error.message}`, 'error');
        throw error;
    }
}

async function deleteDocument(documentId) {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
        await apiCall(`/documents/${documentId}`, { method: 'DELETE' });
        showNotification('Document deleted successfully', 'success');
        loadDocuments();
    } catch (error) {
        showNotification(`Failed to delete document: ${error.message}`, 'error');
    }
}

async function extractText(documentId) {
    try {
        const result = await apiCall(`/documents/${documentId}/extract-text`, { method: 'POST' });
        showNotification('Text extraction completed successfully', 'success');
        loadDocuments();
        return result;
    } catch (error) {
        showNotification(`Text extraction failed: ${error.message}`, 'error');
        throw error;
    }
}

async function getDocumentText(documentId) {
    try {
        return await apiCall(`/documents/${documentId}/text`);
    } catch (error) {
        showNotification(`Failed to get document text: ${error.message}`, 'error');
        throw error;
    }
}

async function getTransactions(statementId) {
    try {
        return await apiCall(`/statements/${statementId}/transactions`);
    } catch (error) {
        showNotification(`Failed to get transactions: ${error.message}`, 'error');
        throw error;
    }
}

async function extractTransactions(statementId) {
    try {
        const result = await apiCall(`/statements/${statementId}/extract-transactions`, { method: 'POST' });
        showNotification('Transaction extraction started in background', 'info');
        return result;
    } catch (error) {
        showNotification(`Failed to start transaction extraction: ${error.message}`, 'error');
        throw error;
    }
}

async function getTransactionSummary(statementId) {
    try {
        return await apiCall(`/statements/${statementId}/transactions/summary`);
    } catch (error) {
        showNotification(`Failed to get transaction summary: ${error.message}`, 'error');
        throw error;
    }
}

async function deleteTransaction(transactionId) {
    if (!confirm('Are you sure you want to delete this transaction?')) return;
    
    try {
        await apiCall(`/transactions/${transactionId}`, { method: 'DELETE' });
        showNotification('Transaction deleted successfully', 'success');
        return true;
    } catch (error) {
        showNotification(`Failed to delete transaction: ${error.message}`, 'error');
        return false;
    }
}

// ========== UI UPDATE FUNCTIONS ==========

function updateDocumentsTable() {
    const tbody = document.getElementById('documentsTableBody');
    tbody.innerHTML = '';
    
    if (documents.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                    No documents found
                </td>
            </tr>
        `;
        return;
    }
    
    documents.forEach(doc => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        
        const status = doc.text_processing_completed ? 
            (doc.poppler_extraction_success || doc.ocr_extraction_success ? 'success' : 'error') : 
            'processing';
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <i class="fas fa-file-pdf text-red-500 mr-3"></i>
                    <div>
                        <div class="text-sm font-medium text-gray-900">${doc.original_filename}</div>
                        <div class="text-sm text-gray-500">${formatFileSize(doc.file_size)}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${doc.statement_id}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                ${getStatusBadge(status, doc.text_processing_completed)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${formatDate(doc.upload_date)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <div class="flex space-x-2">
                    <button onclick="viewDocument(${doc.id})" class="text-blue-600 hover:text-blue-900" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button onclick="viewTransactions('${doc.statement_id}')" class="text-green-600 hover:text-green-900" title="View Transactions">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                    <button onclick="deleteDocument(${doc.id})" class="text-red-600 hover:text-red-900" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

function updateDashboardStats() {
    const total = documents.length;
    const processed = documents.filter(d => d.text_processing_completed).length;
    const processing = documents.filter(d => !d.text_processing_completed).length;
    
    // Calculate total transactions (this would need to be fetched separately for accuracy)
    const totalTransactions = documents.length * 10; // Placeholder
    
    document.getElementById('totalDocuments').textContent = total;
    document.getElementById('processedDocuments').textContent = processed;
    document.getElementById('processingDocuments').textContent = processing;
    document.getElementById('totalTransactions').textContent = totalTransactions;
}

// ========== MODAL FUNCTIONS ==========

function showUploadModal() {
    document.getElementById('uploadModal').classList.remove('hidden');
}

function hideUploadModal() {
    document.getElementById('uploadModal').classList.add('hidden');
    document.getElementById('uploadForm').reset();
}

function showDocumentModal() {
    document.getElementById('documentModal').classList.remove('hidden');
}

function hideDocumentModal() {
    document.getElementById('documentModal').classList.add('hidden');
}

function showTransactionModal() {
    document.getElementById('transactionModal').classList.remove('hidden');
}

function hideTransactionModal() {
    document.getElementById('transactionModal').classList.add('hidden');
}

// ========== DOCUMENT VIEW FUNCTIONS ==========

async function viewDocument(documentId) {
    try {
        const doc = documents.find(d => d.id === documentId);
        if (!doc) {
            showNotification('Document not found', 'error');
            return;
        }
        
        currentDocument = doc;
        
        // Get document text
        let textData = null;
        try {
            textData = await getDocumentText(documentId);
        } catch (error) {
            console.log('Could not fetch document text:', error);
        }
        
        const content = document.getElementById('documentModalContent');
        content.innerHTML = `
            <div class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-gray-900 mb-3">Document Information</h4>
                        <div class="space-y-2 text-sm">
                            <div><span class="font-medium">ID:</span> ${doc.id}</div>
                            <div><span class="font-medium">Statement ID:</span> ${doc.statement_id}</div>
                            <div><span class="font-medium">Filename:</span> ${doc.original_filename}</div>
                            <div><span class="font-medium">File Size:</span> ${formatFileSize(doc.file_size)}</div>
                            <div><span class="font-medium">Upload Date:</span> ${formatDate(doc.upload_date)}</div>
                        </div>
                    </div>
                    
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-gray-900 mb-3">Processing Status</h4>
                        <div class="space-y-2 text-sm">
                            <div><span class="font-medium">Text Processing:</span> ${doc.text_processing_completed ? 'Completed' : 'In Progress'}</div>
                            <div><span class="font-medium">Poppler Success:</span> ${doc.poppler_extraction_success ? 'Yes' : 'No'}</div>
                            <div><span class="font-medium">OCR Success:</span> ${doc.ocr_extraction_success ? 'Yes' : 'No'}</div>
                            ${doc.poppler_word_count ? `<div><span class="font-medium">Poppler Words:</span> ${doc.poppler_word_count}</div>` : ''}
                            ${doc.ocr_word_count ? `<div><span class="font-medium">OCR Words:</span> ${doc.ocr_word_count}</div>` : ''}
                            ${doc.ocr_confidence ? `<div><span class="font-medium">OCR Confidence:</span> ${doc.ocr_confidence}%</div>` : ''}
                        </div>
                    </div>
                </div>
                
                ${textData ? `
                <div class="space-y-4">
                    <h4 class="font-semibold text-gray-900">Extracted Text</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        ${textData.poppler.success ? `
                        <div class="bg-white border rounded-lg p-4">
                            <h5 class="font-medium text-gray-900 mb-2">Poppler Extraction</h5>
                            <div class="text-xs text-gray-600 mb-2">
                                Words: ${textData.poppler.word_count} | Pages: ${textData.poppler.pages}
                            </div>
                            <div class="text-sm text-gray-700 max-h-40 overflow-y-auto">
                                ${textData.poppler.text.substring(0, 500)}${textData.poppler.text.length > 500 ? '...' : ''}
                            </div>
                        </div>
                        ` : ''}
                        
                        ${textData.ocr.success ? `
                        <div class="bg-white border rounded-lg p-4">
                            <h5 class="font-medium text-gray-900 mb-2">OCR Extraction</h5>
                            <div class="text-xs text-gray-600 mb-2">
                                Words: ${textData.ocr.word_count} | Pages: ${textData.ocr.pages} | Confidence: ${textData.ocr.confidence}%
                            </div>
                            <div class="text-sm text-gray-700 max-h-40 overflow-y-auto">
                                ${textData.ocr.text.substring(0, 500)}${textData.ocr.text.length > 500 ? '...' : ''}
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
                ` : ''}
                
                <div class="flex space-x-3">
                    <button onclick="extractText(${doc.id})" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                        <i class="fas fa-sync-alt mr-2"></i>Re-extract Text
                    </button>
                    <button onclick="viewTransactions('${doc.statement_id}')" class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                        <i class="fas fa-exchange-alt mr-2"></i>View Transactions
                    </button>
                </div>
            </div>
        `;
        
        showDocumentModal();
    } catch (error) {
        showNotification(`Failed to load document details: ${error.message}`, 'error');
    }
}

// ========== TRANSACTION VIEW FUNCTIONS ==========

async function viewTransactions(statementId) {
    try {
        const [transactions, summary] = await Promise.all([
            getTransactions(statementId),
            getTransactionSummary(statementId)
        ]);
        
        const content = document.getElementById('transactionModalContent');
        
        let transactionsHtml = '';
        if (transactions.length > 0) {
            transactionsHtml = `
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            ${transactions.map(t => `
                                <tr>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        ${t.transaction_date ? formatDate(t.transaction_date) : '-'}
                                    </td>
                                    <td class="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                                        ${t.description || '-'}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                                        <span class="${t.amount && t.amount > 0 ? 'text-green-600' : 'text-red-600'}">
                                            ${t.amount ? `${Math.abs(parseFloat(t.amount)).toFixed(2)}` : '-'}
                                        </span>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        ${t.category || '-'}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        ${getStatusBadge(t.processing_completed ? 'success' : 'error', t.processing_completed)}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <button onclick="deleteTransactionAndRefresh(${t.id}, '${statementId}')" class="text-red-600 hover:text-red-900">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            transactionsHtml = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-exchange-alt text-4xl mb-4"></i>
                    <p>No transactions found for this statement.</p>
                </div>
            `;
        }
        
        content.innerHTML = `
            <div class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="bg-blue-50 p-4 rounded-lg">
                        <div class="text-2xl font-bold text-blue-600">${summary.total_transactions}</div>
                        <div class="text-sm text-blue-600">Total Transactions</div>
                    </div>
                    <div class="bg-green-50 p-4 rounded-lg">
                        <div class="text-2xl font-bold text-green-600">${summary.total_credits.toFixed(2)}</div>
                        <div class="text-sm text-green-600">Total Credits</div>
                    </div>
                    <div class="bg-red-50 p-4 rounded-lg">
                        <div class="text-2xl font-bold text-red-600">${summary.total_debits.toFixed(2)}</div>
                        <div class="text-sm text-red-600">Total Debits</div>
                    </div>
                    <div class="bg-purple-50 p-4 rounded-lg">
                        <div class="text-2xl font-bold text-purple-600">${summary.net_amount.toFixed(2)}</div>
                        <div class="text-sm text-purple-600">Net Amount</div>
                    </div>
                </div>
                
                <div class="flex space-x-3">
                    <button onclick="extractTransactions('${statementId}')" class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                        <i class="fas fa-sync-alt mr-2"></i>Extract Transactions
                    </button>
                    <button onclick="deleteAllTransactions('${statementId}')" class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
                        <i class="fas fa-trash mr-2"></i>Delete All
                    </button>
                </div>
                
                <div>
                    <h4 class="font-semibold text-gray-900 mb-4">Transactions</h4>
                    ${transactionsHtml}
                </div>
            </div>
        `;
        
        hideDocumentModal();
        showTransactionModal();
    } catch (error) {
        showNotification(`Failed to load transactions: ${error.message}`, 'error');
    }
}

async function deleteTransactionAndRefresh(transactionId, statementId) {
    const success = await deleteTransaction(transactionId);
    if (success) {
        viewTransactions(statementId); // Refresh the view
    }
}

async function deleteAllTransactions(statementId) {
    if (!confirm('Are you sure you want to delete all transactions for this statement?')) return;
    
    try {
        await apiCall(`/statements/${statementId}/transactions`, { method: 'DELETE' });
        showNotification('All transactions deleted successfully', 'success');
        viewTransactions(statementId); // Refresh the view
    } catch (error) {
        showNotification(`Failed to delete transactions: ${error.message}`, 'error');
    }
}

// ========== EVENT LISTENERS ==========

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already logged in
    checkAuthOnLoad();
    
    // Upload form handler
    document.getElementById('uploadForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const statementId = document.getElementById('uploadStatementId').value;
        const fileInput = document.getElementById('uploadFile');
        
        if (!fileInput.files[0]) {
            showNotification('Please select a PDF file', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('statement_id', statementId);
        formData.append('pdf_file', fileInput.files[0]);
        
        try {
            await uploadDocument(formData);
        } catch (error) {
            console.error('Upload error:', error);
        }
    });
    
    // Filter input - allow Enter key to trigger search
    document.getElementById('statementIdFilter').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') loadDocuments();
    });
    
    // Modal backdrop click handlers
    document.getElementById('uploadModal').addEventListener('click', function(e) {
        if (e.target === this) hideUploadModal();
    });
    
    document.getElementById('documentModal').addEventListener('click', function(e) {
        if (e.target === this) hideDocumentModal();
    });
    
    document.getElementById('transactionModal').addEventListener('click', function(e) {
        if (e.target === this) hideTransactionModal();
    });
});

// Auto-refresh documents every 30 seconds to check for processing updates
setInterval(() => {
    if (isAuthenticated() && documents.some(d => !d.text_processing_completed)) {
        loadDocuments();
    }
}, 30000);