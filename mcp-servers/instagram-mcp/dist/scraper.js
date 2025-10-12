import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
/**
 * Python 스크립트를 실행하여 Instagram 크롤링
 */
export async function scrapeInstagram(account, limit) {
    return new Promise((resolve, reject) => {
        const pythonScript = join(__dirname, "../scrapers/instagram_scraper.py");
        const python = spawn("python3", [pythonScript, account, limit.toString()]);
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
                const posts = JSON.parse(stdout);
                resolve(posts);
            }
            catch (error) {
                reject(new Error(`Failed to parse JSON: ${stdout}`));
            }
        });
        python.on("error", (error) => {
            reject(new Error(`Failed to spawn Python: ${error.message}`));
        });
    });
}
