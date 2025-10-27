import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export interface KHUNotice {
    id: string;
    source: string;
    title: string;
    content: string;
    url: string;
    date: string;
    author?: string;
    views?: number;
}

/**
 * Python 스크립트를 실행하여 경희대 공지사항 크롤링
 */
export async function scrapeKHUNotices(
    source: "swedu" | "department" | "schedule",
    limit: number
): Promise<KHUNotice[]> {
    return new Promise((resolve, reject) => {
        const pythonScript = join(__dirname, "../scrapers/khu_scraper.py");

        const python = spawn("python3", [pythonScript, source, limit.toString()]);

        let stdout = "";
        let stderr = "";

        python.stdout.on("data", (data) => {
            stdout += data.toString();
        });

        python.stderr.on("data", (data) => {
            stderr += data.toString();
        });

        python.on("close", (code) => {
            if (code !== 0) {
                reject(new Error(`Python script failed: ${stderr}`));
                return;
            }

            try {
                const notices = JSON.parse(stdout);
                resolve(notices);
            } catch (error) {
                reject(new Error(`Failed to parse JSON: ${stdout}`));
            }
        });

        python.on("error", (error) => {
            reject(new Error(`Failed to spawn Python: ${error.message}`));
        });
    });
}