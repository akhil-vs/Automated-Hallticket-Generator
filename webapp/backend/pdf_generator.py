"""
PDF generation module for hall tickets with 3 tickets per A4 page.
Refactored to use canvas-based drawing with reusable draw_ticket function.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
import io
import qrcode
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class HallTicketGenerator:
    """Generates hall tickets in PDF format with 3 tickets per A4 page."""
    
    # A4 dimensions in mm
    PAGE_WIDTH = 210 * mm
    PAGE_HEIGHT = 297 * mm
    
    # Ticket dimensions (3 per page vertically, with margins)
    TICKET_WIDTH = PAGE_WIDTH - 10 * mm  # Full width minus margins (200mm)
    TICKET_HEIGHT = (PAGE_HEIGHT - 10 * mm - 6 * mm) / 3  # ~93.7mm per ticket
    MARGIN = 5 * mm
    GAP = 3 * mm  # Gap between tickets
    
    def __init__(self, school_config):
        """
        Initialize PDF generator with school configuration.
        
        Args:
            school_config: SchoolConfig object with school details
        """
        self.config = school_config
    
    def _prepare_timetable_horizontal(self, timetable_data: Optional[Dict]) -> Dict:
        """
        Transform timetable data into horizontal format (dates as columns).
        
        Args:
            timetable_data: List of exam dicts or single exam dict
            
        Returns:
            Dictionary with 'dates', 'days', 'subjects', 'times' lists
        """
        if not timetable_data:
            return {'dates': [], 'days': [], 'subjects': [], 'times': []}
        
        exams = timetable_data if isinstance(timetable_data, list) else [timetable_data]
        
        # Extract unique dates and sort them
        date_exam_map = {}
        for exam in exams:
            date = str(exam.get('date', 'N/A')).strip()
            if date and date != 'N/A':
                if date not in date_exam_map:
                    date_exam_map[date] = exam
        
        # Sort dates (try to parse, fallback to string sort)
        try:
            sorted_dates = sorted(date_exam_map.keys(), key=lambda x: (x.split('/') if '/' in x else x.split('-')) if isinstance(x, str) else x)
        except:
            sorted_dates = sorted(date_exam_map.keys())
        
        dates = sorted_dates
        days = []
        subjects = []
        times = []
        
        for date in dates:
            exam = date_exam_map[date]
            # Extract day name if available, otherwise use date
            day = exam.get('day', date.split('/')[0] if '/' in date else date.split('-')[0] if '-' in date else '')
            days.append(day)
            subjects.append(str(exam.get('subject', 'N/A')))
            times.append(str(exam.get('time', 'N/A')))
        
        return {
            'dates': dates,
            'days': days,
            'subjects': subjects,
            'times': times
        }
    
    def _draw_table(self, canvas_obj, x_start: float, y_start: float, 
                   headers: List[str], rows: List[List[str]], 
                   col_widths: List[float], row_height: float, 
                   font_size: float = 6):
        """
        Draw a table using canvas primitives.
        
        Args:
            canvas_obj: ReportLab canvas object
            x_start: Starting x position
            y_start: Starting y position (top of table)
            headers: List of header strings
            rows: List of rows, each row is a list of cell strings
            col_widths: List of column widths
            row_height: Height of each row
            font_size: Font size for table text
        """
        num_cols = len(headers)
        num_rows = len(rows)
        
        # Draw headers
        canvas_obj.setFont("Helvetica-Bold", font_size)
        canvas_obj.setFillColor(colors.black)
        x = x_start
        y = y_start
        
        # Draw header text (no background color)
        cell_padding = 2  # Padding inside cells to prevent overlap
        for i, header in enumerate(headers):
            if i < len(col_widths):
                # Truncate text if it's too long for the cell
                available_width = col_widths[i] - 2 * cell_padding
                header_text = str(header)
                text_width = canvas_obj.stringWidth(header_text, "Helvetica-Bold", font_size)
                
                # Truncate if text is too wide
                if text_width > available_width:
                    while text_width > available_width and len(header_text) > 0:
                        header_text = header_text[:-1]
                        text_width = canvas_obj.stringWidth(header_text + "...", "Helvetica-Bold", font_size)
                    header_text = header_text + "..." if len(str(header)) > len(header_text) else header_text
                
                # Center align header text
                canvas_obj.drawString(x + cell_padding + (col_widths[i] - 2 * cell_padding - text_width) / 2, 
                                    y - row_height + (row_height - font_size) / 2, header_text)
                x += col_widths[i]
        
        # Draw header borders (top and bottom)
        canvas_obj.setStrokeColor(colors.black)
        canvas_obj.setLineWidth(0.1)
        canvas_obj.line(x_start, y - row_height, x_start + sum(col_widths), y - row_height)
        canvas_obj.line(x_start, y, x_start + sum(col_widths), y)
        
        # Draw data rows
        y -= row_height
        canvas_obj.setFont("Helvetica", font_size)
        
        for row_idx, row in enumerate(rows):
            # Draw row text (no background color)
            canvas_obj.setFillColor(colors.black)
            x = x_start
            cell_padding = 2  # Padding inside cells to prevent overlap
            for i, cell_text in enumerate(row):
                if i < len(col_widths):
                    # Truncate text if it's too long for the cell
                    available_width = col_widths[i] - 2 * cell_padding
                    cell_text_str = str(cell_text)
                    text_width = canvas_obj.stringWidth(cell_text_str, "Helvetica", font_size)
                    
                    # Truncate if text is too wide
                    if text_width > available_width:
                        while text_width > available_width and len(cell_text_str) > 0:
                            cell_text_str = cell_text_str[:-1]
                            text_width = canvas_obj.stringWidth(cell_text_str + "...", "Helvetica", font_size)
                        cell_text_str = cell_text_str + "..." if len(str(cell_text)) > len(cell_text_str) else cell_text_str
                    
                    # Center align cell text
                    canvas_obj.drawString(x + cell_padding + (col_widths[i] - 2 * cell_padding - text_width) / 2, 
                                        y - row_height + (row_height - font_size) / 2, cell_text_str)
                    x += col_widths[i]
            
            # Draw row border (bottom border for each row)
            canvas_obj.setStrokeColor(colors.black)
            canvas_obj.setLineWidth(0.1)
            canvas_obj.line(x_start, y - row_height, x_start + sum(col_widths), y - row_height)
            
            y -= row_height
        
        # Draw vertical lines (complete borders for all cells)
        canvas_obj.setStrokeColor(colors.black)
        canvas_obj.setLineWidth(0.1)
        x = x_start
        for i in range(num_cols + 1):
            # Draw vertical line from top to bottom of table
            canvas_obj.line(x, y_start, x, y_start - (num_rows + 1) * row_height)
            if i < num_cols:
                x += col_widths[i]
    
    def draw_ticket(self, canvas_obj, student_data: Dict, student_photo: Optional[PILImage.Image],
                   timetable_data: Optional[Dict], y_offset: float):
        """
        Draw a single hall ticket at the specified yOffset.
        Layout: header, student details on left, photo on top-right, timetable table, signatures at bottom.
        
        Args:
            canvas_obj: ReportLab canvas object
            student_data: Dictionary with student information
            student_photo: PIL Image of student photo
            timetable_data: Optional dictionary with timetable information
            y_offset: Y position from bottom of page (in points)
        """
        # Convert mm to points (1mm = 2.83465 points)
        mm_to_pt = 2.83465
        margin = 10 * mm_to_pt  # 10mm margin
        card_width = 190 * mm_to_pt  # 190mm card width
        card_height = 90 * mm_to_pt  # 90mm card height
        padding = 2  # 2px padding inside border
        left_margin = 15 * mm_to_pt  # 15mm from left for text
        photo_width = 25 * mm_to_pt * 0.8  # Photo width (80% of original 30mm = 24mm)
        photo_height = 30 * mm_to_pt * 0.8  # Photo height (80% of original 35mm = 28mm)
        photo_right_margin = 5 * mm_to_pt  # 5mm from right edge
        
        # Calculate positions (ReportLab uses bottom-left origin)
        x_start = margin
        y_bottom = y_offset
        y_top = y_bottom + card_height
        
        # Content area inside border with padding
        content_x_start = x_start + padding
        content_y_bottom = y_bottom + padding
        content_y_top = y_top - padding
        content_width = card_width - 2 * padding
        content_height = card_height - 2 * padding
        
        # Photo position: top-right corner (inside border with padding)
        # Only calculate photo position if photo box is enabled
        show_photo_box = getattr(self.config, 'show_photo_box', True)
        photo_x = content_x_start + content_width - photo_width - photo_right_margin -25
        photo_y = content_y_top - photo_height - 5 * mm_to_pt - 25  # 5mm from top
        
        # If photo box is disabled, adjust text area to use full width
        if not show_photo_box:
            photo_x = content_x_start + content_width  # Move photo_x beyond content area
        
        # --- 1. DRAW OUTER BORDER ---
        canvas_obj.setStrokeColor(colors.black)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.rect(x_start, y_bottom, card_width, card_height, fill=0, stroke=1)
        
        # --- 2. HEADER (with Logo and School Name) ---
        header_top_margin = 2 * mm_to_pt  # Margin from top border to ensure header stays inside
        
        # Split header into two sections:
        # 1. Logo section: 20% of content width, left-aligned
        # 2. Text section: 80% of content width, center-aligned within that space
        logo_section_width = content_width * 0.20  # 20% for logo
        text_section_width = content_width * 0.80  # 80% for text
        text_section_x = content_x_start + logo_section_width  # Start of text section
        
        # Logo size - fit within logo section with some padding
        logo_section_padding = 2 * mm_to_pt
        max_logo_size = logo_section_width - 2 * logo_section_padding
        logo_size = min(20 * mm_to_pt * 0.75, max_logo_size)  # Use 75% of 20mm or max available
        
        # Calculate header_y to ensure logo stays within top border
        header_y = content_y_top - header_top_margin - logo_size / 2
        
        # Check if logo exists and draw it
        has_logo = self.config.logo_path and self.config.logo_path.exists()
        
        if has_logo:
            # Logo position: left-aligned in logo section, centered vertically
            logo_x = content_x_start + logo_section_padding
            logo_y = header_y - logo_size / 2
            
            # Ensure logo stays within bounds
            if logo_y + logo_size > content_y_top:
                logo_y = content_y_top - logo_size
                header_y = logo_y + logo_size / 2
            if logo_y < content_y_bottom:
                logo_y = content_y_bottom
                header_y = logo_y + logo_size / 2
            
            # Draw logo
            try:
                logo_img = PILImage.open(self.config.logo_path)
                
                # Convert to RGBA if not already (handles transparency)
                if logo_img.mode != 'RGBA':
                    # If image has transparency info, convert to RGBA
                    if logo_img.mode in ('P', 'LA') or 'transparency' in logo_img.info:
                        logo_img = logo_img.convert('RGBA')
                    else:
                        # Convert to RGB for images without transparency
                        logo_img = logo_img.convert('RGB')
                
                # Resize logo
                logo_img.thumbnail((logo_size, logo_size), PILImage.Resampling.LANCZOS)
                
                # Save to buffer with proper format
                logo_buffer = io.BytesIO()
                if logo_img.mode == 'RGBA':
                    # Save RGBA as PNG to preserve transparency
                    logo_img.save(logo_buffer, format='PNG')
                else:
                    # Save RGB as PNG
                    logo_img.save(logo_buffer, format='PNG')
                logo_buffer.seek(0)
                
                # Draw image with mask for transparency support
                canvas_obj.drawImage(ImageReader(logo_buffer), logo_x, logo_y,
                                   width=logo_size, height=logo_size, 
                                   preserveAspectRatio=True, mask='auto')
            except Exception as e:
                logger.warning(f"Could not draw logo: {e}")
                has_logo = False
        
        # School name and exam name: Center-aligned within text section (80% width)
        canvas_obj.setFillColor(colors.black)
        
        # School name - first row
        canvas_obj.setFont("Helvetica-Bold", 14)
        school_name = self.config.school_name or "SCHOOL NAME"
        school_name_width = canvas_obj.stringWidth(school_name, "Helvetica-Bold", 14)
        # Center within text section
        school_name_x = text_section_x + (text_section_width - school_name_width) / 2
        canvas_obj.drawString(school_name_x, header_y, school_name)
        
        # Examination name - second row, below school name
        canvas_obj.setFont("Helvetica-Bold", 10)
        title = self.config.examination_name or "ADMIT CARD"  # Use dynamic examination name
        title_width = canvas_obj.stringWidth(title, "Helvetica-Bold", 10)
        title_y = header_y - 15  # Position title below school name with spacing
        # Center within text section
        title_x = text_section_x + (text_section_width - title_width) / 2
        canvas_obj.drawString(title_x, title_y, title)
        
        # --- 3. LEFT SIDE: Student Details ---
        # Start student details below title, ensuring no overlap with photo
        detail_start_y = title_y - 25  # Increased gap between header and student details (was 15)
        line_spacing = 7 * mm_to_pt
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(colors.black)
        
        # Ad.No and Roll No on same line
        ad_no = str(student_data.get('admission_number', 'N/A'))
        roll_no = str(student_data.get('roll_number', 'N/A'))
        
        # Calculate positions to avoid photo overlap (only if photo box is shown)
        # Ensure text area doesn't extend beyond photo_x
        if show_photo_box:
            max_text_width = photo_x - content_x_start - left_margin - 5 * mm_to_pt
        else:
            max_text_width = content_width - left_margin - 5 * mm_to_pt  # Use full width
        
        # Ad.No
        ad_text = f"Admn.No: {ad_no}"
        canvas_obj.drawString(content_x_start + left_margin, detail_start_y, ad_text)
        
        # Roll No - positioned to the right of Ad.No, but not overlapping photo
        roll_text = f"Roll No: {roll_no}"
        roll_x = content_x_start + left_margin + 75 * mm_to_pt
        # Check if Roll No would overlap with photo, if so, move it (only if photo box is shown)
        if show_photo_box and roll_x + canvas_obj.stringWidth(roll_text, "Helvetica", 9) > photo_x - 5 * mm_to_pt:
            roll_x = photo_x - canvas_obj.stringWidth(roll_text, "Helvetica", 9) - 5 * mm_to_pt
        canvas_obj.drawString(roll_x, detail_start_y, roll_text)
        
        # Name on next line
        name = str(student_data.get('name', 'N/A')).upper()
        name_text = f"Name: {name}"
        # Truncate name if too long to prevent overlap
        max_name_width = photo_x - content_x_start - left_margin - 5 * mm_to_pt
        if canvas_obj.stringWidth(name_text, "Helvetica", 9) > max_name_width:
            # Truncate name
            while canvas_obj.stringWidth(name_text, "Helvetica", 9) > max_name_width and len(name) > 0:
                name = name[:-1]
                name_text = f"Name: {name}..."
        canvas_obj.drawString(content_x_start + left_margin, detail_start_y - line_spacing, name_text)
        
        # Class & Sec on next line
        class_name = str(student_data.get('class', 'N/A'))
        class_text = f"Class & Sec: {class_name}"
        canvas_obj.drawString(content_x_start + left_margin + 210, detail_start_y - line_spacing, class_text)
        
        # --- 3b. QR CODE (Student ID for verification) ---
        # Encode student ID: roll_number|class|admission_number for scanning
        student_id = f"{student_data.get('roll_number', '')}|{student_data.get('class', '')}|{student_data.get('admission_number', '')}"
        if not student_id.strip('|'):
            student_id = str(student_data.get('roll_number', 'N/A'))
        try:
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(student_id)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_size = 18 * mm_to_pt  # 18mm QR code
            qr_x = content_x_start + content_width - qr_size - 5 * mm_to_pt  # 5mm from right
            qr_y = content_y_bottom + 5 * mm_to_pt  # 5mm from bottom
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            canvas_obj.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size,
                                preserveAspectRatio=True)
        except Exception as e:
            logger.warning(f"Could not draw QR code: {e}")

        # --- 4. RIGHT SIDE: Photo Box (Top-Right) ---
        # Only draw photo box if show_photo_box is enabled
        if show_photo_box:
            # Ensure photo stays within content area
            if photo_x + photo_width > content_x_start + content_width:
                photo_x = content_x_start + content_width - photo_width - photo_right_margin
            if photo_y < content_y_bottom:
                photo_y = content_y_bottom
            
            canvas_obj.setStrokeColor(colors.black)
            canvas_obj.setLineWidth(0.2)
            canvas_obj.rect(photo_x, photo_y, photo_width, photo_height, fill=0, stroke=1)
            
            if student_photo:
                try:
                    photo_buffer = io.BytesIO()
                    student_photo.save(photo_buffer, format='PNG')
                    photo_buffer.seek(0)
                    canvas_obj.drawImage(ImageReader(photo_buffer), photo_x, photo_y,
                                       width=photo_width, height=photo_height, 
                                       preserveAspectRatio=True, mask='auto')
                except Exception as e:
                    logger.warning(f"Could not draw photo: {e}")
                    # Fall through to placeholder
                    canvas_obj.setFont("Helvetica", 5)
                    canvas_obj.setFillColor(colors.HexColor('#969696'))
                    text = "AFFIX PHOTO HERE"
                    text_width = canvas_obj.stringWidth(text, "Helvetica", 5)
                    canvas_obj.drawString(photo_x + (photo_width - text_width) / 2, 
                                        photo_y + photo_height / 2, text)
                    canvas_obj.setFillColor(colors.black)
            else:
                # Placeholder text
                canvas_obj.setFont("Helvetica", 5)
                canvas_obj.setFillColor(colors.HexColor('#969696'))
                text = "AFFIX PHOTO HERE"
                text_width = canvas_obj.stringWidth(text, "Helvetica", 5)
                canvas_obj.drawString(photo_x + (photo_width - text_width) / 2, 
                                    photo_y + photo_height / 2, text)
                canvas_obj.setFillColor(colors.black)
        
        # --- 5. TIMETABLE TABLE ---
        # Position timetable below student details, ensuring it doesn't overlap with photo or footer
        table_start_y = detail_start_y - 2 * line_spacing - 5 * mm_to_pt
        table_left_margin = left_margin
        # Use full width of content area for timetable table
        table_width = content_width - table_left_margin - left_margin  # Full width minus left and right margins
        table_end_y = table_start_y  # Initialize in case no timetable
        timing_table_end_y = table_end_y  # Initialize for examination timing table
        
        if timetable_data:
            logger.debug(f"Timetable data received: {type(timetable_data)}, content preview: {str(timetable_data)[:200]}")
            # Prepare timetable data - use horizontal format (dates as columns)
            try:
                tt_data = self._prepare_timetable_horizontal(timetable_data)
                logger.debug(f"Prepared timetable data: dates={len(tt_data['dates'])}, days={len(tt_data['days'])}, subjects={len(tt_data['subjects'])}")
                
                if tt_data['dates']:
                    logger.info(f"Drawing timetable with {len(tt_data['dates'])} dates")
                else:
                    logger.warning(f"Timetable data prepared but no dates found. tt_data: {tt_data}")
            except Exception as e:
                logger.error(f"Error preparing timetable data: {e}", exc_info=True)
                tt_data = {'dates': [], 'days': [], 'subjects': [], 'times': []}
            
            if tt_data.get('dates'):
                # Use all dates - no hard limit, let column width adjustment handle it
                dates = [str(d) for d in tt_data['dates']]
                days = [str(d) for d in tt_data['days']]
                subjects = tt_data['subjects']
                
                # Prepare table data - horizontal format
                # Header row: Dates
                headers = ['Date'] + dates
                # Row 1: Days
                # Row 2: Subjects
                rows = [
                    ['Day'] + days,
                    ['Subject'] + subjects,
                    ['Sign of Invigilator'] + [''] * len(dates)
                ]
                
                # Calculate dynamic column widths based on content
                num_cols = len(headers)
                font_size = 6
                cell_padding = 2
                min_col_width = 15  # Minimum column width in points for readability
                
                # Calculate minimum width needed for each column based on content
                canvas_obj.setFont("Helvetica-Bold", font_size)
                min_widths = []
                
                # First column (label column) - check all label texts
                label_texts = ['Date', 'Day', 'Subject', 'Sign of Invigilator']
                first_col_min = max([canvas_obj.stringWidth(str(text), "Helvetica-Bold", font_size) 
                                    for text in label_texts]) + 2 * cell_padding
                first_col_min = max(first_col_min, min_col_width)
                min_widths.append(first_col_min)
                
                # Date columns - check header (date) and content (day, subject)
                canvas_obj.setFont("Helvetica", font_size)
                for col_idx in range(1, num_cols):
                    # Check header width (date)
                    canvas_obj.setFont("Helvetica-Bold", font_size)
                    header_text = str(headers[col_idx]) if col_idx < len(headers) else ''
                    header_width = canvas_obj.stringWidth(header_text, "Helvetica-Bold", font_size)
                    
                    # Check content widths (day, subject) - with bounds checking
                    canvas_obj.setFont("Helvetica", font_size)
                    day_idx = col_idx - 1
                    day_text = str(days[day_idx]) if day_idx < len(days) else ''
                    day_width = canvas_obj.stringWidth(day_text, "Helvetica", font_size)
                    
                    subject_idx = col_idx - 1
                    subject_text = str(subjects[subject_idx]) if subject_idx < len(subjects) else ''
                    subject_width = canvas_obj.stringWidth(subject_text, "Helvetica", font_size)
                    
                    # Find maximum width needed for this column
                    col_min_width = max(header_width, day_width, subject_width) + 2 * cell_padding
                    col_min_width = max(col_min_width, min_col_width)
                    min_widths.append(col_min_width)
                
                # Calculate total minimum width needed
                total_min_width = sum(min_widths)
                
                # If content fits within available width, use calculated widths (with some padding)
                if total_min_width <= table_width:
                    # Use calculated widths with a small buffer
                    col_widths = [w * 1.05 for w in min_widths]  # 5% buffer
                    # Adjust to exactly fit table_width
                    total_current = sum(col_widths)
                    if total_current > table_width:
                        scale_factor = table_width / total_current
                        col_widths = [w * scale_factor for w in col_widths]
                else:
                    # Content is too wide - scale down proportionally but ensure minimum
                    scale_factor = (table_width - min_widths[0]) / sum(min_widths[1:])
                    
                    # First column gets its minimum width
                    first_col_width = min_widths[0]
                    
                    # Other columns scale proportionally but not below minimum
                    remaining_width = table_width - first_col_width
                    date_cols_min_total = sum(min_widths[1:])
                    
                    if date_cols_min_total <= remaining_width:
                        # Can fit all columns at minimum - distribute remaining space proportionally
                        col_widths = [first_col_width]
                        for i in range(1, num_cols):
                            base_width = min_widths[i]
                            extra_space = (remaining_width - date_cols_min_total) * (base_width / date_cols_min_total)
                            col_widths.append(base_width + extra_space)
                    else:
                        # Must scale below minimum - use proportional scaling
                        col_widths = [first_col_width]
                        for i in range(1, num_cols):
                            proportional_width = min_widths[i] * (remaining_width / date_cols_min_total)
                            col_widths.append(max(proportional_width, min_col_width * 0.8))  # Allow 80% of minimum
                    
                    # Final adjustment to ensure total equals table_width
                    total_current = sum(col_widths)
                    if abs(total_current - table_width) > 0.1:
                        scale_factor = table_width / total_current if total_current > 0 else 1.0
                        col_widths = [w * scale_factor for w in col_widths]
                
                # Ensure we have the correct number of column widths
                if len(col_widths) != num_cols:
                    logger.warning(f"Column width count mismatch: expected {num_cols}, got {len(col_widths)}")
                    # Fallback: use equal widths
                    first_col_width = table_width * 0.15
                    date_col_width = (table_width - first_col_width) / max(1, num_cols - 1)
                    col_widths = [first_col_width] + [date_col_width] * (num_cols - 1)
                
                # Draw table
                self._draw_table(
                    canvas_obj,
                    content_x_start + table_left_margin,
                    table_start_y,
                    headers,
                    rows,
                    col_widths,
                    row_height=4 * mm_to_pt,
                    font_size=6
                )
                table_end_y = table_start_y - (len(rows) + 1) * 4 * mm_to_pt
            else:
                table_end_y = table_start_y
        else:
            table_end_y = table_start_y
        
        # --- 5b. EXAMINATION TIMING TABLE ---
        # Position below timetable table, make it 1/3rd of the page width and align to left
        timing_table_start_y = table_end_y - 5 * mm_to_pt
        timing_table_width = content_width / 3  # 1/3rd of the content width
        timing_table_row_height = 4 * mm_to_pt
        
        # Align the timing table to the left
        timing_table_x = content_x_start + table_left_margin
        
        # Get examination timing data
        timing_data = self.config.examination_timing or {}
        
        # Prepare timing table data
        timing_rows = [
            ['Reporting Time', timing_data.get('reporting_time', '08:30 a.m.')],
            ['Entry to Exam Hall', timing_data.get('entry_time', '08:45 a.m.')],
            ['Cool-off Time', timing_data.get('cooloff_time', '09:00 a.m. to 09:15 a.m.')],
            ['Reading Time', timing_data.get('reading_time', '09:15 a.m. to 09:30 a.m.')],
            ['Writing Time', timing_data.get('writing_time', '09:30 a.m. to 11:30 a.m.')]
        ]
        timing_col_widths = [timing_table_width * 0.5, timing_table_width * 0.5]
        
        # Draw timing table directly (no heading above it)
        timing_table_y = timing_table_start_y
        num_rows = len(timing_rows)
        
        # Draw merged header "Timings" spanning both columns (no background color)
        canvas_obj.setFont("Helvetica-Bold", 6)
        canvas_obj.setFillColor(colors.black)
        header_text = "Timings"
        header_text_width = canvas_obj.stringWidth(header_text, "Helvetica-Bold", 6)
        canvas_obj.drawString(timing_table_x + (timing_table_width - header_text_width) / 2,
                            timing_table_y - timing_table_row_height + (timing_table_row_height - 7) / 2, 
                            header_text)
        
        # Draw header border
        canvas_obj.setStrokeColor(colors.black)
        canvas_obj.setLineWidth(0.1)
        canvas_obj.line(timing_table_x, timing_table_y - timing_table_row_height, 
                       timing_table_x + timing_table_width, timing_table_y - timing_table_row_height)
        canvas_obj.line(timing_table_x, timing_table_y, 
                       timing_table_x + timing_table_width, timing_table_y)
        
        # Draw data rows
        y = timing_table_y - timing_table_row_height
        canvas_obj.setFont("Helvetica", 6)
        cell_padding = 2
        
        for row_idx, row in enumerate(timing_rows):
            # Draw row text (no background color)
            canvas_obj.setFillColor(colors.black)
            x = timing_table_x
            for i, cell_text in enumerate(row):
                if i < len(timing_col_widths):
                    # Truncate text if needed
                    available_width = timing_col_widths[i] - 2 * cell_padding
                    cell_text_str = str(cell_text)
                    text_width = canvas_obj.stringWidth(cell_text_str, "Helvetica", 6)
                    
                    if text_width > available_width:
                        while text_width > available_width and len(cell_text_str) > 0:
                            cell_text_str = cell_text_str[:-1]
                            text_width = canvas_obj.stringWidth(cell_text_str + "...", "Helvetica", 6)
                        cell_text_str = cell_text_str + "..." if len(str(cell_text)) > len(cell_text_str) else cell_text_str
                    
                    # Center align cell text
                    canvas_obj.drawString(x + cell_padding + (timing_col_widths[i] - 2 * cell_padding - text_width) / 2, 
                                        y - timing_table_row_height + (timing_table_row_height - 7) / 2, 
                                        cell_text_str)
                    x += timing_col_widths[i]
            
            # Draw row border (bottom border for each row)
            canvas_obj.setStrokeColor(colors.black)
            canvas_obj.setLineWidth(0.1)
            canvas_obj.line(timing_table_x, y - timing_table_row_height, 
                           timing_table_x + timing_table_width, y - timing_table_row_height)
            
            y -= timing_table_row_height
        
        # Draw all vertical lines (complete borders for all cells)
        canvas_obj.setStrokeColor(colors.black)
        canvas_obj.setLineWidth(0.1)
        # Left border (full height including header)
        canvas_obj.line(timing_table_x, timing_table_y, 
                       timing_table_x, timing_table_y - (num_rows + 1) * timing_table_row_height)
        # Middle vertical line (between Activity and Time columns) - starts below header
        canvas_obj.line(timing_table_x + timing_col_widths[0], 
                       timing_table_y - timing_table_row_height, 
                       timing_table_x + timing_col_widths[0], 
                       timing_table_y - (num_rows + 1) * timing_table_row_height)
        # Right border (full height including header)
        canvas_obj.line(timing_table_x + timing_table_width, timing_table_y, 
                       timing_table_x + timing_table_width, 
                       timing_table_y - (num_rows + 1) * timing_table_row_height)
        
        timing_table_end_y = timing_table_y - (num_rows + 1) * timing_table_row_height
        
        # --- 5c. STATUS TABLE (Right of timings table, below exam timetable) ---
        # Position to the right of timings table, at the same y level
        status_table_x = timing_table_x + timing_table_width + 5 * mm_to_pt  # 5mm gap after timings table
        status_table_y = timing_table_start_y  # Same y level as timings table
        status_table_width = content_width / 4  # 1/4 of content width (smaller than timings table)
        status_table_row_height = 4 * mm_to_pt
        
        # Ensure table doesn't exceed content width
        if status_table_x + status_table_width > content_x_start + content_width:
            status_table_width = content_x_start + content_width - status_table_x
        
        # Prepare status table data (no headers, single row, 3 columns)
        status_row = ['Status', 'A', 'G']
        status_col_widths = [status_table_width / 3, status_table_width / 3, status_table_width / 3]
        
        # Draw status table (no headers, just one row)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.black)
        cell_padding = 2
        
        # Draw row background (no background color)
        y_status = status_table_y - status_table_row_height
        
        # Draw row text
        x_status = status_table_x
        for i, cell_text in enumerate(status_row):
            if i < len(status_col_widths):
                # Truncate text if needed
                available_width = status_col_widths[i] - 2 * cell_padding
                cell_text_str = str(cell_text)
                text_width = canvas_obj.stringWidth(cell_text_str, "Helvetica", 6)
                
                if text_width > available_width:
                    while text_width > available_width and len(cell_text_str) > 0:
                        cell_text_str = cell_text_str[:-1]
                        text_width = canvas_obj.stringWidth(cell_text_str + "...", "Helvetica", 6)
                    cell_text_str = cell_text_str + "..." if len(str(cell_text)) > len(cell_text_str) else cell_text_str
                
                # Center align cell text
                canvas_obj.drawString(x_status + cell_padding + (status_col_widths[i] - 2 * cell_padding - text_width) / 2, 
                                    y_status + (status_table_row_height - 6) / 2, 
                                    cell_text_str)
                x_status += status_col_widths[i]
        
        # Draw borders for status table
        canvas_obj.setStrokeColor(colors.black)
        canvas_obj.setLineWidth(0.1)
        # Top border
        canvas_obj.line(status_table_x, status_table_y, 
                       status_table_x + status_table_width, status_table_y)
        # Bottom border
        canvas_obj.line(status_table_x, y_status, 
                       status_table_x + status_table_width, y_status)
        # Left border
        canvas_obj.line(status_table_x, status_table_y, 
                       status_table_x, y_status)
        # Right border
        canvas_obj.line(status_table_x + status_table_width, status_table_y, 
                       status_table_x + status_table_width, y_status)
        # Vertical lines between columns
        for i in range(1, 3):
            x_vertical = status_table_x + i * status_table_width / 3
            canvas_obj.line(x_vertical, status_table_y, 
                           x_vertical, y_status)
        
        status_table_end_y = y_status
        
        # --- 6. SIGNATURES (Bottom of page, same line, spanning 3/4 width) ---
        # Position signatures at the bottom, on the same line, spanning 3/4 of page width
        signature_area_width = content_width * 0.75  # 3/4 of content width
        signature_area_x = content_x_start + (content_width - signature_area_width) / 2  # Center the 3/4 width area
        # Use the lowest point between timings table and status table
        lowest_table_end = min(timing_table_end_y, status_table_end_y)
        footer_y = max(lowest_table_end - 3 * mm_to_pt, content_y_bottom + 8 * mm_to_pt) - 15
        
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.black)
        
        # Class Teacher (left side of signature area)
        class_teacher_text = "Class Teacher"
        class_teacher_x = signature_area_x
        canvas_obj.drawString(class_teacher_x + 175, footer_y, class_teacher_text)
        
        # Principal (right side of signature area)
        principal_text = "Principal"
        principal_text_width = canvas_obj.stringWidth(principal_text, "Helvetica", 8)
        # Move 15mm left from right edge of signature area
        principal_x = signature_area_x + signature_area_width - principal_text_width - (15 * mm_to_pt)
        canvas_obj.drawString(principal_x, footer_y, principal_text)
        
        # Principal signature (if available) - above "Principal" text
        if self.config.signature_path and self.config.signature_path.exists():
            try:
                sig_width = 25 * mm_to_pt
                sig_height = 8 * mm_to_pt
                sig_spacing = 2 * mm_to_pt  # Space between signature and "Principal" text
                
                # Center signature above "Principal" text
                # principal_x is the left edge of "Principal" text
                # Center the signature relative to the text width
                sig_x = principal_x + (principal_text_width - sig_width) / 2
                sig_y = footer_y + sig_spacing  # Position above the text with spacing
                
                # Ensure signature stays within bounds
                if sig_x < content_x_start:
                    sig_x = content_x_start
                if sig_x + sig_width > content_x_start + content_width:
                    sig_x = content_x_start + content_width - sig_width
                if sig_y + sig_height > content_y_top:
                    sig_y = content_y_top - sig_height
                
                signature_img = PILImage.open(self.config.signature_path)
                # Handle transparency for PNG images (similar to logo)
                if signature_img.mode in ('P', 'LA') or (signature_img.mode == 'RGBA' and signature_img.info.get('transparency', 0)):
                    signature_img = signature_img.convert('RGBA')
                else:
                    signature_img = signature_img.convert('RGB')
                
                signature_img.thumbnail((sig_width, sig_height), PILImage.Resampling.LANCZOS)
                sig_buffer = io.BytesIO()
                signature_img.save(sig_buffer, format='PNG')
                sig_buffer.seek(0)
                canvas_obj.drawImage(ImageReader(sig_buffer), sig_x, sig_y,
                                   width=sig_width, height=sig_height, 
                                   preserveAspectRatio=True, mask='auto')
            except Exception as e:
                logger.warning(f"Could not draw signature: {e}")
        
        # Principal name (if available) - below "Principal" text
        principal_name = getattr(self.config, 'principal_name', '')
        if principal_name:
            canvas_obj.setFont("Helvetica", 8)
            text_width = canvas_obj.stringWidth(principal_name, "Helvetica", 8)
            # Position below Principal text, centered under "Principal"
            canvas_obj.drawString(principal_x + (principal_text_width - text_width) / 2, 
                                footer_y - 3 * mm_to_pt, principal_name)
    
    def generate_pdf(self, output_path: str, students_data: List[Dict], 
                    student_photos: Dict[str, Optional[PILImage.Image]],
                    timetable_data: Optional[Dict] = None):
        """
        Generate PDF with hall tickets, 3 per page vertically.
        
        Args:
            output_path: Path to save the PDF file
            students_data: List of student data dictionaries
            student_photos: Dictionary mapping roll numbers to PIL Images
            timetable_data: Optional dictionary mapping roll numbers to timetable data
        """
        # Create PDF using canvas for precise control
        c = canvas.Canvas(output_path, pagesize=A4)
        page_width, page_height = A4
        
        # Convert mm to points (1mm = 2.83465 points)
        mm_to_pt = 2.83465
        margin = 10 * mm_to_pt  # 10mm margin as per JS example
        card_height = 90 * mm_to_pt  # 90mm card height as per JS example
        gap = 5 * mm_to_pt  # 5mm gap between tickets as per JS example
        
        # Process students in groups of 3
        for i in range(0, len(students_data), 3):
            group = students_data[i:i+3]
            
            # Calculate y offsets for 3 tickets (from top, convert to bottom coordinates)
            # ReportLab uses bottom-left origin, so we calculate from top and convert
            # JavaScript: yStart = margin + (pagePos * (cardHeight + gap))
            y_offsets = []
            for j in range(3):
                if j < len(group):
                    # Calculate from top: margin + j * (card_height + gap)
                    y_from_top = margin + j * (card_height + gap)
                    # Convert to bottom-left origin
                    y_bottom = page_height - y_from_top - card_height
                    y_offsets.append(y_bottom)
            
            # Draw each ticket
            for idx, student in enumerate(group):
                roll_num = str(student.get('roll_number', ''))
                photo = student_photos.get(roll_num)
                timetable = timetable_data.get(roll_num) if timetable_data else None
                
                # If no timetable found for this roll number, try to get any timetable (for class-wide timetables)
                if not timetable and timetable_data:
                    # Get first available timetable (for class-wide schedules)
                    first_key = next(iter(timetable_data.keys()), None)
                    if first_key:
                        timetable = timetable_data[first_key]
                        logger.debug(f"No timetable for roll {roll_num}, using class-wide timetable")
                
                if timetable:
                    logger.debug(f"Timetable found for roll {roll_num}: {type(timetable)}, length: {len(timetable) if isinstance(timetable, list) else 'single'}")
                else:
                    logger.warning(f"No timetable data for roll {roll_num}. Available keys: {list(timetable_data.keys())[:5] if timetable_data else 'None'}")
                
                self.draw_ticket(c, student, photo, timetable, y_offsets[idx])
            
            # Add new page if there are more students
            if i + 3 < len(students_data):
                c.showPage()
        
        c.save()
