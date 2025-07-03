# POR Upload System

A Flask-based web application for processing Purchase Order Requests (POR) from Excel files.

## 🚀 Features

- **Excel File Processing**: Upload and process Excel files (.xlsx, .xls)
- **Drag & Drop Interface**: Modern, intuitive file upload interface
- **Data Extraction**: Automatically extract POR data from Excel files
- **Database Storage**: Store processed data in SQLite database
- **Search & Pagination**: View records with search and pagination
- **Batch Management**: Manage PO number sequences
- **Error Handling**: Comprehensive error handling and user feedback

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd por-upload-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and go to `http://localhost:5000`

## 📁 Project Structure

```
por-upload-system/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── utils.py              # Utility functions
├── po_counter.py         # PO number management
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── static/
│   ├── style.css        # CSS styles
│   └── uploads/         # Uploaded files
├── templates/
│   ├── upload.html      # Upload page
│   ├── view.html        # Records view page
│   ├── change_batch.html # Batch settings page
│   ├── 404.html         # 404 error page
│   └── 500.html         # 500 error page
└── por.db               # SQLite database
```

## 🔧 Configuration

The application can be configured using environment variables:

- `FLASK_DEBUG`: Enable/disable debug mode (default: True)
- `DATABASE_URL`: Database connection string (default: sqlite:///por.db)
- `SECRET_KEY`: Flask secret key for sessions
- `LOG_LEVEL`: Logging level (default: INFO)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)

## 📊 Database Schema

The application uses a single table `por` with the following structure:

- `id`: Primary key
- `po_number`: Purchase Order number (unique)
- `requestor_name`: Name of the requestor
- `date_order_raised`: Date when order was raised
- `filename`: Original uploaded filename
- `job_contract_no`: Job/Contract number
- `op_no`: Operation number
- `description`: Item description
- `quantity`: Item quantity
- `price_each`: Price per unit
- `line_total`: Line item total
- `order_total`: Total order amount
- `data_summary`: Summary of extracted data
- `created_at`: Record creation timestamp

## 🎨 UI Features

- **Responsive Design**: Works on desktop and mobile devices
- **Harbour Theme**: Beautiful nautical design
- **Drag & Drop**: Intuitive file upload interface
- **Real-time Feedback**: Immediate user feedback for actions
- **Pagination**: Efficient record browsing
- **Search**: Quick record lookup

## 🔍 Usage

1. **Upload Files**: Drag and drop Excel files or click to browse
2. **View Records**: Browse uploaded POR records with search and pagination
3. **Manage Batch**: Update starting PO numbers for new uploads
4. **Search**: Use the search function to find specific records

## 🚨 Error Handling

The application includes comprehensive error handling:

- File validation (type, size)
- Database error recovery
- User-friendly error messages
- Logging for debugging

## 🔒 Security Features

- File type validation
- File size limits
- Secure filename handling
- SQL injection prevention
- XSS protection

## 📈 Performance Optimizations

- Database indexing for fast searches
- Efficient pagination
- Optimized file processing
- Memory-efficient Excel reading
- Thread-safe PO counter

## 🧪 Testing

To test the application:

1. Start the application
2. Upload sample Excel files
3. Verify data extraction
4. Test search and pagination
5. Check error handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review error logs

## 🔄 Version History

- **v2.0.0**: Complete rewrite with improved architecture
- **v1.0.0**: Initial release 