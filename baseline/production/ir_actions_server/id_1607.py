if record.x_studio_code and len(record.x_studio_lost_code) > 3:
    raise ValidationError("The code cannot exceed 3 characters.")