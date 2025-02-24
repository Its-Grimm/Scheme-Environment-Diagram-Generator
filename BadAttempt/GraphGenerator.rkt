#lang racket

(require pict)

;; Define the save-pict-alt function
(define (save-pict-alt filename pict)
  (send (pict->bitmap pict) save-file filename 'png))

(define (generate-env-diagram env)
  (displayln "Starting Graph Generator!")
  
  (let ([bindings (for/list ([key (hash-keys env)])
                    (vc-append
                     (text (symbol->string key))           ; Use default text style
                     (text (format "~a" (hash-ref env key)))) ; Use default text style
                    )])
    (displayln "Environment contents:")
    (displayln env)
    (displayln "Bindings:")
    (displayln bindings)
    (define env-pic (apply hc-append bindings))
    (display "Graph Generator Finished!\n")
    (if env-pic
        (save-pict-alt "/home/grimm/Desktop/RKTEnvDiagramGenerator/environment-diagram.png" env-pic)
        (displayln "Failed to generate diagram"))
    env-pic))

(provide generate-env-diagram)
