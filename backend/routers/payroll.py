from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import os
import io

from ..models import Payroll, User, Department, Payslip
from ..database import get_db
from pydantic import BaseModel, Field
from ..services.pdf_generator import PDFGeneratorService
from ..utils.pdf_utils import PDFUtils
from ..database import get_db
from ..services.activity_service import ActivityService

router = APIRouter(prefix="/payroll", tags=["payroll"])


class PayrollCreate(BaseModel):
    user_id: int
    cutoff_start: date
    cutoff_end: date
    basic_pay: float = Field(..., gt=0)
    overtime_pay: float = Field(default=0.0)
    deductions: float = Field(default=0.0)


class PayrollUpdate(BaseModel):
    cutoff_start: Optional[date] = None
    cutoff_end: Optional[date] = None
    basic_pay: Optional[float] = Field(default=None, gt=0)
    overtime_pay: Optional[float] = Field(default=None)
    deductions: Optional[float] = Field(default=None)


class PayrollOut(BaseModel):
    payroll_id: int
    user_id: int
    cutoff_start: date
    cutoff_end: date
    basic_pay: float
    overtime_pay: float
    deductions: float
    net_pay: float
    generated_at: Optional[date] = None

    @classmethod
    def from_orm(cls, obj):
        """Custom serialization to handle datetime conversion"""
        data = {
            **obj.__dict__,
            "generated_at": obj.generated_at.isoformat() if obj.generated_at else None
        }
        return cls(**data)


@router.post("/", response_model=PayrollOut, status_code=status.HTTP_201_CREATED)
def create_payroll(payroll: PayrollCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.user_id == payroll.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if payroll already exists for this user and period
    existing = db.query(Payroll).filter(
        Payroll.user_id == payroll.user_id,
        Payroll.cutoff_start == payroll.cutoff_start,
        Payroll.cutoff_end == payroll.cutoff_end
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Payroll record already exists for this period")
    
    # Calculate net pay
    net_pay = payroll.basic_pay + payroll.overtime_pay - payroll.deductions
    
    # Create payroll record
    db_payroll = Payroll(
        user_id=payroll.user_id,
        cutoff_start=payroll.cutoff_start,
        cutoff_end=payroll.cutoff_end,
        basic_pay=payroll.basic_pay,
        overtime_pay=payroll.overtime_pay,
        deductions=payroll.deductions,
        net_pay=net_pay
    )
    db.add(db_payroll)
    db.commit()
    db.refresh(db_payroll)
    return PayrollOut.from_orm(db_payroll)


@router.get("/", response_model=List[PayrollOut])
def list_payroll(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    payrolls = db.query(Payroll).offset(skip).limit(limit).all()
    return [PayrollOut.from_orm(payroll) for payroll in payrolls]


@router.get("/{payroll_id}", response_model=PayrollOut)
def get_payroll(payroll_id: int, db: Session = Depends(get_db)):
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    return PayrollOut.from_orm(payroll)


@router.put("/{payroll_id}", response_model=PayrollOut)
def update_payroll(payroll_id: int, payroll_update: PayrollUpdate, db: Session = Depends(get_db)):
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    # Update fields
    update_data = payroll_update.model_dump(exclude_unset=True)
    for attr, value in update_data.items():
        setattr(payroll, attr, value)
    
    # Recalculate net pay if any financial fields changed
    if any(field in update_data for field in ['basic_pay', 'overtime_pay', 'deductions']):
        payroll.net_pay = payroll.basic_pay + payroll.overtime_pay - payroll.deductions
    
    db.commit()
    db.refresh(payroll)
    return PayrollOut.from_orm(payroll)


@router.delete("/{payroll_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payroll(payroll_id: int, db: Session = Depends(get_db)):
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    db.delete(payroll)
    db.commit()
    return


@router.post("/{payroll_id}/generate-payslip", response_model=dict)
def generate_payslip(payroll_id: int, db: Session = Depends(get_db)):
    """Generate PDF payslip for a specific payroll record"""
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    try:
        # Initialize PDF generator
        pdf_generator = PDFGeneratorService()
        
        # Get employee information
        employee = db.query(User).filter(User.user_id == payroll.user_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Generate PDF payslip
        pdf_path = pdf_generator.generate_payslip_pdf(payroll, employee)
        
        # Save payslip record
        payslip_record = pdf_generator.save_payslip_record(payroll_id, pdf_path)
        
        # Log activity
        activity_service = ActivityService(db)
        activity_service.log_activity(
            action="payslip_generated",
            resource="payslip",
            resource_id=payslip_record.payslip_id,
            user_id=1,  # This would be the actual user_id from the token in a real app
            details={
                "payroll_id": payroll_id,
                "employee_id": payroll.user_id,
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "pdf_file_name": os.path.basename(pdf_path),
                "generation_time": datetime.now().isoformat()
            }
        )
        
        # Get PDF file info for response
        pdf_metadata = PDFUtils.get_payslip_metadata(pdf_path)
        
        db.commit()
        
        return {
            "payroll_id": payroll_id,
            "employee_id": payroll.user_id,
            "pdf_file_path": pdf_path,
            "pdf_file_name": pdf_metadata.get("filename", ""),
            "pdf_file_size": pdf_metadata.get("size_formatted", ""),
            "generation_status": "generated",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/{payroll_id}/download-payslip")
def download_payslip(payroll_id: int, db: Session = Depends(get_db)):
    """Download generated PDF payslip"""
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    # Get payslip record
    payslip = db.query(Payslip).filter(
        Payslip.payroll_id == payroll_id
    ).first()
    
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    if payslip.generation_status != "generated":
        raise HTTPException(status_code=400, detail="Payslip not generated yet")
    
    if not os.path.exists(payslip.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    try:
        # Increment download count
        payslip.download_count += 1
        db.commit()
        
        # Read PDF file
        with open(payslip.file_path, "rb") as file:
            file_content = file.read()
        
        # Return PDF file for download
        return Response(
            content=file_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={os.path.basename(payslip.file_path)}",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download payslip: {str(e)}")


@router.get("/{payroll_id}/view-payslip")
def view_payslip(payroll_id: int, db: Session = Depends(get_db)):
    """View PDF payslip in browser"""
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    # Get payslip record
    payslip = db.query(Payslip).filter(
        Payslip.payroll_id == payroll_id
    ).first()
    
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    if payslip.generation_status != "generated":
        raise HTTPException(status_code=400, detail="Payslip not generated yet")
    
    if not os.path.exists(payslip.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    try:
        # Read PDF file
        with open(payslip.file_path, "rb") as file:
            file_content = file.read()
        
        # Return PDF file inline for viewing
        return Response(
            content=file_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={os.path.basename(payslip.file_path)}",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to view payslip: {str(e)}")


@router.post("/bulk-generate-payslips", response_model=dict)
def bulk_generate_payslips(payroll_ids: List[int], db: Session = Depends(get_db)):
    """Generate PDF payslips for multiple payroll records"""
    
    if not payroll_ids:
        raise HTTPException(status_code=400, detail="No payroll IDs provided")
    
    results = []
    failed_count = 0
    
    try:
        # Initialize PDF generator
        pdf_generator = PDFGeneratorService()
        activity_service = ActivityService(db)
        
        for payroll_id in payroll_ids:
            try:
                # Get payroll record
                payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
                if not payroll:
                    results.append({
                        "payroll_id": payroll_id,
                        "status": "failed",
                        "error": "Payroll record not found"
                    })
                    failed_count += 1
                    continue
                  
                # Get employee information
                employee = db.query(User).filter(User.user_id == payroll.user_id).first()
                if not employee:
                    results.append({
                        "payroll_id": payroll_id,
                        "status": "failed",
                        "error": "Employee not found"
                    })
                    failed_count += 1
                    continue
                  
                # Generate PDF payslip
                pdf_path = pdf_generator.generate_payslip_pdf(payroll, employee)
                
                # Save payslip record
                payslip_record = pdf_generator.save_payslip_record(payroll_id, pdf_path)
                
                # Log activity
                activity_service.log_activity(
                    action="bulk_payslip_generated",
                    resource="payslip",
                    resource_id=payslip_record.payslip_id,
                    user_id=1,  # This would be the actual user_id from the token in a real app
                    details={
                        "payroll_id": payroll_id,
                        "employee_id": payroll.user_id,
                        "employee_name": f"{employee.first_name} {employee.last_name}",
                        "pdf_file_name": os.path.basename(pdf_path),
                        "generation_time": datetime.now().isoformat()
                    }
                )
                
                # Get PDF file info for response
                pdf_metadata = PDFUtils.get_payslip_metadata(pdf_path)
                
                results.append({
                    "payroll_id": payroll_id,
                    "status": "success",
                    "pdf_file_path": pdf_path,
                    "pdf_file_name": pdf_metadata.get("filename", ""),
                    "pdf_file_size": pdf_metadata.get("size_formatted", "")
                })
                
            except Exception as e:
                results.append({
                    "payroll_id": payroll_id,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        db.commit()
        
        return {
            "total_payrolls": len(payroll_ids),
            "successful_count": len(payroll_ids) - failed_count,
            "failed_count": failed_count,
            "results": results
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk generation failed: {str(e)}")


@router.get("/payslips/list", response_model=List[dict])
def list_payslips(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all generated payslips"""
    
    payslips = db.query(Payslip).offset(skip).limit(limit).all()
    
    payslip_list = []
    for payslip in payslips:
        # Get related payroll and employee info
        payroll = db.query(Payroll).filter(Payroll.payroll_id == payslip.payroll_id).first()
        employee = payroll.user if payroll else None
        
        payslip_info = {
            "payslip_id": payslip.payslip_id,
            "payroll_id": payslip.payroll_id,
            "employee_name": f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
            "employee_id": employee.user_id if employee else None,
            "file_path": payslip.file_path,
            "file_name": os.path.basename(payslip.file_path) if payslip.file_path else None,
            "file_size": payslip.file_size,
            "file_size_formatted": PDFUtils.format_file_size(payslip.file_size) if payslip.file_size else None,
            "file_hash": payslip.file_hash,
            "generation_status": payslip.generation_status,
            "download_count": payslip.download_count,
            "generated_at": payslip.generated_at.isoformat() if payslip.generated_at else None,
            "updated_at": payslip.updated_at.isoformat() if payslip.updated_at else None
        }
        
        payslip_list.append(payslip_info)
    
    return payslip_list


@router.get("/summary")
def get_payroll_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get payroll summary statistics"""
    # Total payrolls
    total_payrolls = db.query(Payroll).count()
    
    # Total net pay
    total_net_pay = db.query(func.sum(Payroll.net_pay)).scalar() or 0
    
    # Average net pay
    avg_net_pay = db.query(func.avg(Payroll.net_pay)).scalar() or 0
    
    # Payrolls this month
    current_month = date.today().month
    current_year = date.today().year
    recent_payrolls = db.query(Payroll).filter(
        func.extract('month', Payroll.generated_at) == current_month,
        func.extract('year', Payroll.generated_at) == current_year
    ).count()
    
    return {
        "total_payrolls": total_payrolls,
        "total_net_pay": float(total_net_pay),
        "average_net_pay": float(avg_net_pay),
        "recent_payrolls": recent_payrolls
    }


@router.get("/employee/{employee_id}")
def get_employee_payroll_details(employee_id: int, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get payroll details for a specific employee"""
    # Check if employee exists
    employee = db.query(User).filter(User.user_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get employee payroll records
    payrolls = db.query(Payroll).filter(Payroll.user_id == employee_id).all()
    
    # Convert to list of dictionaries
    payroll_details = []
    for payroll in payrolls:
        payroll_dict = {
            "payroll_id": payroll.payroll_id,
            "user_id": payroll.user_id,
            "cutoff_start": payroll.cutoff_start.isoformat() if payroll.cutoff_start else None,
            "cutoff_end": payroll.cutoff_end.isoformat() if payroll.cutoff_end else None,
            "basic_pay": float(payroll.basic_pay),
            "overtime_pay": float(payroll.overtime_pay),
            "deductions": float(payroll.deductions),
            "net_pay": float(payroll.net_pay),
            "generated_at": payroll.generated_at.isoformat() if payroll.generated_at else None
        }
        payroll_details.append(payroll_dict)
    
    return payroll_details


@router.get("/departments")
def get_departments(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get all departments"""
    departments = db.query(Department).all()
    
    dept_list = []
    for dept in departments:
        dept_dict = {
            "department_id": dept.department_id,
            "department_name": dept.department_name
        }
        dept_list.append(dept_dict)
    
    return dept_list


@router.get("/filtered")
def get_filtered_payroll(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[PayrollOut]:
    """Get payroll records with optional filters"""
    query = db.query(Payroll)
    
    # Apply date filters
    if start_date:
        query = query.filter(Payroll.cutoff_start >= start_date)
    if end_date:
        query = query.filter(Payroll.cutoff_end <= end_date)
    
    # Apply department filter
    if department_id:
        # Join with User table to filter by department
        query = query.join(User).filter(User.department_id == department_id)
    
    # Apply user filter
    if user_id:
        query = query.filter(Payroll.user_id == user_id)
    
    # Apply pagination
    payrolls = query.offset(skip).limit(limit).all()
    
    return [PayrollOut.from_orm(payroll) for payroll in payrolls]


@router.get("/{payroll_id}/payslips/list", response_model=List[dict])
def get_payslip_list(payroll_id: int, db: Session = Depends(get_db)):
    """Get list of payslips for a specific payroll"""
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    payslips = db.query(Payslip).filter(
        Payslip.payroll_id == payroll_id
    ).all()
    
    if not payslips:
        return []
    
    payslip_list = []
    for payslip in payslips:
        payslip_list.append({
            "payslip_id": payslip.payslip_id,
            "file_path": payslip.file_path,
            "file_name": os.path.basename(payslip.file_path) if payslip.file_path else None,
            "file_size": payslip.file_size,
            "generation_status": payslip.generation_status,
            "download_count": payslip.download_count,
            "generated_at": payslip.generated_at.isoformat() if payslip.generated_at else None
        })
    
    return payslip_list