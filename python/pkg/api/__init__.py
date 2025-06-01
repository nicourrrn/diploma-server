from .fund import fund_router
from .recipient import recipient_router
from .requirement import requirement_router
from .volunteer import volunteer_router
from .profile import profile_router


__all__ = [
    "fund_router",
    "recipient_router",
    "requirement_router",
    "volunteer_router",
    "profile_router",
]

# @router.get("/items")
# async def get_items_endpoint(req: Request, query: str = "") -> list[Item]:
#     db = req.app.state.db
#     try:
#         items = await (get_items(db, query) if query != "" else get_items(db))
#     except DatabaseException as e:
#         raise HTTPException(status_code=404, detail=str(e))
#
#     return items
