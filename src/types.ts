export type Answer = 'a' | 'b' | 'c' | 'd'

export interface Topic {
  id: string
  name: string
}

export interface ProgramBlock {
  id: string
  name: string
  topics: Topic[]
}

export interface SourceRef {
  pdf: string
  page: number
  answerPdf: string | null
  extraction?: string
}

export interface Question {
  id: string
  examId: string
  year: number
  access: 'libre' | 'promocion_interna'
  sitting: string
  exercise: string
  section: string
  isReserve: boolean
  originalNumber: number
  prompt: string
  options: string[]
  correctAnswer: Answer | 'anulada' | null
  answerStatus: string
  blockId: string
  topicId: string
  classificationConfidence: number
  classificationMethod?: string
  status: string
  statusReason: string
  active: boolean
  duplicateOf: string | null
  source: SourceRef
}

export interface SourceDocument {
  id: string
  path: string
  pages: number
  role: string
  year: number | null
  status: string
  note: string
}

export interface ExamSummary {
  id: string
  name: string
  year: number
  access: string
  sitting: string
}

export interface Bank {
  meta: {
    builtAt: string
    officialCall: string
    scoringNote: string
  }
  examConfig: {
    durationMinutes: number
    firstPartQuestions: number
    firstPartReserve: number
    practicalQuestions: number
    practicalReserve: number
    wrongPenalty: number
    blankPenalty: number
    officialMaximum: number
    partMaximum: number
    officialCutNote: string
  }
  program: ProgramBlock[]
  documents: SourceDocument[]
  exams: ExamSummary[]
  questions: Question[]
}

export interface TestSpec {
  id: string
  title: string
  mode: 'custom' | 'simulation' | 'historical' | 'mistakes'
  questionIds: string[]
  durationMinutes?: number
  createdAt: string
}

export interface TestResult {
  correct: number
  wrong: number
  blank: number
  rawScore: number
  maximumRaw: number
  percentage: number
  byTopic: Record<string, { correct: number; wrong: number; blank: number }>
}

export interface AttemptRecord {
  id: string
  title: string
  mode: TestSpec['mode']
  finishedAt: string
  durationSeconds: number
  questionIds: string[]
  answers: Record<string, Answer>
  marked: string[]
  result: TestResult
}

export interface QuestionProgress {
  questionId: string
  seen: number
  correct: number
  wrong: number
  favorite: boolean
  lastSeenAt?: string
}
