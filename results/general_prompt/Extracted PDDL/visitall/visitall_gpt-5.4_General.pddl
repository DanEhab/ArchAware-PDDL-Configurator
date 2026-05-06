(define (domain grid-visit-all)
(:requirements :typing)
(:types
        place - object)
(:predicates
        (at-robot ?x - place)
        (visited ?x - place)
        (connected ?x ?y - place)
)

(:action move
 :parameters (?curpos ?nextpos - place)
 :precondition (and
        (at-robot ?curpos)
        (connected ?curpos ?nextpos))
 :effect (and
        (not (at-robot ?curpos))
        (at-robot ?nextpos)
        (visited ?nextpos))
)

)