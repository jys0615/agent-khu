import { InstagramPost } from "./scraper.js";
/**
 * 게시물 캐시 저장
 */
export declare function cachePost(postId: string, post: InstagramPost): Promise<void>;
/**
 * 캐시된 게시물 읽기
 */
export declare function getCachedPost(postId: string): Promise<InstagramPost | null>;
/**
 * 모든 캐시된 게시물 가져오기
 */
export declare function getAllCachedPosts(): Promise<InstagramPost[]>;
/**
 * 캐시가 유효한지 확인
 */
export declare function isCacheValid(): Promise<boolean>;
/**
 * 캐시 초기화
 */
export declare function clearCache(): Promise<void>;
