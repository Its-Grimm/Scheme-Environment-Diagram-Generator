(define count
  ; ls will always be a proper list
  (lambda (ls)
    (if (null? ls)
        0
        (+ 1 (count (cdr ls))))))

(count `(1 6 8 4 9))

(define pair-count
  (lambda (ls)
    (if (null? ls)
        0
        (if (pair? (cdr ls))

            (+ 1 (pair-count(cdr ls)))))))


(pair-count `(3 1 . 2))
