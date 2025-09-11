"""
PDF Utility Functions

Utility functions for PDF generation and manipulation.
"""

import os
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
import uuid


class PDFUtils:
    """Utility class for PDF generation and manipulation"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom styles for PDF documents"""
        self.styles.add(ParagraphStyle(
            name='CompanyTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=20,
            textColor=colors.black
        ))
        
        self.styles.add(ParagraphStyle(
            name='NormalBold',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            textColor=colors.black
        ))
        
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=3,
            textColor=colors.grey
        ))
    
    def create_data_table(self, data: List[Dict[str, Any]], headers: List[str]) -> Table:
        """Create a formatted table from data
        
        Args:
            data: List of dictionaries containing data
            headers: List of column headers
            
        Returns:
            Table: Formatted table object
        """
        if not data:
            # Create empty table with headers only
            table_data = [headers]
        else:
            # Create table with headers and data
            table_data = [headers]
            
            for row in data:
                table_row = []
                for header in headers:
                    value = row.get(header, '')
                    # Handle datetime objects
                    if isinstance(value, (datetime, date)):
                        table_row.append(value.isoformat())
                    else:
                        table_row.append(str(value))
                table_data.append(table_row)
        
        # Create table with alternating row colors
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        return table
    
    def create_info_table(self, info_data: List[List[str]]) -> Table:
        """Create an information table
        
        Args:
            info_data: List of [label, value] pairs
            
        Returns:
            Table: Formatted information table
        """
        table = Table(info_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def generate_pdf_document(self, file_path: str, title: str, sections: List[Dict[str, Any]]):
        """Generate a PDF document with multiple sections
        
        Args:
            file_path: Path to save the PDF file
            title: Title of the document
            sections: List of section dictionaries containing:
                     - 'title': Section title
                     - 'content': List of content elements (tables, paragraphs, etc.)
                     
        Returns:
            str: Path to the generated PDF file
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Main Title
            story.append(Paragraph(title, self.styles['CompanyTitle']))
            story.append(Spacer(1, 20))
            
            # Add sections
            for section in sections:
                if 'title' in section:
                    story.append(Paragraph(section['title'], self.styles['SectionTitle']))
                    story.append(Spacer(1, 10))
                
                if 'content' in section:
                    story.extend(section['content'])
                
                story.append(Spacer(1, 20))
            
            # Footer
            footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} by AlphaAI HR System"
            story.append(Paragraph(footer_text, self.styles['SmallText']))
            
            # Build PDF
            doc.build(story)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"Failed to generate PDF document: {str(e)}")
    
    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> str:
        """Merge multiple PDF files into one
        
        Args:
            pdf_paths: List of paths to PDF files to merge
            output_path: Path for the merged output PDF
            
        Returns:
            str: Path to the merged PDF file
        """
        try:
            # PyPDF2 is commonly used for PDF merging
            from PyPDF2 import PdfMerger
            
            merger = PdfMerger()
            
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    merger.append(pdf_path)
            
            merger.write(output_path)
            merger.close()
            
            return output_path
            
        except ImportError:
            # Fallback: create a simple PDF listing the files
            sections = []
            
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    filename = os.path.basename(pdf_path)
                    file_info = [
                        ["File:", filename],
                        ["Size:", f"{os.path.getsize(pdf_path):,} bytes"],
                        ["Modified:", datetime.fromtimestamp(os.path.getmtime(pdf_path)).strftime('%Y-%m-%d %H:%M')]
                    ]
                    
                    info_table = self.create_info_table(file_info)
                    sections.append({
                        'title': f"File: {filename}",
                        'content': [info_table]
                    })
            
            return self.generate_pdf_document(output_path, "Merged Export Files", sections)
            
        except Exception as e:
            raise Exception(f"Failed to merge PDFs: {str(e)}")
    
    def create_watermark(self, text: str, opacity: float = 0.3) -> str:
        """Create a watermark PDF
        
        Args:
            text: Watermark text
            opacity: Watermark opacity (0.0 to 1.0)
            
        Returns:
            str: Path to the watermark PDF file
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                # Create watermark
                c = canvas.Canvas(temp_file.name, pagesize=A4)
                width, height = A4
                
                # Set watermark properties
                c.setFillColorRGB(1, 1, 1, opacity)  # White with opacity
                c.setFont("Helvetica-Bold", 48)
                
                # Center the text
                text_width = c.stringWidth(text, "Helvetica-Bold", 48)
                x = (width - text_width) / 2
                y = (height - 48) / 2
                
                # Draw rotated text
                c.saveState()
                c.translate(x + text_width/2, y + 24)
                c.rotate(45)
                c.drawCentredString(0, 0, text)
                c.restoreState()
                
                c.save()
                
                return temp_file.name
                
        except Exception as e:
            raise Exception(f"Failed to create watermark: {str(e)}")
    
    def add_watermark_to_pdf(self, source_path: str, watermark_path: str, output_path: str) -> str:
        """Add watermark to an existing PDF
        
        Args:
            source_path: Path to the source PDF
            watermark_path: Path to the watermark PDF
            output_path: Path for the output PDF with watermark
            
        Returns:
            str: Path to the watermarked PDF file
        """
        try:
            from PyPDF2 import PdfReader, PdfWriter
            
            reader = PdfReader(source_path)
            writer = PdfWriter()
            
            watermark_reader = PdfReader(watermark_path)
            
            # Add each page with watermark
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                watermark_page = watermark_reader.pages[0]  # Assuming single page watermark
                
                # Merge watermark
                page.merge_page(watermark_page)
                writer.add_page(page)
            
            # Save the result
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return output_path
            
        except ImportError:
            # Fallback: copy the original file
            import shutil
            shutil.copy2(source_path, output_path)
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to add watermark to PDF: {str(e)}")
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """Get information about a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict: Dictionary containing PDF information
        """
        try:
            from PyPDF2 import PdfReader
            
            if not os.path.exists(pdf_path):
                return {"error": "PDF file not found"}
            
            reader = PdfReader(pdf_path)
            
            info = {
                "file_path": pdf_path,
                "file_size": os.path.getsize(pdf_path),
                "page_count": len(reader.pages),
                "metadata": reader.metadata,
                "created_at": datetime.fromtimestamp(os.path.getmtime(pdf_path)).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return info
            
        except ImportError:
            # Fallback: get basic file info
            return {
                "file_path": pdf_path,
                "file_size": os.path.getsize(pdf_path),
                "page_count": "Unknown (PyPDF2 not available)",
                "metadata": {},
                "created_at": datetime.fromtimestamp(os.path.getmtime(pdf_path)).strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {"error": f"Failed to get PDF info: {str(e)}"}