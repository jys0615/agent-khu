export interface InstagramPost {
    id: string;
    shortcode: string;
    caption: string;
    url: string;
    image_url: string;
    posted_at: string;
    likes?: number;
    comments?: number;
}
/**
 * Python 스크립트를 실행하여 Instagram 크롤링
 */
export declare function scrapeInstagram(account: string, limit: number): Promise<InstagramPost[]>;
