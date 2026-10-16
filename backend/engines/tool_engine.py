"""Small deterministic generators for applications whose core behavior is well-defined."""
from __future__ import annotations

import json
import re


def detect_tool(brief: str) -> str | None:
    text = (brief or "").lower()
    if re.search(r"\bcalculator\b", text):
        return "calculator"
    return None


def generate(pf, title: str, tool: str) -> dict:
    """Write a self-contained working tool with no external API or credentials."""
    if tool != "calculator":
        raise ValueError(f"unsupported deterministic tool: {tool}")
    pf.write("src/App.tsx", _CALCULATOR_TSX.replace("__TITLE__", json.dumps(title[:70], ensure_ascii=False)))
    pf.write("src/styles/app.css", _CALCULATOR_CSS)
    pf.write(".env.example", "# This app runs entirely in the browser. No API URL or API key is needed.\n")
    pf.write("README.md", f"""# {title}

A responsive calculator built from a single prompt. It supports arithmetic precedence, parentheses, keyboard input, clear/backspace, error states and recent calculations.

## Run locally

```powershell
npm install
npm run dev
```

Run `npm run build` for the TypeScript check and production build. The calculator runs locally in the browser and requires no server, API key or account. User-entered expressions are parsed; they are never evaluated as executable code.
""")
    return {"entities": 0, "api_enabled": False, "auth_enabled": False, "unsupported_auth": False, "title": title, "tool": tool}


_CALCULATOR_TSX = r'''import { useEffect, useState } from 'react'
import './styles/app.css'

const TOOL_TITLE = __TITLE__ as string

function calculate(input: string): number {
  const source = input.replace(/[×]/g, '*').replace(/[÷]/g, '/').replace(/\s+/g, '')
  if (!source || !/^[0-9.+\-*/()%]+$/.test(source)) throw new Error('Enter a valid expression.')
  let at = 0
  const expression = (): number => {
    let value = term()
    while (source[at] === '+' || source[at] === '-') {
      const op = source[at++]
      const right = term()
      value = op === '+' ? value + right : value - right
    }
    return value
  }
  const term = (): number => {
    let value = factor()
    while (source[at] === '*' || source[at] === '/' || source[at] === '%') {
      const op = source[at++]
      const right = factor()
      if ((op === '/' || op === '%') && right === 0) throw new Error('Cannot divide by zero.')
      value = op === '*' ? value * right : op === '/' ? value / right : value % right
    }
    return value
  }
  const factor = (): number => {
    const op = source[at]
    if (op === '+' || op === '-') {
      at++
      const value = factor()
      return op === '-' ? -value : value
    }
    if (op === '(') {
      at++
      const value = expression()
      if (source[at++] !== ')') throw new Error('Check the parentheses.')
      return value
    }
    const match = source.slice(at).match(/^(?:\d+\.?\d*|\.\d+)/)
    if (!match) throw new Error('Enter a valid expression.')
    at += match[0].length
    return Number(match[0])
  }
  const result = expression()
  if (at !== source.length || !Number.isFinite(result)) throw new Error('This expression cannot be calculated.')
  return result
}

const keys = ['AC', 'DEL', '(', ')', '%', '7', '8', '9', '÷', '4', '5', '6', '×', '1', '2', '3', '-', '±', '0', '.', '+', '=']
export default function App() {
  const [expression, setExpression] = useState('')
  const [answer, setAnswer] = useState('0')
  const [error, setError] = useState('')
  const [history, setHistory] = useState<string[]>([])

  function press(key: string) {
    setError('')
    if (key === 'AC') { setExpression(''); setAnswer('0'); return }
    if (key === 'DEL') { setExpression((old) => old.slice(0, -1)); return }
    if (key === '±') { setExpression((old) => old.startsWith('-') ? old.slice(1) : `-${old}`); return }
    if (key === '=') {
      try {
        const raw = calculate(expression)
        const result = String(Number(raw.toPrecision(12)))
        setAnswer(result)
        setHistory((old) => [`${expression} = ${result}`, ...old].slice(0, 6))
        setExpression(result)
      } catch (e) { setError((e as Error).message) }
      return
    }
    setExpression((old) => (old + key).slice(0, 100))
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey || event.altKey) return
      if (/^[0-9.+\-*/()%]$/.test(event.key)) { event.preventDefault(); press(event.key) }
      else if (event.key === 'Enter' || event.key === '=') { event.preventDefault(); press('=') }
      else if (event.key === 'Backspace') { event.preventDefault(); press('DEL') }
      else if (event.key === 'Escape') { event.preventDefault(); press('AC') }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  return <main className="tool-page"><section className="calculator-card" aria-label={TOOL_TITLE}>
    <header className="tool-header"><div className="tool-mark" aria-hidden="true">ƒ</div><div><p className="eyebrow">EVERYDAY TOOL</p><h1>{TOOL_TITLE}</h1><p className="tool-subtitle">Clear answers, no distractions.</p></div></header>
    <div className="calculator-screen" aria-live="polite"><p>{expression || 'Ready when you are'}</p><output>{answer}</output>{error && <small role="alert">{error}</small>}</div>
    <div className="calculator-keys">{keys.map((key) => <button key={key} type="button" onClick={() => press(key)} aria-label={key === 'DEL' ? 'Delete last character' : key === 'AC' ? 'Clear' : key} className={`${['÷', '×', '-', '+', '%'].includes(key) ? 'operator' : ''} ${key === '=' ? 'equals' : ''} ${key === 'AC' || key === 'DEL' ? 'utility' : ''}`}>{key === 'DEL' ? '⌫' : key}</button>)}</div>
    <footer className="tool-footer"><span>Keyboard supported</span><span>Recent calculations</span></footer>
    {history.length > 0 && <section className="calculator-history"><h2>Recent calculations</h2>{history.map((entry, index) => <button type="button" key={`${entry}-${index}`} onClick={() => { const value = entry.split(' = ')[1]; setExpression(value); setAnswer(value); setError('') }}>{entry}</button>)}</section>}
  </section></main>
}
'''

_CALCULATOR_CSS = r'''@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{font-family:Inter,system-ui,sans-serif;color:#f4f7fb;background:#080d15;font-synthesis:none;text-rendering:optimizeLegibility;-webkit-font-smoothing:antialiased}*{box-sizing:border-box}body{margin:0;min-width:320px;min-height:100vh}.tool-page{min-height:100vh;display:grid;place-items:center;padding:28px 16px;background:radial-gradient(ellipse at top,#28354d 0%,#111827 47%,#070b12 100%);color:#f4f7fb}.calculator-card{width:min(100%,430px);padding:22px;border:1px solid #ffffff1c;border-radius:27px;background:linear-gradient(160deg,#151d2bf2,#0f1520f5);box-shadow:0 28px 100px #0008}.tool-header{display:flex;align-items:center;gap:13px;margin-bottom:21px}.tool-mark{display:grid;place-items:center;width:48px;height:48px;border-radius:15px;background:linear-gradient(140deg,#6c7cff,#9c76f7);font-size:25px;font-weight:800;color:white;box-shadow:0 10px 30px #7d7eff35}.tool-header .eyebrow{margin:0;color:#a8b6d2;font-size:9px;letter-spacing:.17em}.tool-header h1{font:600 23px/1.2 'Space Grotesk',Inter,sans-serif;margin:4px 0;letter-spacing:-.04em}.tool-subtitle{margin:0;color:#a5b1c7;font-size:11px}.calculator-screen{padding:18px;margin-bottom:14px;background:#080d15;border:1px solid #ffffff10;border-radius:17px;text-align:right;min-height:112px;display:flex;flex-direction:column;justify-content:flex-end;overflow:hidden}.calculator-screen p{color:#8290a8;font-size:13px;min-height:18px;margin:0 0 9px;overflow-wrap:anywhere}.calculator-screen output{font-size:clamp(28px,8vw,42px);line-height:1.1;font-weight:650;letter-spacing:-.045em;overflow-wrap:anywhere}.calculator-screen small{color:#ff9aaa;font-size:11px;margin-top:9px}.calculator-keys{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}.calculator-keys button{height:53px;border:1px solid #ffffff0d;border-radius:13px;background:#212a3a;color:#e7edfa;font-size:17px;font-weight:600;transition:transform .14s ease,background .14s ease;cursor:pointer}.calculator-keys button:hover{transform:translateY(-1px);background:#303b51}.calculator-keys button:focus-visible{outline:2px solid #9b9eff;outline-offset:2px}.calculator-keys button.operator{background:#292a43;color:#c9c9ff}.calculator-keys button.utility{background:#293342;color:#bac5d9}.calculator-keys button.equals{background:linear-gradient(135deg,#6c7cff,#8a73f2);color:white;border-color:transparent}.calculator-keys button:active{transform:scale(.97)}.tool-footer{display:flex;justify-content:space-between;gap:12px;padding:14px 2px 0;color:#8492ab;font-size:10px}.calculator-history{border-top:1px solid #ffffff15;margin-top:15px;padding-top:15px}.calculator-history h2{font-size:11px;color:#b9c4d8;margin:0 0 7px}.calculator-history button{display:block;width:100%;text-align:right;padding:7px 0;color:#919eb3;font-size:11px;background:transparent;border:0;cursor:pointer}.calculator-history button:hover{color:#fff}@media(max-width:390px){.calculator-card{padding:15px;border-radius:20px}.calculator-keys{gap:6px}.calculator-keys button{height:48px;border-radius:10px}.tool-footer{font-size:9px}}@media(prefers-reduced-motion:reduce){.calculator-keys button{transition:none}}
'''
