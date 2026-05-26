(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (available ?x - hoist) 
             (clear ?x - surface)
             (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck)
             (lifting ?x - hoist ?y - crate)
             (at ?x - locatable ?y - place))
	
(:action Drive
:parameters (?x - truck ?y - place ?z - place) 
:precondition (and (at ?x ?y))
:effect (and (not (at ?x ?y)) (at ?x ?z)))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?x ?p) (available ?x) (at ?y ?p) (on ?y ?z) (clear ?y))
:effect (and (lifting ?x ?y) (not (available ?x)) (not (at ?y ?p)) (not (clear ?y)) (not (on ?y ?z)) (clear ?z)))

(:action Drop 
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?x ?p) (lifting ?x ?y) (at ?z ?p) (clear ?z))
:effect (and (available ?x) (not (lifting ?x ?y)) (at ?y ?p) (clear ?y) (on ?y ?z) (not (clear ?z))))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?x ?p) (lifting ?x ?y) (at ?z ?p))
:effect (and (not (lifting ?x ?y)) (available ?x) (in ?y ?z)))

(:action Unload 
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?x ?p) (available ?x) (at ?z ?p) (in ?y ?z))
:effect (and (lifting ?x ?y) (not (available ?x)) (not (in ?y ?z))))

)