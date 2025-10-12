"""
공지사항 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, crud
from ..database import get_db
from ..mcp_client import instagram_mcp_client

router = APIRouter(
    prefix="/api/notices",
    tags=["notices"]
)


@router.get("", response_model=List[schemas.Notice])
async def get_notices(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    최신 공지사항 목록 조회
    """
    notices = crud.get_latest_notices(db, limit=limit)
    return notices


@router.get("/search", response_model=List[schemas.Notice])
async def search_notices(
    query: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    공지사항 검색
    """
    notices = crud.search_notices(db, query=query, limit=limit)
    return notices


@router.post("/sync", response_model=dict)
async def sync_instagram(
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Instagram에서 최신 게시물 동기화
    """
    try:
        # MCP Server에서 게시물 가져오기
        posts = await instagram_mcp_client.get_posts(
            limit=20,
            force_refresh=force_refresh
        )
        
        created_count = 0
        for post in posts:
            notice = crud.create_notice_from_instagram(db, post)
            if notice:
                created_count += 1
        
        return {
            "status": "success",
            "fetched": len(posts),
            "created": created_count,
            "message": f"{created_count}개의 새로운 공지사항이 추가되었습니다."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notice_id}", response_model=schemas.Notice)
async def get_notice(
    notice_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 공지사항 조회
    """
    notice = db.query(crud.models.Notice).filter(
        crud.models.Notice.id == notice_id
    ).first()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    return notice