import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Archive, BarChart3, BookOpenCheck, Check, ChevronLeft, ChevronRight, Clock3,
  Download, FileArchive, FileDown, Flag, Heart, History, Home, ListFilter,
  Menu, Play, RotateCcw, Search, Settings2, ShieldCheck, X,
} from 'lucide-react'
import bankData from './data/bank.json'
import type { Answer, AttemptRecord, Bank, Question, QuestionProgress, TestSpec } from './types'
import { formatScore, scoreTest } from './lib/scoring'
import { applyQuestionOutcomes, db, saveAttempt, toggleFavorite } from './lib/storage'

const bank = bankData as Bank
type View = 'home' | 'questions' | 'create' | 'history' | 'progress' | 'sources'

const navItems: { id: View; label: string; icon: typeof Home }[] = [
  { id: 'home', label: 'Inicio', icon: Home },
  { id: 'questions', label: 'Preguntas', icon: Search },
  { id: 'create', label: 'Nuevo test', icon: BookOpenCheck },
  { id: 'history', label: 'Históricos', icon: History },
  { id: 'progress', label: 'Progreso', icon: BarChart3 },
  { id: 'sources', label: 'Fuentes', icon: Archive },
]

function shuffle<T>(items: T[]): T[] {
  const result = [...items]
  for (let index = result.length - 1; index > 0; index -= 1) {
    const random = Math.floor(Math.random() * (index + 1))
    ;[result[index], result[random]] = [result[random], result[index]]
  }
  return result
}

function App() {
  const [view, setView] = useState<View>('home')
  const [mobileMenu, setMobileMenu] = useState(false)
  const [progress, setProgress] = useState<QuestionProgress[]>([])
  const [attempts, setAttempts] = useState<AttemptRecord[]>([])
  const [test, setTest] = useState<TestSpec | null>(null)
  const [notice, setNotice] = useState('')

  const activeQuestions = useMemo(() => bank.questions.filter(question => question.active), [])
  const progressMap = useMemo(() => new Map(progress.map(item => [item.questionId, item])), [progress])

  const refreshLocal = async () => {
    setProgress(await db.progress.toArray())
    setAttempts((await db.attempts.orderBy('finishedAt').reverse().toArray()))
  }

  useEffect(() => {
    const initialize = async () => {
      if (bank.questions.length === 0) {
        await Promise.all([db.attempts.clear(), db.progress.clear()])
        localStorage.removeItem('tai-age-progress-updated-at')
        localStorage.removeItem('tai-age-supabase-sync-code')
      }
      await refreshLocal()
    }
    void initialize()
  }, [])

  const refreshAndSync = async () => {
    await refreshLocal()
  }

  const startTest = (spec: TestSpec) => {
    setTest(spec)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const repeatMistakes = () => {
    const ids = progress.filter(item => item.wrong > 0).sort((a, b) => b.wrong - a.wrong).map(item => item.questionId)
    const usable = ids.filter(id => activeQuestions.some(question => question.id === id))
    if (!usable.length) {
      setNotice('Aún no hay preguntas falladas. Completa un test para crear tu cola de repaso.')
      return
    }
    startTest({ id: crypto.randomUUID(), title: 'Repaso de errores', mode: 'mistakes', questionIds: usable, createdAt: new Date().toISOString() })
  }

  if (test) {
    return <TestRunner spec={test} questions={test.questionIds.map(id => bank.questions.find(q => q.id === id)).filter(Boolean) as Question[]}
      onClose={() => { setTest(null); void refreshAndSync() }} progressMap={progressMap} />
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenu ? 'sidebar-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark" aria-hidden="true"><span>TAI</span><i>1188</i></div>
          <div><strong>Preparador</strong><small>Administración General del Estado</small></div>
        </div>
        <nav aria-label="Navegación principal">
          {navItems.map(item => <button key={item.id} className={view === item.id ? 'active' : ''} onClick={() => { setView(item.id); setMobileMenu(false) }}>
            <item.icon size={18} /><span>{item.label}</span>
          </button>)}
        </nav>
        <div className="source-stamp"><ShieldCheck size={16} /><span>Temario oficial<br/><b>TAILI.pdf</b></span></div>
      </aside>
      <main>
        <header className="topbar">
          <button className="icon-button menu-button" onClick={() => setMobileMenu(!mobileMenu)} aria-label="Abrir menú"><Menu /></button>
          <div><span className="eyebrow">Preparación local · sin cuentas</span><h1>{navItems.find(item => item.id === view)?.label}</h1></div>
          <button className="soft-button" onClick={() => setView('create')} disabled={!activeQuestions.length}><Play size={16} /> Empezar test</button>
        </header>
        {notice && <div className="notice" role="status"><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Cerrar"><X size={16}/></button></div>}
        <div className="page-content">
          {view === 'home' && <Dashboard questions={activeQuestions} attempts={attempts} progress={progress} onView={setView} onStart={startTest} onMistakes={repeatMistakes} />}
          {view === 'questions' && <QuestionExplorer questions={bank.questions} program={bank.program} progressMap={progressMap} onFavorite={async id => { await toggleFavorite(id); await refreshAndSync() }} />}
          {view === 'create' && <TestBuilder questions={activeQuestions} progressMap={progressMap} onStart={startTest} />}
          {view === 'history' && <HistoricalExams onStart={startTest} />}
          {view === 'progress' && <ProgressPage attempts={attempts} progress={progress} questions={activeQuestions} onMistakes={repeatMistakes} />}
          {view === 'sources' && <SourcesPage />}
        </div>
      </main>
    </div>
  )
}

function Dashboard({ questions, attempts, progress, onView, onStart, onMistakes }: {
  questions: Question[]; attempts: AttemptRecord[]; progress: QuestionProgress[]; onView: (view: View) => void; onStart: (spec: TestSpec) => void; onMistakes: () => void
}) {
  const seen = progress.filter(item => item.seen > 0).length
  const accuracy = progress.reduce((sum, item) => sum + item.correct, 0) / Math.max(1, progress.reduce((sum, item) => sum + item.correct + item.wrong, 0)) * 100
  const quick = () => onStart({ id: crypto.randomUUID(), title: 'Test rápido · 20 preguntas', mode: 'custom', questionIds: shuffle(questions).slice(0, 20).map(q => q.id), createdAt: new Date().toISOString() })
  return <>
    <section className="hero-panel">
      <div className="hero-copy"><span className="eyebrow light">Sesión de estudio</span><h2>Una pregunta.<br/><em>Una decisión.</em></h2><p>{questions.length ? 'Practica con literalidad oficial, revisa el porqué de cada resultado y conserva tu progreso solo en este dispositivo.' : 'El preparador está listo para recibir nuevas preguntas.'}</p>
        <div className="hero-actions">{questions.length ? <><button className="primary-button" onClick={quick}><Play size={17}/> Test rápido</button><button className="ghost-button" onClick={() => onView('create')}><Settings2 size={17}/> Configurar</button></> : <span>Banco vacío · las preguntas se añadirán próximamente.</span>}</div>
      </div>
      <div className="answer-sheet" aria-label="Resumen de progreso">
        <div className="sheet-header"><span>HOJA DE PROGRESO</span><b>{new Date().toLocaleDateString('es-ES')}</b></div>
        {[['Preguntas vistas', `${seen}/${questions.length}`], ['Precisión', `${accuracy.toFixed(0)}%`], ['Sesiones', String(attempts.length)]].map(([label, value], row) =>
          <div className="sheet-row" key={label}><i>{row + 1}</i><span>{label}</span><b>{value}</b><div className="bubbles"><u/><u/><u className={row === 1 && accuracy >= 50 ? 'filled' : ''}/><u/></div></div>)}
      </div>
    </section>
    <section className="stat-strip">
      <div><span>Banco activo</span><strong>{questions.length}</strong><small>preguntas verificadas</small></div>
      <div><span>Programa vigente</span><strong>33</strong><small>temas · 4 bloques</small></div>
      <div><span>Documentos</span><strong>{bank.documents.length}</strong><small>PDF inventariados</small></div>
      <div><span>Último resultado</span><strong>{attempts[0] ? `${formatScore(attempts[0].result.percentage)}%` : '—'}</strong><small>puntuación directa</small></div>
    </section>
    <section className="section-heading"><div><span className="eyebrow">Programa oficial</span><h2>Banco dividido por temas</h2><p>Los 33 temas de TAILI.pdf. El banco de preguntas está vacío.</p></div><button className="outline-button" onClick={() => onView('questions')}><Search size={16}/> Explorar preguntas</button></section>
    <div className="topic-map">{bank.program.map(block => <section key={block.id}>
      <header><b>{block.id}</b><h3>{block.name}</h3><span>{block.topics.reduce((sum, topic) => sum + questions.filter(q => q.topicId === topic.id).length, 0)} preguntas</span></header>
      <div>{block.topics.map(topic => { const count = questions.filter(q => q.topicId === topic.id).length; return <button key={topic.id} onClick={() => onView('questions')}><b>{topic.id}</b><span>{topic.name}</span><i>{count}</i></button> })}</div>
    </section>)}</div>
    {questions.length > 0 && <><section className="section-heading"><div><span className="eyebrow">Siguiente paso</span><h2>Elige cómo continuar</h2></div></section>
    <div className="action-grid">
      <button className="action-card simulation" onClick={() => onView('create')}><span className="card-icon"><Clock3/></span><small>120 minutos</small><h3>Simulacro oficial</h3><p>80 preguntas, supuesto práctico y reservas con la penalización vigente.</p><b>Configurar simulacro <ChevronRight size={17}/></b></button>
      <button className="action-card" onClick={onMistakes}><span className="card-icon"><RotateCcw/></span><small>Repaso inteligente</small><h3>Repetir errores</h3><p>Vuelve sobre las preguntas que más te cuestan, ordenadas por fallos.</p><b>Empezar repaso <ChevronRight size={17}/></b></button>
      <button className="action-card" onClick={() => onView('history')}><span className="card-icon"><History/></span><small>Convocatorias</small><h3>Exámenes históricos</h3><p>Haz una prueba respetando su numeración y procedencia originales.</p><b>Ver exámenes <ChevronRight size={17}/></b></button>
    </div></>}
  </>
}

function QuestionExplorer({ questions, program, progressMap, onFavorite }: {
  questions: Question[]; program: Bank['program']; progressMap: Map<string, QuestionProgress>; onFavorite: (id: string) => void
}) {
  const [text, setText] = useState('')
  const [block, setBlock] = useState('')
  const [topic, setTopic] = useState('')
  const [year, setYear] = useState('')
  const [access, setAccess] = useState('')
  const [status, setStatus] = useState('active')
  const [expanded, setExpanded] = useState<string | null>(null)
  const filtered = questions.filter(q => {
    const statusMatch = status === 'all' || (status === 'active' ? q.active : status === 'historical' ? Boolean(q.correctAnswer && q.correctAnswer !== 'anulada') : ['missing_official_answer', 'classification_review', 'ocr_review'].includes(q.status))
    return (!text || foldedSearch(q.prompt + q.options.join(' ')).includes(foldedSearch(text))) && (!block || q.blockId === block) && (!topic || q.topicId === topic) && (!year || String(q.year) === year) && (!access || q.access === access) && statusMatch
  })
  return <>
    <section className="section-heading"><div><span className="eyebrow">Banco trazable</span><h2>Explorador de preguntas</h2><p>{filtered.length} resultados. Las respuestas solo se muestran al abrir una pregunta.</p></div></section>
    <div className="filter-panel">
      <label className="search-field"><Search size={17}/><input value={text} onChange={e => setText(e.target.value)} placeholder="Buscar por texto o concepto" /></label>
      <select value={block} onChange={e => { setBlock(e.target.value); setTopic('') }} aria-label="Bloque"><option value="">Todos los bloques</option>{program.map(b => <option key={b.id} value={b.id}>{b.id}. {b.name}</option>)}</select>
      <select value={topic} onChange={e => setTopic(e.target.value)} aria-label="Tema"><option value="">Todos los temas</option>{program.filter(b => !block || b.id === block).flatMap(b => b.topics).map(t => <option key={t.id} value={t.id}>{t.id} · {t.name}</option>)}</select>
      <select value={year} onChange={e => setYear(e.target.value)} aria-label="Año"><option value="">Todos los años</option>{[...new Set(questions.map(q => q.year))].sort().map(y => <option key={y}>{y}</option>)}</select>
      <select value={access} onChange={e => setAccess(e.target.value)} aria-label="Acceso"><option value="">Todas las vías</option><option value="libre">Ingreso libre</option><option value="promocion_interna">Promoción interna</option></select>
      <select value={status} onChange={e => setStatus(e.target.value)} aria-label="Estado"><option value="active">Banco vigente</option><option value="historical">Con respuesta oficial</option><option value="pending">Pendientes de revisión</option><option value="all">Todas</option></select>
    </div>
    {!questions.length && <div className="empty-state"><Search/><h3>El banco está vacío</h3><p>Aún no hay preguntas cargadas.</p></div>}
    <div className="question-list">{filtered.slice(0, 200).map(question => {
      const open = expanded === question.id
      return <article key={question.id} className={`question-row ${question.active ? '' : 'excluded'}`}>
        <button className="question-main" onClick={() => setExpanded(open ? null : question.id)} aria-expanded={open}>
          <span className="question-number">{question.originalNumber}</span><span><small>{question.topicId} · {topicName(question.topicId)} · {question.year} · {question.sitting}{question.isReserve ? ' · reserva' : ''}</small><strong>{question.prompt}</strong></span><ChevronRight className={open ? 'rotated' : ''}/>
        </button>
        <button className={`favorite-button ${progressMap.get(question.id)?.favorite ? 'selected' : ''}`} onClick={() => onFavorite(question.id)} aria-label="Favorita"><Heart size={18}/></button>
        {open && <div className="question-detail">
          <ol type="a">{question.options.map((option, index) => <li key={option} className={String.fromCharCode(97 + index) === question.correctAnswer ? 'correct-option' : ''}>{option}</li>)}</ol>
          <div className="provenance"><Check size={15}/><span>{question.correctAnswer ? <>Respuesta oficial: <b>{question.correctAnswer.toUpperCase()}</b></> : 'Sin plantilla oficial disponible'}</span><span>{question.source.pdf} · página {question.source.page}</span></div>
          {!question.active && <div className="exclusion-reason">Fuera del banco activo: {question.statusReason}</div>}
        </div>}
      </article>})}</div>
  </>
}

function foldedSearch(value: string): string { return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase() }

function TestBuilder({ questions, progressMap, onStart }: { questions: Question[]; progressMap: Map<string, QuestionProgress>; onStart: (spec: TestSpec) => void }) {
  const [mode, setMode] = useState<'custom' | 'simulation'>('custom')
  const [blocks, setBlocks] = useState<string[]>(['I', 'II', 'III', 'IV'])
  const allTopicIds = useMemo(() => bank.program.flatMap(block => block.topics.map(topic => topic.id)), [])
  const [topics, setTopics] = useState<string[]>(allTopicIds)
  const [count, setCount] = useState(20)
  const [pool, setPool] = useState<'all' | 'unseen' | 'failed' | 'favorite'>('all')
  const [practical, setPractical] = useState<'III' | 'IV'>('III')
  const eligible = questions.filter(q => blocks.includes(q.blockId) && topics.includes(q.topicId) && !q.isReserve && (pool === 'all' || (pool === 'unseen' && !progressMap.get(q.id)?.seen) || (pool === 'failed' && (progressMap.get(q.id)?.wrong ?? 0) > 0) || (pool === 'favorite' && progressMap.get(q.id)?.favorite)))

  const toggleBlock = (blockId: string) => {
    const topicIds = bank.program.find(block => block.id === blockId)?.topics.map(topic => topic.id) ?? []
    if (blocks.includes(blockId)) {
      setBlocks(blocks.filter(id => id !== blockId))
      setTopics(topics.filter(id => !topicIds.includes(id)))
    } else {
      setBlocks([...blocks, blockId])
      setTopics([...new Set([...topics, ...topicIds])])
    }
  }

  const start = () => {
    let selected: Question[]
    let title: string
    if (mode === 'simulation') {
      const first = shuffle(questions.filter(q => q.section === 'first')).slice(0, 80)
      const used = new Set(first.map(q => q.id))
      const firstReservePool = shuffle(questions.filter(q => q.section === 'first_reserve' && !used.has(q.id)))
      const firstReserve = firstReservePool.slice(0, 5)
      firstReserve.forEach(q => used.add(q.id))
      const practicalPool = shuffle(questions.filter(q => q.exercise === 'supuesto_practico' && q.blockId === practical && !q.isReserve && !used.has(q.id)))
      const caseQuestions = practicalPool.slice(0, 20)
      caseQuestions.forEach(q => used.add(q.id))
      const authenticCaseReserves = shuffle(questions.filter(q => q.exercise === 'supuesto_practico' && q.blockId === practical && q.isReserve && !used.has(q.id)))
      const reserveFillers = shuffle(questions.filter(q => q.exercise === 'supuesto_practico' && q.blockId === practical && !used.has(q.id) && !authenticCaseReserves.some(r => r.id === q.id)))
      const caseReserve = [...authenticCaseReserves, ...reserveFillers].slice(0, 5)
      selected = [...first, ...firstReserve, ...caseQuestions, ...caseReserve]
      title = `Simulacro oficial · supuesto ${practical}`
    } else {
      selected = shuffle(eligible).slice(0, count)
      title = `Test personalizado · ${selected.length} preguntas`
    }
    onStart({ id: crypto.randomUUID(), title, mode, questionIds: selected.map(q => q.id), durationMinutes: mode === 'simulation' ? 120 : undefined, createdAt: new Date().toISOString() })
  }
  return <>
    <section className="section-heading"><div><span className="eyebrow">Configura la sesión</span><h2>Nuevo test</h2><p>Las soluciones permanecen ocultas hasta que finalices.</p></div></section>
    <div className="builder-layout">
      <section className="builder-card">
        <div className="segmented"><button className={mode === 'custom' ? 'active' : ''} onClick={() => setMode('custom')}>Personalizado</button><button className={mode === 'simulation' ? 'active' : ''} onClick={() => setMode('simulation')}>Simulacro vigente</button></div>
        {mode === 'custom' ? <>
          <fieldset><legend>Bloques</legend><div className="choice-grid">{bank.program.map(b => <label key={b.id} className={blocks.includes(b.id) ? 'checked' : ''}><input type="checkbox" checked={blocks.includes(b.id)} onChange={() => toggleBlock(b.id)}/><b>{b.id}</b><span>{b.name}</span></label>)}</div></fieldset>
          <fieldset><div className="legend-row"><legend>Temas</legend><span><button type="button" onClick={() => { setBlocks(['I', 'II', 'III', 'IV']); setTopics(allTopicIds) }}>Seleccionar todos</button><button type="button" onClick={() => { setBlocks([]); setTopics([]) }}>Quitar todos</button></span></div><div className="topic-choice-list">{bank.program.filter(block => blocks.includes(block.id)).map(block => <section key={block.id}><h4><b>{block.id}</b><span>{block.name}</span><i>{block.topics.filter(topic => topics.includes(topic.id)).length}/{block.topics.length}</i></h4>{block.topics.map(topic => { const count = questions.filter(q => q.topicId === topic.id && !q.isReserve).length; return <label key={topic.id} className={topics.includes(topic.id) ? 'checked' : ''}><input type="checkbox" checked={topics.includes(topic.id)} onChange={() => setTopics(topics.includes(topic.id) ? topics.filter(id => id !== topic.id) : [...topics, topic.id])}/><b>{topic.id}</b><span>{topic.name}</span><i title={`${count} preguntas disponibles`}><strong>{count}</strong><small>preg.</small></i></label> })}</section>)}</div></fieldset>
          <div className="form-row"><label>Número de preguntas<input type="number" min="5" max="100" value={count} onChange={e => setCount(Number(e.target.value))}/></label><label>Selección<select value={pool} onChange={e => setPool(e.target.value as typeof pool)}><option value="all">Cualquiera</option><option value="unseen">Nunca vistas</option><option value="failed">Falladas</option><option value="favorite">Favoritas</option></select></label></div>
          <p className="availability">{eligible.length} preguntas disponibles con estos criterios.</p>
        </> : <>
          <div className="official-format"><div><strong>80 + 5</strong><span>Primera parte</span></div><i>+</i><div><strong>20 + 5</strong><span>Supuesto práctico</span></div><i>=</i><div><strong>120'</strong><span>Tiempo total</span></div></div>
          <fieldset><legend>Elige el supuesto práctico</legend><div className="choice-grid practical"><label className={practical === 'III' ? 'checked' : ''}><input type="radio" checked={practical === 'III'} onChange={() => setPractical('III')}/><b>III</b><span>Desarrollo de sistemas</span></label><label className={practical === 'IV' ? 'checked' : ''}><input type="radio" checked={practical === 'IV'} onChange={() => setPractical('IV')}/><b>IV</b><span>Sistemas y comunicaciones</span></label></div></fieldset>
          <div className="info-box">La nota oficial requiere los baremos y cortes que publique la Comisión. Aquí verás la puntuación directa exacta: aciertos − errores/3.</div>
        </>}
      </section>
      <aside className="start-card"><span className="eyebrow light">Resumen</span><h3>{mode === 'simulation' ? 'Simulacro completo' : `${Math.min(count, eligible.length)} preguntas`}</h3><ul><li><Check/> Respuestas ocultas</li><li><Flag/> Marcas de revisión</li><li><FileDown/> PDF y soluciones</li></ul><button className="primary-button full" onClick={start} disabled={!questions.length || (mode === 'custom' && !eligible.length)}><Play/> Empezar ahora</button></aside>
    </div>
  </>
}

function HistoricalExams({ onStart }: { onStart: (spec: TestSpec) => void }) {
  return <>
    <section className="section-heading"><div><span className="eyebrow">Literalidad original</span><h2>Exámenes históricos</h2><p>Las pruebas mantienen su numeración, reservas y procedencia. En modo test solo entran preguntas con respuesta oficial, extracción limpia y clasificación vigente.</p></div></section>
    {!bank.exams.length && <div className="empty-state"><History/><h3>No hay exámenes cargados</h3><p>Las convocatorias aparecerán aquí cuando se añadan preguntas.</p></div>}
    <div className="exam-list">{bank.exams.map(exam => {
      const questions = bank.questions.filter(q => q.examId === exam.id && q.active && (q.section.startsWith('first') || q.section.startsWith('case_i')))
      return <article key={exam.id}><div className="year-block">{exam.year}<small>{exam.sitting}</small></div><div><span className="status-pill">Plantilla enlazada</span><h3>{exam.name}</h3><p>{questions.length} preguntas utilizables · ingreso {exam.access}</p></div><button className="outline-button" onClick={() => onStart({ id: crypto.randomUUID(), title: exam.name, mode: 'historical', questionIds: questions.map(q => q.id), durationMinutes: 120, createdAt: new Date().toISOString() })}><Play size={16}/> Realizar</button></article>})}</div>
    <div className="info-box wide">Los demás PDF históricos están inventariados en Fuentes. Los escaneos sin capa de texto y los formatos aún no validados no se mezclan con el banco activo: así se evita estudiar una transcripción o respuesta dudosa.</div>
  </>
}

function ProgressPage({ attempts, progress, questions, onMistakes }: { attempts: AttemptRecord[]; progress: QuestionProgress[]; questions: Question[]; onMistakes: () => void }) {
  const wrong = progress.filter(item => item.wrong > 0).length
  const favorites = progress.filter(item => item.favorite).length
  const unseen = questions.length - progress.filter(item => item.seen).length
  return <>
    <section className="section-heading"><div><span className="eyebrow">Progreso local</span><h2>Tu progreso</h2></div></section>
    <div className="progress-cards"><div><RotateCcw/><strong>{wrong}</strong><span>Preguntas falladas</span><button onClick={onMistakes} disabled={!wrong}>Repasar</button></div><div><Heart/><strong>{favorites}</strong><span>Favoritas</span></div><div><BookOpenCheck/><strong>{unseen}</strong><span>Nunca vistas</span></div></div>
    <section className="section-heading compact"><div><h2>Historial local</h2></div></section>
    {attempts.length ? <div className="attempt-table">{attempts.map(attempt => <article key={attempt.id}><div><small>{new Date(attempt.finishedAt).toLocaleString('es-ES')}</small><strong>{attempt.title}</strong></div><span>{attempt.result.correct} aciertos · {attempt.result.wrong} errores · {attempt.result.blank} blancas</span><b>{formatScore(attempt.result.rawScore)} / {attempt.result.maximumRaw}</b></article>)}</div> : <div className="empty-state"><BarChart3/><h3>Aún no hay resultados</h3><p>El historial está vacío.</p></div>}
  </>
}

function SourcesPage() {
  const statuses = Object.entries(bank.documents.reduce<Record<string, number>>((acc, doc) => ({ ...acc, [doc.status]: (acc[doc.status] ?? 0) + 1 }), {}))
  return <>
    <section className="section-heading"><div><span className="eyebrow">Auditoría documental</span><h2>Fuentes y estado</h2><p>No hay fuentes cargadas en el preparador.</p></div></section>
    {!bank.documents.length && <div className="empty-state"><Archive/><h3>Sin documentos cargados</h3><p>Esta sección estará disponible cuando se añadan fuentes.</p></div>}
    <div className="source-summary">{statuses.map(([status, count]) => <div key={status}><strong>{count}</strong><span>{status.replaceAll('_', ' ')}</span></div>)}</div>
    <div className="source-table"><div className="source-head"><span>Documento</span><span>Tipo</span><span>Páginas</span><span>Estado</span></div>{bank.documents.map(doc => <div key={doc.id}><span><b>{doc.path.split('/').pop()}</b><small>{doc.path}</small></span><span>{doc.role}</span><span>{doc.pages}</span><span><i className={`status-dot ${doc.status}`}/>{doc.status.replaceAll('_', ' ')}<small>{doc.note}</small></span></div>)}</div>
  </>
}

function TestRunner({ spec, questions, onClose, progressMap }: { spec: TestSpec; questions: Question[]; onClose: () => void; progressMap: Map<string, QuestionProgress> }) {
  const [index, setIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, Answer>>({})
  const [marked, setMarked] = useState<Set<string>>(new Set())
  const [finished, setFinished] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const startTime = useRef(Date.now())
  const question = questions[index]
  const isTestReserve = question?.isReserve || (spec.mode === 'simulation' && ((index >= 80 && index < 85) || index >= 105))
  const result = useMemo(() => scoreTest(questions, answers, bank.examConfig.wrongPenalty), [finished])
  useEffect(() => {
    if (finished) return
    const timer = window.setInterval(() => setElapsed(Math.floor((Date.now() - startTime.current) / 1000)), 1000)
    return () => window.clearInterval(timer)
  }, [finished])
  const finish = async () => {
    const finalResult = scoreTest(questions, answers, bank.examConfig.wrongPenalty)
    const attempt: AttemptRecord = { id: spec.id, title: spec.title, mode: spec.mode, finishedAt: new Date().toISOString(), durationSeconds: elapsed, questionIds: questions.map(q => q.id), answers, marked: [...marked], result: finalResult }
    await saveAttempt(attempt)
    await applyQuestionOutcomes(questions, answers)
    setFinished(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  if (!question) return <div className="test-shell"><div className="empty-state"><X/><h2>No hay preguntas disponibles</h2><button className="primary-button" onClick={onClose}>Volver</button></div></div>
  if (finished) return <ResultScreen spec={spec} questions={questions} answers={answers} result={result} onClose={onClose}/>
  const remaining = spec.durationMinutes ? spec.durationMinutes * 60 - elapsed : null
  return <div className="test-shell">
    <header className="test-header"><button className="icon-button" onClick={onClose} aria-label="Salir"><X/></button><div><small>En curso</small><strong>{spec.title}</strong></div><div className={`timer ${remaining !== null && remaining < 600 ? 'urgent' : ''}`}><Clock3/>{remaining === null ? formatTime(elapsed) : formatTime(Math.max(0, remaining))}</div></header>
    <div className="test-layout">
      <main className="test-main"><div className="question-kicker"><span>{question.topicId} · {topicName(question.topicId)}</span><span>{isTestReserve ? 'Reserva · ' : ''}Pregunta {index + 1} de {questions.length}</span></div><h1>{question.prompt}</h1>
        <div className="answer-options">{question.options.map((option, optionIndex) => { const letter = String.fromCharCode(97 + optionIndex) as Answer; return <label key={letter} className={answers[question.id] === letter ? 'selected' : ''}><input type="radio" name={question.id} checked={answers[question.id] === letter} onChange={() => setAnswers({ ...answers, [question.id]: letter })}/><b>{letter.toUpperCase()}</b><span>{option}</span></label>})}</div>
        <div className="question-actions"><button className={`mark-button ${marked.has(question.id) ? 'marked' : ''}`} onClick={() => { const next = new Set(marked); next.has(question.id) ? next.delete(question.id) : next.add(question.id); setMarked(next) }}><Flag size={17}/>{marked.has(question.id) ? 'Marcada para revisar' : 'Marcar para revisar'}</button><span>{question.year} · {question.sitting} · original {question.originalNumber}</span></div>
        <div className="test-nav"><button className="outline-button" onClick={() => setIndex(Math.max(0, index - 1))} disabled={index === 0}><ChevronLeft/> Anterior</button>{index === questions.length - 1 ? <button className="primary-button" onClick={() => void finish()}><Check/> Finalizar test</button> : <button className="primary-button" onClick={() => setIndex(index + 1)}>Siguiente <ChevronRight/></button>}</div>
      </main>
      <aside className="answer-map"><div><strong>Hoja de respuestas</strong><small>{Object.keys(answers).length} contestadas · {questions.length - Object.keys(answers).length} en blanco</small></div><div className="answer-grid">{questions.map((q, qIndex) => <button key={q.id} className={`${answers[q.id] ? 'answered' : ''} ${marked.has(q.id) ? 'marked' : ''} ${qIndex === index ? 'current' : ''}`} onClick={() => setIndex(qIndex)}>{qIndex + 1}</button>)}</div><button className="finish-link" onClick={() => void finish()}>Finalizar y corregir</button></aside>
    </div>
  </div>
}

function formatTime(seconds: number): string { return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}` }

function ResultScreen({ spec, questions, answers, result, onClose }: { spec: TestSpec; questions: Question[]; answers: Record<string, Answer>; result: ReturnType<typeof scoreTest>; onClose: () => void }) {
  const [review, setReview] = useState<'all' | 'wrong' | 'blank'>('wrong')
  const visible = questions.filter(q => review === 'all' || (review === 'wrong' ? answers[q.id] && answers[q.id] !== q.correctAnswer : !answers[q.id]))
  return <div className="result-shell"><header className="result-header"><div><span className="eyebrow light">Test corregido</span><h1>{spec.title}</h1></div><button className="ghost-button" onClick={onClose}><X/> Cerrar</button></header>
    <main className="result-content"><section className="score-hero"><div className="score-dial"><strong>{formatScore(result.rawScore)}</strong><span>de {result.maximumRaw}</span></div><div><span className="eyebrow">Puntuación directa</span><h2>{result.percentage >= 50 ? 'Buen avance.' : 'Ya tienes un mapa claro para repasar.'}</h2><p>Aciertos − errores/3. Esta cifra no es la nota oficial transformada por la Comisión.</p></div></section>
      <div className="result-stats"><div className="success"><Check/><strong>{result.correct}</strong><span>Aciertos</span></div><div className="danger"><X/><strong>{result.wrong}</strong><span>Errores</span></div><div><span className="blank-icon">—</span><strong>{result.blank}</strong><span>En blanco</span></div><div><BarChart3/><strong>{formatScore(result.percentage)}%</strong><span>Directa</span></div></div>
      <div className="export-bar"><span><FileArchive/> Generar documentos del test</span><button onClick={() => void import('./lib/exportPdf').then(mod => mod.downloadExamPdf(spec, questions))}><FileDown/> Simulacro PDF</button><button onClick={() => void import('./lib/exportPdf').then(mod => mod.downloadSolutionsPdf(spec, questions, answers))}><FileDown/> Soluciones PDF</button><button onClick={() => void import('./lib/exportPdf').then(mod => mod.downloadExamZip(spec, questions, answers))}><Download/> ZIP completo</button></div>
      <section className="section-heading compact"><div><h2>Revisión pregunta a pregunta</h2></div><div className="segmented small"><button className={review === 'wrong' ? 'active' : ''} onClick={() => setReview('wrong')}>Errores</button><button className={review === 'blank' ? 'active' : ''} onClick={() => setReview('blank')}>Blancas</button><button className={review === 'all' ? 'active' : ''} onClick={() => setReview('all')}>Todas</button></div></section>
      <div className="review-list">{visible.map((q, index) => { const correct = q.correctAnswer as Answer; return <article key={q.id}><div className={`review-status ${answers[q.id] === correct ? 'ok' : answers[q.id] ? 'fail' : 'blank'}`}>{answers[q.id] === correct ? <Check/> : answers[q.id] ? <X/> : '—'}</div><div><small>{q.topicId} · {topicName(q.topicId)} · {q.year} · página {q.source.page}</small><h3>{q.prompt}</h3><p>Correcta: <b>{correct.toUpperCase()}) {q.options[correct.charCodeAt(0) - 97]}</b></p>{answers[q.id] && answers[q.id] !== correct && <p>Tu respuesta: {answers[q.id].toUpperCase()}) {q.options[answers[q.id].charCodeAt(0) - 97]}</p>}</div><span>{index + 1}</span></article> })}</div>
    </main>
  </div>
}

function topicName(topicId: string): string {
  return bank.program.flatMap(block => block.topics).find(topic => topic.id === topicId)?.name ?? topicId
}

export default App
