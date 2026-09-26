import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'
import JSZip from 'jszip'
import type { Answer, Question, TestSpec } from '../types'

function safeName(value: string): string {
  return value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

function addHeader(doc: jsPDF, title: string, subtitle: string): void {
  doc.setFillColor(23, 50, 77)
  doc.rect(0, 0, 210, 28, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(15)
  doc.text(title, 16, 12)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.text(subtitle, 16, 19)
  doc.setTextColor(20, 32, 43)
}

function ensureSpace(doc: jsPDF, y: number, needed: number): number {
  if (y + needed <= 278) return y
  doc.addPage()
  return 18
}

function addFooters(doc: jsPDF): void {
  const pages = doc.getNumberOfPages()
  for (let page = 1; page <= pages; page += 1) {
    doc.setPage(page)
    doc.setDrawColor(218, 225, 231)
    doc.line(16, 286, 194, 286)
    doc.setTextColor(98, 116, 133)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7)
    doc.text('Preparador TAI AGE · simulacro no oficial', 16, 291)
    doc.text(`${page} / ${pages}`, 194, 291, { align: 'right' })
    doc.setTextColor(20, 32, 43)
  }
}

export function buildExamPdf(spec: TestSpec, questions: Question[]): jsPDF {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  addHeader(doc, 'SIMULACRO TAI AGE', 'Documento no oficial · generado para estudio personal')
  doc.setFontSize(10)
  doc.text(spec.title, 16, 38)
  doc.setFontSize(8.5)
  const instructions = [
    `Preguntas: ${questions.length}.`,
    'Cada error descuenta un tercio de un acierto. Las respuestas en blanco no penalizan.',
    'Las preguntas marcadas como reserva se aplican por orden cuando corresponda.',
  ]
  doc.text(instructions, 16, 45)
  let y = 65
  questions.forEach((question, index) => {
    const reserve = question.isReserve || (spec.mode === 'simulation' && ((index >= 80 && index < 85) || index >= 105))
    const promptLines = doc.splitTextToSize(`${index + 1}. ${reserve ? '[RESERVA] ' : ''}${question.prompt}`, 164)
    const optionLines = question.options.flatMap((option, optionIndex) => doc.splitTextToSize(`${String.fromCharCode(97 + optionIndex)}) ${option}`, 156))
    y = ensureSpace(doc, y, (promptLines.length + optionLines.length) * 4 + 8)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(9)
    doc.text(promptLines, 16, y)
    y += promptLines.length * 4 + 2
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8.5)
    question.options.forEach((option, optionIndex) => {
      const lines = doc.splitTextToSize(`${String.fromCharCode(97 + optionIndex)}) ${option}`, 156)
      doc.text(lines, 22, y)
      y += lines.length * 3.8 + 1
    })
    y += 3
  })
  doc.addPage()
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(14)
  doc.text('Hoja de respuestas', 16, 20)
  autoTable(doc, {
    startY: 28,
    head: [['N.º', 'A', 'B', 'C', 'D', 'Revisión']],
    // Helvetica integrada en PDF no cubre de forma fiable los glifos Unicode
    // de círculo/casilla. Usamos marcas ASCII para impresión consistente.
    body: questions.map((_, index) => [String(index + 1), '( )', '( )', '( )', '( )', '[ ]']),
    styles: { fontSize: 8, cellPadding: 1.3, halign: 'center' },
    headStyles: { fillColor: [23, 50, 77] },
    margin: { left: 25, right: 25 },
  })
  addFooters(doc)
  return doc
}

export function buildSolutionsPdf(spec: TestSpec, questions: Question[], answers?: Record<string, Answer>): jsPDF {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  addHeader(doc, 'SOLUCIONES · TAI AGE', `${spec.title} · documento de estudio no oficial`)
  autoTable(doc, {
    startY: 36,
    head: [['N.º', 'Correcta', 'Tu respuesta', 'Tema', 'Procedencia']],
    body: questions.map((question, index) => [
      String(index + 1),
      question.correctAnswer?.toUpperCase() ?? '—',
      answers?.[question.id]?.toUpperCase() ?? '—',
      question.topicId,
      question.origin === 'uploaded' ? `Fuente añadida: ${question.source.pdf} · ${question.originalNumber}` : `${question.year} · ${question.sitting} · ${question.section} ${question.originalNumber} · p. ${question.source.page}`,
    ]),
    styles: { fontSize: 7.5, cellPadding: 1.6, valign: 'middle' },
    headStyles: { fillColor: [23, 50, 77] },
    columnStyles: { 0: { cellWidth: 12 }, 1: { cellWidth: 17 }, 2: { cellWidth: 20 }, 3: { cellWidth: 18 } },
    margin: { left: 12, right: 12 },
  })
  addFooters(doc)
  return doc
}

function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export function downloadExamPdf(spec: TestSpec, questions: Question[]): void {
  buildExamPdf(spec, questions).save(`${safeName(spec.title)}-simulacro.pdf`)
}

export function downloadSolutionsPdf(spec: TestSpec, questions: Question[], answers?: Record<string, Answer>): void {
  buildSolutionsPdf(spec, questions, answers).save(`${safeName(spec.title)}-soluciones.pdf`)
}

export async function downloadExamZip(spec: TestSpec, questions: Question[], answers?: Record<string, Answer>): Promise<void> {
  const base = safeName(spec.title)
  const zip = new JSZip()
  zip.file(`${base}-simulacro.pdf`, buildExamPdf(spec, questions).output('arraybuffer'))
  zip.file(`${base}-soluciones.pdf`, buildSolutionsPdf(spec, questions, answers).output('arraybuffer'))
  saveBlob(await zip.generateAsync({ type: 'blob' }), `${base}.zip`)
}
