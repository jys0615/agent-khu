import React from 'react';

interface MealCardProps {
    meal: {
        cafeteria: string;
        meal_type: string;
        menu: string;
        price: number;
        source_url?: string;
        menu_url?: string;
    };
}

const MealCard: React.FC<MealCardProps> = ({ meal }) => {
    const mealTypeLabels: { [key: string]: { label: string; icon: string; color: string } } = {
        breakfast: { label: '조식', icon: '🌅', color: 'bg-orange-100 text-orange-700' },
        lunch: { label: '중식', icon: '☀️', color: 'bg-yellow-100 text-yellow-700' },
        dinner: { label: '석식', icon: '🌙', color: 'bg-blue-100 text-blue-700' },
    };

    const mealInfo = mealTypeLabels[meal.meal_type] || mealTypeLabels['lunch'];

    const rawUrl = meal.source_url || meal.menu_url || '';
    const normalizedUrl = rawUrl && !/^https?:\/\//i.test(rawUrl) ? `https://${rawUrl}` : rawUrl;

    return (
        <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            {/* 상단: 식당명 + 식사 종류 */}
            <div className="flex items-center justify-between mb-3">
                <h4 className="text-base font-bold text-gray-800">{meal.cafeteria}</h4>
                <span className={`text-xs px-3 py-1 rounded-full ${mealInfo.color} font-medium`}>
                    {mealInfo.icon} {mealInfo.label}
                </span>
            </div>

            {/* 메뉴 */}
            <div className="mb-3">
                <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
                    {meal.menu}
                </p>
            </div>

            {/* 가격 */}
            {meal.price > 0 && (
                <div className="flex items-center justify-end">
                    <span className="text-sm font-semibold text-green-600">
                        💰 {meal.price.toLocaleString()}원
                    </span>
                </div>
            )}

            {/* 원본 링크 버튼 */}
            {normalizedUrl && (
                <div className="mt-3 flex justify-end">
                    <a
                        href={normalizedUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs px-3 py-1 rounded-md bg-khu-primary text-white hover:bg-khu-red-600 transition-colors"
                    >
                        원본 메뉴표 보기 ↗
                    </a>
                </div>
            )}
        </div>
    );
};

export default MealCard;