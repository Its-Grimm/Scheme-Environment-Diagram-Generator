#lang racket

(require racket/syntax)  ;; Required for syntax parsing

(define (analyze-env ast env)
  (newline)
  (displayln "Inside File Analyzer!")
  (displayln "Analyzing AST:")
  (displayln ast)
  (displayln "Current env:")
  (displayln env)

  ;; Make a mutable environment so we can modify it inside the loop
  (define updated-env (make-hash))

  ;; Process each expression in the AST
  (for ([expr ast])
    (let ([stx (syntax->datum expr)])  ;; Convert syntax object to a list
      (match stx
        ;; Function definition (define (name args ...) body)
        [(list 'define (list name args ...) body)
         (hash-set! updated-env name (list 'procedure args body))
         (displayln (format "Added function: ~a ~a" name args))]

        ;; Variable definition (define name value)
        [(list 'define name value)
         (hash-set! updated-env name value)
         (displayln (format "Added variable: ~a ~a" name value))]

        ;; Other expressions (ignored for now)
        [_ (void)])))

  (displayln "Updated Environment:")
  (displayln updated-env)
  (displayln "File Analyzer Finished!")
  updated-env  ;; Return updated environment
)

(provide analyze-env)
