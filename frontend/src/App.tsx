import React, { useState } from 'react';
import RFQInput from './components/RFQInput';
import PayoffObjectPanel from './components/PayoffObjectPanel';
import QuoteQualityCards from './components/QuoteQualityCards';
import AlternativesTable from './components/AlternativesTable';
import ExplanationPanel from './components/ExplanationPanel';
import AuditTrace from './components/AuditTrace';
import { parseRFQ, optimizeQuote, getAudit } from './api/client';

export default function App() {
  const [rawText, setRawText] = useState('');
  const [payoffObj, setPayoffObj] = useState<any | null>(null);
  const [missingFields, setMissingFields] = useState<any[]>([]);
  const [riskAssessment, setRiskAssessment] = useState<any | null>(null);
  const [winProb, setWinProb] = useState<number | null>(null);
  const [deskEcon, setDeskEcon] = useState<number | null>(null);
  const [alternatives, setAlternatives] = useState<any[]>([]);
  const [recommendedId, setRecommendedId] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<string>('');
  const [auditRecords, setAuditRecords] = useState<any[]>([]);

  async function handleParse() {
    try {
      const data = await parseRFQ({ raw_text: rawText });
      setPayoffObj(data.payoff_object);
      setMissingFields(data.missing_fields);
      setRiskAssessment(null);
      setWinProb(null);
      setDeskEcon(null);
      setAlternatives([]);
      setRecommendedId(null);
      setExplanation('');
    } catch (err) {
      console.error(err);
      alert('Parse failed. Check console for details.');
    }
  }

  async function handleOptimize() {
    try {
      const data = await optimizeQuote({ raw_text: rawText });
      setPayoffObj(data.original_payoff);
      setMissingFields(data.missing_fields);
      setRiskAssessment(data.current_quote_quality.risk_assessment);
      setWinProb(data.current_quote_quality.win_probability);
      setDeskEcon(data.current_quote_quality.desk_economics_score);
      setAlternatives(data.alternatives);
      setRecommendedId(data.recommended_alternative_id);
      setExplanation(data.explanation);
      // fetch audit after optimisation
      const audit = await getAudit();
      setAuditRecords(audit);
    } catch (err) {
      console.error(err);
      alert('Optimisation failed. Check console for details.');
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <header className="p-4 border-b border-gray-800 mb-4">
        <h1 className="text-2xl font-bold">Q‑Struct OS</h1>
        <p className="text-xs text-gray-400">Counterfactual Quote Intelligence for Structured Products</p>
      </header>
      <div className="container mx-auto p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-1">
            <RFQInput
              rawText={rawText}
              setRawText={setRawText}
              onParse={handleParse}
              onOptimize={handleOptimize}
            />
            {missingFields && missingFields.length > 0 && (
              <div className="mt-2 p-2 bg-yellow-800 text-yellow-200 text-xs rounded-md">
                Missing fields: {missingFields.map((m) => m.field_name).join(', ')}
              </div>
            )}
          </div>
          <div className="md:col-span-2">
            <PayoffObjectPanel payoffObject={payoffObj} />
          </div>
          <div className="md:col-span-1">
            <QuoteQualityCards
              riskAssessment={riskAssessment}
              winProbability={winProb}
              deskEconomics={deskEcon}
            />
          </div>
        </div>
        <AlternativesTable alternatives={alternatives} recommendedId={recommendedId} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ExplanationPanel explanation={explanation} />
          <AuditTrace auditRecords={auditRecords} />
        </div>
      </div>
    </div>
  );
}
