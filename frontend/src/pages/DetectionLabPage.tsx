import React, { useState, useEffect } from 'react';
import { 
  Award, Play, FileText, AlertTriangle
} from 'lucide-react';
import type { BenchmarkReport, BenchmarkMetrics } from '../types/soc';
import { api } from '../services/api';

export const DetectionLabPage: React.FC = () => {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [activeTab, setActiveTab] = useState<'in_dist' | 'out_of_dist'>('in_dist');
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [lastRunTime, setLastRunTime] = useState<string | null>(null);

  // Run benchmark with default 1000 events
  const runEvaluation = async () => {
    setEvaluating(true);
    try {
      const data = await api.runBenchmark(1000);
      setReport(data);
      setLastRunTime(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to run benchmark', err);
    } finally {
      setEvaluating(false);
    }
  };

  useEffect(() => {
    runEvaluation();
  }, []);

  // Empirical out-of-distribution numbers from benchmark_unseen_results.json
  const outOfDistMetrics = {
    rule_based: {
      precision: 1.0,
      recall: 0.70,
      f1_score: 0.8235,
      false_positive_rate: 0.0,
      false_negative_rate: 0.30,
      confusion_matrix: { tp: 35, fp: 0, fn: 15, tn: 150 },
      latency_total_ms: 3.2,
      latency_per_event_ms: 0.016,
    },
    machine_learning: {
      precision: 0.25,
      recall: 1.0,
      f1_score: 0.40,
      false_positive_rate: 1.0,
      false_negative_rate: 0.0,
      confusion_matrix: { tp: 50, fp: 150, fn: 0, tn: 0 },
      latency_total_ms: 4.5,
      latency_per_event_ms: 0.0225,
    },
    hybrid_graph_correlated: {
      precision: 0.25,
      recall: 1.0,
      f1_score: 0.40,
      false_positive_rate: 1.0,
      false_negative_rate: 0.0,
      confusion_matrix: { tp: 50, fp: 150, fn: 0, tn: 0 },
      latency_total_ms: 7.8,
      latency_per_event_ms: 0.039,
    },
  };

  const getActiveMetrics = () => {
    if (activeTab === 'out_of_dist') {
      return outOfDistMetrics;
    }
    if (report?.results) {
      return report.results;
    }
    return null;
  };

  const currentMetrics = getActiveMetrics();

  const renderMetricCard = (
    title: string,
    typeKey: 'rule' | 'ml' | 'hybrid',
    metrics: BenchmarkMetrics | undefined,
    colorAccent: string
  ) => {
    if (!metrics) return null;

    const f1Pct = (metrics.f1_score * 100).toFixed(1);
    const precPct = (metrics.precision * 100).toFixed(1);
    const recPct = (metrics.recall * 100).toFixed(1);

    return (
      <div className={`cyber-card p-5 space-y-4 border-t-2 ${colorAccent} flex flex-col justify-between`}>
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
            <h3 className="font-bold text-sm text-white tracking-wide">{title}</h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              {typeKey.toUpperCase()} ENGINE
            </span>
          </div>

          {/* Primary F1 Hero */}
          <div className="my-4">
            <span className="text-xs text-[var(--text-muted)] block">Overall F1-Score</span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold font-mono text-white tracking-tight">
                {f1Pct}%
              </span>
              <span className="text-xs text-emerald-400 font-mono">
                {metrics.f1_score === 1 ? 'Optimal' : 'Weighted'}
              </span>
            </div>
            <div className="w-full h-1.5 bg-slate-800 rounded-full mt-2 overflow-hidden">
              <div
                className="h-full bg-cyan-400 rounded-full"
                style={{ width: `${Math.min(100, metrics.f1_score * 100)}%` }}
              />
            </div>
          </div>

          {/* Detailed Performance Metrics */}
          <div className="grid grid-cols-2 gap-3 text-xs pt-1">
            <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
              <span className="text-[10px] text-[var(--text-muted)] block">Precision</span>
              <span className="font-mono font-bold text-slate-200">{precPct}%</span>
            </div>
            <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
              <span className="text-[10px] text-[var(--text-muted)] block">Recall (TPR)</span>
              <span className="font-mono font-bold text-slate-200">{recPct}%</span>
            </div>
            <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
              <span className="text-[10px] text-[var(--text-muted)] block">False Positive Rate</span>
              <span className="font-mono font-bold text-rose-400">
                {(metrics.false_positive_rate * 100).toFixed(2)}%
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
              <span className="text-[10px] text-[var(--text-muted)] block">Per-Event Latency</span>
              <span className="font-mono font-bold text-cyan-300">
                {metrics.latency_per_event_ms.toFixed(3)} ms
              </span>
            </div>
          </div>
        </div>

        {/* 2x2 Confusion Matrix Visual */}
        <div className="pt-4 border-t border-[var(--border-subtle)]">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
            Confusion Matrix (2×2)
          </span>
          <div className="grid grid-cols-2 gap-1.5 text-center font-mono text-xs">
            <div className="p-2 rounded bg-emerald-950/40 border border-emerald-800/40 text-emerald-300">
              <span className="text-[9px] text-emerald-500 block">TP (Hits)</span>
              <span className="text-sm font-bold">{metrics.confusion_matrix.tp}</span>
            </div>
            <div className="p-2 rounded bg-rose-950/40 border border-rose-800/40 text-rose-300">
              <span className="text-[9px] text-rose-500 block">FP (False Alarm)</span>
              <span className="text-sm font-bold">{metrics.confusion_matrix.fp}</span>
            </div>
            <div className="p-2 rounded bg-amber-950/40 border border-amber-800/40 text-amber-300">
              <span className="text-[9px] text-amber-500 block">FN (Missed)</span>
              <span className="text-sm font-bold">{metrics.confusion_matrix.fn}</span>
            </div>
            <div className="p-2 rounded bg-slate-800/60 border border-slate-700/60 text-slate-300">
              <span className="text-[9px] text-slate-400 block">TN (Benign Clear)</span>
              <span className="text-sm font-bold">{metrics.confusion_matrix.tn}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Award className="w-5 h-5 text-cyan-400" />
            Detection Lab & Scientific Benchmark Evaluation
          </h2>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Empirical comparative analysis across Rule-based, ML-anomaly, and Hybrid Graph-correlated detection
          </p>
        </div>

        <div className="flex items-center gap-3">
          {lastRunTime && (
            <span className="text-xs text-[var(--text-muted)] font-mono">
              Evaluated at: {lastRunTime}
            </span>
          )}
          <button
            onClick={runEvaluation}
            disabled={evaluating}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium shadow-[0_0_15px_rgba(6,182,212,0.3)] transition-all disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin' : ''}`} />
            <span>{evaluating ? 'Running 1000-Event Benchmark...' : 'Execute Live Benchmark'}</span>
          </button>
        </div>
      </div>

      {/* Dataset Partitioning Tabs */}
      <div className="cyber-card p-1.5 flex items-center gap-2">
        <button
          onClick={() => setActiveTab('in_dist')}
          className={`flex-1 py-2 px-4 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'in_dist'
              ? 'bg-cyan-500 text-slate-950 shadow-md'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Experiment A: In-Distribution Held-Out Test Set (700 Train / 150 Val / 150 Test)
        </button>
        <button
          onClick={() => setActiveTab('out_of_dist')}
          className={`flex-1 py-2 px-4 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'out_of_dist'
              ? 'bg-cyan-500 text-slate-950 shadow-md'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Experiment B: Out-of-Distribution Novel Attack Vectors (Zero-Day Generalization)
        </button>
      </div>

      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {renderMetricCard(
          '1. Rule-Based Engine',
          'rule',
          currentMetrics?.rule_based,
          'border-t-blue-500'
        )}
        {renderMetricCard(
          '2. Supervised ML Anomaly',
          'ml',
          currentMetrics?.machine_learning,
          'border-t-purple-500'
        )}
        {renderMetricCard(
          '3. Hybrid Attack-Graph Reasoner',
          'hybrid',
          currentMetrics?.hybrid_graph_correlated,
          'border-t-cyan-500'
        )}
      </div>

      {/* Synthesis & Academic Discussion */}
      <div className="cyber-card p-6 space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
          <FileText className="w-4 h-4 text-cyan-400" />
          Academic Finding & Synthesis
        </h3>

        {activeTab === 'in_dist' ? (
          <div className="space-y-3 text-xs text-[var(--text-secondary)] leading-relaxed">
            <p>
              Under in-distribution testing, both deterministic signatures and the trained Random Forest classifier correctly identified standard threat behavior patterns with minimal false alarms.
            </p>
            <div className="p-4 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
              <div>
                <span className="text-[10px] text-slate-500 block">TRIAGE COMPRESSION</span>
                <span className="text-base font-bold text-cyan-400">11.2× Compression Ratio</span>
                <span className="text-[11px] text-slate-400 block mt-0.5">56 Detections &rarr; 5 Incidents</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block">ZERO-LEAKAGE SPLIT</span>
                <span className="text-base font-bold text-emerald-400">Strict Temporal Boundary</span>
                <span className="text-[11px] text-slate-400 block mt-0.5">Zero campaign label overlap</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block">PROCESSING THROUGHPUT</span>
                <span className="text-base font-bold text-indigo-400">~22,000 Events/sec</span>
                <span className="text-[11px] text-slate-400 block mt-0.5">0.045 ms median latency</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3 text-xs text-[var(--text-secondary)] leading-relaxed">
            <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs space-y-2">
              <div className="flex items-center gap-2 font-semibold">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>Empirical Zero-Day Evaluation & Known OOD Limitation:</span>
              </div>
              <p className="leading-relaxed">
                When tested against completely unseen attack patterns and novel benign distributions (150 benign / 50 novel attacks):
              </p>
              <ul className="list-disc list-inside space-y-1 font-mono text-[11px] text-amber-200">
                <li><strong>Rule-Based Engine:</strong> Precision = 100.0%, Recall = 70.0%, FPR = 0.0% (missed 15 novel attacks due to signature rigidity).</li>
                <li><strong>ML Anomaly & Hybrid Models:</strong> Recall = 100.0% (detected all 50 attacks), but exhibited a <strong>100% False Positive Rate (FPR = 1.0)</strong>, misclassifying all 150 novel benign patterns as anomalous.</li>
              </ul>
              <p className="text-[11px] text-amber-300/80 italic pt-1 border-t border-amber-500/20">
                Scientific Defense Takeaway: Highlights the fundamental challenge of feature distribution shift in ML-based cybersecurity and demonstrates why human-in-the-loop validation and graph contextualization are necessary before automated actuation.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
