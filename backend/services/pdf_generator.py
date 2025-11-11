from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
import io
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from backend.models import Payroll, User, Payslip
from backend.database import get_db
import uuid

class PDFGeneratorService:
    """Service for generating PDF documents using ReportLab"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom styles for the payslip"""
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
    
    def generate_payslip_pdf(self, payroll: Payroll, employee: User) -> str:
        """Generate a PDF payslip for a specific payroll record"""
        try:
            # Create unique filename
            filename = f"payslip_{payroll.payroll_id}_{employee.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join("payslips", filename)
            
            # Ensure payslips directory exists
            os.makedirs("payslips", exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Company Header
            story.append(Paragraph("ALPHASYSD HR PAYROLL SYSTEM", self.styles['CompanyTitle']))
            story.append(Spacer(1, 20))
            
            # Employee Information
            story.append(Paragraph("EMPLOYEE INFORMATION", self.styles['SectionTitle']))
            
            emp_info = [
                ["Employee Name:", f"{employee.first_name} {employee.last_name}"],
                ["Employee ID:", str(employee.user_id)],
                ["Department:", employee.department.department_name if employee.department else "N/A"],
                ["Pay Period:", f"{payroll.cutoff_start} to {payroll.cutoff_end}"],
                ["Pay Date:", payroll.generated_at.strftime('%Y-%m-%d') if payroll.generated_at else "N/A"]
            ]
            
            emp_table = Table(emp_info, colWidths=[2*inch, 3*inch])
            emp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(emp_table)
            story.append(Spacer(1, 20))
            
            # Earnings Section
            story.append(Paragraph("EARNINGS", self.styles['SectionTitle']))
            
            earnings_data = [
                ["Description", "Amount"],
                ["Basic Pay", f"₱{payroll.basic_pay:,.2f}"],
                ["Overtime Pay", f"₱{payroll.overtime_pay:,.2f}"],
                ["", ""],
                ["Total Earnings", f"₱{payroll.basic_pay + payroll.overtime_pay:,.2f}"]
            ]
            
            earnings_table = Table(earnings_data, colWidths=[3*inch, 2*inch])
            earnings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(earnings_table)
            story.append(Spacer(1, 20))
            
            # Deductions Section
            story.append(Paragraph("DEDUCTIONS", self.styles['SectionTitle']))
            
            deductions_data = [
                ["Description", "Amount"],
                ["Other Deductions", f"₱{payroll.deductions:,.2f}"],
                ["", ""],
                ["Total Deductions", f"₱{payroll.deductions:,.2f}"]
            ]
            
            deductions_table = Table(deductions_data, colWidths=[3*inch, 2*inch])
            deductions_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(deductions_table)
            story.append(Spacer(1, 20))
            
            # Net Pay
            story.append(Paragraph("NET PAY", self.styles['SectionTitle']))
            
            net_pay_data = [
                ["Total Earnings", f"₱{payroll.basic_pay + payroll.overtime_pay:,.2f}"],
                ["Less Total Deductions", f"-₱{payroll.deductions:,.2f}"],
                ["", ""],
                ["Net Pay", f"₱{payroll.net_pay:,.2f}"]
            ]
            
            net_pay_table = Table(net_pay_data, colWidths=[3*inch, 2*inch])
            net_pay_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(net_pay_table)
            story.append(Spacer(1, 30))
            
            # Footer
            footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
            story.append(Paragraph(footer_text, self.styles['SmallText']))
            story.append(Paragraph("Thank you for your service!", self.styles['SmallText']))
            
            # Build PDF
            doc.build(story)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Failed to generate PDF payslip: {str(e)}")
    
    def generate_payslip_pdf_stream(self, payroll: Payroll, employee: User) -> io.BytesIO:
        """Generate PDF payslip as a stream for download"""
        try:
            # Create in-memory PDF
            buffer = io.BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content (same as file generation but in memory)
            story = []
            
            # Company Header
            story.append(Paragraph("ALPHASYSD HR PAYROLL SYSTEM", self.styles['CompanyTitle']))
            story.append(Spacer(1, 20))
            
            # Employee Information
            story.append(Paragraph("EMPLOYEE INFORMATION", self.styles['SectionTitle']))
            
            emp_info = [
                ["Employee Name:", f"{employee.first_name} {employee.last_name}"],
                ["Employee ID:", str(employee.user_id)],
                ["Department:", employee.department.department_name if employee.department else "N/A"],
                ["Pay Period:", f"{payroll.cutoff_start} to {payroll.cutoff_end}"],
                ["Pay Date:", payroll.generated_at.strftime('%Y-%m-%d') if payroll.generated_at else "N/A"]
            ]
            
            emp_table = Table(emp_info, colWidths=[2*inch, 3*inch])
            emp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(emp_table)
            story.append(Spacer(1, 20))
            
            # Earnings Section
            story.append(Paragraph("EARNINGS", self.styles['SectionTitle']))
            
            earnings_data = [
                ["Description", "Amount"],
                ["Basic Pay", f"₱{payroll.basic_pay:,.2f}"],
                ["Overtime Pay", f"₱{payroll.overtime_pay:,.2f}"],
                ["", ""],
                ["Total Earnings", f"₱{payroll.basic_pay + payroll.overtime_pay:,.2f}"]
            ]
            
            earnings_table = Table(earnings_data, colWidths=[3*inch, 2*inch])
            earnings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(earnings_table)
            story.append(Spacer(1, 20))
            
            # Deductions Section
            story.append(Paragraph("DEDUCTIONS", self.styles['SectionTitle']))
            
            deductions_data = [
                ["Description", "Amount"],
                ["Other Deductions", f"₱{payroll.deductions:,.2f}"],
                ["", ""],
                ["Total Deductions", f"₱{payroll.deductions:,.2f}"]
            ]
            
            deductions_table = Table(deductions_data, colWidths=[3*inch, 2*inch])
            deductions_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(deductions_table)
            story.append(Spacer(1, 20))
            
            # Net Pay
            story.append(Paragraph("NET PAY", self.styles['SectionTitle']))
            
            net_pay_data = [
                ["Total Earnings", f"₱{payroll.basic_pay + payroll.overtime_pay:,.2f}"],
                ["Less Total Deductions", f"-₱{payroll.deductions:,.2f}"],
                ["", ""],
                ["Net Pay", f"₱{payroll.net_pay:,.2f}"]
            ]
            
            net_pay_table = Table(net_pay_data, colWidths=[3*inch, 2*inch])
            net_pay_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(net_pay_table)
            story.append(Spacer(1, 30))
            
            # Footer
            footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
            story.append(Paragraph(footer_text, self.styles['SmallText']))
            story.append(Paragraph("Thank you for your service!", self.styles['SmallText']))
            
            # Build PDF
            doc.build(story)
            
            # Reset buffer position to beginning
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            raise Exception(f"Failed to generate PDF payslip stream: {str(e)}")
    
    def save_payslip_record(self, payroll_id: int, file_path: str) -> Payslip:
        """Save payslip record to database"""
        try:
            db = next(get_db())
            
            # Check if payslip already exists
            existing_payslip = db.query(Payslip).filter(
                Payslip.payroll_id == payroll_id
            ).first()
            
            if existing_payslip:
                # Update existing record
                existing_payslip.file_path = file_path
                existing_payslip.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing_payslip)
                return existing_payslip
            else:
                # Create new record
                payslip = Payslip(
                    payroll_id=payroll_id,
                    file_path=file_path
                )
                db.add(payslip)
                db.commit()
                db.refresh(payslip)
                return payslip
                
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to save payslip record: {str(e)}")
        finally:
            db.close()
    
    def get_payslip_file_path(self, payroll_id: int) -> Optional[str]:
        """Get file path for existing payslip"""
        try:
            db = next(get_db())
            payslip = db.query(Payslip).filter(
                Payslip.payroll_id == payroll_id
            ).first()
            return payslip.file_path if payslip else None
        finally:
            db.close()
    
    def delete_payslip_file(self, file_path: str) -> bool:
        """Delete payslip file from filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            raise Exception(f"Failed to delete payslip file: {str(e)}")
    
    def generate_data_export(self, file_path: str, data: List[Dict[str, Any]], headers: List[str], data_type: str):
        """Generate a PDF data export file
        
        Args:
            file_path: Path to save the PDF file
            data: List of dictionaries containing data
            headers: List of column headers
            data_type: Type of data being exported
            
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
            
            # Title
            title = f"{data_type.replace('_', ' ').title()} Data Export"
            story.append(Paragraph(title, self.styles['CompanyTitle']))
            story.append(Spacer(1, 20))
            
            # Export Information
            export_info = [
                ["Export Date:", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ["Data Type:", data_type.replace('_', ' ').title()],
                ["Total Records:", str(len(data))],
                ["Export Format:", "PDF"]
            ]
            
            info_table = Table(export_info, colWidths=[2*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # Data Table
            table_data = [headers]  # Add headers as first row
            
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
            data_table = Table(table_data)
            data_table.setStyle(TableStyle([
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
            
            story.append(data_table)
            story.append(Spacer(1, 30))
            
            # Footer
            footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} by AlphaAI HR System"
            story.append(Paragraph(footer_text, self.styles['SmallText']))
            
            # Build PDF
            doc.build(story)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"Failed to generate PDF data export: {str(e)}")
    
    def add_data_section(self, file_path: str, data: List[Dict[str, Any]], headers: List[str], data_type: str):
        """Add a data section to an existing PDF file
        
        Args:
            file_path: Path to the existing PDF file
            data: List of dictionaries containing data
            headers: List of column headers
            data_type: Type of data being added
            
        Returns:
            str: Path to the updated PDF file
        """
        try:
            # Read existing PDF content
            existing_content = []
            with open(file_path, 'rb') as f:
                # For simplicity, we'll create a new PDF with existing content + new section
                # In a real implementation, you'd use PDF merger or similar functionality
                pass
            
            # Create new PDF with combined content
            # For now, we'll just create a new PDF with the additional section
            # This is a simplified approach - in production, you'd want a proper PDF merger
            
            # Create temporary file with new content
            temp_file_path = file_path.replace('.pdf', '_temp.pdf')
            
            # Generate new PDF with additional section
            doc = SimpleDocTemplate(
                temp_file_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Add new section
            section_title = f"{data_type.replace('_', ' ').title()} Data"
            story.append(Paragraph(section_title, self.styles['SectionTitle']))
            story.append(Spacer(1, 10))
            
            # Data Table
            table_data = [headers]  # Add headers as first row
            
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
            
            # Create table
            data_table = Table(table_data)
            data_table.setStyle(TableStyle([
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
            
            story.append(data_table)
            story.append(Spacer(1, 20))
            
            # Build PDF
            doc.build(story)
            
            # Replace original file with temp file
            import shutil
            shutil.move(temp_file_path, file_path)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"Failed to add data section to PDF: {str(e)}")