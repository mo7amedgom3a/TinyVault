from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.services.user_service import UserService
from app.services.item_service import ItemService
from app.utilities.dependencies import get_user_service, get_item_service, verify_admin_api_key
from app.schemas import UserResponse, ItemResponse

router = APIRouter(
    prefix="/admin", 
    tags=["admin"],
    responses={
        401: {"description": "Unauthorized - Invalid API key"},
        403: {"description": "Forbidden - Insufficient permissions"},
        500: {"description": "Internal server error"}
    }
)


@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(verify_admin_api_key)])
async def get_users(
    user_service: UserService = Depends(get_user_service)
):
    """Get all users with item counts.
    
    **Authentication Required**: Admin API key must be provided in X-API-Key header.
    
    Returns a list of all users with their associated item counts.
    """
    try:
        users_with_counts = await user_service.get_all_users_with_item_count()
        
        # Convert to response format
        response = []
        for user, item_count in users_with_counts:
            response.append(UserResponse(
                id=user.id,
                telegram_user_id=user.telegram_user_id,
                first_seen_at=user.first_seen_at,
                last_seen_at=user.last_seen_at,
                item_count=item_count
            ))
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/items", dependencies=[Depends(verify_admin_api_key)])
async def get_items(
    user_id: int = None,
    limit: int = 100,
    offset: int = 0,
    item_service: ItemService = Depends(get_item_service)
):
    """Get items with optional user filtering.
    
    **Authentication Required**: Admin API key must be provided in X-API-Key header.
    
    - **user_id**: Optional filter to get items for a specific user
    - **limit**: Maximum number of items to return (default: 100)
    - **offset**: Number of items to skip for pagination (default: 0)
    
    Returns paginated list of items with metadata.
    """
    try:
        if user_id:
            # Get items for specific user
            items = await item_service.get_user_items(user_id, limit)
        else:
            # Get all items
            items = await item_service.get_all_items(limit, offset)
        
        # Convert to response format
        response = []
        for item in items:
            response.append(ItemResponse(
                id=item.id,
                short_code=item.short_code,
                kind=item.kind,
                content=item.content,
                owner_user_id=item.owner_user_id,
                created_at=item.created_at,
                deleted_at=item.deleted_at
            ))
        
        return {
            "items": response,
            "total": len(response),
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve items: {str(e)}"
        )


@router.delete("/items/{short_code}", dependencies=[Depends(verify_admin_api_key)])
async def delete_item(
    short_code: str,
    item_service: ItemService = Depends(get_item_service)
):
    """Delete any item by short code.
    
    **Authentication Required**: Admin API key must be provided in X-API-Key header.
    
    - **short_code**: The unique short code of the item to delete
    
    This operation permanently removes the item from the database.
    """
    try:
        success = await item_service.hard_delete_item(short_code)
        
        if success:
            return {"message": f"Item {short_code} deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {short_code} not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete item: {str(e)}"
        )


@router.get("/stats", dependencies=[Depends(verify_admin_api_key)])
async def get_admin_stats(
    user_service: UserService = Depends(get_user_service),
    item_service: ItemService = Depends(get_item_service)
):
    """Get system-wide statistics.
    
    **Authentication Required**: Admin API key must be provided in X-API-Key header.
    
    Returns comprehensive system statistics including user counts, item counts,
    and activity metrics.
    """
    try:
        # Get user statistics
        users_with_counts = await user_service.get_all_users_with_item_count()
        total_users = len(users_with_counts)
        total_items = sum(count for _, count in users_with_counts)
        
        # Get active users (last 30 days)
        active_users = await user_service.get_active_users(30)
        active_user_count = len(active_users)
        
        return {
            "total_users": total_users,
            "total_items": total_items,
            "active_users_30_days": active_user_count,
            "average_items_per_user": round(total_items / total_users, 2) if total_users > 0 else 0
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        ) 