import React, { useState } from 'react';
import { SEBIComplianceRecord } from '../types/terminal';
import { ShieldCheck, Copy, Check, FileCheck2, Lock } from 'lucide-react';

interface SEBIComplianceStampProps {
  compliance: SEBIComplianceRecord;
}

export const SEBIComplianceStamp: React.FC<SEBIComplianceStampProps> = ({ compliance }) => {
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(compliance.immutableReportHashSha256);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border border-[#223044] bg-[#0C111A] p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#1E293B]">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold tracking-wider text-slate-100 uppercase font-mono">
            SEBI (Research Analysts) Regulations, 2014 Compliance Audit Ledger
          </h2>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-xs text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
          <Lock className="w-3 h-3 text-emerald-400" />
          <span>IMMUTABLE TRIGGER LOCKED</span>
        </div>
      </div>

      {/* Main Ledger Credentials */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Registration Identifier</span>
          <div className="text-xs font-bold font-mono text-slate-200">
            {compliance.researchAnalystRegNo}
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Statutory accredited RA entity</span>
        </div>

        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Analyst / Engine Certification</span>
          <div className="text-xs font-bold font-mono text-slate-200">
            {compliance.analystName}
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Automated Econometric Calibration</span>
        </div>

        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Audit Ledger Timestamp</span>
          <div className="text-xs font-bold font-mono text-cyan-300">
            {compliance.verificationTimestamp}
          </div>
          <span className="text-[10px] text-slate-500 font-mono">ISO 8601 UTC Ground Truth</span>
        </div>
      </div>

      {/* Cryptographic SHA-256 Hash Box */}
      <div className="p-3 rounded bg-[#090D12] border border-[#223044] space-y-2">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400 flex items-center gap-1.5">
            <FileCheck2 className="w-3.5 h-3.5 text-cyan-400" />
            IMMUTABLE REPORT SHA-256 DIGEST:
          </span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#151D2A] border border-[#223044] hover:border-slate-500 text-[11px] text-slate-300 cursor-pointer transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-400">COPIED</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3 text-slate-400" />
                <span>COPY SHA-256</span>
              </>
            )}
          </button>
        </div>
        <div className="font-mono text-xs text-cyan-400/90 break-all p-2 rounded bg-[#070A0F] border border-[#1A2333]">
          {compliance.immutableReportHashSha256}
        </div>
      </div>

      {/* Statutory Disclosures & Standards Reference */}
      <div className="text-[11px] text-slate-400 space-y-1.5 font-sans leading-relaxed pt-1">
        <p>
          <strong className="text-slate-300">Statutory Compliance Disclosures:</strong> This valuation intelligence report is prepared under the framework of SEBI (Research Analysts) Regulations, 2014 and SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018.
        </p>
        <p className="text-slate-500 text-[10px] font-mono">
          REGULATORY CITATIONS: {compliance.regulationReferences.join(' | ')}
        </p>
      </div>
    </div>
  );
};
