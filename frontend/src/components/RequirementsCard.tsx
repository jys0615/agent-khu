// frontend/src/components/RequirementsCard.tsx
import React from 'react';
import type { Requirements } from '../api/chat';

type Props = { data: Requirements };

const RequirementsCard: React.FC<Props> = ({ data }) => {
    const { program, year, total_credits, groups = [], policies } = data;

    return (
        <div className="w-full rounded-2xl shadow p-4 sm:p-6 bg-white border border-gray-100">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">
                    졸업요건 · {program} · {year}
                </h3>
                {typeof total_credits === 'number' && (
                    <span className="text-sm text-gray-500">총 이수학점: {total_credits}</span>
                )}
            </div>

            <div className="space-y-3">
                {groups.map((g) => (
                    <div key={g.key} className="rounded-xl border border-gray-200 p-3">
                        <div className="flex items-center justify-between">
                            <div className="font-medium">
                                {g.name || g.key}
                            </div>
                            <div className="text-sm text-gray-600">
                                최소 {g.min_credits}학점
                            </div>
                        </div>

                        {g.required_courses && g.required_courses.length > 0 && (
                            <div className="mt-2 text-sm">
                                <div className="text-gray-500 mb-1">필수 과목</div>
                                <div className="flex flex-wrap gap-2">
                                    {g.required_courses.map((c) => (
                                        <span key={c} className="px-2 py-1 bg-gray-100 rounded-full text-xs">
                                            {c}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {g.any_of && g.any_of.length > 0 && (
                            <div className="mt-2 text-sm">
                                <div className="text-gray-500 mb-1">택1(이상) 그룹</div>
                                <div className="space-y-1">
                                    {g.any_of.map((block, i) => (
                                        <div key={i} className="flex flex-wrap gap-2">
                                            {block.map((opt) => (
                                                <span key={opt} className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs">
                                                    {opt}
                                                </span>
                                            ))}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {policies && (
                <div className="mt-4 text-sm text-gray-700">
                    {typeof policies.english_major_courses_required === 'number' && (
                        <div>전공 영어강좌: 최소 {policies.english_major_courses_required}과목</div>
                    )}
                </div>
            )}
        </div>
    );
};

export default RequirementsCard;