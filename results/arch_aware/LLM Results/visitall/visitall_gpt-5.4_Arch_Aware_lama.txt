(define (domain grid-visit-all)
(:requirements :typing)
(:types        place - object)
(:predicates
	(at-robot ?x - place)
	(visited ?x - place)
	(connected ?x ?y - place)
)
	
(:action move
:parameters (?curpos ?nextpos - place)
:precondition (and (connected ?curpos ?nextpos) (at-robot ?curpos))
:effect (and (at-robot ?nextpos) (visited ?nextpos) (not (at-robot ?curpos)))
)

)