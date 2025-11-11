from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import os
import io

from backend.models import Payroll, User, Department, Payslip
from backend.database import get_db
from pydantic import BaseModel, Field
from backend.services.pdf_generator import PDFGeneratorService
from backend.utils.pdf_utils import PDFUtils
from backend.services.activity_service import ActivityService
from backend.utils.logger import ActivityLogger as EnhancedLogger
from backend.utils.json_logger import JSONActivityLogger as StructuredLogger
from backend.utils.performance_monitor import PerformanceMonitor
from backend.utils.log_aggregator import LogAggregator
from backend.utils.payroll_performance_monitor import PayrollPerformanceMonitor
from backend.utils.payroll_log_aggregator import PayrollLogAggregator
from backend.middleware.rbac import PermissionChecker, has_permission, has_role

# Initialize enhanced logging and monitoring
payroll_logger = EnhancedLogger()
structured_logger = StructuredLogger(log_dir="logs/json")
performance_monitor = PerformanceMonitor()
payroll_performance_monitor = PayrollPerformanceMonitor(log_dir="logs/payroll")
payroll_log_aggregator = PayrollLogAggregator(log_dir="logs/payroll")
log_aggregator = LogAggregator()

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
@has_permission("create_payroll")
def create_payroll(payroll: PayrollCreate, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("create_payroll"))):
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("create_payroll")
    
    # Log the start of payroll creation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="create_payroll_start",
        details={
            "user_id": payroll.user_id,
            "cutoff_start": str(payroll.cutoff_start),
            "cutoff_end": str(payroll.cutoff_end),
            "basic_pay": payroll.basic_pay,
            "overtime_pay": payroll.overtime_pay,
            "deductions": payroll.deductions
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Check if user exists
    user = db.query(User).filter(User.user_id == payroll.user_id).first()
    if not user:
        payroll_logger.log_error(
            error_type="UserNotFound",
            message=f"User not found during payroll creation: {payroll.user_id}",
            details={"user_id": payroll.user_id}
        )
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if payroll already exists for this user and period
    existing = db.query(Payroll).filter(
        Payroll.user_id == payroll.user_id,
        Payroll.cutoff_start == payroll.cutoff_start,
        Payroll.cutoff_end == payroll.cutoff_end
    ).first()
    
    if existing:
        payroll_logger.log_error(
            error_type="PayrollExists",
            message=f"Payroll record already exists for user {payroll.user_id}",
            details={
                "user_id": payroll.user_id,
                "cutoff_start": str(payroll.cutoff_start),
                "cutoff_end": str(payroll.cutoff_end)
            }
        )
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
    
    # Log successful payroll creation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="create_payroll_success",
        details={
            "payroll_id": db_payroll.payroll_id,
            "user_id": payroll.user_id,
            "net_pay": net_pay,
            "generation_time": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Record performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="payroll_creation_count",
        value=1,
        tags={"type": "create"},
        component="payroll_router"
    )
    performance_monitor.record_gauge(
        name="payroll_amount",
        value=net_pay,
        tags={"type": "net_pay"},
        component="payroll_router"
    )
    
    # Log structured data
    structured_logger.log_audit_event(
        event_type="PAYROLL_CREATED",
        description=f"Payroll created for user {payroll.user_id}",
        user_id=payroll.user_id,
        details={
            "payroll_id": db_payroll.payroll_id,
            "net_pay": net_pay,
            "basic_pay": payroll.basic_pay,
            "overtime_pay": payroll.overtime_pay,
            "deductions": payroll.deductions
        }
    )
    
    return PayrollOut.from_orm(db_payroll)


@router.get("/", response_model=List[PayrollOut])
@has_permission("read_payroll")
def list_payroll(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("read_payroll"))):
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("list_payroll")
    
    # Log the list payroll operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="list_payroll",
        details={
            "skip": skip,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    payrolls = db.query(Payroll).offset(skip).limit(limit).all()
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="payroll_list_count",
        value=len(payrolls),
        tags={"type": "list"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_LIST",
        description=f"Listed {len(payrolls)} payroll records",
        details={
            "skip": skip,
            "limit": limit,
            "count": len(payrolls)
        }
    )
    
    return [PayrollOut.from_orm(payroll) for payroll in payrolls]


@router.get("/{payroll_id}", response_model=PayrollOut)
@has_permission("read_payroll")
def get_payroll(payroll_id: int, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("read_payroll"))):
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_payroll")
    
    # Log the get payroll operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_payroll",
        details={
            "payroll_id": payroll_id,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        payroll_logger.log_error(
            error_type="PayrollNotFound",
            message=f"Payroll record not found: {payroll_id}",
            details={"payroll_id": payroll_id}
        )
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    # Log successful payroll retrieval
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_payroll_success",
        details={
            "payroll_id": payroll_id,
            "user_id": payroll.user_id,
            "net_pay": payroll.net_pay,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_RETRIEVED",
        description=f"Payroll record retrieved: {payroll_id}",
        user_id=payroll.user_id,
        details={
            "payroll_id": payroll_id,
            "user_id": payroll.user_id,
            "net_pay": payroll.net_pay
        }
    )
    
    # Record performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="payroll_retrieval_count",
        value=1,
        tags={"type": "get"},
        component="payroll_router"
    )
    
    return PayrollOut.from_orm(payroll)


@router.put("/{payroll_id}", response_model=PayrollOut)
@has_permission("update_payroll")
def update_payroll(payroll_id: int, payroll_update: PayrollUpdate, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("update_payroll"))):
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("update_payroll")
    
    # Log the update payroll operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="update_payroll_start",
        details={
            "payroll_id": payroll_id,
            "update_data": payroll_update.model_dump(exclude_unset=True),
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        payroll_logger.log_error(
            error_type="PayrollNotFound",
            message=f"Payroll record not found during update: {payroll_id}",
            details={"payroll_id": payroll_id}
        )
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
    
    # Log successful payroll update
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="update_payroll_success",
        details={
            "payroll_id": payroll_id,
            "update_data": update_data,
            "new_net_pay": payroll.net_pay,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Record performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="payroll_update_count",
        value=1,
        tags={"type": "update"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_UPDATED",
        description=f"Payroll record updated: {payroll_id}",
        user_id=payroll.user_id,
        details={
            "payroll_id": payroll_id,
            "update_data": update_data,
            "new_net_pay": payroll.net_pay
        }
    )
    
    return PayrollOut.from_orm(payroll)


@router.delete("/{payroll_id}", status_code=status.HTTP_204_NO_CONTENT)
@has_permission("delete_payroll")
def delete_payroll(payroll_id: int, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("delete_payroll"))):
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("delete_payroll")
    
    # Log the delete payroll operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="delete_payroll",
        details={
            "payroll_id": payroll_id,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        payroll_logger.log_error(
            error_type="PayrollNotFound",
            message=f"Payroll record not found during deletion: {payroll_id}",
            details={"payroll_id": payroll_id}
        )
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    db.delete(payroll)
    db.commit()
    
    # Log successful payroll deletion
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="delete_payroll_success",
        details={
            "payroll_id": payroll_id,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Record performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="payroll_deletion_count",
        value=1,
        tags={"type": "delete"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_DELETED",
        description=f"Payroll record deleted: {payroll_id}",
        user_id=0,  # System activity
        details={
            "payroll_id": payroll_id
        }
    )
    
    return


@router.post("/{payroll_id}/generate-payslip", response_model=dict)
def generate_payslip(payroll_id: int, db: Session = Depends(get_db)):
    """Generate PDF payslip for a specific payroll record"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("generate_payslip")
    
    # Log the generate payslip operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="generate_payslip_start",
        details={
            "payroll_id": payroll_id,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        payroll_logger.log_error(
            error_type="PayrollNotFound",
            message=f"Payroll record not found during payslip generation: {payroll_id}",
            details={"payroll_id": payroll_id}
        )
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    try:
        # Initialize PDF generator
        pdf_generator = PDFGeneratorService()
        
        # Get employee information
        employee = db.query(User).filter(User.user_id == payroll.user_id).first()
        if not employee:
            payroll_logger.log_error(
                error_type="EmployeeNotFound",
                message=f"Employee not found during payslip generation for payroll: {payroll_id}",
                details={"payroll_id": payroll_id, "user_id": payroll.user_id}
            )
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
        
        # Log successful payslip generation
        payroll_logger.log_activity(
            user_id=0,  # System activity
            action="generate_payslip_success",
            details={
                "payroll_id": payroll_id,
                "payslip_id": payslip_record.payslip_id,
                "employee_id": payroll.user_id,
                "pdf_file_name": os.path.basename(pdf_path),
                "generation_time": datetime.now().isoformat()
            },
            log_to_db=True,
            log_to_file=True
        )
        
        # Record performance metrics
        performance_monitor.stop_timer(timer_id)
        performance_monitor.record_counter(
            name="payslip_generation_count",
            value=1,
            tags={"type": "generate"},
            component="payroll_router"
        )
        
        # Log structured data for audit
        structured_logger.log_audit_event(
            event_type="PAYSHEET_GENERATED",
            description=f"Payslip generated for payroll: {payroll_id}",
            user_id=payroll.user_id,
            details={
                "payroll_id": payroll_id,
                "payslip_id": payslip_record.payslip_id,
                "employee_id": payroll.user_id,
                "pdf_file_name": os.path.basename(pdf_path)
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
        payroll_logger.log_error(
            error_type="PDFGenerationFailed",
            message=f"PDF generation failed for payroll: {payroll_id}",
            details={"payroll_id": payroll_id, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/{payroll_id}/download-payslip")
def download_payslip(payroll_id: int, db: Session = Depends(get_db)):
    """Download generated PDF payslip"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("download_payslip")
    
    # Log the download payslip operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="download_payslip",
        details={
            "payroll_id": payroll_id,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        payroll_logger.log_error(
            error_type="PayrollNotFound",
            message=f"Payroll record not found during payslip download: {payroll_id}",
            details={"payroll_id": payroll_id}
        )
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    # Get payslip record
    payslip = db.query(Payslip).filter(
        Payslip.payroll_id == payroll_id
    ).first()
    
    if not payslip:
        payroll_logger.log_error(
            error_type="PayslipNotFound",
            message=f"Payslip record not found for payroll: {payroll_id}",
            details={"payroll_id": payroll_id}
        )
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    if payslip.generation_status != "generated":
        payroll_logger.log_error(
            error_type="PayslipNotGenerated",
            message=f"Payslip not generated yet for payroll: {payroll_id}",
            details={"payroll_id": payroll_id, "status": payslip.generation_status}
        )
        raise HTTPException(status_code=400, detail="Payslip not generated yet")
    
    if not os.path.exists(payslip.file_path):
        payroll_logger.log_error(
            error_type="PDFFileNotFound",
            message=f"PDF file not found for payslip: {payroll_id}",
            details={"payroll_id": payroll_id, "file_path": payslip.file_path}
        )
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    try:
        # Increment download count
        payslip.download_count += 1
        db.commit()
        
        # Log successful payslip download
        payroll_logger.log_activity(
            user_id=0,  # System activity
            action="download_payslip_success",
            details={
                "payroll_id": payroll_id,
                "payslip_id": payslip.payslip_id,
                "download_count": payslip.download_count,
                "timestamp": datetime.now().isoformat()
            },
            log_to_db=True,
            log_to_file=True
        )
        
        # Record performance metrics
        performance_monitor.stop_timer(timer_id)
        performance_monitor.record_counter(
            name="payslip_download_count",
            value=1,
            tags={"type": "download"},
            component="payroll_router"
        )
        
        # Log structured data for audit
        structured_logger.log_audit_event(
            event_type="PAYSHEET_DOWNLOADED",
            description=f"Payslip downloaded for payroll: {payroll_id}",
            user_id=payroll.user_id,
            details={
                "payroll_id": payroll_id,
                "payslip_id": payslip.payslip_id,
                "download_count": payslip.download_count
            }
        )
        
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
        payroll_logger.log_error(
            error_type="PayslipDownloadFailed",
            message=f"Payslip download failed for payroll: {payroll_id}",
            details={"payroll_id": payroll_id, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Failed to download payslip: {str(e)}")


@router.get("/{payroll_id}/view-payslip")
def view_payslip(payroll_id: int, db: Session = Depends(get_db)):
    """View PDF payslip in browser"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("view_payslip")
    
    # Log the view payslip operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="view_payslip",
        details={
            "payroll_id": payroll_id,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        payroll_logger.log_error(
            error_type="PayrollNotFound",
            message=f"Payroll record not found during payslip viewing: {payroll_id}",
            details={"payroll_id": payroll_id}
        )
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    # Get payslip record
    payslip = db.query(Payslip).filter(
        Payslip.payroll_id == payroll_id
    ).first()
    
    if not payslip:
        payroll_logger.log_error(
            error_type="PayslipNotFound",
            message=f"Payslip record not found for payroll: {payroll_id}",
            details={"payroll_id": payroll_id}
        )
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    if payslip.generation_status != "generated":
        payroll_logger.log_error(
            error_type="PayslipNotGenerated",
            message=f"Payslip not generated yet for payroll: {payroll_id}",
            details={"payroll_id": payroll_id, "status": payslip.generation_status}
        )
        raise HTTPException(status_code=400, detail="Payslip not generated yet")
    
    if not os.path.exists(payslip.file_path):
        payroll_logger.log_error(
            error_type="PDFFileNotFound",
            message=f"PDF file not found for payslip: {payroll_id}",
            details={"payroll_id": payroll_id, "file_path": payslip.file_path}
        )
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    try:
        # Log successful payslip viewing
        payroll_logger.log_activity(
            user_id=0,  # System activity
            action="view_payslip_success",
            details={
                "payroll_id": payroll_id,
                "payslip_id": payslip.payslip_id,
                "timestamp": datetime.now().isoformat()
            },
            log_to_db=True,
            log_to_file=True
        )
        
        # Record performance metrics
        performance_monitor.stop_timer(timer_id)
        performance_monitor.record_counter(
            name="payslip_view_count",
            value=1,
            tags={"type": "view"},
            component="payroll_router"
        )
        
        # Log structured data for audit
        structured_logger.log_audit_event(
            event_type="PAYSHEET_VIEWED",
            description=f"Payslip viewed for payroll: {payroll_id}",
            user_id=payroll.user_id,
            details={
                "payroll_id": payroll_id,
                "payslip_id": payslip.payslip_id
            }
        )
        
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
        payroll_logger.log_error(
            error_type="PayslipViewFailed",
            message=f"Payslip view failed for payroll: {payroll_id}",
            details={"payroll_id": payroll_id, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Failed to view payslip: {str(e)}")


@router.post("/bulk-generate-payslips", response_model=dict)
def bulk_generate_payslips(payroll_ids: List[int], db: Session = Depends(get_db)):
    """Generate PDF payslips for multiple payroll records"""
    
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("bulk_generate_payslips")
    
    # Log the bulk generate payslips operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="bulk_generate_payslips_start",
        details={
            "payroll_ids": payroll_ids,
            "total_count": len(payroll_ids),
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    if not payroll_ids:
        payroll_logger.log_error(
            error_type="NoPayrollIDs",
            message="No payroll IDs provided for bulk generation",
            details={"payroll_ids": payroll_ids}
        )
        raise HTTPException(status_code=400, detail="No payroll IDs provided")
    
    results = []
    failed_count = 0
    
    try:
        # Initialize PDF generator
        pdf_generator = PDFGeneratorService()
        activity_service = ActivityService(db)
        
        for payroll_id in payroll_ids:
            try:
                # Log individual generation attempt
                payroll_logger.log_activity(
                    user_id=0,  # System activity
                    action="bulk_payslip_generation_attempt",
                    details={
                        "payroll_id": payroll_id,
                        "timestamp": datetime.now().isoformat()
                    },
                    log_to_db=True,
                    log_to_file=True
                )
                
                # Get payroll record
                payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
                if not payroll:
                    payroll_logger.log_error(
                        error_type="PayrollNotFound",
                        message=f"Payroll record not found during bulk generation: {payroll_id}",
                        details={"payroll_id": payroll_id}
                    )
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
                    payroll_logger.log_error(
                        error_type="EmployeeNotFound",
                        message=f"Employee not found during bulk generation for payroll: {payroll_id}",
                        details={"payroll_id": payroll_id, "user_id": payroll.user_id}
                    )
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
                
                # Log successful individual payslip generation
                payroll_logger.log_activity(
                    user_id=0,  # System activity
                    action="bulk_payslip_generated_success",
                    details={
                        "payroll_id": payroll_id,
                        "payslip_id": payslip_record.payslip_id,
                        "employee_id": payroll.user_id,
                        "pdf_file_name": os.path.basename(pdf_path),
                        "generation_time": datetime.now().isoformat()
                    },
                    log_to_db=True,
                    log_to_file=True
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
                payroll_logger.log_error(
                    error_type="BulkPDFGenerationFailed",
                    message=f"Bulk PDF generation failed for payroll: {payroll_id}",
                    details={"payroll_id": payroll_id, "error": str(e)}
                )
                results.append({
                    "payroll_id": payroll_id,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        # Record performance metrics
        performance_monitor.stop_timer(timer_id)
        performance_monitor.record_counter(
            name="bulk_payslip_generation_count",
            value=len(payroll_ids),
            tags={"type": "bulk_generate"},
            component="payroll_router"
        )
        
        # Log structured data for audit
        structured_logger.log_audit_event(
            event_type="BULK_PAYSHEET_GENERATED",
            description=f"Bulk payslip generation completed: {len(payroll_ids) - failed_count}/{len(payroll_ids)} successful",
            user_id=0,  # System activity
            details={
                "total_payrolls": len(payroll_ids),
                "successful_count": len(payroll_ids) - failed_count,
                "failed_count": failed_count
            }
        )
        
        db.commit()
        
        return {
            "total_payrolls": len(payroll_ids),
            "successful_count": len(payroll_ids) - failed_count,
            "failed_count": failed_count,
            "results": results
        }
        
    except Exception as e:
        payroll_logger.log_error(
            error_type="BulkGenerationFailed",
            message=f"Bulk generation failed: {str(e)}",
            details={"payroll_ids": payroll_ids, "error": str(e)}
        )
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk generation failed: {str(e)}")


@router.get("/payslips/list", response_model=List[dict])
def list_payslips(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all generated payslips"""
    
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("list_payslips")
    
    # Log the list payslips operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="list_payslips",
        details={
            "skip": skip,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
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
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="payslip_list_count",
        value=len(payslips),
        tags={"type": "list"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYSHEET_LIST",
        description=f"Listed {len(payslips)} payslip records",
        details={
            "skip": skip,
            "limit": limit,
            "count": len(payslips)
        }
    )
    
    return payslip_list


@router.get("/summary")
def get_payroll_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get payroll summary statistics"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_payroll_summary")
    
    # Log the get payroll summary operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_payroll_summary",
        details={
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
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
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="payroll_summary_count",
        value=1,
        tags={"type": "summary"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_SUMMARY",
        description="Payroll summary statistics retrieved",
        user_id=0,  # System activity
        details={
            "total_payrolls": total_payrolls,
            "total_net_pay": float(total_net_pay),
            "average_net_pay": float(avg_net_pay),
            "recent_payrolls": recent_payrolls
        }
    )
    
    return {
        "total_payrolls": total_payrolls,
        "total_net_pay": float(total_net_pay),
        "average_net_pay": float(avg_net_pay),
        "recent_payrolls": recent_payrolls
    }


@router.get("/employee/{employee_id}")
def get_employee_payroll_details(employee_id: int, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get payroll details for a specific employee"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_employee_payroll_details")
    
    # Log the get employee payroll details operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_employee_payroll_details",
        details={
            "employee_id": employee_id,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Check if employee exists
    employee = db.query(User).filter(User.user_id == employee_id).first()
    if not employee:
        payroll_logger.log_error(
            error_type="EmployeeNotFound",
            message=f"Employee not found when retrieving payroll details: {employee_id}",
            details={"employee_id": employee_id}
        )
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
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="employee_payroll_details_count",
        value=len(payroll_details),
        tags={"type": "employee_details"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="EMPLOYEE_PAYROLL_DETAILS",
        description=f"Retrieved payroll details for employee: {employee_id}",
        user_id=employee_id,
        details={
            "employee_id": employee_id,
            "payroll_count": len(payroll_details)
        }
    )
    
    return payroll_details


@router.get("/departments")
def get_departments(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get all departments"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_departments")
    
    # Log the get departments operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_departments",
        details={
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    departments = db.query(Department).all()
    
    dept_list = []
    for dept in departments:
        dept_dict = {
            "department_id": dept.department_id,
            "department_name": dept.department_name
        }
        dept_list.append(dept_dict)
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="departments_list_count",
        value=len(dept_list),
        tags={"type": "departments"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="DEPARTMENTS_LIST",
        description=f"Listed {len(dept_list)} departments",
        details={
            "department_count": len(dept_list)
        }
    )
    
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
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_filtered_payroll")
    
    # Log the get filtered payroll operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_filtered_payroll",
        details={
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "department_id": department_id,
            "user_id": user_id,
            "skip": skip,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
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
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="filtered_payroll_count",
        value=len(payrolls),
        tags={"type": "filtered"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_FILTERED",
        description=f"Retrieved {len(payrolls)} filtered payroll records",
        user_id=0,  # System activity
        details={
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "department_id": department_id,
            "user_id": user_id,
            "skip": skip,
            "limit": limit,
            "count": len(payrolls)
        }
    )
    
    return [PayrollOut.from_orm(payroll) for payroll in payrolls]


@router.get("/{payroll_id}/payslips/list", response_model=List[dict])
def get_payslip_list(payroll_id: int, db: Session = Depends(get_db)):
    """Get list of payslips for a specific payroll"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_payslip_list")
    
    # Log the get payslip list operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_payslip_list",
        details={
            "payroll_id": payroll_id,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    payroll = db.query(Payroll).filter(Payroll.payroll_id == payroll_id).first()
    if not payroll:
        payroll_logger.log_error(
            error_type="PayrollNotFound",
            message=f"Payroll record not found when retrieving payslip list: {payroll_id}",
            details={"payroll_id": payroll_id}
        )
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    payslips = db.query(Payslip).filter(
        Payslip.payroll_id == payroll_id
    ).all()
    
    if not payslips:
        # Log empty payslip list
        payroll_logger.log_activity(
            user_id=0,  # System activity
            action="get_payslip_list_empty",
            details={
                "payroll_id": payroll_id,
                "count": 0,
                "timestamp": datetime.now().isoformat()
            },
            log_to_db=True,
            log_to_file=True
        )
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
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="payslip_list_count",
        value=len(payslips),
        tags={"type": "payroll_payslips"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_PAYSHEET_LIST",
        description=f"Retrieved {len(payslips)} payslips for payroll: {payroll_id}",
        user_id=payroll.user_id,
        details={
            "payroll_id": payroll_id,
            "payslip_count": len(payslips)
        }
    )
    
    return payslip_list


# Performance monitoring endpoints
@router.get("/performance/stats")
def get_performance_stats(db: Session = Depends(get_db)):
    """Get performance statistics for payroll operations"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_performance_stats")
    
    # Log the get performance stats operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_performance_stats",
        details={
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Get performance statistics
    stats = payroll_performance_monitor.get_performance_stats()
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="performance_stats_count",
        value=1,
        tags={"type": "stats"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PERFORMANCE_STATS_RETRIEVED",
        description="Performance statistics retrieved for payroll operations",
        user_id=0,  # System activity
        details={
            "stats": stats
        }
    )
    
    return stats


@router.get("/performance/slow-operations")
def get_slow_operations(db: Session = Depends(get_db)):
    """Get slow operations for payroll performance analysis"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_slow_operations")
    
    # Log the get slow operations operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_slow_operations",
        details={
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Get slow operations
    slow_ops = payroll_performance_monitor.get_slow_operations()
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="slow_operations_count",
        value=len(slow_ops),
        tags={"type": "slow_ops"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="SLOW_OPERATIONS_RETRIEVED",
        description=f"Retrieved {len(slow_ops)} slow operations",
        user_id=0,  # System activity
        details={
            "slow_operations_count": len(slow_ops)
        }
    )
    
    return slow_ops


@router.get("/performance/export")
def export_performance_data(db: Session = Depends(get_db)):
    """Export performance data for payroll operations"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("export_performance_data")
    
    # Log the export performance data operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="export_performance_data",
        details={
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Export performance data
    export_data = payroll_performance_monitor.export_performance_data()
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="performance_export_count",
        value=1,
        tags={"type": "export"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PERFORMANCE_DATA_EXPORTED",
        description="Performance data exported for payroll operations",
        user_id=0,  # System activity
        details={
            "export_data_size": len(str(export_data))
        }
    )
    
    return export_data


# Log aggregation endpoints
@router.get("/logs/search")
def search_payroll_logs(
    query: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Search payroll logs"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("search_payroll_logs")
    
    # Log the search payroll logs operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="search_payroll_logs",
        details={
            "query": query,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Search logs
    results = payroll_log_aggregator.search_logs(query, limit, offset)
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="log_search_count",
        value=len(results),
        tags={"type": "search"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_LOGS_SEARCHED",
        description=f"Search performed on payroll logs: {query}",
        user_id=0,  # System activity
        details={
            "query": query,
            "results_count": len(results)
        }
    )
    
    return results


@router.get("/logs/stats")
def get_log_stats(db: Session = Depends(get_db)):
    """Get log statistics for payroll operations"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_log_stats")
    
    # Log the get log stats operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_log_stats",
        details={
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Get log statistics
    stats = payroll_log_aggregator.get_log_stats()
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="log_stats_count",
        value=1,
        tags={"type": "stats"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_LOG_STATS_RETRIEVED",
        description="Log statistics retrieved for payroll operations",
        user_id=0,  # System activity
        details={
            "stats": stats
        }
    )
    
    return stats


@router.get("/logs/user/{user_id}/activity")
def get_user_activity_summary(user_id: int, db: Session = Depends(get_db)):
    """Get user activity summary for payroll operations"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_user_activity_summary")
    
    # Log the get user activity summary operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_user_activity_summary",
        details={
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Get user activity summary
    summary = payroll_log_aggregator.get_user_activity_summary(user_id)
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="user_activity_count",
        value=1,
        tags={"type": "user_activity"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="USER_ACTIVITY_SUMMARY",
        description=f"User activity summary retrieved for user: {user_id}",
        user_id=user_id,
        details={
            "user_id": user_id,
            "activity_summary": summary
        }
    )
    
    return summary


@router.get("/logs/payroll/{payroll_id}/operations")
def get_payroll_operations_summary(payroll_id: int, db: Session = Depends(get_db)):
    """Get payroll operations summary"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("get_payroll_operations_summary")
    
    # Log the get payroll operations summary operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="get_payroll_operations_summary",
        details={
            "payroll_id": payroll_id,
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Get payroll operations summary
    summary = payroll_log_aggregator.get_payroll_operations_summary(payroll_id)
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="payroll_operations_count",
        value=1,
        tags={"type": "operations_summary"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_OPERATIONS_SUMMARY",
        description=f"Payroll operations summary retrieved for payroll: {payroll_id}",
        user_id=0,  # System activity
        details={
            "payroll_id": payroll_id,
            "operations_summary": summary
        }
    )
    
    return summary


@router.get("/logs/export")
def export_payroll_logs(db: Session = Depends(get_db)):
    """Export payroll logs"""
    # Start performance monitoring
    timer_id = performance_monitor.start_timer("export_payroll_logs")
    
    # Log the export payroll logs operation
    payroll_logger.log_activity(
        user_id=0,  # System activity
        action="export_payroll_logs",
        details={
            "timestamp": datetime.now().isoformat()
        },
        log_to_db=True,
        log_to_file=True
    )
    
    # Export payroll logs
    export_data = payroll_log_aggregator.export_logs()
    
    # Log performance metrics
    performance_monitor.stop_timer(timer_id)
    performance_monitor.record_counter(
        name="log_export_count",
        value=1,
        tags={"type": "export"},
        component="payroll_router"
    )
    
    # Log structured data for audit
    structured_logger.log_audit_event(
        event_type="PAYROLL_LOGS_EXPORTED",
        description="Payroll logs exported",
        user_id=0,  # System activity
        details={
            "export_data_size": len(str(export_data))
        }
    )
    
    return export_data