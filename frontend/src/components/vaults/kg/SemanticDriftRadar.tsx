import React from 'react';

interface SemanticDriftRadarProps {
  chapterDriftScores: Record<string, number>;
  overallObfuscationIndex: number;
}

export const SemanticDriftRadar: React.FC<SemanticDriftRadarProps> = ({
  chapterDriftScores,
  overallObfuscationIndex
}) => {
  const chapters = Object.entries(chapterDriftScores);
  const maxScore = Math.max(...Object.values(chapterDriftScores), 1.0);

  return (
    <div className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-lg text-purple-400">
            📊
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
                SEBI ICDR Schedule VI Semantic Drift Distribution
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-mono border border-purple-500/30">
                11 CHAPTERS
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Aggregated disclosure churn and physical page displacement across statutory chapters
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl">
          <span className="text-[11px] font-mono text-slate-400">Cohen-Malloy Evasion Index:</span>
          <span
            className={`text-xs font-bold font-mono px-2 py-0.5 rounded ${
              overallObfuscationIndex > 0.6
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                : overallObfuscationIndex > 0.3
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
            }`}
          >
            {(overallObfuscationIndex * 100).toFixed(1)}% Evasion Score
          </span>
        </div>
      </div>

      {/* Chapters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {chapters.map(([chapterKey, score]) => {
          const cleanName = chapterKey
            .replace('CHAPTER_', '')
            .split('_')
            .map((w, i) => (i === 0 ? `Ch. ${w}:` : w.charAt(0) + w.slice(1).toLowerCase()))
            .join(' ');

          const pct = Math.min(100, Math.round((score / maxScore) * 100));
          const isHighDrift = score > 30.0;
          const isModerateDrift = score > 10.0 && score <= 30.0;

          return (
            <div
              key={chapterKey}
              className={`p-3 rounded-xl border flex flex-col justify-between space-y-2 ${
                isHighDrift
                  ? 'bg-rose-950/20 border-rose-500/30'
                  : isModerateDrift
                  ? 'bg-amber-950/20 border-amber-500/30'
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-200 truncate pr-2" title={cleanName}>
                  {cleanName}
                </span>
                <span
                  className={`text-[11px] font-mono font-bold ${
                    isHighDrift ? 'text-rose-400' : isModerateDrift ? 'text-amber-400' : 'text-slate-400'
                  }`}
                >
                  {score.toFixed(1)} pts
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isHighDrift
                      ? 'bg-gradient-to-r from-rose-500 to-amber-500'
                      : isModerateDrift
                      ? 'bg-amber-500'
                      : 'bg-emerald-500'
                  }`}
                  style={{ width: `${Math.max(4, pct)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
