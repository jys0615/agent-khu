import React from 'react';

interface MealCardProps {
    meal: {
        cafeteria: string;
        meal_type: string;
        menu: string;
        price: number;
    };
}

const MealCard: React.FC<MealCardProps> = ({ meal }) => {
    const mealTypeLabels: { [key: string]: { label: string; icon: string; color: string } } = {
        breakfast: { label: '조식', icon: '🌅', color: 'bg-orange-100 text-orange-700' },
        lunch: { label: '중식', icon: '☀️', color: 'bg-yellow-100 text-yellow-700' },
        dinner: { label: '석식', icon: '🌙', color: 'bg-blue-100 text-blue-700' },
    };

    const mealInfo = mealTypeLabels[meal.meal_type] || mealTypeLabels['lunch'];

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
        </div>
    );
};

export default MealCard;