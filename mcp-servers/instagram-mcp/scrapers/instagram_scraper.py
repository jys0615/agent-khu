#!/usr/bin/env python3
"""
Instagram Scraper using Instaloader
경희대 소프트웨어융합대학 인스타그램 크롤러
"""

import sys
import json
from datetime import datetime
import instaloader

def scrape_instagram(account: str, limit: int = 10):
    """
    Instagram 계정에서 게시물 크롤링
    """
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True
    )
    
    try:
        profile = instaloader.Profile.from_username(loader.context, account)
        posts = []
        
        for post in profile.get_posts():
            if len(posts) >= limit:
                break
            
            # 게시물 정보 추출
            post_data = {
                "id": str(post.mediaid),
                "shortcode": post.shortcode,
                "caption": post.caption or "",
                "url": f"https://instagram.com/p/{post.shortcode}",
                "image_url": post.url,
                "posted_at": post.date_utc.isoformat(),
                "likes": post.likes,
                "comments": post.comments
            }
            
            posts.append(post_data)
        
        return posts
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: instagram_scraper.py <account> <limit>", file=sys.stderr)
        sys.exit(1)
    
    account = sys.argv[1]
    limit = int(sys.argv[2])
    
    posts = scrape_instagram(account, limit)
    print(json.dumps(posts, ensure_ascii=False, indent=2))