#lang racket

(define (read-racket-file filename)
  (call-with-input-file filename
    (lambda (port)
      (let loop ((forms '()))
        (let ((form (read-syntax filename port)))  ; Read one expression
          (if (eof-object? form)
              (begin
                (displayln "File Parser Finished!")
                (reverse forms))  ; Return the collected expressions
              (loop (cons form forms))))))))  ; Recursively read the file

(provide read-racket-file)
