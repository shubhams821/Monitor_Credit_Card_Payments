# Credit Monitor Frontend

A modern, responsive web interface for the Credit Monitor Document Processing System. This frontend provides a beautiful and intuitive way to interact with all the backend APIs for document upload, text extraction, and transaction processing.

## Features

### 🎯 Dashboard Overview
- **Real-time Statistics**: View total documents, processed documents, processing status, and transaction counts
- **Visual Cards**: Beautiful hover effects and color-coded status indicators
- **Auto-refresh**: Automatically updates processing status every 30 seconds

### 📄 Document Management
- **Upload Documents**: Drag-and-drop or click-to-upload PDF files with user and statement IDs
- **Document List**: View all documents in a clean, sortable table
- **Filtering**: Search documents by User ID or Statement ID
- **Document Details**: View comprehensive document information including:
  - File metadata (size, upload date, etc.)
  - Processing status (Poppler and OCR extraction results)
  - Extracted text preview (both Poppler and OCR methods)
  - Word counts, page counts, and confidence scores

### 💳 Transaction Management
- **Transaction View**: View all transactions for a specific statement
- **Transaction Summary**: See financial summaries including:
  - Total transactions count
  - Total credits and debits
  - Net amount
  - Category breakdown
- **Transaction Actions**: Delete individual transactions or all transactions for a statement
- **Manual Extraction**: Trigger transaction extraction manually

### 🔧 Advanced Features
- **Text Extraction**: Manually re-extract text from documents using both Poppler and OCR
- **Real-time Processing**: Background processing with status updates
- **Error Handling**: Comprehensive error messages and user notifications
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices

## Setup Instructions

### Prerequisites
1. Make sure the backend API is running on `http://localhost:8000`
2. Ensure CORS is properly configured on the backend (if needed)

### Installation
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Open `index.html` in your web browser:
   ```bash
   # On Windows
   start index.html
   
   # On macOS
   open index.html
   
   # On Linux
   xdg-open index.html
   ```

   Or simply double-click the `index.html` file in your file explorer.

### Alternative: Using a Local Server
For better development experience, you can serve the frontend using a local server:

```bash
# Using Python 3
python -m http.server 3000

# Using Node.js (if you have http-server installed)
npx http-server -p 3000

# Using PHP
php -S localhost:3000
```

Then open `http://localhost:3000` in your browser.

## API Integration

The frontend connects to the following backend endpoints:

### Document Endpoints
- `GET /documents/` - List all documents
- `POST /upload-document/` - Upload new document
- `GET /documents/{id}` - Get specific document
- `DELETE /documents/{id}` - Delete document
- `POST /documents/{id}/extract-text` - Extract text from document
- `GET /documents/{id}/text` - Get extracted text

### Transaction Endpoints
- `GET /statements/{statement_id}/transactions` - Get transactions for statement
- `POST /statements/{statement_id}/extract-transactions` - Extract transactions
- `GET /statements/{statement_id}/transactions/summary` - Get transaction summary
- `DELETE /transactions/{id}` - Delete specific transaction
- `DELETE /statements/{statement_id}/transactions` - Delete all transactions

## Usage Guide

### 1. Uploading Documents
1. Click the "Upload Document" button in the navigation bar
2. Fill in the User ID and Statement ID fields
3. Select a PDF file to upload
4. Click "Upload" to start the process
5. The document will be processed in the background

### 2. Viewing Documents
1. Documents are automatically loaded and displayed in the table
2. Use the filter fields to search by User ID or Statement ID
3. Click the eye icon to view detailed document information
4. Click the exchange icon to view transactions for that statement

### 3. Managing Transactions
1. Click the exchange icon on any document to view its transactions
2. View transaction summary statistics at the top
3. Use "Extract Transactions" to manually trigger extraction
4. Delete individual transactions or all transactions for a statement

### 4. Text Extraction
1. View document details to see extraction results
2. Use "Re-extract Text" to manually trigger text extraction
3. Compare Poppler and OCR extraction results
4. View confidence scores and word counts

## Technical Details

### Technologies Used
- **HTML5**: Semantic markup and structure
- **CSS3**: Modern styling with Tailwind CSS framework
- **JavaScript (ES6+)**: Modern JavaScript with async/await
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Font Awesome**: Icon library for beautiful icons
- **Inter Font**: Modern, readable typography

### Browser Support
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

### Responsive Design
- Mobile-first approach
- Responsive grid layouts
- Touch-friendly interface
- Optimized for all screen sizes

## Customization

### Changing API URL
To change the API endpoint, edit the `API_BASE_URL` constant in `app.js`:

```javascript
const API_BASE_URL = 'http://your-api-server:port';
```

### Styling Customization
The frontend uses Tailwind CSS classes. You can customize the appearance by:
1. Modifying the CSS classes in the HTML
2. Adding custom CSS in the `<style>` section
3. Replacing Tailwind with your preferred CSS framework

### Adding New Features
The modular JavaScript structure makes it easy to add new features:
1. Add new API functions in the "API Functions" section
2. Create corresponding UI update functions
3. Add event listeners for new interactions
4. Update the HTML structure as needed

## Troubleshooting

### Common Issues

1. **API Connection Error**
   - Ensure the backend server is running on the correct port
   - Check that CORS is properly configured
   - Verify the API_BASE_URL in app.js

2. **Upload Failures**
   - Check file size (max 10MB)
   - Ensure file is a valid PDF
   - Verify all required fields are filled

3. **Processing Not Updating**
   - The page auto-refreshes every 30 seconds
   - Manual refresh may be needed for immediate updates
   - Check browser console for error messages

4. **Modal Not Closing**
   - Click outside the modal or use the X button
   - Check for JavaScript errors in the console

### Debug Mode
Open the browser's developer tools (F12) to see:
- Network requests and responses
- JavaScript console logs
- Error messages and stack traces

## Contributing

To contribute to the frontend:
1. Follow the existing code structure and naming conventions
2. Test changes across different browsers
3. Ensure responsive design works on mobile devices
4. Add appropriate error handling for new features
5. Update this README for any new features or changes

## License

This frontend is part of the Credit Monitor system and follows the same license as the main project.
