import React, { useState } from 'react'
import { Code2, Play, AlertOctagon, CheckCircle2, AlertTriangle, ShieldCheck, Copy, Check } from 'lucide-react'
import { analyzePhpCode, ScanPhpResponse } from '@/api/scanner'
import clsx from 'clsx'

const SAMPLE_VULNERABLE_PHP = `<?php
// PHP2Shell Vulnerable Sample (CVE-2026-109618)
// Memory corruption during custom error handler execution
set_error_handler(function($errno, $errstr, $errfile, $errline) {
    echo "Error [$errno]: " . $errstr . " in " . $errfile;
});

// SQL Injection Flaw
$user_id = $_GET['id'];
$query = "SELECT * FROM accounts WHERE id = " . $user_id;
mysql_query($query);
`

export function ClientScannerPage() {
  const [sourceCode, setSourceCode] = useState(SAMPLE_VULNERABLE_PHP)
  const [isScanning, setIsScanning] = useState(false)
  const [result, setResult] = useState<ScanPhpResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const handleScan = async () => {
    if (!sourceCode.trim()) {
      setError('Please provide PHP source code to analyze.')
      return
    }

    try {
      setIsScanning(true)
      setError(null)
      const data = await analyzePhpCode(sourceCode, 'sample.php')
      setResult(data)
    } catch (err: any) {
      setError(err?.userMessage || 'Vulnerability analysis failed.')
    } finally {
      setIsScanning(false)
    }
  }

  const handleCopy = (snippet: string, id: string) => {
    navigator.clipboard.writeText(snippet)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 dark:border-dark-700 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Code2 className="w-6 h-6 text-primary-500" />
            PHP Vulnerability & PHP2Shell Code Scanner
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Analyze PHP source code for PHP2Shell (CVE-2026-109618 / CVE-2026-109619) and OWASP Top 10 weaknesses
          </p>
        </div>

        <button
          onClick={handleScan}
          disabled={isScanning}
          className="btn-primary text-xs self-start sm:self-auto flex items-center gap-1.5"
        >
          {isScanning ? (
            <span className="flex items-center gap-1.5">
              <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Analyzing Code...
            </span>
          ) : (
            <span className="flex items-center gap-1.5">
              <Play className="w-3.5 h-3.5" />
              Analyze Code
            </span>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Editor & Input */}
      <div className="card p-4 space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
          <span>SOURCE CODE (PHP 5.4 - 8.5)</span>
          <button
            onClick={() => setSourceCode(SAMPLE_VULNERABLE_PHP)}
            className="text-primary-600 dark:text-primary-400 hover:underline"
          >
            Reset to Vulnerable Sample
          </button>
        </div>
        <textarea
          rows={10}
          value={sourceCode}
          onChange={e => setSourceCode(e.target.value)}
          className="w-full p-3.5 font-mono text-xs rounded-lg border border-slate-300 dark:border-dark-600 bg-slate-900 text-emerald-400 focus:ring-2 focus:ring-primary-500"
          placeholder="Paste PHP code here..."
        />
      </div>

      {/* Results View */}
      {result && (
        <div className="space-y-4">
          {/* Summary Banner */}
          <div
            className={clsx(
              'card p-5 border flex flex-col sm:flex-row sm:items-center justify-between gap-4',
              result.has_php2shell_vulnerability
                ? 'border-rose-300 dark:border-rose-900 bg-rose-50/50 dark:bg-rose-950/20'
                : result.findings.length > 0
                ? 'border-amber-300 dark:border-amber-900 bg-amber-50/50 dark:bg-amber-950/20'
                : 'border-emerald-300 dark:border-emerald-900 bg-emerald-50/50 dark:bg-emerald-950/20'
            )}
          >
            <div className="flex items-center gap-3">
              {result.has_php2shell_vulnerability ? (
                <AlertOctagon className="w-8 h-8 text-rose-500 flex-shrink-0" />
              ) : result.findings.length > 0 ? (
                <AlertTriangle className="w-8 h-8 text-amber-500 flex-shrink-0" />
              ) : (
                <CheckCircle2 className="w-8 h-8 text-emerald-500 flex-shrink-0" />
              )}
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-base">
                  {result.has_php2shell_vulnerability
                    ? 'PHP2Shell Critical RCE Risk Detected'
                    : result.findings.length > 0
                    ? `${result.findings.length} Vulnerabilities Found`
                    : 'No Vulnerabilities Detected'}
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Total Analyzed Lines: {result.total_lines} • Matched Findings: {result.findings.length}
                </p>
              </div>
            </div>

            <div className="text-xs font-mono font-semibold">
              {result.has_php2shell_vulnerability && (
                <span className="px-2.5 py-1 rounded bg-rose-600 text-white uppercase">
                  CVSS 9.2 Critical
                </span>
              )}
            </div>
          </div>

          {/* Remediation Blueprint (if PHP2Shell affected) */}
          {result.remediation_guidance && (
            <div className="card p-6 border-rose-200 dark:border-rose-900 space-y-4">
              <div className="flex items-center gap-2 font-bold text-rose-600 dark:text-rose-400 text-sm">
                <ShieldCheck className="w-5 h-5" />
                <h3>Automated PHP2Shell Remediation Blueprint</h3>
              </div>
              <div className="space-y-3">
                {result.remediation_guidance.recommended_actions.map(action => (
                  <div
                    key={action.layer}
                    className="p-3.5 rounded-lg bg-slate-50 dark:bg-dark-900 border border-slate-200 dark:border-dark-700 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {action.layer} ({action.priority})
                      </span>
                    </div>
                    <p className="text-slate-600 dark:text-slate-400">{action.step}</p>
                    {action.code_snippet && (
                      <div className="relative mt-2">
                        <pre className="p-3 rounded bg-slate-950 text-slate-200 font-mono text-[11px] overflow-x-auto">
                          {action.code_snippet}
                        </pre>
                        <button
                          onClick={() => handleCopy(action.code_snippet!, action.layer)}
                          className="absolute right-2 top-2 btn-ghost p-1 text-slate-400 hover:text-white"
                        >
                          {copiedId === action.layer ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Finding Cards */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
              Detailed Findings
            </h4>
            {result.findings.map(finding => (
              <div key={finding.rule_id} className="card p-5 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-dark-700 pb-3">
                  <div>
                    <span className="text-xs font-mono font-bold text-primary-600 dark:text-primary-400 mr-2">
                      [{finding.rule_id}]
                    </span>
                    <span className="font-semibold text-slate-900 dark:text-white text-sm">
                      {finding.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-slate-100 dark:bg-dark-700 text-slate-600 dark:text-slate-300">
                      {finding.cwe}
                    </span>
                    <span
                      className={clsx(
                        'text-xs font-mono uppercase px-2 py-0.5 rounded font-bold',
                        finding.severity === 'critical'
                          ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                          : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                      )}
                    >
                      {finding.severity}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {finding.description}
                </p>

                <div className="bg-slate-900 text-rose-400 p-2.5 rounded font-mono text-xs overflow-x-auto">
                  <span className="text-slate-500 mr-3">Line {finding.line_number}:</span>
                  {finding.line_content}
                </div>

                <div className="p-3 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900 text-xs text-emerald-800 dark:text-emerald-300">
                  <span className="font-semibold block mb-0.5">Remediation:</span>
                  {finding.remediation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
