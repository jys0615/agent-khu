import fs from "fs/promises";
import path from "path";
import { homedir } from "os";
const CACHE_DIR = path.join(homedir(), ".cache", "instagram-mcp", "khu_sw.union");
const CACHE_INDEX = path.join(CACHE_DIR, "index.json");
const CACHE_TTL = 24 * 60 * 60 * 1000; // 24시간
/**
 * 캐시 디렉토리 초기화
 */
async function ensureCacheDir() {
    try {
        await fs.mkdir(CACHE_DIR, { recursive: true });
    }
    catch (error) {
        // 이미 존재하면 무시
    }
}
/**
 * 게시물 캐시 저장
 */
export async function cachePost(postId, post) {
    await ensureCacheDir();
    const filePath = path.join(CACHE_DIR, `${postId}.json`);
    await fs.writeFile(filePath, JSON.stringify(post, null, 2), "utf-8");
    // 인덱스 업데이트
    await updateCacheIndex();
}
/**
 * 캐시된 게시물 읽기
 */
export async function getCachedPost(postId) {
    const filePath = path.join(CACHE_DIR, `${postId}.json`);
    try {
        const content = await fs.readFile(filePath, "utf-8");
        return JSON.parse(content);
    }
    catch (error) {
        return null;
    }
}
/**
 * 모든 캐시된 게시물 가져오기
 */
export async function getAllCachedPosts() {
    await ensureCacheDir();
    try {
        const indexContent = await fs.readFile(CACHE_INDEX, "utf-8");
        const index = JSON.parse(indexContent);
        return index.posts || [];
    }
    catch (error) {
        return [];
    }
}
/**
 * 캐시 인덱스 업데이트
 */
async function updateCacheIndex() {
    const files = await fs.readdir(CACHE_DIR);
    const postFiles = files.filter((f) => f.endsWith(".json") && f !== "index.json");
    const posts = [];
    for (const file of postFiles) {
        try {
            const content = await fs.readFile(path.join(CACHE_DIR, file), "utf-8");
            const post = JSON.parse(content);
            posts.push(post);
        }
        catch (error) {
            console.error(`Error reading ${file}:`, error);
        }
    }
    // 날짜순 정렬 (최신순)
    posts.sort((a, b) => new Date(b.posted_at).getTime() - new Date(a.posted_at).getTime());
    await fs.writeFile(CACHE_INDEX, JSON.stringify({ posts, updated_at: new Date().toISOString() }, null, 2), "utf-8");
}
/**
 * 캐시가 유효한지 확인
 */
export async function isCacheValid() {
    try {
        const indexContent = await fs.readFile(CACHE_INDEX, "utf-8");
        const index = JSON.parse(indexContent);
        if (!index.updated_at) {
            return false;
        }
        const updatedAt = new Date(index.updated_at).getTime();
        const now = Date.now();
        return (now - updatedAt) < CACHE_TTL;
    }
    catch (error) {
        return false;
    }
}
/**
 * 캐시 초기화
 */
export async function clearCache() {
    try {
        await fs.rm(CACHE_DIR, { recursive: true, force: true });
    }
    catch (error) {
        console.error("Error clearing cache:", error);
    }
}
