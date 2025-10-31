from fastapi import APIRouter, HTTPException, Query
from backend.app.core.config import settings
from backend.app.services.word_extractor import WordExtractor
from backend.app.services.utils import safe_float_convert, safe_str_convert
from backend.app.schemas.text_schemas import TextRequest, TextResponse
from backend.app.schemas.db_schemas import TestResultCreate, UserCreate
from backend.app.db.dependencies import SessionDependency
from backend.app.db.repositories import UserRepository, TestResultRepository
from backend.app.services.progress_calculator import UserProgressCalculator
from backend.app.core.logger import error_logger, request_logger


router = APIRouter()


@router.get(
    "/text",
    response_model=TextResponse,
)
async def get_random_text(
    lang: str = Query(default="ru", description="Язык текста"),
    difficulty: str = Query(default="easy", description="Уровень сложности"),
):
    try:
        request_logger.info(f"Text request: lang={lang}, difficulty={difficulty}")
        request = TextRequest(lang=lang, difficulty=difficulty)

        config = settings.text_generation_config[request.lang][request.difficulty]

        word_extractor = WordExtractor(
            filepath=settings.language_filepath[request.lang],
            count_words=int(config["count_words"]),
            level=str(config["level"]),
        )

        generated_text = word_extractor.generate_random_text()

        return TextResponse(
            text=generated_text,
            language=request.lang,
            difficulty=request.difficulty,
        )

    except Exception as e:
        error_logger.error(f"Error in get_random_text: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-result")
async def save_test_result(
    test_data: dict[str, str | int | float | None],
    session: SessionDependency,
):
    try:
        request_logger.info(f"Test result request: {test_data}")
        user_repo = UserRepository(session)
        test_result_repo = TestResultRepository(session)
        user_id = test_data.get("user_id")

        if user_id in (None, "anonymous", ""):
            user = await user_repo.create(UserCreate())
            user_id = user.id
        else:
            user = await user_repo.get_by_id(str(user_id))
            if not user:
                user = await user_repo.create(UserCreate())
                user_id = user.id

        test_result_data = TestResultCreate(
            user_id=str(user_id),
            chars_per_minute=safe_float_convert(
                test_data.get(settings.chars_per_minute)
            ),
            accuracy=safe_float_convert(test_data.get(settings.accuracy)),
            time_seconds=safe_float_convert(test_data.get(settings.time_seconds)),
            language=safe_str_convert(test_data.get(settings.language)),
            difficulty=safe_str_convert(test_data.get(settings.difficulty)),
        )
        test_result = await test_result_repo.create(test_result_data)

        return {"user_id": user_id, "test_result_id": test_result.id}

    except ValueError as e:
        error_logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Incorrect data: {str(e)}")

    except Exception as e:
        error_logger.error(f"Error in save_test_result: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Save error: {str(e)}")


@router.get(
    "/statistics/{user_id}",
)
async def get_user_test_statistics(user_id: str, session: SessionDependency):
    test_result_repo = TestResultRepository(session)
    try:
        all_test_results = await test_result_repo.get_by_user_id(user_id)
        if not all_test_results:
            error_logger.warning("No statistics found for this user")
            raise HTTPException(
                status_code=404, detail="No statistics found for this user"
            )

        last_result = await test_result_repo.get_last_result_by_user_id(user_id)
        best_performance = await test_result_repo.get_user_best_performance(user_id)
        avg_statistics = await test_result_repo.get_user_test_result_statistics(user_id)
        progress_metrics = await UserProgressCalculator.calculate_progress(
            all_test_results
        )

        return {
            "last_result": last_result,
            "best_performance": best_performance,
            "avg_statistics": avg_statistics,
            "progress_metrics": progress_metrics,
            "all_test_results": all_test_results,
        }

    except Exception as e:
        error_logger.error(
            f"Error in get_user_test_statistics: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Internal server error when receiving statistics"
        )
