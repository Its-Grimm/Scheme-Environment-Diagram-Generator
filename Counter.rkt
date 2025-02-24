(define make-counter
  (lambda ()
    (let((n 0))
      (lambda ()
        (set! n (+ n 1))
        n))))

(define my-counter (make-counter))
