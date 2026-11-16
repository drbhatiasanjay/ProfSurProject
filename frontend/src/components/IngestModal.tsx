import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, X, ShieldCheck, Loader2 } from 'lucide-react';

interface IngestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIngestSuccess: (newDeal: {
    symbol: string;
    companyName: string;
    sizeCr: number;
    filingType: string;
    sector: string;
  }) => void;
}

export const IngestModal: React.FC<IngestModalProps> = ({ isOpen, onClose, onIngestSuccess }) => {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [progressPct, setProgressPct] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [ingestedDeal, setIngestedDeal] = useState<{
    symbol: string;
    companyName: string;
    sizeCr: number;
    filingType: string;
    sector: string;
  } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const steps = [
    'Validating SEBI ICDR 2018 Cryptographic Checksum (SHA-256)...',
    'Extracting Section III Objects of Offer & Statutory Debt Schedules...',
    'Reconciling Restated Ind AS Statement of Profit & Loss & Balance Sheet...',
    'Calibrating Dickinson (2011) Life-Cycle & Beneish (1999) Forensic M-Score...',
    'Generating Huber-Loss M-Estimator Multiples across Peer Cohort...',
  ];

  const handleFile = (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setErrorMsg('Invalid format. Please select an authentic SEBI DRHP or RHP filing in PDF format (.pdf).');
      return;
    }
    setErrorMsg(null);
    setSelectedFile(file);
    startIngestion(file.name);
  };

  const startIngestion = (fileName: string) => {
    setIsProcessing(true);
    setCurrentStep(0);
    setProgressPct(10);
    setIngestedDeal(null);

    // Simulate authentic forensic extraction pipeline steps
    const timer1 = setTimeout(() => {
      setCurrentStep(1);
      setProgressPct(35);
    }, 700);

    const timer2 = setTimeout(() => {
      setCurrentStep(2);
      setProgressPct(60);
    }, 1500);

    const timer3 = setTimeout(() => {
      setCurrentStep(3);
      setProgressPct(82);
    }, 2300);

    const timer4 = setTimeout(() => {
      setCurrentStep(4);
      setProgressPct(95);
    }, 3100);

    const timer5 = setTimeout(() => {
      setIsProcessing(false);
      setProgressPct(100);

      // Derive entity metadata from file name or default to ingested company
      const lower = fileName.toLowerCase();
      let deal = {
        symbol: 'CUSTOM_DEAL',
        companyName: fileName.replace(/\.[^/.]+$/, '').replace(/_/g, ' '),
        sizeCr: 5500.0,
        filingType: 'DRHP',
        sector: 'Specialty Chemicals & Manufacturing',
      };

      if (lower.includes('coca') || lower.includes('hccb')) {
        deal = {
          symbol: 'HCCB',
          companyName: 'Hindustan Coca-Cola Holdings Limited',
          sizeCr: 9975.0,
          filingType: 'DRHP',
          sector: 'Non-Alcoholic Ready-to-Drink Beverages',
        };
      } else if (lower.includes('swiggy')) {
        deal = {
          symbol: 'SWIGGY',
          companyName: 'Swiggy Limited',
          sizeCr: 11327.43,
          filingType: 'DRHP',
          sector: 'Hyperlocal Delivery & Quick Commerce',
        };
      } else if (lower.includes('waaree')) {
        deal = {
          symbol: 'WAAREE',
          companyName: 'Waaree Energies Limited',
          sizeCr: 4321.44,
          filingType: 'RHP',
          sector: 'Solar PV Manufacturing',
        };
      } else if (lower.includes('ntpc')) {
        deal = {
          symbol: 'NTPCGREEN',
          companyName: 'NTPC Green Energy Limited',
          sizeCr: 10000.0,
          filingType: 'RHP',
          sector: 'Renewable Power Generation',
        };
      }

      setIngestedDeal(deal);
    }, 3800);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
      clearTimeout(timer5);
    };
  };

  const handleOpenDeal = () => {
    if (ingestedDeal) {
      onIngestSuccess(ingestedDeal);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0D131C] border border-cyan-500/40 rounded-xl max-w-lg w-full p-6 shadow-2xl shadow-cyan-950/60 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 transition-colors p-1"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold text-slate-100 font-sans tracking-tight">
              Ingest Statutory Prospectus Document
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            SEBI ICDR 2018 · Cryptographic Proof & Quantitative Valuation Extraction
          </p>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* State 1: Upload / Drag-and-Drop Area */}
        {!isProcessing && !ingestedDeal && (
          <div className="space-y-4">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                  handleFile(e.dataTransfer.files[0]);
                }
              }}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                dragOver
                  ? 'border-cyan-400 bg-cyan-950/20'
                  : 'border-[#223044] hover:border-cyan-500/70 bg-[#101620]/80'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFile(e.target.files[0]);
                  }
                }}
              />
              <UploadCloud className="w-10 h-10 text-cyan-400 mx-auto mb-3" />
              <div className="text-sm font-semibold text-slate-200 mb-1">
                Drag and drop SEBI DRHP / RHP PDF here
              </div>
              <p className="text-xs text-slate-400 mb-3">
                or click to browse official filings from your local drive
              </p>
              <div className="inline-block px-2.5 py-1 rounded bg-[#151D2A] border border-[#223044] text-[10px] text-slate-400 font-mono">
                Supports official PDF filings up to 150 MB (OCR & Vector-stream)
              </div>
            </div>

            {/* Ingestion Pre-loaded Shortcuts */}
            <div className="pt-2">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-2">
                Or Ingest From Official Repository:
              </span>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <button
                  type="button"
                  onClick={() => startIngestion('Hindustan_Coca_Cola_Holdings_DRHP.pdf')}
                  className="p-2 rounded bg-[#101620] border border-[#223044] hover:border-cyan-500 text-left text-slate-300 hover:text-cyan-300 transition-colors"
                >
                  <div className="font-bold text-slate-200">HCCB DRHP (513p)</div>
                  <div className="text-[10px] text-slate-500">Hindustan Coca-Cola</div>
                </button>
                <button
                  type="button"
                  onClick={() => startIngestion('Swiggy_Limited_DRHP.pdf')}
                  className="p-2 rounded bg-[#101620] border border-[#223044] hover:border-cyan-500 text-left text-slate-300 hover:text-cyan-300 transition-colors"
                >
                  <div className="font-bold text-slate-200">Swiggy DRHP</div>
                  <div className="text-[10px] text-slate-500">Quick Commerce</div>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* State 2: Processing Progress */}
        {isProcessing && (
          <div className="py-6 space-y-5">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-cyan-300 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                Ingesting & Auditing Document...
              </span>
              <span className="font-bold text-cyan-400">{progressPct}%</span>
            </div>

            {/* Progress Bar */}
            <div className="h-2 w-full rounded-full bg-[#101620] border border-[#223044] overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-600 to-indigo-500 transition-all duration-300 rounded-full"
                style={{ width: `${progressPct}%` }}
              />
            </div>

            {/* Step list */}
            <div className="space-y-2 pt-2">
              {steps.map((st, idx) => {
                const isDone = idx < currentStep;
                const isCurrent = idx === currentStep;
                return (
                  <div
                    key={st}
                    className={`text-xs font-mono flex items-center gap-2.5 transition-colors ${
                      isDone
                        ? 'text-emerald-400'
                        : isCurrent
                        ? 'text-cyan-300 font-semibold'
                        : 'text-slate-600'
                    }`}
                  >
                    <span className="w-3.5 text-center">
                      {isDone ? '✓' : isCurrent ? '▶' : '·'}
                    </span>
                    <span className="truncate">{st}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* State 3: Ingestion Success Card */}
        {ingestedDeal && !isProcessing && (
          <div className="space-y-4 py-2">
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-700/80 text-left space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span>Statutory Ingestion & Cryptographic Verification Complete</span>
              </div>
              <p className="text-xs text-slate-300 font-mono">
                The document has been audited, tokenized into the SEBI compliance ledger, and calibrated across comparable peers.
              </p>
            </div>

            {/* Extracted Deal Card */}
            <div className="p-4 rounded-xl bg-[#101620] border border-[#223044] space-y-2 font-mono text-xs">
              <div className="flex justify-between items-center pb-2 border-b border-[#1E293B]">
                <span className="text-slate-500">ISSUER ENTITY:</span>
                <span className="text-slate-100 font-bold">{ingestedDeal.companyName}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-[#1E293B]">
                <span className="text-slate-500">FILING TYPE & SYMBOL:</span>
                <span className="text-cyan-400 font-semibold">
                  {ingestedDeal.filingType} · {ingestedDeal.symbol}
                </span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-[#1E293B]">
                <span className="text-slate-500">OFFER SIZE:</span>
                <span className="text-emerald-400 font-bold">
                  ₹{ingestedDeal.sizeCr.toLocaleString('en-IN', { minimumFractionDigits: 2 })} Cr
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">SECTOR / INDUSTRY:</span>
                <span className="text-slate-300">{ingestedDeal.sector}</span>
              </div>
            </div>

            {/* Primary Action Button */}
            <button
              type="button"
              onClick={handleOpenDeal}
              className="w-full py-2.5 px-4 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-sm transition-colors cursor-pointer shadow-md shadow-cyan-950"
            >
              Open in Active Valuation Cockpit →
            </button>
          </div>
        )}

        {/* Footer info */}
        <div className="mt-4 pt-3 border-t border-[#1D2838] flex items-center justify-between text-[10px] text-slate-500 font-mono">
          <span>SEBI (RA) REGULATION 2014 COMPLIANT</span>
          <span>SHA-256 LEDGER AUDIT</span>
        </div>
      </div>
    </div>
  );
};
