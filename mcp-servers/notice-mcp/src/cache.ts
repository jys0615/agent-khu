import fs from "fs/promises";
import path from "path";
import { homedir } from "os";
import { KHUNotice } from "./scraper.js";

const CACHE_DIR = path.join(homedir(), ".cache", "khu-notice-mcp");
const CACHE_TTL = 6 * 60 * 60 * 1000; // 6시간

/**
 * 캐시 디렉토리 초기화
 */
async function ensureCacheDir(source: string) {
    const sourceDir = path.join(CACHE_DIR, source);
    try {
        await fs.mkdir(sourceDir, { recursive: true });
    } catch (error) {
        // 이미 존재하면 무시
    }
    return sourceDir;
}

/**
 * 공지사항 캐시 저장
 */
export async function cacheNotice(source: string, noticeId: string, notice: KHUNotice): Promise<void> {
    const sourceDir = await ensureCacheDir(source);
    const filePath = path.join(sourceDir, `${noticeId}.json`);
    await fs.writeFile(filePath, JSON.stringify(notice, null, 2), "utf-8");

    // 인덱스 업데이트
    await updateCacheIndex(source);
}

/**
 * 캐시된 공지사항 읽기
 */
export async function getCachedNotice(source: string, noticeId: string): Promise<KHUNotice | null> {
    const sourceDir = path.join(CACHE_DIR, source);
    const filePath = path.join(sourceDir, `${noticeId}.json`);

    try {
        const content = await fs.readFile(filePath, "utf-8");
        return JSON.parse(content);
    } catch (error) {
        return null;
    }
}

/**
 * 모든 캐시된 공지사항 가져오기
 */
export async function getAllCachedNotices(source: string): Promise<KHUNotice[]> {
    const sourceDir = path.join(CACHE_DIR, source);
    const indexPath = path.join(sourceDir, "index.json");

    try {
        const indexContent = await fs.readFile(indexPath, "utf-8");
        const index = JSON.parse(indexContent);
        return index.notices || [];
    } catch (error) {
        return [];
    }
}

/**
 * 캐시 인덱스 업데이트
 */
async function updateCacheIndex(source: string): Promise<void> {
    const sourceDir = path.join(CACHE_DIR, source);

    try {
        const files = await fs.readdir(sourceDir);
        const noticeFiles = files.filter((f) => f.endsWith(".json") && f !== "index.json");

        const notices: KHUNotice[] = [];

        for (const file of noticeFiles) {
            try {
                const content = await fs.readFile(path.join(sourceDir, file), "utf-8");
                const notice = JSON.parse(content);
                notices.push(notice);
            } catch (error) {
                console.error(`Error reading ${file}:`, error);
            }
        }

        // 날짜순 정렬 (최신순)
        notices.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

        const indexPath = path.join(sourceDir, "index.json");
        await fs.writeFile(
            indexPath,
            JSON.stringify({ notices, updated_at: new Date().toISOString() }, null, 2),
            "utf-8"
        );
    } catch (error) {
        console.error("Error updating cache index:", error);
    }
}

/**
 * 캐시가 유효한지 확인
 */
export async function isCacheValid(source: string): Promise<boolean> {
    const sourceDir = path.join(CACHE_DIR, source);
    const indexPath = path.join(sourceDir, "index.json");

    try {
        const indexContent = await fs.readFile(indexPath, "utf-8");
        const index = JSON.parse(indexContent);

        if (!index.updated_at) {
            return false;
        }

        const updatedAt = new Date(index.updated_at).getTime();
        const now = Date.now();

        return (now - updatedAt) < CACHE_TTL;
    } catch (error) {
        return false;
    }
}

/**
 * 캐시 초기화
 */
export async function clearCache(source?: string): Promise<void> {
    try {
        if (source) {
            const sourceDir = path.join(CACHE_DIR, source);
            await fs.rm(sourceDir, { recursive: true, force: true });
        } else {
            await fs.rm(CACHE_DIR, { recursive: true, force: true });
        }
    } catch (error) {
        console.error("Error clearing cache:", error);
    }
}