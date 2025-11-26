// frontend/src/components/EvaluationCard.tsx
import React from 'react';
import type { Evaluation } from '../api/chat';

type Props = { data: Evaluation };

const Badge: React.FC<{ ok: boolean; label?: string }> = ({ ok, label }) => (
    <span
        className={`px-2 py-1 rounded-full text-xs ${ok ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}
    >
        {label || (ok ? '충족' : '미충족')}
    </span>
);

const EvaluationCard: React.FC<Props> = ({ data }) => {
    const { program, year, ok, groups = [], totals, policies, evaluated_at } = data;

    return (
        <div className="w-full rounded-2xl shadow p-4 sm:p-6 bg-white border border-gray-100">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">
                    졸업 충족도 · {program} · {year}
                </h3>
                <Badge ok={ok} />
            </div>

            <div className="space-y-3">
                {groups.map((g) => (
                    <div key={g.group} className="rounded-xl border border-gray-200 p-3">
                        <div className="flex items-center justify-between">
                            <div className="font-medium">{g.group}</div>
                            <Badge ok={g.ok} />
                        </div>
                        <div className="mt-2 text-sm text-gray-700">
                            <div>학점: {g.earned_credits} / {g.min_credits}</div>
                            {g.missing_required && g.missing_required.length > 0 && (
                                <div className="mt-1">
                                    <div className="text-gray-500">미이수 필수</div>
                                    <div className="flex flex-wrap gap-2 mt-1">
                                        {g.missing_required.map((c) => (
                                            <span key={c} className="px-2 py-1 bg-rose-50 text-rose-700 rounded-full text-xs">
                                                {c}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {g.any_of && g.any_of.length > 0 && (
                                <div className="mt-2">
                                    <div className="text-gray-500 text-sm">택1(이상) 그룹</div>
                                    <div className="space-y-1 mt-1">
                                        {g.any_of.map((block, i) => (
                                            <div key={i} className="flex flex-wrap gap-2">
                                                {block.options.map((opt) => (
                                                    <span key={opt} className={`px-2 py-1 rounded-full text-xs ${block.ok ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-600'
                                                        }`}>
                                                        {opt}
                                                    </span>
                                                ))}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {(totals || policies) && (
                <div className="mt-4 grid sm:grid-cols-2 gap-3 text-sm">
                    {totals && (
                        <div className="rounded-xl bg-gray-50 p-3">
                            <div className="text-gray-500 mb-1">총합</div>
                            <div>요구 학점 합계: {totals.required_credits_sum ?? '-'}</div>
                            <div>이수 학점 합계: {totals.earned_credits_sum ?? '-'}</div>
                        </div>
                    )}
                    {policies && (
                        <div className="rounded-xl bg-gray-50 p-3">
                            <div className="text-gray-500 mb-1">정책</div>
                            {typeof policies.english_required === 'number' && (
                                <div>영어강좌: {policies.english_earned ?? 0} / {policies.english_required} {policies.english_ok ? '✅' : '❌'}</div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {evaluated_at && (
                <div className="mt-3 text-xs text-gray-400">평가시각: {new Date(evaluated_at).toLocaleString()}</div>
            )}
        </div>
    );
};

export default EvaluationCard;