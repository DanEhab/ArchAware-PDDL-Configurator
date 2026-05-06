(define (domain grid-visit-all)
(:requirements :typing)
(:types        place - object)
(:predicates (connected ?x ?y - place)
	     (at-robot ?x - place)
	     (visited ?x - place)
)
	
(:action move
:parameters (?curpos ?nextpos - place)
:precondition (and (connected ?curpos ?nextpos) (at-robot ?curpos))
:effect (and (not (at-robot ?curpos)) (at-robot ?nextpos) (visited ?nextpos))
)

)