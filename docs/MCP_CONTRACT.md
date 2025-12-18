# MCP Tool Contract (Draft)

Purpose: unify request/response shapes for MCP servers, align with official MCP server SDK migration, and standardize error/mime handling.

## Conventions
- Protocol: MCP 2024-11-05.
- Transport: stdio (official MCP server SDK after migration).
- Content: prefer `mimeType: application/json`; text fallback only for human-readable errors.
- Error: use JSON object `{ "error": { "type": "<kind>", "message": "<detail>", "hint": "<optional>" } }` with `isError=true`.
- Success wrapper (SDK default): `content: [{ "type": "text", "text": "<json>", "mimeType": "application/json" }]`.
- Pagination: optional `limit` (int), default documented per tool.
- Locale/timezone: Asia/Seoul, date format `YYYY-MM-DD` unless source has explicit format.

## Common Types
- `Notice`: { title, url, date, author, source, views }
- `Classroom`: { code, building, room_number, floor, name, room_type, professor_name?, latitude?, longitude?, is_accessible? }
- `Course`: { code, name, professor, credits, time, classroom, classification }
- `Meal`: { cafeteria, meal_type, menu, price, menu_url?, source_url? }
- `Shuttle`: { route, departure, arrival, next_time?, note?, weekday_times?, weekend_times? }
- `CurriculumRequirement`: free-form JSON per program/year (server-defined), but must be valid JSON object.
- `SeatInfo`: { location, floor?, total, available, usage_rate }

## Tool Contracts (Request → Response)

### notice-mcp
- get_latest_notices
  - Req: { department: string (name or code), limit?: int }
  - Res: { notices: Notice[] }
- search_notices
  - Req: { query: string, limit?: int, department?: string (code) }
  - Res: { notices: Notice[] }
- crawl_fresh_notices
  - Req: { department: string (name or code), limit?: int, keyword?: string }
  - Res: { success: bool, department: string, crawled: int, new_count: int, keyword?: string }

### classroom-mcp
- search_classroom
  - Req: { query: string }
  - Res: { found: bool, rooms: Classroom[] }

### meal-mcp
- get_today_meal
  - Req: { meal_type?: "lunch" | "dinner" }
  - Res: { meals: Meal[] }
- search_meals
  - Req: { query: string }
  - Res: { meals: Meal[] }
- get_cafeteria_info
  - Req: { }
  - Res: { cafeterias: any }

### shuttle-mcp
- get_next_shuttle
  - Req: { route?: "to_station" | "to_campus" }
  - Res: Shuttle | { shuttles?: Shuttle[] }

### course-mcp
- search_courses
  - Req: { department?: string, keyword?: string }
  - Res: { courses: Course[], found: bool }

### curriculum-mcp
- search_curriculum
  - Req: { query: string, year?: string }
  - Res: { found: bool, courses: Course[] }
- get_curriculum_by_semester
  - Req: { semester: "1학기" | "2학기", year?: string }
  - Res: { found: bool, courses: Course[] }
- list_programs
  - Req: { year?: string }
  - Res: { programs: string[] }
- get_requirements
  - Req: { program: string, year: string }
  - Res: { requirements: any, found?: bool }
- evaluate_progress
  - Req: { program: string, year: string, taken_courses: string[] }
  - Res: { evaluation: any, found?: bool }

### library-mcp
- get_library_info
  - Req: { campus?: "seoul" | "global" }
  - Res: { library_info: any }
- get_seat_availability
  - Req: { campus?: "seoul" | "global" }
  - Res: { library_seats: SeatInfo[] }
- reserve_seat
  - Req: { room: string, seat_number?: string, username?: string, password?: string }
  - Res: { reservation: any, needs_login?: bool }

## Error Policy
- Always return JSON object with `error` key.
- Example: `{ "error": { "type": "NotFound", "message": "Department 'ime' not configured" } }`
- Network/parse errors: `{ "error": { "type": "UpstreamError", "message": "HTTP 502 from source" } }`

## Client Expectations
- Responses must be JSON-decodable; avoid mixing plain text and JSON in one response.
- `mimeType: application/json` preferred for predictable parsing.
- Tool names stay unchanged to avoid agent prompt drift.

## Next Actions (step 1 → 2)
- Validate each server’s current output against this contract and note diffs.
- When migrating to SDK, enforce `mimeType` and error shape above.
