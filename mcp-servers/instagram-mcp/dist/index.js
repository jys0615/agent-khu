#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema, ListResourcesRequestSchema, ReadResourceRequestSchema, } from "@modelcontextprotocol/sdk/types.js";
import { scrapeInstagram } from "./scraper.js";
import { cachePost, getCachedPost, getAllCachedPosts, isCacheValid } from "./cache.js";
const ACCOUNT_NAME = "khu_sw.union";
/**
 * Instagram MCP Server
 * 경희대 소프트웨어융합대학 인스타그램 게시물을 MCP로 제공
 */
const server = new Server({
    name: "instagram-mcp",
    version: "0.1.0",
}, {
    capabilities: {
        tools: {},
        resources: {},
    },
});
/**
 * Tools 목록 제공
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "get_instagram_posts",
                description: `경희대 소프트웨어융합대학(${ACCOUNT_NAME}) 인스타그램 최근 게시물 가져오기`,
                inputSchema: {
                    type: "object",
                    properties: {
                        limit: {
                            type: "number",
                            description: "가져올 게시물 수 (기본값: 10)",
                            default: 10,
                        },
                        force_refresh: {
                            type: "boolean",
                            description: "캐시 무시하고 새로 크롤링 (기본값: false)",
                            default: false,
                        },
                    },
                },
            },
            {
                name: "search_posts",
                description: "인스타그램 게시물에서 키워드 검색",
                inputSchema: {
                    type: "object",
                    properties: {
                        query: {
                            type: "string",
                            description: "검색할 키워드",
                        },
                        limit: {
                            type: "number",
                            description: "최대 결과 수 (기본값: 5)",
                            default: 5,
                        },
                    },
                    required: ["query"],
                },
            },
        ],
    };
});
/**
 * Tool 실행
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    if (name === "get_instagram_posts") {
        const limit = args?.limit || 10;
        const forceRefresh = args?.force_refresh || false;
        try {
            let posts;
            // 캐시 확인
            if (!forceRefresh && await isCacheValid()) {
                console.error("📦 Using cached posts");
                posts = await getAllCachedPosts();
                posts = posts.slice(0, limit);
            }
            else {
                console.error(`🔄 Scraping ${ACCOUNT_NAME}...`);
                posts = await scrapeInstagram(ACCOUNT_NAME, limit);
                // 캐시 저장
                for (const post of posts) {
                    await cachePost(post.id, post);
                }
                console.error(`✅ Scraped ${posts.length} posts`);
            }
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify(posts, null, 2),
                    },
                ],
            };
        }
        catch (error) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Error: ${error instanceof Error ? error.message : String(error)}`,
                    },
                ],
                isError: true,
            };
        }
    }
    if (name === "search_posts") {
        const query = args?.query || "";
        const limit = args?.limit || 5;
        try {
            const allPosts = await getAllCachedPosts();
            const results = allPosts.filter((post) => post.caption.toLowerCase().includes(query.toLowerCase())).slice(0, limit);
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify(results, null, 2),
                    },
                ],
            };
        }
        catch (error) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Error: ${error instanceof Error ? error.message : String(error)}`,
                    },
                ],
                isError: true,
            };
        }
    }
    throw new Error(`Unknown tool: ${name}`);
});
/**
 * Resources 목록 제공 (캐시된 게시물들)
 */
server.setRequestHandler(ListResourcesRequestSchema, async () => {
    try {
        const posts = await getAllCachedPosts();
        return {
            resources: posts.map((post) => ({
                uri: `instagram://khu_sw.union/${post.id}`,
                name: post.caption.substring(0, 50) + "...",
                description: `Posted at ${post.posted_at}`,
                mimeType: "application/json",
            })),
        };
    }
    catch (error) {
        return { resources: [] };
    }
});
/**
 * Resource 읽기
 */
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const uri = request.params.uri;
    const match = uri.match(/^instagram:\/\/khu_sw\.union\/(.+)$/);
    if (!match) {
        throw new Error(`Invalid URI: ${uri}`);
    }
    const postId = match[1];
    const post = await getCachedPost(postId);
    if (!post) {
        throw new Error(`Post not found: ${postId}`);
    }
    return {
        contents: [
            {
                uri,
                mimeType: "application/json",
                text: JSON.stringify(post, null, 2),
            },
        ],
    };
});
/**
 * 서버 시작
 */
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("Instagram MCP Server running on stdio");
}
main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
});
