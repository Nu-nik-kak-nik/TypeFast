from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class DatabaseException(HTTPException):
    def __init__(self, detail: str, original_error: Exception | None = None):
        error_msg = f"Database error: {detail}"
        if original_error:
            error_msg += f" | Original error: {str(original_error)}"

        logger.error(
            error_msg,
            extra={
                "error_type": "database",
                "original_error": str(original_error) if original_error else None,
                "error_class": original_error.__class__.__name__
                if original_error
                else None,
            },
            exc_info=original_error,
        )

        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )


class NotFoundException(HTTPException):
    def __init__(self, entity: str, entity_id: str):
        detail = f"{entity} with id '{entity_id}' not found"

        logger.warning(
            detail,
            extra={"error_type": "not_found", "entity": entity, "entity_id": entity_id},
        )

        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
