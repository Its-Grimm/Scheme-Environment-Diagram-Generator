#lang racket

(define (analyze-env ast env)
  (newline)
  (displayln "Inside FileAnalyzer.rkt")
  (displayln "Analyzing AST:")
  (displayln ast)  ; Check the AST input
  (displayln "Current env:")
  (displayln env)  ; Check the environment before modification

  (cond
    [(symbol? ast) 
     (hash-ref env ast 'unbound)
    ]  ; Lookup variables in the environment

    [(pair? ast)
     (match ast
       [
        (list 'define (list name args ...) body)
        (hash-set! env name (list 'procedure args body))
        env  ; Return the updated environment
       ]  ; Store function definitions

       [
        (list 'define name value)
        (hash-set! env name value)
        env  ; Return the updated environment
       ]  ; Store variable definitions

       [
        (list 'lambda args body)
        (list 'lambda args body)
       ]  ; Return lambda as a procedure

       [_
        (for-each (lambda (x) (analyze-env x env)) ast)  ; Analyze subexpressions
        env  ; Return the updated environment
        ; (map (lambda (x) (analyze-env x env)) ast)
       ]
     )
    ]  ; Recursively analyze
    [else ast]
  )
  (displayln "File Analyzer Finished!")
  (newline)
)  ; Return unchanged for literals

(provide analyze-env)

; (define env (make-hash))
; (define analyzed (analyze-env test-code env))

; (displayln analyzed)  ; View the extracted environment
