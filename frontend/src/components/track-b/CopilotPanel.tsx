"use client";

import React, { useState } from "react";
import { MessageSquare, Send, Globe, Bot, ShieldCheck, AlertCircle } from "lucide-react";

interface CopilotPanelProps {
  runId: string | null;
  scenario?: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  factIds?: string[];
  evidenceLinks?: string[];
  warnings?: string[];
  language?: string;
}

export default function CopilotPanel({ runId, scenario = "precautionary" }: CopilotPanelProps) {
  const [language, setLanguage] = useState<"en" | "ne">("en");
  const [inputQuery, setInputQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        language === "ne"
          ? "नमस्ते! म अर्बिक (Orbiq) एआई कोपाइलट हुँ। यो विश्लेषण रनको बाढी, पूर्वाधार जोखिम, र सम्पर्कविहीन बस्तीबारे सोध्न सक्नुहुन्छ।"
          : "Hello! I am the Orbiq Situation Copilot. Ask me about mapped flood extent, exposed infrastructure, or cut-off settlements for this run."
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const samplePromptsEn = [
    "How much new flood water is mapped?",
    "Which settlements lost hospital access?",
    "Which bridges are exposed?",
    "How many people died in the flood?"
  ];

  const samplePromptsNe = [
    "बाढीले कति क्षेत्र डुबानमा पारेको छ?",
    "कुन कुन बस्तीको अस्पताल जाने बाटो बन्द भयो?",
    "जोखिममा परेका पुलहरू कुन कुन हुन्?",
    "कति मान्छे घाइते भए?"
  ];

  const handleSend = async (textToSend?: string) => {
    const q = textToSend || inputQuery;
    if (!q.trim() || !runId) return;

    const userMsg: Message = { role: "user", content: q };
    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const res = await fetch(`/api/track-b/runs/${runId}/copilot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q,
          language: language,
          scenario: scenario
        })
      });

      if (!res.ok) {
        throw new Error(`Copilot request failed: ${res.statusText}`);
      }

      const data = await res.json();
      const assistantMsg: Message = {
        role: "assistant",
        content: data.answer,
        factIds: data.fact_ids,
        evidenceLinks: data.evidence_links,
        warnings: data.warnings,
        language: data.language
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: Unable to query copilot (${err.message || err}).`
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const samplePrompts = language === "ne" ? samplePromptsNe : samplePromptsEn;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3 text-slate-200 flex flex-col h-[460px]">
      {/* Header with Bilingual Toggle */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
          <Bot className="w-4 h-4 text-sky-400" />
          <span>Grounded Situation Copilot</span>
        </h3>
        <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded p-0.5 text-xs">
          <Globe className="w-3 h-3 text-slate-400 ml-1" />
          <button
            type="button"
            onClick={() => setLanguage("en")}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
              language === "en" ? "bg-sky-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            English
          </button>
          <button
            type="button"
            onClick={() => setLanguage("ne")}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
              language === "ne" ? "bg-sky-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            नेपाली
          </button>
        </div>
      </div>

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 text-xs">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${
              m.role === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-2.5 ${
                m.role === "user"
                  ? "bg-sky-600 text-white rounded-br-none"
                  : "bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-none"
              }`}
            >
              <div className="leading-relaxed whitespace-pre-wrap">{m.content}</div>

              {/* Fact Citations */}
              {m.factIds && m.factIds.length > 0 && (
                <div className="mt-2 pt-1.5 border-t border-slate-800 flex flex-wrap gap-1 items-center">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  <span className="text-[10px] text-slate-400">Verified Facts:</span>
                  {m.factIds.map((fid) => (
                    <span
                      key={fid}
                      className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-900 border border-slate-700 text-sky-300"
                    >
                      {fid.split(":").slice(1).join(":")}
                    </span>
                  ))}
                </div>
              )}

              {/* Warnings / Limitations */}
              {m.warnings && m.warnings.length > 0 && (
                <div className="mt-1.5 flex items-center gap-1 text-[10px] text-amber-400">
                  <AlertCircle className="w-3 h-3" />
                  <span>{m.warnings[0]}</span>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-slate-400 italic">
            <Bot className="w-3.5 h-3.5 animate-spin" />
            <span>Consulting deterministic fact store...</span>
          </div>
        )}
      </div>

      {/* Sample Quick Questions */}
      <div className="flex gap-1.5 overflow-x-auto pb-1 text-[10px]">
        {samplePrompts.map((p, i) => (
          <button
            key={i}
            type="button"
            onClick={() => handleSend(p)}
            className="whitespace-nowrap px-2 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex gap-2 pt-1 border-t border-slate-800"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder={
            !runId
              ? "Run an analysis first to enable copilot queries..."
              : language === "ne"
              ? "प्रश्न सोध्नुहोस् (जस्तै: बाढीको क्षेत्रफल कति छ?)..."
              : "Ask a grounded situation question..."
          }
          disabled={!runId || isLoading}
          className="flex-1 bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-sky-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!runId || isLoading || !inputQuery.trim()}
          className="px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 disabled:text-slate-600 text-white transition text-xs flex items-center justify-center"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
