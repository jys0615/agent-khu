#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
    ListResourcesRequestSchema,
    ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { scrapeKHUNotices, KHUNotice } from "./scraper.js";
import {
    cacheNotice,
    getCachedNotice,
    getAllCachedNotices,
    isCacheValid
} from "./cache.js";

/**
 * KHU Notice MCP Server
 * 경희대학교 공지사항 크롤링 MCP Server
 */
const server = new Server(
    {
        name: "khu-notice-mcp",
        version: "0.1.0",
    },
    {
        capabilities: {
            tools: {},
            resources: {},
        },
    }
);

/**
 * Tools 목록 제공
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "get_sw_notices",
                description: "경희대 SW중심대학사업단 공지사항 가져오기",
                inputSchema: {
                    type: "object",
                    properties: {
                        limit: {
                            type: "number",
                            description: "가져올 공지사항 수 (기본값: 10)",
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
                name: "get_department_notices",
                description: "소프트웨어융합대학 학과 공지사항 가져오기",
                inputSchema: {
                    type: "object",
                    properties: {
                        limit: {
                            type: "number",
                            description: "가져올 공지사항 수 (기본값: 10)",
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
                name: "get_academic_schedule",
                description: "경희대 학사일정 가져오기",
                inputSchema: {
                    type: "object",
                    properties: {
                        force_refresh: {
                            type: "boolean",
                            description: "캐시 무시하고 새로 크롤링 (기본값: false)",
                            default: false,
                        },
                    },
                },
            },
            {
                name: "search_notices",
                description: "경희대 공지사항 검색",
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

    if (name === "get_sw_notices") {
        const limit = (args?.limit as number) || 10;
        const forceRefresh = (args?.force_refresh as boolean) || false;

        try {
            let notices: KHUNotice[];

            // 캐시 확인
            if (!forceRefresh && await isCacheValid("swedu")) {
                console.error("📦 Using cached SW notices");
                notices = await getAllCachedNotices("swedu");
                notices = notices.slice(0, limit);
            } else {
                console.error(`🔄 Scraping SW중심대학사업단...`);
                notices = await scrapeKHUNotices("swedu", limit);

                // 캐시 저장
                for (const notice of notices) {
                    await cacheNotice("swedu", notice.id, notice);
                }
                console.error(`✅ Scraped ${notices.length} SW notices`);
            }

            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify(notices, null, 2),
                    },
                ],
            };
        } catch (error) {
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

    if (name === "get_department_notices") {
        const limit = (args?.limit as number) || 10;
        const forceRefresh = (args?.force_refresh as boolean) || false;

        try {
            let notices: KHUNotice[];

            if (!forceRefresh && await isCacheValid("department")) {
                console.error("📦 Using cached department notices");
                notices = await getAllCachedNotices("department");
                notices = notices.slice(0, limit);
            } else {
                console.error(`🔄 Scraping 소프트웨어융합대학...`);
                notices = await scrapeKHUNotices("department", limit);

                for (const notice of notices) {
                    await cacheNotice("department", notice.id, notice);
                }
                console.error(`✅ Scraped ${notices.length} department notices`);
            }

            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify(notices, null, 2),
                    },
                ],
            };
        } catch (error) {
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

    if (name === "get_academic_schedule") {
        const forceRefresh = (args?.force_refresh as boolean) || false;

        try {
            let schedules: KHUNotice[];

            if (!forceRefresh && await isCacheValid("schedule")) {
                console.error("📦 Using cached academic schedule");
                schedules = await getAllCachedNotices("schedule");
            } else {
                console.error(`🔄 Scraping 학사일정...`);
                schedules = await scrapeKHUNotices("schedule", 50);

                for (const schedule of schedules) {
                    await cacheNotice("schedule", schedule.id, schedule);
                }
                console.error(`✅ Scraped ${schedules.length} schedule items`);
            }

            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify(schedules, null, 2),
                    },
                ],
            };
        } catch (error) {
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

    if (name === "search_notices") {
        const query = (args?.query as string) || "";
        const limit = (args?.limit as number) || 5;

        try {
            const allNotices = [
                ...await getAllCachedNotices("swedu"),
                ...await getAllCachedNotices("department"),
                ...await getAllCachedNotices("schedule"),
            ];

            const results = allNotices.filter((notice) =>
                notice.title.toLowerCase().includes(query.toLowerCase()) ||
                notice.content.toLowerCase().includes(query.toLowerCase())
            ).slice(0, limit);

            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify(results, null, 2),
                    },
                ],
            };
        } catch (error) {
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
 * Resources 목록 제공
 */
server.setRequestHandler(ListResourcesRequestSchema, async () => {
    try {
        const allNotices = [
            ...await getAllCachedNotices("swedu"),
            ...await getAllCachedNotices("department"),
            ...await getAllCachedNotices("schedule"),
        ];

        return {
            resources: allNotices.map((notice) => ({
                uri: `khu://notices/${notice.source}/${notice.id}`,
                name: notice.title,
                description: `${notice.source} - ${notice.date}`,
                mimeType: "application/json",
            })),
        };
    } catch (error) {
        return { resources: [] };
    }
});

/**
 * Resource 읽기
 */
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const uri = request.params.uri;
    const match = uri.match(/^khu:\/\/notices\/(.+)\/(.+)$/);

    if (!match) {
        throw new Error(`Invalid URI: ${uri}`);
    }

    const [, source, noticeId] = match;
    const notice = await getCachedNotice(source, noticeId);

    if (!notice) {
        throw new Error(`Notice not found: ${uri}`);
    }

    return {
        contents: [
            {
                uri,
                mimeType: "application/json",
                text: JSON.stringify(notice, null, 2),
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
    console.error("KHU Notice MCP Server running on stdio");
}

main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
});