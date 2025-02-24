#lang racket

(require "FileParser.rkt" "FileAnalyzer.rkt" "GraphGenerator.rkt")

(define (run filename)
  (display "Running with file: ")
  (display filename)
  (newline)

  (newline) ; Step 1: Parse
  (define ast (read-racket-file filename))
  (newline)

  (displayln "Parsed AST:")
  (displayln ast)  ; Add to see if the AST is being parsed correctly

  (define env (make-hash)) ; Create an empty environment

  (newline) ; Step 2: Analyze
  (define analyzed-env (analyze-env ast env))
  (newline)

  (displayln "Analyzed environment:")
  (displayln analyzed-env)  ; Check if this is actually the modified environment

  (newline) ; Step 3: Generate Diagram
  (generate-env-diagram analyzed-env)
  (newline)

  (display "Runner Finished!\n")
)

(provide run)
