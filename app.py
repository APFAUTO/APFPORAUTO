"""
POR Upload Application
A Flask-based system for processing Purchase Order Requests (POR) from Excel files.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, List

from flask import Flask, request, render_template, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from models import POR, session, PORFile
from utils import read_ws, find_vertical, get_order_total, extract_line_items, to_float, stringify
from po_counter import increment_po, current_po, po_counter_path

# Configuration
UPLOAD_FOLDER = "static/uploads"

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'msg', 'eml'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
RECORDS_PER_PAGE = 10

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=MAX_FILE_SIZE,
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    allowed_extensions = {'xlsx', 'xls', 'msg', 'eml', 'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def capitalize_text(value):
    """Capitalize text values, handling None and non-string values."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.upper()
    return value


def process_uploaded_file(file) -> Tuple[bool, str, Optional[dict], Optional[list]]:
    """
    Process uploaded Excel file or email file and extract POR data and line items.
    Returns:
        Tuple of (success, message, data_dict, line_items)
    """
    try:
        # Validate file
        if not file or file.filename == '':
            return False, "No file selected", None, None
        
        if not allowed_file(file.filename):
            return False, "Invalid file type. Please upload Excel files (.xlsx, .xls) or email files (.msg, .eml)", None, None
        
        # Check file extension
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension in ['msg', 'eml']:
            return process_email_file(file)
        else:
            return process_excel_file(file)
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return False, f"❌ Error processing file: {str(e)}", None, None


def process_excel_file(file) -> Tuple[bool, str, Optional[dict], Optional[list]]:
    """Process Excel file and extract POR data."""
    try:
        # Read worksheet
        rows, ws = read_ws(file)
        if not rows:
            return False, "Empty or invalid Excel file", None, None
        
        # Extract data
        requestor = capitalize_text(find_vertical(rows, 'Requestor Name') or 'Unknown')
        date_order = find_vertical(rows, 'Date Order Raised') or datetime.now().strftime('%d/%m/%Y')
        
        # Extract ship/project name from B2 (based on parsing map)
        ship_project_name = capitalize_text(ws.cell(2, 2).value if ws.cell(2, 2).value else 'Unknown')
        
        # Extract supplier from D2
        supplier = capitalize_text(ws.cell(2, 4).value if ws.cell(2, 4).value else '')
        
        # Extract specification/standards from A29
        specification_standards = capitalize_text(ws.cell(29, 1).value if ws.cell(29, 1).value else '')
        
        # Extract supplier contact details from C33-C36
        supplier_contact_name = capitalize_text(ws.cell(33, 3).value if ws.cell(33, 3).value else '')
        supplier_contact_email = ws.cell(34, 3).value if ws.cell(34, 3).value else ''  # Keep email in original case
        quote_ref = capitalize_text(ws.cell(35, 3).value if ws.cell(35, 3).value else '')
        quote_date = stringify(ws.cell(36, 3).value) if ws.cell(36, 3).value else ''  # Format as dd/mm/yyyy
        
        # Generate PO number and filename
        po_number = increment_po()
        safe_filename = secure_filename(f'PO_{po_number}_{date_order}_{requestor.replace(" ", "_")}.xlsx')
        
        # Save file locally
        try:
            file.seek(0)
            file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
            file.save(file_path)
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return False, f"❌ Error saving file: {str(e)}", None, None
        
        # Extract line items
        header_row = next((i for i, r in enumerate(ws.iter_rows(values_only=True), 1) 
                          if any(isinstance(c, str) and 'MATERIAL' in c.upper() for c in r)), None)
        
        items = extract_line_items(ws, header_row) if header_row else []
        
        # Capitalize text fields in line items
        for item in items:
            item['job'] = capitalize_text(item.get('job'))
            item['op'] = capitalize_text(item.get('op'))
            item['desc'] = capitalize_text(item.get('desc'))
        
        first_item = items[0] if items else {}
        
        # Calculate totals
        order_total = to_float(get_order_total(ws))
        
        # Prepare data
        data = {
            'po_number': po_number,
            'requestor_name': requestor,
            'date_order_raised': date_order,
            'ship_project_name': ship_project_name,
            'supplier': supplier,
            'filename': safe_filename,
            'job_contract_no': first_item.get('job'),
            'op_no': first_item.get('op'),
            'description': first_item.get('desc'),
            'quantity': first_item.get('qty'),
            'price_each': to_float(first_item.get('price')),
            'line_total': to_float(first_item.get('ltot')),
            'order_total': order_total,
            'specification_standards': specification_standards,
            'supplier_contact_name': supplier_contact_name,
            'supplier_contact_email': supplier_contact_email,
            'quote_ref': quote_ref,
            'quote_date': quote_date,
            'data_summary': "\n".join(str(r) for r in rows[:10]),
            'created_at': datetime.now(timezone.utc)
        }
        
        return True, f"✅ Successfully processed PO #{po_number}", data, items
        
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        return False, f"❌ Error processing Excel file: {str(e)}", None, None


def process_email_file(file) -> Tuple[bool, str, Optional[dict], Optional[list]]:
    """Process email file (.msg or .eml) and extract POR data."""
    try:
        import email
        from email import policy
        
        # Generate PO number and filename
        po_number = increment_po()
        date_order = datetime.now().strftime('%d/%m/%Y')
        
        # Save file locally
        original_filename = secure_filename(file.filename)
        safe_filename = secure_filename(f'PO_{po_number}_{date_order}_EMAIL_{original_filename}')
        
        try:
            file.seek(0)
            file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
            file.save(file_path)
        except Exception as e:
            logger.error(f"Error saving email file: {str(e)}")
            return False, f"❌ Error saving email file: {str(e)}", None, None
        
        # Parse email content
        file.seek(0)
        if file.filename.lower().endswith('.msg'):
            # For .msg files, we'll extract basic info
            # Note: Full .msg parsing requires additional libraries like extract-msg
            email_data = {
                'subject': 'Email Subject (MSG file)',
                'from': 'Unknown Sender',
                'date': date_order,
                'body': 'MSG file content - manual processing required'
            }
        else:
            # Parse .eml file
            msg = email.message_from_file(file, policy=policy.default)
            
            # Extract email headers
            subject = msg.get('subject', 'No Subject')
            from_header = msg.get('from', 'Unknown Sender')
            date_header = msg.get('date', '')
            
            # Extract email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_content()
                        break
            else:
                body = msg.get_content()
            
            email_data = {
                'subject': subject,
                'from': from_header,
                'date': date_header,
                'body': body
            }
        
        # Extract basic POR data from email
        # This is a simplified extraction - you may need to customize based on your email format
        requestor = capitalize_text(email_data['from'].split('<')[0].strip() if '<' in email_data['from'] else email_data['from'])
        
        # Try to extract supplier from subject or body
        supplier = 'Unknown'
        if 'supplier' in email_data['subject'].lower():
            supplier = capitalize_text(email_data['subject'])
        
        # Prepare data
        data = {
            'po_number': po_number,
            'requestor_name': requestor,
            'date_order_raised': date_order,
            'ship_project_name': 'Email Upload',
            'supplier': supplier,
            'filename': safe_filename,
            'job_contract_no': '',
            'op_no': '',
            'description': email_data['subject'][:100],  # Use subject as description
            'quantity': 1,
            'price_each': 0.0,
            'line_total': 0.0,
            'order_total': 0.0,
            'specification_standards': '',
            'supplier_contact_name': '',
            'supplier_contact_email': email_data['from'],
            'quote_ref': '',
            'quote_date': '',
            'data_summary': f"Email Subject: {email_data['subject']}\nFrom: {email_data['from']}\nDate: {email_data['date']}\n\nBody Preview:\n{email_data['body'][:500]}...",
            'created_at': datetime.now(timezone.utc)
        }
        
        # Create a simple line item from email data
        items = [{
            'job': '',
            'op': '',
            'desc': email_data['subject'],
            'qty': 1,
            'price': 0.0,
            'ltot': 0.0
        }]
        
        return True, f"✅ Successfully processed Email PO #{po_number}", data, items
        
    except Exception as e:
        logger.error(f"Error processing email file: {str(e)}")
        return False, f"❌ Error processing email file: {str(e)}", None, None


def save_por_to_database(data: dict, line_items: list = None) -> bool:
    """Save POR data and its line items to database."""
    try:
        from models import get_session, LineItem
        db_session = get_session()
        por = POR(**data)
        db_session.add(por)
        db_session.flush()  # Get POR id
        # Save line items if provided
        if line_items:
            for item in line_items:
                line_item = LineItem(
                    por_id=por.id,
                    job_contract_no=item.get('job'),
                    op_no=item.get('op'),
                    description=item.get('desc'),
                    quantity=item.get('qty'),
                    price_each=to_float(item.get('price')),
                    line_total=to_float(item.get('ltot'))
                )
                db_session.add(line_item)
        db_session.commit()
        db_session.close()
        return True
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        try:
            db_session.rollback()
            db_session.close()
        except:
            pass
        return False


def get_paginated_records(page: int, search_query: str = '') -> Tuple[List[POR], dict]:
    """
    Get paginated POR records with optional search.
    Also attaches all line items to each POR record.
    """
    try:
        from models import get_session, LineItem
        db_session = get_session()
        query = db_session.query(POR).order_by(POR.id.desc())
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                POR.po_number.like(search_term) |
                POR.requestor_name.like(search_term) |
                POR.job_contract_no.like(search_term) |
                POR.op_no.like(search_term) |
                POR.description.like(search_term)
            )
        total_records = query.count()
        total_pages = (total_records + RECORDS_PER_PAGE - 1) // RECORDS_PER_PAGE
        offset = (page - 1) * RECORDS_PER_PAGE
        records = query.offset(offset).limit(RECORDS_PER_PAGE).all()
        # Attach line items to each record
        for record in records:
            record.file_count = len(record.attached_files)
            record.files = record.attached_files
            # Attach all line items
            record.line_items = db_session.query(LineItem).filter_by(por_id=record.id).all()
        pagination_info = {
            'current_page': page,
            'total_pages': total_pages,
            'total_records': total_records,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'records_per_page': RECORDS_PER_PAGE
        }
        db_session.close()
        return records, pagination_info
    except Exception as e:
        logger.error(f"Error fetching records: {str(e)}")
        try:
            db_session.close()
        except:
            pass
        return [], {}


@app.route('/test')
def test():
    return "App is working! Database connection: " + str(session is not None)

@app.route('/', methods=['GET', 'POST'])
def upload():
    """Handle file upload and processing."""
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            success, message, data, line_items = process_uploaded_file(file)
            if success and data:
                if save_por_to_database(data, line_items):
                    flash(message, 'success')
                else:
                    flash("❌ Error saving to database", 'error')
            else:
                flash(message, 'error')
        except RequestEntityTooLarge:
            flash("❌ File too large. Maximum size is 16MB.", 'error')
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            flash(f"❌ Unexpected error: {str(e)}", 'error')
    return render_template("upload.html", current_po=current_po)


@app.route('/view')
def view():
    """Display paginated POR records with search."""
    try:
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('q', '').strip()
        
        # Validate page number
        if page < 1:
            page = 1
        
        records, pagination = get_paginated_records(page, search_query)
        
        return render_template("view.html", 
                             pors=records, 
                             current_po=current_po,
                             **pagination)
                             
    except Exception as e:
        logger.error(f"View error: {str(e)}")
        flash(f"❌ Error loading records: {str(e)}", 'error')
        # Provide default pagination values when there's an error
        default_pagination = {
            'current_page': 1,
            'total_pages': 0,
            'total_records': 0,
            'has_prev': False,
            'has_next': False,
            'records_per_page': RECORDS_PER_PAGE
        }
        return render_template("view.html", pors=[], current_po=current_po, **default_pagination)


@app.route('/change-batch', methods=['GET', 'POST'])
def change_batch():
    """Handle batch number updates."""
    if request.method == 'POST':
        try:
            new_po = request.form.get('po_number', '').strip()
            
            if not new_po:
                flash("❌ Please enter a PO number", 'error')
            else:
                try:
                    new_po = int(new_po)
                    if new_po < 1:
                        flash("❌ PO number must be greater than 0", 'error')
                    else:
                        # Update global variable and file
                        global current_po
                        current_po = new_po
                        with open(po_counter_path, 'w') as f:
                            f.write(str(new_po))
                        flash(f"✅ Starting PO set to {new_po}", 'success')
                        
                except ValueError:
                    flash("❌ Invalid PO number format", 'error')
                    
        except Exception as e:
            logger.error(f"Batch change error: {str(e)}")
            flash(f"❌ Error updating batch number: {str(e)}", 'error')
    
    return render_template("change_batch.html")


@app.route('/attach-files/<int:por_id>', methods=['GET', 'POST'])
def attach_files(por_id):
    """Handle file attachments for POR records."""
    try:
        # Get the POR record
        from models import get_session
        db_session = get_session()
        por = db_session.query(POR).filter_by(id=por_id).first()
        
        if not por:
            flash("❌ POR record not found", 'error')
            return redirect(url_for('view'))
        
        if request.method == 'POST':
            try:
                files = request.files.getlist('files')
                file_types = request.form.getlist('file_types')
                descriptions = request.form.getlist('descriptions')
                
                logger.info(f"Received {len(files)} files for upload")
                logger.info(f"File types: {file_types}")
                logger.info(f"Descriptions: {descriptions}")
                
                uploaded_count = 0
                for i, file in enumerate(files):
                    if file and file.filename:
                        logger.info(f"Processing file: {file.filename}")
                        # Validate file
                        if not allowed_file(file.filename):
                            logger.warning(f"File {file.filename} not allowed")
                            continue
                        
                        # Get file info
                        file_type = file_types[i] if i < len(file_types) else 'other'
                        description = descriptions[i] if i < len(descriptions) else ''
                        
                        # Generate safe filename
                        original_filename = file.filename
                        file_extension = os.path.splitext(original_filename)[1]
                        safe_filename = f"POR_{por.po_number}_{file_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}{file_extension}"
                        
                        # Save file
                        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
                        file.save(file_path)
                        logger.info(f"File saved to: {file_path}")
                        file_size = os.path.getsize(file_path)
                        logger.info(f"File size: {file_size} bytes")
                        
                        # Create PORFile record
                        por_file = PORFile(
                            por_id=por_id,
                            original_filename=original_filename,
                            stored_filename=safe_filename,
                            file_type=file_type,
                            file_size=file_size,
                            mime_type=file.content_type or 'application/octet-stream',
                            description=description
                        )
                        
                        db_session.add(por_file)
                        uploaded_count += 1
                        logger.info(f"Added file to database: {por_file.original_filename}")
                
                if uploaded_count > 0:
                    db_session.commit()
                    logger.info(f"Committed {uploaded_count} files to database")
                    flash(f"✅ Successfully uploaded {uploaded_count} file(s)", 'success')
                else:
                    logger.warning("No files were uploaded")
                    flash("❌ No valid files were uploaded", 'error')
                    
            except Exception as e:
                db_session.rollback()
                logger.error(f"File upload error: {str(e)}")
                flash(f"❌ Error uploading files: {str(e)}", 'error')
            finally:
                db_session.close()
        
        # Get existing attachments
        db_session = get_session()
        por = db_session.query(POR).filter_by(id=por_id).first()
        attached_files = por.attached_files if por else []
        db_session.close()
        
        return render_template("attach_files.html", por=por, attached_files=attached_files)
        
    except Exception as e:
        logger.error(f"Attach files error: {str(e)}")
        flash(f"❌ Error: {str(e)}", 'error')
        return redirect(url_for('view'))


@app.route('/download-file/<int:file_id>')
def download_file(file_id):
    """Download an attached file."""
    try:
        from models import get_session
        db_session = get_session()
        por_file = db_session.query(PORFile).filter_by(id=file_id).first()
        
        if not por_file:
            flash("❌ File not found", 'error')
            return redirect(url_for('view'))
        

        
        file_path = os.path.join(UPLOAD_FOLDER, por_file.stored_filename)
        
        if not os.path.exists(file_path):
            flash("❌ File not found on server", 'error')
            return redirect(url_for('view'))
        
        db_session.close()
        
        return send_file(file_path, as_attachment=True, download_name=por_file.original_filename)
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        flash(f"❌ Error downloading file: {str(e)}", 'error')
        return redirect(url_for('view'))


@app.route('/delete-file/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    """Delete an attached file."""
    try:
        from models import get_session
        db_session = get_session()
        por_file = db_session.query(PORFile).filter_by(id=file_id).first()
        
        if not por_file:
            flash("❌ File not found", 'error')
            return redirect(url_for('view'))
        
        # Delete physical file
        file_path = os.path.join(UPLOAD_FOLDER, por_file.stored_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete database record
        db_session.delete(por_file)
        db_session.commit()
        db_session.close()
        
        flash("✅ File deleted successfully", 'success')
        
    except Exception as e:
        logger.error(f"Delete file error: {str(e)}")
        flash(f"❌ Error deleting file: {str(e)}", 'error')
    
    return redirect(request.referrer or url_for('view'))


@app.route('/update_por_field', methods=['POST'])
def update_por_field():
    """Update a field in a POR record."""
    try:
        from flask import jsonify
        from models import get_session
        
        data = request.get_json()
        por_id = data.get('por_id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([por_id, field, value is not None]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Validate field name to prevent SQL injection
        allowed_fields = {
            'requestor_name', 'ship_project_name', 'supplier', 'job_contract_no', 
            'op_no', 'order_total', 'quote_ref', 'quote_date'
        }
        
        if field not in allowed_fields:
            return jsonify({'success': False, 'error': 'Invalid field name'})
        
        # Convert value types
        if field == 'order_total':
            try:
                value = float(value) if value else 0.0
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid number format'})
        
        db_session = get_session()
        por = db_session.query(POR).filter(POR.id == por_id).first()
        
        if not por:
            return jsonify({'success': False, 'error': 'POR not found'})
        
        # Update the field
        setattr(por, field, value)
        db_session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating POR field: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if 'db_session' in locals():
            db_session.close()


@app.route('/update_line_item_field', methods=['POST'])
def update_line_item_field():
    """Update a field in a line item record."""
    try:
        from flask import jsonify
        from models import get_session, LineItem
        
        data = request.get_json()
        line_item_id = data.get('line_item_id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([line_item_id, field, value is not None]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Validate field name to prevent SQL injection
        allowed_fields = {
            'job_contract_no', 'op_no', 'description', 'quantity', 'price_each', 'line_total'
        }
        
        if field not in allowed_fields:
            return jsonify({'success': False, 'error': 'Invalid field name'})
        
        # Convert value types
        if field in ['quantity']:
            try:
                value = int(value) if value else 0
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid number format'})
        elif field in ['price_each', 'line_total']:
            try:
                value = float(value) if value else 0.0
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid number format'})
        
        db_session = get_session()
        line_item = db_session.query(LineItem).filter(LineItem.id == line_item_id).first()
        
        if not line_item:
            return jsonify({'success': False, 'error': 'Line item not found'})
        
        # Update the field
        setattr(line_item, field, value)
        db_session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating line item field: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if 'db_session' in locals():
            db_session.close()


@app.route('/attach_email/<int:por_id>', methods=['POST'])
def attach_email_to_por(por_id):
    """Attach an email file to a specific POR record."""
    try:
        from flask import jsonify
        from models import get_session
        
        # Get the POR record
        db_session = get_session()
        por = db_session.query(POR).filter(POR.id == por_id).first()
        
        if not por:
            return jsonify({'success': False, 'error': 'POR not found'})
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Only .msg and .eml files are allowed'})
        
        # Check file extension
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_extension not in ['msg', 'eml']:
            return jsonify({'success': False, 'error': 'Only email files (.msg, .eml) are allowed'})
        
        # Generate safe filename with PO number
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1]
        safe_filename = f"POR_{por.po_number}_EMAIL_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}{file_extension}"
        
        # Save file
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Parse email content for description
        file.seek(0)
        email_description = "Email attachment"
        
        try:
            import email
            from email import policy
            
            if file_extension == '.eml':
                msg = email.message_from_file(file, policy=policy.default)
                subject = msg.get('subject', 'No Subject')
                from_header = msg.get('from', 'Unknown Sender')
                email_description = f"Email: {subject} (from {from_header})"
            else:
                email_description = f"Outlook Message: {original_filename}"
        except:
            email_description = f"Email: {original_filename}"
        
        # Create PORFile record
        por_file = PORFile(
            por_id=por_id,
            original_filename=original_filename,
            stored_filename=safe_filename,
            file_type='email',
            file_size=file_size,
            mime_type='message/rfc822' if file_extension == '.eml' else 'application/vnd.ms-outlook',
            description=email_description
        )
        
        db_session.add(por_file)
        db_session.commit()
        db_session.close()
        
        return jsonify({
            'success': True, 
            'message': f'Email attached to PO #{por.po_number}',
            'file_id': por_file.id,
            'filename': original_filename
        })
        
    except Exception as e:
        logger.error(f"Error attaching email: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if 'db_session' in locals():
            db_session.close()


@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
