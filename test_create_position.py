from backend.database import get_db
from backend.models import Position, Department

db = next(get_db())

try:
    # Get department to make sure it exists
    dept = db.query(Department).filter(Department.department_id == 1).first()
    if not dept:
        print('Department with ID 1 not found!')
    else:
        print(f'Department found: ID {dept.department_id}, Name {dept.department_name}')
    
    # Try to create a position
    new_position = Position(
        position_name="Test Position",
        description="Test Description",
        department_id=1
    )
    
    db.add(new_position)
    db.commit()
    db.refresh(new_position)
    
    print(f'Successfully created position: ID {new_position.position_id}, Name {new_position.position_name}')
    
except Exception as e:
    print(f'Error creating position: {str(e)}')
    db.rollback()

finally:
    db.close()