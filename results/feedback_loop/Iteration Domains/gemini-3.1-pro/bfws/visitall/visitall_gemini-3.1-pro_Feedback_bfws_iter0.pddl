(define (domain grid-visit-all)
(:requirements :typing)
(:types        place - object)
(:predicates (visited ?x - place)
	     (at-robot ?x - place)
	     (connected ?x ?y - place)
)
	
(:action move
:parameters (?curpos ?nextpos - place)
:precondition (and (at-robot ?curpos) (connected ?curpos ?nextpos))
:effect (and (visited ?nextpos) (at-robot ?nextpos) (not (at-robot ?curpos)))
)

)